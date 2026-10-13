"use client";

import * as React from "react";
import { motion, useReducedMotion } from "motion/react";
import { CalendarClock, Check, CircleSlash, Copy, Plus } from "lucide-react";
import type { GateThresholds, PlaceholderAudit } from "@/lib/api/types";
import { daysUntil, longDate } from "@/lib/facts";
import { cn } from "@/lib/utils";

/** Deadline countdown tile with a soft progress ring (30-day horizon). */
export function DeadlineTile({
  label,
  iso,
  relative,
  emphasis = false,
  className,
  now,
}: {
  label: string;
  iso: string | null;
  relative?: string | null;
  emphasis?: boolean;
  className?: string;
  now?: Date;
}) {
  const [today, setToday] = React.useState<Date | null>(now ?? null);
  React.useEffect(() => {
    if (!now) setToday(new Date());
  }, [now]);
  const d = iso && today ? daysUntil(iso, today) : null;
  const past = d !== null && d < 0;
  const urgent = d !== null && d >= 0 && d <= 7;
  const frac = d === null ? 0 : past ? 1 : Math.max(0.04, 1 - Math.min(d, 30) / 30);
  const R = 22;
  const C = 2 * Math.PI * R;
  const tone = past ? "text-stop" : urgent ? "text-warn" : "text-f-date";
  return (
    <div className={cn("flex items-center gap-4 rounded-2xl p-4", emphasis ? "bg-white shadow-card" : "bg-sand-2/70", className)}>
      <div className={cn("relative grid size-[58px] shrink-0 place-items-center", tone)}>
        <svg viewBox="0 0 52 52" className="absolute inset-0 -rotate-90" aria-hidden>
          <circle cx="26" cy="26" r={R} fill="none" stroke="currentColor" strokeOpacity="0.14" strokeWidth="4" />
          <circle
            cx="26"
            cy="26"
            r={R}
            fill="none"
            stroke="currentColor"
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray={C}
            strokeDashoffset={C * (1 - frac)}
            style={{ transition: "stroke-dashoffset 1s cubic-bezier(.22,1,.36,1)" }}
          />
        </svg>
        <span className="t-num text-[17px] font-semibold text-ink">{d === null ? "—" : past ? "!" : d}</span>
      </div>
      <div className="min-w-0">
        <p className="text-[12px] font-semibold tracking-[0.04em] text-muted uppercase">{label}</p>
        <p className="mt-0.5 text-[17px] font-semibold tracking-[-0.02em] text-ink">
          {d === null ? (iso ? "—" : "Date not resolved") : past ? `${Math.abs(d)} day${Math.abs(d) === 1 ? "" : "s"} ago` : d === 0 ? "Today" : `in ${d} day${d === 1 ? "" : "s"}`}
        </p>
        <p className="mt-0.5 flex items-center gap-1.5 truncate text-[13px] text-body">
          <CalendarClock className="size-3.5 shrink-0 text-muted" aria-hidden />
          <span className="truncate">{iso ? longDate(iso) : relative ?? "—"}</span>
        </p>
      </div>
    </div>
  );
}

/** chrF meter: 0–100 track with the language's review/ready thresholds as ticks. */
export function ChrfMeter({ value, thresholds, compact = false }: { value: number | null; thresholds: GateThresholds | null; compact?: boolean }) {
  const reduce = useReducedMotion();
  const t = thresholds;
  const zone = value === null || !t ? "none" : value >= t.ready ? "ready" : value >= t.review ? "review" : "interpreter";
  const fill = { none: "bg-faint", ready: "bg-ok", review: "bg-warn", interpreter: "bg-stop" }[zone];
  return (
    <div className="w-full">
      <div className="flex items-baseline justify-between">
        <span className="text-[12px] font-semibold tracking-[0.04em] text-muted uppercase">Back-translation chrF</span>
        <span className={cn("t-num font-semibold text-ink", compact ? "text-[18px]" : "text-[26px]")}>{value === null ? "—" : value.toFixed(1)}</span>
      </div>
      <div className="relative mt-2 h-2.5 rounded-pill bg-sand">
        {t && (
          <>
            <div className="absolute inset-y-0 left-0 rounded-l-pill bg-stop/10" style={{ width: `${t.review}%` }} />
            <div className="absolute inset-y-0 bg-warn/10" style={{ left: `${t.review}%`, width: `${t.ready - t.review}%` }} />
            <div className="absolute inset-y-0 right-0 rounded-r-pill bg-ok/10" style={{ left: `${t.ready}%` }} />
          </>
        )}
        <motion.div
          className={cn("absolute inset-y-0 left-0 rounded-pill", fill)}
          initial={reduce ? false : { width: 0 }}
          animate={{ width: `${Math.max(0, Math.min(100, value ?? 0))}%` }}
          transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
        />
        {t &&
          [t.review, t.ready].map((x) => (
            <span key={x} className="absolute -top-1 -bottom-1 w-[2px] rounded bg-ink/70" style={{ left: `calc(${x}% - 1px)` }} />
          ))}
      </div>
      {!compact && (
        <div className="relative mt-1.5 h-4 text-[11px] text-muted">
          {t ? (
            <>
              <span className="absolute" style={{ left: `${t.review}%`, transform: "translateX(-50%)" }}>
                {t.review}
              </span>
              <span className="absolute" style={{ left: `${t.ready}%`, transform: "translateX(-50%)" }}>
                {t.ready}
              </span>
            </>
          ) : (
            <span>No thresholds for this language</span>
          )}
        </div>
      )}
    </div>
  );
}

/** Every placeholder from the source must appear exactly once in the explanation. */
export function PlaceholderChecklist({ expected, audit, labels, columns = 2 }: { expected: string[]; audit: PlaceholderAudit; labels?: Record<string, string>; columns?: 1 | 2 }) {
  const rows = [
    ...expected.map((id) => ({
      id,
      state: audit.missing.includes(id) ? "missing" : audit.duplicated.includes(id) ? "duplicated" : "ok",
    })),
    ...audit.unexpected.map((id) => ({ id, state: "unexpected" })),
  ];
  const icon = { ok: Check, missing: CircleSlash, duplicated: Copy, unexpected: Plus } as const;
  const tone = { ok: "bg-ok-soft text-ok", missing: "bg-stop-soft text-stop", duplicated: "bg-warn-soft text-warn", unexpected: "bg-stop-soft text-stop" } as const;
  const text = { ok: "exactly once", missing: "missing", duplicated: "duplicated", unexpected: "not in source" } as const;
  return (
    <ul className={cn("grid grid-cols-1 gap-1.5", columns === 2 && "sm:grid-cols-2")}>
      {rows.map((r) => {
        const s = r.state as keyof typeof icon;
        const Icon = icon[s];
        return (
          <li key={`${r.id}-${s}`} className="flex items-center gap-2.5 rounded-xl bg-white px-2.5 py-2 text-[13px] ring-1 ring-line">
            <span className={cn("grid size-6 shrink-0 place-items-center rounded-full", tone[s])}>
              <Icon className="size-3.5" strokeWidth={2.6} aria-hidden />
            </span>
            <span className="font-semibold text-ink">⟦{r.id}⟧</span>
            <span className="min-w-0 truncate text-muted">{labels?.[r.id] ?? ""}</span>
            <span className={cn("ml-auto shrink-0 text-[12px] font-medium", s === "ok" ? "text-ok" : s === "duplicated" ? "text-warn" : "text-stop")}>{text[s]}</span>
          </li>
        );
      })}
    </ul>
  );
}
