"""Append-only, hash-chained audit log that stores hashes — never content.

Each line is a JSON object::

    {"seq": 12, "ts": "2026-10-13T10:00:00+00:00", "event": "explain", "analysis_id": "…",
     "hashes": {"letter": "sha256:…", "output": "sha256:…"}, "meta": {"target_lang": "ti", "gate": "review"},
     "prev": "sha256:…", "hash": "sha256:…"}

``hash`` covers every other field including ``prev``, so deleting or editing a line
breaks the chain (``verify()``).  ``meta`` may only hold short scalars (codes, counts,
timings, statuses) — enforced by :func:`_safe_meta`.
"""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

GENESIS = "sha256:" + "0" * 64


def sha256(text: str | bytes) -> str:
    if isinstance(text, str):
        text = text.encode("utf-8")
    return "sha256:" + hashlib.sha256(text).hexdigest()


def _safe_meta(meta: dict | None) -> dict:
    out = {}
    for k, v in (meta or {}).items():
        if isinstance(v, bool) or v is None or isinstance(v, (int, float)):
            out[k] = v
        elif isinstance(v, str) and len(v) <= 40 and "\n" not in v:
            out[k] = v
        elif isinstance(v, (list, tuple)) and all(isinstance(x, str) and len(x) <= 12 for x in v) and len(v) <= 40:
            out[k] = list(v)
        # anything else (free text, nested content) is dropped on purpose
    return out


class AuditLog:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()
        self._last_hash = GENESIS
        self._seq = 0
        self._loaded = False

    def _load_tail(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self.path.exists():
            return
        last = None
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    last = line
        if last:
            entry = json.loads(last)
            self._last_hash = entry["hash"]
            self._seq = entry["seq"]

    def record(self, event: str, *, analysis_id: str | None = None,
               inputs: dict[str, str] | None = None, meta: dict | None = None) -> dict:
        with self._lock:
            self._load_tail()
            self._seq += 1
            entry = {
                "seq": self._seq,
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "event": event,
                "analysis_id": analysis_id,
                "hashes": {k: sha256(v) for k, v in (inputs or {}).items() if v is not None},
                "meta": _safe_meta(meta),
                "prev": self._last_hash,
            }
            entry["hash"] = sha256(json.dumps(entry, sort_keys=True, ensure_ascii=False))
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
            self._last_hash = entry["hash"]
            return entry

    def recent(self, n: int = 50) -> list[dict]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as fh:
            lines = [ln for ln in fh if ln.strip()]
        return [json.loads(ln) for ln in lines[-n:]][::-1]

    def verify(self) -> dict:
        if not self.path.exists():
            return {"ok": True, "entries": 0}
        prev = GENESIS
        n = 0
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                entry = json.loads(line)
                n += 1
                claimed = entry.pop("hash")
                if entry["prev"] != prev or sha256(json.dumps(entry, sort_keys=True, ensure_ascii=False)) != claimed:
                    return {"ok": False, "entries": n, "first_bad_seq": entry.get("seq")}
                prev = claimed
        return {"ok": True, "entries": n}


_log: AuditLog | None = None
_log_lock = threading.Lock()


def get_audit_log() -> AuditLog:
    global _log
    from .config import get_settings

    path = get_settings().audit_path
    with _log_lock:
        if _log is None or _log.path != path:
            _log = AuditLog(path)
        return _log
