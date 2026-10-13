"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { BarChart3, Download, FileText, Fingerprint, Languages, Loader2, Play, Printer, RefreshCw, Search, ShieldCheck } from "lucide-react";
import type { Workspace } from "./use-workspace";
import type { AuditEntry } from "@/lib/api/types";
import { LogoMark } from "@/components/brand/logo";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator } from "@/components/ui/command";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Tip } from "@/components/ui/tooltip";
import { Kbd } from "@/components/domain/atoms";
import { cn } from "@/lib/utils";
import { langAttr } from "./facts-pane";

function StatusPill({ ws }: { ws: Workspace }) {
  const mock = ws.api?.source === "mock";
  const h = ws.health;
  const state = mock ? "mock" : h.error ? "down" : !h.data ? "loading" : h.data.backend_reachable ? "ok" : "degraded";
  const dot = { mock: "bg-warn", down: "bg-stop", loading: "bg-faint", ok: "bg-ok", degraded: "bg-warn" }[state];
  const label = {
    mock: "Mock data",
    down: "API unreachable",
    loading: "Connecting…",
    ok: h.data?.model ?? "Model ready",
    degraded: "Model offline",
  }[state];
  const detail = mock
    ? "NEXT_PUBLIC_DATA_SOURCE=mock — hand-written sample texts, no model. Set it to api to use the backend."
    : h.error
      ? `GET /api/health failed: ${h.error}`
      : h.data
        ? `API ${h.data.status} · model ${h.data.model ?? "unknown"} · LLM backend ${h.data.backend_reachable ? "reachable" : "not reachable"}`
        : "Checking /api/health…";
  return (
    <Tip label={detail}>
      <button
        onClick={() => void ws.refreshHealth()}
        className="inline-flex h-9 max-w-[220px] items-center gap-2 rounded-pill bg-white px-3 text-[13px] font-medium text-ink ring-1 ring-line transition hover:ring-ink/20"
        aria-label={`Status: ${label}. Refresh`}
      >
        <span className={cn("size-2 shrink-0 rounded-full", dot, state === "loading" && "animate-pulse")} />
        <span className="truncate">{label}</span>
      </button>
    </Tip>
  );
}

export function AuditSheet({ ws, open, onOpenChange, entries, setEntries }: { ws: Workspace; open: boolean; onOpenChange: (v: boolean) => void; entries: AuditEntry[]; setEntries: (e: AuditEntry[]) => void }) {
  const [state, setState] = React.useState<"idle" | "loading" | "error">("idle");
  const [err, setErr] = React.useState<string | null>(null);
  const load = React.useCallback(async () => {
    if (!ws.api) return;
    setState("loading");
    try {
      setEntries(await ws.api.audit());
      setState("idle");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }, [ws.api, setEntries]);
  React.useEffect(() => {
    if (open) void load();
  }, [open, load]);
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right">
        <SheetHeader>
          <SheetTitle>Audit log</SheetTitle>
          <SheetDescription>Append-only. Each step is stored as a SHA-256 hash — never the letter or the explanation.</SheetDescription>
        </SheetHeader>
        <div className="flex items-center justify-between px-6 pb-3">
          <span className="text-[12.5px] text-muted">{entries.length} entries</span>
          <button onClick={() => void load()} className="inline-flex items-center gap-1.5 rounded-pill bg-sand-2 px-3 py-1.5 text-[12.5px] font-medium text-ink hover:bg-sand">
            <RefreshCw className={cn("size-3.5", state === "loading" && "animate-spin")} /> Refresh
          </button>
        </div>
        <div className="scrollbar-thin min-h-0 flex-1 overflow-y-auto px-4 pb-6">
          {state === "error" && <p className="rounded-2xl bg-stop-soft p-3 text-[13px] text-stop">Could not load /api/audit: {err}</p>}
          {state !== "error" && entries.length === 0 && <p className="px-2 py-10 text-center text-[14px] text-muted">{state === "loading" ? "Loading…" : "No entries yet."}</p>}
          <ol className="space-y-1.5">
            {entries.map((e, i) => (
              <li key={i} className="rounded-2xl bg-white px-3.5 py-2.5 ring-1 ring-line">
                <div className="flex items-center justify-between gap-2 text-[13px]">
                  <span className="font-semibold text-ink">{e.step}</span>
                  <time className="text-[12px] text-muted">{e.ts ? new Date(e.ts).toLocaleTimeString("en-GB") : "—"}</time>
                </div>
                <p className="mt-1 truncate font-mono text-[11.5px] text-muted" title={e.hash}>
                  sha256:{e.hash}
                </p>
              </li>
            ))}
          </ol>
        </div>
      </SheetContent>
    </Sheet>
  );
}

export function CommandPalette({ ws, open, onOpenChange, onPrint, onAudit }: { ws: Workspace; open: boolean; onOpenChange: (v: boolean) => void; onPrint: (k: "client" | "caseworker") => void; onAudit: () => void }) {
  const router = useRouter();
  const run = (fn: () => void) => {
    onOpenChange(false);
    setTimeout(fn, 10);
  };
  const canClient = ws.explain.result && ws.explain.result.gate.status !== "interpreter";
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent hideClose className="max-w-lg overflow-hidden p-0">
        <DialogTitle className="sr-only">Command palette</DialogTitle>
        <Command loop>
          <CommandInput placeholder="Search samples, languages, actions…" />
          <CommandList className="max-h-[60dvh]">
            <CommandEmpty>Nothing found.</CommandEmpty>
            <CommandGroup heading="Actions">
              <CommandItem disabled={!ws.analysis || ws.explain.status === "streaming"} onSelect={() => run(() => void ws.runExplain())}>
                <Play className="size-4 text-muted" /> Explain in {ws.language?.name ?? "client language"}
              </CommandItem>
              <CommandItem disabled={!canClient} onSelect={() => run(() => onPrint("client"))}>
                <Printer className="size-4 text-muted" /> Print client copy
              </CommandItem>
              <CommandItem disabled={!ws.analysis} onSelect={() => run(() => onPrint("caseworker"))}>
                <Printer className="size-4 text-muted" /> Print caseworker copy
              </CommandItem>
              <CommandItem onSelect={() => run(onAudit)}>
                <Fingerprint className="size-4 text-muted" /> Open audit log
              </CommandItem>
              <CommandItem onSelect={() => run(() => router.push("/evidence/"))}>
                <BarChart3 className="size-4 text-muted" /> Go to evidence
              </CommandItem>
            </CommandGroup>
            <CommandSeparator />
            <CommandGroup heading="Sample letters">
              {ws.samples.map((s) => (
                <CommandItem key={s.id} value={`sample ${s.title} ${s.type} ${s.language}`} onSelect={() => run(() => void ws.analyze({ kind: "sample", id: s.id }))}>
                  <FileText className="size-4 text-muted" />
                  <span className="truncate">{s.title}</span>
                  <span className="ml-auto text-[11px] font-semibold text-brown uppercase">{s.language}</span>
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandSeparator />
            <CommandGroup heading="Client language">
              {ws.languages.map((l) => (
                <CommandItem key={l.code} value={`language ${l.name} ${l.native_name} ${l.code}`} onSelect={() => run(() => ws.setTargetLang(l.code))}>
                  <Languages className="size-4 text-muted" />
                  <span lang={langAttr(l.code)} className="font-medium">
                    {l.native_name}
                  </span>
                  <span className="text-muted">{l.name}</span>
                  {l.code === ws.targetLang && <span className="ml-auto text-[11px] font-semibold text-ok">current</span>}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </DialogContent>
    </Dialog>
  );
}

export function ExportMenu({ ws, redact, setRedact, onPrint }: { ws: Workspace; redact: boolean; setRedact: (v: boolean) => void; onPrint: (k: "client" | "caseworker") => void }) {
  const [open, setOpen] = React.useState(false);
  const gate = ws.explain.result?.gate.status;
  const clientBlocked = !ws.explain.result || gate === "interpreter";
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button className="inline-flex h-9 items-center gap-1.5 rounded-pill bg-ink px-3.5 text-[13px] font-semibold text-white shadow-pill transition hover:-translate-y-0.5" aria-label="Export">
          <Download className="size-3.5" /> <span className="hidden sm:inline">Export</span>
        </button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-[300px] p-2">
        <button
          disabled={clientBlocked}
          onClick={() => {
            setOpen(false);
            onPrint("client");
          }}
          className="flex w-full items-start gap-3 rounded-xl p-2.5 text-left hover:bg-sand-2 disabled:opacity-45 disabled:hover:bg-transparent"
        >
          <Printer className="mt-0.5 size-4 text-muted" />
          <span>
            <span className="block text-[14px] font-medium text-ink">Client copy</span>
            <span className="block text-[12.5px] text-muted">
              {!ws.explain.result ? "Explain the letter first" : gate === "interpreter" ? "Blocked by the gate — use an interpreter" : `In ${ws.languages.find((l) => l.code === ws.explain.lang)?.name ?? "the client language"}`}
            </span>
          </span>
        </button>
        <button
          disabled={!ws.analysis}
          onClick={() => {
            setOpen(false);
            onPrint("caseworker");
          }}
          className="flex w-full items-start gap-3 rounded-xl p-2.5 text-left hover:bg-sand-2 disabled:opacity-45"
        >
          <FileText className="mt-0.5 size-4 text-muted" />
          <span>
            <span className="block text-[14px] font-medium text-ink">Caseworker copy</span>
            <span className="block text-[12.5px] text-muted">Facts, gate, back-translation, draft, audit</span>
          </span>
        </button>
        <div className="mx-2.5 my-2 h-px bg-line" />
        <label className="flex cursor-pointer items-center justify-between gap-3 rounded-xl p-2.5 hover:bg-sand-2">
          <span>
            <span className="block text-[14px] font-medium text-ink">Redact names &amp; addresses</span>
            <span className="block text-[12.5px] text-muted">Applies to the letter view and exports</span>
          </span>
          <input type="checkbox" checked={redact} onChange={(e) => setRedact(e.target.checked)} className="size-4 accent-[#1A1615]" />
        </label>
      </PopoverContent>
    </Popover>
  );
}

export function TopBar({
  ws,
  onCommand,
  onAudit,
  exportMenu,
}: {
  ws: Workspace;
  onCommand: () => void;
  onAudit: () => void;
  exportMenu: React.ReactNode;
}) {
  const title = ws.analysis?.title ?? ws.analysis?.fact_card.letter_type ?? (ws.analyzing ? "Analysing…" : "No letter");
  const ref = ws.analysis?.fact_card.reference_numbers[0]?.value;
  return (
    <header className="flex h-[64px] shrink-0 items-center gap-2 px-3 sm:gap-3 sm:px-5">
      <Link href="/" className="flex shrink-0 items-center gap-2.5 rounded-pill outline-none focus-visible:ring-2 focus-visible:ring-ink/40" aria-label="Passerelle home">
        <LogoMark className="size-8" />
        <span className="hidden text-[18px] font-semibold tracking-[-0.045em] text-ink lg:inline">passerelle</span>
      </Link>
      <span className="hidden h-6 w-px bg-line-strong sm:block" />
      <div className="hidden min-w-0 items-center gap-2 sm:flex">
        {ws.analyzing && <Loader2 className="size-3.5 animate-spin text-muted" />}
        <span className="truncate text-[14px] font-semibold text-ink">{title}</span>
        {ref && <span className="hidden truncate text-[13px] text-muted md:inline">· {ref}</span>}
      </div>
      <button
        onClick={onCommand}
        className="mx-auto hidden h-9 w-[min(320px,30vw)] items-center gap-2 rounded-pill bg-white px-3.5 text-[13px] text-faint ring-1 ring-line transition hover:ring-ink/20 md:flex"
        aria-label="Open command palette"
      >
        <Search className="size-3.5" /> Search samples, languages…
        <span className="ml-auto flex gap-0.5">
          <Kbd>Ctrl</Kbd>
          <Kbd>K</Kbd>
        </span>
      </button>
      <div className="ml-auto flex items-center gap-1.5 sm:gap-2 md:ml-0">
        <button onClick={onCommand} className="grid size-9 place-items-center rounded-full bg-white text-ink ring-1 ring-line md:hidden" aria-label="Open command palette">
          <Search className="size-4" />
        </button>
        <StatusPill ws={ws} />
        <Tip label="Egress guard: only the configured model endpoint is allowed (enforced by the backend).">
          <span className="hidden h-9 items-center gap-1.5 rounded-pill bg-white px-3 text-[13px] font-medium text-ink ring-1 ring-line xl:inline-flex">
            <ShieldCheck className="size-3.5 text-ok" /> Local only
          </span>
        </Tip>
        <Tip label="Audit log">
          <button onClick={onAudit} className="grid size-9 place-items-center rounded-full bg-white text-ink ring-1 ring-line transition hover:ring-ink/20" aria-label="Open audit log">
            <Fingerprint className="size-4" />
          </button>
        </Tip>
        {exportMenu}
      </div>
    </header>
  );
}
