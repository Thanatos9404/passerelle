"""Integrity of the synthetic letter dataset (data/letters)."""

import json
from collections import Counter
from pathlib import Path

from eval.letter_templates import LETTER_TYPES
from eval.metrics import fact_preserved

D = Path(__file__).resolve().parents[1] / "data" / "letters"


def _gts():
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(D.glob("*_[0-9].json"))]


def test_size_and_coverage():
    gts = _gts()
    assert len(gts) >= 36
    combos = Counter((g["letter_type"], g["lang"]) for g in gts)
    assert len(LETTER_TYPES) == 12
    assert all(combos[(t, lang)] >= 1 for t in LETTER_TYPES for lang in ("de", "fr", "it"))


def test_splits_disjoint_and_dev_balanced():
    gts = _gts()
    splits = json.loads((D / "splits.json").read_text(encoding="utf-8"))
    assert not set(splits["dev"]) & set(splits["test"])
    assert set(splits["explain_subset"]) <= set(splits["test"])
    dev = [g for g in gts if g["split"] == "dev"]
    assert len({g["letter_type"] for g in dev}) == 12
    assert Counter(g["lang"] for g in dev) == {"de": 4, "fr": 4, "it": 4}


def test_ground_truth_spans_match_text():
    for g in _gts():
        text = (D / f"{g['id']}.txt").read_text(encoding="utf-8")
        for f in g["facts"]:
            for s, e in f["spans"]:
                assert text[s:e] == f["value"], (g["id"], f)
            assert fact_preserved(f, text, g["lang"], g["lang"]) or f["type"] in {"address", "legal", "url"}


def test_licence_and_synthetic_flags():
    for g in _gts():
        assert g["license"] == "CDLA-Permissive-2.0" and g["synthetic"] is True


def test_dataset_is_small():
    total = sum(p.stat().st_size for p in (D.parent).rglob("*") if p.is_file())
    assert total < 100 * 1024 * 1024
