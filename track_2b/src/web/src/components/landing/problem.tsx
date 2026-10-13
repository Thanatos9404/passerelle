import { Reveal, SectionHead } from "@/components/motion/primitives";

const CARDS = [
  {
    big: "10 days",
    title: "to object to a payment order",
    body: "After a Zahlungsbefehl is delivered, the recipient has ten days to file an objection (Rechtsvorschlag). If the deadline passes unread, debt enforcement simply continues.",
    source: "Swiss Debt Enforcement and Bankruptcy Act (SchKG/LP), Art. 74",
  },
  {
    big: "DE · FR · IT",
    title: "the languages letters arrive in",
    body: "German, French and Italian are official languages of the Confederation, and each canton sets its own. Letters follow the authority's language — rarely the language the recipient reads.",
    source: "Federal Constitution of the Swiss Confederation, Art. 70",
  },
  {
    big: "Sensitive",
    title: "personal data, by law",
    body: "Data on health, social-assistance measures and administrative proceedings is sensitive personal data. Pasting a client's letter into a public cloud chatbot is not an option.",
    source: "Federal Act on Data Protection (FADP, in force 1 Sep 2023), Art. 5 lit. c",
  },
];

export function Problem() {
  return (
    <section id="problem" className="bg-paper pt-16 pb-24 md:pt-24 md:pb-36">
      <div className="container-x">
        <SectionHead
          eyebrow="The problem"
          title="A letter only works"
          muted="if it is understood."
          lead="Official letters carry deadlines, amounts and consequences. For people who do not read German, French or Italian, one misread date can cost a benefit, a permit or trigger debt enforcement — and professional interpreters are not always available when the letter arrives."
        />
        <div className="mt-14 grid grid-cols-1 gap-4 md:mt-20 md:grid-cols-3 md:gap-5">
          {CARDS.map((c, i) => (
            <Reveal key={c.big} delay={i * 0.08} className="flex h-full flex-col rounded-4xl bg-sand p-7 md:p-8">
              <p className="t-num text-[44px] leading-none font-semibold tracking-[-0.045em] text-ink md:text-[52px]">{c.big}</p>
              <p className="mt-2 text-[17px] font-semibold tracking-[-0.02em] text-ink">{c.title}</p>
              <p className="mt-4 text-[15.5px] leading-relaxed text-body">{c.body}</p>
              <p className="mt-auto pt-6 text-[12.5px] leading-snug text-muted">Source: {c.source}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
