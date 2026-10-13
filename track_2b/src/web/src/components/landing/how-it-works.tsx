"use client";

import * as React from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ArrowDown, FileSearch, Languages, Lock, MessageSquareReply, ScanText, ShieldCheck } from "lucide-react";
import { MOCK_LETTERS, buildFacts } from "@/lib/mock/letters";
import { MOCK_CLIENT_MESSAGES, MOCK_EXPLANATIONS, MOCK_REPLIES } from "@/lib/mock/explanations";
import { MOCK_LANGUAGES, chrF } from "@/lib/api/mock";
import { placeholdersIn, renderFactValue, splitMasked, highlightValues, TYPE_LABEL } from "@/lib/facts";
import { LetterText } from "@/components/domain/letter-text";
import { GateBadge, SegmentText } from "@/components/domain/atoms";
import { ChrfMeter, PlaceholderChecklist } from "@/components/domain/widgets";
import { ButtonLink } from "@/components/ui/button";
import { Reveal, WordReveal, EASE } from "@/components/motion/primitives";
import { cn } from "@/lib/utils";

const L = MOCK_LETTERS[0];
const FACTS = buildFacts(L);
const byId = new Map(FACTS.map((f) => [f.id, f]));
const TI = MOCK_EXPLANATIONS[L.id].ti;
const TI_BACK = TI.drift.reduce((t, [a, b]) => t.replace(a, b), L.reference);
const TI_CHRF = Math.round(chrF(TI_BACK, L.reference) * 10) / 10;
const TI_LANG = MOCK_LANGUAGES.find((l) => l.code === "ti")!;
const TI_STATUS = !TI_LANG.thresholds ? "review" : TI_CHRF >= TI_LANG.thresholds.ready ? "ready" : TI_CHRF >= TI_LANG.thresholds.review ? "review" : "interpreter";

const STEPS = [
  { key: "read", label: "Read", icon: ScanText, title: "Read the letter", body: "Paste text, upload a PDF or pick a sample. German, French and Italian are detected automatically." },
  { key: "extract", label: "Extract", icon: FileSearch, title: "Extract a fact card", body: "Deterministic Swiss-format extractors and Apertus JSON extraction run side by side. Where they disagree, the caseworker sees a flag." },
  { key: "lock", label: "Fact-lock", icon: Lock, title: "Lock every critical fact", body: "Dates, CHF amounts, IBANs, AHV numbers and references become immutable placeholders before generation, then return in a verified, locale-safe format." },
  { key: "explain", label: "Explain", icon: Languages, title: "Explain in the client's language", body: "Plain language at A2/B1 level: what this is, what to do, by when, what happens if not, who can help. Right-to-left aware." },
  { key: "verify", label: "Verify", icon: ShieldCheck, title: "Verify before handing over", body: "Apertus back-translates the explanation. chrF against the source explanation and a placeholder audit decide: ready, review with the client, or a human interpreter." },
  { key: "reply", label: "Reply", icon: MessageSquareReply, title: "Draft the reply", body: "The client answers in their own language; Passerelle drafts a formal reply in the authority's language with the reference and facts locked." },
] as const;
type StepKey = (typeof STEPS)[number]["key"];

function Frag({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("w-full max-w-[460px] rounded-3xl bg-white p-5 shadow-float ring-1 ring-black/5 md:p-6", className)}>{children}</div>;
}

function Label({ children }: { children: React.ReactNode }) {
  return <p className="mb-3 text-[11.5px] font-semibold tracking-[0.06em] text-muted uppercase">{children}</p>;
}

function Fragment({ k }: { k: StepKey }) {
  switch (k) {
    case "read": {
      const excerpt = L.text.split("\n").slice(10, 18).join("\n");
      const off = L.text.indexOf(excerpt);
      const fs = FACTS.filter((f) => f.span && f.span[0] >= off && f.span[1] <= off + excerpt.length).map((f) => ({ ...f, span: [f.span![0] - off, f.span![1] - off] as [number, number] }));
      return (
        <Frag>
          <div className="mb-4 flex gap-1 rounded-pill bg-sand-2 p-1 text-[12.5px] font-medium">
            {["Samples", "Paste", "Upload PDF"].map((t, i) => (
              <span key={t} className={cn("flex-1 rounded-pill py-1.5 text-center", i === 0 ? "bg-white text-ink shadow-card" : "text-muted")}>
                {t}
              </span>
            ))}
          </div>
          <Label>Betreibungsamt Aarenfeld · DE detected</Label>
          <LetterText text={excerpt} facts={fs} className="text-[13px]" />
        </Frag>
      );
    }
    case "extract": {
      const rows = ["D4", "A1", "A2", "R1", "I1"].map((id) => byId.get(id)!);
      return (
        <Frag>
          <Label>Fact card · 2 extractors</Label>
          <ul className="divide-y divide-line">
            {rows.map((f) => (
              <li key={f.id} className="flex items-center gap-3 py-2.5 text-[13.5px]">
                <span className="w-20 shrink-0 text-muted">{TYPE_LABEL[f.type]}</span>
                <span className="t-num min-w-0 truncate font-semibold text-ink">{renderFactValue(f)}</span>
                <span className="ml-auto shrink-0 rounded-pill bg-ok-soft px-2 py-0.5 text-[11.5px] font-semibold text-ok">rules + Apertus</span>
              </li>
            ))}
          </ul>
          <div className="mt-3 rounded-2xl bg-warn-soft p-3 text-[12.5px] leading-snug text-warn">
            <span className="font-semibold">Flagged:</span> {L.disagreements[0].field} — rules {L.disagreements[0].deterministic?.split(" ")[0]}, model {L.disagreements[0].llm?.split(" ")[0]}
          </div>
        </Frag>
      );
    }
    case "lock": {
      const sentence = "Wenn Sie nicht einverstanden sind, müssen Sie bis ⟦D4⟧ beim Amt Rechtsvorschlag erheben. Forderung: ⟦A1⟧ plus ⟦A2⟧.";
      const parts = sentence.split(/(⟦[A-Z]\d⟧)/);
      return (
        <Frag>
          <Label>What the model sees</Label>
          <p className="text-[15px] leading-[1.9] text-ink">
            {parts.map((p, i) =>
              /^⟦/.test(p) ? (
                <span key={i} className="mx-0.5 rounded-md bg-ink px-1.5 py-0.5 text-[12.5px] font-semibold text-white">
                  {p}
                </span>
              ) : (
                <React.Fragment key={i}>{p}</React.Fragment>
              ),
            )}
          </p>
          <div className="my-4 flex items-center gap-2 text-[12px] text-muted">
            <ArrowDown className="size-3.5" /> re-inserted after generation, never generated
          </div>
          <ul className="grid grid-cols-1 gap-1.5">
            {["D4", "A1", "A2"].map((id) => {
              const f = byId.get(id)!;
              return (
                <li key={id} className="flex items-center gap-3 rounded-xl bg-sand-2/70 px-3 py-2 text-[13px]">
                  <span className="font-semibold text-ink">⟦{id}⟧</span>
                  <span className="text-muted">{TYPE_LABEL[f.type]}</span>
                  <span className="ml-auto inline-flex items-center gap-1.5 font-semibold text-ink">
                    <Lock className="size-3 text-muted" /> {renderFactValue(f)}
                  </span>
                </li>
              );
            })}
          </ul>
        </Frag>
      );
    }
    case "explain": {
      const segs = splitMasked(TI.masked.split("\n\n").slice(0, 3).join("\n\n"), FACTS);
      return (
        <Frag>
          <div className="mb-3 flex items-center justify-between">
            <span lang="ti" className="text-[15px] font-semibold text-ink">
              ትግርኛ <span className="font-sans text-[12.5px] font-normal text-muted">· Tigrinya</span>
            </span>
            <span className="inline-flex items-center gap-1.5 text-[12px] text-muted">
              <span className="size-1.5 animate-pulse rounded-full bg-ok" /> streaming
            </span>
          </div>
          <p lang="ti" className="text-[15px] whitespace-pre-line text-ink">
            <SegmentText segments={segs} facts={FACTS} size="sm" tooltip={false} />
            <span className="animate-caret ml-0.5 inline-block h-[1.1em] w-[2px] translate-y-[3px] bg-ink" />
          </p>
        </Frag>
      );
    }
    case "verify": {
      const expected = [...new Set(placeholdersIn(L.reference))];
      return (
        <Frag>
          <div className="mb-4 flex items-center justify-between gap-3">
            <Label>Tigrinya · round trip to German</Label>
            <GateBadge status={TI_STATUS} size="sm" className="-mt-3" />
          </div>
          <ChrfMeter value={TI_CHRF} thresholds={TI_LANG.thresholds} />
          <div className="mt-4">
            <PlaceholderChecklist expected={expected.slice(0, 6)} audit={{ missing: [], duplicated: [], unexpected: [] }} labels={Object.fromEntries(expected.map((id) => [id, TYPE_LABEL[byId.get(id)?.type ?? ""] ?? ""]))} />
          </div>
          <p className="mt-4 text-[12.5px] leading-snug text-muted">Facts are intact, but meaning drifted in the round trip — the gate routes it to a person instead of the client.</p>
        </Frag>
      );
    }
    case "reply": {
      const msg = MOCK_CLIENT_MESSAGES[L.id].ar;
      const raw = new Map(L.facts.map((f) => [f.id, f.value]));
      const body = MOCK_REPLIES[L.id].split("\n\n").slice(3, 6).join("\n\n").replace(/⟦([A-Z]\d)⟧/g, (m, id: string) => raw.get(id) ?? m);
      return (
        <Frag>
          <Label>Client writes · العربية</Label>
          <p lang="ar" dir="rtl" className="rounded-2xl rounded-tr-md bg-sand-2 px-4 py-3 text-[15px] text-ink">
            {msg}
          </p>
          <div className="my-4 flex items-center gap-2 text-[12px] text-muted">
            <ArrowDown className="size-3.5" /> formal draft in German, for the caseworker to approve
          </div>
          <div className="rounded-2xl p-4 text-[13.5px] leading-relaxed whitespace-pre-line text-body ring-1 ring-line">
            <SegmentText segments={highlightValues(body, FACTS)} facts={FACTS} size="sm" tooltip={false} />
          </div>
        </Frag>
      );
    }
  }
}

export function HowItWorks() {
  const [step, setStep] = React.useState<StepKey>("read");
  const reduce = useReducedMotion();
  const meta = STEPS.find((s) => s.key === step)!;
  return (
    <section id="how" className="scroll-mt-24 bg-paper pt-12 pb-16 md:pt-16 md:pb-24">
      <div className="container-x grid items-center gap-12 lg:grid-cols-[1fr_1.05fr] lg:gap-16">
        <div className="lg:order-2">
          <Reveal>
            <p className="t-eyebrow">How it works</p>
          </Reveal>
          <WordReveal className="t-h2 mt-4" lines={[{ text: "Six careful steps" }, { text: "between a letter and a person.", className: "text-muted" }]} />
          <div className="mt-6 min-h-[112px]">
            <AnimatePresence mode="wait" initial={false}>
              <motion.div
                key={step}
                initial={reduce ? false : { opacity: 0, y: 8, filter: "blur(6px)" }}
                animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                exit={reduce ? undefined : { opacity: 0, y: -6, filter: "blur(6px)" }}
                transition={{ duration: 0.35, ease: EASE }}
              >
                <p className="t-lead">
                  <strong className="font-semibold text-ink">{meta.title}.</strong> {meta.body}
                </p>
              </motion.div>
            </AnimatePresence>
          </div>
          <div role="tablist" aria-label="Pipeline steps" className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-3">
            {STEPS.map((s, i) => {
              const active = s.key === step;
              const Icon = s.icon;
              return (
                <button
                  key={s.key}
                  role="tab"
                  id={`how-tab-${s.key}`}
                  aria-selected={active}
                  aria-controls="how-panel"
                  tabIndex={active ? 0 : -1}
                  onClick={() => setStep(s.key)}
                  onKeyDown={(e) => {
                    const d = e.key === "ArrowRight" || e.key === "ArrowDown" ? 1 : e.key === "ArrowLeft" || e.key === "ArrowUp" ? -1 : 0;
                    if (!d) return;
                    e.preventDefault();
                    const next = STEPS[(i + d + STEPS.length) % STEPS.length];
                    setStep(next.key);
                    document.getElementById(`how-tab-${next.key}`)?.focus();
                  }}
                  className={cn(
                    "relative flex h-12 items-center justify-center gap-2 rounded-pill border text-[15.5px] font-medium transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ink/40",
                    active ? "border-transparent text-white" : "border-line-strong bg-white text-ink hover:border-ink/25",
                  )}
                >
                  {active && <motion.span layoutId="how-pill" className="absolute inset-0 rounded-pill bg-ink" transition={{ type: "spring", stiffness: 380, damping: 32 }} />}
                  <span className="relative inline-flex items-center gap-2">
                    <span className={cn("text-[12px] tabular-nums", active ? "text-white/60" : "text-faint")}>{String(i + 1).padStart(2, "0")}</span>
                    <Icon className="size-4" aria-hidden /> {s.label}
                  </span>
                </button>
              );
            })}
          </div>
          <ButtonLink href="/workspace/" arrow className="mt-10">
            Try it on a sample letter
          </ButtonLink>
        </div>
        <Reveal className="lg:order-1">
          <div
            id="how-panel"
            role="tabpanel"
            aria-labelledby={`how-tab-${step}`}
            className="relative grid min-h-[520px] place-items-center overflow-hidden rounded-4xl p-5 sm:p-10 md:min-h-[600px]"
            style={{ background: "linear-gradient(180deg, #9CC1E7 0%, #C9DBEE 45%, #EDDFD0 100%)" }}
          >
            <AnimatePresence mode="popLayout" initial={false}>
              <motion.div
                key={step}
                className="flex w-full justify-center"
                initial={reduce ? false : { opacity: 0, y: 30, scale: 0.97, filter: "blur(8px)" }}
                animate={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
                exit={reduce ? undefined : { opacity: 0, y: -20, scale: 0.98, filter: "blur(8px)" }}
                transition={{ duration: 0.55, ease: EASE }}
              >
                <Fragment k={step} />
              </motion.div>
            </AnimatePresence>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
