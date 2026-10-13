"use client";

import * as React from "react";
import type { Fact } from "@/lib/api/types";
import { FAMILY_STYLE, TYPE_LABEL, factFamily } from "@/lib/facts";
import { cn } from "@/lib/utils";

type Piece = { text: string; fact?: Fact };

export function pieces(text: string, facts: Fact[]): Piece[] {
  const spans = facts
    .flatMap((f) => (f.spans?.length ? f.spans : f.span ? [f.span] : []).map((sp) => ({ f, sp })))
    .filter(({ sp }) => sp[0] >= 0 && sp[1] <= text.length && sp[1] > sp[0])
    .sort((a, b) => a.sp[0] - b.sp[0]);
  const out: Piece[] = [];
  let pos = 0;
  for (const { f, sp } of spans) {
    const [s, e] = sp;
    if (s < pos) continue; // overlapping span — keep the first
    if (s > pos) out.push({ text: text.slice(pos, s) });
    out.push({ text: text.slice(s, e), fact: f });
    pos = e;
  }
  if (pos < text.length) out.push({ text: text.slice(pos) });
  return out;
}

/** The letter with fact spans highlighted; hovering a span highlights the fact everywhere. */
export function LetterText({
  text,
  facts,
  activeId,
  onHover,
  redact = false,
  className,
}: {
  text: string;
  facts: Fact[];
  activeId?: string | null;
  onHover?: (id: string | null) => void;
  redact?: boolean;
  className?: string;
}) {
  const ps = React.useMemo(() => pieces(text, facts), [text, facts]);
  return (
    <div className={cn("text-[13.5px] leading-[1.7] whitespace-pre-wrap text-body", className)}>
      {ps.map((p, i) => {
        if (!p.fact) return <React.Fragment key={i}>{p.text}</React.Fragment>;
        const fam = FAMILY_STYLE[factFamily(p.fact.type)];
        const hidden = redact && (p.fact.type === "name" || p.fact.type === "address");
        const active = activeId === p.fact.id;
        return (
          <mark
            key={i}
            data-fact={p.fact.id}
            title={`${TYPE_LABEL[p.fact.type] ?? p.fact.type} · ⟦${p.fact.id}⟧`}
            onMouseEnter={() => onHover?.(p.fact!.id)}
            onMouseLeave={() => onHover?.(null)}
            className={cn(
              "rounded-[5px] px-[2px] py-[1px] text-ink underline decoration-2 underline-offset-[3px] transition-[background-color,box-shadow] duration-200 [box-decoration-break:clone]",
              fam.bg,
              fam.ring,
              active && "shadow-[0_0_0_2px_currentColor] " + fam.text,
              hidden && "bg-ink text-transparent decoration-transparent select-none",
            )}
          >
            {hidden ? p.text.replace(/\S/g, "x") : p.text}
          </mark>
        );
      })}
    </div>
  );
}

export function FactLegend({ className }: { className?: string }) {
  return (
    <ul className={cn("flex flex-wrap gap-x-4 gap-y-1.5 text-[12px] text-muted", className)}>
      {(Object.keys(FAMILY_STYLE) as (keyof typeof FAMILY_STYLE)[]).map((k) => (
        <li key={k} className="inline-flex items-center gap-1.5">
          <span className={cn("size-2 rounded-full", FAMILY_STYLE[k].dot)} />
          {FAMILY_STYLE[k].label}
        </li>
      ))}
    </ul>
  );
}
