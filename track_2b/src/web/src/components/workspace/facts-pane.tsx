"use client";

import * as React from "react";
import { AlertTriangle, Check, ChevronsUpDown, Copy, Languages, Mail, MapPin, Phone, Clock, Sparkles, Square, SquareCheck } from "lucide-react";
import type { Workspace } from "./use-workspace";
import type { Language } from "@/lib/api/types";
import { DeadlineTile } from "@/components/domain/widgets";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Button } from "@/components/ui/button";
import { Tip } from "@/components/ui/tooltip";
import { FAMILY_STYLE, factFamily } from "@/lib/facts";
import { cn, fmtChf } from "@/lib/utils";
import { Pane, PaneBody, PaneHeader, SectionLabel } from "./pane";

export function langAttr(code: string) {
  return code === "prs" ? "fa-AF" : code;
}

export function LanguagePicker({ ws, children, align = "start" }: { ws: Workspace; children: React.ReactNode; align?: "start" | "end" | "center" }) {
  const [open, setOpen] = React.useState(false);
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>{children}</PopoverTrigger>
      <PopoverContent align={align} className="w-[340px] p-0">
        <Command>
          <CommandInput placeholder="Search languages…" />
          <CommandList>
            <CommandEmpty>No language found.</CommandEmpty>
            <CommandGroup heading="Client language">
              {ws.languages.map((l) => (
                <CommandItem
                  key={l.code}
                  value={`${l.name} ${l.native_name} ${l.code} ${l.script}`}
                  onSelect={() => {
                    ws.setTargetLang(l.code);
                    setOpen(false);
                  }}
                >
                  <LanguageRow l={l} selected={l.code === ws.targetLang} />
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

function LanguageRow({ l, selected }: { l: Language; selected: boolean }) {
  return (
    <>
      <span lang={langAttr(l.code)} dir={l.rtl ? "rtl" : "ltr"} className="w-[92px] shrink-0 truncate text-[16px] font-semibold text-ink">
        {l.native_name}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-[13.5px] text-ink">{l.name}</span>
        <span className="block truncate text-[11.5px] text-muted">
          {l.script}
          {l.rtl ? " · RTL" : ""} · {l.quality_tier ? `tier ${l.quality_tier}` : "tier: not evaluated"}
        </span>
      </span>
      {selected && <Check className="size-4 shrink-0 text-ink" />}
    </>
  );
}

function FactRow({ label, value, factId, ws, activeFact, setActiveFact, mono }: { label: string; value: string; factId?: string | null; ws: Workspace; activeFact: string | null; setActiveFact: (id: string | null) => void; mono?: boolean }) {
  const [copied, setCopied] = React.useState(false);
  const fact = factId ? ws.analysis?.facts.find((f) => f.id === factId) : undefined;
  const fam = fact ? FAMILY_STYLE[factFamily(fact.type)] : null;
  return (
    <li
      onMouseEnter={() => factId && setActiveFact(factId)}
      onMouseLeave={() => setActiveFact(null)}
      className={cn("group flex items-center gap-3 rounded-xl px-2.5 py-2 transition-colors", activeFact && activeFact === factId ? "bg-sand-2" : "hover:bg-sand-2/60")}
    >
      {fam && <span className={cn("size-2 shrink-0 rounded-full", fam.dot)} aria-hidden />}
      <span className="min-w-0 flex-1 truncate text-[13.5px] text-body">{label}</span>
      <span dir="ltr" className={cn("t-num shrink-0 text-[14px] font-semibold text-ink", mono && "font-mono text-[12.5px] font-medium")}>
        {value}
      </span>
      <Tip label={copied ? "Copied" : "Copy"}>
        <button
          aria-label={`Copy ${label}`}
          onClick={() => {
            void navigator.clipboard?.writeText(value).then(() => {
              setCopied(true);
              setTimeout(() => setCopied(false), 1200);
            });
          }}
          className="grid size-6 shrink-0 place-items-center rounded-md text-muted opacity-0 transition group-hover:opacity-100 hover:text-ink focus-visible:opacity-100"
        >
          {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
        </button>
      </Tip>
    </li>
  );
}

export function FactsPane({ ws, activeFact, setActiveFact, className }: { ws: Workspace; activeFact: string | null; setActiveFact: (id: string | null) => void; className?: string }) {
  const a = ws.analysis;
  const c = a?.fact_card;
  const [checked, setChecked] = React.useState<Record<number, boolean>>({});
  React.useEffect(() => setChecked({}), [a?.analysis_id]);
  const l = ws.language;
  const streaming = ws.explain.status === "streaming";

  return (
    <Pane className={className}>
      <PaneHeader icon={<Sparkles className="size-4" />} title="Fact card" aside={a ? <span className="text-[12px] text-muted">{a.facts.length} facts locked</span> : null} />
      <PaneBody className="space-y-5">
        {ws.analyzing || !a || !c ? (
          <FactsSkeleton loading={ws.analyzing || ws.boot.status === "loading"} />
        ) : (
          <>
            <div>
              {c.letter_type && <p className="text-[11.5px] font-semibold tracking-[0.06em] text-muted uppercase">{c.letter_type}</p>}
              <p className="mt-1 text-[18px] leading-snug font-semibold tracking-[-0.025em] text-ink">{c.authority ?? "Unknown authority"}</p>
              {c.summary && <p className="mt-1.5 text-[13.5px] leading-relaxed text-body">{c.summary}</p>}
            </div>

            {a.warnings?.map((w, i) => (
              <div key={i} className="flex items-start gap-2 rounded-2xl bg-warn-soft p-3 text-[13px] leading-relaxed text-warn">
                <AlertTriangle className="mt-0.5 size-4 shrink-0" /> {w}
              </div>
            ))}

            {c.required_action && (
              <div className="rounded-2xl bg-ink p-4 text-white">
                <p className="text-[11px] font-semibold tracking-[0.08em] text-white/55 uppercase">What the client must do</p>
                <p className="mt-1.5 text-[14.5px] leading-relaxed">{c.required_action}</p>
              </div>
            )}

            {a.disagreements.length > 0 && (
              <div className="space-y-2">
                {a.disagreements.map((d, i) => (
                  <div key={i} className="rounded-2xl bg-warn-soft p-3.5 text-[13px] leading-relaxed text-ink">
                    <p className="flex items-center gap-1.5 font-semibold text-warn">
                      <AlertTriangle className="size-4" /> Extractors disagree: {d.field}
                    </p>
                    <p className="mt-1.5 text-body">
                      <span className="font-medium text-ink">Rules:</span> {d.deterministic ?? "—"}
                      <br />
                      <span className="font-medium text-ink">Apertus:</span> {d.llm ?? "—"}
                    </p>
                    {d.note && <p className="mt-1 text-muted">{d.note}</p>}
                  </div>
                ))}
              </div>
            )}

            {c.deadlines.length > 0 && (
              <div>
                <SectionLabel>Deadlines</SectionLabel>
                <div className="space-y-2">
                  {c.deadlines.map((d, i) => (
                    <div key={i} onMouseEnter={() => d.fact_id && setActiveFact(d.fact_id)} onMouseLeave={() => setActiveFact(null)}>
                      <DeadlineTile label={d.label} iso={d.date} relative={d.relative} emphasis={i === 0} />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {(c.amounts.length > 0 || c.reference_numbers.length > 0) && (
              <div>
                <SectionLabel>Amounts &amp; references</SectionLabel>
                <ul className="-mx-1">
                  {c.amounts.map((m, i) => (
                    <FactRow key={`a${i}`} ws={ws} label={m.label} value={m.display ?? (m.currency === "CHF" ? fmtChf(m.value) : `${m.currency} ${m.value ?? "—"}`)} factId={m.fact_id} activeFact={activeFact} setActiveFact={setActiveFact} />
                  ))}
                  {c.reference_numbers.map((r, i) => (
                    <FactRow key={`r${i}`} ws={ws} label={r.label} value={r.value} factId={r.fact_id} activeFact={activeFact} setActiveFact={setActiveFact} mono={r.value.length > 16} />
                  ))}
                </ul>
              </div>
            )}

            {c.documents_to_bring.length > 0 && (
              <div>
                <SectionLabel>Documents to bring</SectionLabel>
                <ul className="space-y-1">
                  {c.documents_to_bring.map((d, i) => (
                    <li key={i}>
                      <button
                        onClick={() => setChecked((s) => ({ ...s, [i]: !s[i] }))}
                        className="flex w-full items-start gap-2.5 rounded-xl px-2 py-1.5 text-left text-[13.5px] text-body transition-colors hover:bg-sand-2/60"
                        aria-pressed={!!checked[i]}
                      >
                        {checked[i] ? <SquareCheck className="mt-0.5 size-4 shrink-0 text-ok" /> : <Square className="mt-0.5 size-4 shrink-0 text-faint" />}
                        <span className={cn(checked[i] && "text-muted line-through")}>{d}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {c.consequences && (
              <div className="rounded-2xl bg-stop-soft/60 p-3.5">
                <p className="text-[11.5px] font-semibold tracking-[0.06em] text-stop uppercase">If ignored</p>
                <p className="mt-1 text-[13.5px] leading-relaxed text-ink">{c.consequences}</p>
              </div>
            )}

            {c.contact && (
              <div>
                <SectionLabel>Contact</SectionLabel>
                <ul className="space-y-1.5 text-[13.5px] text-body">
                  {c.contact.name && <li className="font-medium text-ink">{c.contact.name}</li>}
                  {c.contact.phone && (
                    <li className="flex items-center gap-2">
                      <Phone className="size-3.5 text-muted" /> <span dir="ltr">{c.contact.phone}</span>
                    </li>
                  )}
                  {c.contact.email && (
                    <li className="flex items-center gap-2">
                      <Mail className="size-3.5 text-muted" /> {c.contact.email}
                    </li>
                  )}
                  {c.contact.address && (
                    <li className="flex items-center gap-2">
                      <MapPin className="size-3.5 text-muted" /> {c.contact.address}
                    </li>
                  )}
                  {c.contact.hours && (
                    <li className="flex items-center gap-2">
                      <Clock className="size-3.5 text-muted" /> {c.contact.hours}
                    </li>
                  )}
                </ul>
              </div>
            )}
          </>
        )}
      </PaneBody>

      {/* client language + primary action */}
      <div className="border-t border-line bg-paper/70 p-4">
        <p className="mb-2 flex items-center gap-1.5 text-[11.5px] font-semibold tracking-[0.06em] text-muted uppercase">
          <Languages className="size-3.5" /> Client language
        </p>
        <LanguagePicker ws={ws}>
          <button
            className="flex h-12 w-full items-center gap-3 rounded-2xl bg-white px-3.5 text-left ring-1 ring-line transition hover:ring-ink/20"
            aria-label={`Client language: ${l?.name ?? ws.targetLang}. Change`}
          >
            {l ? (
              <>
                <span lang={langAttr(l.code)} dir={l.rtl ? "rtl" : "ltr"} className="text-[17px] font-semibold text-ink">
                  {l.native_name}
                </span>
                <span className="truncate text-[13px] text-muted">
                  {l.name} · {l.script}
                  {l.rtl ? " · RTL" : ""}
                </span>
              </>
            ) : (
              <span className="text-[14px] text-muted">Choose a language</span>
            )}
            <ChevronsUpDown className="ml-auto size-4 shrink-0 text-muted" />
          </button>
        </LanguagePicker>
        <Button size="lg" className="mt-3 w-full" arrow={!streaming} disabled={!a || ws.analyzing || streaming || !l} onClick={() => void ws.runExplain()}>
          {streaming ? (
            "Explaining…"
          ) : (
            <span className="truncate">
              Explain in{" "}
              <span lang={l ? langAttr(l.code) : undefined} className="font-semibold">
                {l?.native_name ?? "…"}
              </span>
            </span>
          )}
        </Button>
      </div>
    </Pane>
  );
}

function FactsSkeleton({ loading }: { loading: boolean }) {
  if (!loading)
    return <p className="py-10 text-center text-[14px] text-muted">The fact card appears once a letter is analysed.</p>;
  return (
    <div className="space-y-4" aria-busy="true">
      <div className="h-3 w-1/3 animate-pulse rounded-full bg-sand" />
      <div className="h-5 w-2/3 animate-pulse rounded-full bg-sand" />
      <div className="h-24 animate-pulse rounded-2xl bg-sand-2" />
      <div className="h-[86px] animate-pulse rounded-2xl bg-sand-2" />
      <div className="h-[86px] animate-pulse rounded-2xl bg-sand-2" />
    </div>
  );
}
