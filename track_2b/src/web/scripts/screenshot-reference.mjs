// Captures design-reference screenshots of the primary reference (obliqq.framer.ai)
// at 1440x900 across several scroll positions. Dev-time only; never runs in the app.
// Usage: npm run shots:reference
import { chromium } from "@playwright/test";
import { mkdirSync } from "node:fs";

const OUT = "screenshots/reference";
mkdirSync(OUT, { recursive: true });
const SITES = [
  { name: "obliq", url: "https://obliqq.framer.ai/", positions: 12 },
];

const browser = await chromium.launch();
for (const s of SITES) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  try {
    await page.goto(s.url, { waitUntil: "networkidle", timeout: 60000 });
  } catch (e) {
    console.log("goto warn", s.name, e.message);
  }
  await page.waitForTimeout(3000);
  const total = await page.evaluate(() => document.documentElement.scrollHeight);
  console.log(s.name, "height", total);
  for (let i = 0; i < s.positions; i++) {
    const y = Math.round((i / (s.positions - 1)) * Math.max(0, total - 900));
    await page.evaluate(async (target) => {
      const start = window.scrollY;
      const steps = 14;
      for (let k = 1; k <= steps; k++) {
        window.scrollTo(0, start + ((target - start) * k) / steps);
        await new Promise((r) => setTimeout(r, 50));
      }
    }, y);
    await page.waitForTimeout(1500);
    await page.screenshot({ path: `${OUT}/${s.name}-${String(i).padStart(2, "0")}.png` });
  }
  // computed-style probe of a few key elements for token verification
  const probe = await page.evaluate(() => {
    const pick = (el) => {
      const cs = getComputedStyle(el);
      return { tag: el.tagName, text: (el.textContent || "").trim().slice(0, 40), font: cs.fontFamily.slice(0, 40), size: cs.fontSize, weight: cs.fontWeight, ls: cs.letterSpacing, lh: cs.lineHeight, color: cs.color };
    };
    const hs = [...document.querySelectorAll("h1,h2,h3,p")].slice(0, 30).map(pick);
    return hs;
  });
  console.log(JSON.stringify(probe, null, 0));
  await page.close();
}
await browser.close();
