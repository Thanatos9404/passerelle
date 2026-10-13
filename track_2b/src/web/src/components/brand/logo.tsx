import { cn } from "@/lib/utils";

/** Passerelle mark: a footbridge (arch + deck + hangers) — two banks, one crossing. */
export function LogoMark({ className, inverted = false }: { className?: string; inverted?: boolean }) {
  const fg = inverted ? "#1A1615" : "#FFFFFF";
  return (
    <svg viewBox="0 0 32 32" className={cn("size-8", className)} aria-hidden>
      <rect width="32" height="32" rx="10" fill={inverted ? "#FFFFFF" : "#1A1615"} />
      <path d="M7.2 20.4C10.6 13.4 21.4 13.4 24.8 20.4" stroke={fg} strokeWidth="2.3" fill="none" strokeLinecap="round" />
      <path d="M5.6 21.2H26.4" stroke={fg} strokeWidth="2.3" strokeLinecap="round" />
      <path d="M12 16.6V21M16 15V21M20 16.6V21" stroke={fg} strokeWidth="1.5" strokeLinecap="round" opacity="0.72" />
    </svg>
  );
}

export function Logo({ className, inverted }: { className?: string; inverted?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark inverted={inverted} />
      <span className={cn("text-[20px] font-semibold tracking-[-0.045em]", inverted ? "text-white" : "text-ink")}>passerelle</span>
    </span>
  );
}
