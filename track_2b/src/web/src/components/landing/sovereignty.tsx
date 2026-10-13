"use client";

import * as React from "react";
import { motion, useReducedMotion } from "motion/react";
import { Building2, Cloud, EyeOff, Fingerprint, Laptop, Scale, ShieldBan, Terminal } from "lucide-react";
import { Reveal, SectionHead, EASE } from "@/components/motion/primitives";
import { cn } from "@/lib/utils";

function Tile({ className, children, delay = 0 }: { className?: string; children: React.ReactNode; delay?: number }) {
  return (
    <Reveal delay={delay} className={cn("group h-full", className)}>
      <div className="flex h-full flex-col overflow-hidden rounded-4xl bg-sand p-6 transition-[transform,box-shadow] duration-500 ease-[cubic-bezier(.22,1,.36,1)] hover:-translate-y-1 hover:shadow-soft md:p-8">
        {children}
      </div>
    </Reveal>
  );
}

function TileText({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mt-auto pt-6">
      <h3 className="t-h3">{title}</h3>
      <p className="mt-2 text-[15.5px] leading-relaxed text-body">{children}</p>
    </div>
  );
}

const TERMINAL = [
  { t: "$ docker compose --profile local-llm up", c: "text-white" },
  { t: "llm  | loaded apertus-v1.5-8b-text Q4_K_M (GGUF)", c: "text-white/70" },
  { t: "llm  | offloading layers to GPU (6 GB VRAM)", c: "text-white/70" },
  { t: "app  | egress guard: only LLM_BASE_URL allowed", c: "text-[#9fd3a8]" },
  { t: "app  | UI + API listening on :8080", c: "text-white/70" },
];

function TerminalFrag() {
  const reduce = useReducedMotion();
  return (
    <div className="rounded-3xl bg-ink p-5 font-mono text-[12.5px] leading-[1.9] shadow-float md:text-[13px]">
      <div className="mb-3 flex gap-1.5" aria-hidden>
        {[0, 1, 2].map((i) => (
          <span key={i} className="size-2.5 rounded-full bg-white/20" />
        ))}
      </div>
      {TERMINAL.map((l, i) => (
        <motion.p
          key={i}
          className={cn("truncate", l.c)}
          initial={reduce ? false : { opacity: 0, x: -8 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, ease: EASE, delay: 0.25 + i * 0.22 }}
        >
          {l.t}
        </motion.p>
      ))}
    </div>
  );
}

function EgressFrag() {
  const rows = [
    { host: "llm:8080", ok: true },
    { host: "api.openai.com:443", ok: false },
    { host: "fonts.googleapis.com:443", ok: false },
  ];
  return (
    <ul className="flex flex-col gap-2">
      {rows.map((r) => (
        <li key={r.host} className="flex items-center gap-3 rounded-2xl bg-white px-4 py-3 text-[13.5px] shadow-[0_1px_2px_rgba(97,74,68,.06)]">
          <span className={cn("rounded-pill px-2 py-0.5 text-[11px] font-bold tracking-[0.04em]", r.ok ? "bg-ok-soft text-ok" : "bg-stop-soft text-stop")}>{r.ok ? "ALLOW" : "BLOCK"}</span>
          <span className="truncate font-mono text-[12.5px] text-ink">{r.host}</span>
        </li>
      ))}
    </ul>
  );
}

function AuditFrag() {
  const steps = ["analyze", "explain:ti", "verify", "reply"];
  const [hashes, setHashes] = React.useState<string[]>(steps.map(() => ""));
  React.useEffect(() => {
    // real SHA-256 digests of the step names, computed in the browser — illustrative of the format only
    Promise.all(
      steps.map(async (s) => {
        try {
          const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`passerelle:${s}`));
          return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
        } catch {
          return "";
        }
      }),
    ).then(setHashes);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <ul className="flex flex-col gap-1.5 rounded-2xl bg-white p-3 shadow-[0_1px_2px_rgba(97,74,68,.06)]">
      {steps.map((s, i) => (
        <li key={s} className="flex items-center gap-3 px-1.5 py-1 text-[12.5px]">
          <span className="w-[74px] shrink-0 font-medium text-ink">{s}</span>
          <span className="truncate font-mono text-muted">{hashes[i] ? `sha256:${hashes[i].slice(0, 28)}…` : "sha256:…"}</span>
        </li>
      ))}
    </ul>
  );
}

function RedactFrag() {
  const [on, setOn] = React.useState(true);
  return (
    <div className="rounded-2xl bg-white p-4 shadow-[0_1px_2px_rgba(97,74,68,.06)]">
      <div className="flex items-center justify-between">
        <span className="text-[13.5px] font-medium text-ink">Redact names &amp; addresses</span>
        <button
          role="switch"
          aria-checked={on}
          aria-label="Toggle redaction preview"
          onClick={() => setOn((v) => !v)}
          className={cn("relative h-6 w-11 rounded-pill transition-colors", on ? "bg-ok" : "bg-faint")}
        >
          <motion.span layout className={cn("absolute top-0.5 size-5 rounded-full bg-white shadow", on ? "right-0.5" : "left-0.5")} />
        </button>
      </div>
      <p className="mt-3 text-[13.5px] leading-relaxed text-body">
        Herr{" "}
        <span className={cn("rounded px-0.5 transition-colors", on ? "bg-ink text-transparent select-none" : "bg-f-contact-soft text-ink")}>Samuel Tesfay</span>,{" "}
        <span className={cn("rounded px-0.5 transition-colors", on ? "bg-ink text-transparent select-none" : "bg-f-contact-soft text-ink")}>Lindenweg 7</span>
      </p>
    </div>
  );
}

export function Sovereignty() {
  return (
    <section id="sovereignty" className="scroll-mt-24 bg-paper py-24 md:py-36">
      <div className="container-x">
        <SectionHead
          eyebrow="Sovereignty"
          title="Nothing leaves the building."
          muted="Not even a font request."
          lead="Asylum, health and social-assistance data stays where it belongs. Passerelle is designed for an air-gapped laptop first, and scales up without changing the code."
        />
        <div className="mt-14 grid grid-cols-1 gap-4 md:mt-20 md:grid-cols-6 md:gap-5">
          <Tile className="md:col-span-4">
            <div className="mb-1 flex items-center gap-2 text-[13px] font-medium text-brown">
              <Terminal className="size-4" /> Target architecture (b): air-gapped
            </div>
            <div className="mt-4">
              <TerminalFrag />
            </div>
            <TileText title="Runs on a laptop GPU">
              <strong className="font-semibold text-ink">Apertus v1.5 8B</strong>, quantised to Q4_K_M, served by llama.cpp on a 6 GB laptop GPU — no internet connection, no API key, no per-letter cost to a vendor.
            </TileText>
          </Tile>
          <Tile className="md:col-span-2" delay={0.08}>
            <div className="flex items-center gap-2 text-[13px] font-medium text-brown">
              <ShieldBan className="size-4" /> Egress guard
            </div>
            <div className="mt-4">
              <EgressFrag />
            </div>
            <TileText title="One allowed host">Every outbound connection except the configured model endpoint is refused.</TileText>
          </Tile>
          <Tile className="md:col-span-2">
            <div className="flex items-center gap-2 text-[13px] font-medium text-brown">
              <Fingerprint className="size-4" /> Append-only audit
            </div>
            <div className="mt-4">
              <AuditFrag />
            </div>
            <TileText title="Hashes, not content">Each step is logged as a hash, so a supervisor can prove what ran without the log holding anyone&apos;s letter.</TileText>
          </Tile>
          <Tile className="md:col-span-2" delay={0.08}>
            <div className="flex items-center gap-2 text-[13px] font-medium text-brown">
              <EyeOff className="size-4" /> Redaction
            </div>
            <div className="mt-4">
              <RedactFrag />
            </div>
            <TileText title="One-click redaction">Names and addresses are blacked out in exported copies when they leave the caseworker&apos;s desk.</TileText>
          </Tile>
          <Tile className="md:col-span-2" delay={0.16}>
            <div className="flex items-center gap-2 text-[13px] font-medium text-brown">
              <Scale className="size-4" /> Three deployments
            </div>
            <ul className="mt-4 flex flex-col gap-2 text-[14px]">
              {[
                { i: Laptop, t: "Air-gapped laptop", s: "8B · Q4_K_M · our target", hl: true },
                { i: Building2, t: "On-premise server", s: "8B or 70B, same Docker image", hl: false },
                { i: Cloud, t: "Swiss sovereign cloud", s: "70B via OpenAI-compatible API", hl: false },
              ].map(({ i: Icon, t, s, hl }) => (
                <li key={t} className={cn("flex items-center gap-3 rounded-2xl px-3.5 py-2.5", hl ? "bg-ink text-white" : "bg-white text-ink")}>
                  <Icon className="size-4 shrink-0" />
                  <span className="min-w-0">
                    <span className="block font-medium">{t}</span>
                    <span className={cn("block truncate text-[12px]", hl ? "text-white/65" : "text-muted")}>{s}</span>
                  </span>
                </li>
              ))}
            </ul>
            <TileText title="Same code, any scale">Only three environment variables change: model name, base URL and key.</TileText>
          </Tile>
        </div>
      </div>
    </section>
  );
}
