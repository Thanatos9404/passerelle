"use client";

import * as React from "react";
import { Clock, Coins, Cpu, FlaskConical, Info, Zap } from "lucide-react";
import { useEvalSummary } from "@/lib/eval";
import { Reveal, Ticker, WordReveal } from "@/components/motion/primitives";
import { ChrfChart, ExtractionTable, FactPreservationChart, GateMatrix } from "./charts";
import { EM_DASH, cn } from "@/lib/utils";

function Meta({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="text-[12px] font-semibold tracking-[0.04em] text-muted uppercase">{label}</dt>
      <dd className="mt-1 truncate text-[15px] font-medium text-ink">{value ?? EM_DASH}</dd>
    </div>
  );
}

export function EvidenceView() {
  const s = useEvalSummary();
  const d = s.status === "ready" ? s.data : null;
  const c = d?.cost;
  const hasAny = !!(d && (d.fact_preservation?.by_lang?.length || d.chrf?.by_lang?.length || d.gate?.confusion?.length || d.extraction?.by_type?.length || c));

  const costTiles = [
    { icon: Clock, label: "Seconds per letter & language", v: c?.seconds_per_letter, f: (x: number) => `${x.toFixed(1)} s` },
    { icon: Cpu, label: "Tokens per letter (all steps)", v: c?.tokens_per_letter, f: (x: number) => Math.round(x).toLocaleString("en") },
    { icon: Zap, label: "GPU energy per letter (estimate)", v: c?.energy_wh_per_letter, f: (x: number) => `${x.toFixed(2)} Wh` },
    { icon: Coins, label: "CHF per letter (electricity + laptop, estimate)", v: c?.chf_per_letter, f: (x: number) => `CHF ${x.toFixed(3)}` },
  ];

  return (
    <>
      <section className="relative overflow-hidden pt-[120px] pb-16 md:pt-[150px] md:pb-24" style={{ background: "linear-gradient(180deg, #B7D5F1 0%, #D9E6F2 45%, #F4E6DA 100%)" }}>
        <div className="container-x">
          <Reveal>
            <p className="t-eyebrow">Evidence</p>
          </Reveal>
          <WordReveal
            as="h1"
            onMount
            className="t-display mt-4 max-w-[900px] !text-[clamp(38px,5.2vw,72px)]"
            lines={[{ text: "How well does it work?" }, { text: "Here is what we measured.", className: "text-ink/45" }]}
          />
          <Reveal delay={0.3} className="t-lead mt-6 max-w-[680px]">
            Every figure on this page is read from the evaluation summary (<code className="rounded bg-white/60 px-1.5 py-0.5 text-[0.85em]">data/eval_runs/summary.json</code>). Nothing is typed in by hand; anything missing is shown as a dash.
          </Reveal>
          <Reveal delay={0.4}>
            <dl className="frost mt-10 grid grid-cols-2 gap-5 rounded-3xl border border-white/60 p-5 md:grid-cols-5 md:p-6">
              <Meta label="Model" value={d?.model} />
              <Meta label="Hardware" value={d?.hardware} />
              <Meta label="Split" value={d?.split} />
              <Meta label="Letters" value={d?.n_letters} />
              <Meta label="Generated" value={d?.generated_at ? new Date(d.generated_at).toLocaleString("en-GB") : null} />
            </dl>
          </Reveal>
          {s.status !== "loading" && !hasAny && (
            <Reveal delay={0.5}>
              <div className="mt-4 flex items-start gap-3 rounded-2xl bg-white/70 p-4 text-[14px] leading-relaxed text-body ring-1 ring-white">
                <Info className="mt-0.5 size-4 shrink-0 text-brown" />
                <p>
                  <span className="font-semibold text-ink">The evaluation has not produced a summary yet.</span> The charts below show where each result will appear once{" "}
                  <code className="rounded bg-sand-2 px-1 text-[13px]">make eval</code> has run on the held-out test split. We do not show placeholder or estimated numbers.
                </p>
              </div>
            </Reveal>
          )}
        </div>
      </section>

      <div className="bg-sand-2 py-14 md:py-20">
        <div className="container-x flex flex-col gap-5">
          <Reveal>
            <FactPreservationChart data={d?.fact_preservation} />
          </Reveal>
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
            <Reveal>
              <ChrfChart data={d?.chrf} />
            </Reveal>
            <Reveal delay={0.06}>
              <GateMatrix data={d?.gate} />
            </Reveal>
          </div>
          <Reveal>
            <ExtractionTable data={d?.extraction} />
          </Reveal>
          <Reveal>
            <section className="rounded-4xl bg-white p-6 shadow-[0_1px_2px_rgba(97,74,68,.05)] ring-1 ring-line md:p-8">
              <h3 className="t-h3">Cost &amp; speed</h3>
              <p className="mt-1.5 max-w-[640px] text-[14.5px] leading-relaxed text-body">Measured end to end (extract, explain, back-translate, verify) for one letter on the laptop GPU, quantised Q4_K_M.</p>
              <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {costTiles.map(({ icon: Icon, label, v, f }) => (
                  <div key={label} className="rounded-3xl bg-sand-2/70 p-5">
                    <Icon className="size-4 text-brown" />
                    <Ticker value={v ?? null} format={f} className={cn("mt-4 block text-[34px] leading-none font-semibold", v == null ? "text-faint" : "text-ink")} />
                    <p className="mt-2 text-[13.5px] text-muted">{label}</p>
                  </div>
                ))}
              </div>
              <p className="mt-4 text-[13px] leading-relaxed text-muted">
                Human interpreter comparison:{" "}
                {c?.interpreter_chf_range ? (
                  <span className="font-medium text-ink">
                    CHF {c.interpreter_chf_range[0]}–{c.interpreter_chf_range[1]} per hour (assumed range, not a cited tariff)
                  </span>
                ) : (
                  EM_DASH
                )}
                {c?.interpreter_note ? ` — ${c.interpreter_note}` : ""}
              </p>
            </section>
          </Reveal>
          <Reveal>
            <section className="rounded-4xl bg-sand p-6 md:p-8">
              <h3 className="t-h3 flex items-center gap-2">
                <FlaskConical className="size-5 text-brown" /> How to read this
              </h3>
              <ul className="mt-4 grid grid-cols-1 gap-3 text-[14.5px] leading-relaxed text-body md:grid-cols-2">
                <li>Letters are synthetic (fictional offices, people and numbers), 12 letter types × DE/FR/IT, with ground-truth facts.</li>
                <li>Gate thresholds are calibrated per language on the dev split; the test split is never used for tuning.</li>
                <li>chrF measures round-trip meaning preservation, not fluency. A native-speaker review is the gold standard; our team could spot-check Tamil only.</li>
                <li>Weak languages are reported as they are. The gate, not the model, is the safety story.</li>
                {(d?.notes ?? []).map((n, i) => (
                  <li key={i}>{n}</li>
                ))}
              </ul>
            </section>
          </Reveal>
        </div>
      </div>
    </>
  );
}
