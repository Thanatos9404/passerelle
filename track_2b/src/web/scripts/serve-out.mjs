// Minimal static server for the exported site (./out), mimicking FastAPI StaticFiles(html=True).
// Usage: node scripts/serve-out.mjs [port]   — /api/* is not served (use ?data=mock to try the UI).
import { createServer } from "node:http";
import { createReadStream, existsSync, statSync } from "node:fs";
import { extname, join, normalize } from "node:path";

const root = new URL("../out/", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
const port = Number(process.argv[2] ?? 4321);
const types = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml", ".webp": "image/webp", ".woff2": "font/woff2", ".txt": "text/plain; charset=utf-8", ".md": "text/markdown; charset=utf-8", ".ico": "image/x-icon", ".png": "image/png" };

createServer((req, res) => {
  const url = new URL(req.url ?? "/", "http://x");
  let p = normalize(join(root, decodeURIComponent(url.pathname)));
  if (!p.startsWith(normalize(root))) return res.writeHead(403).end();
  if (existsSync(p) && statSync(p).isDirectory()) {
    if (!url.pathname.endsWith("/")) return res.writeHead(307, { Location: url.pathname + "/" + url.search }).end();
    p = join(p, "index.html");
  }
  if (!existsSync(p)) {
    res.writeHead(404, { "Content-Type": "text/html; charset=utf-8" });
    return createReadStream(join(root, "404.html")).on("error", () => res.end()).pipe(res);
  }
  res.writeHead(200, { "Content-Type": types[extname(p)] ?? "application/octet-stream" });
  createReadStream(p).on("error", () => res.end()).pipe(res);
}).listen(port, () => console.log(`serving ${root} on http://localhost:${port}`));
