"""Sample letters (synthetic dataset in data/letters/: <id>.txt + <id>.json ground truth)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .config import get_settings


@lru_cache(maxsize=2)
def _index(letters_dir: str) -> dict[str, dict]:
    d = Path(letters_dir)
    out: dict[str, dict] = {}
    if not d.exists():
        return out
    for gt_path in sorted(d.glob("*.json")):
        if gt_path.name in {"splits.json", "metadata.json"}:
            continue
        try:
            gt = json.loads(gt_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        txt = gt_path.with_suffix(".txt")
        if "id" not in gt or not txt.exists():
            continue
        out[gt["id"]] = {"meta": gt, "path": str(txt)}
    return out


def list_samples() -> list[dict]:
    idx = _index(str(get_settings().letters_dir))
    return [
        {
            "id": sid,
            "title": e["meta"].get("title"),
            "language": e["meta"].get("lang"),
            "type": e["meta"].get("letter_type"),
            "split": e["meta"].get("split"),
            "authority": e["meta"].get("authority"),
        }
        for sid, e in idx.items()
    ]


def get_sample(sample_id: str) -> dict | None:
    e = _index(str(get_settings().letters_dir)).get(sample_id)
    if not e:
        return None
    return {**e["meta"], "text": Path(e["path"]).read_text(encoding="utf-8")}
