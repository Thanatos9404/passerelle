import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "@fontsource/noto-sans-ethiopic/ethiopic-400.css";
import "@fontsource/noto-sans-ethiopic/ethiopic-600.css";
import "@fontsource/noto-sans-tamil/tamil-400.css";
import "@fontsource/noto-sans-tamil/tamil-600.css";
import "@fontsource/noto-naskh-arabic/arabic-400.css";
import "@fontsource/noto-naskh-arabic/arabic-600.css";
import "./globals.css";
import { TooltipProvider } from "@/components/ui/tooltip";

// Open Runde (SIL OFL 1.1) — self-hosted from github.com/lauridskern/open-runde; no runtime font requests.
const runde = localFont({
  src: [
    { path: "../fonts/OpenRunde-Regular.woff2", weight: "400", style: "normal" },
    { path: "../fonts/OpenRunde-Medium.woff2", weight: "500", style: "normal" },
    { path: "../fonts/OpenRunde-Semibold.woff2", weight: "600", style: "normal" },
  ],
  variable: "--font-runde",
  display: "swap",
  fallback: ["ui-sans-serif", "system-ui", "Segoe UI", "sans-serif"],
});

export const metadata: Metadata = {
  title: { default: "Passerelle — every letter, understood", template: "%s · Passerelle" },
  description:
    "A sovereign, air-gapped caseworker assistant on Apertus that explains Swiss official letters in the client's own language — with locked facts, back-translation checks and a confidence gate.",
  applicationName: "Passerelle",
};

export const viewport: Viewport = {
  themeColor: "#F9F8F8",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={runde.variable}>
      <body>
        <TooltipProvider delayDuration={150}>{children}</TooltipProvider>
      </body>
    </html>
  );
}
