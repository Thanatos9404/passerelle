"use client";

import * as React from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Check, Copy, Languages, Loader2, MessageSquareReply, Printer, RotateCcw, ShieldCheck, Square, Wand2, X } from "lucide-react";
import type { Workspace } from "./use-workspace";
import type { Fact } from "@/lib/api/types";
import { Tabs, TabsContent, PillTabs } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Tip } from "@/components/ui/tooltip";
import { FactChip, GATE_META, GateBadge, SegmentText } from "@/components/domain/atoms";
import { ChrfMeter, PlaceholderChecklist } from "@/components/domain/widgets";
import { TYPE_LABEL, explanationSegments, highlightValues, placeholdersIn, renderFactValue, splitMasked } from "@/lib/facts";
import { wordDiff } from "@/lib/diff";
import { MOCK_CLIENT_MESSAGES } from "@/lib/mock/explanations";
import { cn, fmtSec } from "@/lib/utils";
import { EASE } from "@/components/motion/primitives";
import { ErrorCard, Pane, PaneBody, PaneHeader, SectionLabel } from "./pane";
import { LanguagePicker, langAttr } from "./facts-pane";

export type ClientTab = "explanation" | "verification" | "reply";

const NO_FACTS: Fact[] = [];

const STAGES = [
  { key: "source_plain", label: "Plain version" },
  { key: "translate", label: "Translating" },
  { key: "back_translate", label: "Back-translating" },
  { key: "verify", label: "Verifying" },
];

function StageTrack({ stage, done }: { stage: string | null; done: boolean }) {
  const idx = done ? STAGES.length : Math.max(0, STAGES.findIndex((s) => s.key === stage));
  return (
    <ol className="flex flex-wrap items-center gap-1.5" aria-label="Progress">
      {STAGES.map((s, i) => {
        const state = i < idx ? "done" : i === idx ? "active" : "todo";
        return (
          <li key={s.key} className={cn("inline-flex h-7 items-center gap-1.5 rounded-pill px-2.5 text-[12px] font-medium", state === "done" ? "bg-ok-soft text-ok" : state === "active" ? "bg-ink text-white" : "bg-sand-2 text-muted")}>
            {state === "done" ? <Check className="size-3.5" /> : state === "active" ? <Loader2 className="size-3.5 animate-spin" /> : <Square className="size-3" />}
            {s.label}
          </li>
        );
      })}
    </ol>
  );
}

function useCopy() {
  const [copied, setCopied] = React.useState(false);
  return {
    copied,
    copy: (t: string) =>
      void navigator.clipboard?.writeText(t).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 1400);
      }),
  };
}

function ExplanationView({ ws, activeFact, setActiveFact, onPrint }: { ws: Workspace; activeFact: string | null; setActiveFact: (id: string | null) => void; onPrint: (k: "client" | "caseworker") => void }) {
  const e = ws.explain;
  const facts = ws.analysis?.facts ?? NO_FACTS;
  const lang = ws.languages.find((l) => l.code === (e.lang ?? ws.targetLang)) ?? ws.language;
  const rtl = e.result?.rtl ?? lang?.rtl ?? false;
  const display = e.masked.replace(/⟦[^⟧]*$/, "");
  const segs = React.useMemo(() => (e.result ? explanationSegments(e.result, facts) : splitMasked(display, facts)), [e.result, display, facts]);
  const { copied, copy } = useCopy();
  const reduce = useReducedMotion();

  if (e.status === "idle")
    return (
      <div className="grid h-full min-h-[320px] place-items-center text-center">
        <div className="max-w-[340px]">
          <div className="mx-auto grid size-14 place-items-center rounded-full bg-sand-2 text-ink">
            <Languages className="size-6" />
          </div>
          <p className="mt-4 text-[18px] font-semibold tracking-[-0.02em] text-ink">Ready to explain</p>
          <p className="mt-1.5 text-[14px] leading-relaxed text-muted">
            Choose the client&apos;s language and press <span className="font-medium text-ink">Explain</span>. Dates, amounts and references arrive as locked chips — the model never writes them.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-1.5">
            {ws.languages.slice(0, 6).map((l) => (
              <button
                key={l.code}
                onClick={() => ws.setTargetLang(l.code)}
                lang={langAttr(l.code)}
                className={cn("h-8 rounded-pill px-3 text-[14px] font-medium ring-1 transition", l.code === ws.targetLang ? "bg-ink text-white ring-ink" : "bg-white text-ink ring-line hover:ring-ink/25")}
              >
                {l.native_name}
              </button>
            ))}
          </div>
        </div>
      </div>
    );

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        {e.status === "done" && e.result ? (
          <div className="flex flex-wrap items-center gap-2">
            <GateBadge status={e.result.gate.status} />
            <span className="text-[12.5px] text-muted">chrF {e.result.chrf?.toFixed(1) ?? "—"}</span>
          </div>
        ) : (
          <StageTrack stage={e.stage} done={false} />
        )}
        {e.status === "streaming" && (
          <Button size="sm" variant="ghost" onClick={ws.cancelExplain}>
            <X className="size-3.5" /> Cancel
          </Button>
        )}
      </div>

      {e.status === "error" && (
        <ErrorCard
          title="No explanation this time"
          message={e.error ?? "Unknown error"}
          action={
            <Button size="sm" variant="outline" onClick={() => void ws.runExplain()}>
              <RotateCcw className="size-3.5" /> Try again
            </Button>
          }
        />
      )}

      {(e.status === "streaming" || e.status === "done" || (e.status === "error" && display)) && (
        <motion.div
          initial={reduce ? false : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: EASE }}
          lang={lang ? langAttr(lang.code) : undefined}
          dir={rtl ? "rtl" : "ltr"}
          aria-live="polite"
          aria-busy={e.status === "streaming"}
          className={cn("rounded-2xl bg-paper p-5 text-[17px] whitespace-pre-line text-ink ring-1 ring-line sm:p-6", rtl ? "text-right" : "text-left")}
        >
          {segs.length === 0 && e.status === "streaming" ? (
            <span className="text-[14px] text-muted" dir="ltr">
              Waiting for the first tokens…
            </span>
          ) : (
            <SegmentText segments={segs} facts={facts} activeId={activeFact} onHover={setActiveFact} />
          )}
          {e.status === "streaming" && <span className="animate-caret ms-0.5 inline-block h-[1.05em] w-[2px] translate-y-[3px] bg-ink" aria-hidden />}
        </motion.div>
      )}

      {e.status === "done" && e.result && (
        <>
          {e.result.gate.status !== "ready" && (
            <div className={cn("rounded-2xl p-3.5 text-[13.5px] leading-relaxed", GATE_META[e.result.gate.status].cls)}>
              <p className="font-semibold">{GATE_META[e.result.gate.status].help}</p>
              <ul className="mt-1 list-disc ps-5 text-ink/80">
                {e.result.gate.reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}
          <div className="flex flex-wrap items-center gap-2">
            <Button size="sm" variant="outline" onClick={() => copy(e.result!.explanation)}>
              {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />} {copied ? "Copied" : "Copy text"}
            </Button>
            {e.result.gate.status === "interpreter" ? (
              <Tip label="The gate says a human interpreter is needed — a client copy is not offered.">
                <span tabIndex={0}>
                  <Button size="sm" variant="outline" disabled>
                    <Printer className="size-3.5" /> Client copy
                  </Button>
                </span>
              </Tip>
            ) : (
              <Button size="sm" variant="outline" onClick={() => onPrint("client")}>
                <Printer className="size-3.5" /> Client copy
              </Button>
            )}
            <Button size="sm" variant="ghost" onClick={() => onPrint("caseworker")}>
              <Printer className="size-3.5" /> Caseworker copy
            </Button>
            <span className="ms-auto text-[12px] text-muted">
              {fmtSec(e.result.timings.total ?? Object.values(e.result.timings).reduce((s, x) => s + x, 0))}
              {typeof e.result.tokens === "object" && e.result.tokens ? ` · ${((e.result.tokens.prompt ?? 0) + (e.result.tokens.completion ?? 0)).toLocaleString("en")} tokens` : typeof e.result.tokens === "number" ? ` · ${e.result.tokens} tokens` : ""}
            </span>
          </div>
        </>
      )}
    </div>
  );
}

function DiffText({ text, facts, sharedWith }: { text: string; facts: Fact[]; sharedWith: { text: string; shared: boolean }[] }) {
  const byId = new Map(facts.map((f) => [f.id, f]));
  return (
    <p className="text-[14px] leading-[1.75] whitespace-pre-line text-body" aria-label={text}>
      {sharedWith.map((t, i) => {
        const m = /^⟦([A-Z]{1,3}\d{1,3})⟧$/.exec(t.text);
        if (m) {
          const f = byId.get(m[1]);
          return <FactChip key={i} id={m[1]} fact={f} text={f ? renderFactValue(f) : t.text} size="sm" tooltip={false} />;
        }
        return t.shared ? (
          <React.Fragment key={i}>{t.text}</React.Fragment>
        ) : (
          <mark key={i} className="rounded-[4px] bg-warn-soft px-[1px] text-ink">
            {t.text}
          </mark>
        );
      })}
    </p>
  );
}

function VerificationView({ ws }: { ws: Workspace }) {
  const r = ws.explain.result;
  const facts = ws.analysis?.facts ?? NO_FACTS;
  const lang = ws.languages.find((l) => l.code === (ws.explain.lang ?? ws.targetLang)) ?? null;
  const diff = React.useMemo(() => (r?.reference ? wordDiff(r.reference, r.back_translation) : null), [r]);
  if (!r)
    return (
      <div className="grid min-h-[320px] place-items-center text-center">
        <div className="max-w-[320px]">
          <div className="mx-auto grid size-14 place-items-center rounded-full bg-sand-2 text-ink">
            <ShieldCheck className="size-6" />
          </div>
          <p className="mt-4 text-[17px] font-semibold tracking-[-0.02em] text-ink">Nothing to verify yet</p>
          <p className="mt-1.5 text-[14px] text-muted">
            {ws.explain.status === "streaming" ? "Verification runs as soon as the explanation is complete." : "Run an explanation first. Every one is back-translated and audited before you hand it over."}
          </p>
        </div>
      </div>
    );
  const expected = [...new Set([...placeholdersIn(r.reference ?? r.masked), ...r.placeholder_audit.missing])].filter((id) => !r.placeholder_audit.unexpected.includes(id));
  const byId = new Map(facts.map((f) => [f.id, f]));
  const labels = Object.fromEntries(expected.map((id) => [id, byId.get(id) ? `${TYPE_LABEL[byId.get(id)!.type] ?? byId.get(id)!.type} · ${renderFactValue(byId.get(id)!)}` : ""]));
  const meta = GATE_META[r.gate.status];
  const letterLang = ws.analysis?.letter_lang.toUpperCase() ?? "";
  return (
    <div className="flex flex-col gap-5">
      <div className={cn("rounded-3xl p-5", meta.cls)}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <GateBadge status={r.gate.status} size="lg" className="bg-white/70" />
          <span className="text-[12.5px] font-medium">Confidence gate · {lang?.name ?? r.target_lang}</span>
        </div>
        <p className="mt-3 text-[14.5px] font-semibold text-ink">{meta.help}</p>
        <ul className="mt-2 space-y-1 text-[13.5px] leading-relaxed text-ink/80">
          {r.gate.reasons.map((x, i) => (
            <li key={i} className="flex gap-2">
              <span className={cn("mt-2 size-1.5 shrink-0 rounded-full", meta.dot)} />
              {x}
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-2xl bg-paper p-4 ring-1 ring-line">
        <ChrfMeter value={r.chrf} thresholds={r.gate.thresholds ?? lang?.thresholds ?? null} />
        <p className="mt-2 text-[12.5px] leading-relaxed text-muted">
          chrF between the back-translation and the {letterLang} plain explanation. Below {(r.gate.thresholds ?? lang?.thresholds)?.review ?? "the review threshold"}: interpreter; below {(r.gate.thresholds ?? lang?.thresholds)?.ready ?? "the ready threshold"}: review with the client.
        </p>
      </div>

      <div>
        <SectionLabel>Placeholder audit</SectionLabel>
        <PlaceholderChecklist expected={expected} audit={r.placeholder_audit} labels={labels} columns={1} />
      </div>

      <div>
        <SectionLabel>Round trip · side by side</SectionLabel>
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          <div className="rounded-2xl bg-paper p-4 ring-1 ring-line">
            <p className="mb-2 text-[12px] font-semibold text-muted">Source plain explanation · {letterLang}</p>
            {r.reference && diff ? <DiffText text={r.reference} facts={facts} sharedWith={diff.a} /> : <p className="text-[13.5px] text-muted">The backend did not return the reference text.</p>}
          </div>
          <div className="rounded-2xl bg-paper p-4 ring-1 ring-line">
            <p className="mb-2 text-[12px] font-semibold text-muted">Back-translation · {letterLang}</p>
            {diff ? <DiffText text={r.back_translation} facts={facts} sharedWith={diff.b} /> : <p className="text-[14px] leading-[1.75] whitespace-pre-line text-body">{r.back_translation}</p>}
          </div>
        </div>
        {diff && (
          <p className="mt-2 flex items-center gap-2 text-[12px] text-muted">
            <mark className="rounded-[4px] bg-warn-soft px-1 text-ink">highlighted</mark> words differ between the two texts
          </p>
        )}
      </div>

      {Object.keys(r.timings).length > 0 && (
        <dl className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {Object.entries(r.timings).map(([k, v]) => (
            <div key={k} className="rounded-xl bg-sand-2/70 px-3 py-2">
              <dt className="text-[11px] text-muted">{k.replace(/_/g, " ")}</dt>
              <dd className="t-num text-[14px] font-semibold text-ink">{fmtSec(v)}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}

function ReplyView({ ws, onPrint }: { ws: Workspace; onPrint: (k: "client" | "caseworker") => void }) {
  const a = ws.analysis;
  const lang = ws.language;
  const facts = a?.facts ?? NO_FACTS;
  const example = ws.api?.source === "mock" && ws.source?.kind === "sample" ? MOCK_CLIENT_MESSAGES[ws.source.id]?.[ws.targetLang] : undefined;
  const { copied, copy } = useCopy();
  const res = ws.reply.result;
  const segs = React.useMemo(() => (res ? highlightValues(res.reply_letter, facts) : []), [res, facts]);
  const used = res?.facts_used.map((id) => facts.find((f) => f.id === id)).filter((f): f is Fact => !!f) ?? [];
  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="mb-2 flex items-center justify-between gap-2">
          <label htmlFor="client-msg" className="text-[13px] font-medium text-ink">
            Client&apos;s answer in{" "}
            <span lang={lang ? langAttr(lang.code) : undefined} className="font-semibold">
              {lang?.native_name ?? "their language"}
            </span>
          </label>
          {example && (
            <button onClick={() => ws.setClientMessage(example)} className="inline-flex shrink-0 items-center gap-1 rounded-pill bg-sand-2 px-2.5 py-1 text-[12px] font-medium text-ink hover:bg-sand">
              <Wand2 className="size-3" /> Use example message
            </button>
          )}
        </div>
        <textarea
          id="client-msg"
          value={ws.clientMessage}
          onChange={(e) => ws.setClientMessage(e.target.value)}
          lang={lang ? langAttr(lang.code) : undefined}
          dir="auto"
          rows={4}
          placeholder="Type or paste what the client wants to say…"
          className="scrollbar-thin w-full resize-y rounded-2xl border border-line bg-paper p-4 text-[16px] leading-relaxed text-ink outline-none placeholder:text-faint focus:border-ink/25"
        />
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <Button onClick={() => void ws.runReply()} disabled={!a || !ws.clientMessage.trim() || ws.reply.status === "loading"}>
            {ws.reply.status === "loading" ? <Loader2 className="size-4 animate-spin" /> : <MessageSquareReply className="size-4" />}
            {ws.reply.status === "loading" ? "Drafting…" : "Draft formal reply"}
          </Button>
          <span className="text-[12.5px] text-muted">Drafted in {a ? a.letter_lang.toUpperCase() : "the letter's language"} with the reference and facts locked.</span>
        </div>
      </div>

      {ws.reply.status === "error" && <ErrorCard title="No draft this time" message={ws.reply.error ?? "Unknown error"} />}

      <AnimatePresence>
        {res && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.4, ease: EASE }} className="flex flex-col gap-3">
            <div className="rounded-2xl bg-paper p-5 ring-1 ring-line sm:p-6">
              <p className="mb-3 text-[11.5px] font-semibold tracking-[0.06em] text-muted uppercase">Draft · for caseworker approval</p>
              <div className="text-[14px] leading-[1.75] whitespace-pre-line text-ink">
                <SegmentText segments={segs} facts={facts} size="sm" />
              </div>
            </div>
            {used.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5 text-[12.5px] text-muted">
                Locked facts used:
                {used.map((f) => (
                  <FactChip key={f.id} id={f.id} fact={f} text={`⟦${f.id}⟧`} size="sm" />
                ))}
              </div>
            )}
            <div className="flex flex-wrap gap-2">
              <Button size="sm" variant="outline" onClick={() => copy(res.reply_letter)}>
                {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />} {copied ? "Copied" : "Copy draft"}
              </Button>
              <Button size="sm" variant="ghost" onClick={() => onPrint("caseworker")}>
                <Printer className="size-3.5" /> Caseworker copy
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function ClientPane({
  ws,
  tab,
  setTab,
  activeFact,
  setActiveFact,
  onPrint,
  className,
}: {
  ws: Workspace;
  tab: ClientTab;
  setTab: (t: ClientTab) => void;
  activeFact: string | null;
  setActiveFact: (id: string | null) => void;
  onPrint: (k: "client" | "caseworker") => void;
  className?: string;
}) {
  const l = ws.language;
  const status = ws.explain.result?.gate.status;
  return (
    <Pane className={className}>
      <Tabs value={tab} onValueChange={(v) => setTab(v as ClientTab)} className="flex min-h-0 flex-1 flex-col">
        <PaneHeader
          icon={<Languages className="size-4" />}
          title={
            <span className="flex items-center gap-2">
              Client
              <LanguagePicker ws={ws} align="start">
                <button className="rounded-pill bg-sand-2 px-2.5 py-0.5 text-[14px] font-semibold text-ink hover:bg-sand" aria-label="Change client language">
                  <span lang={l ? langAttr(l.code) : undefined}>{l?.native_name ?? "—"}</span>
                </button>
              </LanguagePicker>
            </span>
          }
          aside={status ? <span className={cn("size-2.5 rounded-full", GATE_META[status].dot)} title={GATE_META[status].label} /> : null}
        >
          <div className="mt-3 -mb-0.5 overflow-x-auto no-scrollbar">
            <PillTabs
              id="client-tabs"
              value={tab}
              size="sm"
              items={[
                { value: "explanation", label: "Explanation" },
                { value: "verification", label: "Verification" },
                { value: "reply", label: "Reply" },
              ]}
            />
          </div>
        </PaneHeader>
        <PaneBody>
          <TabsContent value="explanation" className="outline-none">
            <ExplanationView ws={ws} activeFact={activeFact} setActiveFact={setActiveFact} onPrint={onPrint} />
          </TabsContent>
          <TabsContent value="verification" className="outline-none">
            <VerificationView ws={ws} />
          </TabsContent>
          <TabsContent value="reply" className="outline-none">
            <ReplyView ws={ws} onPrint={onPrint} />
          </TabsContent>
        </PaneBody>
      </Tabs>
    </Pane>
  );
}
