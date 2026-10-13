"""Evaluation runner (SPEC §4).  Stages are resumable; every LLM call is cached in data/eval_runs/llm_cache.jsonl.

    python -m eval.run_eval extract            # fact extraction on all letters (scored on test)
    python -m eval.run_eval explain            # naive vs fact-lock on dev + explain_subset x languages
    python -m eval.run_eval judge              # optional helper judge (another open model) on round trips
    python -m eval.run_eval calibrate          # gate thresholds from the DEV split only
    python -m eval.run_eval score              # all test metrics -> data/eval_runs/summary.json
    python -m eval.run_eval all                # everything in order (then: python -m eval.figures)

Options: --langs ti,ar  --limit N (letters)  --judge-model llama3:latest
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import replace
from pathlib import Path

from passerelle.config import get_settings
from passerelle.explain import explain
from passerelle.extract import _normalize, analyze, guess_letter_type
from passerelle.languages import EVAL_LANGS, LANGUAGES, check_output_language
from passerelle.llm import is_degenerate, parse_json_lenient
from passerelle.prompts import PROMPT_VERSION, naive_messages
from passerelle.verify import unexpected_numbers

from .harness import RUNS, CachedClient, GpuSampler, energy_from_cache, load_letters
from .metrics import EVAL_TYPES, extraction_scores, key, preservation

CACHE = RUNS / "llm_cache.jsonl"
EXTRACT_ITEMS = RUNS / "extraction_items.jsonl"
EXPLAIN_ITEMS = RUNS / "explain_items.jsonl"
JUDGE_ITEMS = RUNS / "judge_items.jsonl"


def _jsonl_read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _jsonl_append(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _log(msg: str) -> None:
    print(time.strftime("%H:%M:%S"), msg, flush=True)


# ------------------------------------------------------------------------------ extract

def llm_only_keys(llm: dict | None) -> set:
    """Apertus-only predictions, normalised with the same normalisers (no grounding)."""
    if not llm:
        return set()
    out = set()

    def add(t, raw):
        n = _normalize(t, str(raw), None) if raw else None
        if n:
            out.add(key(t, n))

    for d in llm.get("dates") or []:
        if isinstance(d, dict):
            add("date", d.get("text"))
    for t in llm.get("times") or []:
        add("time", t)
    for a in llm.get("amounts") or []:
        if isinstance(a, dict):
            add("amount", a.get("text"))
    for r in llm.get("references") or []:
        add("reference", r)
    add("iban", llm.get("iban"))
    add("ahv", llm.get("ahv_number"))
    for p in llm.get("phones") or []:
        add("phone", p)
    for e in llm.get("emails") or []:
        add("email", e)
    rel = llm.get("deadline_relative")
    if rel:
        from passerelle.facts import extract_facts

        for f in extract_facts(str(rel)):
            if f.type == "duration":
                out.add(key("duration", f.normalized))
    return out


def stage_extract(client: CachedClient, letters: list[dict]) -> None:
    done = {r["id"] for r in _jsonl_read(EXTRACT_ITEMS)}
    for i, L in enumerate(letters):
        if L["id"] in done:
            continue
        t0 = time.time()
        a = analyze(L["text"], client=client)
        rec = {
            "id": L["id"], "split": L["split"], "lang": L["lang"], "letter_type": L["letter_type"],
            "detected_lang": a.lang, "llm_ok": a.llm_ok, "llm_error": a.llm_error, "llm_raw": a.llm_raw,
            "rule_facts": [{"type": f.type, "normalized": f.normalized, "role": f.role, "value": f.value} for f in a.rule_facts],
            "merged_facts": [{"type": f.type, "normalized": f.normalized, "role": f.role, "source": f.source,
                              "critical": f.critical, "value": f.value} for f in a.facts],
            "card_letter_type": a.card.get("letter_type"), "keyword_letter_type": guess_letter_type(a.text),
            "disagreements": a.disagreements, "timings": a.timings, "tokens": a.tokens,
            "wall_s": round(time.time() - t0, 2),
        }
        _jsonl_append(EXTRACT_ITEMS, rec)
        _log(f"extract {i + 1}/{len(letters)} {L['id']} llm_ok={a.llm_ok} {a.timings['total_ms']:.0f} ms")


def score_extraction(letters: list[dict]) -> dict:
    recs = {r["id"]: r for r in _jsonl_read(EXTRACT_ITEMS)}
    out = {}
    for split in ("test", "dev"):
        L = [x for x in letters if x["split"] == split and x["id"] in recs]
        gold = {x["id"]: {key(f["type"], f["normalized"]) for f in x["facts"] if f["type"] in EVAL_TYPES} for x in L}
        rules = {x["id"]: {key(f["type"], f["normalized"]) for f in recs[x["id"]]["rule_facts"] if f["type"] in EVAL_TYPES} for x in L}
        llm = {x["id"]: llm_only_keys(recs[x["id"]]["llm_raw"]) for x in L}
        merged = {x["id"]: {key(f["type"], f["normalized"]) for f in recs[x["id"]]["merged_facts"] if f["type"] in EVAL_TYPES} for x in L}
        # deadline / appointment role accuracy and letter type accuracy
        def role_acc(role: str, getter) -> dict:
            n = ok = 0
            for x in L:
                g = {f["normalized"] for f in x["facts"] if f["type"] == "date" and f["role"] == role}
                if not g:
                    continue
                n += 1
                ok += int(getter(x) == g)
            return {"n": n, "exact": ok, "accuracy": round(ok / n, 4) if n else None}

        def rule_role(role):
            return lambda x: {f["normalized"] for f in recs[x["id"]]["rule_facts"] if f["type"] == "date" and f["role"] == role}

        def merged_role(role):
            return lambda x: {f["normalized"] for f in recs[x["id"]]["merged_facts"] if f["type"] == "date" and f["role"] == role}

        def llm_role(role):
            def g(x):
                raw = recs[x["id"]]["llm_raw"] or {}
                return {n for d in raw.get("dates") or [] if isinstance(d, dict) and d.get("role") == role
                        for n in [_normalize("date", str(d.get("text")), None)] if n}
            return g

        out[split] = {
            "n_letters": len(L),
            "deterministic": extraction_scores(rules, gold),
            "apertus_only": extraction_scores(llm, gold),
            "merged": extraction_scores(merged, gold),
            "deadline_role": {"deterministic": role_acc("deadline", rule_role("deadline")),
                              "apertus_only": role_acc("deadline", llm_role("deadline")),
                              "merged": role_acc("deadline", merged_role("deadline"))},
            "appointment_role": {"deterministic": role_acc("appointment", rule_role("appointment")),
                                 "apertus_only": role_acc("appointment", llm_role("appointment")),
                                 "merged": role_acc("appointment", merged_role("appointment"))},
            "letter_type_accuracy": {
                "keyword_baseline": round(sum(recs[x["id"]]["keyword_letter_type"] == x["letter_type"] for x in L) / max(1, len(L)), 4),
                "apertus": round(sum((recs[x["id"]]["llm_raw"] or {}).get("letter_type") == x["letter_type"] for x in L) / max(1, len(L)), 4),
            },
            "llm_json_ok": sum(1 for x in L if recs[x["id"]]["llm_ok"]),
            "ungrounded_llm_values": sum(sum(1 for d in recs[x["id"]]["disagreements"] if d["kind"] == "ungrounded") for x in L),
            "llm_only_values": sum(sum(1 for d in recs[x["id"]]["disagreements"] if d["kind"] == "llm_only") for x in L),
            "language_detection_accuracy": round(sum(recs[x["id"]]["detected_lang"] == x["lang"] for x in L) / max(1, len(L)), 4),
        }
    return out


# ------------------------------------------------------------------------------ explain

def _naive(client: CachedClient, text: str, tgt: str) -> dict:
    s = get_settings()
    t0 = time.time()
    r = client.chat_guarded(naive_messages(text, tgt), task="naive", max_tokens=s.max_tokens_translate)
    return {"output": r.text, "usage": r.usage(), "finish": r.finish_reason, "wall_s": round(time.time() - t0, 2)}


def stage_explain(client: CachedClient, letters: list[dict], langs: list[str]) -> None:
    done = {(r["id"], r["target"]) for r in _jsonl_read(EXPLAIN_ITEMS)}
    total = len(letters) * len(langs)
    k = 0
    for L in letters:
        a = None
        for tgt in langs:
            k += 1
            if (L["id"], tgt) in done:
                continue
            if a is None:
                a = analyze(L["text"], client=client)  # cached from the extract stage
            t0 = time.time()
            try:
                fl = explain(a, tgt, client)
                nv = _naive(client, a.text, tgt)
            except Exception as exc:  # backend hiccup (e.g. OOM on a shared laptop): wait, skip, resume later
                _log(f"explain {k}/{total} {L['id']}->{tgt} FAILED: {str(exc)[:160]}; skipping (rerun to resume)")
                time.sleep(30)
                continue
            gt_facts = L["facts"]
            rec = {
                "id": L["id"], "split": L["split"], "lang": L["lang"], "letter_type": L["letter_type"], "target": tgt,
                "factlock": {
                    "explanation": fl["explanation"], "masked": fl["masked"], "source_plain": fl["source_plain"],
                    "source_plain_masked": fl["source_plain_masked"], "source_plain_repaired": fl["source_plain_repaired"],
                    "back_translation": fl["back_translation"], "back_translation_masked": fl["back_translation_masked"],
                    "chrf": fl["chrf"], "placeholder_audit": fl["placeholder_audit"],
                    "number_audit": fl["number_audit"], "script_check": fl["script_check"], "degenerate": fl["degenerate"],
                    "gate_at_runtime": fl["gate"], "timings": fl["timings"], "tokens": fl["tokens"],
                    "preservation": preservation(gt_facts, fl["explanation"], tgt, L["lang"]),
                    "hallucinated_numbers": unexpected_numbers(fl["explanation"], a.text, a.facts),
                },
                "naive": {
                    **nv,
                    "preservation": preservation(gt_facts, nv["output"], tgt, L["lang"]),
                    "hallucinated_numbers": unexpected_numbers(nv["output"], a.text, a.facts),
                    "degenerate": nv["finish"] in {"degenerate", "length"} or is_degenerate(nv["output"]),
                    "script_check": check_output_language(nv["output"], tgt, L["lang"]),
                },
                "wall_s": round(time.time() - t0, 2),
                "prompt_version": PROMPT_VERSION,
            }
            _jsonl_append(EXPLAIN_ITEMS, rec)
            _log(f"explain {k}/{total} {L['id']}->{tgt} chrF={fl['chrf']} gate={fl['gate']['status']} "
                 f"FL={rec['factlock']['preservation']['rate']} naive={rec['naive']['preservation']['rate']} {rec['wall_s']}s")


# -------------------------------------------------------------------------------- judge

JUDGE_SYSTEM = "You are a strict, careful evaluator of translations of official letters."
JUDGE_USER = """Text A is a plain-language explanation of an official letter, written in {lang}. Text B was produced by translating A into another language and then translating it back into {lang} (a round trip). Placeholders such as ⟦D1⟧ stand for facts; ignore them.

Text A:
<<<
{a}
>>>

Text B:
<<<
{b}
>>>

Does B convey the same information as A? Pay attention to who must do what, by when, and what happens otherwise.
Scores: 5 = same meaning; 4 = only minor wording differences; 3 = some information missing or slightly wrong; 2 = important information missing or wrong; 1 = meaningless or unrelated.
Answer only with JSON: {{"score": <1-5>, "issues": "<at most 15 words>"}}"""


def stage_judge(judge_model: str, items: list[dict]) -> None:
    s = get_settings()
    js = replace(s, llm_name=judge_model)
    client = CachedClient(CACHE, js)
    done = {(r["id"], r["target"]) for r in _jsonl_read(JUDGE_ITEMS)}
    for i, it in enumerate(items):
        if (it["id"], it["target"]) in done:
            continue
        fl = it["factlock"]
        if fl["back_translation_masked"] in (None, ""):
            rec = {"id": it["id"], "target": it["target"], "score": 1 if fl["degenerate"] else None, "issues": "no back-translation"}
        else:
            lang = LANGUAGES[it["lang"]].name
            msgs = [{"role": "system", "content": JUDGE_SYSTEM},
                    {"role": "user", "content": JUDGE_USER.format(lang=lang, a=fl["source_plain_masked"], b=fl["back_translation_masked"])}]
            r = client.chat(msgs, task="judge", max_tokens=80, temperature=0.0)
            obj = parse_json_lenient(r.text) or {}
            score = obj.get("score")
            try:
                score = int(score)
            except (TypeError, ValueError):
                score = None
            rec = {"id": it["id"], "target": it["target"], "score": score, "issues": str(obj.get("issues", ""))[:200],
                   "judge_model": judge_model}
        _jsonl_append(JUDGE_ITEMS, rec)
        if i % 20 == 0:
            _log(f"judge {i + 1}/{len(items)} {it['id']}->{it['target']} score={rec['score']}")


# --------------------------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["extract", "explain", "judge", "calibrate", "score", "all"])
    ap.add_argument("--langs", default=",".join(EVAL_LANGS))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--test-letters", type=int, default=12,
                    help="test letters for the explanation ablation (one per letter type, source languages rotated)")
    ap.add_argument("--judge-model", default=os.environ.get("JUDGE_MODEL", "llama3:latest"))
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    RUNS.mkdir(parents=True, exist_ok=True)
    langs = [x for x in args.langs.split(",") if x]
    stages = ["extract", "explain", "judge", "calibrate", "score"] if args.stage == "all" else [args.stage]
    gpu = GpuSampler().start()
    run_log = RUNS / "run_log.jsonl"
    try:
        for st in stages:
            t0 = time.time()
            client = CachedClient(CACHE)
            n_before = len(client.cache)
            if st == "extract":
                letters = load_letters()
                stage_extract(client, letters[: args.limit or None])
            elif st == "explain":
                letters = load_letters("explain")
                from .letter_templates import LETTER_TYPES

                # one test letter per type; source language = the one after its dev language -> 4 DE / 4 FR / 4 IT
                keep = {f"{t}_{('de', 'fr', 'it')[(i + 1) % 3]}_0" for i, t in enumerate(LETTER_TYPES)}
                keep = set(sorted(keep)[: args.test_letters])
                letters = [x for x in letters if x["split"] == "dev" or x["id"] in keep]
                letters.sort(key=lambda x: (x["split"] != "dev", x["id"]))  # dev first (needed for calibration)
                stage_explain(client, letters[: args.limit or None], langs)
            elif st == "judge":
                stage_judge(args.judge_model, _jsonl_read(EXPLAIN_ITEMS))
            elif st == "calibrate":
                from .calibrate import calibrate

                calibrate()
            elif st == "score":
                from .score import score

                score()
            fresh = [e for e in client.cache.values()][n_before:]
            _jsonl_append(run_log, {"stage": st, "start": t0, "end": time.time(), "fresh_calls": len(fresh),
                                    "model": get_settings().llm_name, "prompt_version": PROMPT_VERSION,
                                    "gpu_energy_wh_fresh_calls": energy_from_cache(fresh, gpu.samples),
                                    "gpu": gpu.summary()})
    finally:
        gpu.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
