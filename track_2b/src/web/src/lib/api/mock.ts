/**
 * In-browser mock of the Passerelle API (NEXT_PUBLIC_DATA_SOURCE=mock).
 * Realistic latency, SSE-like token streaming and the same gate logic the backend describes,
 * computed on the hand-written mock corpus. Every number here derives from mock texts —
 * none of it is an evaluation result.
 */
import type { PasserelleApi } from "./index";
import type {
  AnalyzeRequest,
  AnalyzeResponse,
  AuditEntry,
  ExplainRequest,
  ExplainResponse,
  ExplainStreamEvent,
  Fact,
  GateStatus,
  Language,
  ReplyRequest,
} from "./types";
import { MOCK_LETTERS, buildFacts, type MockLetter } from "@/lib/mock/letters";
import { MOCK_EXPLANATIONS, MOCK_REPLIES } from "@/lib/mock/explanations";
import { PLACEHOLDER_RE, placeholdersIn, renderFactValue } from "@/lib/facts";
import { sleep } from "@/lib/utils";

export const MOCK_LANGUAGES: Language[] = [
  { code: "ti", name: "Tigrinya", native_name: "ትግርኛ", script: "Ethiopic", rtl: false, thresholds: { ready: 85, review: 75 }, quality_tier: null },
  { code: "ar", name: "Arabic", native_name: "العربية", script: "Arabic", rtl: true, thresholds: { ready: 85, review: 72 }, quality_tier: null },
  { code: "prs", name: "Dari", native_name: "دری", script: "Arabic", rtl: true, thresholds: { ready: 85, review: 72 }, quality_tier: null },
  { code: "uk", name: "Ukrainian", native_name: "Українська", script: "Cyrillic", rtl: false, thresholds: { ready: 85, review: 72 }, quality_tier: null },
  { code: "ta", name: "Tamil", native_name: "தமிழ்", script: "Tamil", rtl: false, thresholds: { ready: 85, review: 72 }, quality_tier: null },
  { code: "tr", name: "Turkish", native_name: "Türkçe", script: "Latin", rtl: false, thresholds: { ready: 85, review: 72 }, quality_tier: null },
  { code: "so", name: "Somali", native_name: "Soomaali", script: "Latin", rtl: false, thresholds: { ready: 85, review: 75 }, quality_tier: null },
  { code: "sq", name: "Albanian", native_name: "Shqip", script: "Latin", rtl: false, thresholds: { ready: 85, review: 72 }, quality_tier: null },
  { code: "ku", name: "Kurdish (Kurmanji)", native_name: "Kurdî", script: "Latin", rtl: false, thresholds: { ready: 85, review: 75 }, quality_tier: null },
  { code: "pt", name: "Portuguese", native_name: "Português", script: "Latin", rtl: false, thresholds: { ready: 85, review: 72 }, quality_tier: null },
  { code: "es", name: "Spanish", native_name: "Español", script: "Latin", rtl: false, thresholds: { ready: 85, review: 72 }, quality_tier: null },
  { code: "en", name: "English", native_name: "English", script: "Latin", rtl: false, thresholds: { ready: 85, review: 72 }, quality_tier: null },
];

/** chrF (character n-gram F-score, n=1..6, beta=2, whitespace removed) — same definition as sacreBLEU's default. */
export function chrF(hyp: string, ref: string, order = 6, beta = 2): number {
  const h = hyp.replace(/\s+/g, "");
  const r = ref.replace(/\s+/g, "");
  let pSum = 0;
  let rSum = 0;
  let n = 0;
  for (let k = 1; k <= order; k++) {
    const grams = (s: string) => {
      const m = new Map<string, number>();
      for (let i = 0; i + k <= s.length; i++) {
        const g = s.slice(i, i + k);
        m.set(g, (m.get(g) ?? 0) + 1);
      }
      return m;
    };
    const hg = grams(h);
    const rg = grams(r);
    let match = 0;
    let ht = 0;
    let rt = 0;
    hg.forEach((c, g) => {
      ht += c;
      match += Math.min(c, rg.get(g) ?? 0);
    });
    rg.forEach((c) => (rt += c));
    if (ht === 0 || rt === 0) continue;
    pSum += match / ht;
    rSum += match / rt;
    n++;
  }
  if (n === 0) return 0;
  const P = pSum / n;
  const R = rSum / n;
  if (P + R === 0) return 0;
  const b2 = beta * beta;
  return (100 * ((1 + b2) * P * R)) / (b2 * P + R);
}

interface Analysis {
  id: string;
  letter: MockLetter | null;
  text: string;
  facts: Fact[];
}
const analyses = new Map<string, Analysis>();
const audit: AuditEntry[] = [];

async function sha256(s: string): Promise<string> {
  try {
    const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
    return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  } catch {
    // insecure context fallback (FNV-1a, not cryptographic; mock only)
    let h = 0x811c9dc5;
    for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
    return (h >>> 0).toString(16).padStart(8, "0").repeat(8);
  }
}

async function log(step: string, payload: string) {
  audit.unshift({ ts: new Date().toISOString(), step, hash: await sha256(payload), source: "mock" });
  if (audit.length > 50) audit.pop();
}

function jitter(base: number) {
  return base * (0.8 + Math.random() * 0.4);
}

/** Tiny deterministic extractor for pasted text in mock mode (Swiss formats only). */
function extractPasted(text: string): Fact[] {
  const rules: { type: Fact["type"]; prefix: string; re: RegExp; norm?: (m: RegExpExecArray) => string | null }[] = [
    { type: "date", prefix: "D", re: /\b(\d{1,2})\.(\d{1,2})\.(20\d{2})\b/g, norm: (m) => `${m[3]}-${m[2].padStart(2, "0")}-${m[1].padStart(2, "0")}` },
    { type: "amount", prefix: "A", re: /\b(?:CHF|Fr\.)\s?\d{1,3}(?:['’ ]\d{3})*(?:[.,]\d{2}|\.–)?/g, norm: (m) => {
      const n = m[0].replace(/^(CHF|Fr\.)\s?/, "").replace(/['’ ]/g, "").replace(".–", ".00").replace(",", ".");
      return Number.isFinite(Number(n)) ? `${Number(n).toFixed(2)} CHF` : null;
    } },
    { type: "iban", prefix: "I", re: /\bCH\d{2}(?: ?[0-9A-Z]{4}){4} ?[0-9A-Z]{1}\b/g },
    { type: "ahv", prefix: "V", re: /\b756\.\d{4}\.\d{4}\.\d{2}\b/g },
    { type: "phone", prefix: "P", re: /\b0\d{2} \d{3} \d{2} \d{2}\b/g },
    { type: "time", prefix: "T", re: /\b\d{1,2}[:h]\d{2}\b/g },
  ];
  const facts: Fact[] = [];
  const taken: [number, number][] = [];
  for (const r of rules) {
    let i = 0;
    for (const m of text.matchAll(r.re)) {
      const s = m.index ?? 0;
      const e = s + m[0].length;
      if (taken.some(([a, b]) => s < b && e > a)) continue;
      taken.push([s, e]);
      facts.push({ id: `${r.prefix}${++i}`, type: r.type, value: m[0], normalized: r.norm ? r.norm(m as RegExpExecArray) : null, span: [s, e], source: "deterministic" });
    }
  }
  return facts.sort((a, b) => (a.span?.[0] ?? 0) - (b.span?.[0] ?? 0));
}

function detectLang(text: string): "de" | "fr" | "it" {
  const t = text.toLowerCase();
  const score = (ws: string[]) => ws.reduce((s, w) => s + (t.split(w).length - 1), 0);
  const de = score([" und ", " der ", " die ", " sie ", " nicht ", "freundliche"]);
  const fr = score([" et ", " le ", " la ", " vous ", " pas ", "veuillez"]);
  const it = score([" e ", " il ", " la ", " di ", " non ", "distinti"]);
  return fr > de && fr >= it ? "fr" : it > de && it > fr ? "it" : "de";
}

function gateFor(lang: Language | undefined, chrf: number, audit: ExplainResponse["placeholder_audit"]): { status: GateStatus; reasons: string[] } {
  const t = lang?.thresholds ?? { ready: 85, review: 72 };
  const reasons: string[] = [];
  let status: GateStatus = "ready";
  const bump = (s: GateStatus) => {
    const rank = { ready: 0, review: 1, interpreter: 2 } as const;
    if (rank[s] > rank[status]) status = s;
  };
  if (audit.unexpected.length) {
    bump("interpreter");
    reasons.push(`Unexpected placeholder(s) ${audit.unexpected.map((x) => `⟦${x}⟧`).join(", ")} appeared in the output.`);
  }
  if (audit.duplicated.length) {
    bump("review");
    reasons.push(`Placeholder(s) ${audit.duplicated.map((x) => `⟦${x}⟧`).join(", ")} appear more than once.`);
  }
  const critical = audit.missing.filter((x) => /^[DAI]/.test(x));
  if (critical.length) {
    bump("interpreter");
    reasons.push(`Critical fact(s) ${critical.map((x) => `⟦${x}⟧`).join(", ")} are missing from the explanation.`);
  } else if (audit.missing.length) {
    bump("review");
    reasons.push(`Fact(s) ${audit.missing.map((x) => `⟦${x}⟧`).join(", ")} are missing from the explanation — tell the client in person.`);
  }
  if (chrf < t.review) {
    bump("interpreter");
    reasons.push(`Back-translation chrF ${chrf.toFixed(1)} is below the interpreter threshold (${t.review}) for ${lang?.name ?? "this language"}.`);
  } else if (chrf < t.ready) {
    bump("review");
    reasons.push(`Back-translation chrF ${chrf.toFixed(1)} is below the ready threshold (${t.ready}) for ${lang?.name ?? "this language"}.`);
  }
  if (status === "ready") reasons.push(`All locked facts present exactly once; chrF ${chrf.toFixed(1)} ≥ ${t.ready}.`);
  return { status, reasons };
}

function todayIn(lang: "de" | "fr" | "it") {
  const loc = { de: "de-CH", fr: "fr-CH", it: "it-CH" }[lang];
  return new Date().toLocaleDateString(loc, { day: "numeric", month: "long", year: "numeric" });
}

export const mockApi: PasserelleApi = {
  source: "mock",
  async health() {
    await sleep(150);
    return { status: "ok", model: "mock (no model loaded)", backend_reachable: false };
  },
  async languages() {
    await sleep(120);
    return MOCK_LANGUAGES;
  },
  async samples() {
    await sleep(120);
    return MOCK_LETTERS.map((l) => ({ id: l.id, title: l.title, language: l.language, type: l.type }));
  },
  async analyze(req: AnalyzeRequest, signal?: AbortSignal): Promise<AnalyzeResponse> {
    const letter = req.sample_id ? MOCK_LETTERS.find((l) => l.id === req.sample_id) ?? null : null;
    const det = jitter(0.05);
    const llm = jitter(5.8);
    await sleep(letter ? 900 : 700, signal);
    const id = `mock-${(letter?.id ?? "pasted").slice(0, 12)}-${Math.random().toString(36).slice(2, 8)}`;
    if (letter) {
      const facts = buildFacts(letter);
      analyses.set(id, { id, letter, text: letter.text, facts });
      await log("analyze", letter.text);
      return {
        analysis_id: id,
        letter_lang: letter.language,
        text: letter.text,
        title: letter.title,
        fact_card: letter.card,
        facts,
        disagreements: letter.disagreements,
        timings: { extract_deterministic: det, extract_llm: llm, total: det + llm },
      };
    }
    const text = (req.text ?? "").trim();
    if (!text) throw new Error("No letter text was provided.");
    const facts = extractPasted(text);
    const lang = req.source_lang ?? detectLang(text);
    analyses.set(id, { id, letter: null, text, facts });
    await log("analyze", text);
    const firstLine = text.split(/\n/).find((l) => l.trim()) ?? null;
    return {
      analysis_id: id,
      letter_lang: lang,
      text,
      title: "Pasted letter",
      fact_card: {
        authority: firstLine,
        letter_type: null,
        summary: "Mock mode: only deterministic Swiss-format extractors ran on pasted text. Connect the backend for the Apertus fact card.",
        required_action: null,
        deadlines: facts.filter((f) => f.type === "date").slice(-2).map((f) => ({ label: "Date found in letter", date: f.normalized, relative: f.value, fact_id: f.id })),
        amounts: facts.filter((f) => f.type === "amount").map((f) => ({ label: "Amount found in letter", value: f.normalized ? Number.parseFloat(f.normalized) : null, currency: "CHF", fact_id: f.id })),
        reference_numbers: [],
        documents_to_bring: [],
        consequences: null,
        contact: null,
      },
      facts,
      disagreements: [],
      timings: { extract_deterministic: det, total: det },
    };
  },
  async explainStream(req: ExplainRequest, onEvent: (e: ExplainStreamEvent) => void, signal?: AbortSignal): Promise<ExplainResponse> {
    const a = req.analysis_id ? analyses.get(req.analysis_id) : undefined;
    if (!a) throw new Error("Unknown analysis — analyse the letter first.");
    const lang = MOCK_LANGUAGES.find((l) => l.code === req.target_lang);
    const corpus = a.letter ? MOCK_EXPLANATIONS[a.letter.id]?.[req.target_lang] : undefined;
    onEvent({ type: "stage", stage: "source_plain" });
    await sleep(500, signal);
    onEvent({ type: "stage", stage: "translate" });
    if (!a.letter || !corpus) {
      throw new Error(
        `The mock corpus has no ${lang?.name ?? req.target_lang} explanation for this letter. Switch NEXT_PUBLIC_DATA_SOURCE to "api" to generate one with Apertus.`,
      );
    }
    // stream masked tokens; placeholders arrive whole
    const tokens = corpus.masked.match(/⟦[A-Z]{1,3}\d{1,3}⟧|\s+|[^\s⟦]+/g) ?? [corpus.masked];
    let i = 0;
    const t0 = performance.now();
    while (i < tokens.length) {
      const n = 1 + Math.floor(Math.random() * 3);
      onEvent({ type: "token", text: tokens.slice(i, i + n).join("") });
      i += n;
      await sleep(18 + Math.random() * 30, signal);
    }
    const tExplain = (performance.now() - t0) / 1000;
    onEvent({ type: "stage", stage: "back_translate" });
    await sleep(700, signal);
    let back = a.letter.reference;
    for (const [from, to] of corpus.drift) back = back.replace(from, to);
    onEvent({ type: "stage", stage: "verify" });
    await sleep(350, signal);

    const expected = placeholdersIn(a.letter.reference);
    const got = placeholdersIn(corpus.masked);
    const count = (id: string) => got.filter((x) => x === id).length;
    const placeholder_audit = {
      missing: [...new Set(expected.filter((id) => count(id) === 0))],
      duplicated: [...new Set(got.filter((id) => count(id) > 1 && expected.filter((x) => x === id).length < count(id)))],
      unexpected: [...new Set(got.filter((id) => !expected.includes(id)))],
    };
    const score = chrF(back, a.letter.reference);
    const byId = new Map(a.facts.map((f) => [f.id, f]));
    const explanation = corpus.masked.replace(PLACEHOLDER_RE, (m, id: string) => {
      const f = byId.get(id);
      return f ? renderFactValue(f) : m;
    });
    const result: ExplainResponse = {
      target_lang: req.target_lang,
      explanation,
      masked: corpus.masked,
      rtl: Boolean(lang?.rtl),
      back_translation: back,
      reference: a.letter.reference,
      chrf: Math.round(score * 10) / 10,
      placeholder_audit,
      gate: gateFor(lang, score, placeholder_audit),
      timings: { translate: tExplain + jitter(6), back_translate: jitter(4.2), verify: jitter(0.08) },
      tokens: { prompt: Math.round(jitter(1450)), completion: Math.round(corpus.masked.length / 2.6) },
    };
    await log(`explain:${req.target_lang}`, result.masked);
    onEvent({ type: "done", result });
    return result;
  },
  async reply(req: ReplyRequest, signal?: AbortSignal) {
    const a = analyses.get(req.analysis_id);
    if (!a) throw new Error("Unknown analysis — analyse the letter first.");
    if (!req.client_message.trim()) throw new Error("Write the client's message first.");
    await sleep(1400, signal);
    if (!a.letter) throw new Error("The mock corpus only drafts replies for the sample letters. Connect the backend for pasted letters.");
    const masked = MOCK_REPLIES[a.letter.id].replace("{TODAY}", todayIn(a.letter.language));
    const raw = new Map(a.letter.facts.map((f) => [f.id, f.value]));
    const used = placeholdersIn(masked);
    const reply_letter = masked.replace(PLACEHOLDER_RE, (m, id: string) => raw.get(id) ?? m);
    await log("reply", reply_letter);
    return { reply_letter, facts_used: [...new Set(used)], audit: { hash: (await sha256(reply_letter)).slice(0, 16) } };
  },
  async audit() {
    await sleep(150);
    return [...audit];
  },
  async ingest(file: File) {
    await sleep(500);
    if (/\.txt$/i.test(file.name) || file.type.startsWith("text/")) return { text: await file.text(), pages: 1 };
    throw new Error("PDF text extraction runs on the server (pypdf). In mock mode, paste the text or pick a sample.");
  },
  async evalSummary() {
    // Never fabricate evaluation numbers: use the static file if the eval pipeline produced one.
    try {
      const res = await fetch("/eval/summary.json", { cache: "no-store" });
      return res.ok ? await res.json() : null;
    } catch {
      return null;
    }
  },
};
