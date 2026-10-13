import type { Metadata } from "next";
import { SiteNav } from "@/components/site/nav";
import { CtaFooter } from "@/components/site/footer";
import { SmoothScroll } from "@/components/motion/smooth-scroll";
import { EvidenceView } from "@/components/evidence/evidence-view";

export const metadata: Metadata = { title: "Evidence" };

export default function EvidencePage() {
  return (
    <>
      <SmoothScroll />
      <SiteNav />
      <main>
        <EvidenceView />
      </main>
      <CtaFooter cta={false} />
    </>
  );
}
