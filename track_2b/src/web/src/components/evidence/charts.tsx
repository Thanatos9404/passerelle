"use client";

import * as React from "react";
import { motion, useReducedMotion } from "motion/react";
import { Table2, BarChart3 } from "lucide-react";
import type { EvalSummary, GateStatus, PR } from "@/lib/api/types";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { GATE_META } from "@/components/domain/atoms";
import { MOCK_LANGUAGES } from "@/lib/api/mock";
import { cn, EM_DASH } from "@/lib/utils";

/*
 * Palette (validated with the dataviz validator on #FFFFFF, light):
 *   fact-lock #4A78B0 · naive #C98A4B  — CVD ΔE 19.5, normal ΔE 24.2.
 *   #C98A4B is < 3:1 on white, so values are direct-labelled and every chart has a table view.
 * Status colours are reserved for the gate and always ship with icon + label.
 */
export const C_LOCK = "#4A78B0";
export const C_NAIVE = "#C98A4B";

const pct = (v: number | null | undefined) => (v == null || Number.isNaN(v) ? null : v <= 1 ? v * 100 : v);
const fmtP = (v: number | null | undefined, d = 1) => (pct(v) == null ? EM_DASH : `${pct(v)!.toFixed(d)}%`);
const EXTRA_NAMES: Record<string, string> = { fa: "Persian", ps: "Pashto", am: "Amharic", ru: "Russian", hi: "Hindi", bs: "Bosnian/Croatian/Serbian", de: "German", fr: "French", it: "Italian" };
const langName = (code: string) => MOCK_LANGUAGES.find((l) => l.code === code)?.name ?? EXTRA_NAMES[code] ?? code;

export function ChartCard({
  title,
  subtitle,
  legend,
  children,
  table,
  empty,
  className,
}: {
  title: string;
  subtitle: string;
  legend?: React.ReactNode;
  children: React.ReactNode;
  table?: React.ReactNode;
  empty?: boolean;
  className?: string;
}) {
  const [view, setView] = React.useState<"chart" | "table">("chart");
  return (
    <section className={cn("rounded-4xl bg-white p-6 shadow-[0_1px_2px_rgba(97,74,68,.05)] ring-1 ring-line md:p-8", className)}>
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-[560px]">
          <h3 className="t-h3">{title}</h3>
          <p className="mt-1.5 text-[14.5px] leading-relaxed text-body">{subtitle}</p>
        </div>
        {table && !empty && (
          <div className="flex rounded-pill bg-sand-2 p-1" role="group" aria-label="View">
            {(["chart", "table"] as const).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                aria-pressed={view === v}
                className={cn("inline-flex h-8 items-center gap-1.5 rounded-pill px-3 text-[13px] font-medium capitalize", view === v ? "bg-white text-ink shadow-card" : "text-muted")}
              >
                {v === "chart" ? <BarChart3 className="size-3.5" /> : <Table2 className="size-3.5" />} {v}
              </button>
            ))}
          </div>
        )}
      </header>
      {legend && !empty && <div className="mt-5">{legend}</div>}
      <div className="mt-6">{view === "table" && table ? table : children}</div>
    </section>
  );
}

export function Pending({ what }: { what: string }) {
  return (
    <div className="grid min-h-[180px] place-items-center rounded-3xl border border-dashed border-line-strong bg-paper p-6 text-center">
      <div>
        <p className="t-num text-[40px] leading-none font-semibold text-faint">{EM_DASH}</p>
        <p className="mt-3 text-[14px] text-muted">
          No {what} in the evaluation summary yet. Run <code className="rounded bg-sand-2 px-1.5 py-0.5 text-[12.5px] text-ink">make eval</code> to produce <code className="rounded bg-sand-2 px-1.5 py-0.5 text-[12.5px] text-ink">data/eval_runs/summary.json</code>.
        </p>
      </div>
    </div>
  );
}

export function Legend({ items }: { items: { color: string; label: string; shape?: "dot" | "bar" | "tick" }[] }) {
  return (
    <ul className="flex flex-wrap gap-x-5 gap-y-2 text-[13px] text-body">
      {items.map((i) => (
        <li key={i.label} className="inline-flex items-center gap-2">
          {i.shape === "tick" ? (
            <span className="h-3.5 w-[2px] rounded" style={{ background: i.color }} />
          ) : i.shape === "bar" ? (
            <span className="h-2.5 w-4 rounded-[3px]" style={{ background: i.color }} />
          ) : (
            <span className="size-2.5 rounded-full ring-2 ring-white" style={{ background: i.color }} />
          )}
          {i.label}
        </li>
      ))}
    </ul>
  );
}

function DataTable({ head, rows }: { head: string[]; rows: (string | number)[][] }) {
  return (
    <div className="scrollbar-thin overflow-x-auto">
      <table className="w-full min-w-[420px] text-left text-[13.5px]">
        <thead>
          <tr className="border-b border-line text-[12px] text-muted">
            {head.map((h) => (
              <th key={h} scope="col" className="py-2 pr-4 font-semibold">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-line last:border-0">
              {r.map((c, j) => (
                <td key={j} className={cn("t-num py-2 pr-4", j === 0 ? "font-medium text-ink" : "text-body")}>
                  {c}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Axis ticks at 0/25/50/75/100 as hairlines. */
const ROW = "grid grid-cols-[88px_1fr_44px] items-center gap-3 sm:grid-cols-[120px_1fr_52px]";

function Grid({ ticks = [0, 25, 50, 75, 100], suffix = "%" }: { ticks?: number[]; suffix?: string }) {
  return (
    <div className={cn("pointer-events-none absolute inset-0", ROW)} aria-hidden>
      <div />
      <div className="relative h-full">
        {ticks.map((t) => (
          <div key={t} className="absolute inset-y-0 w-px bg-line" style={{ left: `${t}%` }}>
            <span className="absolute -bottom-6 -translate-x-1/2 text-[11px] text-muted">
              {t}
              {suffix}
            </span>
          </div>
        ))}
      </div>
      <div />
    </div>
  );
}

/* ---------- 1. Fact preservation: dumbbell naive -> fact-lock per language ---------- */
export function FactPreservationChart({ data }: { data: EvalSummary["fact_preservation"] }) {
  const reduce = useReducedMotion();
  const rows = (data?.by_lang ?? []).filter((r) => pct(r.naive) != null || pct(r.factlock) != null);
  const empty = rows.length === 0;
  return (
    <ChartCard
      title="Fact preservation — the key ablation"
      subtitle="Share of critical facts (dates, CHF amounts, references) rendered exactly right in the client-language output, per language: Apertus translating directly vs Passerelle with fact-lock."
      empty={empty}
      legend={<Legend items={[{ color: C_NAIVE, label: "Naive — direct translation" }, { color: C_LOCK, label: "Passerelle — fact-lock" }]} />}
      table={
        <DataTable
          head={["Language", "Naive", "Fact-lock", "Hallucinated numbers (naive)", "Hallucinated numbers (fact-lock)"]}
          rows={rows.map((r) => [langName(r.lang), fmtP(r.naive), fmtP(r.factlock), fmtP(r.hallucinated_naive), fmtP(r.hallucinated_factlock)])}
        />
      }
    >
      {empty ? (
        <Pending what="fact-preservation results" />
      ) : (
        <div className="pb-7">
          <ul className="relative space-y-1">
            <Grid />
            {rows.map((r, i) => {
              const a = pct(r.naive);
              const b = pct(r.factlock);
              return (
                <li key={r.lang} className={cn("relative", ROW)}>
                  <span className="truncate text-[13.5px] font-medium text-ink">{langName(r.lang)}</span>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div tabIndex={0} className="relative h-9 rounded-lg outline-none hover:bg-sand-2/50 focus-visible:ring-2 focus-visible:ring-ink/30" aria-label={`${langName(r.lang)}: naive ${fmtP(a)}, fact-lock ${fmtP(b)}`}>
                        {a != null && b != null && (
                          <motion.div
                            className="absolute top-1/2 h-[2px] -translate-y-1/2 rounded bg-faint"
                            style={{ left: `${Math.min(a, b)}%` }}
                            initial={reduce ? false : { width: 0 }}
                            whileInView={{ width: `${Math.abs(b - a)}%` }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.9, delay: i * 0.05 }}
                          />
                        )}
                        {a != null && <span className="absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ring-white" style={{ left: `${a}%`, background: C_NAIVE }} />}
                        {b != null && (
                          <span className="absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ring-white" style={{ left: `${b}%`, background: C_LOCK }} />
                        )}
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="font-semibold">{langName(r.lang)}</p>
                      <p>Naive: {fmtP(a)} · Fact-lock: {fmtP(b)}</p>
                      <p className="text-white/70">Hallucinated numbers: {fmtP(r.hallucinated_naive)} → {fmtP(r.hallucinated_factlock)}</p>
                    </TooltipContent>
                  </Tooltip>
                  <span className="t-num text-right text-[12.5px] font-semibold text-ink">{b != null ? `${b.toFixed(0)}%` : EM_DASH}</span>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </ChartCard>
  );
}

/* ---------- 2. chrF per language with gate thresholds ---------- */
export function ChrfChart({ data }: { data: EvalSummary["chrf"] }) {
  const reduce = useReducedMotion();
  const rows = (data?.by_lang ?? []).filter((r) => r.chrf != null).sort((a, b) => (b.chrf ?? 0) - (a.chrf ?? 0));
  const empty = rows.length === 0;
  return (
    <ChartCard
      title="Meaning preservation"
      subtitle="chrF between the back-translation and the source-language plain explanation, per client language. Ticks mark the dev-calibrated review and ready thresholds."
      empty={empty}
      legend={<Legend items={[{ color: C_LOCK, label: "chrF (test split)", shape: "bar" }, { color: "#1A1615", label: "Gate thresholds (review · ready)", shape: "tick" }]} />}
      table={<DataTable head={["Language", "chrF", "Review threshold", "Ready threshold"]} rows={rows.map((r) => [langName(r.lang), r.chrf?.toFixed(1) ?? EM_DASH, r.review?.toFixed(1) ?? EM_DASH, r.ready?.toFixed(1) ?? EM_DASH])} />}
    >
      {empty ? (
        <Pending what="chrF results" />
      ) : (
        <div className="pb-7">
          <ul className="relative space-y-2">
            <Grid suffix="" />
            {rows.map((r, i) => (
              <li key={r.lang} className={cn("relative", ROW)}>
                <span className="truncate text-[13.5px] font-medium text-ink">{langName(r.lang)}</span>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div tabIndex={0} className="relative h-7 outline-none focus-visible:ring-2 focus-visible:ring-ink/30" aria-label={`${langName(r.lang)} chrF ${r.chrf?.toFixed(1)}`}>
                      <motion.div
                        className="absolute inset-y-[5px] left-0 rounded-r-[4px]"
                        style={{ background: C_LOCK }}
                        initial={reduce ? false : { width: 0 }}
                        whileInView={{ width: `${Math.min(100, r.chrf ?? 0)}%` }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.9, delay: i * 0.04, ease: [0.22, 1, 0.36, 1] }}
                      />
                      {[r.review, r.ready].map((t, k) => (t == null ? null : <span key={k} className="absolute -inset-y-0.5 w-[2px] rounded bg-ink" style={{ left: `${t}%` }} />))}
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="font-semibold">{langName(r.lang)}</p>
                    <p>chrF {r.chrf?.toFixed(1)} · review ≥ {r.review ?? EM_DASH} · ready ≥ {r.ready ?? EM_DASH}</p>
                  </TooltipContent>
                </Tooltip>
                <span className="t-num text-right text-[12.5px] font-semibold text-ink">{r.chrf?.toFixed(1)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </ChartCard>
  );
}

/* ---------- 3. Gate confusion ---------- */
export function GateMatrix({ data }: { data: EvalSummary["gate"] }) {
  const rows = (["ready", "review", "interpreter"] as GateStatus[]).map((g) => data?.confusion?.find((c) => c.gate === g) ?? null);
  const empty = rows.every((r) => !r);
  const max = Math.max(1, ...rows.flatMap((r) => (r ? [r.ok, r.bad] : [0])));
  const cell = (v: number | undefined) => (v == null ? 0 : 0.08 + (v / max) * 0.62);
  return (
    <ChartCard
      title="Does the gate route bad outputs to people?"
      subtitle="Test-split outputs by gate decision, against whether the output actually had a fact error or a chrF below the dev-calibrated threshold."
      empty={empty}
      table={<DataTable head={["Gate decision", "Output fine", "Output faulty"]} rows={rows.map((r, i) => [GATE_META[(["ready", "review", "interpreter"] as GateStatus[])[i]].label, r?.ok ?? EM_DASH, r?.bad ?? EM_DASH])} />}
    >
      {empty ? (
        <Pending what="gate confusion counts" />
      ) : (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_auto]">
          <div className="grid grid-cols-[minmax(140px,1.7fr)_1fr_1fr] gap-[2px] overflow-hidden rounded-2xl text-[13.5px]">
            <div className="bg-paper p-3 text-[12px] text-muted">Gate says</div>
            <div className="bg-paper p-3 text-center text-[12px] text-muted">Output fine</div>
            <div className="bg-paper p-3 text-center text-[12px] text-muted">Output faulty</div>
            {rows.map((r, i) => {
              const g = (["ready", "review", "interpreter"] as GateStatus[])[i];
              const M = GATE_META[g];
              const Icon = M.icon;
              return (
                <React.Fragment key={g}>
                  <div className="flex items-center gap-2 bg-paper p-3 font-medium text-ink">
                    <Icon className={cn("size-4 shrink-0", M.cls.split(" ").find((c) => c.startsWith("text-")))} /> {M.label}
                  </div>
                  {[r?.ok, r?.bad].map((v, k) => (
                    <Tooltip key={k}>
                      <TooltipTrigger asChild>
                        <div tabIndex={0} className="t-num grid place-items-center p-4 text-[20px] font-semibold text-ink outline-none" style={{ background: `rgba(74,120,176,${cell(v)})` }}>
                          {v ?? EM_DASH}
                        </div>
                      </TooltipTrigger>
                      <TooltipContent>
                        {M.label} · {k === 0 ? "output fine" : "output faulty"}: {v ?? EM_DASH}
                      </TooltipContent>
                    </Tooltip>
                  ))}
                </React.Fragment>
              );
            })}
          </div>
          <dl className="flex gap-3 xl:flex-col">
            {[
              ["Precision", data?.precision, "of flagged outputs were faulty"],
              ["Recall", data?.recall, "of faulty outputs were flagged"],
            ].map(([l, v, s]) => (
              <div key={l as string} className="min-w-[150px] flex-1 rounded-2xl bg-sand-2/70 p-4">
                <dt className="text-[12px] font-semibold tracking-[0.04em] text-muted uppercase">{l as string}</dt>
                <dd className="t-num mt-1 text-[28px] font-semibold text-ink">{fmtP(v as number | null | undefined, 0)}</dd>
                <dd className="text-[12.5px] text-muted">{s as string}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </ChartCard>
  );
}

/* ---------- 4. Extraction P/R per fact type ---------- */
export function ExtractionTable({ data }: { data: EvalSummary["extraction"] }) {
  const rows = data?.by_type ?? [];
  const empty = rows.length === 0;
  const methods: { key: "deterministic" | "apertus" | "merged"; label: string }[] = [
    { key: "deterministic", label: "Rules only" },
    { key: "apertus", label: "Apertus only" },
    { key: "merged", label: "Merged" },
  ];
  const Bar = ({ v }: { v: PR | null | undefined }) => {
    const f1 = v?.f1 ?? (v?.precision != null && v?.recall != null && v.precision + v.recall > 0 ? (2 * v.precision * v.recall) / (v.precision + v.recall) : null);
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <div tabIndex={0} className="flex items-center gap-2 outline-none">
            <div className="h-2 w-16 overflow-hidden rounded-pill bg-sand sm:w-20">
              <div className="h-full rounded-pill" style={{ width: `${pct(f1) ?? 0}%`, background: C_LOCK }} />
            </div>
            <span className="t-num w-12 text-[13px] text-ink">{fmtP(f1, 0)}</span>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          Precision {fmtP(v?.precision)} · Recall {fmtP(v?.recall)} · F1 {fmtP(f1)}
        </TooltipContent>
      </Tooltip>
    );
  };
  return (
    <ChartCard title="Fact extraction (DE · FR · IT)" subtitle="F1 per fact type for the deterministic Swiss-format rules, Apertus JSON extraction, and the merged extractor. Hover for precision and recall." empty={empty}>
      {empty ? (
        <Pending what="extraction scores" />
      ) : (
        <div className="scrollbar-thin overflow-x-auto">
          <table className="w-full min-w-[520px] text-left">
            <thead>
              <tr className="border-b border-line text-[12px] text-muted">
                <th scope="col" className="py-2 pr-4 font-semibold">
                  Fact type
                </th>
                {methods.map((m) => (
                  <th key={m.key} scope="col" className="py-2 pr-4 font-semibold">
                    {m.label} · F1
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.type} className="border-b border-line last:border-0">
                  <td className="py-2.5 pr-4 text-[13.5px] font-medium text-ink capitalize">{r.type}</td>
                  {methods.map((m) => (
                    <td key={m.key} className="py-2.5 pr-4">
                      <Bar v={r[m.key]} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </ChartCard>
  );
}
