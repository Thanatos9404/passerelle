"""Score the TEST split and write data/eval_runs/summary.json (+ per-item scored file).

All metrics are recomputed from the stored raw model outputs with the current metric code; the gate is
re-applied with the thresholds calibrated on the dev split (eval/calibrate.py).  Nothing here calls a model.
"""

from __future__ import annotations

import json
import statistics as stats
import time
from pathlib import Path

from passerelle.extract import merge
from passerelle.factlock import audit, find_placeholders, unmask
from passerelle.facts import extract_facts
from passerelle.languages import LANGUAGES
from passerelle.verify import decide, unexpected_numbers

from .calibrate import THRESHOLDS_OUT, item_labels
from .harness import RUNS, load_letters
from .metrics import EVAL_TYPES, extraction_scores, key, preservation
from .run_eval import llm_only_keys

ELECTRICITY_CHF_PER_KWH = 0.30   # assumption (Swiss household tariffs ~0.25-0.35 CHF/kWh in 2025/26)
LAPTOP_CHF_PER_HOUR = 0.30       # assumption: ~CHF 1'500 laptop over 3 years x ~1'700 working hours
INTERPRETER_CHF_PER_HOUR = (50, 130)  # assumption, hedged range for community interpreting; not a cited tariff


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 4) if xs else None


def _median(xs):
    xs = [x for x in xs if x is not None]
    return round(stats.median(xs), 2) if xs else None


def _pr(pred: list[bool], gold: list[bool]) -> dict:
    tp = sum(p and g for p, g in zip(pred, gold))
    fp = sum(p and not g for p, g in zip(pred, gold))
    fn = sum(g and not p for p, g in zip(pred, gold))
    tn = sum((not p) and (not g) for p, g in zip(pred, gold))
    return {"precision": round(tp / (tp + fp), 4) if tp + fp else None, "recall": round(tp / (tp + fn), 4) if tp + fn else None,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn}


# ------------------------------------------------------------------------------- extraction

def score_extraction(letters: dict[str, dict]) -> dict:
    recs = {r["id"]: r for r in _read(RUNS / "extraction_items.jsonl")}
    out = {}
    for split in ("test", "dev"):
        L = [x for x in letters.values() if x["split"] == split and x["id"] in recs]
        gold, rules, llm, merged, roles = {}, {}, {}, {}, {"deterministic": [], "apertus_only": [], "merged": []}
        types_ok = {"keyword": 0, "apertus": 0}
        for x in L:
            r = recs[x["id"]]
            rf = extract_facts(x["text"])
            mf, card, dis = merge(x["text"], rf, r["llm_raw"])
            gold[x["id"]] = {key(f["type"], f["normalized"]) for f in x["facts"] if f["type"] in EVAL_TYPES}
            rules[x["id"]] = {key(f.type, f.normalized) for f in rf if f.type in EVAL_TYPES}
            llm[x["id"]] = llm_only_keys(r["llm_raw"])
            merged[x["id"]] = {key(f.type, f.normalized) for f in mf if f.type in EVAL_TYPES}
            g_dead = {f["normalized"] for f in x["facts"] if f["type"] == "date" and f["role"] == "deadline"}
            if g_dead:
                raw = r["llm_raw"] or {}
                from passerelle.extract import _normalize

                llm_dead = {n for d in raw.get("dates") or [] if isinstance(d, dict) and d.get("role") == "deadline"
                            for n in [_normalize("date", str(d.get("text")), None)] if n}
                roles["deterministic"].append({f.normalized for f in rf if f.type == "date" and f.role == "deadline"} == g_dead)
                roles["apertus_only"].append(llm_dead == g_dead)
                roles["merged"].append({f.normalized for f in mf if f.type == "date" and f.role == "deadline"} == g_dead)
            types_ok["keyword"] += r["keyword_letter_type"] == x["letter_type"]
            types_ok["apertus"] += (r["llm_raw"] or {}).get("letter_type") == x["letter_type"]
        out[split] = {
            "n_letters": len(L),
            "deterministic": extraction_scores(rules, gold),
            "apertus_only": extraction_scores(llm, gold),
            "merged": extraction_scores(merged, gold),
            "deadline_role_accuracy": {k: {"n": len(v), "accuracy": _mean([float(b) for b in v])} for k, v in roles.items()},
            "letter_type_accuracy": {k: round(v / max(1, len(L)), 4) for k, v in types_ok.items()},
            "apertus_json_valid": sum(1 for x in L if recs[x["id"]]["llm_ok"]),
            "language_detection_accuracy": _mean([float(recs[x["id"]]["detected_lang"] == x["lang"]) for x in L]),
        }
    return out


# ------------------------------------------------------------------------------ explanation

def score_explanations(letters: dict[str, dict]) -> tuple[dict, list[dict]]:
    items = _read(RUNS / "explain_items.jsonl")
    judge = {(j["id"], j["target"]): j["score"] for j in _read(RUNS / "judge_items.jsonl")}
    thresholds = json.loads(THRESHOLDS_OUT.read_text(encoding="utf-8")) if THRESHOLDS_OUT.exists() else {}
    scored = []
    facts_cache: dict[str, list] = {}
    merged_cache: dict[str, dict] = {}
    extraction = {r["id"]: r for r in _read(RUNS / "extraction_items.jsonl")}
    reunmask_changed = 0
    for it in items:
        gt = letters[it["id"]]
        if it["id"] not in facts_cache:
            facts_cache[it["id"]] = extract_facts(gt["text"])
            mf, _, _ = merge(gt["text"], facts_cache[it["id"]], (extraction.get(it["id"]) or {}).get("llm_raw"))
            merged_cache[it["id"]] = {f.id: f for f in mf}
        rf = facts_cache[it["id"]]
        fl, nv = it["factlock"], it["naive"]
        # re-apply the current unmasking/audit code to the stored masked model output
        by_id = merged_cache[it["id"]]
        explanation, _ = unmask(fl["masked"], by_id)
        if explanation != fl["explanation"]:
            reunmask_changed += 1
            fl = {**fl, "explanation": explanation}
            in_src = {h.fid for h in find_placeholders(fl["source_plain_masked"], set(by_id)) if h.fid in by_id}
            crit = {f.id for f in by_id.values() if f.critical}
            fl["placeholder_audit"] = audit(fl["masked"], by_id, required=in_src & crit, offered=in_src).to_dict()
            it = {**it, "factlock": fl}
        lab = item_labels(it, gt, judge)
        fl_halluc = unexpected_numbers(fl["explanation"], gt["text"], rf)
        nv_halluc = unexpected_numbers(nv["output"], gt["text"], rf)
        th_lang = dict(thresholds.get("default", {}))
        th_lang.update((thresholds.get("languages") or {}).get(it["target"], {}))
        th_lang["calibrated"] = bool(thresholds.get("calibrated"))
        number_issues = unexpected_numbers(fl["explanation"], gt["text"], rf)
        gate = decide(it["target"], fl["chrf"], fl["placeholder_audit"], number_issues, fl["script_check"], th_lang,
                      degenerate=fl["degenerate"])
        gate_nofloor = decide(it["target"], fl["chrf"], fl["placeholder_audit"], number_issues, fl["script_check"],
                              {**th_lang, "floor": "ready"}, degenerate=fl["degenerate"])
        scored.append({
            "id": it["id"], "split": it["split"], "lang": it["lang"], "letter_type": it["letter_type"], "target": it["target"],
            "group": LANGUAGES[it["target"]].eval_group,
            "naive": {"preservation": preservation(gt["facts"], nv["output"], it["target"], it["lang"]),
                      "hallucinated": nv_halluc, "degenerate": nv["degenerate"], "script_ok": nv["script_check"].get("ok", True),
                      "latency_ms": nv["usage"].get("latency_ms"), "completion_tokens": nv["usage"].get("completion")},
            "factlock": {"preservation": lab["preservation"], "hallucinated": fl_halluc, "degenerate": fl["degenerate"],
                         "script_ok": fl["script_check"].get("ok", True), "chrf": fl["chrf"], "judge": lab["judge"],
                         "gate": gate["status"], "gate_reasons": [r["code"] for r in gate["details"]],
                         "gate_nofloor": gate_nofloor["status"], "source_repaired": len(fl["source_plain_repaired"]),
                         "placeholders_missing": len(fl["placeholder_audit"]["missing"]),
                         "placeholders_repaired": len(fl["placeholder_audit"].get("repaired", [])),
                         "timings": fl["timings"], "tokens": fl["tokens"]},
            "labels": {k: lab[k] for k in ("broken", "fact_error", "meaning_bad", "bad", "not_good")},
        })
    (RUNS / "explain_scored.jsonl").write_text("\n".join(json.dumps(s, ensure_ascii=False) for s in scored) + "\n", encoding="utf-8")

    def agg(rows: list[dict]) -> dict:
        if not rows:
            return {}
        def cond(c):
            pres = [r[c]["preservation"]["rate"] for r in rows]
            return {
                "fact_preservation": _mean(pres),
                "all_critical_facts_ok": _mean([float(p == 1.0) for p in pres if p is not None]),
                "outputs_with_hallucinated_number": _mean([float(bool(r[c]["hallucinated"])) for r in rows]),
                "hallucinated_numbers_per_output": _mean([float(len(r[c]["hallucinated"])) for r in rows]),
                "degenerate_rate": _mean([float(r[c]["degenerate"]) for r in rows]),
                "wrong_script_rate": _mean([float(not r[c]["script_ok"]) for r in rows]),
            }
        fl = cond("factlock")
        fl.update({
            "chrf_mean": _mean([r["factlock"]["chrf"] for r in rows]),
            "chrf_median": _median([r["factlock"]["chrf"] for r in rows]),
            "judge_mean": _mean([r["factlock"]["judge"] for r in rows]),
            "gate": {s: _mean([float(r["factlock"]["gate"] == s) for r in rows]) for s in ("ready", "review", "interpreter")},
            "gate_without_floor": {s: _mean([float(r["factlock"]["gate_nofloor"] == s) for r in rows]) for s in ("ready", "review", "interpreter")},
            "bad_rate": _mean([float(r["labels"]["bad"]) for r in rows]),
            "source_plain_needed_key_facts_line": _mean([float(r["factlock"]["source_repaired"] > 0) for r in rows]),
        })
        return {"n": len(rows), "naive": cond("naive"), "factlock": fl}

    test = [s for s in scored if s["split"] == "test"]
    per_lang = {code: agg([s for s in test if s["target"] == code]) for code in sorted({s["target"] for s in test})}
    groups = {
        "all": agg(test),
        "low_mid_resource": agg([s for s in test if s["group"] == "low_mid"]),
        "controls": agg([s for s in test if s["group"] == "control"]),
    }

    def gate_eval(rows, field):
        flagged = [r["factlock"][field] != "ready" for r in rows]
        interp = [r["factlock"][field] == "interpreter" for r in rows]
        bad = [r["labels"]["bad"] for r in rows]
        any_problem = [r["labels"]["bad"] or r["labels"]["fact_error"] for r in rows]
        meaning = [r["labels"]["meaning_bad"] for r in rows]
        return {
            "flagged_vs_bad": _pr(flagged, bad),
            "flagged_vs_any_problem": _pr(flagged, any_problem),
            "interpreter_vs_bad": _pr(interp, bad),
            "flagged_vs_judge_meaning_bad": _pr(flagged, meaning),
            "ready_outputs_that_are_bad": sum(1 for f, b in zip(flagged, bad) if not f and b),
            "ready_outputs": sum(1 for f in flagged if not f),
        }

    gate = {
        "definitions": {
            "bad": "degenerate or wrong-script output, or helper-judge round-trip score <= 2",
            "any_problem": "bad, or any ground-truth critical fact not rendered exactly",
            "flagged": "gate status review or interpreter",
        },
        "with_language_floor": gate_eval(test, "gate"),
        "without_language_floor": gate_eval(test, "gate_nofloor"),
        "confusion": {f"{st}|{'bad' if b else 'ok'}": sum(1 for r in test if r["factlock"]["gate"] == st and r["labels"]["bad"] == b)
                      for st in ("ready", "review", "interpreter") for b in (True, False)},
    }
    return {"per_language": per_lang, "groups": groups, "gate": gate, "n_test_items": len(test),
            "n_dev_items": len([s for s in scored if s["split"] == "dev"]),
            "items_reunmasked_with_current_code": reunmask_changed}, scored


# ---------------------------------------------------------------------------------- speed

def score_speed(scored: list[dict], model: str) -> dict:
    cache = [json.loads(x) for x in (RUNS / "llm_cache.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    by_task: dict[str, list] = {}
    for e in cache:
        if e["model"] != model:
            continue
        r = e["result"]
        by_task.setdefault(e["task"], []).append((r.get("latency_ms") or 0, r.get("completion_tokens") or 0, r.get("prompt_tokens") or 0))
    tasks = {}
    for t, rows in by_task.items():
        lat = [a for a, _, _ in rows]
        comp = [c for _, c, _ in rows]
        tasks[t] = {"calls": len(rows), "mean_latency_s": round(sum(lat) / len(lat) / 1000, 2),
                    "mean_completion_tokens": round(sum(comp) / len(comp), 1),
                    "mean_prompt_tokens": round(sum(p for _, _, p in rows) / len(rows), 1),
                    "tokens_per_s_end_to_end": round(sum(comp) / (sum(lat) / 1000), 2) if sum(lat) else None}
    runs = _read(RUNS / "run_log.jsonl")
    energy = {}
    for st in ("extract", "explain"):
        rs = [r for r in runs if r["stage"] == st and r.get("fresh_calls")]
        wh = sum(r.get("gpu_energy_wh_fresh_calls") or 0 for r in rs)
        calls = sum(r["fresh_calls"] for r in rs)
        powers = [r["gpu"].get("mean_w") for r in rs if r.get("gpu", {}).get("available")]
        energy[st] = {"fresh_calls": calls, "gpu_energy_wh": round(wh, 2), "mean_gpu_power_w": _mean(powers)}
    ex = tasks.get("extract", {}).get("mean_latency_s") or 0
    sp = tasks.get("explain_source", {}).get("mean_latency_s") or 0
    tr = tasks.get("translate", {}).get("mean_latency_s") or 0
    bt = tasks.get("back_translate", {}).get("mean_latency_s") or 0
    per_lang = ex + sp + tr + bt   # one letter, one target language, end to end
    calls_per_item = 4
    wh_per_call = (energy["explain"]["gpu_energy_wh"] / energy["explain"]["fresh_calls"]) if energy["explain"]["fresh_calls"] else None
    wh_item = wh_per_call * calls_per_item if wh_per_call else None
    chf_energy = (wh_item / 1000 * ELECTRICITY_CHF_PER_KWH) if wh_item else None
    chf_hw = per_lang / 3600 * LAPTOP_CHF_PER_HOUR
    return {
        "hardware": "NVIDIA RTX 4050 Laptop GPU (6 GB), Apertus v1.5 8B Q4_K_M GGUF, Ollama (llama.cpp), 33/33 layers on GPU, flash attention, q8_0 KV cache, ctx 4096",
        "by_task": tasks,
        "seconds_per_letter_and_language": round(per_lang, 1),
        "seconds_breakdown": {"extract": ex, "source_plain": sp, "translate": tr, "back_translate": bt},
        "energy": energy,
        "wh_per_letter_and_language_estimate": round(wh_item, 3) if wh_item else None,
        "cost_chf_per_letter_and_language_estimate": {
            "electricity": round(chf_energy, 5) if chf_energy else None,
            "laptop_amortisation": round(chf_hw, 4),
            "assumptions": {"electricity_chf_per_kwh": ELECTRICITY_CHF_PER_KWH, "laptop_chf_per_hour": LAPTOP_CHF_PER_HOUR},
        },
        "human_interpreter_chf_per_hour_assumed_range": INTERPRETER_CHF_PER_HOUR,
        "note": "Interpreter range is an assumption for orientation only, not a cited tariff; Passerelle does not replace interpreters for outputs the gate routes to them.",
    }


def score() -> dict:
    from passerelle.config import get_settings

    letters = {x["id"]: x for x in load_letters()}
    extraction = score_extraction(letters)
    expl, scored = score_explanations(letters)
    speed = score_speed(scored, get_settings().llm_name)
    thresholds = json.loads(THRESHOLDS_OUT.read_text(encoding="utf-8")) if THRESHOLDS_OUT.exists() else {}
    g = expl["groups"]
    head = {
        "fact_preservation_low_mid": {"naive": g["low_mid_resource"].get("naive", {}).get("fact_preservation"),
                                      "factlock": g["low_mid_resource"].get("factlock", {}).get("fact_preservation")},
        "fact_preservation_all": {"naive": g["all"].get("naive", {}).get("fact_preservation"),
                                  "factlock": g["all"].get("factlock", {}).get("fact_preservation")},
        "outputs_with_hallucinated_number_all": {"naive": g["all"].get("naive", {}).get("outputs_with_hallucinated_number"),
                                                 "factlock": g["all"].get("factlock", {}).get("outputs_with_hallucinated_number")},
        "extraction_micro_f1_test": {k: extraction["test"][k]["micro"]["f1"] for k in ("deterministic", "apertus_only", "merged")},
        "gate_recall_bad": expl["gate"]["with_language_floor"]["flagged_vs_bad"]["recall"],
        "gate_precision_bad": expl["gate"]["with_language_floor"]["flagged_vs_bad"]["precision"],
        "gate_recall_bad_without_floor": expl["gate"]["without_language_floor"]["flagged_vs_bad"]["recall"],
        "gate_share_ready_all": g["all"].get("factlock", {}).get("gate", {}).get("ready"),
        "seconds_per_letter_and_language": speed["seconds_per_letter_and_language"],
        "tokens_per_s_translate": speed["by_task"].get("translate", {}).get("tokens_per_s_end_to_end"),
    }
    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": get_settings().llm_name,
        "model_file": "apertus-v1.5-8b-text-q4_k_m.gguf (Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF, from andreasmartin/apertus-v1.5-8b-text)",
        "judge_model": next((j.get("judge_model") for j in _read(RUNS / "judge_items.jsonl") if j.get("judge_model")), None),
        "dataset": {"letters": len(letters), "dev": sum(1 for x in letters.values() if x["split"] == "dev"),
                    "test": sum(1 for x in letters.values() if x["split"] == "test"),
                    "explain_test_letters": len({s["id"] for s in scored if s["split"] == "test"}),
                    "explain_dev_letters": len({s["id"] for s in scored if s["split"] == "dev"}),
                    "target_languages": sorted({s["target"] for s in scored})},
        "headline": head,
        "extraction": extraction,
        "explanation": expl,
        "speed_cost": speed,
        "gate_thresholds": {"default": thresholds.get("default"), "pooled_fit": thresholds.get("pooled_fit"),
                            "languages": {k: {kk: v.get(kk) for kk in ("ready", "review", "floor", "tier", "fit")}
                                          for k, v in (thresholds.get("languages") or {}).items()}},
    }
    (RUNS / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(head, indent=1))
    return summary


if __name__ == "__main__":
    score()
