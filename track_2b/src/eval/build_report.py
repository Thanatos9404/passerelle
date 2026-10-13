"""Render technical_report.md -> <TEAM_NAME>_Report.pdf (A4) with headless Chrome/Chromium, then check length.

    python -m eval.build_report [--team TEAM_NAME]

The 6-page limit excludes references: the script reports the total page count and the page on which the
"References" section starts (content before it must fit in 6 pages).
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import markdown

from .harness import ROOT

CSS = """
@page { size: A4; margin: 15mm 15mm 15mm 15mm; }
:root { --ink:#1A1615; --body:#453F3D; --muted:#757170; --beige:#F0EAE5; --sand:#F4F1EE; --sky:#9CC1E7; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif; font-size: 9.1pt; line-height: 1.38;
       color: var(--body); margin: 0; }
h1 { font-size: 17pt; color: var(--ink); letter-spacing: -0.02em; margin: 0 0 2mm 0; line-height: 1.15; }
h2 { font-size: 11.6pt; color: var(--ink); letter-spacing: -0.01em; margin: 4.2mm 0 1.4mm 0; padding-top: 1.6mm;
     border-top: 1px solid var(--beige); }
h3 { font-size: 9.8pt; color: var(--ink); margin: 2.6mm 0 1mm 0; }
p { margin: 0 0 1.6mm 0; }
ul, ol { margin: 0 0 1.6mm 0; padding-left: 5mm; }
li { margin: 0 0 0.6mm 0; }
strong { color: var(--ink); }
code { font-family: "Cascadia Mono", Consolas, monospace; font-size: 8.1pt; background: var(--sand);
       padding: 0 1mm; border-radius: 2px; }
pre { background: var(--sand); padding: 2mm 3mm; border-radius: 6px; font-size: 7.6pt; line-height: 1.3;
      white-space: pre-wrap; margin: 0 0 2mm 0; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 1mm 0 2.4mm 0; font-size: 8.2pt; break-inside: avoid; }
th { text-align: left; color: var(--ink); font-weight: 650; border-bottom: 1.2px solid var(--ink); padding: 0.9mm 1.4mm; }
td { border-bottom: 1px solid var(--beige); padding: 0.8mm 1.4mm; vertical-align: top; }
td:not(:first-child), th:not(:first-child) { text-align: right; }
table.left td, table.left th { text-align: left; }
img { max-width: 100%; display: block; margin: 1mm auto 1mm auto; break-inside: avoid; }
img[src*="figures"] { max-width: 74%; }
p:has(> img) { break-inside: avoid; }
em.caption, .caption { display: block; color: var(--muted); font-size: 7.9pt; font-style: normal; margin: 0 0 2.4mm 0; }
blockquote { margin: 0 0 2mm 0; padding: 1.4mm 3mm; background: var(--sand); border-left: 3px solid var(--sky); color: var(--body); }
a { color: var(--ink); text-decoration: none; }
.meta { color: var(--muted); font-size: 8.4pt; margin-bottom: 3mm; }
hr { border: 0; border-top: 1px solid var(--beige); margin: 3mm 0; }
.refs li { font-size: 8.2pt; }
"""


def find_chrome() -> str | None:
    for name in ("chrome", "google-chrome", "chromium", "chromium-browser", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        if os.path.exists(p):
            return p
    return None


def render_html(md_text: str, base: Path) -> str:
    md_text = re.sub(r"\]\((docs/[^)]+)\)", lambda m: f"]({(base / m.group(1)).resolve().as_uri()})", md_text)
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "sane_lists", "attr_list"])
    # "*Figure N: …*" paragraphs directly after an image become captions
    body = re.sub(r"<p><em>((?:Figure|Table) \d+[^<]*)</em></p>", r'<p class="caption">\1</p>', body)
    body = body.replace("<h2>References</h2>", '<h2 id="references">References</h2><div class="refs">')
    if 'class="refs"' in body:
        body += "</div>"
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--team", default=os.environ.get("TEAM_NAME", "StackUnderflow"))
    ap.add_argument("--md", default=str(ROOT / "technical_report.md"))
    args = ap.parse_args(argv)
    md_path = Path(args.md)
    html = render_html(md_path.read_text(encoding="utf-8"), md_path.parent)
    out_pdf = ROOT / f"{args.team}_Report.pdf"
    chrome = find_chrome()
    if not chrome:
        raise SystemExit("Chrome/Chromium not found; install it or open the HTML and print to PDF")
    with tempfile.TemporaryDirectory() as td:
        html_path = Path(td) / "report.html"
        html_path.write_text(html, encoding="utf-8")
        cmd = [chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--hide-scrollbars",
               f"--print-to-pdf={out_pdf}", html_path.resolve().as_uri()]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    from pypdf import PdfReader

    reader = PdfReader(str(out_pdf))
    n = len(reader.pages)
    ref_page = None
    for i, page in enumerate(reader.pages, 1):
        if re.search(r"^\s*References\s*$", page.extract_text() or "", re.M):
            ref_page = i
    content_pages = (ref_page - 1 if ref_page else n)
    print(f"{out_pdf.name}: {n} pages; References start on page {ref_page}; "
          f"content before references fits in {content_pages if ref_page is None else ref_page} page(s) "
          f"(limit 6 excluding references)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
