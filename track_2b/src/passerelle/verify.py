"""Verification: round-trip chrF, placeholder audit, number audit, script check and the confidence gate.

Gate statuses (ordered): ``ready`` (✅ Ready) < ``review`` (⚠️ Review with client) <
``interpreter`` (⛔ Use a human interpreter).

Rules (each can only *raise* the status):
* chrF(back-translation, source plain explanation) below the language's ``review`` threshold → interpreter;
  below its ``ready`` threshold → review.  chrF is computed on DE/FR/IT text, so values are comparable
  across target languages; thresholds are calibrated on the dev split (see eval/calibrate.py).
* Output not in the expected script / language → interpreter.
* A critical placeholder missing in the translation → review (the fact card still shows the fact).
* A placeholder the model invented → review.  Numbers that are not in the letter → review.
* Per-language ``floor`` from calibration (e.g. languages that failed on dev) → at least that status.
* Duplicated placeholders are informational only (the value re-inserted twice is still correct).
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import sacrebleu

from .config import get_settings
from .facts import Fact, render_fact
from .ingest import to_ascii_digits

STATUS_ORDER = ["ready", "review", "interpreter"]
STATUS_LABEL = {"ready": "Ready", "review": "Review with client", "interpreter": "Use a human interpreter"}
DEFAULT_THRESHOLDS = {"ready": 50.0, "review": 35.0, "floor": "ready"}


def chrf(hypothesis: str, reference: str) -> float:
    if not hypothesis.strip() or not reference.strip():
        return 0.0
    return round(sacrebleu.sentence_chrf(hypothesis, [reference]).score, 2)


# ------------------------------------------------------------------------ number audit

_NUM = re.compile(r"\d+(?:[’'.,:/-]\d+|\s\d{3}(?!\d))*")


def numeric_tokens(text: str) -> list[str]:
    return [m.group(0) for m in _NUM.finditer(to_ascii_digits(text))]


def _compact(tok: str) -> str:
    tok = re.sub(r"[.,]0{1,2}$", "", tok.strip())
    return re.sub(r"\D", "", tok)


def source_number_sets(source_text: str, facts: list[Fact]) -> tuple[set[str], set[str]]:
    toks = numeric_tokens(source_text)
    for f in facts:
        toks.append(f.normalized if f.type != "duration" else str(f.meta.get("count", "")))
        toks.append(render_fact(f))
        if f.type == "date":
            y, m, d = f.normalized.split("-")
            toks += [f"{int(d)}.{int(m)}.{y}", f"{d}/{m}/{y}", f"{y}{m}{d}", f"{int(d)}", f"{int(m)}"]
    compact = {_compact(t) for t in toks if _compact(t)}
    runs = set()
    for t in toks:
        runs.update(re.findall(r"\d+", to_ascii_digits(t)))
    return compact, runs


def unexpected_numbers(output: str, source_text: str, facts: list[Fact],
                       ignore_spans: list[tuple[int, int]] | None = None) -> list[str]:
    """Numbers (>= 2 digits) in ``output`` that cannot be traced back to the letter."""
    if ignore_spans:
        chars = list(output)
        for s, e in ignore_spans:
            for i in range(max(0, s), min(len(chars), e)):
                chars[i] = " "
        output = "".join(chars)
    compact, runs = source_number_sets(source_text, facts)
    bad = []
    for tok in numeric_tokens(output):
        c = _compact(tok)
        if len(c) < 2 or c in compact:
            continue
        tok_runs = re.findall(r"\d+", tok)
        if all(r in runs or len(r) < 2 for r in tok_runs):
            continue
        bad.append(tok)
    return bad


# ---------------------------------------------------------------------------- the gate

@lru_cache(maxsize=4)
def _load_thresholds(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"default": DEFAULT_THRESHOLDS, "languages": {}, "calibrated": False}
    return json.loads(p.read_text(encoding="utf-8"))


def thresholds_for(lang: str) -> dict:
    data = _load_thresholds(str(get_settings().thresholds_path))
    base = dict(DEFAULT_THRESHOLDS)
    base.update(data.get("default") or {})
    base.update((data.get("languages") or {}).get(lang) or {})
    base["calibrated"] = bool(data.get("calibrated"))
    return base


def all_thresholds() -> dict:
    return _load_thresholds(str(get_settings().thresholds_path))


def _raise(status: str, new: str) -> str:
    return new if STATUS_ORDER.index(new) > STATUS_ORDER.index(status) else status


def decide(lang: str, chrf_score: float | None, placeholder_audit: dict, number_issues: list[str],
           script_check: dict | None, thresholds: dict | None = None, degenerate: bool = False) -> dict:
    th = thresholds or thresholds_for(lang)
    status = "ready"
    reasons: list[dict] = []

    def add(code: str, sev: str, msg: str) -> None:
        nonlocal status
        reasons.append({"code": code, "severity": sev, "message": msg})
        if sev in STATUS_ORDER:
            status = _raise(status, sev)

    if degenerate:
        add("degenerate_output", "interpreter", "The model output broke down (repetition loop or length limit).")
    if script_check is not None and not script_check.get("ok", True):
        add("wrong_script_or_language", "interpreter",
            f"Output is not reliably in the target language (script ratio {script_check.get('script_ratio')}, "
            f"detected {script_check.get('detected')}).")
    if chrf_score is not None:
        if chrf_score < th["review"]:
            add("low_roundtrip", "interpreter",
                f"Round-trip meaning check failed: chrF {chrf_score:.1f} < {th['review']:.1f}.")
        elif chrf_score < th["ready"]:
            add("medium_roundtrip", "review",
                f"Round-trip meaning check is borderline: chrF {chrf_score:.1f} < {th['ready']:.1f}.")
    if placeholder_audit.get("missing"):
        add("fact_missing", "review", "Critical facts missing from the explanation: " + ", ".join(placeholder_audit["missing"]))
    if placeholder_audit.get("unexpected"):
        add("unexpected_placeholder", "review", "Unknown fact placeholders: " + ", ".join(placeholder_audit["unexpected"]))
    if number_issues:
        add("unexpected_numbers", "review", "Numbers not found in the letter: " + ", ".join(number_issues[:6]))
    if placeholder_audit.get("duplicated"):
        add("duplicated_placeholder", "info", "Some facts are mentioned more than once (values verified).")
    floor = th.get("floor", "ready")
    if floor in STATUS_ORDER and STATUS_ORDER.index(floor) > STATUS_ORDER.index(status):
        add("language_floor", floor, th.get("floor_reason") or f"Measured quality for this language requires at least '{STATUS_LABEL[floor]}'.")
    if not th.get("calibrated", False):
        reasons.append({"code": "uncalibrated", "severity": "info", "message": "Gate thresholds are defaults (not calibrated)."})
    return {
        "status": status,
        "label": STATUS_LABEL[status],
        "reasons": [r["message"] for r in reasons if r["severity"] != "info"] or
                   ([] if status != "ready" else ["All checks passed."]),
        "details": reasons,
        "thresholds": {"ready": th["ready"], "review": th["review"], "floor": floor},
    }
