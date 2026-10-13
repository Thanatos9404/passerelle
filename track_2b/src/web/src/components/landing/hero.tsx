"use client";

import * as React from "react";
import { motion, useReducedMotion, useScroll, useSpring, useTransform } from "motion/react";
import { ButtonLink } from "@/components/ui/button";
import { Magnetic, WordReveal, EASE } from "@/components/motion/primitives";
import { GrainShader } from "@/components/motion/grain-shader";
import { ProductMockupCanvas, ProductMockupMobile } from "./mockup";

/** Drifting cloud cut-out (keyed from a real sky photo). */
function Cloud({ src, className, flip, drift = 24, dur = 26 }: { src: string; className: string; flip?: boolean; drift?: number; dur?: number }) {
  const reduce = useReducedMotion();
  return (
    <motion.img
      src={src}
      alt=""
      aria-hidden
      draggable={false}
      className={className}
      style={{ scaleX: flip ? -1 : 1 }}
      animate={reduce ? undefined : { x: [0, drift, 0] }}
      transition={{ duration: dur, repeat: Infinity, ease: "easeInOut" }}
    />
  );
}

export function Hero() {
  const ref = React.useRef<HTMLElement>(null);
  const reduce = useReducedMotion();
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
  const p = useSpring(scrollYProgress, { stiffness: 120, damping: 26, mass: 0.4 });

  // parallax depths: photo slow, near clouds fast, far clouds medium
  const photoY = useTransform(p, [0, 1], ["0%", "18%"]);
  const farY = useTransform(p, [0, 1], ["0%", "-30%"]);
  const nearY = useTransform(p, [0, 1], ["0%", "-80%"]);
  const copyY = useTransform(p, [0, 0.5], [0, -60]);
  const copyOpacity = useTransform(p, [0, 0.42], [1, 0]);
  // mockup rises and un-tilts into place
  const rotateX = useTransform(p, [0, 0.38], [22, 0]);
  const scale = useTransform(p, [0, 0.38], [0.9, 1]);
  const mockY = useTransform(p, [0, 0.38], [40, -40]);

  return (
    <section ref={ref} className="relative isolate overflow-hidden" aria-labelledby="hero-title">
      {/* sky: real photo (Lake Brienz, Pexels) washed toward OBLIQ's pale blue and faded into warm sand */}
      <div className="absolute inset-0 -z-10">
        <motion.div className="absolute inset-x-0 -top-[4%] h-[112%]" style={reduce ? undefined : { y: photoY }}>
          <picture>
            <source media="(max-width: 767px)" srcSet="/photos/alpine-lake-1280.webp" />
            <img
              src="/photos/alpine-lake-2400.webp"
              alt=""
              aria-hidden
              className="h-full w-full object-cover object-[50%_42%] [filter:saturate(.72)_brightness(1.1)_contrast(.9)]"
              fetchPriority="high"
            />
          </picture>
        </motion.div>
        <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(156,193,231,.58)_0%,rgba(178,206,236,.42)_30%,rgba(214,226,238,.18)_50%,rgba(237,223,208,0)_58%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_52%_36%_at_50%_30%,rgba(255,255,255,.42),transparent_70%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(180deg,transparent_52%,rgba(237,223,208,.78)_70%,#F4F1EE_86%)]" />
        <motion.div className="absolute inset-0" style={reduce ? undefined : { y: farY }}>
          <Cloud src="/photos/cloud-b.webp" className="absolute top-[13%] -left-[9%] w-[36vw] max-w-[560px] min-w-[260px] opacity-90" drift={30} dur={32} />
          <Cloud src="/photos/cloud-b.webp" className="absolute top-[9%] -right-[8%] w-[34vw] max-w-[520px] min-w-[240px] opacity-90" flip drift={-26} dur={36} />
        </motion.div>
        <motion.div className="absolute inset-0" style={reduce ? undefined : { y: nearY }}>
          <Cloud src="/photos/cloud-a.webp" className="absolute top-[30%] -left-[16%] w-[34vw] max-w-[540px] min-w-[240px] opacity-95" drift={18} dur={22} />
          <Cloud src="/photos/cloud-a.webp" className="absolute top-[34%] -right-[15%] w-[32vw] max-w-[520px] min-w-[220px]" flip drift={-20} dur={24} />
        </motion.div>
        <GrainShader opacity={0.16} />
      </div>

      <div className="container-x relative flex flex-col items-center pt-[112px] text-center md:pt-[132px]">
        <motion.div style={reduce ? undefined : { y: copyY, opacity: copyOpacity }} className="flex flex-col items-center">
          <motion.p
            initial={reduce ? false : { opacity: 0, y: 10, filter: "blur(6px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            transition={{ duration: 0.8, ease: EASE }}
            className="frost mb-6 inline-flex items-center gap-2 rounded-pill border border-white/70 px-3.5 py-1.5 text-[13px] font-medium text-ink shadow-[0_1px_2px_rgba(97,74,68,.08)]"
          >
            <span className="size-1.5 rounded-full bg-ok" aria-hidden />
            Built on Apertus · runs fully air-gapped
          </motion.p>
          <WordReveal
            as="h1"
            onMount
            delay={0.1}
            className="t-display max-w-[1120px] !text-[clamp(38px,5.4vw,78px)]"
            lines={[{ text: "Every letter, understood." }, { text: "In every language." }, { text: "Without leaving the building.", className: "text-ink/45" }]}
          />
          <motion.p
            initial={reduce ? false : { opacity: 0, y: 14, filter: "blur(8px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            transition={{ duration: 0.9, ease: EASE, delay: 0.75 }}
            className="t-lead mt-6 max-w-[660px] text-body"
          >
            Passerelle explains Swiss official letters in the client&apos;s own language. Deadlines and amounts are locked so they cannot be mistranslated, and every explanation is checked before it is handed over.
          </motion.p>
          <motion.div
            initial={reduce ? false : { opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, ease: EASE, delay: 0.9 }}
            className="mt-9 flex flex-wrap items-center justify-center gap-3"
          >
            <Magnetic>
              <ButtonLink href="/workspace/" size="lg" arrow>
                Open workspace
              </ButtonLink>
            </Magnetic>
            <Magnetic>
              <ButtonLink href="/#how" variant="secondary" size="lg">
                See how it works
              </ButtonLink>
            </Magnetic>
          </motion.div>
        </motion.div>

        {/* floating product mockup: rises and un-tilts on scroll */}
        <div className="relative mt-12 w-full max-w-[1180px] text-left [perspective:1800px] md:mt-16">
          <motion.div
            initial={reduce ? false : { opacity: 0, y: 80, filter: "blur(10px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            transition={{ duration: 1.3, ease: EASE, delay: 0.55 }}
          >
            <motion.div
              style={reduce ? undefined : { rotateX, scale, y: mockY, transformOrigin: "50% 0%" }}
              className="rounded-[30px] bg-white/45 p-2 ring-1 ring-white/60 backdrop-blur-sm md:p-2.5"
            >
              <ProductMockupCanvas className="hidden md:block" />
              <ProductMockupMobile className="md:hidden" />
            </motion.div>
          </motion.div>
        </div>
      </div>
      <div className="h-4 md:h-6" />
    </section>
  );
}
