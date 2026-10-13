import { API_BASE } from "@/lib/config";
import type { AnalyzeRequest, EvalSummary, ExplainRequest, ExplainResponse, ExplainStreamEvent, ReplyRequest } from "./types";
import { normAnalyze, normAudit, normExplain, normHealth, normLanguages, normReply, normSamples } from "./normalize";
import { readSse } from "./sse";
import type { PasserelleApi } from "./index";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: unknown,
  ) {
    super(message);
  }
}

async function request<T = unknown>(path: string, init?: RequestInit & { timeoutMs?: number }): Promise<T> {
  const ctrl = new AbortController();
  const timeout = setTimeout(() => ctrl.abort(), init?.timeoutMs ?? 180_000);
  init?.signal?.addEventListener("abort", () => ctrl.abort());
  try {
    const res = await fetch(`${API_BASE}${path}`, { ...init, signal: ctrl.signal });
    if (!res.ok) {
      let detail: unknown = null;
      try {
        detail = await res.json();
      } catch {
        /* not JSON */
      }
      const msg =
        detail && typeof detail === "object" && "detail" in detail
          ? String((detail as { detail: unknown }).detail)
          : `${res.status} ${res.statusText}`;
      throw new ApiError(msg, res.status, detail);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timeout);
  }
}

const post = (body: unknown, signal?: AbortSignal): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
  signal,
});

/** The static export may ship data/eval_runs/summary.json as /eval/summary.json (scripts/sync-eval.mjs). */
export async function staticEvalSummary(): Promise<EvalSummary | null> {
  try {
    const res = await fetch("/eval/summary.json", { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as EvalSummary;
  } catch {
    return null;
  }
}

export const httpApi: PasserelleApi = {
  source: "api",
  async health() {
    return normHealth(await request("/api/health", { timeoutMs: 8000 }));
  },
  async languages() {
    return normLanguages(await request("/api/languages"));
  },
  async samples() {
    return normSamples(await request("/api/samples"));
  },
  async analyze(req: AnalyzeRequest, signal?: AbortSignal) {
    return normAnalyze(await request("/api/analyze", post(req, signal)), req.text ?? "");
  },
  async explainStream(req: ExplainRequest, onEvent: (e: ExplainStreamEvent) => void, signal?: AbortSignal) {
    const res = await fetch(`${API_BASE}/api/explain/stream`, {
      ...post(req, signal),
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    });
    // No streaming endpoint: fall back to the blocking one.
    if (res.status === 404 || res.status === 405) {
      onEvent({ type: "stage", stage: "translate" });
      const result = normExplain(await request("/api/explain", post(req, signal)));
      onEvent({ type: "token", text: result.masked });
      onEvent({ type: "done", result });
      return result;
    }
    if (!res.ok) throw new ApiError(`${res.status} ${res.statusText}`, res.status);
    let final: ExplainResponse | null = null;
    let streamError: string | null = null;
    await readSse(
      res,
      ({ event, data }) => {
        let payload: Record<string, unknown>;
        try {
          payload = JSON.parse(data) as Record<string, unknown>;
        } catch {
          payload = { text: data };
        }
        const kind = event !== "message" ? event : String(payload.type ?? "token");
        if (kind === "token" || kind === "delta") onEvent({ type: "token", text: String(payload.text ?? payload.delta ?? "") });
        else if (kind === "stage") onEvent({ type: "stage", stage: String(payload.stage ?? "") });
        else if (kind === "done" || kind === "result") {
          final = normExplain(payload.result ?? payload);
          onEvent({ type: "done", result: final });
        } else if (kind === "error") {
          streamError = String(payload.message ?? payload.detail ?? "Stream error");
          onEvent({ type: "error", message: streamError });
        }
      },
      signal,
    );
    if (streamError) throw new ApiError(streamError, 500);
    if (!final) throw new ApiError("The stream ended without a result", 502);
    return final;
  },
  async reply(req: ReplyRequest, signal?: AbortSignal) {
    return normReply(await request("/api/reply", post(req, signal)));
  },
  async audit() {
    return normAudit(await request("/api/audit"));
  },
  async ingest(file: File) {
    const fd = new FormData();
    fd.append("file", file);
    const r = await request<{ text?: string; pages?: number }>("/api/ingest", { method: "POST", body: fd });
    return { text: String(r.text ?? ""), pages: r.pages };
  },
  async evalSummary() {
    // The build bakes data/eval_runs/summary.json into /eval/summary.json; only when that is the
    // "pending" placeholder do we ask the live API (which 404s until the eval has run).
    const baked = await staticEvalSummary();
    if (baked && (baked as { status?: string }).status !== "pending") return baked;
    try {
      return await request<EvalSummary>("/api/eval/summary", { timeoutMs: 8000 });
    } catch {
      return baked;
    }
  },
};
