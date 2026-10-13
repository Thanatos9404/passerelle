"use client";

import * as React from "react";
import { FileText, Languages, Search, ShieldCheck, Sparkles } from "lucide-react";
import { MOCK_LETTERS, buildFacts } from "@/lib/mock/letters";
import { MOCK_EXPLANATIONS } from "@/lib/mock/explanations";
import { placeholdersIn, splitMasked } from "@/lib/facts";
import { MOCK_LANGUAGES, chrF } from "@/lib/api/mock";
import { LogoMark } from "@/components/brand/logo";
import { LetterText } from "@/components/domain/letter-text";
import { GateBadge, SegmentText } from "@/components/domain/atoms";
import { ChrfMeter, DeadlineTile } from "@/components/domain/widgets";
import { cn, fmtChf } from "@/lib/utils";

const LETTER = MOCK_LETTERS[0];
const FACTS = buildFacts(LETTER);
const AR_CORPUS = MOCK_EXPLANATIONS[LETTER.id].ar;
const AR = AR_CORPUS.masked;
// Illustration values are computed from the mock corpus, not typed in.
const AR_BACK = AR_CORPUS.drift.reduce((t, [a, b]) => t.replace(a, b), LETTER.reference);
const AR_CHRF = Math.round(chrF(AR_BACK, LETTER.reference) * 10) / 10;
const AR_THRESHOLDS = MOCK_LANGUAGES.find((l) => l.code === "ar")?.thresholds ?? null;
const N_PLACEHOLDERS = new Set(placeholdersIn(LETTER.reference)).size;

/** Scale a fixed-size design to its container width (keeps the miniature crisp). */
function useFitScale(designWidth: number) {
  const ref = React.useRef<HTMLDivElement>(null);
  const [scale, setScale] = React.useState(1);
  React.useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setScale(Math.min(1, e.contentRect.width / designWidth)));
    ro.observe(el);
    return () => ro.disconnect();
  }, [designWidth]);
  return { ref, scale };
}

function Chip({ children, className }: { children: React.ReactNode; className?: string }) {
  return <span className={cn("inline-flex h-7 items-center gap-1.5 rounded-pill bg-white px-2.5 text-[12px] font-medium text-body ring-1 ring-line", className)}>{children}</span>;
}

function Panel({ title, icon, right, children, className }: { title: string; icon: React.ReactNode; right?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex min-h-0 flex-col overflow-hidden rounded-[20px] bg-white ring-1 ring-line", className)}>
      <div className="flex items-center gap-2 border-b border-line px-4 py-3">
        <span className="grid size-7 place-items-center rounded-full bg-sand-2 text-ink">{icon}</span>
        <span className="text-[13.5px] font-semibold tracking-[-0.01em] text-ink">{title}</span>
        <span className="ml-auto">{right}</span>
      </div>
      <div className="min-h-0 flex-1 p-4">{children}</div>
    </div>
  );
}

export function ProductMockupCanvas({ className }: { className?: string }) {
  const W = 1180;
  const H = 660;
  const { ref, scale } = useFitScale(W);
  const [active, setActive] = React.useState<string | null>(null);
  const segs = React.useMemo(() => splitMasked(AR, FACTS), []);
  return (
    <div ref={ref} className={cn("w-full", className)} style={{ height: H * scale }}>
      <div
        style={{ width: W, height: H, transform: `scale(${scale})`, transformOrigin: "top left" }}
        className="flex flex-col overflow-hidden rounded-[26px] bg-sand-2 shadow-float ring-1 ring-black/5"
        aria-hidden
      >
        {/* top bar */}
        <div className="flex h-[58px] shrink-0 items-center gap-3 border-b border-line bg-white/80 px-5">
          <LogoMark className="size-7" />
          <span className="text-[14px] font-semibold text-ink">Workspace</span>
          <span className="text-faint">/</span>
          <span className="text-[14px] text-body">Zahlungsbefehl · 26-048173</span>
          <div className="mx-auto flex h-9 w-[300px] items-center gap-2 rounded-pill bg-sand-2 px-3.5 text-[13px] text-faint">
            <Search className="size-3.5" /> Search letters, languages… <span className="ml-auto text-[11px]">Ctrl K</span>
          </div>
          <Chip>
            <span className="size-1.5 rounded-full bg-ok" /> Apertus 8B · local GPU
          </Chip>
          <Chip>
            <ShieldCheck className="size-3.5 text-ok" /> Egress blocked
          </Chip>
        </div>
        {/* panes */}
        <div className="grid min-h-0 flex-1 grid-cols-[1.02fr_0.86fr_1.12fr] gap-3 p-3">
          <Panel title="Letter" icon={<FileText className="size-3.5" />} right={<Chip>DE · Sample</Chip>}>
            <div className="relative h-full overflow-hidden">
              <LetterText text={LETTER.text} facts={FACTS} activeId={active} onHover={setActive} className="text-[12px] leading-[1.62]" />
              <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-white to-transparent" />
            </div>
          </Panel>
          <Panel title="Fact card" icon={<Sparkles className="size-3.5" />} right={<Chip>{FACTS.length} facts locked</Chip>}>
            <div className="flex flex-col gap-3">
              <div>
                <p className="text-[11px] font-semibold tracking-[0.05em] text-muted uppercase">Payment order · Zahlungsbefehl</p>
                <p className="mt-1 text-[15px] leading-snug font-semibold tracking-[-0.02em] text-ink">Betreibungsamt Aarenfeld</p>
              </div>
              <DeadlineTile label="Objection due" iso="2026-10-22" emphasis={false} />
              <DeadlineTile label="Payment due" iso="2026-11-01" />
              <div className="rounded-2xl bg-sand-2/70 p-3.5">
                {[
                  ["Claim", 1248.6],
                  ["Cost of the order", 73.3],
                ].map(([l, v]) => (
                  <div key={l as string} className="flex items-center justify-between py-1 text-[13px]">
                    <span className="text-body">{l}</span>
                    <span className="t-num font-semibold text-ink">{fmtChf(v as number)}</span>
                  </div>
                ))}
              </div>
            </div>
          </Panel>
          <Panel
            title="Client explanation"
            icon={<Languages className="size-3.5" />}
            right={
              <Chip>
                <span lang="ar" className="text-[13px] leading-none">العربية</span> · RTL
              </Chip>
            }
          >
            <div className="flex h-full flex-col gap-3">
              <div className="flex items-center justify-between">
                <GateBadge status="ready" size="sm" />
                <span className="text-[12px] text-muted">all {N_PLACEHOLDERS} placeholders intact</span>
              </div>
              <div lang="ar" dir="rtl" className="relative min-h-0 flex-1 overflow-hidden text-[14.5px] whitespace-pre-line text-ink">
                <SegmentText segments={segs} facts={FACTS} activeId={active} onHover={setActive} size="sm" tooltip={false} />
                <div className="pointer-events-none absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-white to-transparent" />
              </div>
              <div className="rounded-2xl bg-sand-2/70 p-3">
                <ChrfMeter value={AR_CHRF} thresholds={AR_THRESHOLDS} compact />
              </div>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

/** Phone-width variant: the two cards a caseworker hands over — deadline and the client text. */
export function ProductMockupMobile({ className }: { className?: string }) {
  const segs = React.useMemo(() => splitMasked(AR.split("\n\n").slice(0, 2).join("\n\n"), FACTS), []);
  return (
    <div className={cn("flex flex-col gap-2.5 rounded-[22px] bg-sand-2 p-2.5 shadow-float ring-1 ring-black/5", className)} aria-hidden>
      <div className="flex items-center justify-between rounded-2xl bg-white px-3.5 py-3 ring-1 ring-line">
        <span className="flex items-center gap-2 text-[13px] font-semibold text-ink">
          <LogoMark className="size-6" /> Zahlungsbefehl
        </span>
        <GateBadge status="ready" size="sm" />
      </div>
      <DeadlineTile label="Objection due" iso="2026-10-22" emphasis />
      <div className="rounded-2xl bg-white p-4 ring-1 ring-line">
        <div className="mb-2 flex items-center justify-between text-[12px] text-muted">
          <span lang="ar" className="text-[14px] text-ink">العربية</span>
          <span>{N_PLACEHOLDERS} facts locked</span>
        </div>
        <p lang="ar" dir="rtl" className="text-[14px] whitespace-pre-line text-ink">
          <SegmentText segments={segs} facts={FACTS} size="sm" tooltip={false} />
        </p>
      </div>
    </div>
  );
}
