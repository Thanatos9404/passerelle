/**
 * Typed contract mirroring SPEC.md section 2 (FastAPI, JSON).
 * Fields marked "assumed" are not spelled out in the SPEC; the UI tolerates their absence.
 */

export type LetterLang = "de" | "fr" | "it";

export interface Health {
  status: string; // "ok" | "degraded" | ...
  model: string | null;
  backend_reachable: boolean;
}

export interface GateThresholds {
  /** chrF at or above which the gate can say "ready" */
  ready: number;
  /** chrF at or above which the gate says "review" (below = interpreter) */
  review: number;
}

export interface Language {
  code: string; // BCP-47-ish: "ti", "ar", "prs" / "fa-AF", "uk", "ta", ...
  name: string; // English name
  native_name: string;
  script: string; // "Ethiopic", "Arabic", "Cyrillic", "Tamil", "Latin"
  rtl: boolean;
  thresholds: GateThresholds | null;
  /** eval quality tier (e.g. "A" | "B" | "C"), null until evaluated */
  quality_tier: string | null;
}

export interface Sample {
  id: string;
  title: string;
  language: LetterLang;
  type: string;
}

export type FactType =
  | "date"
  | "deadline"
  | "amount"
  | "iban"
  | "ahv"
  | "reference"
  | "phone"
  | "time"
  | "address"
  | "email"
  | "name"
  | (string & {});

export interface Fact {
  /** Placeholder id, e.g. "D1" -> rendered in masked text as ⟦D1⟧ */
  id: string;
  type: FactType;
  value: string;
  normalized: string | null;
  /** [start, end) character offsets into the letter text */
  span: [number, number] | null;
  /** assumed: which extractor found it */
  source?: "deterministic" | "llm" | "both" | null;
  /** backend: locale-safe rendering used when re-inserting the fact */
  display?: string | null;
  /** backend: every occurrence in the letter */
  spans?: [number, number][];
  role?: string | null;
  critical?: boolean;
}

export interface Deadline {
  label: string;
  /** ISO date (yyyy-mm-dd) when resolvable */
  date: string | null;
  /** original wording, e.g. "innert 10 Tagen" */
  relative?: string | null;
  fact_id?: string | null;
}

export interface Amount {
  label: string;
  value: number | null;
  currency: string;
  display?: string | null;
  fact_id?: string | null;
}

export interface FactCard {
  authority: string | null;
  letter_type: string | null;
  summary?: string | null;
  required_action: string | null;
  deadlines: Deadline[];
  amounts: Amount[];
  reference_numbers: { label: string; value: string; fact_id?: string | null }[];
  documents_to_bring: string[];
  consequences: string | null;
  contact: {
    name?: string | null;
    phone?: string | null;
    email?: string | null;
    address?: string | null;
    hours?: string | null;
  } | null;
}

export interface Disagreement {
  field: string;
  deterministic: string | null;
  llm: string | null;
  note?: string | null;
}

export interface AnalyzeRequest {
  text?: string;
  sample_id?: string;
  source_lang?: LetterLang;
}

export interface AnalyzeResponse {
  /** assumed: required so /explain and /reply can reference the analysis */
  analysis_id: string;
  letter_lang: LetterLang;
  /** assumed: the letter text the spans refer to (needed when analysing by sample_id) */
  text: string;
  title?: string | null;
  fact_card: FactCard;
  facts: Fact[];
  disagreements: Disagreement[];
  timings: Record<string, number>;
  /** non-fatal issues, e.g. Apertus unreachable -> rules-only card */
  warnings?: string[];
}

export type GateStatus = "ready" | "review" | "interpreter";

export interface PlaceholderAudit {
  missing: string[];
  duplicated: string[];
  unexpected: string[];
}

export interface ExplainRequest {
  analysis_id?: string;
  text?: string;
  target_lang: string;
}

export interface ExplainResponse {
  target_lang?: string;
  explanation: string; // unmasked, in the client's language
  /** backend: where each locked fact sits in `explanation` */
  fact_spans?: { id: string; start: number; end: number }[];
  masked: string; // with ⟦X1⟧ placeholders
  rtl: boolean;
  back_translation: string; // into the letter language
  /** assumed: the source-language plain explanation chrF is computed against */
  reference?: string | null;
  chrf: number | null;
  placeholder_audit: PlaceholderAudit;
  gate: { status: GateStatus; reasons: string[]; thresholds?: GateThresholds | null };
  timings: Record<string, number>;
  tokens: Record<string, number> | number | null;
}

/** Streaming events (SSE) — assumed shape, see lib/api/sse.ts */
export type ExplainStreamEvent =
  | { type: "stage"; stage: string }
  | { type: "token"; text: string }
  | { type: "done"; result: ExplainResponse }
  | { type: "error"; message: string };

export interface ReplyRequest {
  analysis_id: string;
  client_message: string;
  client_lang: string;
}

export interface ReplyResponse {
  reply_letter: string;
  facts_used: string[];
  audit: Record<string, unknown> | null;
}

export interface AuditEntry {
  ts: string;
  step: string;
  /** sha256 of inputs/outputs — never content */
  hash: string;
  [k: string]: unknown;
}

export interface IngestResponse {
  text: string;
  pages?: number;
}

/* ---------- Evaluation summary (data/eval_runs/summary.json) ---------- */

export interface PR {
  precision: number | null;
  recall: number | null;
  f1?: number | null;
}

export interface EvalSummary {
  generated_at?: string | null;
  model?: string | null;
  hardware?: string | null;
  split?: string | null;
  n_letters?: number | null;
  extraction?: {
    by_type: { type: string; deterministic?: PR | null; apertus?: PR | null; merged?: PR | null }[];
  } | null;
  fact_preservation?: {
    overall?: { naive?: number | null; factlock?: number | null } | null;
    by_lang: {
      lang: string;
      naive?: number | null;
      factlock?: number | null;
      hallucinated_naive?: number | null;
      hallucinated_factlock?: number | null;
    }[];
  } | null;
  chrf?: {
    by_lang: { lang: string; chrf?: number | null; ready?: number | null; review?: number | null }[];
  } | null;
  gate?: {
    /** rows: gate decision; columns: whether the output actually had a problem */
    confusion?: { gate: GateStatus; ok: number; bad: number }[] | null;
    precision?: number | null;
    recall?: number | null;
  } | null;
  cost?: {
    seconds_per_letter?: number | null;
    tokens_per_letter?: number | null;
    energy_wh_per_letter?: number | null;
    chf_per_letter?: number | null;
    interpreter_chf_range?: [number, number] | null;
    interpreter_note?: string | null;
  } | null;
  notes?: string[] | null;
}
