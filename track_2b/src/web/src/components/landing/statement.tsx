"use client";

import * as React from "react";
import { motion, useReducedMotion, useScroll, useTransform, type MotionValue } from "motion/react";

function Word({ word, i, n, progress, muted }: { word: string; i: number; n: number; progress: MotionValue<number>; muted: boolean }) {
  const start = (i / n) * 0.75;
  const opacity = useTransform(progress, [start, start + 0.18], [0.14, 1]);
  return (
    <motion.span style={{ opacity }} className={muted ? "text-muted" : undefined}>
      {word}{" "}
    </motion.span>
  );
}

/** Replaces OBLIQ's testimonial: a statement of purpose (not a quote), revealed word by word on scroll. */
export function Statement() {
  const ref = React.useRef<HTMLParagraphElement>(null);
  const reduce = useReducedMotion();
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start 85%", "end 45%"] });
  const a = "A misread deadline is not a translation error.".split(" ");
  const b = "It is a lost benefit, a fine, a seizure.".split(" ");
  const all = [...a.map((w) => ({ w, m: false })), ...b.map((w) => ({ w, m: true }))];
  return (
    <section aria-label="Why it matters" className="bg-[linear-gradient(180deg,#F9F8F8,#F4F1EE)] py-24 md:py-36">
      <div className="container-x">
        <p ref={ref} className="mx-auto max-w-[1000px] text-center text-[clamp(32px,4.6vw,60px)] leading-[1.15] font-semibold tracking-[-0.035em] text-ink">
          {reduce
            ? all.map(({ w, m }, i) => (
                <span key={i} className={m ? "text-muted" : undefined}>
                  {w}{" "}
                </span>
              ))
            : all.map(({ w, m }, i) => <Word key={i} word={w} i={i} n={all.length} progress={scrollYProgress} muted={m} />)}
        </p>
        <p className="mx-auto mt-8 max-w-[560px] text-center text-[16px] leading-relaxed text-muted">
          That is why Passerelle never lets the model write a date or an amount — and why it says so when a person should take over.
        </p>
      </div>
    </section>
  );
}
