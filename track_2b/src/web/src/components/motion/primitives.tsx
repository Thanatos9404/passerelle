"use client";

import * as React from "react";
import { animate, motion, useInView, useMotionValue, useReducedMotion, useSpring, type Variants } from "motion/react";
import { cn } from "@/lib/utils";

export const EASE = [0.22, 1, 0.36, 1] as const;

/** Word-by-word blur-in headline. Lines are separate entries; `muted` lines render lighter. */
export function WordReveal({
  lines,
  className,
  as: Tag = "h2",
  delay = 0,
  stagger = 0.06,
  onMount = false,
}: {
  lines: { text: string; className?: string }[];
  className?: string;
  as?: "h1" | "h2" | "h3" | "p";
  delay?: number;
  stagger?: number;
  onMount?: boolean;
}) {
  const ref = React.useRef<HTMLHeadingElement>(null);
  const inView = useInView(ref, { once: true, margin: "0px 0px -12% 0px" });
  const reduce = useReducedMotion();
  const show = onMount || inView;
  let i = 0;
  const label = lines.map((l) => l.text).join(" ");
  return (
    <Tag ref={ref} className={className} aria-label={label}>
      {lines.map((line, li) => (
        <span key={li} className={cn("block", line.className)} aria-hidden>
          {line.text.split(" ").map((w, wi) => {
            const d = delay + i++ * stagger;
            return (
              <React.Fragment key={wi}>
                <motion.span
                  className="inline-block will-change-[filter,transform]"
                  initial={reduce ? false : { opacity: 0, y: "0.35em", filter: "blur(12px)" }}
                  animate={show ? { opacity: 1, y: 0, filter: "blur(0px)" } : undefined}
                  transition={{ duration: 0.85, ease: EASE, delay: d }}
                >
                  {w}
                </motion.span>
                {wi < line.text.split(" ").length - 1 ? " " : ""}
              </React.Fragment>
            );
          })}
        </span>
      ))}
    </Tag>
  );
}

const blurUp: Variants = {
  hidden: { opacity: 0, y: 26, filter: "blur(8px)" },
  show: { opacity: 1, y: 0, filter: "blur(0px)" },
};

/** Blur-up entrance when scrolled into view. */
export function Reveal({
  children,
  className,
  delay = 0,
  y = 26,
  as = "div",
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  y?: number;
  as?: "div" | "li" | "section" | "p";
}) {
  const reduce = useReducedMotion();
  const MotionTag = motion[as] as typeof motion.div;
  return (
    <MotionTag
      className={className}
      initial={reduce ? false : "hidden"}
      whileInView="show"
      viewport={{ once: true, margin: "0px 0px -10% 0px" }}
      variants={{ hidden: { ...blurUp.hidden, y }, show: blurUp.show }}
      transition={{ duration: 0.9, ease: EASE, delay }}
    >
      {children}
    </MotionTag>
  );
}

/** Counts up to a value when visible. Renders an em dash when the value is missing. */
export function Ticker({
  value,
  format,
  className,
}: {
  value: number | null | undefined;
  format: (v: number) => string;
  className?: string;
}) {
  const ref = React.useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const reduce = useReducedMotion();
  const [display, setDisplay] = React.useState<string>(() => (value == null ? "—" : format(reduce ? value : 0)));
  React.useEffect(() => {
    if (value == null) {
      setDisplay("—");
      return;
    }
    if (!inView) return;
    if (reduce) {
      setDisplay(format(value));
      return;
    }
    const c = animate(0, value, { duration: 1.4, ease: EASE, onUpdate: (v) => setDisplay(format(v)) });
    return () => c.stop();
  }, [value, inView, reduce, format]);
  return (
    <span ref={ref} className={cn("t-num", className)}>
      {display}
    </span>
  );
}

/** Subtle magnetic pull toward the cursor (desktop pointers only). */
export function Magnetic({ children, strength = 0.25, className }: { children: React.ReactNode; strength?: number; className?: string }) {
  const ref = React.useRef<HTMLDivElement>(null);
  const reduce = useReducedMotion();
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const sx = useSpring(x, { stiffness: 260, damping: 18, mass: 0.4 });
  const sy = useSpring(y, { stiffness: 260, damping: 18, mass: 0.4 });
  return (
    <motion.div
      ref={ref}
      className={cn("inline-block", className)}
      style={reduce ? undefined : { x: sx, y: sy }}
      onPointerMove={(e) => {
        if (reduce || e.pointerType !== "mouse" || !ref.current) return;
        const r = ref.current.getBoundingClientRect();
        x.set((e.clientX - (r.left + r.width / 2)) * strength);
        y.set((e.clientY - (r.top + r.height / 2)) * strength);
      }}
      onPointerLeave={() => {
        x.set(0);
        y.set(0);
      }}
    >
      {children}
    </motion.div>
  );
}

/** Section heading anatomy from OBLIQ: eyebrow -> two-line H2 (second line muted) -> lead. */
export function SectionHead({
  eyebrow,
  title,
  muted,
  lead,
  align = "center",
  className,
}: {
  eyebrow: string;
  title: string;
  muted?: string;
  lead?: React.ReactNode;
  align?: "center" | "left";
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-4", align === "center" ? "items-center text-center" : "items-start text-left", className)}>
      <Reveal>
        <p className="t-eyebrow">{eyebrow}</p>
      </Reveal>
      <WordReveal
        className={cn("t-h2", align === "center" ? "max-w-[860px]" : "max-w-[620px]")}
        lines={[{ text: title }, ...(muted ? [{ text: muted, className: "text-muted" }] : [])]}
      />
      {lead && (
        <Reveal delay={0.15} className={cn("t-lead max-w-[640px]", align === "center" && "mx-auto")}>
          {lead}
        </Reveal>
      )}
    </div>
  );
}
