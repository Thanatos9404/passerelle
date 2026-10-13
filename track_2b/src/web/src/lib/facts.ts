import type { Fact, FactType } from "@/lib/api/types";

export type FactFamily = "date" | "amount" | "id" | "contact";

export function factFamily(t: FactType): FactFamily {
  switch (t) {
    case "date":
    case "deadline":
    case "duration":
    case "time":
      return "date";
    case "amount":
    case "iban":
      return "amount";
    case "reference":
    case "ahv":
      return "id";
    default:
      return "contact";
  }
}

export const FAMILY_STYLE: Record<FactFamily, { text: string; bg: string; ring: string; dot: string; label: string }> = {
  date: { text: "text-f-date", bg: "bg-f-date-soft", ring: "decoration-f-date/50", dot: "bg-f-date", label: "Dates & times" },
  amount: { text: "text-f-amount", bg: "bg-f-amount-soft", ring: "decoration-f-amount/50", dot: "bg-f-amount", label: "Money" },
  id: { text: "text-f-id", bg: "bg-f-id-soft", ring: "decoration-f-id/50", dot: "bg-f-id", label: "References" },
  contact: { text: "text-f-contact", bg: "bg-f-contact-soft", ring: "decoration-f-contact/50", dot: "bg-f-contact", label: "Contact & people" },
};

export const TYPE_LABEL: Record<string, string> = {
  date: "Date",
  deadline: "Deadline",
  time: "Time",
  amount: "Amount",
  iban: "IBAN",
  reference: "Reference",
  ahv: "AHV/AVS no.",
  phone: "Phone",
  duration: "Period",
  address: "Address",
  email: "Email",
  name: "Name",
};

/** Placeholder token as used by fact-lock: ⟦D1⟧ */
export const PLACEHOLDER_RE = /⟦([A-Z]{1,3}\d{1,3})⟧/g;

export function isoToSwiss(iso: string): string | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  return m ? `${m[3]}.${m[2]}.${m[1]}` : null;
}

function groupChf(n: number): string {
  const [i, d] = n.toFixed(2).split(".");
  return `${i.replace(/\B(?=(\d{3})+(?!\d))/g, "'")}.${d}`;
}

/**
 * Locale-safe rendering of a locked fact (what fact-lock re-inserts):
 * dates as dd.mm.yyyy, money as CHF 1'234.50, IBAN in groups of four. Falls back to the source value.
 */
export function renderFactValue(f: Pick<Fact, "type" | "value" | "normalized" | "display">): string {
  if (f.display) return f.display;
  const n = f.normalized ?? "";
  if ((f.type === "date" || f.type === "deadline") && n) return isoToSwiss(n) ?? f.value;
  if (f.type === "amount" && n) {
    const m = /(-?\d+(?:\.\d+)?)\s*([A-Z]{3})?/.exec(n);
    if (m) return `${m[2] ?? "CHF"} ${groupChf(Number(m[1]))}`;
  }
  if (f.type === "time" && n) return n.replace("-", "–");
  if (f.type === "iban" && n) return n.replace(/(.{4})/g, "$1 ").trim();
  return f.value;
}

export type Segment = { kind: "text"; text: string } | { kind: "fact"; id: string; text: string };

/** Split masked text into text and placeholder segments. Unknown ids keep their token text. */
export function splitMasked(masked: string, facts: Fact[], rendered?: Record<string, string>): Segment[] {
  const byId = new Map(facts.map((f) => [f.id, f]));
  const out: Segment[] = [];
  let last = 0;
  for (const m of masked.matchAll(PLACEHOLDER_RE)) {
    const idx = m.index ?? 0;
    if (idx > last) out.push({ kind: "text", text: masked.slice(last, idx) });
    const id = m[1];
    const f = byId.get(id);
    out.push({ kind: "fact", id, text: rendered?.[id] ?? (f ? renderFactValue(f) : m[0]) });
    last = idx + m[0].length;
  }
  if (last < masked.length) out.push({ kind: "text", text: masked.slice(last) });
  return out;
}

/**
 * Recover the exact values the backend re-inserted, by aligning the masked text with the
 * unmasked explanation (literal chunks between placeholders must match in order).
 */
export function alignRendered(masked: string, unmasked: string): Record<string, string> {
  const parts = masked.split(PLACEHOLDER_RE); // [text, id, text, id, ...]
  const out: Record<string, string> = {};
  let pos = 0;
  if (!unmasked.startsWith(parts[0])) return out;
  pos = parts[0].length;
  for (let i = 1; i < parts.length; i += 2) {
    const id = parts[i];
    const next = parts[i + 1] ?? "";
    const end = next ? unmasked.indexOf(next, pos) : unmasked.length;
    if (end < 0) return out;
    if (!(id in out)) out[id] = unmasked.slice(pos, end);
    pos = end + next.length;
  }
  return out;
}

/** Segments from unmasked text + the backend's fact spans (exact, no alignment guesswork). */
export function segmentsFromSpans(text: string, spans: { id: string; start: number; end: number }[]): Segment[] {
  const out: Segment[] = [];
  let pos = 0;
  for (const sp of [...spans].sort((a, b) => a.start - b.start)) {
    if (sp.start < pos || sp.end > text.length) continue;
    if (sp.start > pos) out.push({ kind: "text", text: text.slice(pos, sp.start) });
    out.push({ kind: "fact", id: sp.id, text: text.slice(sp.start, sp.end) });
    pos = sp.end;
  }
  if (pos < text.length) out.push({ kind: "text", text: text.slice(pos) });
  return out;
}

/** Best segmentation of a finished explanation. */
export function explanationSegments(r: { explanation: string; masked: string; fact_spans?: { id: string; start: number; end: number }[] }, facts: Fact[]): Segment[] {
  if (r.fact_spans?.length) return segmentsFromSpans(r.explanation, r.fact_spans);
  return splitMasked(r.masked, facts, alignRendered(r.masked, r.explanation));
}

/** Highlight fact values inside plain text (used for reply letters). */
export function highlightValues(text: string, facts: Fact[]): Segment[] {
  const needles = facts
    .flatMap((f) => [f.value, renderFactValue(f), f.value.replace(/, /g, "\n")].filter((v, i, a) => v && v.length > 2 && a.indexOf(v) === i).map((v) => ({ id: f.id, v })))
    .sort((a, b) => b.v.length - a.v.length);
  const marks: { s: number; e: number; id: string }[] = [];
  for (const { id, v } of needles) {
    let from = 0;
    for (;;) {
      const i = text.indexOf(v, from);
      if (i < 0) break;
      if (!marks.some((m) => i < m.e && i + v.length > m.s)) marks.push({ s: i, e: i + v.length, id });
      from = i + v.length;
    }
  }
  marks.sort((a, b) => a.s - b.s);
  const out: Segment[] = [];
  let last = 0;
  for (const m of marks) {
    if (m.s > last) out.push({ kind: "text", text: text.slice(last, m.s) });
    out.push({ kind: "fact", id: m.id, text: text.slice(m.s, m.e) });
    last = m.e;
  }
  if (last < text.length) out.push({ kind: "text", text: text.slice(last) });
  return out;
}

export function placeholdersIn(masked: string): string[] {
  return [...masked.matchAll(PLACEHOLDER_RE)].map((m) => m[1]);
}

/** Whole days from today (local) to an ISO date; negative = past. */
export function daysUntil(iso: string, now = new Date()): number | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!m) return null;
  const target = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return Math.round((target.getTime() - today.getTime()) / 86_400_000);
}

export function longDate(iso: string | null): string {
  if (!iso) return "—";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!m) return iso;
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  return d.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "long", year: "numeric" });
}
