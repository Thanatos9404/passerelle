import { resolveDataSource, type DataSource } from "@/lib/config";
import type {
  AnalyzeRequest,
  AnalyzeResponse,
  AuditEntry,
  EvalSummary,
  ExplainRequest,
  ExplainResponse,
  ExplainStreamEvent,
  Health,
  IngestResponse,
  Language,
  ReplyRequest,
  ReplyResponse,
  Sample,
} from "./types";

export interface PasserelleApi {
  source: DataSource;
  health(): Promise<Health>;
  languages(): Promise<Language[]>;
  samples(): Promise<Sample[]>;
  analyze(req: AnalyzeRequest, signal?: AbortSignal): Promise<AnalyzeResponse>;
  explainStream(req: ExplainRequest, onEvent: (e: ExplainStreamEvent) => void, signal?: AbortSignal): Promise<ExplainResponse>;
  reply(req: ReplyRequest, signal?: AbortSignal): Promise<ReplyResponse>;
  audit(): Promise<AuditEntry[]>;
  ingest(file: File): Promise<IngestResponse>;
  evalSummary(): Promise<EvalSummary | null>;
}

let cached: Promise<PasserelleApi> | null = null;

/** Lazily loads the selected implementation so the mock corpus is a separate chunk. */
export function getApi(): Promise<PasserelleApi> {
  if (!cached) {
    cached = resolveDataSource() === "mock" ? import("./mock").then((m) => m.mockApi) : import("./http").then((m) => m.httpApi);
  }
  return cached;
}

export * from "./types";
