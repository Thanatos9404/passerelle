"""Fact-lock: replace critical facts by immutable placeholders before generation,
audit the placeholders in the model output, and re-insert verified, locale-safe values.

Placeholders look like ``⟦D1⟧`` (U+27E6 / U+27E7).  The model never sees the digits of a
locked fact, so it cannot mistranslate or hallucinate them; on the way back every
placeholder is replaced by a deterministic rendering of the normalised value
(``15.11.2026``, ``CHF 1'250.50``, ``CH93 0076 2011 6238 5295 7`` …).

Unmasking is tolerant to the bracket variants small models produce (``[D1]``,
``[[D1]]``, ``【D1】``, Arabic-Indic digits ``⟦D١⟧`` …); such repairs are reported.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .facts import Fact, render_fact

OPEN, CLOSE = "⟦", "⟧"
_CANON = re.compile(r"⟦([A-Z])(\d{1,3})⟧")
_OPENERS = "⟦〚【⟨〈‹«<([{"
_CLOSERS = "⟧〛】⟩〉›»>)]}"
# Apertus sometimes re-uses the opening bracket as the closer ("⟦A1⟦"), so openers of the
# double-bracket family are accepted as closers too.
_TOLERANT = re.compile(
    r"(?:\[\[|\{\{|[" + re.escape(_OPENERS) + r"])\s*([A-Z])\s*[-_]?\s*(\d{1,3})\s*(?:\]\]|\}\}|["
    + re.escape(_CLOSERS + "⟦〚【") + r"])"
)


def placeholder(fid: str) -> str:
    return f"{OPEN}{fid}{CLOSE}"


def mask(text: str, facts: list[Fact], only: set[str] | None = None) -> str:
    """Replace every occurrence of every fact (or only ids in ``only``) by its placeholder."""
    spans: list[tuple[int, int, str]] = []
    for f in facts:
        if only is not None and f.id not in only:
            continue
        for s, e in (f.spans or [f.span]):
            spans.append((s, e, f.id))
    spans.sort()
    out, pos = [], 0
    for s, e, fid in spans:
        if s < pos:  # overlapping spans cannot happen after resolution, but be safe
            continue
        out.append(text[pos:s])
        out.append(placeholder(fid))
        pos = e
    out.append(text[pos:])
    return "".join(out)


@dataclass
class PlaceholderHit:
    fid: str
    start: int
    end: int
    canonical: bool


def find_placeholders(text: str, known: set[str] | None = None) -> list[PlaceholderHit]:
    hits = []
    for m in _TOLERANT.finditer(text):
        fid = f"{m.group(1)}{int(m.group(2))}"
        canonical = m.group(0) == placeholder(fid)
        if not canonical and known is not None and fid not in known:
            # a bracketed token that is not one of ours, e.g. "[A4]" paper size; ignore
            continue
        hits.append(PlaceholderHit(fid, m.start(), m.end(), canonical))
    return hits


@dataclass
class PlaceholderAudit:
    missing: list[str] = field(default_factory=list)            # required ids absent
    missing_optional: list[str] = field(default_factory=list)   # non-required ids absent (info)
    duplicated: list[str] = field(default_factory=list)         # ids occurring more than once (info)
    unexpected: list[str] = field(default_factory=list)         # ids not in the mapping
    repaired: list[str] = field(default_factory=list)           # non-canonical bracket forms accepted
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.missing and not self.unexpected

    def to_dict(self) -> dict:
        return {
            "missing": self.missing, "duplicated": self.duplicated, "unexpected": self.unexpected,
            "missing_optional": self.missing_optional, "repaired": self.repaired, "counts": self.counts,
            "ok": self.ok,
        }


def audit(text: str, facts_by_id: dict[str, Fact], required: set[str] | None = None,
          offered: set[str] | None = None) -> PlaceholderAudit:
    """Check placeholders in generated text.

    ``required``: ids that must appear (critical facts).  ``offered``: ids present in the
    model input (defaults to all known ids) — anything else is ``unexpected``.
    """
    known = set(facts_by_id)
    offered = known if offered is None else offered
    required = set() if required is None else required
    hits = find_placeholders(text, known)
    counts: dict[str, int] = {}
    a = PlaceholderAudit()
    for h in hits:
        counts[h.fid] = counts.get(h.fid, 0) + 1
        if not h.canonical and h.fid not in a.repaired:
            a.repaired.append(h.fid)
    a.counts = counts
    a.unexpected = sorted({fid for fid in counts if fid not in offered}, key=_id_key)
    a.missing = sorted([fid for fid in required if fid not in counts], key=_id_key)
    a.missing_optional = sorted([fid for fid in offered - required if fid not in counts], key=_id_key)
    a.duplicated = sorted([fid for fid, n in counts.items() if n > 1 and fid in offered], key=_id_key)
    return a


def _id_key(fid: str) -> tuple[str, int]:
    return (fid[0], int(fid[1:]) if fid[1:].isdigit() else 0)


def unmask(text: str, facts_by_id: dict[str, Fact], mode: str = "render") -> tuple[str, list[dict]]:
    """Replace placeholders by fact values.

    mode="render": locale-safe canonical rendering (used for model output);
    mode="surface": the original surface string (exact round trip of ``mask``).
    Unknown placeholders are left visible so a human notices them.
    Returns the text and the spans of inserted facts (for UI fact chips).
    """
    out, spans, pos = [], [], 0
    cursor = 0
    seen: dict[str, int] = {}
    for h in find_placeholders(text, set(facts_by_id)):
        f = facts_by_id.get(h.fid)
        if f is None:
            continue
        out.append(text[pos:h.start])
        cursor += h.start - pos
        if mode == "surface":
            k = seen.get(f.id, 0)
            seen[f.id] = k + 1
            surfaces = f.meta.get("surfaces") or [f.value]
            value = surfaces[k] if k < len(surfaces) else f.value
        else:
            value = render_fact(f)
        spans.append({"id": f.id, "type": f.type, "start": cursor, "end": cursor + len(value), "value": value})
        out.append(value)
        cursor += len(value)
        pos = h.end
    out.append(text[pos:])
    return "".join(out), spans


def strip_placeholders(text: str) -> str:
    """Remove placeholders (for chrF on language only)."""
    return re.sub(r"\s{2,}", " ", _TOLERANT.sub(" ", text)).strip()


class StreamUnmasker:
    """Incrementally unmask a token stream.

    Always holds back the last ``_MAX_HOLD`` characters (longer than any placeholder) and never cuts
    inside a complete placeholder, so a placeholder split across deltas is unmasked exactly like in
    the batch path.
    """

    _MAX_HOLD = 14

    def __init__(self, facts_by_id: dict[str, Fact]):
        self.facts = facts_by_id
        self.buf = ""

    def feed(self, delta: str) -> str:
        self.buf += delta
        cut = len(self.buf) - self._MAX_HOLD
        if cut <= 0:
            return ""
        for m in _TOLERANT.finditer(self.buf):
            if m.start() < cut < m.end():
                cut = m.start()
                break
        ready, self.buf = self.buf[:cut], self.buf[cut:]
        return unmask(ready, self.facts)[0]

    def flush(self) -> str:
        ready, self.buf = self.buf, ""
        return unmask(ready, self.facts)[0]
