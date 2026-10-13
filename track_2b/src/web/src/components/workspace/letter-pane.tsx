"use client";

import * as React from "react";
import { AlertTriangle, ChevronDown, ClipboardPaste, FileText, FileUp, Library, Loader2, RotateCcw } from "lucide-react";
import type { Workspace } from "./use-workspace";
import { FactLegend, LetterText } from "@/components/domain/letter-text";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { cn, fmtSec } from "@/lib/utils";
import { Pane, PaneHeader, PaneBody, ErrorCard } from "./pane";

const LANG_NAME: Record<string, string> = { de: "German", fr: "French", it: "Italian" };

export function SamplePicker({ ws, children, align = "start" }: { ws: Workspace; children: React.ReactNode; align?: "start" | "end" }) {
  const [open, setOpen] = React.useState(false);
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>{children}</PopoverTrigger>
      <PopoverContent align={align} className="w-[340px]">
        <p className="px-2.5 pt-1.5 pb-1 text-[11px] font-semibold tracking-[0.06em] text-muted uppercase">Sample letters · synthetic</p>
        <ul className="scrollbar-thin max-h-[min(60dvh,420px)] overflow-y-auto overscroll-contain">
          {ws.samples.map((s) => {
            const active = ws.source?.kind === "sample" && ws.source.id === s.id;
            return (
              <li key={s.id}>
                <button
                  onClick={() => {
                    setOpen(false);
                    void ws.analyze({ kind: "sample", id: s.id });
                  }}
                  className={cn("flex w-full items-start gap-3 rounded-xl px-2.5 py-2 text-left transition-colors hover:bg-sand-2", active && "bg-sand-2")}
                >
                  <span className="mt-0.5 grid h-6 w-8 shrink-0 place-items-center rounded-md bg-white text-[11px] font-bold text-brown uppercase ring-1 ring-line">{s.language}</span>
                  <span className="min-w-0">
                    <span className="block truncate text-[14px] font-medium text-ink">{s.title}</span>
                    <span className="block truncate text-[12.5px] text-muted">{s.type}</span>
                  </span>
                </button>
              </li>
            );
          })}
          {!ws.samples.length && <li className="px-2.5 py-4 text-sm text-muted">No samples available.</li>}
        </ul>
      </PopoverContent>
    </Popover>
  );
}

export function PasteDialog({ ws, open, onOpenChange }: { ws: Workspace; open: boolean; onOpenChange: (v: boolean) => void }) {
  const [text, setText] = React.useState("");
  const submit = () => {
    if (!text.trim()) return;
    onOpenChange(false);
    void ws.analyze({ kind: "text", text });
  };
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <div className="p-6">
          <DialogTitle>Paste a letter</DialogTitle>
          <DialogDescription className="mt-1">German, French or Italian. The text stays on this machine.</DialogDescription>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) submit();
            }}
            autoFocus
            rows={12}
            placeholder={"Betreibungsamt …\n\nZahlungsbefehl – Betreibung Nr. …"}
            className="scrollbar-thin mt-4 w-full resize-y rounded-2xl border border-line bg-paper p-4 text-[14px] leading-relaxed text-ink outline-none placeholder:text-faint focus:border-ink/25"
          />
          <div className="mt-4 flex items-center justify-between gap-3">
            <span className="text-[12.5px] text-muted">Ctrl + Enter to analyse</span>
            <Button onClick={submit} disabled={!text.trim()} arrow>
              Analyse letter
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function LetterPane({ ws, activeFact, setActiveFact, redact, className }: { ws: Workspace; activeFact: string | null; setActiveFact: (id: string | null) => void; redact: boolean; className?: string }) {
  const [pasteOpen, setPasteOpen] = React.useState(false);
  const [uploadErr, setUploadErr] = React.useState<string | null>(null);
  const [uploading, setUploading] = React.useState(false);
  const [dragOver, setDragOver] = React.useState(false);
  const fileRef = React.useRef<HTMLInputElement>(null);
  const a = ws.analysis;

  const onFile = async (f: File | undefined) => {
    if (!f || !ws.api) return;
    setUploadErr(null);
    setUploading(true);
    try {
      const { text } = await ws.api.ingest(f);
      if (!text.trim()) throw new Error("No text could be extracted from this file (scanned PDFs need OCR, which is out of scope).");
      await ws.analyze({ kind: "text", text, name: f.name });
    } catch (e) {
      setUploadErr(e instanceof Error ? e.message : String(e));
    } finally {
      setUploading(false);
    }
  };

  return (
    <Pane
      className={className}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        void onFile(e.dataTransfer.files?.[0]);
      }}
    >
      <PaneHeader
        icon={<FileText className="size-4" />}
        title="Letter"
        aside={
          a ? (
            <span className="rounded-pill bg-sand-2 px-2.5 py-1 text-[12px] font-semibold text-brown" title={`Detected: ${LANG_NAME[a.letter_lang]}`}>
              {a.letter_lang.toUpperCase()} · {LANG_NAME[a.letter_lang]}
            </span>
          ) : null
        }
      >
        <div className="mt-3 flex flex-wrap gap-1.5">
          <SamplePicker ws={ws}>
            <button className="inline-flex h-8 items-center gap-1.5 rounded-pill bg-sand-2 px-3 text-[13px] font-medium text-ink transition-colors hover:bg-sand">
              <Library className="size-3.5" /> Samples <ChevronDown className="size-3.5 text-muted" />
            </button>
          </SamplePicker>
          <button onClick={() => setPasteOpen(true)} className="inline-flex h-8 items-center gap-1.5 rounded-pill bg-sand-2 px-3 text-[13px] font-medium text-ink transition-colors hover:bg-sand">
            <ClipboardPaste className="size-3.5" /> Paste
          </button>
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="inline-flex h-8 items-center gap-1.5 rounded-pill bg-sand-2 px-3 text-[13px] font-medium text-ink transition-colors hover:bg-sand disabled:opacity-60"
          >
            {uploading ? <Loader2 className="size-3.5 animate-spin" /> : <FileUp className="size-3.5" />} Upload PDF
          </button>
          <input ref={fileRef} type="file" accept=".pdf,.txt,application/pdf,text/plain" className="sr-only" tabIndex={-1} onChange={(e) => void onFile(e.target.files?.[0])} />
        </div>
      </PaneHeader>
      <PaneBody>
        {dragOver && (
          <div className="pointer-events-none absolute inset-3 z-10 grid place-items-center rounded-3xl border-2 border-dashed border-ink/25 bg-white/85 text-[15px] font-medium text-ink">
            Drop a PDF or .txt letter
          </div>
        )}
        {uploadErr && (
          <div className="mb-3 flex items-start gap-2 rounded-2xl bg-warn-soft p-3 text-[13px] text-warn">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" /> {uploadErr}
          </div>
        )}
        {ws.analyzing && <LetterSkeleton />}
        {!ws.analyzing && ws.analyzeError && (
          <ErrorCard
            title="The letter could not be analysed"
            message={ws.analyzeError}
            action={
              ws.source ? (
                <Button size="sm" variant="outline" onClick={() => ws.source && void ws.analyze(ws.source)}>
                  <RotateCcw className="size-3.5" /> Try again
                </Button>
              ) : null
            }
          />
        )}
        {!ws.analyzing && !ws.analyzeError && !a && ws.boot.status !== "loading" && (
          <div className="grid h-full min-h-[280px] place-items-center text-center">
            <div className="max-w-[280px]">
              <p className="text-[17px] font-semibold tracking-[-0.02em] text-ink">No letter yet</p>
              <p className="mt-1.5 text-[14px] text-muted">Pick a sample, paste text or drop a PDF anywhere on this pane.</p>
            </div>
          </div>
        )}
        {!ws.analyzing && a && (
          <article aria-label="Letter text" className="rounded-2xl bg-paper p-4 ring-1 ring-line sm:p-5">
            <LetterText text={a.text} facts={a.facts} activeId={activeFact} onHover={setActiveFact} redact={redact} />
          </article>
        )}
      </PaneBody>
      {a && !ws.analyzing && (
        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-line px-5 py-3">
          <FactLegend />
          <span className="text-[12px] text-muted">{a.facts.length} facts{a.timings.total ? ` · ${fmtSec(a.timings.total)}` : ""}</span>
        </div>
      )}
      <PasteDialog ws={ws} open={pasteOpen} onOpenChange={setPasteOpen} />
    </Pane>
  );
}

function LetterSkeleton() {
  return (
    <div className="space-y-2.5 rounded-2xl bg-paper p-5 ring-1 ring-line" aria-busy="true" aria-label="Analysing letter">
      {[38, 52, 30, 0, 22, 28, 26, 0, 44, 70, 92, 84, 66, 0, 96, 90, 72].map((w, i) =>
        w ? <div key={i} className="h-3 animate-pulse rounded-full bg-sand" style={{ width: `${w}%`, animationDelay: `${i * 60}ms` }} /> : <div key={i} className="h-2" />,
      )}
      <p className="pt-3 text-[13px] text-muted">Extracting facts — Swiss-format rules and Apertus run side by side…</p>
    </div>
  );
}
