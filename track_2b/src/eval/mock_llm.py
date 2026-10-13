"""Mock OpenAI-compatible LLM server for tests and CI (no GPU, no network).

It returns *schema-valid* outputs for every Passerelle task so the whole pipeline can be exercised:

* ``extract``         – JSON fact card built from the deterministic extractors (+ roles)
* ``explain_source``  – five headings, each with a sentence, using every required placeholder
* ``translate``       – identity "translation" prefixed with a language tag (keeps placeholders)
* ``back_translate``  – strips the tag again (so chrF is high)
* ``naive``/``reply`` – plausible text with the letter's facts / placeholders

The task is read from the ``X-Passerelle-Task`` header, falling back to sniffing the prompt.
It is NOT a model: numbers produced with it are never reported as results.

Run:  ``python -m eval.mock_llm --port 8099``  then ``LLM_BASE_URL=http://127.0.0.1:8099/v1``.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from passerelle.facts import extract_facts
from passerelle.extract import guess_letter_type

app = FastAPI(title="Passerelle mock LLM")
STATE = {"requests": 0}
_FENCED = re.compile(r"<<<\n?(.*?)\n?>>>", re.S)
_PH = re.compile(r"⟦[A-Z]\d{1,3}⟧")


def _fenced(text: str, idx: int = 0) -> str:
    blocks = _FENCED.findall(text)
    return blocks[idx] if len(blocks) > idx else text


def _task(request: Request, messages: list[dict]) -> str:
    t = request.headers.get("x-passerelle-task")
    if t:
        return t
    sys_ = (messages[0].get("content") or "") if messages else ""
    user = (messages[-1].get("content") or "") if messages else ""
    if "JSON object" in user or "JSON" in sys_:
        return "extract"
    if "Translate faithfully" in sys_:
        return "back_translate"
    if "Translate the text" in sys_:
        return "translate"
    if "five headings" in user or "Facts the reader must get" in user:
        return "explain_source"
    if "reply letter" in user:
        return "reply"
    if "Explain this letter" in user:
        return "naive"
    return "chat"


def _extract(user: str) -> dict:
    letter = _fenced(user)
    facts = extract_facts(letter)
    first_line = next((ln.strip() for ln in letter.splitlines() if ln.strip()), None)
    dates = [{"text": f.value, "role": f.role if f.role in {"letter_date", "deadline", "appointment", "effective", "past"} else "other"}
             for f in facts if f.type == "date"]
    rel = next((f for f in facts if f.type == "duration" and f.role == "deadline"), None)
    return {
        "authority": first_line,
        "letter_type": guess_letter_type(letter),
        "subject": first_line,
        "summary": "Mock summary of the letter.",
        "action_required": "Mock: reply before the deadline.",
        "dates": dates,
        "deadline_relative": f"{rel.value} {rel.meta.get('unit_text', '')}".strip() if rel else None,
        "times": [f.value for f in facts if f.type == "time"],
        "appointment_place": None,
        "amounts": [{"text": f.value, "purpose": "mock"} for f in facts if f.type == "amount"],
        "references": [f.value for f in facts if f.type == "reference"],
        "iban": next((f.value for f in facts if f.type == "iban"), None),
        "ahv_number": next((f.value for f in facts if f.type == "ahv"), None),
        "phones": [f.value for f in facts if f.type == "phone" and f.role != "fax"],
        "emails": [f.value for f in facts if f.type == "email"],
        "documents": ["Mock document"],
        "consequences": "Mock consequence.",
        "contact_person": None,
    }


def _explain_source(user: str) -> str:
    m = re.search(r"Facts the reader must get.*?\n(.*?)\n\n", user, re.S)
    required = _PH.findall(m.group(1)) if m else []
    hm = re.search(r"each followed by one to three short sentences:\n(.*?)\n\n", user, re.S)
    heads = [h for h in (hm.group(1).splitlines() if hm else []) if h.strip()] or ["1", "2", "3", "4", "5"]
    chunks = [required[i::len(heads)] for i in range(len(heads))]
    lines = []
    for h, ph in zip(heads, chunks):
        lines.append(h)
        lines.append("Mock sentence " + " ".join(ph) + ".")
    return "\n".join(lines)


def _respond(task: str, messages: list[dict], target_hint: str = "") -> str:
    user = messages[-1].get("content") or ""
    sys_ = messages[0].get("content") or ""
    if task == "extract":
        return json.dumps(_extract(user), ensure_ascii=False)
    if task == "explain_source":
        return _explain_source(user)
    if task == "translate":
        tgt = re.search(r"into (\w+)", sys_)
        return f"[{(tgt.group(1) if tgt else 'xx')[:3].lower()}] " + _fenced(user)
    if task == "back_translate":
        return re.sub(r"^\[\w{2,3}\]\s*", "", _fenced(user))
    if task == "reply":
        refs = re.search(r"contains (.*)\.", user)
        ph = _PH.findall(refs.group(1)) if refs else []
        client_ph = _PH.findall(_fenced(user, 1))
        return (f"Betreff: {' '.join(ph)}\n\nSehr geehrte Damen und Herren\n\nMock reply. "
                + " ".join(client_ph) + "\n\nFreundliche Grüsse\n[Name]")
    if task == "naive":
        facts = extract_facts(_fenced(user))
        return "Mock naive explanation: " + "; ".join(f.value for f in facts if f.critical)
    if task == "judge":
        return json.dumps({"score": 4, "issues": "mock"})
    return "Mock response."


@app.get("/v1/models")
def models():
    return {"object": "list", "data": [{"id": "mock-apertus", "object": "model", "owned_by": "passerelle-mock"}]}


@app.post("/v1/chat/completions")
async def chat(request: Request):
    body = await request.json()
    STATE["requests"] += 1
    messages = body.get("messages") or []
    task = _task(request, messages)
    text = _respond(task, messages)
    model = body.get("model", "mock-apertus")
    prompt_tokens = sum(len((m.get("content") or "")) for m in messages) // 4
    completion_tokens = max(1, len(text) // 4)
    usage = {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
             "total_tokens": prompt_tokens + completion_tokens}
    cid = "chatcmpl-" + uuid.uuid4().hex[:12]
    if body.get("stream"):
        def gen():
            for i in range(0, len(text), 7):
                chunk = {"id": cid, "object": "chat.completion.chunk", "created": int(time.time()), "model": model,
                         "choices": [{"index": 0, "delta": {"content": text[i:i + 7]}, "finish_reason": None}]}
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            end = {"id": cid, "object": "chat.completion.chunk", "model": model,
                   "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}], "usage": usage}
            yield f"data: {json.dumps(end)}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(gen(), media_type="text/event-stream")
    return JSONResponse({
        "id": cid, "object": "chat.completion", "created": int(time.time()), "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        "usage": usage,
    })


def main(argv: list[str] | None = None) -> int:
    import uvicorn

    ap = argparse.ArgumentParser(description="Mock OpenAI-compatible server for Passerelle tests/CI")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8099)
    args = ap.parse_args(argv)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
