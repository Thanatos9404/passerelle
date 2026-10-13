"use client";

import * as React from "react";
import { motion } from "motion/react";
import { FileText, Languages, Sparkles } from "lucide-react";
import type { AuditEntry } from "@/lib/api/types";
import { useWorkspace } from "./use-workspace";
import { LetterPane } from "./letter-pane";
import { FactsPane } from "./facts-pane";
import { ClientPane, type ClientTab } from "./client-pane";
import { AuditSheet, CommandPalette, ExportMenu, TopBar } from "./topbar";
import { PrintSheet } from "./print-sheet";
import { ErrorCard } from "./pane";
import { cn } from "@/lib/utils";

type PaneKey = "letter" | "facts" | "client";

const PANES: { key: PaneKey; label: string; icon: typeof FileText }[] = [
  { key: "letter", label: "Letter", icon: FileText },
  { key: "facts", label: "Facts", icon: Sparkles },
  { key: "client", label: "Client", icon: Languages },
];

export function WorkspaceApp() {
  const ws = useWorkspace();
  const [activeFact, setActiveFact] = React.useState<string | null>(null);
  const [redact, setRedact] = React.useState(false);
  const [tab, setTab] = React.useState<ClientTab>("explanation");
  const [mobilePane, setMobilePane] = React.useState<PaneKey>("letter");
  const [midPane, setMidPane] = React.useState<"letter" | "facts">("letter");
  const [cmdOpen, setCmdOpen] = React.useState(false);
  const [auditOpen, setAuditOpen] = React.useState(false);
  const [audit, setAudit] = React.useState<AuditEntry[]>([]);
  const [printKind, setPrintKind] = React.useState<"client" | "caseworker" | null>(null);

  // Ctrl/Cmd+K command palette
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCmdOpen((v) => !v);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // when an explanation starts on a phone, jump to the client pane
  React.useEffect(() => {
    if (ws.explain.status === "streaming") {
      setMobilePane("client");
      setTab("explanation");
    }
  }, [ws.explain.status]);

  const print = React.useCallback(
    async (kind: "client" | "caseworker") => {
      if (kind === "caseworker" && ws.api) {
        try {
          setAudit(await ws.api.audit());
        } catch {
          /* print without audit */
        }
      }
      setPrintKind(kind);
      document.body.setAttribute("data-printing", kind);
      const done = () => {
        document.body.removeAttribute("data-printing");
        setPrintKind(null);
        window.removeEventListener("afterprint", done);
      };
      window.addEventListener("afterprint", done);
      requestAnimationFrame(() => requestAnimationFrame(() => window.print()));
    },
    [ws.api],
  );

  const shared = { ws, activeFact, setActiveFact };

  if (ws.boot.status === "error")
    return (
      <div className="grid min-h-dvh place-items-center bg-sand-2 p-6">
        <div className="w-full max-w-md">
          <ErrorCard
            title="The workspace could not start"
            message={`${ws.boot.error ?? "Unknown error"}. If you are running against the backend, check that FastAPI is up and NEXT_PUBLIC_API_BASE points to it.`}
          />
        </div>
      </div>
    );

  return (
    <>
      <div data-app-root className="flex h-dvh flex-col overflow-hidden bg-sand-2">
        <TopBar ws={ws} onCommand={() => setCmdOpen(true)} onAudit={() => setAuditOpen(true)} exportMenu={<ExportMenu ws={ws} redact={redact} setRedact={setRedact} onPrint={print} />} />

        {/* phone: 3-way switch · tablet: letter/facts switch for the left column */}
        <div className="px-3 pb-2 md:hidden">
          <div role="tablist" aria-label="Workspace panes" className="grid grid-cols-3 gap-1 rounded-pill bg-white p-1 ring-1 ring-line">
            {PANES.map((p) => {
              const active = mobilePane === p.key;
              const Icon = p.icon;
              return (
                <button
                  key={p.key}
                  role="tab"
                  aria-selected={active}
                  onClick={() => setMobilePane(p.key)}
                  className={cn("relative flex h-9 items-center justify-center gap-1.5 rounded-pill text-[13.5px] font-medium", active ? "text-white" : "text-muted")}
                >
                  {active && <motion.span layoutId="mobile-pane" className="absolute inset-0 rounded-pill bg-ink" transition={{ type: "spring", stiffness: 420, damping: 34 }} />}
                  <span className="relative inline-flex items-center gap-1.5">
                    <Icon className="size-3.5" /> {p.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        <main className="grid min-h-0 flex-1 grid-cols-1 gap-3 px-3 pb-3 md:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)] md:px-4 md:pb-4 xl:grid-cols-[minmax(0,1.02fr)_minmax(0,0.86fr)_minmax(0,1.18fr)]">
          <div className={cn("min-h-0 flex-col gap-2 md:flex xl:contents", mobilePane === "client" ? "hidden" : "flex")}>
            <div role="tablist" aria-label="Left column" className="hidden shrink-0 gap-1 self-start rounded-pill bg-white p-1 ring-1 ring-line md:flex xl:hidden">
              {(["letter", "facts"] as const).map((k) => (
                <button
                  key={k}
                  role="tab"
                  aria-selected={midPane === k}
                  onClick={() => setMidPane(k)}
                  className={cn("relative h-8 rounded-pill px-4 text-[13px] font-medium capitalize", midPane === k ? "text-white" : "text-muted")}
                >
                  {midPane === k && <motion.span layoutId="mid-pane" className="absolute inset-0 rounded-pill bg-ink" transition={{ type: "spring", stiffness: 420, damping: 34 }} />}
                  <span className="relative">{k === "letter" ? "Letter" : "Fact card"}</span>
                </button>
              ))}
            </div>
            <LetterPane
              {...shared}
              redact={redact}
              className={cn("min-h-0 flex-1", mobilePane === "letter" ? "flex" : "hidden", midPane === "letter" ? "md:flex" : "md:hidden", "xl:flex")}
            />
            <FactsPane {...shared} className={cn("min-h-0 flex-1", mobilePane === "facts" ? "flex" : "hidden", midPane === "facts" ? "md:flex" : "md:hidden", "xl:flex")} />
          </div>
          <ClientPane {...shared} tab={tab} setTab={setTab} onPrint={print} className={cn("min-h-0", mobilePane === "client" ? "flex" : "hidden", "md:flex")} />
        </main>
      </div>

      <CommandPalette ws={ws} open={cmdOpen} onOpenChange={setCmdOpen} onPrint={print} onAudit={() => setAuditOpen(true)} />
      <AuditSheet ws={ws} open={auditOpen} onOpenChange={setAuditOpen} entries={audit} setEntries={setAudit} />
      <PrintSheet ws={ws} kind={printKind} redact={redact} audit={audit} />
    </>
  );
}
