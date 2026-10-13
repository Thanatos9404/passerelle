"use client";

import * as React from "react";
import { getApi } from "@/lib/api";
import type { EvalSummary, GateStatus, PR } from "@/lib/api/types";

export type EvalState = { status: "loading" } | { status: "ready"; data: EvalSummary } | { status: "missing" };

type Obj = Record<string, unknown>;
const isObj = (v: unknown): v is Obj => typeof v === "object" && v !== null && !Array.isArray(v);
const n = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);
const s = (v: unknown): string | null => (typeof v === "string" && v.trim() ? v : null);
const get = (o: unknown, ...path: string[]): unknown => path.reduce<unknown>((x, k) => (isObj(x) ? x[k] : undefined), o);
const pr = (v: unknown): PR | null => (isObj(v) ? { precision: n(v.precision), recall: n(v.recall), f1: n(v.f1) } : null);

/**
 * Adapts data/eval_runs/summary.json as written by src/eval/score.py
 * ({headline, extraction, explanation, speed_cost, gate_thresholds, dataset}) to the UI's EvalSummary.
 * A summary already in the UI shape passes through. Nothing is invented: absent fields stay null.
 */
export function adaptSummary(raw: unknown): EvalSummary | null {
  if (!isObj(raw)) return null;
  const expl = raw.explanation;
  if (!isObj(expl) && !isObj(raw.speed_cost) && !isObj(raw.headline)) {
    // already the UI shape (or a placeholder)
    return raw as EvalSummary;
  }
  const perLang = isObj(get(expl, "per_language")) ? (get(expl, "per_language") as Obj) : {};
  const thr = isObj(get(raw, "gate_thresholds", "languages")) ? (get(raw, "gate_thresholds", "languages") as Obj) : {};
  const langs = Object.keys(perLang);

  const confusionRaw = get(expl, "gate", "confusion");
  const confusion = isObj(confusionRaw)
    ? (["ready", "review", "interpreter"] as GateStatus[]).map((g) => ({ gate: g, ok: n(confusionRaw[`${g}|ok`]) ?? 0, bad: n(confusionRaw[`${g}|bad`]) ?? 0 }))
    : null;

  const ex = isObj(get(raw, "extraction", "test")) ? get(raw, "extraction", "test") : get(raw, "extraction", "dev");
  const byType = (m: string) => (isObj(get(ex, m, "by_type")) ? (get(ex, m, "by_type") as Obj) : {});
  const types = [...new Set([...Object.keys(byType("deterministic")), ...Object.keys(byType("apertus_only")), ...Object.keys(byType("merged"))])];

  const sc = isObj(raw.speed_cost) ? raw.speed_cost : {};
  const byTask = isObj(sc.by_task) ? (sc.by_task as Obj) : {};
  const taskTokens = Object.values(byTask).reduce<number | null>((acc, t) => {
    const p = n(get(t, "mean_prompt_tokens"));
    const c = n(get(t, "mean_completion_tokens"));
    return p === null && c === null ? acc : (acc ?? 0) + (p ?? 0) + (c ?? 0);
  }, null);
  const chfE = n(get(sc, "cost_chf_per_letter_and_language_estimate", "electricity"));
  const chfH = n(get(sc, "cost_chf_per_letter_and_language_estimate", "laptop_amortisation"));
  const range = get(sc, "human_interpreter_chf_per_hour_assumed_range");

  return {
    generated_at: s(raw.generated_at),
    model: s(raw.model),
    hardware: s(sc.hardware),
    split: "test",
    n_letters: n(get(raw, "dataset", "letters")),
    fact_preservation: {
      overall: { naive: n(get(raw, "headline", "fact_preservation_all", "naive")), factlock: n(get(raw, "headline", "fact_preservation_all", "factlock")) },
      by_lang: langs.map((l) => ({
        lang: l,
        naive: n(get(perLang[l], "naive", "fact_preservation")),
        factlock: n(get(perLang[l], "factlock", "fact_preservation")),
        hallucinated_naive: n(get(perLang[l], "naive", "outputs_with_hallucinated_number")),
        hallucinated_factlock: n(get(perLang[l], "factlock", "outputs_with_hallucinated_number")),
      })),
    },
    chrf: {
      by_lang: langs.map((l) => ({
        lang: l,
        chrf: n(get(perLang[l], "factlock", "chrf_mean")),
        ready: n(get(thr[l], "ready")),
        review: n(get(thr[l], "review")),
      })),
    },
    gate: {
      confusion,
      precision: n(get(raw, "headline", "gate_precision_bad")),
      recall: n(get(raw, "headline", "gate_recall_bad")),
    },
    extraction: types.length
      ? { by_type: types.map((t) => ({ type: t, deterministic: pr(byType("deterministic")[t]), apertus: pr(byType("apertus_only")[t]), merged: pr(byType("merged")[t]) })) }
      : null,
    cost: {
      seconds_per_letter: n(sc.seconds_per_letter_and_language),
      tokens_per_letter: taskTokens,
      energy_wh_per_letter: n(sc.wh_per_letter_and_language_estimate),
      chf_per_letter: chfE === null && chfH === null ? null : (chfE ?? 0) + (chfH ?? 0),
      interpreter_chf_range: Array.isArray(range) && range.length === 2 && n(range[0]) !== null && n(range[1]) !== null ? [range[0] as number, range[1] as number] : null,
      interpreter_note: s(sc.note),
    },
    notes: [
      ...(s(get(expl, "gate", "definitions", "bad")) ? [`"Faulty" output (gate evaluation): ${s(get(expl, "gate", "definitions", "bad"))}.`] : []),
      ...(n(get(raw, "headline", "gate_recall_bad_without_floor")) !== null
        ? [`Gate recall without the per-language floor: ${((n(get(raw, "headline", "gate_recall_bad_without_floor")) ?? 0) * 100).toFixed(0)}%.`]
        : []),
    ],
  };
}

/** Loads /api/eval/summary, falling back to the static /eval/summary.json. Never invents numbers. */
export function useEvalSummary(): EvalState {
  const [st, setSt] = React.useState<EvalState>({ status: "loading" });
  React.useEffect(() => {
    let alive = true;
    getApi()
      .then((api) => api.evalSummary())
      .then((d) => {
        const a = adaptSummary(d);
        if (alive) setSt(a ? { status: "ready", data: a } : { status: "missing" });
      })
      .catch(() => alive && setSt({ status: "missing" }));
    return () => {
      alive = false;
    };
  }, []);
  return st;
}

const mean = (xs: (number | null | undefined)[]) => {
  const v = xs.filter((x): x is number => typeof x === "number" && Number.isFinite(x));
  return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null;
};

/** Headline numbers derived from the summary (null when absent). Percentages are returned 0..100. */
export function headline(d: EvalSummary | null) {
  const pct = (v: number | null | undefined) => (v == null ? null : v <= 1 ? v * 100 : v);
  const fp = d?.fact_preservation;
  return {
    factlock: pct(fp?.overall?.factlock ?? mean(fp?.by_lang?.map((r) => r.factlock) ?? [])),
    naive: pct(fp?.overall?.naive ?? mean(fp?.by_lang?.map((r) => r.naive) ?? [])),
    chrf: mean(d?.chrf?.by_lang?.map((r) => r.chrf) ?? []),
    gateRecall: pct(d?.gate?.recall ?? null),
    seconds: d?.cost?.seconds_per_letter ?? null,
    nLangs: d?.chrf?.by_lang?.filter((r) => r.chrf != null).length || null,
  };
}
