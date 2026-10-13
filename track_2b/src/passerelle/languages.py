"""Target languages: native names, script, direction, prompt hints, eval membership."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Language:
    code: str
    name: str            # English name used in prompts
    native: str
    script: str          # ISO 15924
    rtl: bool = False
    prompt_hint: str = ""  # extra precision for the model ("Modern Standard Arabic", "Ge'ez script", ...)
    eval_group: str = ""   # low_mid | control | "" (not evaluated)

    def to_dict(self) -> dict:
        return asdict(self)


LANGUAGES: dict[str, Language] = {
    lang.code: lang
    for lang in [
        Language("ti", "Tigrinya", "ትግርኛ", "Ethi", prompt_hint="Tigrinya as spoken in Eritrea, written in Ge'ez (Ethiopic) script", eval_group="low_mid"),
        Language("ar", "Arabic", "العربية", "Arab", True, "Modern Standard Arabic, Arabic script", "low_mid"),
        Language("prs", "Dari", "دری", "Arab", True, "Dari (Afghan Persian), Arabic script", "low_mid"),
        Language("uk", "Ukrainian", "Українська", "Cyrl", prompt_hint="Ukrainian, Cyrillic script", eval_group="low_mid"),
        Language("ta", "Tamil", "தமிழ்", "Taml", prompt_hint="Tamil, Tamil script", eval_group="low_mid"),
        Language("tr", "Turkish", "Türkçe", "Latn", eval_group="low_mid"),
        Language("so", "Somali", "Soomaali", "Latn", prompt_hint="Somali, Latin script", eval_group="low_mid"),
        Language("sq", "Albanian", "Shqip", "Latn", eval_group="low_mid"),
        Language("en", "English", "English", "Latn", eval_group="control"),
        Language("pt", "Portuguese", "Português", "Latn", eval_group="control"),
        Language("es", "Spanish", "Español", "Latn", eval_group="control"),
        # Supported in the UI but not part of the evaluation (no measured quality)
        Language("fa", "Persian", "فارسی", "Arab", True, "Persian (Farsi), Arabic script"),
        Language("ps", "Pashto", "پښتو", "Arab", True, "Pashto, Arabic script"),
        Language("ku", "Kurdish (Kurmanji)", "Kurdî", "Latn", prompt_hint="Northern Kurdish (Kurmanji), Latin script"),
        Language("am", "Amharic", "አማርኛ", "Ethi", prompt_hint="Amharic, Ge'ez (Ethiopic) script"),
        Language("ru", "Russian", "Русский", "Cyrl"),
        Language("hi", "Hindi", "हिन्दी", "Deva", prompt_hint="Hindi, Devanagari script"),
        Language("bs", "Bosnian/Croatian/Serbian", "Bosanski/Hrvatski/Srpski", "Latn", prompt_hint="Bosnian, Latin script"),
        Language("de", "German", "Deutsch", "Latn"),
        Language("fr", "French", "Français", "Latn"),
        Language("it", "Italian", "Italiano", "Latn"),
    ]
}

SOURCE_LANGS = ("de", "fr", "it")
EVAL_LANGS = tuple(c for c, lang in LANGUAGES.items() if lang.eval_group in {"low_mid", "control"})


def get_language(code: str) -> Language:
    code = (code or "").strip().lower()
    aliases = {"fa-af": "prs", "dari": "prs", "tir": "ti", "ara": "ar", "ukr": "uk", "tam": "ta",
               "tur": "tr", "som": "so", "sqi": "sq", "alb": "sq", "eng": "en", "por": "pt", "spa": "es",
               "deu": "de", "ger": "de", "fra": "fr", "fre": "fr", "ita": "it", "kmr": "ku"}
    code = aliases.get(code, code)
    if code not in LANGUAGES:
        raise KeyError(f"unsupported language: {code}")
    return LANGUAGES[code]


# ------------------------------------------------------------------ script check

_SCRIPT_PREFIX = {
    "Ethi": ("ETHIOPIC",), "Arab": ("ARABIC",), "Cyrl": ("CYRILLIC",), "Taml": ("TAMIL",),
    "Deva": ("DEVANAGARI",), "Latn": ("LATIN",),
}

_STOPWORDS = {
    "de": "der die das und ist nicht sie ihre wir bitte mit für von bis zu den dem eine sind werden".split(),
    "fr": "le la les et est vous votre nous des du une pour avec au aux dans pas sont jusqu".split(),
    "it": "il lo la le è non lei sua noi per con del della di che entro una gli sono".split(),
    "en": "the and you your to of is must this by if will for with are not".split(),
    "pt": "o os as do da que você para com não um uma até é seu sua".split(),
    "es": "el los las del que usted para con no un una hasta es su".split(),
    "tr": "ve bir bu için ile siz sizin kadar olarak gerekir değil eğer ne veya".split(),
    "so": "waa iyo ku ka in aad uu ee oo waxaad haddii ama kale lagu",
    "sq": "dhe të në një për me ju juaj nga deri nëse është që ka duhet".split(),
    "ku": "û di de ji bi ku ev wê tu we ne".split(),
    "bs": "i u je da se na za od ne su vas vaš".split(),
}
_STOPWORDS["so"] = _STOPWORDS["so"].split()  # type: ignore[union-attr]


def script_ratio(text: str, script: str) -> float:
    """Share of letters in ``text`` belonging to ``script`` (placeholders/facts should be removed first)."""
    prefixes = _SCRIPT_PREFIX.get(script, ())
    total = hit = 0
    for ch in text:
        if not ch.isalpha():
            continue
        total += 1
        try:
            name = unicodedata.name(ch)
        except ValueError:
            continue
        if any(name.startswith(p) for p in prefixes):
            hit += 1
    return hit / total if total else 0.0


def guess_latin_language(text: str, candidates: tuple[str, ...]) -> tuple[str | None, dict[str, float]]:
    words = re.findall(r"[^\W\d_]+", text.lower())
    if not words:
        return None, {}
    scores = {}
    for lang in candidates:
        sw = set(_STOPWORDS.get(lang, []))
        if sw:
            scores[lang] = sum(1 for w in words if w in sw) / len(words)
    if not scores:
        return None, {}
    best = max(scores, key=lambda k: scores[k])
    return (best if scores[best] > 0 else None), scores


def check_output_language(text: str, target: str, source: str) -> dict:
    """Is ``text`` plausibly written in the target language/script?"""
    lang = get_language(target)
    ratio = script_ratio(text, lang.script)
    result = {"expected_script": lang.script, "script_ratio": round(ratio, 3), "ok": True, "detected": None}
    if lang.script != "Latn":
        result["ok"] = ratio >= 0.6
        return result
    # Latin-script target: make sure it is not the source language or English
    candidates = tuple(dict.fromkeys([target, source, "en", "de", "fr", "it"]))
    best, scores = guess_latin_language(text, candidates)
    result["detected"] = best
    if ratio < 0.6:
        result["ok"] = False
    elif best and best != target and target in scores:
        # wrong language only if the competitor clearly dominates
        result["ok"] = scores[best] <= 1.5 * scores.get(target, 0.0) + 0.02
    return result
