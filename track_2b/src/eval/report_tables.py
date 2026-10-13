"""Fill technical_report.md / README.md placeholders with numbers taken verbatim from summary.json.

    python -m eval.report_tables
Replaces the markers HEADLINE_SUMMARY, EVAL_TABLES (report) and RESULTS_TABLE (root README) — or the blocks
between <!-- auto:... --> markers on re-runs.
"""

from __future__ import annotations

import json
import re

from passerelle.languages import LANGUAGES

from .harness import ROOT, RUNS


def pct(x, d=0):
    return "–" if x is None else f"{x * 100:.{d}f}%"


def num(x, d=1):
    return "–" if x is None else f"{x:.{d}f}"


def build(s: dict) -> dict[str, str]:
    ex = s["extraction"]["test"]
    e = s["explanation"]
    g = e["groups"]
    sp = s["speed_cost"]
    gate = e["gate"]
    lm, al = g["low_mid_resource"], g["all"]
    head = (f"On {e['n_test_items']} test explanations (12 letters × {len(e['per_language'])} languages), fact-lock "
            f"renders **{pct(lm['factlock']['fact_preservation'])}** of critical facts exactly in the 8 low/mid-resource "
            f"languages vs **{pct(lm['naive']['fact_preservation'])}** for naive prompting, and outputs with a number "
            f"not in the letter are rare either way ({pct(al['naive']['outputs_with_hallucinated_number'], 1)} vs "
            f"{pct(al['factlock']['outputs_with_hallucinated_number'], 1)}). The gate flags "
            f"{pct(gate['with_language_floor']['flagged_vs_bad']['recall'])} of bad outputs "
            f"(precision {pct(gate['with_language_floor']['flagged_vs_bad']['precision'])}); one letter in one language "
            f"takes ~{sp['seconds_per_letter_and_language']:.0f} s on the laptop GPU.")

    t1 = ["| Setup (test, %d letters) | Precision | Recall | F1 | Deadline role acc. |" % ex["n_letters"],
          "|---|---|---|---|---|"]
    for k, lab in (("deterministic", "Rules only"), ("apertus_only", "Apertus only"), ("merged", "**Merged (ours)**")):
        m = ex[k]["micro"]
        t1.append(f"| {lab} | {pct(m['precision'], 1)} | {pct(m['recall'], 1)} | {pct(m['f1'], 1)} | "
                  f"{pct(ex['deadline_role_accuracy'][k]['accuracy'])} |")
    t1.append(f"\n*Table 1: Fact extraction (micro over 9 fact types). Letter type: keyword baseline "
              f"{pct(ex['letter_type_accuracy']['keyword'])}, Apertus {pct(ex['letter_type_accuracy']['apertus'])}; "
              f"Apertus returned valid JSON for {ex['apertus_json_valid']}/{ex['n_letters']} letters.*")

    t2 = ["| Target language | Facts naive | Facts fact-lock | Halluc. naive | Halluc. fact-lock | chrF median | Judge | Ready / Review / Interp. |",
          "|---|---|---|---|---|---|---|---|"]
    order = sorted(e["per_language"], key=lambda c: (LANGUAGES[c].eval_group == "control", c))
    for c in order:
        r = e["per_language"][c]
        if not r:
            continue
        gg = r["factlock"]["gate"]
        t2.append(f"| {LANGUAGES[c].name}{' (control)' if LANGUAGES[c].eval_group == 'control' else ''} | "
                  f"{pct(r['naive']['fact_preservation'])} | **{pct(r['factlock']['fact_preservation'])}** | "
                  f"{pct(r['naive']['outputs_with_hallucinated_number'])} | {pct(r['factlock']['outputs_with_hallucinated_number'])} | "
                  f"{num(r['factlock']['chrf_median'])} | {num(r['factlock']['judge_mean'], 2)} | "
                  f"{pct(gg['ready'])} / {pct(gg['review'])} / {pct(gg['interpreter'])} |")
    for key, lab in (("low_mid_resource", "8 low/mid-resource"), ("controls", "2 controls"), ("all", "All")):
        r = g[key]
        gg = r["factlock"]["gate"]
        t2.append(f"| **{lab}** | {pct(r['naive']['fact_preservation'])} | **{pct(r['factlock']['fact_preservation'])}** | "
                  f"{pct(r['naive']['outputs_with_hallucinated_number'])} | {pct(r['factlock']['outputs_with_hallucinated_number'])} | "
                  f"{num(r['factlock']['chrf_median'])} | {num(r['factlock']['judge_mean'], 2)} | "
                  f"{pct(gg['ready'])} / {pct(gg['review'])} / {pct(gg['interpreter'])} |")
    t2.append("\n*Table 2: Explanation ablation on the test split (12 letters per language). Facts = share of "
              "ground-truth critical facts rendered exactly; Halluc. = outputs containing a number not in the letter; "
              "judge = helper-judge round-trip score (1–5).*")

    w, wo = gate["with_language_floor"], gate["without_language_floor"]
    t3 = ["| Gate (test) | Flagged precision | Flagged recall | Interpreter recall | Bad outputs marked Ready |",
          "|---|---|---|---|---|",
          f"| With language floors | {pct(w['flagged_vs_bad']['precision'])} | {pct(w['flagged_vs_bad']['recall'])} | "
          f"{pct(w['interpreter_vs_bad']['recall'])} | {w['ready_outputs_that_are_bad']} of {w['ready_outputs']} |",
          f"| Thresholds only | {pct(wo['flagged_vs_bad']['precision'])} | {pct(wo['flagged_vs_bad']['recall'])} | "
          f"{pct(wo['interpreter_vs_bad']['recall'])} | {wo['ready_outputs_that_are_bad']} of {wo['ready_outputs']} |",
          f"\n*Table 3: Gate quality. Bad = degenerate or wrong-script output, or judge ≤ 2 "
          f"({pct(al['factlock']['bad_rate'])} of test outputs). Calibrated on dev: review below chrF "
          f"{s['gate_thresholds']['default']['review']}, ready from {s['gate_thresholds']['default']['ready']}.*"]

    bt = sp["by_task"]
    t4 = ["| Step (per call) | Seconds | Completion tokens | Tokens/s |", "|---|---|---|---|"]
    for k, lab in (("extract", "Extraction (JSON), once per letter"), ("explain_source", "Plain-language text, once per letter"),
                   ("translate", "Translation, per language"), ("back_translate", "Back-translation, per language"),
                   ("naive", "Naive baseline (comparison)")):
        if k in bt:
            t4.append(f"| {lab} | {bt[k]['mean_latency_s']:.1f} | {bt[k]['mean_completion_tokens']:.0f} | {num(bt[k]['tokens_per_s_end_to_end'])} |")
    cost = sp["cost_chf_per_letter_and_language_estimate"]
    t4.append(f"\n*Table 4: Speed on the RTX 4050 Laptop GPU. One letter in one language end to end: "
              f"~{sp['seconds_per_letter_and_language']:.0f} s; GPU energy ≈ {num(sp['wh_per_letter_and_language_estimate'], 2)} Wh "
              f"(≈ CHF {num(cost['electricity'], 4)} at an assumed CHF {cost['assumptions']['electricity_chf_per_kwh']}/kWh; "
              f"laptop amortisation ≈ CHF {num(cost['laptop_amortisation'], 3)}). For orientation only, community "
              f"interpreting is assumed to cost CHF {sp['human_interpreter_chf_per_hour_assumed_range'][0]}–"
              f"{sp['human_interpreter_chf_per_hour_assumed_range'][1]} per hour (assumption, not a cited tariff).*")

    figs = ("\n![Fact preservation](docs/figures/ablation_fact_preservation.png)\n\n"
            "*Figure 2: Share of critical facts rendered exactly, naive vs fact-lock, per target language (test).*\n\n"
            "![Gate](docs/figures/gate_by_language.png)\n\n"
            "*Figure 3: Gate decisions per target language (test).*\n")
    tables = ("### Fact extraction\n\n" + "\n".join(t1) + "\n\n### Fact preservation, hallucinated numbers, meaning, gate\n\n"
              + "\n".join(t2) + "\n" + figs + "\n" + "\n".join(t3) + "\n\n### Cost and speed\n\n" + "\n".join(t4) + "\n")
    readme = ("| Metric (test split) | Naive Apertus | Passerelle |\n|---|---|---|\n"
              f"| Critical facts rendered exactly, 8 low/mid-resource languages | {pct(lm['naive']['fact_preservation'])} | **{pct(lm['factlock']['fact_preservation'])}** |\n"
              f"| Critical facts rendered exactly, all 10 languages | {pct(al['naive']['fact_preservation'])} | **{pct(al['factlock']['fact_preservation'])}** |\n"
              f"| Outputs with a number not in the letter | {pct(al['naive']['outputs_with_hallucinated_number'], 1)} | {pct(al['factlock']['outputs_with_hallucinated_number'], 1)} |\n"
              f"| Fact extraction micro-F1 (rules / Apertus / merged) | – | {pct(ex['deterministic']['micro']['f1'], 1)} / {pct(ex['apertus_only']['micro']['f1'], 1)} / **{pct(ex['merged']['micro']['f1'], 1)}** |\n"
              f"| Bad outputs flagged by the gate (recall / precision) | – | {pct(w['flagged_vs_bad']['recall'])} / {pct(w['flagged_vs_bad']['precision'])} |\n"
              f"| Seconds per letter and language (RTX 4050 laptop) | – | ~{sp['seconds_per_letter_and_language']:.0f} s |\n")
    return {"HEADLINE_SUMMARY": head, "EVAL_TABLES": tables, "RESULTS_TABLE": readme}


def _fill(path, mapping):
    txt = path.read_text(encoding="utf-8")
    for k, v in mapping.items():
        sep = "" if k == "HEADLINE_SUMMARY" else "\n"  # inline marker inside a paragraph
        block = f"<!-- auto:{k} -->{sep}{v}{sep}<!-- /auto:{k} -->"
        if f"<!-- auto:{k} -->" in txt:
            txt = re.sub(rf"<!-- auto:{k} -->.*?<!-- /auto:{k} -->", lambda m: block, txt, flags=re.S)
        elif k in txt:
            txt = txt.replace(k, block)
    path.write_text(txt, encoding="utf-8")


def main() -> int:
    s = json.loads((RUNS / "summary.json").read_text(encoding="utf-8"))
    parts = build(s)
    _fill(ROOT / "technical_report.md", {k: parts[k] for k in ("HEADLINE_SUMMARY", "EVAL_TABLES")})
    _fill(ROOT.parent / "README.md", {"RESULTS_TABLE": parts["RESULTS_TABLE"]})
    # spot-check sheet for a team member who reads Tamil (filled in by hand; never auto-scored)
    items = [json.loads(x) for x in (RUNS / "explain_items.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    rows = ["# Tamil spot-check (test split)\n", "For a Tamil reader on the team: rate each explanation "
            "(1 = wrong/misleading … 5 = correct and clear) and note errors. Licence CC-BY-4.0.\n"]
    for it in [i for i in items if i["target"] == "ta" and i["split"] == "test"][:6]:
        fl = it["factlock"]
        rows += [f"\n## {it['id']} — chrF {fl['chrf']}, gate at runtime: {fl['gate_at_runtime']['status']}\n",
                 "**Plain-language source (letter language)**\n\n" + fl["source_plain"] + "\n",
                 "**Tamil explanation (Passerelle)**\n\n" + fl["explanation"] + "\n",
                 "**Naive Tamil explanation**\n\n" + it["naive"]["output"] + "\n",
                 "**Reviewer score (1-5):** ___  **Notes:** ___\n"]
    (ROOT / "docs" / "spotcheck_ta.md").write_text("\n".join(rows), encoding="utf-8")
    print("filled report + README from summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
