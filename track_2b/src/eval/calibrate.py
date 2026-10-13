"""Calibrate the confidence gate on the DEV split only (never on test).

Labels for a fact-lock output (dev item):
  broken       degenerate output or wrong script/language
  fact_error   a ground-truth critical fact is not rendered exactly in the final explanation
  meaning_bad  helper judge score <= 2 on the round trip (source plain explanation vs back-translation)
  not_good     broken or fact_error or judge <= 3
Thresholds on chrF (computed in DE/FR/IT, hence comparable across target languages):
  review  (below -> interpreter): maximises F2 for detecting broken|meaning_bad on pooled dev
  ready   (below -> review):      maximises F1 for detecting not_good on pooled dev, ready >= review
Per language: own ``review`` threshold (within ±10 of the pooled one) only if its dev items contain
>= 3 bad and >= 3 good examples; a ``floor`` of review/interpreter if >= 25 % / >= 50 % of its dev
outputs are broken or meaning_bad.  Output: passerelle/resources/gate_thresholds.json + calibration.json.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from passerelle.config import PACKAGE_DIR
from passerelle.languages import LANGUAGES

from .harness import RUNS, load_letters
from .metrics import preservation

THRESHOLDS_OUT = PACKAGE_DIR / "resources" / "gate_thresholds.json"


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def item_labels(it: dict, gt: dict, judge: dict) -> dict:
    fl = it["factlock"]
    pres = preservation(gt["facts"], fl["explanation"], it["target"], it["lang"])
    js = judge.get((it["id"], it["target"]))
    broken = bool(fl["degenerate"]) or not fl["script_check"].get("ok", True)
    fact_error = pres["rate"] is not None and pres["rate"] < 1.0
    meaning_bad = js is not None and js <= 2
    return {
        "chrf": fl["chrf"] if fl["chrf"] is not None else 0.0,
        "judge": js, "broken": broken, "fact_error": fact_error, "meaning_bad": meaning_bad,
        "bad": broken or meaning_bad,
        "not_good": broken or fact_error or (js is not None and js <= 3),
        "preservation": pres,
    }


def _fbeta(tp, fp, fn, beta):
    if tp == 0:
        return 0.0
    p, r = tp / (tp + fp), tp / (tp + fn)
    b2 = beta * beta
    return (1 + b2) * p * r / (b2 * p + r)


def best_threshold(items: list[dict], label: str, beta: float, lo: float = 0.0, hi: float = 100.0) -> tuple[float, float]:
    best_t, best_f = lo, -1.0
    t = lo
    while t <= hi:
        tp = sum(1 for x in items if x["chrf"] < t and x[label])
        fp = sum(1 for x in items if x["chrf"] < t and not x[label])
        fn = sum(1 for x in items if x["chrf"] >= t and x[label])
        f = _fbeta(tp, fp, fn, beta)
        if f > best_f + 1e-9:
            best_t, best_f = t, f
        t += 0.5
    return round(best_t, 1), round(best_f, 4)


def calibrate() -> dict:
    letters = {x["id"]: x for x in load_letters()}
    items = [it for it in _read(RUNS / "explain_items.jsonl") if it["split"] == "dev"]
    judge = {(j["id"], j["target"]): j["score"] for j in _read(RUNS / "judge_items.jsonl")}
    if not items:
        raise SystemExit("no dev explain items — run the explain stage first")
    labelled = []
    for it in items:
        lab = item_labels(it, letters[it["id"]], judge)
        lab.update({"id": it["id"], "target": it["target"]})
        labelled.append(lab)
    have_judge = any(x["judge"] is not None for x in labelled)
    review_t, review_f = best_threshold(labelled, "bad", beta=2.0)
    ready_t, ready_f = best_threshold(labelled, "not_good", beta=1.0, lo=review_t)
    langs: dict[str, dict] = {}
    for code in sorted({x["target"] for x in labelled}):
        L = [x for x in labelled if x["target"] == code]
        n_bad = sum(x["bad"] for x in L)
        n_good = sum(not x["not_good"] for x in L)
        bad_rate = n_bad / len(L)
        entry: dict = {"ready": ready_t, "review": review_t}
        if n_bad >= 3 and n_good >= 3:
            t, f = best_threshold(L, "bad", beta=2.0, lo=max(0.0, review_t - 10), hi=min(100.0, review_t + 10))
            entry["review"] = t
            entry["ready"] = max(ready_t, t)
            entry["fit"] = "language"
        else:
            entry["fit"] = "pooled"
        if bad_rate >= 0.5:
            entry["floor"], entry["tier"] = "interpreter", "interpreter_recommended"
        elif bad_rate >= 0.25:
            entry["floor"], entry["tier"] = "review", "review_required"
        else:
            entry["floor"], entry["tier"] = "ready", "reliable"
        entry["floor_reason"] = (f"On the dev split {n_bad}/{len(L)} outputs for {LANGUAGES[code].name} were broken or "
                                 f"judged wrong in meaning.") if entry["floor"] != "ready" else None
        chrfs = sorted(x["chrf"] for x in L)
        js = [x["judge"] for x in L if x["judge"] is not None]
        entry["dev_stats"] = {
            "n": len(L), "bad": n_bad, "good": n_good, "bad_rate": round(bad_rate, 3),
            "chrf_mean": round(sum(chrfs) / len(chrfs), 2), "chrf_median": chrfs[len(chrfs) // 2],
            "judge_mean": round(sum(js) / len(js), 2) if js else None,
            "fact_error_rate": round(sum(x["fact_error"] for x in L) / len(L), 3),
        }
        langs[code] = entry
    out = {
        "calibrated": True,
        "calibrated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "split": "dev",
        "n_items": len(labelled),
        "judge_available": have_judge,
        "metric": "chrF(back-translation, source plain explanation), placeholders stripped, sacrebleu sentence_chrf",
        "method": "pooled F2 (review) / F1 (ready) on dev; per-language review threshold if >=3 bad and >=3 good dev items; floors from dev bad rate",
        "default": {"ready": ready_t, "review": review_t, "floor": "ready"},
        "pooled_fit": {"review_f2": review_f, "ready_f1": ready_f},
        "languages": langs,
    }
    THRESHOLDS_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (RUNS / "calibration.json").write_text(json.dumps({**out, "items": labelled}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"calibrated on {len(labelled)} dev items: review<{review_t} ready<{ready_t}; floors: "
          + ", ".join(f"{k}={v['floor']}" for k, v in langs.items()))
    return out


if __name__ == "__main__":
    calibrate()
