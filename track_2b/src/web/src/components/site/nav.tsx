"use client";

import * as React from "react";
import Link from "next/link";
import { motion, useMotionValueEvent, useScroll } from "motion/react";
import { Menu } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { ButtonLink } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

const LINKS = [
  { href: "/#how", label: "How it works" },
  { href: "/#languages", label: "Languages" },
  { href: "/#sovereignty", label: "Sovereignty" },
  { href: "/evidence/", label: "Evidence" },
];

/** OBLIQ nav: full-width and transparent at the top, morphs into a centred frosted pill on scroll. */
export function SiteNav() {
  const { scrollY } = useScroll();
  const [compact, setCompact] = React.useState(false);
  useMotionValueEvent(scrollY, "change", (v) => setCompact(v > 40));

  return (
    <header className="pointer-events-none fixed inset-x-0 top-0 z-40 flex justify-center px-3 pt-3 md:pt-4">
      <motion.nav
        aria-label="Main"
        initial={false}
        animate={{
          maxWidth: compact ? 880 : 1200,
          paddingLeft: compact ? 18 : 12,
          paddingRight: compact ? 8 : 12,
          backgroundColor: compact ? "rgba(255,255,255,0.72)" : "rgba(255,255,255,0)",
          borderColor: compact ? "rgba(26,22,21,0.07)" : "rgba(26,22,21,0)",
          boxShadow: compact ? "0 4px 50px 0 rgba(97,74,68,0.12)" : "0 0 0 0 rgba(97,74,68,0)",
        }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className={cn(
          "pointer-events-auto flex h-[60px] w-full items-center justify-between rounded-pill border md:h-[68px]",
          compact && "backdrop-blur-md",
        )}
      >
        <Link href="/" className="rounded-pill outline-none focus-visible:ring-2 focus-visible:ring-ink/40" aria-label="Passerelle home">
          <Logo />
        </Link>
        <ul className="hidden items-center gap-1 md:flex">
          {LINKS.map((l) => (
            <li key={l.href}>
              <Link
                href={l.href}
                className="rounded-pill px-3.5 py-2 text-[15.5px] text-ink/85 transition-colors hover:bg-white/60 hover:text-ink"
              >
                {l.label}
              </Link>
            </li>
          ))}
        </ul>
        <div className="flex items-center gap-2">
          <ButtonLink href="/workspace/" size="md" className="hidden sm:inline-flex">
            Open workspace
          </ButtonLink>
          <Sheet>
            <SheetTrigger
              className="grid size-11 place-items-center rounded-full bg-white/80 text-ink shadow-card md:hidden"
              aria-label="Open menu"
            >
              <Menu className="size-5" />
            </SheetTrigger>
            <SheetContent side="right" className="p-6">
              <SheetTitle className="sr-only">Menu</SheetTitle>
              <Logo />
              <ul className="mt-10 flex flex-col gap-1">
                {LINKS.map((l) => (
                  <li key={l.href}>
                    <Link href={l.href} className="block rounded-2xl px-3 py-3 text-[22px] font-semibold tracking-[-0.03em] text-ink hover:bg-sand-2">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
              <ButtonLink href="/workspace/" size="lg" arrow className="mt-auto w-full">
                Open workspace
              </ButtonLink>
            </SheetContent>
          </Sheet>
        </div>
      </motion.nav>
    </header>
  );
}
