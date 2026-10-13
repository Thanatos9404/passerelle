"""Evaluation metrics: fact extraction P/R/F1, fact preservation in explanations, hallucinated numbers,
gate precision/recall.

Fact preservation ("is the fact rendered exactly correctly in the target-language output?") is
checked with the same matcher for the naive baseline and for fact-lock outputs.  A fact counts as
preserved if one *verifiable* rendering appears in the output after digit normalisation
(Arabic-Indic/Persian digits -> 0-9):
  date      DD.MM.YYYY, D.M.YYYY, DD/MM/YYYY, YYYY-MM-DD, the letter's surface form, or day+month+year
            within a 30-character window where the month is a number or a month name in the source
            language, English or the target language (best-effort month tables below)
  amount    the number with any thousands separator (' ’ space none) and . or , decimals ("80", "80.00", "80.–")
  time      HH:MM, H:MM, HH.MM, HHhMM, "H h MM"
  iban/ahv/phone/reference   digit/character sequence ignoring spaces, dots and dashes
  duration  the number of days/weeks/months as a standalone number (or the source number word)
"""

from __future__ import annotations

import re

from passerelle.ingest import to_ascii_digits
from passerelle.verify import unexpected_numbers  # noqa: F401  (re-exported for the harness)

EVAL_TYPES = ("date", "time", "amount", "iban", "ahv", "reference", "phone", "email", "duration")


def key(ftype: str, normalized: str) -> tuple[str, str]:
    if ftype in {"reference", "iban", "ahv"}:
        return ftype, re.sub(r"[\s.\-/]", "", str(normalized)).upper()
    if ftype == "email":
        return ftype, str(normalized).lower()
    return ftype, str(normalized)


def prf(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    f = 2 * p * r / (p + r) if p and r else (0.0 if p is not None and r is not None else None)
    return {"precision": _r(p), "recall": _r(r), "f1": _r(f), "tp": tp, "fp": fp, "fn": fn}


def _r(x):
    return None if x is None else round(x, 4)


def extraction_scores(pred: dict[str, set], gold: dict[str, set]) -> dict:
    """pred/gold: letter_id -> set of (type, key) tuples."""
    by_type = {}
    T = {"tp": 0, "fp": 0, "fn": 0}
    for t in EVAL_TYPES:
        tp = fp = fn = 0
        for lid in gold:
            g = {k for k in gold[lid] if k[0] == t}
            p = {k for k in pred.get(lid, set()) if k[0] == t}
            tp += len(g & p)
            fp += len(p - g)
            fn += len(g - p)
        by_type[t] = prf(tp, fp, fn)
        T["tp"] += tp
        T["fp"] += fp
        T["fn"] += fn
    return {"by_type": by_type, "micro": prf(T["tp"], T["fp"], T["fn"])}


# ------------------------------------------------------------------- fact preservation

MONTH_NAMES: dict[str, list[list[str]]] = {
    "en": [["january", "jan"], ["february", "feb"], ["march", "mar"], ["april", "apr"], ["may"], ["june", "jun"],
           ["july", "jul"], ["august", "aug"], ["september", "sep", "sept"], ["october", "oct"], ["november", "nov"], ["december", "dec"]],
    "de": [["januar"], ["februar"], ["märz"], ["april"], ["mai"], ["juni"], ["juli"], ["august"], ["september"], ["oktober"], ["november"], ["dezember"]],
    "fr": [["janvier"], ["février", "fevrier"], ["mars"], ["avril"], ["mai"], ["juin"], ["juillet"], ["août", "aout"], ["septembre"], ["octobre"], ["novembre"], ["décembre", "decembre"]],
    "it": [["gennaio"], ["febbraio"], ["marzo"], ["aprile"], ["maggio"], ["giugno"], ["luglio"], ["agosto"], ["settembre"], ["ottobre"], ["novembre"], ["dicembre"]],
    "pt": [["janeiro"], ["fevereiro"], ["março", "marco"], ["abril"], ["maio"], ["junho"], ["julho"], ["agosto"], ["setembro"], ["outubro"], ["novembro"], ["dezembro"]],
    "es": [["enero"], ["febrero"], ["marzo"], ["abril"], ["mayo"], ["junio"], ["julio"], ["agosto"], ["septiembre", "setiembre"], ["octubre"], ["noviembre"], ["diciembre"]],
    "tr": [["ocak"], ["şubat", "subat"], ["mart"], ["nisan"], ["mayıs", "mayis"], ["haziran"], ["temmuz"], ["ağustos", "agustos"], ["eylül", "eylul"], ["ekim"], ["kasım", "kasim"], ["aralık", "aralik"]],
    "so": [["janaayo", "jannaayo"], ["febraayo", "febraryo"], ["maarso", "maarij"], ["abriil", "abril"], ["maajo", "may"], ["juun", "juunyo"], ["luuliyo", "julaay"], ["ogosto", "agoosto"], ["sebtembar", "sebteembar"], ["oktoobar", "oktobar"], ["nofembar", "noofembar"], ["desembar", "diseembar"]],
    "sq": [["janar"], ["shkurt"], ["mars"], ["prill"], ["maj"], ["qershor"], ["korrik"], ["gusht"], ["shtator"], ["tetor"], ["nëntor", "nentor"], ["dhjetor"]],
    "uk": [["січня", "січень"], ["лютого", "лютий"], ["березня", "березень"], ["квітня", "квітень"], ["травня", "травень"], ["червня", "червень"],
           ["липня", "липень"], ["серпня", "серпень"], ["вересня", "вересень"], ["жовтня", "жовтень"], ["листопада", "листопад"], ["грудня", "грудень"]],
    "ar": [["يناير", "كانون الثاني"], ["فبراير", "شباط"], ["مارس", "آذار"], ["أبريل", "ابريل", "نيسان"], ["مايو", "أيار"], ["يونيو", "حزيران"],
           ["يوليو", "تموز"], ["أغسطس", "اغسطس", "آب"], ["سبتمبر", "أيلول"], ["أكتوبر", "اكتوبر", "تشرين الأول"], ["نوفمبر", "تشرين الثاني"], ["ديسمبر", "كانون الأول"]],
    "prs": [["جنوری", "ژانویه"], ["فبروری", "فوریه"], ["مارچ", "مارس"], ["اپریل", "آوریل"], ["می", "مه"], ["جون", "ژوئن"],
            ["جولای", "ژوئیه"], ["اگست", "اوت"], ["سپتمبر", "سپتامبر"], ["اکتوبر", "اکتبر"], ["نومبر", "نوامبر"], ["دسمبر", "دسامبر"]],
    "ta": [["ஜனவரி"], ["பிப்ரவரி"], ["மார்ச்"], ["ஏப்ரல்"], ["மே"], ["ஜூன்"], ["ஜூலை"], ["ஆகஸ்ட்"], ["செப்டம்பர்"], ["அக்டோபர்"], ["நவம்பர்"], ["டிசம்பர்"]],
    # Eritrean Tigrinya uses these names for Gregorian months; transliterations also accepted
    "ti": [["ጥሪ", "ጃንዩወሪ"], ["ለካቲት", "ፌብሩወሪ"], ["መጋቢት", "ማርች"], ["ሚያዝያ", "ኤፕሪል"], ["ግንቦት", "ሜይ"], ["ሰነ", "ጁን"],
           ["ሓምለ", "ጁላይ"], ["ነሓሰ", "ኦገስት"], ["መስከረም", "ሴፕቴምበር"], ["ጥቅምቲ", "ኦክቶበር"], ["ሕዳር", "ኖቬምበር"], ["ታሕሳስ", "ዲሴምበር"]],
}


def _norm_text(text: str) -> str:
    return to_ascii_digits(text).replace(" ", " ").replace(" ", " ")


def _amount_rx(normalized: str) -> re.Pattern:
    whole, cents = normalized.split(".")
    groups = []
    w = whole
    while len(w) > 3:
        groups.insert(0, w[-3:])
        w = w[:-3]
    groups.insert(0, w)
    sep = r"[’'ʼ´`\s.,]?"
    whole_rx = sep.join(groups)
    if cents == "00":
        tail = r"(?:[.,](?:00|[-–—]{1,2}))?"
    else:
        tail = r"[.,]" + cents
    return re.compile(r"(?<![\d])" + whole_rx + tail + r"(?![\d])")


def _compact(s: str) -> str:
    return re.sub(r"[\s.\-/’'·]", "", s).upper()


def fact_preserved(fact: dict, output: str, target_lang: str, source_lang: str) -> bool:
    out = _norm_text(output)
    t, n = fact["type"], str(fact["normalized"])
    if t == "date":
        y, m, d = n.split("-")
        di, mi = int(d), int(m)
        variants = [f"{d}.{m}.{y}", f"{di}.{mi}.{y}", f"{d}/{m}/{y}", f"{di}/{mi}/{y}", f"{y}-{m}-{d}",
                    f"{d}.{m}.{y[2:]}", f"{d}-{m}-{y}", fact.get("value", "@@")]
        if any(v and v in out for v in variants):
            return True
        names = []
        for lang in {target_lang, source_lang, "en"}:
            for name in MONTH_NAMES.get(lang, [[]] * 12)[mi - 1]:
                names.append(re.escape(name))
        low = out.lower()
        month_rx = r"(?:" + "|".join(names + [rf"0?{mi}"]) + r")" if names else rf"0?{mi}"
        rx = re.compile(rf"(?<!\d)0?{di}(?!\d)[^\n]{{0,30}}?{month_rx}[^\n]{{0,30}}?{y}|{month_rx}[^\n]{{0,12}}?(?<!\d)0?{di}(?!\d)[^\n]{{0,20}}?{y}")
        return bool(rx.search(low))
    if t == "amount":
        return bool(_amount_rx(n).search(out))
    if t == "time":
        hh, mm = n.split(":")
        h = int(hh)
        rx = re.compile(rf"(?<!\d)0?{h}\s?(?:[:.h]|\s?h\s?)\s?{mm}(?!\d)" if mm != "00" else rf"(?<!\d)0?{h}(?:\s?[:.h]\s?00)?(?!\d)")
        return bool(rx.search(out))
    if t in {"iban", "ahv", "phone", "reference"}:
        target = _compact(n if t != "phone" else "0" + n[3:])
        comp = _compact(out)
        if target in comp:
            return True
        if t == "phone":
            return _compact(n) in comp or _compact("0041" + n[3:]) in comp
        return False
    if t == "email":
        return n.lower() in out.lower()
    if t == "duration":
        num = re.sub(r"\D", "", n)
        if re.search(rf"(?<!\d){num}(?!\d)", out):
            return True
        val = str(fact.get("value", ""))
        return bool(val) and not val.isdigit() and val.lower() in out.lower()
    return fact.get("value", "@@") in out


def preservation(facts: list[dict], output: str, target_lang: str, source_lang: str) -> dict:
    crit = [f for f in facts if f.get("critical") and f["type"] in EVAL_TYPES]
    hits = [fact_preserved(f, output, target_lang, source_lang) for f in crit]
    return {
        "n": len(crit),
        "preserved": sum(hits),
        "rate": round(sum(hits) / len(crit), 4) if crit else None,
        "missed": [f"{f['type']}:{f['normalized']}" for f, h in zip(crit, hits) if not h],
        "by_type": {t: [int(h) for f, h in zip(crit, hits) if f["type"] == t] for t in {f["type"] for f in crit}},
    }
