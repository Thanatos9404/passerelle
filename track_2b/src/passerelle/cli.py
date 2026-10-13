"""Command line: ``passerelle serve | analyze | explain | audit-verify``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _read(path: str) -> str:
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        from .ingest import pdf_to_text

        return pdf_to_text(p.read_bytes())
    return p.read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="passerelle", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sv = sub.add_parser("serve", help="run the API + static UI")
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--port", type=int, default=8080)
    an = sub.add_parser("analyze", help="extract the fact card of a letter (txt or pdf)")
    an.add_argument("file")
    an.add_argument("--no-llm", action="store_true")
    ex = sub.add_parser("explain", help="explain a letter in a target language")
    ex.add_argument("file")
    ex.add_argument("--to", required=True, help="target language code, e.g. ti, ar, prs, uk")
    sub.add_parser("audit-verify", help="verify the hash chain of the audit log")
    args = ap.parse_args(argv)

    if args.cmd == "serve":
        import uvicorn

        from .api import create_app

        uvicorn.run(create_app(), host=args.host, port=args.port, log_level="info")
        return 0
    if args.cmd == "audit-verify":
        from .audit import get_audit_log

        print(json.dumps(get_audit_log().verify(), indent=2))
        return 0

    from .explain import explain
    from .extract import analyze
    from .llm import LLMClient

    client = LLMClient()
    a = analyze(_read(args.file), client=None if getattr(args, "no_llm", False) else client,
                use_llm=not getattr(args, "no_llm", False))
    if args.cmd == "analyze":
        json.dump(a.to_api(), sys.stdout, ensure_ascii=False, indent=2)
        print()
        return 0
    res = explain(a, args.to, client)
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    print(res["explanation"])
    print("\n---")
    print(json.dumps({k: res[k] for k in ("chrf", "gate", "placeholder_audit", "timings", "tokens")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
