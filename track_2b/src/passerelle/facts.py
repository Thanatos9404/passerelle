"""Deterministic extractors for critical facts in Swiss official letters (DE/FR/IT).

Every extractor returns *candidates* with a character span, a surface value and a
normalised value.  Overlaps are resolved by priority (IBAN > AHV > e-mail > URL >
labelled reference > phone > amount > date > time > legal ref > duration >
address > generic reference), then identical (type, normalised) facts share one
placeholder id such as ``D1`` / ``A2``.

Normalised forms
  date      ISO ``YYYY-MM-DD``          amount   ``1250.50`` (CHF)
  duration  ISO-8601 ``P30D``/``P2W``/``P1M``    time ``HH:MM``
  iban      compact ``CH9300762011623852957``     ahv  ``756.1234.5678.97``
  phone     E.164 ``+41441234567``    reference / email / url / address / legal: whitespace-normalised surface
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

FACT_TYPES = (
    "date", "duration", "amount", "iban", "ahv", "reference",
    "phone", "time", "email", "url", "address", "legal",
)
PREFIX = {
    "date": "D", "duration": "N", "amount": "A", "iban": "I", "ahv": "S", "reference": "R",
    "phone": "P", "time": "H", "email": "E", "url": "W", "address": "L", "legal": "G",
}
TYPE_BY_PREFIX = {v: k for k, v in PREFIX.items()}

# --------------------------------------------------------------------------- data


@dataclass
class Fact:
    id: str
    type: str
    value: str                     # surface text exactly as in the letter (first occurrence)
    normalized: str
    span: tuple[int, int]          # first occurrence
    spans: list[tuple[int, int]] = field(default_factory=list)
    source: str = "rule"           # rule | llm | both
    critical: bool = False
    role: str | None = None        # letter_date | deadline | appointment | effective | contact | ...
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["span"] = list(self.span)
        d["spans"] = [list(s) for s in self.spans]
        return d


@dataclass
class _Cand:
    type: str
    start: int
    end: int
    value: str
    normalized: str
    priority: int
    meta: dict = field(default_factory=dict)


# ------------------------------------------------------------------ vocabularies

MONTHS: dict[str, int] = {
    # German
    "januar": 1, "jänner": 1, "jan": 1, "februar": 2, "feb": 2, "febr": 2, "märz": 3, "maerz": 3,
    "mär": 3, "mrz": 3, "april": 4, "apr": 4, "mai": 5, "juni": 6, "jun": 6, "juli": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sept": 9, "sep": 9, "oktober": 10, "okt": 10,
    "november": 11, "nov": 11, "dezember": 12, "dez": 12,
    # French
    "janvier": 1, "janv": 1, "février": 2, "fevrier": 2, "févr": 2, "fév": 2, "mars": 3,
    "avril": 4, "avr": 4, "juin": 6, "juillet": 7, "juil": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "oct": 10, "novembre": 11, "décembre": 12, "decembre": 12,
    "déc": 12, "dec": 12,
    # Italian
    "gennaio": 1, "genn": 1, "gen": 1, "febbraio": 2, "febbr": 2, "marzo": 3, "mar": 3,
    "aprile": 4, "maggio": 5, "magg": 5, "mag": 5, "giugno": 6, "giu": 6, "luglio": 7, "lug": 7,
    "agosto": 8, "ago": 8, "settembre": 9, "sett": 9, "set": 9, "ottobre": 10, "ott": 10,
    "dicembre": 12, "dic": 12,
}
_MONTH_ALT = "|".join(sorted((re.escape(m) for m in MONTHS), key=len, reverse=True))

NUMBER_WORDS: dict[str, int] = {
    # German
    "ein": 1, "eine": 1, "einem": 1, "einen": 1, "eines": 1, "zwei": 2, "drei": 3, "vier": 4,
    "fünf": 5, "sechs": 6, "sieben": 7, "acht": 8, "neun": 9, "zehn": 10, "elf": 11, "zwölf": 12,
    "vierzehn": 14, "fünfzehn": 15, "zwanzig": 20, "dreissig": 30, "dreißig": 30, "sechzig": 60,
    "neunzig": 90,
    # French
    "un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7,
    "huit": 8, "neuf": 9, "dix": 10, "onze": 11, "douze": 12, "quatorze": 14, "quinze": 15,
    "vingt": 20, "trente": 30, "soixante": 60, "nonante": 90, "quatre-vingt-dix": 90,
    # Italian
    "uno": 1, "una": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5, "sei": 6, "sette": 7,
    "otto": 8, "nove": 9, "dieci": 10, "undici": 11, "dodici": 12, "quattordici": 14,
    "quindici": 15, "venti": 20, "trenta": 30, "sessanta": 60, "novanta": 90,
}
_NUMWORD_ALT = "|".join(sorted((re.escape(w) for w in NUMBER_WORDS), key=len, reverse=True))

_UNIT_DAY = r"(?:Arbeitstagen|Arbeitstage|Werktagen|Werktage|Kalendertagen|Tagen|Tage|Tag|jours\s+ouvrables|jours|jour|giorni\s+lavorativi|giorni|giorno)"
_UNIT_WEEK = r"(?:Wochen|Woche|semaines|semaine|settimane|settimana)"
_UNIT_MONTH = r"(?:Monaten|Monate|Monats|Monat|mois|mesi|mese)"

DEADLINE_CUES = re.compile(
    r"(?:\bbis\b|spätestens|\bfrist\b|fällig|zahlbar|einzureichen|einreichen|innert|innerhalb|binnen|"
    r"jusqu['’]au|jusqu['’]à|d['’]ici|au plus tard|avant le|délai|échéance|payable|\bdans\b|sous\b|"
    r"entro|al più tardi|scadenza|termine|pagabile|non oltre)",
    re.IGNORECASE,
)
APPOINTMENT_CUES = re.compile(
    r"(?:termin|gespräch|anhörung|vorsprache|vorladung|eingeladen|einladung|erscheinen|"
    r"rendez-vous|entretien|audition|convoqu|invité|présenter|"
    r"appuntamento|colloquio|audizione|convocat|invitat|presentarsi)",
    re.IGNORECASE,
)
_FAX_CUE = re.compile(r"fax\s*:?\s*$", re.IGNORECASE)

# ------------------------------------------------------------------- regexes

_APOS = "'’ʼ´`"
_THOUSANDS = _APOS + "    "
_NUM_AMOUNT = (
    r"(?:\d{1,3}(?:[" + _THOUSANDS + r"]\d{3})+(?![\d])"           # 1'250 / 1 250
    r"|\d{1,3}(?:\.\d{3})+(?=,\d{2}\b)"                              # 1.250 (only with ,50)
    r"|\d+)"
    r"(?:[.,]\d{2}(?!\d)|[.,]\d(?!\d)|\.[-–—]{1,2}|,[-–—]{1,2})?"    # .50 / ,50 / .– / .--
)
_CUR_BEFORE = r"(?:CHF|SFr\.|sFr\.|SFr|Fr\.)"
_CUR_AFTER = r"(?:CHF|Fr\.|Franken|francs?|franchi|franco)(?![\w])"
RE_AMOUNT_BEFORE = re.compile(_CUR_BEFORE + r"\s?(" + _NUM_AMOUNT + r")")
RE_AMOUNT_AFTER = re.compile(r"(?<![\d.,'’])(" + _NUM_AMOUNT + r")\s?" + _CUR_AFTER)

RE_IBAN = re.compile(r"\b((?:CH|LI)\d{2}(?:[  ]?[0-9A-Z]){17})\b")
RE_AHV = re.compile(r"(?<![\d.])(756[.\s]?\d{4}[.\s]?\d{4}[.\s]?\d{2})(?![\d])")
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
RE_URL = re.compile(r"\b(?:https?://|www\.)[^\s<>()\"]+[^\s<>().,;:!?\"]")
RE_PHONE = re.compile(
    r"(?<![\d])(?:"
    r"(?:\+|00)\s?41\s?(?:\(0\)\s?)?\d{2}[\s/]?\d{3}[\s.]?\d{2}[\s.]?\d{2}"
    r"|0(?:800|840|842|844|848|900|901|906)[\s/]?\d{3}[\s.]?\d{3}"
    r"|0\d{2}[\s/]?\d{3}[\s.]?\d{2}[\s.]?\d{2}"
    r")(?![\d])"
)
RE_DATE_NUM = re.compile(r"(?<![\d.])(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{4}|\d{2})(?![\d])")
RE_DATE_SLASH = re.compile(r"(?<![\d/])(\d{1,2})/(\d{1,2})/(\d{4})(?![\d])")
RE_DATE_NUM_NOYEAR = re.compile(r"(?<![\d.])(\d{1,2})\.(\d{1,2})\.(?![\d\s]*\d{2})")
RE_DATE_LONG = re.compile(
    r"(?<![\d])(\d{1,2})(?:\.|er|ᵉʳ|°|º)?\s*(" + _MONTH_ALT + r")(?![a-zäöüéèàû])\.?(?:\s+|\s*,\s*)?(\d{4})?",
    re.IGNORECASE,
)
_H = r"([01]?\d|2[0-3])"
_M = r"([0-5]\d)"
# (regex, lock-group) — the lock group is the part replaced by a placeholder
TIME_PATTERNS = [
    (re.compile(r"(?<![\d.:'’])(" + _H + r"[:.]" + _M + r"\s?(?:Uhr|h|heures|ore)\b)", re.I), 1),   # 14.30 Uhr
    (re.compile(r"(?<![\d.:'’])(" + _H + r":" + _M + r")(?![\d])"), 1),                              # 14:30
    (re.compile(r"(?<![\d.:'’])(" + _H + r"\s?h\s?" + r"([0-5]\d)?)(?![\w])"), 1),                  # 8h30 / 14 h
    (re.compile(r"(?<![\d.:'’])(" + _H + r"\s?Uhr)\b"), 1),                                          # 9 Uhr
    (re.compile(r"\bore\s+(" + _H + r"(?:[.:]" + _M + r")?)(?![\d])", re.I), 1),                     # ore 9.30
    (re.compile(r"\b(?:alle|dalle)\s+(" + _H + r"[.:]" + _M + r")(?![\d])", re.I), 1),               # alle 9.30
    (re.compile(r"(?<![\d.:'’])(" + _H + r"[.:]" + _M + r")\s*(?:bis|–|-)\s*" + _H + r"[.:]" + _M + r"\s?(?:Uhr|h)\b"), 1),  # 8.00 bis 11.30 Uhr
]
RE_DURATION = re.compile(
    r"(?<![\w.,'’])(\d{1,3}|" + _NUMWORD_ALT + r")\s+(" + _UNIT_DAY + "|" + _UNIT_WEEK + "|" + _UNIT_MONTH + r")\b",
    re.IGNORECASE,
)
RE_LEGAL = re.compile(
    r"\b(?:Art\.|art\.|§)\s?\d+[a-z]?(?:\s?(?:Abs\.|al\.|cpv\.|Ziff\.|let\.|lit\.|cifra)\s?\d+[a-z]?)*"
    r"(?:\s(?:[A-Z][A-Za-z]{1,7}(?:/[A-Z]{2,3})?)(?![a-z]))?"
)

_STREET_DE = (
    r"\b((?:[A-ZÄÖÜ][a-zäöüß]+[- ])?[A-ZÄÖÜ][a-zäöüß]*(?:strasse|straße|str\.|weg|gasse|platz|allee|ring|rain|"
    r"quai|matte|halde|steig|stutz|hof|graben|berg|park))\s+(\d{1,4}[a-zA-Z]?)\b"
)
_STREET_ROMANCE = (
    r"\b((?:Rue|Avenue|Av\.|Chemin|Ch\.|Route|Rte|Place|Boulevard|Bd|Quai|Ruelle|Impasse|Allée|Promenade|Sentier|"
    r"Via|Viale|Piazza|Piazzale|Corso|Vicolo|Strada|Largo|Contrada)"
    r"(?:\s+(?:de\s+la|de\s+l['’]|du|des|de|d['’]|della|dello|delle|dei|degli|del|di|San|Santa|St-|Ste-|la|le|les)){0,2}"
    r"(?:\s*[A-ZÉÈÀÂ][\w'’\-éèàêçâîôû]*){1,3})\s+(\d{1,4}[a-zA-Z]?)\b"
)
RE_STREET = re.compile(_STREET_DE + "|" + _STREET_ROMANCE)
RE_POBOX = re.compile(r"\b(?:Postfach|Case postale|Casella postale|CP)\s+\d{1,5}\b")
RE_POSTAL = re.compile(
    r"(?:^|(?<=,)|(?<=CH-))[ \t]*(?:CH-)?([1-9]\d{3})[ \t]+"
    r"([A-ZÄÖÜÉÈ][\wäöüéèàçâêîôû'’.\-]*(?:[ \t]+(?:[A-ZÄÖÜÉÈ][\wäöüéèàçâêîôû'’.\-]*|am|an|bei|im|sur|sous|près|di|de|del|al)){0,3})",
    re.MULTILINE,
)
_LOCALITY_STOP = {"Tel", "Tel.", "Telefon", "Tél", "Tél.", "Téléphone", "Fax", "E-Mail", "Mail", "Internet", "Web", "Mobile", "Natel"}

_REF_LABELS = (
    # German
    r"Referenz(?:nummer)?|Ref\.|Unser Zeichen|Ihr Zeichen|Aktenzeichen|Geschäftsnummer|Geschäfts-Nr\.|"
    r"Dossiernummer|Dossier-Nr\.|Dossier Nr\.|Fallnummer|Fall-Nr\.|Kundennummer|Kunden-Nr\.|Versichertennummer|Versicherten-Nr\.|"
    r"Policennummer|Police-Nr\.|Policen-Nr\.|Betreibungsnummer|Betreibungs-Nr\.|Betreibung Nr\.|Rechnungsnummer|Rechnungs-Nr\.|"
    r"Rechnung Nr\.|Verfügung Nr\.|Verfügungsnummer|Steuernummer|Steuer-Nr\.|Register-Nr\.|Personennummer|Personen-Nr\.|"
    r"N-Nummer|ZEMIS-Nr\.|ZEMIS-Nummer|ZEMIS|Mieternummer|Mieter-Nr\.|Objektnummer|Objekt-Nr\.|Vertragsnummer|Vertrags-Nr\.|"
    r"Bussennummer|Bussen-Nr\.|Busse Nr\.|Mandatsnummer|Mandats-Nr\.|Kontonummer|Konto-Nr\.|QR-Referenz|Zahlungsreferenz|"
    r"Schüler-Nr\.|Antragsnummer|Antrags-Nr\.|Gesuchsnummer|Gesuchs-Nr\.|Abrechnungsnummer|Abrechnungs-Nr\.|"
    # French
    r"Notre référence|Votre référence|Référence de paiement|Référence|Réf\.|N° de dossier|Dossier n°|Dossier no|"
    r"(?:No|N°|Nº|n°|no)\.?\s?(?:de\s|d['’])?(?:dossier|référence|police|assuré|client|contribuable|poursuite|facture|"
    r"décision|contrat|amende|SYMIC|personnel|demande|élève|compte)|Poursuite n°|Facture n°|Décision n°|Amende n°|"
    # Italian
    r"Riferimento(?: di pagamento)?|Rif\.|Numero di riferimento|N\. pratica|Pratica n\.|Pratica N\.|Incarto n\.|N\. incarto|"
    r"(?:N\.|N°|n\.|no\.|Nr\.)\s?(?:pratica|assicurato|polizza|cliente|contribuente|esecuzione|fattura|decisione|"
    r"contratto|multa|SIMIC|riferimento|domanda|allievo|conto)|Esecuzione n\.|Fattura n\.|Decisione n\.|Multa n\."
)
RE_REF_LABELLED = re.compile(
    r"(?i:" + _REF_LABELS + r")\s*[:.]?\s*"
    r"((?:[A-Z0-9][A-Z0-9\-/.]*)(?!\w)(?:[  ](?=[A-Z0-9])[A-Z0-9][A-Z0-9\-/.]*(?!\w)){0,6})",
)
RE_REF_GENERIC = re.compile(r"\b([A-Z]{2,6}[-/]\d{2,4}[-/][A-Z0-9]{2,8}(?:[-/][A-Z0-9]{1,8})*)\b")

PRIORITY = {
    "iban": 100, "ahv": 95, "email": 90, "url": 85, "reference": 80, "phone": 70, "amount": 65,
    "date": 60, "time": 55, "legal": 50, "duration": 45, "address": 40, "reference_generic": 35,
}

# ------------------------------------------------------------- normalisers


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def normalize_amount(num: str) -> str | None:
    """'1'250.50' -> '1250.50', '80.–' -> '80.00', '1 250,50' -> '1250.50'."""
    s = num.strip()
    s = re.sub(r"[.,][-–—]{1,2}$", "", s)
    for ch in _THOUSANDS:
        s = s.replace(ch, "")
    if "," in s and "." in s:          # 1.250,50
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", s):
        s = s.replace(".", "")
    try:
        return f"{Decimal(s):.2f}"
    except InvalidOperation:
        return None


def format_chf(normalized: str) -> str:
    """Locale-safe Swiss rendering: '1250.50' -> "CHF 1'250.50"."""
    d = Decimal(normalized)
    whole, frac = f"{d:.2f}".split(".")
    groups = []
    while len(whole) > 3:
        groups.insert(0, whole[-3:])
        whole = whole[:-3]
    groups.insert(0, whole)
    return "CHF " + "'".join(groups) + "." + frac


def iban_valid(compact: str) -> bool:
    if len(compact) < 15:
        return False
    rearranged = compact[4:] + compact[:4]
    digits = "".join(str(int(c, 36)) for c in rearranged)
    return int(digits) % 97 == 1


def format_iban(compact: str) -> str:
    return " ".join(compact[i:i + 4] for i in range(0, len(compact), 4))


def ahv_valid(digits13: str) -> bool:
    if len(digits13) != 13 or not digits13.isdigit():
        return False
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(digits13[:12]))
    return (10 - total % 10) % 10 == int(digits13[12])


def format_ahv(digits13: str) -> str:
    return f"{digits13[:3]}.{digits13[3:7]}.{digits13[7:11]}.{digits13[11:]}"


def normalize_phone(s: str) -> str | None:
    d = _digits(s.replace("(0)", ""))
    if d.startswith("0041"):
        d = d[4:]
    elif d.startswith("41") and s.strip().startswith("+"):
        d = d[2:]
    elif d.startswith("0"):
        d = d[1:]
    else:
        return None
    if len(d) != 9:
        return None
    return "+41" + d


def format_phone(e164: str) -> str:
    n = "0" + e164[3:]
    if n[:4] in {"0800", "0840", "0842", "0844", "0848", "0900", "0901", "0906"}:
        return f"{n[:4]} {n[4:7]} {n[7:]}"
    return f"{n[:3]} {n[3:6]} {n[6:8]} {n[8:]}"


def _mk_date(d: int, m: int, y: int) -> str | None:
    if y < 100:
        y += 2000
    try:
        return date(y, m, d).isoformat()
    except ValueError:
        return None


def format_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


def parse_date_text(s: str, ref: date | None = None) -> str | None:
    """Parse one date string in any supported format (incl. ISO) -> ISO or None."""
    s = s.strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return _mk_date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    for cand in _extract_dates(s, ref):
        return cand.normalized
    return None


def parse_amount_text(s: str) -> str | None:
    for c in _extract_amounts(s):
        return c.normalized
    m = re.search(_NUM_AMOUNT, s)
    if m:
        return normalize_amount(m.group(0))
    return None


def parse_time_text(s: str) -> str | None:
    for c in _extract_times(s):
        return c.normalized
    m = re.fullmatch(r"\s*([01]?\d|2[0-3])[:.h]([0-5]\d)\s*", s)
    if m:
        return f"{int(m.group(1)):02d}:{m.group(2)}"
    return None


def normalize_reference(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().rstrip(".,;:")).upper()


# --------------------------------------------------------------- extractors


def _extract_amounts(text: str) -> list[_Cand]:
    out = []
    for rx in (RE_AMOUNT_BEFORE, RE_AMOUNT_AFTER):
        for m in rx.finditer(text):
            norm = normalize_amount(m.group(1))
            if norm is None:
                continue
            out.append(_Cand("amount", m.start(), m.end(), m.group(0), norm, PRIORITY["amount"], {"currency": "CHF"}))
    return out


def _extract_dates(text: str, ref: date | None = None) -> list[_Cand]:
    out: list[_Cand] = []
    for rx in (RE_DATE_NUM, RE_DATE_SLASH):
        for m in rx.finditer(text):
            iso = _mk_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            if iso:
                out.append(_Cand("date", m.start(), m.end(), m.group(0), iso, PRIORITY["date"]))
    for m in RE_DATE_LONG.finditer(text):
        month = MONTHS.get(m.group(2).lower().rstrip("."))
        if not month:
            continue
        day = int(m.group(1))
        end = m.end()
        if m.group(3):
            iso = _mk_date(day, month, int(m.group(3)))
            meta = {}
        else:
            # trim trailing separators that belonged to the optional year group
            seg = m.group(0)
            trimmed = seg.rstrip(" ,\t\n")
            end = m.start() + len(trimmed)
            iso = _infer_year(day, month, ref)
            meta = {"year_inferred": True}
        if iso:
            out.append(_Cand("date", m.start(), end, text[m.start():end], iso, PRIORITY["date"], meta))
    for m in RE_DATE_NUM_NOYEAR.finditer(text):
        iso = _infer_year(int(m.group(1)), int(m.group(2)), ref)
        if iso:
            out.append(_Cand("date", m.start(), m.end(), m.group(0), iso, PRIORITY["date"] - 1, {"year_inferred": True}))
    return out


def _infer_year(day: int, month: int, ref: date | None) -> str | None:
    ref = ref or date.today()
    for y in (ref.year, ref.year + 1):
        iso = _mk_date(day, month, y)
        if iso and date.fromisoformat(iso) >= ref:
            return iso
    return _mk_date(day, month, ref.year)


def _extract_times(text: str) -> list[_Cand]:
    out = []
    for rx, grp in TIME_PATTERNS:
        for m in rx.finditer(text):
            hh = int(m.group(grp + 1))
            mm_raw = m.group(grp + 2) if rx.groups >= grp + 2 else None
            mm = int(mm_raw) if mm_raw else 0
            start, end = m.start(grp), m.end(grp)
            out.append(_Cand("time", start, end, text[start:end], f"{hh:02d}:{mm:02d}", PRIORITY["time"]))
    return out


def _extract_durations(text: str) -> list[_Cand]:
    out = []
    for m in RE_DURATION.finditer(text):
        raw_n, unit = m.group(1), m.group(2).lower()
        n = int(raw_n) if raw_n.isdigit() else NUMBER_WORDS.get(raw_n.lower())
        if not n:
            continue
        if re.match(_UNIT_WEEK, unit, re.IGNORECASE):
            norm = f"P{n}W"
        elif re.match(_UNIT_MONTH, unit, re.IGNORECASE):
            norm = f"P{n}M"
        else:
            norm = f"P{n}D"
        before = text[max(0, m.start() - 45):m.start()]
        is_deadline = bool(DEADLINE_CUES.search(before)) or bool(
            re.match(r"\s+(?:nach|ab|dès|à compter|dalla|dal|a contare)", text[m.end():m.end() + 14], re.IGNORECASE)
        )
        # lock only the number (the unit is translated by the model)
        out.append(_Cand("duration", m.start(1), m.end(1), raw_n, norm, PRIORITY["duration"],
                         {"unit_text": m.group(2), "deadline": is_deadline, "count": n}))
    return out


def _extract_simple(text: str) -> list[_Cand]:
    out: list[_Cand] = []
    for m in RE_IBAN.finditer(text):
        compact = re.sub(r"\s", "", m.group(1))
        if len(compact) != 21:
            continue
        out.append(_Cand("iban", m.start(), m.end(), m.group(0), compact, PRIORITY["iban"], {"valid": iban_valid(compact)}))
    for m in RE_AHV.finditer(text):
        d = _digits(m.group(1))
        out.append(_Cand("ahv", m.start(), m.end(), m.group(0), format_ahv(d), PRIORITY["ahv"], {"valid": ahv_valid(d)}))
    for m in RE_EMAIL.finditer(text):
        out.append(_Cand("email", m.start(), m.end(), m.group(0), m.group(0).lower(), PRIORITY["email"]))
    for m in RE_URL.finditer(text):
        out.append(_Cand("url", m.start(), m.end(), m.group(0), m.group(0).lower(), PRIORITY["url"]))
    for m in RE_PHONE.finditer(text):
        norm = normalize_phone(m.group(0))
        if norm:
            line_before = text[text.rfind("\n", 0, m.start()) + 1:m.start()]
            out.append(_Cand("phone", m.start(), m.end(), m.group(0), norm, PRIORITY["phone"],
                             {"fax": bool(_FAX_CUE.search(line_before))}))
    for m in RE_LEGAL.finditer(text):
        val = m.group(0).rstrip()
        out.append(_Cand("legal", m.start(), m.start() + len(val), val, re.sub(r"\s+", " ", val), PRIORITY["legal"]))
    for m in RE_STREET.finditer(text):
        val = m.group(0)
        out.append(_Cand("address", m.start(), m.end(), val, re.sub(r"\s+", " ", val), PRIORITY["address"]))
    for m in RE_POBOX.finditer(text):
        out.append(_Cand("address", m.start(), m.end(), m.group(0), re.sub(r"\s+", " ", m.group(0)), PRIORITY["address"]))
    for m in RE_POSTAL.finditer(text):
        words = m.group(2).split()
        kept = []
        for w in words:
            if w in _LOCALITY_STOP:
                break
            kept.append(w)
        if not kept:
            continue
        locality = " ".join(kept).rstrip(",.;")
        start = m.start(1)
        if text[max(0, start - 3):start] == "CH-":
            start -= 3
        value_end = m.start(2) + len(m.group(2)[: m.group(2).find(kept[-1]) + len(kept[-1])].rstrip(",.;"))
        val = text[start:value_end]
        out.append(_Cand("address", start, value_end, val, f"{m.group(1)} {locality}", PRIORITY["address"], {"postal": True}))
    for m in RE_REF_LABELLED.finditer(text):
        val = m.group(1).rstrip(".-/ ")
        if sum(c.isdigit() for c in val) < 2:
            continue
        start = m.start(1)
        out.append(_Cand("reference", start, start + len(val), val, normalize_reference(val), PRIORITY["reference"],
                         {"label": text[m.start():m.start(1)].strip(" :.")}))
    for m in RE_REF_GENERIC.finditer(text):
        val = m.group(1)
        out.append(_Cand("reference", m.start(1), m.end(1), val, normalize_reference(val), PRIORITY["reference_generic"]))
    return out


def _resolve(cands: list[_Cand]) -> list[_Cand]:
    chosen: list[_Cand] = []
    for c in sorted(cands, key=lambda c: (-c.priority, -(c.end - c.start), c.start)):
        if c.end <= c.start:
            continue
        if any(not (c.end <= o.start or c.start >= o.end) for o in chosen):
            continue
        chosen.append(c)
    return sorted(chosen, key=lambda c: c.start)


def _letter_date(text: str, dates: list[_Cand]) -> _Cand | None:
    """Heuristic: a date in the first ~25 lines that stands on a 'Place, <date>' or 'Datum:' line."""
    head_end = 0
    for _ in range(25):
        nxt = text.find("\n", head_end + 1)
        if nxt == -1:
            head_end = len(text)
            break
        head_end = nxt
    for c in dates:
        if c.start > head_end:
            break
        line_start = text.rfind("\n", 0, c.start) + 1
        line_end = text.find("\n", c.end)
        line_end = len(text) if line_end == -1 else line_end
        before = text[line_start:c.start].strip()
        after = text[c.end:line_end].strip()
        if after == "" and (before == "" or before.endswith(",") or re.search(r"(?:Datum|Date|Data|le|den|il)\s*:?$", before, re.I)):
            return c
    return None


def extract_facts(text: str, lang: str | None = None) -> list[Fact]:
    """Run all deterministic extractors and return merged, de-duplicated facts with ids."""
    simple = _extract_simple(text)
    amounts = _extract_amounts(text)
    times = _extract_times(text)
    durations = _extract_durations(text)
    # First pass without year inference to find the letter date (reference for inference)
    first_dates = [c for c in _extract_dates(text, None) if not c.meta.get("year_inferred")]
    first_dates = [c for c in _resolve(simple + amounts + first_dates) if c.type == "date"]
    ld = _letter_date(text, first_dates)
    ref = date.fromisoformat(ld.normalized) if ld else None
    dates = _extract_dates(text, ref)
    chosen = _resolve(simple + amounts + times + durations + dates)

    facts: list[Fact] = []
    by_key: dict[tuple[str, str], Fact] = {}
    counters: dict[str, int] = {}
    for c in chosen:
        key = (c.type, c.normalized)
        if key in by_key:
            prev = by_key[key]
            prev.spans.append((c.start, c.end))
            prev.meta.setdefault("surfaces", [prev.value]).append(c.value)  # per-occurrence surface
            continue
        counters[c.type] = counters.get(c.type, 0) + 1
        f = Fact(
            id=f"{PREFIX[c.type]}{counters[c.type]}",
            type=c.type,
            value=c.value,
            normalized=c.normalized,
            span=(c.start, c.end),
            spans=[(c.start, c.end)],
            meta=dict(c.meta),
        )
        by_key[key] = f
        facts.append(f)
    _assign_roles(text, facts, ld)
    return facts


def _assign_roles(text: str, facts: list[Fact], letter_date: _Cand | None) -> None:
    ld_iso = letter_date.normalized if letter_date else None
    times = [f for f in facts if f.type == "time"]
    for f in facts:
        if f.type == "date":
            s = f.span[0]
            before = text[max(0, s - 40):s]
            after = text[f.span[1]:f.span[1] + 40]
            sentence = text[max(0, s - 160):f.span[1] + 60]
            if ld_iso and f.normalized == ld_iso and letter_date and f.span[0] == letter_date.start:
                f.role = "letter_date"
            elif any(t.span[0] - f.span[1] in range(0, 25) for t in times) or (
                APPOINTMENT_CUES.search(sentence) and re.search(r"\b(?:um|à|alle|ore|dès)\b", after, re.I)
            ):
                f.role = "appointment"
            elif DEADLINE_CUES.search(before):
                f.role = "deadline"
            elif ld_iso and f.normalized < ld_iso:
                f.role = "past"
            else:
                f.role = "other"
        elif f.type == "duration":
            f.role = "deadline" if f.meta.get("deadline") else "other"
        elif f.type == "phone":
            f.role = "fax" if f.meta.get("fax") else "contact"
        elif f.type == "time":
            f.role = "appointment"
    mark_critical(facts, ld_iso)


def mark_critical(facts: list[Fact], letter_date_iso: str | None = None) -> None:
    """Critical = must be carried into every explanation (rendered by fact-lock)."""
    for f in facts:
        if f.type in {"amount", "iban", "ahv", "reference", "time", "email"}:
            f.critical = True
        elif f.type == "phone":
            f.critical = f.role != "fax"
        elif f.type == "duration":
            f.critical = bool(f.meta.get("deadline"))
        elif f.type == "date":
            if f.role in {"deadline", "appointment", "effective"}:
                f.critical = True
            elif f.role in {"letter_date", "past"}:
                f.critical = False
            else:
                f.critical = bool(letter_date_iso and f.normalized > letter_date_iso)
        elif f.type == "address":
            f.critical = f.role == "appointment_place"
        else:
            f.critical = False


def render_fact(f: Fact) -> str:
    """Locale-safe rendering used when re-inserting a fact into generated text."""
    if f.type == "date":
        return format_date(f.normalized)
    if f.type == "amount":
        return format_chf(f.normalized)
    if f.type == "iban":
        return format_iban(f.normalized)
    if f.type == "ahv":
        return f.normalized
    if f.type == "phone":
        return format_phone(f.normalized)
    if f.type == "time":
        return f.normalized
    if f.type == "duration":
        return str(f.meta.get("count") or re.sub(r"\D", "", f.normalized))
    if f.type == "reference":
        return f.value.strip()
    return re.sub(r"\s+", " ", f.value.strip())


def facts_from_dicts(items: list[dict]) -> list[Fact]:
    out = []
    for d in items:
        d = dict(d)
        d["span"] = tuple(d.get("span") or (0, 0))
        d["spans"] = [tuple(s) for s in d.get("spans") or [d["span"]]]
        out.append(Fact(**{k: v for k, v in d.items() if k in Fact.__dataclass_fields__}))
    return out
