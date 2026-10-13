"""Report figures from data/eval_runs/summary.json + explain_scored.jsonl -> docs/figures/*.png|svg.

Palette (project directive, warm neutral): ink #1A1615, muted #757170, beige #F0EAE5, sky #9CC1E7,
plus a warm tan #B5917A for the third gate state.  Colour is never the only carrier of identity:
every multi-series chart has a legend and direct value labels; stacked segments have 2px white gaps.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from passerelle.languages import LANGUAGES  # noqa: E402

from .harness import ROOT, RUNS  # noqa: E402

INK, BODY, MUTED, BEIGE, SKY, TAN, WHITE = "#1A1615", "#453F3D", "#757170", "#F0EAE5", "#9CC1E7", "#B5917A", "#FFFFFF"
OUT = ROOT / "docs" / "figures"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": BODY,
    "xtick.color": MUTED, "ytick.color": BODY, "axes.titlesize": 10.5, "axes.titleweight": "bold",
    "axes.titlecolor": INK, "axes.titlelocation": "left", "axes.titlepad": 10, "figure.dpi": 110,
    "savefig.dpi": 220, "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "legend.frameon": False, "legend.fontsize": 8.5,
})


def _save(fig, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", facecolor=WHITE)
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)


def _grid(ax, axis="x"):
    ax.grid(axis=axis, color=BEIGE, linewidth=0.9)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def _lang_label(code: str) -> str:
    lang = LANGUAGES[code]
    return f"{lang.name}" + ("  (control)" if lang.eval_group == "control" else "")


def _paired_bars(per_lang: dict, metric: str, title: str, xlabel: str, name: str, pct: bool = True,
                 better_low: bool = False) -> None:
    codes = [c for c in per_lang if per_lang[c]]
    key = lambda c: (LANGUAGES[c].eval_group == "control", per_lang[c]["naive"].get(metric) or 0)  # noqa: E731
    codes.sort(key=key, reverse=False)
    fig, ax = plt.subplots(figsize=(6.6, 0.42 * len(codes) + 1.2))
    h = 0.36
    for i, c in enumerate(codes):
        nv = per_lang[c]["naive"].get(metric) or 0
        fl = per_lang[c]["factlock"].get(metric) or 0
        for off, val, col in ((h / 2 + 0.02, nv, MUTED), (-h / 2 - 0.02, fl, INK)):
            ax.barh(i + off, val * (100 if pct else 1), height=h, color=col, linewidth=0)
            ax.text(val * (100 if pct else 1) + 1, i + off, f"{val * 100:.0f}%" if pct else f"{val:.2f}",
                    va="center", ha="left", fontsize=7.5, color=BODY)
    ax.set_yticks(range(len(codes)), [_lang_label(c) for c in codes])
    ax.set_xlim(0, 112 if pct else None)
    ax.set_xlabel(xlabel)
    _grid(ax)
    ax.set_title(title)
    handles = [plt.Rectangle((0, 0), 1, 1, color=MUTED), plt.Rectangle((0, 0), 1, 1, color=INK)]
    ax.legend(handles, ["Naive (Apertus explains the raw letter)", "Passerelle fact-lock"], loc="lower center",
              bbox_to_anchor=(0.45, 1.0), ncol=2, borderaxespad=1.6)
    _save(fig, name)


def fig_gate(per_lang: dict) -> None:
    codes = sorted([c for c in per_lang if per_lang[c]], key=lambda c: (LANGUAGES[c].eval_group == "control",
                   -(per_lang[c]["factlock"]["gate"].get("interpreter") or 0)))
    fig, ax = plt.subplots(figsize=(6.6, 0.4 * len(codes) + 1.2))
    states = [("ready", "Ready", INK, WHITE), ("review", "Review with client", SKY, INK), ("interpreter", "Use a human interpreter", TAN, INK)]
    for i, c in enumerate(codes):
        left = 0.0
        for st, _, col, txt in states:
            v = (per_lang[c]["factlock"]["gate"].get(st) or 0) * 100
            if v > 0:
                ax.barh(i, v, left=left, height=0.62, color=col, edgecolor=WHITE, linewidth=2)
                if v >= 12:
                    ax.text(left + v / 2, i, f"{v:.0f}%", ha="center", va="center", fontsize=7.5, color=txt)
            left += v
    ax.set_yticks(range(len(codes)), [_lang_label(c) for c in codes])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of test explanations (%)")
    ax.invert_yaxis()
    _grid(ax)
    ax.set_title("Confidence gate decisions per target language (test split)")
    ax.legend([plt.Rectangle((0, 0), 1, 1, color=s[2]) for s in states], [s[1] for s in states],
              loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=3, borderaxespad=1.6)
    _save(fig, "gate_by_language")


def fig_chrf(scored: list[dict], thresholds: dict) -> None:
    test = [s for s in scored if s["split"] == "test" and s["factlock"]["chrf"] is not None]
    codes = sorted({s["target"] for s in test}, key=lambda c: (LANGUAGES[c].eval_group == "control",
                   sorted(x["factlock"]["chrf"] for x in test if x["target"] == c)[len([x for x in test if x["target"] == c]) // 2]))
    fig, ax = plt.subplots(figsize=(6.6, 0.4 * len(codes) + 1.3))
    for i, c in enumerate(codes):
        vals = sorted(s["factlock"]["chrf"] for s in test if s["target"] == c)
        jitter = [((k % 5) - 2) * 0.06 for k in range(len(vals))]
        ax.scatter(vals, [i + j for j in jitter], s=14, color=SKY, edgecolor=WHITE, linewidth=0.6, zorder=3)
        med = vals[len(vals) // 2]
        ax.plot([med, med], [i - 0.3, i + 0.3], color=INK, linewidth=2, zorder=4, solid_capstyle="round")
    d = thresholds.get("default") or {}
    for t, lab in ((d.get("review"), "interpreter below"), (d.get("ready"), "ready at/above")):
        if t is not None:
            ax.axvline(t, color=MUTED, linewidth=1, linestyle=(0, (3, 3)), zorder=2)
            ax.text(t, len(codes) - 0.3, f" {lab} {t:g}", fontsize=7, color=MUTED, va="bottom")
    ax.set_yticks(range(len(codes)), [_lang_label(c) for c in codes])
    ax.set_xlim(0, 100)
    ax.set_xlabel("chrF: back-translation vs. plain-language source (0-100)")
    _grid(ax)
    ax.set_title("Round-trip meaning check per language (dots = test letters, bar = median)")
    _save(fig, "chrf_by_language")


def fig_extraction(extraction: dict) -> None:
    test = extraction["test"]
    types = ["date", "amount", "reference", "time", "phone", "duration", "iban", "ahv", "email"]
    systems = [("deterministic", "Rules only", MUTED), ("apertus_only", "Apertus only", SKY), ("merged", "Merged (Passerelle)", INK)]
    fig, ax = plt.subplots(figsize=(6.8, 2.9))
    w = 0.26
    for k, (sys_, lab, col) in enumerate(systems):
        vals = [(test[sys_]["by_type"][t]["f1"] or 0) * 100 for t in types]
        xs = [i + (k - 1) * (w + 0.02) for i in range(len(types))]
        ax.bar(xs, vals, width=w, color=col, linewidth=0)
    ax.set_xticks(range(len(types)), [t if t != "ahv" else "AHV/AVS" for t in types])
    ax.set_ylim(0, 105)
    ax.set_ylabel("F1 (%)")
    _grid(ax, "y")
    ax.spines["left"].set_visible(False)
    micro = " · ".join(f"{lab}: {test[s]['micro']['f1'] * 100:.1f}" for s, lab, _ in systems)
    ax.set_title(f"Fact extraction F1 by type (test, {test['n_letters']} letters)")
    ax.legend([plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in systems], [f"{lab}" for _, lab, _ in systems],
              loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, borderaxespad=1.6)
    ax.text(0, -0.2, f"micro-F1  {micro}", transform=ax.transAxes, fontsize=7.5, color=MUTED)
    _save(fig, "extraction_f1")


def fig_speed(speed: dict) -> None:
    rows = [("extract", "Fact extraction (JSON)"), ("explain_source", "Plain-language source text"),
            ("translate", "Translation (target language)"), ("back_translate", "Back-translation (check)"),
            ("naive", "Naive baseline (for comparison)")]
    rows = [(k, lab) for k, lab in rows if k in speed["by_task"]]
    fig, ax = plt.subplots(figsize=(6.6, 0.42 * len(rows) + 1.0))
    for i, (k, lab) in enumerate(rows):
        t = speed["by_task"][k]
        ax.barh(i, t["mean_latency_s"], height=0.56, color=INK if k != "naive" else MUTED, linewidth=0)
        ax.text(t["mean_latency_s"] + 0.3, i, f"{t['mean_latency_s']:.1f} s · {t['mean_completion_tokens']:.0f} tok · "
                f"{t['tokens_per_s_end_to_end'] or 0:.0f} tok/s", va="center", fontsize=7.5, color=BODY)
    ax.set_yticks(range(len(rows)), [lab for _, lab in rows])
    ax.invert_yaxis()
    ax.set_xlabel("Mean wall-clock seconds per call (RTX 4050 Laptop, Q4_K_M)")
    ax.set_xlim(0, max(speed["by_task"][k]["mean_latency_s"] for k, _ in rows) * 1.9)
    _grid(ax)
    ax.set_title("Where the time goes, per letter and target language")
    _save(fig, "speed")


def main() -> int:
    summary = json.loads((RUNS / "summary.json").read_text(encoding="utf-8"))
    scored = [json.loads(x) for x in (RUNS / "explain_scored.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    per_lang = summary["explanation"]["per_language"]
    _paired_bars(per_lang, "fact_preservation", "Critical facts rendered exactly (test split)",
                 "Share of ground-truth critical facts present in the output (%)", "ablation_fact_preservation")
    _paired_bars(per_lang, "outputs_with_hallucinated_number", "Outputs containing a number that is not in the letter",
                 "Share of outputs (%)", "ablation_hallucinated_numbers")
    fig_gate(per_lang)
    fig_chrf(scored, summary.get("gate_thresholds") or {})
    fig_extraction(summary["extraction"])
    fig_speed(summary["speed_cost"])
    print("figures written to", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
