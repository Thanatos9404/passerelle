"""Letter ingestion: text normalisation, PDF text extraction, source-language detection.

OCR is out of scope: scanned letters must arrive as text (or a PDF with a text layer).
Normalisation is character-for-character (except CRLF -> LF) so that fact spans
returned by the API index into the normalised text we hand back to the client.
"""

from __future__ import annotations

import io
import re
import unicodedata

_SPACE_LIKE = {" ": " ", " ": " ", " ": " ", " ": " ", " ": " ", "\t": " "}
_ZERO_WIDTH = re.compile("[​‌‍⁠﻿]")


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _ZERO_WIDTH.sub("", text)
    return "".join(_SPACE_LIKE.get(c, c) for c in text).strip("\n")


def pdf_to_text(data: bytes, max_pages: int = 20) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages = []
    for i, page in enumerate(reader.pages):
        if i >= max_pages:
            break
        pages.append(page.extract_text() or "")
    return normalize_text("\n\n".join(pages))


_STOP = {
    "de": "der die das und ist nicht sie ihre ihr wir bitte mit für von bis zu den dem eine einer einen sich auf werden wird sind haben im am des freundlichen grüssen sehr geehrte".split(),
    "fr": "le la les et est vous votre vos nous des du une un pour avec au aux dans pas par sur ce cette être sont madame monsieur veuillez salutations jusqu".split(),
    "it": "il lo la le e è non lei sua suo noi per con del della dei di che entro una gli alla al nel sono essere egregio gentile signora signor distinti saluti".split(),
}


def detect_language(text: str) -> str:
    """Very small stop-word classifier for the three Swiss official languages."""
    words = re.findall(r"[a-zàâçéèêëîïôûùüÿäöß]+", text.lower())
    scores = {lang: 0 for lang in _STOP}
    sets = {lang: set(ws) for lang, ws in _STOP.items()}
    for w in words:
        for lang, s in sets.items():
            if w in s:
                scores[lang] += 1
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "de"


def to_ascii_digits(text: str) -> str:
    """Map any Unicode decimal digit (Arabic-Indic, Persian, Devanagari, Tamil…) to 0-9."""
    out = []
    for ch in text:
        if ch.isdigit() and not ("0" <= ch <= "9"):
            try:
                out.append(str(unicodedata.digit(ch)))
                continue
            except (TypeError, ValueError):
                pass
        if ch in "٫":  # Arabic decimal separator
            out.append(".")
            continue
        if ch in "٬":  # Arabic thousands separator
            out.append("'")
            continue
        out.append(ch)
    return "".join(out)
