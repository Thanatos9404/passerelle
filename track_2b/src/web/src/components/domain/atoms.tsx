"use client";

import * as React from "react";
import { CircleAlert, CircleCheck, Lock, OctagonX } from "lucide-react";
import type { Fact, GateStatus } from "@/lib/api/types";
import { FAMILY_STYLE, TYPE_LABEL, factFamily, renderFactValue, type Segment } from "@/lib/facts";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

/** Inline locked-fact chip. Always LTR-isolated so numbers survive inside RTL text. */
export function FactChip({
  fact,
  text,
  id,
  size = "md",
  active,
  onHover,
  tooltip = true,
}: {
  fact?: Fact;
  text: string;
  id: string;
  size?: "sm" | "md";
  active?: boolean;
  onHover?: (id: string | null) => void;
  tooltip?: boolean;
}) {
  const fam = FAMILY_STYLE[factFamily(fact?.type ?? "reference")];
  const chip = (
    <span
      dir="ltr"
      tabIndex={tooltip ? 0 : undefined}
      onMouseEnter={() => onHover?.(id)}
      onMouseLeave={() => onHover?.(null)}
      onFocus={() => onHover?.(id)}
      onBlur={() => onHover?.(null)}
      className={cn(
        "mx-[1px] inline-flex items-baseline gap-1 rounded-[7px] align-baseline font-semibold whitespace-nowrap [unicode-bidi:isolate] outline-none",
        size === "sm" ? "px-1.5 py-[1px] text-[0.92em]" : "px-1.5 py-[2px] text-[0.95em]",
        fam.bg,
        fam.text,
        active && "ring-2 ring-current/35",
        "transition-shadow focus-visible:ring-2 focus-visible:ring-ink/40",
      )}
      style={{ fontFamily: "var(--font-runde), ui-sans-serif, system-ui, sans-serif", lineHeight: 1.35 }}
    >
      <Lock className="size-[0.72em] translate-y-[0.05em] self-center opacity-70" aria-hidden strokeWidth={2.6} />
      {text}
    </span>
  );
  if (!tooltip) return chip;
  return (
    <Tooltip>
      <TooltipTrigger asChild>{chip}</TooltipTrigger>
      <TooltipContent>
        <span className="block text-[11px] font-semibold tracking-[0.06em] text-white/60 uppercase">
          Locked fact ⟦{id}⟧ · {TYPE_LABEL[fact?.type ?? ""] ?? fact?.type ?? "fact"}
        </span>
        <span className="mt-0.5 block">In the letter: {fact?.value ?? "—"}</span>
        {fact && renderFactValue(fact) !== fact.value && <span className="block text-white/70">Rendered as: {renderFactValue(fact)}</span>}
      </TooltipContent>
    </Tooltip>
  );
}

/** Render text/fact segments with chips. */
export function SegmentText({
  segments,
  facts,
  activeId,
  onHover,
  size,
  tooltip = true,
}: {
  segments: Segment[];
  facts: Fact[];
  activeId?: string | null;
  onHover?: (id: string | null) => void;
  size?: "sm" | "md";
  tooltip?: boolean;
}) {
  const byId = React.useMemo(() => new Map(facts.map((f) => [f.id, f])), [facts]);
  return (
    <>
      {segments.map((s, i) =>
        s.kind === "text" ? (
          <React.Fragment key={i}>{s.text}</React.Fragment>
        ) : (
          <FactChip key={i} id={s.id} fact={byId.get(s.id)} text={s.text} active={activeId === s.id} onHover={onHover} size={size} tooltip={tooltip} />
        ),
      )}
    </>
  );
}

export const GATE_META: Record<GateStatus, { label: string; short: string; icon: typeof CircleCheck; cls: string; dot: string; help: string }> = {
  ready: {
    label: "Ready",
    short: "Ready",
    icon: CircleCheck,
    cls: "bg-ok-soft text-ok",
    dot: "bg-ok",
    help: "Facts intact and the round trip matches. Hand over the explanation.",
  },
  review: {
    label: "Review with client",
    short: "Review",
    icon: CircleAlert,
    cls: "bg-warn-soft text-warn",
    dot: "bg-warn",
    help: "Usable, but go through it together with the client before relying on it.",
  },
  interpreter: {
    label: "Use a human interpreter",
    short: "Interpreter",
    icon: OctagonX,
    cls: "bg-stop-soft text-stop",
    dot: "bg-stop",
    help: "Do not rely on this text. Book an interpreter for this letter.",
  },
};

export function GateBadge({ status, size = "md", className }: { status: GateStatus; size?: "sm" | "md" | "lg"; className?: string }) {
  const m = GATE_META[status];
  const Icon = m.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-pill font-semibold whitespace-nowrap",
        size === "sm" && "h-6 px-2.5 text-[12px]",
        size === "md" && "h-8 px-3 text-[13.5px]",
        size === "lg" && "h-10 px-4 text-[15px]",
        m.cls,
        className,
      )}
    >
      <Icon className={cn(size === "lg" ? "size-[18px]" : "size-4")} aria-hidden strokeWidth={2.4} />
      {m.label}
    </span>
  );
}

export function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="inline-flex h-5 min-w-5 items-center justify-center rounded-md border border-line bg-white px-1 font-sans text-[11px] font-medium text-muted">
      {children}
    </kbd>
  );
}

export function Eyebrow({ children, className }: { children: React.ReactNode; className?: string }) {
  return <p className={cn("text-[11.5px] font-semibold tracking-[0.06em] text-muted uppercase", className)}>{children}</p>;
}
