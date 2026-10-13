import { Reveal, SectionHead } from "@/components/motion/primitives";
import { MOCK_LANGUAGES } from "@/lib/api/mock";
import { cn } from "@/lib/utils";

// Names and scripts only — quality tiers come from the evaluation, shown in the workspace and /evidence.
const LANGS = MOCK_LANGUAGES.map(({ code, name, native_name, script, rtl }) => ({ code, name, native_name, script, rtl }));

export function LanguagesSection() {
  return (
    <section id="languages" className="scroll-mt-24 bg-sand-2 py-24 md:py-36">
      <div className="container-x">
        <SectionHead
          eyebrow="Languages"
          title="Speaks the languages"
          muted="people actually read."
          lead="Apertus was trained on more than a thousand languages, including low-resource ones that commercial tools treat as an afterthought. Quality still differs per language — so the gate is calibrated per language, and says so."
        />
        <ul className="mt-14 grid grid-cols-2 gap-3 sm:grid-cols-3 md:mt-20 lg:grid-cols-4">
          {LANGS.map((l, i) => (
            <Reveal as="li" key={l.code} delay={(i % 4) * 0.05}>
              <div className="group flex h-full flex-col justify-between rounded-3xl bg-white p-5 shadow-[0_1px_2px_rgba(97,74,68,.05)] ring-1 ring-line transition-[transform,box-shadow] duration-500 ease-[cubic-bezier(.22,1,.36,1)] hover:-translate-y-1 hover:shadow-soft md:p-6">
                <p
                  lang={l.code === "prs" ? "fa-AF" : l.code}
                  dir={l.rtl ? "rtl" : "ltr"}
                  className={cn("text-[28px] leading-tight font-semibold tracking-[-0.02em] text-ink md:text-[34px]", l.rtl && "text-right")}
                >
                  {l.native_name}
                </p>
                <div className="mt-6 flex items-end justify-between gap-2">
                  <div>
                    <p className="text-[15px] font-semibold tracking-[-0.01em] text-ink">{l.name}</p>
                    <p className="text-[13px] text-muted">{l.script} script</p>
                  </div>
                  {l.rtl && <span className="rounded-pill bg-sand-2 px-2 py-0.5 text-[11.5px] font-semibold text-brown">RTL</span>}
                </div>
              </div>
            </Reveal>
          ))}
        </ul>
        <p className="mx-auto mt-10 max-w-[680px] text-center text-[14px] leading-relaxed text-muted">
          Ge&apos;ez, Tamil and Arabic-script fonts are bundled with the app (Noto, SIL OFL) — nothing is fetched from a font CDN, so it renders the same on an air-gapped laptop.
        </p>
      </div>
    </section>
  );
}
