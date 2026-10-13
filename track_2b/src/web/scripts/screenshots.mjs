// Visual QA: screenshots of every page at desktop (1440x900) and mobile (390x844).
// Usage: node scripts/screenshots.mjs [baseUrl] [--only=landing,workspace] [--tag=suffix]
import { chromium } from "@playwright/test";
import { mkdirSync } from "node:fs";

const args = process.argv.slice(2);
const base = (args.find((a) => !a.startsWith("--")) ?? "http://localhost:3000").replace(/\/$/, "");
const only = (args.find((a) => a.startsWith("--only=")) ?? "").slice(7).split(",").filter(Boolean);
const tag = (args.find((a) => a.startsWith("--tag=")) ?? "").slice(6);
const query = (args.find((a) => a.startsWith("--query=")) ?? "").slice(8); // e.g. data=mock for the static export
const u = (path, extra = "") => {
  const q = [query, extra].filter(Boolean).join("&");
  return `${base}${path}${q ? `?${q}` : ""}`;
};
const OUT = process.env.SHOTS_OUT ?? "screenshots";
mkdirSync(OUT, { recursive: true });

const VIEWPORTS = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "mobile", width: 390, height: 844 },
];

async function scrollShots(page, name, vp, n) {
  const total = await page.evaluate(() => document.documentElement.scrollHeight);
  for (let i = 0; i < n; i++) {
    const y = Math.round((i / Math.max(1, n - 1)) * Math.max(0, total - vp.height));
    await page.evaluate(async (target) => {
      const start = window.scrollY;
      for (let k = 1; k <= 12; k++) {
        window.scrollTo(0, start + ((target - start) * k) / 12);
        await new Promise((r) => setTimeout(r, 40));
      }
    }, y);
    await page.waitForTimeout(1300);
    await page.screenshot({ path: `${OUT}/${name}-${vp.name}-${String(i).padStart(2, "0")}${tag}.png` });
  }
}

const PAGES = {
  landing: async (page, vp) => {
    await page.goto(u("/"), { waitUntil: "networkidle" });
    await page.waitForTimeout(2200);
    await scrollShots(page, "landing", vp, vp.name === "desktop" ? 9 : 12);
  },
  workspace: async (page, vp) => {
    await page.goto(u("/workspace/"), { waitUntil: "networkidle" });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: `${OUT}/workspace-${vp.name}-00-loaded${tag}.png` });
    // run an explanation if the primary action exists
    if (vp.name === "mobile") {
      await page.getByRole("tab", { name: /Facts/ }).first().click();
      await page.waitForTimeout(500);
      await page.screenshot({ path: `${OUT}/workspace-${vp.name}-00b-facts${tag}.png` });
    }
    const btn = page.getByRole("button", { name: /^Explain in/ });
    if (await btn.count()) {
      await btn.first().click();
      await page.waitForTimeout(6500);
      await page.screenshot({ path: `${OUT}/workspace-${vp.name}-01-explained${tag}.png` });
      const ver = page.getByRole("tab", { name: /Verification/ });
      if (await ver.count()) {
        await ver.first().click();
        await page.waitForTimeout(1200);
        await page.screenshot({ path: `${OUT}/workspace-${vp.name}-02-verification${tag}.png`, fullPage: vp.name === "mobile" });
      }
      const rep = page.getByRole("tab", { name: /Reply/ });
      if (await rep.count()) {
        await rep.first().click();
        await page.waitForTimeout(500);
        const ex = page.getByRole("button", { name: /Use example/ });
        if (await ex.count()) await ex.first().click();
        else await page.locator("#client-msg").fill("I do not agree with this letter. I want to object.");
        const draft = page.getByRole("button", { name: /Draft formal reply/ });
        if (await draft.count()) {
          await draft.first().click();
          await page.waitForTimeout(2600);
        }
        await page.screenshot({ path: `${OUT}/workspace-${vp.name}-03-reply${tag}.png` });
      }
    }
  },
  "workspace-rtl": async (page, vp) => {
    await page.goto(u("/workspace/", "lang=ar"), { waitUntil: "networkidle" });
    await page.waitForTimeout(2500);
    if (vp.name === "mobile") {
      await page.getByRole("tab", { name: /Facts/ }).first().click();
      await page.waitForTimeout(400);
    }
    const btn = page.getByRole("button", { name: /^Explain in/ });
    if (await btn.count()) {
      await btn.first().click();
      await page.waitForTimeout(6500);
    }
    await page.screenshot({ path: `${OUT}/workspace-rtl-${vp.name}${tag}.png` });
  },
  evidence: async (page, vp) => {
    await page.goto(u("/evidence/"), { waitUntil: "networkidle" });
    await page.waitForTimeout(2000);
    await scrollShots(page, "evidence", vp, vp.name === "desktop" ? 4 : 6);
  },
};

const browser = await chromium.launch();
const errors = [];
for (const vp of VIEWPORTS) {
  for (const [name, run] of Object.entries(PAGES)) {
    if (only.length && !only.includes(name)) continue;
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 1, isMobile: vp.name === "mobile", hasTouch: vp.name === "mobile" });
    const page = await ctx.newPage();
    page.on("console", (m) => m.type() === "error" && errors.push(`[${name}/${vp.name}] ${m.text()}`));
    page.on("pageerror", (e) => errors.push(`[${name}/${vp.name}] pageerror ${e.message}`));
    page.on("requestfailed", (r) => !r.url().includes("_rsc=") && errors.push(`[${name}/${vp.name}] requestfailed ${r.url()}`));
    page.on("request", (r) => {
      const u = new URL(r.url());
      if (!["localhost", "127.0.0.1"].includes(u.hostname) && !u.protocol.startsWith("data")) errors.push(`[${name}/${vp.name}] EXTERNAL REQUEST ${r.url()}`);
    });
    try {
      await run(page, vp);
    } catch (e) {
      errors.push(`[${name}/${vp.name}] script ${e.message}`);
    }
    await ctx.close();
  }
}
await browser.close();
console.log(errors.length ? errors.join("\n") : "no console errors, no external requests");
