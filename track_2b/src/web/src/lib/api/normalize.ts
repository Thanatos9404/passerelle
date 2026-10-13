/**
 * Defensive normalisers: the backend is being built in parallel, so the UI accepts a few
 * reasonable shapes for each payload and fills documented defaults instead of crashing.
 */
import type {
  AnalyzeResponse,
  AuditEntry,
  ExplainResponse,
  FactCard,
  GateStatus,
  Health,
  Language,
  LetterLang,
  ReplyResponse,
  Sample,
} from "./types";

type Obj = Record<string, unknown>;
const isObj = (v: unknown): v is Obj => typeof v === "object" && v !== null && !Array.isArray(v);
const str = (v: unknown, d = ""): string => (typeof v === "string" ? v : v == null ? d : String(v));
const strOrNull = (v: unknown): string | null => (typeof v === "string" && v.trim() ? v : null);
const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : typeof v === "string" && v.trim() !== "" && Number.isFinite(Number(v)) ? Number(v) : null);
const arr = <T = unknown>(v: unknown): T[] => (Array.isArray(v) ? (v as T[]) : []);
const unwrap = (v: unknown, key: string): unknown => (isObj(v) && key in v ? v[key] : v);
const human = (v: unknown): string | null => {
  const t = strOrNull(v);
  if (!t) return null;
  if (!/^[a-z0-9_]+$/.test(t)) return t;
  const h = t.replace(/_/g, " ");
  return h.charAt(0).toUpperCase() + h.slice(1);
};
const spanOf = (x: unknown): [number, number] | null => {
  const sp = Array.isArray(x) && x.length === 2 ? [num(x[0]), num(x[1])] : isObj(x) ? [num(x.start), num(x.end)] : null;
  return sp && sp[0] !== null && sp[1] !== null ? [sp[0], sp[1]] : null;
};
/** Backend timings are milliseconds with *_ms keys; the UI works in seconds. */
function normTimings(v: unknown): Record<string, number> {
  if (!isObj(v)) return {};
  const out: Record<string, number> = {};
  for (const [k, x] of Object.entries(v)) {
    const n = num(x);
    if (n === null) continue;
    if (k.endsWith("_ms")) out[k.slice(0, -3)] = n / 1000;
    else out[k] = n;
  }
  return out;
}

export function normGate(v: unknown): GateStatus {
  const s = str(v).toLowerCase();
  if (["ready", "ok", "green", "pass", "✅"].some((k) => s.includes(k))) return "ready";
  if (["interpreter", "human", "red", "block", "stop", "fail", "⛔"].some((k) => s.includes(k))) return "interpreter";
  return "review";
}

export function normHealth(v: unknown): Health {
  const o = isObj(v) ? v : {};
  return {
    status: str(o.status, "unknown"),
    model: strOrNull(o.model),
    backend_reachable: Boolean(o.backend_reachable ?? o.llm_reachable ?? false),
  };
}

export function normLanguages(v: unknown): Language[] {
  return arr(unwrap(v, "languages")).filter(isObj).map((o) => {
    const t = isObj(o.thresholds) ? o.thresholds : isObj(o.gate_thresholds) ? o.gate_thresholds : null;
    const ready = t ? num(t.ready ?? t.green ?? t.pass) : null;
    const review = t ? num(t.review ?? t.amber ?? t.warn) : null;
    return {
      code: str(o.code ?? o.id),
      name: str(o.name ?? o.english_name ?? o.code),
      native_name: str(o.native_name ?? o.native ?? o.name),
      script: ({ Ethi: "Ethiopic", Arab: "Arabic", Cyrl: "Cyrillic", Taml: "Tamil", Latn: "Latin", Deva: "Devanagari", Grek: "Greek" } as Record<string, string>)[str(o.script)] ?? str(o.script, "Latin"),
      rtl: Boolean(o.rtl),
      thresholds: ready !== null && review !== null ? { ready, review } : null,
      quality_tier: ((t: string | null) => (t && t !== "not_evaluated" ? t : null))(strOrNull(o.quality_tier ?? o.tier)),
    };
  });
}

const asLang = (v: unknown): LetterLang => {
  const s = str(v).toLowerCase().slice(0, 2);
  return s === "fr" || s === "it" ? s : "de";
};

export function normSamples(v: unknown): Sample[] {
  return arr(unwrap(v, "samples")).filter(isObj).map((o) => ({
    id: str(o.id),
    title: str(o.title ?? o.id),
    language: asLang(o.language ?? o.lang),
    type: human(o.type ?? o.letter_type) ?? "",
  }));
}

function normCard(v: unknown): FactCard {
  const o = isObj(v) ? v : {};
  const contact = isObj(o.contact) ? o.contact : null;
  const deadlines: FactCard["deadlines"] = arr(o.deadlines).map((d) =>
    isObj(d)
      ? {
          label: human(d.label) ?? "Deadline",
          date: strOrNull(d.date) ?? (/^\d{4}-\d{2}-\d{2}/.test(str(d.normalized)) ? str(d.normalized) : null),
          relative: strOrNull(d.relative ?? d.text),
          fact_id: strOrNull(d.fact_id ?? d.id),
        }
      : { label: "Deadline", date: strOrNull(d), relative: null, fact_id: null },
  );
  if (isObj(o.appointment)) {
    const a = o.appointment;
    const ids = arr(a.fact_ids).map((x) => str(x));
    deadlines.push({
      label: `Appointment${strOrNull(a.time) ? ` at ${str(a.time)}` : ""}`,
      date: strOrNull(a.date),
      relative: strOrNull(a.place),
      fact_id: ids[0] ?? null,
    });
  }
  const refs: FactCard["reference_numbers"] = arr(o.reference_numbers ?? o.references).map((r) =>
    isObj(r)
      ? { label: human(r.label) ?? "Reference", value: str(r.display ?? r.value), fact_id: strOrNull(r.fact_id ?? r.id) }
      : { label: "Reference", value: str(r), fact_id: null },
  );
  for (const [key, label] of [
    ["iban", "IBAN"],
    ["ahv_number", "AHV/AVS no."],
  ] as const) {
    const x = o[key];
    if (isObj(x) && strOrNull(x.value)) refs.push({ label, value: str(x.value), fact_id: strOrNull(x.fact_id) });
  }
  return {
    authority: strOrNull(o.authority ?? o.issuer),
    letter_type: human(o.letter_type ?? o.type),
    summary: strOrNull(o.summary ?? o.subject),
    required_action: strOrNull(o.required_action ?? o.action_required ?? o.action),
    deadlines,
    amounts: arr(o.amounts).map((a) =>
      isObj(a)
        ? {
            label: human(a.label ?? a.purpose) ?? "Amount",
            value: num(a.value ?? a.amount),
            currency: str(a.currency, "CHF"),
            display: strOrNull(a.display),
            fact_id: strOrNull(a.fact_id ?? a.id),
          }
        : { label: "Amount", value: num(a), currency: "CHF", display: null, fact_id: null },
    ),
    reference_numbers: refs,
    documents_to_bring: arr(o.documents_to_bring ?? o.documents).map((d) => str(d)),
    consequences: strOrNull(o.consequences ?? o.consequence),
    contact: contact
      ? {
          name: strOrNull(contact.name ?? contact.person),
          phone: strOrNull(contact.phone),
          email: strOrNull(contact.email),
          address: strOrNull(contact.address),
          hours: strOrNull(contact.hours),
        }
      : null,
  };
}

export function normAnalyze(v: unknown, fallbackText = ""): AnalyzeResponse {
  const o = isObj(v) ? v : {};
  const card = isObj(o.fact_card) ? o.fact_card : {};
  const warnings: string[] = [];
  if (o.llm_ok === false)
    warnings.push(`Apertus extraction unavailable — showing the rules-only fact card${strOrNull(o.llm_error) ? ` (${str(o.llm_error).slice(0, 140)})` : ""}.`);
  return {
    analysis_id: str(o.analysis_id ?? o.id, ""),
    letter_lang: asLang(o.letter_lang ?? o.language),
    text: str(o.text ?? o.letter_text, fallbackText),
    title: strOrNull(o.title ?? card.subject) ?? human(card.letter_type),
    fact_card: normCard(o.fact_card),
    facts: arr(o.facts)
      .filter(isObj)
      .map((f) => {
        const spans = arr(f.spans)
          .map(spanOf)
          .filter((x): x is [number, number] => !!x);
        const span = spanOf(f.span) ?? spans[0] ?? null;
        return {
          id: str(f.id),
          type: str(f.type, "other"),
          value: str(f.value),
          normalized: strOrNull(f.normalized),
          display: strOrNull(f.display),
          span,
          spans: spans.length ? spans : span ? [span] : [],
          role: strOrNull(f.role),
          critical: Boolean(f.critical),
          source: (strOrNull(f.source) as "deterministic" | "llm" | "both" | null) ?? null,
        };
      }),
    disagreements: arr(o.disagreements)
      .filter(isObj)
      .map((d) => ({
        field: human(d.field ?? d.key ?? d.type) ?? "Field",
        deterministic: strOrNull(d.deterministic ?? d.rule_value),
        llm: strOrNull(d.llm ?? d.apertus ?? d.llm_value),
        note: strOrNull(d.note ?? d.message),
      })),
    timings: normTimings(o.timings),
    warnings,
  };
}

export function normExplain(v: unknown): ExplainResponse {
  const o = isObj(v) ? v : {};
  const pa = isObj(o.placeholder_audit) ? o.placeholder_audit : {};
  const g = isObj(o.gate) ? o.gate : { status: o.gate };
  return {
    target_lang: strOrNull(o.target_lang) ?? undefined,
    explanation: str(o.explanation),
    fact_spans: arr(o.fact_spans)
      .filter(isObj)
      .map((x) => ({ id: str(x.id), start: num(x.start) ?? -1, end: num(x.end) ?? -1 }))
      .filter((x) => x.id && x.start >= 0 && x.end > x.start),
    masked: str(o.masked ?? o.explanation),
    rtl: Boolean(o.rtl),
    back_translation: str(o.back_translation_masked ?? o.back_translation, ""),
    reference: strOrNull(o.source_plain_masked ?? o.reference ?? o.source_explanation ?? o.source_plain),
    chrf: num(o.chrf),
    placeholder_audit: {
      missing: arr(pa.missing).map((x) => str(x)),
      duplicated: arr(pa.duplicated).map((x) => str(x)),
      unexpected: arr(pa.unexpected).map((x) => str(x)),
    },
    gate: {
      status: normGate(g.status),
      reasons: arr(g.reasons).map((x) => (isObj(x) ? str(x.message) : str(x))),
      thresholds: isObj(g.thresholds) && num(g.thresholds.ready) !== null && num(g.thresholds.review) !== null ? { ready: num(g.thresholds.ready)!, review: num(g.thresholds.review)! } : null,
    },
    timings: normTimings(o.timings),
    tokens: isObj(o.tokens)
      ? (Object.fromEntries(Object.entries(o.tokens).filter(([, x]) => num(x) !== null).map(([k, x]) => [k, num(x)!])) as Record<string, number>)
      : num(o.tokens),
  };
}

export function normReply(v: unknown): ReplyResponse {
  const o = isObj(v) ? v : {};
  return {
    reply_letter: str(o.reply_letter ?? o.letter ?? o.reply),
    facts_used: arr(o.facts_used).map((x) => (isObj(x) ? str(x.id) : str(x))),
    audit: isObj(o.audit) ? o.audit : null,
  };
}

export function normAudit(v: unknown): AuditEntry[] {
  return arr(unwrap(v, "entries")).filter(isObj).map((e) => ({
    ...e,
    ts: str(e.ts ?? e.timestamp ?? e.time),
    step: str(e.step ?? e.event ?? e.action),
    hash: str(e.hash ?? e.sha256 ?? e.digest ?? (isObj(e.hashes) ? Object.values(e.hashes)[0] : "")),
  }));
}
