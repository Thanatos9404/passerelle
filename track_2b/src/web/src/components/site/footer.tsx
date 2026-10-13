"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import { Logo } from "@/components/brand/logo";
import { ButtonLink } from "@/components/ui/button";
import { Magnetic, WordReveal } from "@/components/motion/primitives";

function Clouds() {
  const reduce = useReducedMotion();
  return (
    <div aria-hidden className="pointer-events-none absolute inset-x-0 top-0 h-[520px] overflow-hidden">
      <motion.img
        src="/photos/cloud-a.webp"
        alt=""
        className="absolute top-10 -left-[14%] w-[38vw] max-w-[560px] min-w-[240px] opacity-95"
        animate={reduce ? undefined : { x: [0, 26, 0] }}
        transition={{ duration: 28, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.img
        src="/photos/cloud-a.webp"
        alt=""
        className="absolute top-4 -right-[13%] w-[36vw] max-w-[540px] min-w-[220px] -scale-x-100 opacity-95"
        animate={reduce ? undefined : { x: [0, -24, 0] }}
        transition={{ duration: 31, repeat: Infinity, ease: "easeInOut" }}
      />
    </div>
  );
}

/** Final CTA band on the sky + frosted footer panel (OBLIQ pattern). */
export function CtaFooter({ cta = true }: { cta?: boolean }) {
  return (
    <div className="relative isolate overflow-hidden" style={{ background: "linear-gradient(180deg, #F4F1EE 0%, #CFE1F3 22%, #B7D5F1 60%, #C7DDF2 100%)" }}>
      <Clouds />
      {cta && (
        <section className="container-x relative flex flex-col items-center pt-32 pb-24 text-center md:pt-44 md:pb-32">
          <WordReveal className="t-h2 !text-[clamp(36px,5vw,64px)]" lines={[{ text: "Ready for the next letter." }]} />
          <p className="t-lead mt-5 max-w-[520px]">Open the workspace, pick a sample letter and explain it in a client language.</p>
          <Magnetic className="mt-9">
            <ButtonLink href="/workspace/" size="lg" arrow>
              Open workspace
            </ButtonLink>
          </Magnetic>
        </section>
      )}
      <footer className="container-x relative pb-8 md:pb-12">
        <div className="frost rounded-4xl border border-white/60 p-7 md:p-10">
          <div className="grid grid-cols-1 gap-10 sm:grid-cols-2 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
            <div>
              <Logo />
              <p className="mt-4 max-w-[300px] text-[15px] leading-relaxed text-body">
                A sovereign caseworker assistant on Apertus. Built for Hack Apertus 2026, Track 2B.
              </p>
            </div>
            <nav aria-label="Product">
              <p className="text-[14px] font-semibold tracking-[0.02em] text-ink uppercase">Product</p>
              <ul className="mt-4 flex flex-col gap-3 text-[15px] text-body">
                <li><Link className="hover:text-ink" href="/workspace/">Workspace</Link></li>
                <li><Link className="hover:text-ink" href="/evidence/">Evidence</Link></li>
                <li><Link className="hover:text-ink" href="/#how">How it works</Link></li>
              </ul>
            </nav>
            <div>
              <p className="text-[14px] font-semibold tracking-[0.02em] text-ink uppercase">Licences</p>
              <ul className="mt-4 flex flex-col gap-3 text-[15px] text-body">
                <li>Code · Apache-2.0</li>
                <li>Docs · CC-BY-4.0</li>
                <li>Data · CDLA-Permissive-2.0</li>
              </ul>
            </div>
            <div>
              <p className="text-[14px] font-semibold tracking-[0.02em] text-ink uppercase">Honesty</p>
              <ul className="mt-4 flex flex-col gap-3 text-[15px] text-body">
                <li>Synthetic letters only</li>
                <li>Not legal advice</li>
                <li>A caseworker approves every output</li>
              </ul>
            </div>
          </div>
          <div className="mt-10 flex flex-col gap-2 border-t border-ink/10 pt-6 text-[13.5px] text-muted md:flex-row md:items-center md:justify-between">
            <p>© 2026 Passerelle · fonts: Open Runde &amp; Noto (SIL OFL)</p>
            <p>
              Photos:{" "}
              <a className="underline decoration-ink/20 underline-offset-2 hover:text-ink" href="https://www.pexels.com/photo/serene-lake-brienz-in-summer-switzerland-38995800/">Maria Eduarda Godoi</a>{" "}
              &amp;{" "}
              <a className="underline decoration-ink/20 underline-offset-2 hover:text-ink" href="https://www.pexels.com/photo/stunning-view-of-the-swiss-alps-and-lake-34656976/">Jean-Paul Wettstein</a>{" "}
              on Pexels
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
