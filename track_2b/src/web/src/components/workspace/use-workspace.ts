"use client";

import * as React from "react";
import { getApi, type PasserelleApi } from "@/lib/api";
import type { AnalyzeResponse, ExplainResponse, Health, Language, ReplyResponse, Sample } from "@/lib/api/types";

export type Source = { kind: "sample"; id: string } | { kind: "text"; text: string; name?: string };
export type Stage = "explain" | "backtranslate" | "verify" | string;

export interface ExplainState {
  status: "idle" | "streaming" | "done" | "error";
  stage: Stage | null;
  masked: string;
  lang: string | null;
  result: ExplainResponse | null;
  error: string | null;
  startedAt: number | null;
}

export interface ReplyState {
  status: "idle" | "loading" | "done" | "error";
  result: ReplyResponse | null;
  error: string | null;
}

const IDLE_EXPLAIN: ExplainState = { status: "idle", stage: null, masked: "", lang: null, result: null, error: null, startedAt: null };
const IDLE_REPLY: ReplyState = { status: "idle", result: null, error: null };

function errMsg(e: unknown): string {
  if (e instanceof DOMException && e.name === "AbortError") return "Cancelled.";
  if (e instanceof Error) return e.message;
  return String(e);
}

export function useWorkspace() {
  const [api, setApi] = React.useState<PasserelleApi | null>(null);
  const [boot, setBoot] = React.useState<{ status: "loading" | "ready" | "error"; error?: string }>({ status: "loading" });
  const [health, setHealth] = React.useState<{ data: Health | null; error: string | null }>({ data: null, error: null });
  const [languages, setLanguages] = React.useState<Language[]>([]);
  const [samples, setSamples] = React.useState<Sample[]>([]);
  const [source, setSource] = React.useState<Source | null>(null);
  const [analysis, setAnalysis] = React.useState<AnalyzeResponse | null>(null);
  const [analyzing, setAnalyzing] = React.useState(false);
  const [analyzeError, setAnalyzeError] = React.useState<string | null>(null);
  const [targetLang, setTargetLangState] = React.useState<string>("ti");
  const [explain, setExplain] = React.useState<ExplainState>(IDLE_EXPLAIN);
  const [reply, setReply] = React.useState<ReplyState>(IDLE_REPLY);
  const [clientMessage, setClientMessage] = React.useState("");
  const analyzeCtl = React.useRef<AbortController | null>(null);
  const explainCtl = React.useRef<AbortController | null>(null);
  const replyCtl = React.useRef<AbortController | null>(null);

  const language = React.useMemo(() => languages.find((l) => l.code === targetLang) ?? null, [languages, targetLang]);

  const syncUrl = React.useCallback((patch: Record<string, string | null>) => {
    const u = new URL(window.location.href);
    for (const [k, v] of Object.entries(patch)) {
      if (v) u.searchParams.set(k, v);
      else u.searchParams.delete(k);
    }
    window.history.replaceState(null, "", u.toString());
  }, []);

  const resetDownstream = React.useCallback(() => {
    explainCtl.current?.abort();
    replyCtl.current?.abort();
    setExplain(IDLE_EXPLAIN);
    setReply(IDLE_REPLY);
    setClientMessage("");
  }, []);

  const analyze = React.useCallback(
    async (src: Source, a: PasserelleApi | null = api) => {
      if (!a) return;
      analyzeCtl.current?.abort();
      const ctl = new AbortController();
      analyzeCtl.current = ctl;
      setSource(src);
      setAnalyzing(true);
      setAnalyzeError(null);
      resetDownstream();
      syncUrl({ sample: src.kind === "sample" ? src.id : null });
      try {
        const res = await a.analyze(src.kind === "sample" ? { sample_id: src.id } : { text: src.text }, ctl.signal);
        if (ctl.signal.aborted) return;
        setAnalysis(res);
      } catch (e) {
        if (ctl.signal.aborted) return;
        setAnalysis(null);
        setAnalyzeError(errMsg(e));
      } finally {
        if (!ctl.signal.aborted) setAnalyzing(false);
      }
    },
    [api, resetDownstream, syncUrl],
  );

  const setTargetLang = React.useCallback(
    (code: string) => {
      setTargetLangState(code);
      syncUrl({ lang: code });
      // a new language invalidates the explanation and the reply
      explainCtl.current?.abort();
      setExplain((s) => (s.lang === code ? s : IDLE_EXPLAIN));
      setReply(IDLE_REPLY);
    },
    [syncUrl],
  );

  const runExplain = React.useCallback(async () => {
    if (!api || !analysis) return;
    explainCtl.current?.abort();
    const ctl = new AbortController();
    explainCtl.current = ctl;
    const lang = targetLang;
    setReply(IDLE_REPLY);
    setExplain({ ...IDLE_EXPLAIN, status: "streaming", stage: "source_plain", lang, startedAt: Date.now() });
    try {
      const result = await api.explainStream(
        { analysis_id: analysis.analysis_id, target_lang: lang },
        (ev) => {
          if (ctl.signal.aborted) return;
          if (ev.type === "token") setExplain((s) => ({ ...s, masked: s.masked + ev.text }));
          else if (ev.type === "stage") setExplain((s) => ({ ...s, stage: ev.stage }));
        },
        ctl.signal,
      );
      if (ctl.signal.aborted) return;
      setExplain((s) => ({ ...s, status: "done", stage: null, masked: result.masked || s.masked, result }));
    } catch (e) {
      if (ctl.signal.aborted) return;
      setExplain((s) => ({ ...s, status: "error", stage: null, error: errMsg(e) }));
    }
  }, [api, analysis, targetLang]);

  const cancelExplain = React.useCallback(() => {
    explainCtl.current?.abort();
    setExplain(IDLE_EXPLAIN);
  }, []);

  const runReply = React.useCallback(async () => {
    if (!api || !analysis) return;
    replyCtl.current?.abort();
    const ctl = new AbortController();
    replyCtl.current = ctl;
    setReply({ status: "loading", result: null, error: null });
    try {
      const result = await api.reply({ analysis_id: analysis.analysis_id, client_message: clientMessage, client_lang: targetLang }, ctl.signal);
      if (!ctl.signal.aborted) setReply({ status: "done", result, error: null });
    } catch (e) {
      if (!ctl.signal.aborted) setReply({ status: "error", result: null, error: errMsg(e) });
    }
  }, [api, analysis, clientMessage, targetLang]);

  const refreshHealth = React.useCallback(async (a: PasserelleApi | null = api) => {
    if (!a) return;
    try {
      setHealth({ data: await a.health(), error: null });
    } catch (e) {
      setHealth({ data: null, error: errMsg(e) });
    }
  }, [api]);

  // boot: load API implementation, languages, samples; then analyse the requested or first sample
  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const a = await getApi();
        if (!alive) return;
        setApi(a);
        void refreshHealth(a);
        const [langs, smp] = await Promise.all([a.languages(), a.samples()]);
        if (!alive) return;
        setLanguages(langs);
        setSamples(smp);
        const params = new URLSearchParams(window.location.search);
        const wantLang = params.get("lang");
        if (wantLang && langs.some((l) => l.code === wantLang)) setTargetLangState(wantLang);
        else if (langs.length && !langs.some((l) => l.code === "ti")) setTargetLangState(langs[0].code);
        setBoot({ status: "ready" });
        const wantSample = params.get("sample");
        const first = smp.find((s) => s.id === wantSample) ?? smp[0];
        if (first) void analyze({ kind: "sample", id: first.id }, a);
      } catch (e) {
        if (alive) setBoot({ status: "error", error: errMsg(e) });
      }
    })();
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // health poll
  React.useEffect(() => {
    if (!api) return;
    const t = setInterval(() => void refreshHealth(api), 30_000);
    return () => clearInterval(t);
  }, [api, refreshHealth]);

  return {
    api,
    boot,
    health,
    languages,
    samples,
    source,
    analysis,
    analyzing,
    analyzeError,
    analyze,
    targetLang,
    language,
    setTargetLang,
    explain,
    runExplain,
    cancelExplain,
    reply,
    runReply,
    clientMessage,
    setClientMessage,
    refreshHealth,
  };
}

export type Workspace = ReturnType<typeof useWorkspace>;
