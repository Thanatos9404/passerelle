import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const EM_DASH = "—";

/** Format a number or return an em dash when it is missing. Never invent a value. */
export function fmtNum(v: number | null | undefined, digits = 1, suffix = ""): string {
  if (v === null || v === undefined || Number.isNaN(v)) return EM_DASH;
  return `${v.toLocaleString("en-CH", { minimumFractionDigits: digits, maximumFractionDigits: digits })}${suffix}`;
}

export function fmtPct(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return EM_DASH;
  // accept 0..1 or 0..100
  const pct = v <= 1 ? v * 100 : v;
  return `${pct.toFixed(digits)}%`;
}

/** Swiss money format: CHF 1'248.60 */
export function fmtChf(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return EM_DASH;
  const [i, d] = Math.abs(v).toFixed(2).split(".");
  const grouped = i.replace(/\B(?=(\d{3})+(?!\d))/g, "’");
  return `${v < 0 ? "-" : ""}CHF ${grouped}.${d}`;
}

/** 0.42 -> "420 ms", 12.3 -> "12.3 s" */
export function fmtSec(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return EM_DASH;
  return v < 1 ? `${Math.round(v * 1000)} ms` : `${v.toFixed(1)} s`;
}

export function sleep(ms: number, signal?: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    const t = setTimeout(resolve, ms);
    signal?.addEventListener("abort", () => {
      clearTimeout(t);
      reject(new DOMException("Aborted", "AbortError"));
    });
  });
}
