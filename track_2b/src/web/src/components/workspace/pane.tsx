"use client";

import * as React from "react";
import { AlertOctagon } from "lucide-react";
import { cn } from "@/lib/utils";

export function Pane({ className, children, ...props }: React.ComponentProps<"section">) {
  return (
    <section className={cn("relative flex min-h-0 flex-col overflow-hidden rounded-3xl bg-white shadow-card ring-1 ring-line", className)} {...props}>
      {children}
    </section>
  );
}

export function PaneHeader({ icon, title, aside, children }: { icon: React.ReactNode; title: React.ReactNode; aside?: React.ReactNode; children?: React.ReactNode }) {
  return (
    <header className="border-b border-line px-5 pt-4 pb-3.5">
      <div className="flex min-h-8 items-center gap-2.5">
        <span className="grid size-8 shrink-0 place-items-center rounded-full bg-sand-2 text-ink">{icon}</span>
        <h2 className="text-[15.5px] font-semibold tracking-[-0.02em] text-ink">{title}</h2>
        {aside && <div className="ml-auto flex min-w-0 items-center gap-2">{aside}</div>}
      </div>
      {children}
    </header>
  );
}

export function PaneBody({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("scrollbar-thin relative min-h-0 flex-1 overflow-y-auto overscroll-contain p-4 sm:p-5", className)}>{children}</div>;
}

export function ErrorCard({ title, message, action }: { title: string; message: string; action?: React.ReactNode }) {
  return (
    <div role="alert" className="rounded-2xl bg-stop-soft/70 p-4 ring-1 ring-stop/15">
      <div className="flex items-start gap-3">
        <AlertOctagon className="mt-0.5 size-5 shrink-0 text-stop" aria-hidden />
        <div className="min-w-0">
          <p className="text-[14.5px] font-semibold text-ink">{title}</p>
          <p className="mt-1 text-[13.5px] leading-relaxed break-words text-body">{message}</p>
          {action && <div className="mt-3">{action}</div>}
        </div>
      </div>
    </div>
  );
}

export function SectionLabel({ children, className }: { children: React.ReactNode; className?: string }) {
  return <h3 className={cn("mb-2.5 text-[11.5px] font-semibold tracking-[0.06em] text-muted uppercase", className)}>{children}</h3>;
}
