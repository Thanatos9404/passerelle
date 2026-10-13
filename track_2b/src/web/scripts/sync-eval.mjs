// Copies the evaluation summary produced by the eval harness into the static export.
//   track_2b/data/eval_runs/summary.json  ->  public/eval/summary.json
// If no summary exists yet, writes a placeholder with NO numbers (the UI then shows em dashes).
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = resolve(here, "../../../data/eval_runs/summary.json");
const dst = resolve(here, "../public/eval/summary.json");
mkdirSync(dirname(dst), { recursive: true });

if (existsSync(src)) {
  const json = JSON.parse(readFileSync(src, "utf8"));
  writeFileSync(dst, JSON.stringify(json, null, 2));
  console.log(`[sync-eval] copied ${src}`);
} else {
  writeFileSync(
    dst,
    JSON.stringify({ status: "pending", generated_at: null, note: "Placeholder written by scripts/sync-eval.mjs because track_2b/data/eval_runs/summary.json does not exist yet. It contains no results." }, null, 2),
  );
  console.log("[sync-eval] no eval summary yet — wrote placeholder (no numbers)");
}
