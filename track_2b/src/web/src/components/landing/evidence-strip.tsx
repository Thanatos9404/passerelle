"use client";

import { ButtonLink } from "@/components/ui/button";
import { Reveal, SectionHead, Ticker } from "@/components/motion/primitives";
import { headline, useEvalSummary } from "@/lib/eval";

export function EvidenceStrip() {
  const s = useEvalSummary();
  const d = s.status === "ready" ? s.data : null;
  const h = headline(d);
  const empty = s.status !== "loading" && [h.factlock, h.chrf, h.gateRecall, h.seconds].every((v) => v == null);
  const tiles = [
    { v: h.factlock, f: (x: number) => `${x.toFixed(1)}%`, label: "critical facts rendered exactly", sub: h.naive != null ? `vs ${h.naive.toFixed(1)}% when Apertus translates directly` : "fact-lock vs naive translation" },
    { v: h.chrf, f: (x: number) => x.toFixed(1), label: "mean back-translation chrF", sub: h.nLangs ? `across ${h.nLangs} client languages` : "per language on /evidence" },
    { v: h.gateRecall, f: (x: number) => `${x.toFixed(0)}%`, label: "of faulty outputs caught by the gate", sub: "routed to review or an interpreter" },
    { v: h.seconds, f: (x: number) => `${x.toFixed(0)} s`, label: "per letter on a laptop GPU", sub: d?.hardware ?? "RTX 4050 · Q4_K_M" },
  ];
  return (
    <section id="evidence" className="scroll-mt-24 bg-sand-2 py-24 md:py-36">
      <div className="container-x">
        <SectionHead
          eyebrow="Evidence"
          title="Measured, not promised."
          muted="Straight from the eval run."
          lead={
            empty
              ? "The evaluation run has not produced a summary yet, so the figures below are shown as dashes rather than estimates."
              : "Held-out synthetic letters, eight client languages plus high-resource controls, and an ablation against direct translation."
          }
        />
        <div className="mt-14 grid grid-cols-1 gap-4 sm:grid-cols-2 md:mt-20 lg:grid-cols-4">
          {tiles.map((t, i) => (
            <Reveal key={t.label} delay={i * 0.06} className="flex flex-col rounded-4xl bg-white p-7 shadow-[0_1px_2px_rgba(97,74,68,.05)] ring-1 ring-line">
              <Ticker value={s.status === "loading" ? null : t.v} format={t.f} className={t.v == null ? "text-[48px] leading-none font-semibold text-faint" : "text-[48px] leading-none font-semibold text-ink"} />
              <p className="mt-4 text-[15.5px] font-semibold tracking-[-0.01em] text-ink">{t.label}</p>
              <p className="mt-1 text-[13.5px] text-muted">{t.sub}</p>
            </Reveal>
          ))}
        </div>
        <div className="mt-10 flex flex-col items-center gap-3">
          <ButtonLink href="/evidence/" variant="outline" arrow>
            Read the full evidence
          </ButtonLink>
          {d?.generated_at && <p className="text-[12.5px] text-muted">Summary generated {new Date(d.generated_at).toLocaleString("en-GB")}</p>}
        </div>
      </div>
    </section>
  );
}
