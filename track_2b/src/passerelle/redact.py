"""One-click redaction for exports: names, addresses, AHV/AVS numbers, IBANs, phones, e-mails, birth dates.

Names are found from titles/salutations (Herr/Frau/Monsieur/Madame/Signor/Signora/…, also when the title
stands alone on the line above the name in an address block); every later occurrence of a found surname
is redacted too.  Rule-based by design (auditable, no model call); it will miss names without any cue.
"""

from __future__ import annotations

import re

from .facts import Fact, extract_facts

_TITLE = r"(?:Herrn|Herr|Frau|Hr\.|Fr\.|Familie|Monsieur|Madame|Mme|M\.|Mlle|Famille|Signora|Signor|Sig\.ra|Sig\.|Famiglia|Dr\.|Prof\.)"
_NAME = r"[A-ZÄÖÜÉÈÀ][\wäöüéèàçâêîôû'’\-]+"
RE_TITLED = re.compile(_TITLE + r"[ \t]+((?:" + _NAME + r")(?:[ \t]+" + _NAME + r"){0,2})")
RE_TITLE_LINE = re.compile(r"(?m)^[ \t]*" + _TITLE + r"[ \t]*\n[ \t]*((?:" + _NAME + r")(?:[ \t]+" + _NAME + r"){0,3})[ \t]*$")
RE_BIRTH = re.compile(
    r"(?:geboren am|geb\.|Geburtsdatum:?|né(?:e)? le|date de naissance:?|nato il|nata il|data di nascita:?)\s*"
    r"(\d{1,2}\.\s?\d{1,2}\.\s?\d{2,4}|\d{1,2}\.?\s+\w+\s+\d{4})",
    re.IGNORECASE,
)
_NOT_NAMES = {"Sehr", "Geehrte", "Geehrter", "Damen", "Herren", "Mesdames", "Messieurs", "Gentile", "Egregio", "Egregi",
              "Signore", "Signori", "Bitte", "Die", "Der", "Das"}

ALL_KINDS = ("name", "address", "ahv", "iban", "phone", "email", "birthdate")
_FACT_KIND = {"address": "address", "ahv": "ahv", "iban": "iban", "phone": "phone", "email": "email"}
_LABEL = {"name": "[NAME]", "address": "[ADDRESS]", "ahv": "[AHV]", "iban": "[IBAN]", "phone": "[PHONE]",
          "email": "[EMAIL]", "birthdate": "[DATE OF BIRTH]"}


def redact(text: str, facts: list[Fact] | None = None, kinds: tuple[str, ...] | list[str] = ALL_KINDS) -> dict:
    kinds = tuple(k for k in kinds if k in ALL_KINDS)
    facts = facts if facts is not None else extract_facts(text)
    spans: list[tuple[int, int, str]] = []
    for f in facts:
        kind = _FACT_KIND.get(f.type)
        if kind in kinds:
            for s, e in f.spans or [f.span]:
                spans.append((s, e, kind))
    if "birthdate" in kinds:
        for m in RE_BIRTH.finditer(text):
            spans.append((m.start(1), m.end(1), "birthdate"))
    if "name" in kinds:
        surnames: set[str] = set()
        for rx in (RE_TITLED, RE_TITLE_LINE):
            for m in rx.finditer(text):
                words = [w for w in m.group(1).split() if w not in _NOT_NAMES]
                if not words:
                    continue
                start = m.start(1) + m.group(1).find(words[0])
                spans.append((start, m.end(1), "name"))
                surnames.update(w for w in words if len(w) > 2)
        for name in surnames:
            for m in re.finditer(r"(?<![\w])" + re.escape(name) + r"(?![\w])", text):
                spans.append((m.start(), m.end(), "name"))
    # merge overlapping spans (first come wins by start, longest first)
    spans.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    merged: list[tuple[int, int, str]] = []
    for s, e, k in spans:
        if merged and s < merged[-1][1]:
            ps, pe, pk = merged[-1]
            merged[-1] = (ps, max(pe, e), pk)
            continue
        merged.append((s, e, k))
    out, pos = [], 0
    counts: dict[str, int] = {}
    for s, e, k in merged:
        out.append(text[pos:s])
        out.append(_LABEL[k])
        counts[k] = counts.get(k, 0) + 1
        pos = e
    out.append(text[pos:])
    return {"redacted": "".join(out), "counts": counts}
