import { Binary, Box, Cpu, FileText, Gauge, Layers, Server, Mountain, Plug } from "lucide-react";

const ITEMS = [
  { icon: Mountain, label: "Apertus v1.5 8B" },
  { icon: Cpu, label: "llama.cpp" },
  { icon: Binary, label: "GGUF · Q4_K_M" },
  { icon: Server, label: "FastAPI" },
  { icon: Gauge, label: "sacreBLEU chrF" },
  { icon: FileText, label: "pypdf" },
  { icon: Layers, label: "Next.js static export" },
  { icon: Box, label: "Docker Compose" },
  { icon: Plug, label: "OpenAI-compatible API" },
];

/** OBLIQ's logo marquee, re-purposed: the open components Passerelle is built on (no customer logos). */
export function BuiltOn() {
  const row = [...ITEMS, ...ITEMS];
  return (
    <section aria-label="Built on open components" className="bg-[linear-gradient(180deg,#F4F1EE_0%,#F4F1EE_60%,#F9F8F8_100%)] pt-6 pb-16 md:pt-8 md:pb-24">
      <p className="text-center text-[15px] text-muted md:text-base">Built entirely on open, inspectable components</p>
      <div className="fade-x mx-auto mt-8 max-w-[1000px] overflow-hidden">
        <ul className="animate-marquee flex w-max items-center gap-12 pr-12 motion-reduce:animate-none">
          {row.map(({ icon: Icon, label }, i) => (
            <li key={i} aria-hidden={i >= ITEMS.length} className="flex items-center gap-2.5 text-[19px] font-semibold tracking-[-0.03em] whitespace-nowrap text-ink/55">
              <Icon className="size-5" strokeWidth={2.2} aria-hidden />
              {label}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
