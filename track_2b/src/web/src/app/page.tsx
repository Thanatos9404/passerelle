import { SiteNav } from "@/components/site/nav";
import { CtaFooter } from "@/components/site/footer";
import { SmoothScroll } from "@/components/motion/smooth-scroll";
import { Hero } from "@/components/landing/hero";
import { BuiltOn } from "@/components/landing/built-on";
import { Problem } from "@/components/landing/problem";
import { HowItWorks } from "@/components/landing/how-it-works";
import { Statement } from "@/components/landing/statement";
import { LanguagesSection } from "@/components/landing/languages";
import { Sovereignty } from "@/components/landing/sovereignty";
import { EvidenceStrip } from "@/components/landing/evidence-strip";

export default function Home() {
  return (
    <>
      <SmoothScroll />
      <SiteNav />
      <main>
        <Hero />
        <BuiltOn />
        <Problem />
        <HowItWorks />
        <Statement />
        <LanguagesSection />
        <Sovereignty />
        <EvidenceStrip />
      </main>
      <CtaFooter />
    </>
  );
}
