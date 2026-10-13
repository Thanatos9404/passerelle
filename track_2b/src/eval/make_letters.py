"""Generate the synthetic Swiss letter dataset (data/letters/) with exact ground truth.

    python -m eval.make_letters [--out data/letters] [--instances 2] [--seed 2610]

* 12 letter types x {de, fr, it} x N instances (default 2 -> 72 letters).
* Every fact-bearing slot is rendered in a randomly chosen Swiss surface format (numeric vs long dates,
  CHF/Fr./typographic apostrophes, +41 vs 0xx phones, number words for durations, …) and recorded
  with type, surface, normalised value, role, criticality and character spans.  The ground truth is
  produced by the generator — never by the extractors under test.
* All entities are fictional; IBAN/AHV numbers are random with valid checksums.
* Splits: ``dev`` (12 letters, one per type, languages rotated) for threshold calibration only;
  ``test`` (the rest).  ``explain_subset`` marks the 24 test letters used for the (GPU-heavy)
  explanation ablation: instance 0 of every (type, language) not in dev.
Licence: CDLA-Permissive-2.0.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from .letter_templates import HEADER, LETTER_TYPES, T

GENERATOR_VERSION = "1.0"
LICENSE = "CDLA-Permissive-2.0"

COMMUNES = {
    "de": [("Seewil", "Aarenfeld"), ("Birkental", "Aarenfeld"), ("Hohenbühl", "Lindmatt"), ("Rüttiwil", "Lindmatt")],
    "fr": [("Valdorée", "Jura-Lac"), ("Courtelaine", "Jura-Lac"), ("Bellecombe-sur-Lac", "Haute-Broye"), ("Montverlin", "Haute-Broye")],
    "it": [("Valcastello", "Ticino Alto"), ("Montelago", "Ticino Alto"), ("Riva Serena", "Verbano Nord"), ("Sorvigo", "Verbano Nord")],
}
POSTAL_RANGE = {"de": (3000, 9699), "fr": (1000, 2999), "it": (6500, 6999)}
AREA_CODES = {"de": ["044", "031", "061", "071", "052", "041"], "fr": ["021", "022", "024", "026", "032"], "it": ["091"]}
STREETS = {
    "de": ["Bahnhofstrasse", "Lindenstrasse", "Kirchgasse", "Rosenweg", "Sonnenrain", "Mattenweg", "Dorfplatz", "Schulhausstrasse", "Seestrasse"],
    "fr": ["Rue du Marché", "Chemin des Vignes", "Avenue de la Gare", "Rue des Tilleuls", "Route de la Forêt", "Place de l'Église", "Rue du Lac"],
    "it": ["Via Cantonale", "Via dei Mulini", "Viale Stazione", "Via San Rocco", "Piazza Grande", "Via al Lago", "Via delle Scuole"],
}
PEOPLE = [
    ("f", "Amina", "Ahmadi"), ("m", "Yonas", "Tesfay"), ("f", "Olena", "Kovalenko"), ("m", "Kumaran", "Sivakumar"),
    ("f", "Hawa", "Abdi"), ("m", "Arben", "Krasniqi"), ("m", "Mehmet", "Yilmaz"), ("f", "Fatima", "Haidari"),
    ("f", "Selam", "Gebremedhin"), ("m", "Dmytro", "Shevchenko"), ("f", "Nirmala", "Rajan"), ("m", "Abdirahman", "Warsame"),
    ("f", "Leonora", "Berisha"), ("f", "Ayşe", "Demir"), ("f", "Zahra", "Noori"), ("m", "Tesfalem", "Haile"),
    ("m", "Omar", "Al-Khatib"), ("f", "Mariam", "Yousef"), ("m", "Ricardo", "Pereira"), ("f", "Lucía", "Gómez"),
]
STAFF = {"de": ["Frau Brunner", "Herr Meier", "Frau Keller", "Herr Baumann"],
         "fr": ["Mme Rochat", "M. Favre", "Mme Pittet", "M. Gerber"],
         "it": ["la signora Bernasconi", "il signor Fontana", "la signora Pedrazzi", "il signor Rusconi"]}
CHILD_NAMES = ["Sara", "Daniel", "Lina", "Noah", "Maryam", "Elias", "Hiwet", "Bilal"]
CREDITORS = {"de": "Krankenversicherung Sana Montis AG", "fr": "Assurance-maladie Sana Montis SA", "it": "Assicurazione malattie Sana Montis SA"}
INSURERS = {"de": "Krankenversicherung Sana Montis AG", "fr": "Caisse-maladie Alpenrose SA", "it": "Cassa malati Monteverde SA"}
AGENCIES = {"de": "Verwaltung Lindenhof Immobilien AG", "fr": "Régie du Léman-Sud SA", "it": "Amministrazione stabili Ceresio SA"}
REGIONS = {"de": "Nordwest", "fr": "Romandie", "it": "Sud"}

MONTHS = {
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
    "it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
}
WEEKDAYS = {
    "de": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
    "fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
    "it": ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"],
}
NUM_WORDS = {"de": {10: "zehn", 20: "zwanzig", 30: "dreissig", 14: "vierzehn"},
             "fr": {10: "dix", 20: "vingt", 30: "trente", 14: "quatorze"},
             "it": {10: "dieci", 20: "venti", 30: "trenta", 14: "quattordici"}}
LEGAL = {
    "debt_collection": {"de": "Art. 74 SchKG", "fr": "art. 74 LP", "it": "art. 74 LEF"},
    "rent_increase": {"de": "Art. 270b OR", "fr": "art. 270b CO", "it": "art. 270b CO"},
}


@dataclass
class Slot:
    surface: str
    ftype: str | None = None      # fact type or None (plain text)
    normalized: str | None = None
    role: str | None = None
    critical: bool = False


# ------------------------------------------------------------------------- renderers

def fmt_date(d: date, lang: str, rng: random.Random, weekday: bool = False, style: str | None = None) -> str:
    style = style or rng.choice(["num", "num", "long", "long"])
    if style == "num":
        s = rng.choice([f"{d.day:02d}.{d.month:02d}.{d.year}", f"{d.day}.{d.month}.{d.year}"])
        return s
    m = MONTHS[lang][d.month - 1]
    if lang == "de":
        s = f"{d.day}. {m} {d.year}"
    elif lang == "fr":
        s = f"{'1er' if d.day == 1 else d.day} {m} {d.year}"
    else:
        s = f"{'1°' if d.day == 1 and rng.random() < 0.5 else d.day} {m} {d.year}"
    if weekday:
        wd = WEEKDAYS[lang][d.weekday()]
        s = f"{wd}, {s}" if lang == "de" else f"{wd} {s}"
    return s


def fmt_chf(value: float, lang: str, rng: random.Random) -> str:
    whole = int(round(value * 100)) // 100
    cents = int(round(value * 100)) % 100
    sep = rng.choice(["'", "'", "’"])
    w = f"{whole:,}".replace(",", sep)
    if cents == 0 and rng.random() < 0.35:
        num = f"{w}.–"
    else:
        num = f"{w}.{cents:02d}"
    if lang == "fr" and rng.random() < 0.25:
        return f"{f'{whole:,}'.replace(',', ' ')}.{cents:02d} CHF"
    return rng.choice([f"CHF {num}", f"CHF {num}", f"Fr. {num}"])


def fmt_phone(area: str, rest: str, rng: random.Random) -> str:
    a, b, c = rest[:3], rest[3:5], rest[5:7]
    return rng.choice([f"{area} {a} {b} {c}", f"{area} {a} {b} {c}", f"+41 {area[1:]} {a} {b} {c}", f"{area}/{a} {b} {c}"])


def fmt_time(h: int, m: int, lang: str, rng: random.Random, inline: bool) -> str:
    if lang == "de":
        return rng.choice([f"{h:02d}.{m:02d} Uhr", f"{h}.{m:02d} Uhr", f"{h:02d}:{m:02d} Uhr"])
    if lang == "fr":
        return rng.choice([f"{h} h {m:02d}", f"{h:02d}h{m:02d}", f"{h:02d}:{m:02d}"])
    return rng.choice([f"{h}.{m:02d}", f"{h:02d}:{m:02d}"]) if inline else f"{h:02d}:{m:02d}"


def iban_ch(rng: random.Random) -> str:
    bban = f"{rng.randint(0, 99999):05d}{rng.randint(0, 10**12 - 1):012d}"
    num = int(bban + "1217" + "00")  # C=12, H=17
    check = 98 - num % 97
    return f"CH{check:02d}{bban}"


def ahv_number(rng: random.Random) -> str:
    digits = "756" + "".join(str(rng.randint(0, 9)) for _ in range(9))
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(digits))
    return digits + str((10 - total % 10) % 10)


def qr_reference(rng: random.Random) -> str:
    body = "".join(str(rng.randint(0, 9)) for _ in range(26))
    table = [0, 9, 4, 6, 8, 2, 7, 1, 3, 5]
    carry = 0
    for ch in body:
        carry = table[(carry + int(ch)) % 10]
    full = body + str((10 - carry) % 10)
    return full[:2] + " " + " ".join(full[i:i + 5] for i in range(2, 27, 5))


def fmt_duration(n: int, lang: str, rng: random.Random) -> str:
    if n in NUM_WORDS[lang] and rng.random() < 0.25:
        return NUM_WORDS[lang][n]
    return str(n)


# ------------------------------------------------------------------------- context

def build_context(ltype: str, lang: str, rng: random.Random, instance: int) -> tuple[dict[str, Slot], dict]:
    commune, canton = rng.choice(COMMUNES[lang])
    gender, first, last = rng.choice(PEOPLE)
    lo, hi = POSTAL_RANGE[lang]
    area = rng.choice(AREA_CODES[lang])
    letter_date = date(2026, 10, 1) + timedelta(days=rng.randint(0, 19))
    while letter_date.weekday() >= 5:
        letter_date += timedelta(days=1)

    def future(a: int, b: int, weekday_only: bool = True) -> date:
        d = letter_date + timedelta(days=rng.randint(a, b))
        while weekday_only and d.weekday() >= 5:
            d += timedelta(days=1)
        return d

    def date_slot(d: date, role: str, critical: bool, weekday: bool = False) -> Slot:
        return Slot(fmt_date(d, lang, rng, weekday), "date", d.isoformat(), role, critical)

    def amount_slot(v: float) -> Slot:
        return Slot(fmt_chf(v, lang, rng), "amount", f"{v:.2f}", None, True)

    def time_slot(h: int, m: int, role: str = "appointment", critical: bool = True, inline: bool = False) -> Slot:
        return Slot(fmt_time(h, m, lang, rng, inline), "time", f"{h:02d}:{m:02d}", role, critical)

    def dur_slot(n: int) -> Slot:
        return Slot(fmt_duration(n, lang, rng), "duration", f"P{n}D", "deadline", True)

    def street_slot(role: str | None = None, critical: bool = False) -> Slot:
        s = f"{rng.choice(STREETS[lang])} {rng.randint(1, 48)}"
        return Slot(s, "address", s, role, critical)

    def postal_slot(town: str, role: str | None = None, critical: bool = False) -> Slot:
        s = f"{rng.randint(lo, hi)} {town}"
        return Slot(s, "address", s, role, critical)

    phone_rest = f"{rng.randint(200, 999)}{rng.randint(10, 99)}{rng.randint(10, 99)}"
    phone_e164 = "+41" + area[1:] + phone_rest
    dept_slug = {"tax_reminder": "steueramt", "social_assistance_appointment": "sozialdienst"}.get(ltype, "info")
    slug = re.sub(r"[^a-z]", "", commune.lower().replace("ü", "ue").replace("é", "e").replace("è", "e"))
    email = f"{dept_slug}@{slug}.ch"
    title = {"de": ("Frau", "Herr"), "fr": ("Madame", "Monsieur"), "it": ("Signora", "Signor")}[lang][0 if gender == "f" else 1]
    if lang == "de":
        salutation = f"Sehr geehrte Frau {last}" if gender == "f" else f"Sehr geehrter Herr {last}"
    elif lang == "fr":
        salutation = "Madame," if gender == "f" else "Monsieur,"
    else:
        salutation = f"Gentile Signora {last}" if gender == "f" else f"Egregio Signor {last}"

    ctx: dict[str, Slot] = {
        "commune": Slot(commune), "canton": Slot(canton), "place": Slot(commune), "region": Slot(REGIONS[lang]),
        "auth_street": street_slot(), "auth_postal": postal_slot(commune),
        "auth_phone": Slot(fmt_phone(area, phone_rest, rng), "phone", phone_e164, "contact", True),
        "auth_email": Slot(email, "email", email, None, True),
        "phone_label": Slot({"de": rng.choice(["Telefon", "Tel."]), "fr": rng.choice(["Tél.", "Téléphone"]), "it": rng.choice(["Tel.", "Telefono"])}[lang]),
        "rcp_title": Slot(title), "rcp_name": Slot(f"{first} {last}"),
        "rcp_street": street_slot(), "rcp_postal": postal_slot(commune),
        "letter_date": date_slot(letter_date, "letter_date", False),
        "salutation": Slot(salutation), "salutation_close": Slot("Madame" if gender == "f" else "Monsieur"),
        "contact": Slot(rng.choice(STAFF[lang])),
        "year": Slot(str(letter_date.year)), "year_next": Slot(str(letter_date.year + 1)),
        "creditor": Slot(CREDITORS[lang]), "insurer": Slot(INSURERS[lang]), "agency": Slot(AGENCIES[lang]),
    }
    y = letter_date.year
    if ltype == "tax_reminder":
        ctx.update(ref=Slot(f"{rng.randint(1, 9)}.{rng.randint(100, 999)}.{rng.randint(100, 999)}.{rng.randint(10, 99)}", "reference", None, None, True),
                   tax_year=Slot(str(y - 1)), deadline=date_slot(future(20, 35), "deadline", True),
                   fine=amount_slot(rng.choice([500, 1000, 1000])), fee=amount_slot(rng.choice([20, 30, 40, 50])))
    elif ltype == "premium_reduction":
        eff = date(y + 1, 1, 1)
        ctx.update(ref=Slot(f"{rng.randint(1000000, 9999999)}", "reference", None, None, True),
                   ahv=Slot(_fmt_ahv(ahv_number(rng)), "ahv", None, None, True),
                   effective=date_slot(eff, "effective", True), amount_month=amount_slot(rng.choice([85, 112.5, 145, 168, 210.4])),
                   deadline=date_slot(future(25, 40), "deadline", True), stop_date=date_slot(date(y + 1, 3, 1), "other", True),
                   objection_days=dur_slot(30))
    elif ltype == "permit_renewal":
        ctx.update(ref=Slot(f"MIG-{y}-{rng.randint(100000, 999999)}", "reference", None, None, True),
                   zemis=Slot(f"{rng.randint(10000000, 99999999)}.{rng.randint(1, 9)}", "reference", None, None, True),
                   expiry=date_slot(future(60, 90, False), "effective", True), deadline=date_slot(future(25, 40), "deadline", True),
                   fee=amount_slot(rng.choice([65, 95, 120])), iban=_iban_slot(rng),
                   open_from=time_slot(8, 0, "other", False, inline=True), open_to=time_slot(11, 30, "other", False, inline=True))
    elif ltype == "social_assistance_appointment":
        appt = future(10, 25)
        ctx.update(ref=Slot(f"SOZ-{y}-{rng.randint(10000, 99999)}", "reference", None, None, True),
                   appt_date=date_slot(appt, "appointment", True, weekday=True),
                   appt_time=time_slot(rng.choice([8, 9, 10, 13, 14, 15]), rng.choice([0, 15, 30, 45])),
                   appt_street=street_slot("appointment_place", True),
                   cancel_deadline=date_slot(appt - timedelta(days=2), "deadline", True))
    elif ltype == "school_enrolment":
        child = rng.choice(CHILD_NAMES)
        birth = date(y - 4, rng.randint(1, 12), rng.randint(1, 28))
        info = future(14, 30)
        ctx.update(ref=Slot(f"SCH-{y}-{rng.randint(1000, 9999)}", "reference", None, None, True),
                   school_year=Slot(f"{y + 1}/{str(y + 2)[2:]}"), child_name=Slot(child),
                   child_birth=date_slot(birth, "past", False), school_start=date_slot(date(y + 1, 8, 16), "effective", True),
                   deadline=date_slot(future(30, 45), "deadline", True), info_date=date_slot(info, "appointment", True, weekday=True),
                   info_time=time_slot(19, rng.choice([0, 30]), inline=True), school_house=Slot(rng.choice(["Dorf", "Mitte", "Lindenhof"])))
    elif ltype == "debt_collection":
        main = rng.choice([480.0, 1250.5, 2310.75, 865.2, 3400.0])
        ctx.update(ref=Slot(f"{str(y)[2:]}-{rng.randint(100000, 999999)}", "reference", None, None, True),
                   amount_main=amount_slot(main), costs=amount_slot(rng.choice([53.3, 73.3, 103.3])),
                   interest_from=date_slot(letter_date - timedelta(days=rng.randint(60, 150)), "past", False),
                   pay_days=dur_slot(20), objection_days=dur_slot(10), iban=_iban_slot(rng),
                   legal_ref=Slot(LEGAL[ltype][lang], "legal", LEGAL[ltype][lang], None, False),
                   open_from=time_slot(8, 0, "other", False, inline=True), open_to=time_slot(11, 30, "other", False, inline=True))
        ctx["salutation"] = Slot({"de": "Sehr geehrte Damen und Herren", "fr": "Madame, Monsieur,", "it": "Gentili signore e signori"}[lang])
    elif ltype == "rent_increase":
        old = rng.choice([1180.0, 1420.0, 1655.0, 1890.0])
        eff = date(y + 1, rng.choice([1, 4]), 1)
        cs, cp = _conc_address(lang, rng)
        ctx.update(ref=Slot(f"{rng.randint(1000, 9999)}.{rng.randint(10, 99)}.{rng.randint(100, 999)}", "reference", None, None, True),
                   effective=date_slot(eff, "effective", True), rent_old=amount_slot(old), rent_new=amount_slot(old + rng.choice([35, 48, 62])),
                   extra_costs=amount_slot(rng.choice([180, 220, 260])), contest_days=dur_slot(30),
                   conc_street=Slot(cs, "address", cs, None, False), conc_postal=Slot(cp, "address", cp, None, False),
                   legal_ref=Slot(LEGAL[ltype][lang], "legal", LEGAL[ltype][lang], None, False))
    elif ltype == "ahv_contributions":
        annual = rng.choice([530.0, 1060.0, 1650.0, 2420.0])
        ctx.update(ahv=Slot(_fmt_ahv(ahv_number(rng)), "ahv", None, None, True),
                   ref=Slot(f"NE-{rng.randint(100000, 999999)}", "reference", None, None, True),
                   annual=amount_slot(annual), quarter=amount_slot(annual / 4), due=date_slot(date(y + 1, 3, 31), "deadline", True),
                   iban=_iban_slot(rng), qr_ref=Slot(qr_reference(rng), "reference", None, None, True), notify_days=dur_slot(30))
    elif ltype == "family_allowance":
        child = rng.choice(CHILD_NAMES)
        b16 = future(40, 80, False)
        ctx.update(ref=Slot(f"FAK-{rng.randint(100000, 999999)}", "reference", None, None, True), child_name=Slot(child),
                   child_birth=date_slot(date(b16.year - 16, b16.month, b16.day), "past", False),
                   age16_date=date_slot(b16, "other", True), allowance=amount_slot(rng.choice([268, 290, 325])),
                   deadline=date_slot(future(20, 30), "deadline", True), stop_date=date_slot(date(b16.year, b16.month, 1) + timedelta(days=31), "other", True))
    elif ltype == "health_insurance_reminder":
        open_amt = rng.choice([389.4, 412.8, 655.2, 798.0])
        fee = rng.choice([20.0, 30.0, 40.0])
        ctx.update(ref=Slot(f"{rng.randint(100, 999)}.{rng.randint(1000, 9999)}.{rng.randint(1000, 9999)}", "reference", None, None, True),
                   invoice=Slot(f"R-{y}-{rng.randint(100000, 999999)}", "reference", None, None, True),
                   amount_open=amount_slot(open_amt), fee=amount_slot(fee), total=amount_slot(open_amt + fee),
                   deadline=date_slot(future(10, 20), "deadline", True), iban=_iban_slot(rng))
    elif ltype == "asylum_interview":
        appt = future(10, 30)
        ctx.update(ref=Slot(f"N {rng.randint(100, 999)} {rng.randint(100, 999)}", "reference", None, None, True),
                   appt_date=date_slot(appt, "appointment", True, weekday=True),
                   appt_time=time_slot(rng.choice([8, 9, 13]), rng.choice([0, 30])),
                   appt_street=street_slot("appointment_place", True), appt_postal=postal_slot(commune, "appointment_place", True))
    elif ltype == "fine_notice":
        off = letter_date - timedelta(days=rng.randint(5, 20))
        ctx.update(ref=Slot(f"OB-{y}-{rng.randint(100000, 999999)}", "reference", None, None, True),
                   offence_date=date_slot(off, "past", False),
                   offence_time=time_slot(rng.randint(8, 18), rng.choice([5, 20, 35, 50]), "other", False, inline=True),
                   plate=Slot(f"AF {rng.randint(10000, 99999)}"), offence_street=street_slot(),
                   amount=amount_slot(rng.choice([40, 80, 120])), pay_days=dur_slot(30), iban=_iban_slot(rng),
                   qr_ref=Slot(qr_reference(rng), "reference", None, None, True))
    meta = {"commune": commune, "canton": canton, "recipient": f"{first} {last}", "letter_date": letter_date.isoformat()}
    return ctx, meta


def _fmt_ahv(d: str) -> str:
    return f"{d[:3]}.{d[3:7]}.{d[7:11]}.{d[11:]}"


def _iban_slot(rng: random.Random) -> Slot:
    compact = iban_ch(rng)
    surface = " ".join(compact[i:i + 4] for i in range(0, len(compact), 4))
    return Slot(surface, "iban", compact, None, True)


def _conc_address(lang: str, rng: random.Random) -> tuple[str, str]:
    lo, hi = POSTAL_RANGE[lang]
    town = rng.choice(COMMUNES[lang])[0]
    return f"{rng.choice(STREETS[lang])} {rng.randint(1, 30)}", f"{rng.randint(lo, hi)} {town}"


# ------------------------------------------------------------------------- rendering

_SLOT_RX = re.compile(r"\{([a-z_0-9]+)\}")


def render(template: str, ctx: dict[str, Slot]) -> tuple[str, list[dict]]:
    """Fill {slots}; return text and a list of fact occurrences with spans."""
    out, occ, pos = [], [], 0
    cursor = 0
    for m in _SLOT_RX.finditer(template):
        lit = template[pos:m.start()]
        out.append(lit)
        cursor += len(lit)
        name = m.group(1)
        slot = ctx[name]
        if _SLOT_RX.search(slot.surface):  # nested (e.g. "Gemeinde {commune}")
            inner, inner_occ = render(slot.surface, ctx)
            for o in inner_occ:
                o["span"] = [o["span"][0] + cursor, o["span"][1] + cursor]
            occ.extend(inner_occ)
            out.append(inner)
            cursor += len(inner)
        else:
            if slot.ftype:
                occ.append({"slot": name, "span": [cursor, cursor + len(slot.surface)]})
            out.append(slot.surface)
            cursor += len(slot.surface)
        pos = m.end()
    out.append(template[pos:])
    return "".join(out), occ


def normalize_slot(slot: Slot) -> str:
    if slot.normalized is not None:
        return slot.normalized
    if slot.ftype == "reference":
        return re.sub(r"\s+", " ", slot.surface).upper()
    if slot.ftype == "ahv":
        return slot.surface
    return slot.surface


def make_letter(ltype: str, lang: str, instance: int, seed: int) -> tuple[str, dict]:
    rng = random.Random(f"{seed}-{ltype}-{lang}-{instance}")
    ctx, meta = build_context(ltype, lang, rng, instance)
    tpl = T[ltype]
    ctx["auth_name"] = Slot(tpl["auth"][lang])
    ctx["auth_dept"] = Slot(tpl["dept"][lang])
    text, occ = render(HEADER[lang] + tpl["body"][lang], ctx)
    authority = render(tpl["auth"][lang], ctx)[0]
    facts: dict[tuple[str, str], dict] = {}
    for o in occ:
        slot = ctx[o["slot"]]
        key = (slot.ftype, normalize_slot(slot))
        if key not in facts:
            facts[key] = {"type": slot.ftype, "value": slot.surface, "normalized": key[1], "role": slot.role,
                          "critical": slot.critical, "slot": o["slot"], "spans": []}
        else:  # same fact again: critical if any occurrence is critical
            facts[key]["critical"] = facts[key]["critical"] or slot.critical
            if facts[key]["role"] in (None, "other") and slot.role:
                facts[key]["role"] = slot.role
        facts[key]["spans"].append(o["span"])
    fact_list = sorted(facts.values(), key=lambda f: f["spans"][0][0])
    for f in fact_list:
        for s, e in f["spans"]:
            assert text[s:e] == ctx[f["slot"]].surface, (ltype, lang, f)
    deadlines = sorted(f["normalized"] for f in fact_list if f["type"] == "date" and f["role"] == "deadline")
    appt = next((f for f in fact_list if f["type"] == "date" and f["role"] == "appointment"), None)
    appt_time = next((f for f in fact_list if f["type"] == "time" and f["role"] == "appointment"), None)
    sid = f"{ltype}_{lang}_{instance}"
    gt = {
        "id": sid,
        "letter_type": ltype,
        "lang": lang,
        "instance": instance,
        "title": f"{tpl['title'][lang]} — {authority}",
        "authority": authority,
        "facts": fact_list,
        "card": {
            "letter_date": meta["letter_date"],
            "deadline": deadlines[0] if deadlines else None,
            "deadline_relative": next((f["normalized"] for f in fact_list if f["type"] == "duration"), None),
            "appointment": {"date": appt["normalized"], "time": appt_time["normalized"] if appt_time else None} if appt else None,
            "amounts": [f["normalized"] for f in fact_list if f["type"] == "amount"],
            "references": [f["normalized"] for f in fact_list if f["type"] == "reference"],
            "iban": next((f["normalized"] for f in fact_list if f["type"] == "iban"), None),
            "ahv": next((f["normalized"] for f in fact_list if f["type"] == "ahv"), None),
            "phone": next((f["normalized"] for f in fact_list if f["type"] == "phone"), None),
            "email": next((f["normalized"] for f in fact_list if f["type"] == "email"), None),
        },
        "action_required": tpl["action"][lang],
        "consequence": tpl["consequence"][lang],
        "documents": tpl["documents"][lang],
        "recipient": meta["recipient"],
        "synthetic": True,
        "license": LICENSE,
        "generator_version": GENERATOR_VERSION,
    }
    return text, gt


def assign_splits(gts: list[dict]) -> None:
    langs = ["de", "fr", "it"]
    for g in gts:
        i = LETTER_TYPES.index(g["letter_type"])
        dev_lang = langs[i % 3]
        g["split"] = "dev" if (g["instance"] == 0 and g["lang"] == dev_lang) else "test"
        g["explain_subset"] = g["split"] == "test" and g["instance"] == 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[2] / "data" / "letters"))
    ap.add_argument("--instances", type=int, default=2)
    ap.add_argument("--seed", type=int, default=2610)
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob("*.txt")) + list(out.glob("*_[0-9].json")):
        old.unlink()
    gts = []
    texts = {}
    for ltype in LETTER_TYPES:
        for lang in ("de", "fr", "it"):
            for inst in range(args.instances):
                text, gt = make_letter(ltype, lang, inst, args.seed)
                texts[gt["id"]] = text
                gts.append(gt)
    assign_splits(gts)
    for gt in gts:
        (out / f"{gt['id']}.txt").write_text(texts[gt["id"]] + "\n", encoding="utf-8")
        (out / f"{gt['id']}.json").write_text(json.dumps(gt, ensure_ascii=False, indent=1), encoding="utf-8")
    splits = {
        "dev": [g["id"] for g in gts if g["split"] == "dev"],
        "test": [g["id"] for g in gts if g["split"] == "test"],
        "explain_subset": [g["id"] for g in gts if g.get("explain_subset")],
        "generator_version": GENERATOR_VERSION, "seed": args.seed, "license": LICENSE,
    }
    (out / "splits.json").write_text(json.dumps(splits, indent=1), encoding="utf-8")
    print(f"wrote {len(gts)} letters to {out} (dev={len(splits['dev'])}, test={len(splits['test'])}, "
          f"explain_subset={len(splits['explain_subset'])})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
