"""FastAPI application: JSON API under /api and the static UI (Next.js export) at /.

Endpoints (SPEC §2; fields marked + are additions beyond the original contract):
  GET  /api/health                 {status, model, backend_reachable, +egress, +version, +prompt_version, +gate_calibrated}
  GET  /api/languages              [{code, name, native, script, rtl, gate, quality, +eval_group}]
  GET  /api/samples                [{id, title, language, type, +split, +authority}]
  GET  /api/samples/{id}           + full sample incl. text and ground truth
  POST /api/analyze                {text | sample_id, source_lang?} -> {analysis_id, letter_lang, fact_card, facts, disagreements, timings, +text, +tokens, +llm_ok}
  POST /api/explain                {analysis_id | text, target_lang} -> explanation, masked, rtl, back_translation, chrf, placeholder_audit, gate, timings, tokens, +source_plain, +fact_spans
  GET|POST /api/explain/stream     same, as Server-Sent Events: stage / source_plain / token / result / error
  POST /api/reply                  {analysis_id, client_message, client_lang} -> {reply_letter, facts_used, audit}
  GET  /api/audit                  recent hash-only audit entries (+ chain verification)
  + POST /api/redact               {text | analysis_id, kinds?} -> {redacted, counts}
  + POST /api/ingest               multipart file (PDF or .txt) -> {text, chars}
  + GET  /api/evidence             data/eval_runs/summary.json (if present)
"""

from __future__ import annotations

import json
import threading
from collections import OrderedDict
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from . import __version__, egress
from .audit import get_audit_log
from .config import get_settings
from .explain import explain, explain_events
from .extract import Analysis, analyze
from .ingest import normalize_text, pdf_to_text
from .languages import LANGUAGES, get_language
from .llm import LLMClient, LLMError
from .prompts import PROMPT_VERSION
from .redact import redact
from .reply import draft_reply
from .samples import get_sample, list_samples
from .verify import all_thresholds, thresholds_for


class AnalyzeRequest(BaseModel):
    text: str | None = Field(default=None, max_length=60_000)
    sample_id: str | None = None
    source_lang: str | None = None
    use_llm: bool = True


class ExplainRequest(BaseModel):
    analysis_id: str | None = None
    text: str | None = Field(default=None, max_length=60_000)
    source_lang: str | None = None
    target_lang: str


class ReplyRequest(BaseModel):
    analysis_id: str
    client_message: str = Field(max_length=8_000)
    client_lang: str


class RedactRequest(BaseModel):
    text: str | None = Field(default=None, max_length=60_000)
    analysis_id: str | None = None
    kinds: list[str] | None = None


class _Store:
    def __init__(self, cap: int = 300):
        self.cap = cap
        self._d: OrderedDict[str, Analysis] = OrderedDict()
        self._lock = threading.Lock()

    def put(self, a: Analysis) -> None:
        with self._lock:
            self._d[a.id] = a
            self._d.move_to_end(a.id)
            while len(self._d) > self.cap:
                self._d.popitem(last=False)

    def get(self, aid: str) -> Analysis | None:
        with self._lock:
            return self._d.get(aid)


def create_app() -> FastAPI:
    s = get_settings()
    egress.configure(s.llm_base_url, s.egress_allow)
    if s.egress_socket_guard:
        egress.install_socket_guard()
    app = FastAPI(title="Passerelle", version=__version__,
                  description="Sovereign caseworker assistant for Swiss official letters, built on Apertus.")
    app.add_middleware(CORSMiddleware, allow_origins=list(s.cors_origins), allow_methods=["*"], allow_headers=["*"])
    store = _Store()
    client = LLMClient(s)
    app.state.client = client
    app.state.store = store

    def _analysis_for(aid: str | None, text: str | None, source_lang: str | None) -> Analysis:
        if aid:
            a = store.get(aid)
            if a is None:
                raise HTTPException(404, f"unknown analysis_id {aid}")
            return a
        if text and text.strip():
            a = analyze(text, source_lang=source_lang, client=client)
            store.put(a)
            return a
        raise HTTPException(422, "provide analysis_id or text")

    def _lang(code: str):
        try:
            return get_language(code)
        except KeyError as exc:
            raise HTTPException(400, str(exc)) from exc

    # ------------------------------------------------------------------------- meta
    @app.get("/api/health")
    def health():
        thr = all_thresholds()
        return {
            "status": "ok",
            "version": __version__,
            "model": s.llm_name,
            "backend_reachable": client.ping(),
            "egress": egress.status(),
            "prompt_version": PROMPT_VERSION,
            "gate_calibrated": bool(thr.get("calibrated")),
        }

    @app.get("/api/languages")
    def languages():
        thr = all_thresholds().get("languages", {})
        out = []
        for code, lang in LANGUAGES.items():
            t = thresholds_for(code)
            out.append({
                **lang.to_dict(),
                "native_name": lang.native,
                "gate": {"ready": t["ready"], "review": t["review"], "floor": t.get("floor", "ready")},
                "thresholds": {"ready": t["ready"], "review": t["review"]},
                "quality": (thr.get(code) or {}).get("tier", "not_evaluated"),
                "quality_tier": (thr.get(code) or {}).get("tier", "not_evaluated"),
                "eval": (thr.get(code) or {}).get("dev_stats"),
            })
        return out

    @app.get("/api/samples")
    def samples():
        return list_samples()

    @app.get("/api/samples/{sample_id}")
    def sample(sample_id: str):
        smp = get_sample(sample_id)
        if not smp:
            raise HTTPException(404, "unknown sample")
        return smp

    @app.get("/api/evidence")
    @app.get("/api/eval/summary")
    def evidence():
        p = s.eval_summary_path
        if not p.exists():
            raise HTTPException(404, "no evaluation summary yet")
        return JSONResponse(json.loads(p.read_text(encoding="utf-8")))

    @app.get("/api/audit")
    def audit_entries(limit: int = Query(50, ge=1, le=500)):
        log = get_audit_log()
        return {"entries": log.recent(limit), "chain": log.verify()}

    # ---------------------------------------------------------------------- pipeline
    @app.post("/api/ingest")
    async def ingest(file: UploadFile = File(...)):
        data = await file.read()
        if len(data) > 10_000_000:
            raise HTTPException(413, "file too large")
        name = (file.filename or "").lower()
        pages = None
        if name.endswith(".pdf") or data[:4] == b"%PDF":
            text = pdf_to_text(data)
            pages = text.count("\f") + 1 if text else 0
        else:
            text = normalize_text(data.decode("utf-8", errors="replace"))
        if not text.strip():
            raise HTTPException(422, "no text layer found (OCR is out of scope; paste the text instead)")
        get_audit_log().record("ingest", inputs={"document": text}, meta={"chars": len(text)})
        return {"text": text, "chars": len(text), "pages": pages}

    @app.post("/api/analyze")
    def analyze_ep(req: AnalyzeRequest):
        text, sample_id = req.text, None
        if req.sample_id:
            smp = get_sample(req.sample_id)
            if not smp:
                raise HTTPException(404, "unknown sample")
            text, sample_id = smp["text"], req.sample_id
        if not text or not text.strip():
            raise HTTPException(422, "provide text or sample_id")
        a = analyze(text, source_lang=req.source_lang, client=client, use_llm=req.use_llm, sample_id=sample_id)
        store.put(a)
        get_audit_log().record("analyze", analysis_id=a.id, inputs={"letter": a.text},
                               meta={"lang": a.lang, "facts": len(a.facts), "llm_ok": a.llm_ok,
                                     "disagreements": len(a.disagreements)})
        return a.to_api()

    @app.post("/api/explain")
    def explain_ep(req: ExplainRequest):
        _lang(req.target_lang)
        a = _analysis_for(req.analysis_id, req.text, req.source_lang)
        try:
            return explain(a, req.target_lang, client)
        except LLMError as exc:
            raise HTTPException(502, f"LLM backend error: {exc}") from exc

    def _sse(a: Analysis, target: str):
        def gen():
            try:
                for event, payload in explain_events(a, target, client, stream=True):
                    yield f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
            except Exception as exc:  # report errors in-band; the HTTP status is already 200
                yield f"event: error\ndata: {json.dumps({'message': str(exc)[:300]})}\n\n"
        return StreamingResponse(gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.post("/api/explain/stream")
    def explain_stream_post(req: ExplainRequest):
        _lang(req.target_lang)
        return _sse(_analysis_for(req.analysis_id, req.text, req.source_lang), req.target_lang)

    @app.get("/api/explain/stream")
    def explain_stream_get(analysis_id: str, target_lang: str):
        _lang(target_lang)
        return _sse(_analysis_for(analysis_id, None, None), target_lang)

    @app.post("/api/reply")
    def reply_ep(req: ReplyRequest):
        _lang(req.client_lang)
        a = _analysis_for(req.analysis_id, None, None)
        try:
            return draft_reply(a, req.client_message, req.client_lang, client)
        except LLMError as exc:
            raise HTTPException(502, f"LLM backend error: {exc}") from exc

    @app.post("/api/redact")
    def redact_ep(req: RedactRequest):
        kinds = tuple(req.kinds) if req.kinds else None
        if req.analysis_id:
            a = _analysis_for(req.analysis_id, None, None)
            res = redact(a.text, a.facts, kinds) if kinds else redact(a.text, a.facts)
        elif req.text:
            text = normalize_text(req.text)
            res = redact(text, None, kinds) if kinds else redact(text)
        else:
            raise HTTPException(422, "provide text or analysis_id")
        get_audit_log().record("redact", inputs={"redacted": res["redacted"]}, meta={"items": sum(res["counts"].values())})
        return res

    # --------------------------------------------------------------------- static UI
    static_dir = Path(s.static_dir)

    @app.get("/{path:path}", include_in_schema=False)
    def static(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "not found")
        if not static_dir.exists():
            if path in {"", "index.html"}:
                return HTMLResponse(
                    "<!doctype html><meta charset=utf-8><title>Passerelle</title>"
                    "<body style='font-family:system-ui;margin:3rem;color:#1A1615;background:#F4F1EE'>"
                    "<h1>Passerelle API is running</h1><p>The web UI has not been built "
                    "(<code>src/web/out</code> missing). See <a href='/docs'>/docs</a> for the API.</p>")
            raise HTTPException(404, "not found")
        root = static_dir.resolve()
        candidates = [path, f"{path}/index.html", f"{path}.html"] if path else ["index.html"]
        for c in candidates:
            p = (root / c).resolve()
            if root in p.parents or p == root:
                if p.is_file():
                    return FileResponse(p)
        nf = root / "404.html"
        if nf.is_file():
            return FileResponse(nf, status_code=404)
        raise HTTPException(404, "not found")

    return app


app = None  # created lazily by cli / uvicorn factory


def get_app() -> FastAPI:
    global app
    if app is None:
        app = create_app()
    return app
