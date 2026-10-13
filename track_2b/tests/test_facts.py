"""Deterministic Swiss-format extractors (DE/FR/IT). Many cases are deliberately NOT in the dataset templates."""

import pytest

from passerelle.facts import (
    ahv_valid, extract_facts, format_chf, format_phone, iban_valid, normalize_amount, parse_date_text, render_fact,
)


def one(text, ftype):
    found = [f for f in extract_facts(text) if f.type == ftype]
    assert found, f"no {ftype} in {text!r}: {[(f.type, f.value) for f in extract_facts(text)]}"
    return found[0]


@pytest.mark.parametrize("text,iso", [
    ("bis 15.11.2026 einreichen", "2026-11-15"),
    ("am 5.1.2027", "2027-01-05"),
    ("Frist: 15.11.26", "2026-11-15"),
    ("bis 15. November 2026", "2026-11-15"),
    ("am 1. März 2027", "2027-03-01"),
    ("bis 15. Nov. 2026", "2026-11-15"),
    ("Dienstag, 3. November 2026", "2026-11-03"),
    ("au plus tard le 15 novembre 2026", "2026-11-15"),
    ("dès le 1er décembre 2026", "2026-12-01"),
    ("le 3 févr. 2027", "2027-02-03"),
    ("lundi 2 août 2027", "2027-08-02"),
    ("entro il 15 novembre 2026", "2026-11-15"),
    ("dal 1° dicembre 2026", "2026-12-01"),
    ("martedì 3 novembre 2026", "2026-11-03"),
    ("il 15/11/2026", "2026-11-15"),
])
def test_dates(text, iso):
    assert one(text, "date").normalized == iso


def test_date_without_year_inferred_from_letter_date():
    t = "Seewil, 5. Oktober 2026\n\nBitte melden Sie sich bis 3. November."
    dates = [f for f in extract_facts(t) if f.type == "date"]
    assert {d.normalized for d in dates} == {"2026-10-05", "2026-11-03"}
    assert any(d.meta.get("year_inferred") for d in dates)


@pytest.mark.parametrize("text", ["im Jahr 2026", "Steuererklärung 2025", "Büro 2.14", "Zins zu 5 %", "3 Kopien"])
def test_no_false_dates(text):
    assert not [f for f in extract_facts(text) if f.type in {"date", "amount"}]


def test_invalid_date_rejected():
    assert not [f for f in extract_facts("am 31.02.2026") if f.type == "date"]


@pytest.mark.parametrize("text,value", [
    ("CHF 1'250.50", "1250.50"), ("CHF 1’250.50", "1250.50"), ("Fr. 80.–", "80.00"), ("Fr. 1'250.--", "1250.00"),
    ("1 250,50 CHF", "1250.50"), ("CHF 1250", "1250.00"), ("SFr. 99.95", "99.95"), ("250 Franken", "250.00"),
    ("une amende de 120 francs", "120.00"), ("75 franchi", "75.00"), ("CHF 50.-", "50.00"), ("CHF 1.250,50", "1250.50"),
    ("CHF 12'000.00", "12000.00"), ("Fr. 3.50", "3.50"),
])
def test_amounts(text, value):
    assert one(text, "amount").normalized == value


def test_fr_friday_not_amount():
    assert not [f for f in extract_facts("Fr 14.11.") if f.type == "amount"]


def test_normalize_amount_and_format():
    assert normalize_amount("1'250.50") == "1250.50"
    assert format_chf("1250.50") == "CHF 1'250.50"
    assert format_chf("80.00") == "CHF 80.00"
    assert format_chf("1234567.80") == "CHF 1'234'567.80"


def test_iban():
    f = one("Bitte zahlen auf IBAN CH93 0076 2011 6238 5295 7.", "iban")
    assert f.normalized == "CH9300762011623852957" and f.meta["valid"]
    assert iban_valid("CH9300762011623852957")
    assert not iban_valid("CH9400762011623852957")
    assert render_fact(f) == "CH93 0076 2011 6238 5295 7"
    assert one("IBAN CH9300762011623852957", "iban").normalized == "CH9300762011623852957"


def test_ahv():
    f = one("AHV-Nr. 756.1234.5678.97", "ahv")
    assert f.normalized == "756.1234.5678.97"
    assert f.meta["valid"] == ahv_valid("7561234567897")
    assert one("N° AVS 7569217076985", "ahv").normalized == "756.9217.0769.85"


@pytest.mark.parametrize("text,e164", [
    ("Tel. 044 123 45 67", "+41441234567"), ("+41 44 123 45 67", "+41441234567"), ("0041 44 123 45 67", "+41441234567"),
    ("+41 (0)44 123 45 67", "+41441234567"), ("Natel 079 123 45 67", "+41791234567"), ("Gratis 0800 123 456", "+41800123456"),
    ("Tél. 021/316 11 11", "+41213161111"), ("tel. 091 814 00 00", "+41918140000"),
])
def test_phones(text, e164):
    assert one(text, "phone").normalized == e164


def test_fax_not_contact():
    facts = extract_facts("Telefon 044 123 45 67\nFax 044 123 45 68")
    roles = {f.normalized: f.role for f in facts if f.type == "phone"}
    assert roles["+41441234567"] == "contact" and roles["+41441234568"] == "fax"
    assert format_phone("+41441234567") == "044 123 45 67"


@pytest.mark.parametrize("text,hhmm", [
    ("um 14:30", "14:30"), ("um 14.30 Uhr", "14:30"), ("um 9 Uhr", "09:00"), ("à 8h30", "08:30"),
    ("à 14 h 30", "14:30"), ("alle ore 9.30", "09:30"), ("alle 9:30", "09:30"), ("dalle 8.00", "08:00"),
])
def test_times(text, hhmm):
    assert one(text, "time").normalized == hhmm


def test_time_range():
    times = sorted(f.normalized for f in extract_facts("Montag bis Freitag, 8.00 bis 11.30 Uhr") if f.type == "time")
    assert times == ["08:00", "11:30"]


@pytest.mark.parametrize("text,norm,surface", [
    ("innert 30 Tagen", "P30D", "30"), ("innert zehn Tagen", "P10D", "zehn"), ("innerhalb von 14 Tagen", "P14D", "14"),
    ("dans les 30 jours", "P30D", "30"), ("dans un délai de dix jours", "P10D", "dix"), ("entro 30 giorni", "P30D", "30"),
    ("entro dieci giorni", "P10D", "dieci"), ("innert 2 Wochen", "P2W", "2"), ("dans un mois", "P1M", "un"),
    ("entro un mese", "P1M", "un"),
])
def test_durations(text, norm, surface):
    f = one(text, "duration")
    assert (f.normalized, f.value) == (norm, surface)
    assert f.meta["deadline"] is True
    assert render_fact(f) == norm[1:-1]


@pytest.mark.parametrize("text,value", [
    ("Referenz: SOZ-2026-04512", "SOZ-2026-04512"), ("Betreibung Nr. 26-104523", "26-104523"),
    ("N° de dossier : 2026/1187", "2026/1187"), ("Dossier n° MIG-2026-1187", "MIG-2026-1187"),
    ("Rif. 2026-TI-0042", "2026-TI-0042"), ("N. pratica 12345", "12345"), ("N-Nummer: N 612 345", "N 612 345"),
    ("Ihr Zeichen: AB/12 345", "AB/12 345"), ("Steuernummer: 1.234.567.89", "1.234.567.89"),
    ("QR-Referenz 21 00000 00003 13947 14300 09017", "21 00000 00003 13947 14300 09017"),
    ("Unser Zeichen MIG/2026/1187 vom", "MIG/2026/1187"),
])
def test_references(text, value):
    assert one(text, "reference").value == value


def test_reference_stops_before_capitalised_word():
    f = one("Referenz: 2026-0451 Sehr geehrte Frau", "reference")
    assert f.value == "2026-0451"


def test_email_url_legal_address():
    facts = extract_facts("Kontakt: info@seewil.ch, www.seewil.ch\nBahnhofstrasse 12\n8004 Seewil\nArt. 74 SchKG\nRue du Marché 5\nVia Cantonale 15")
    types = {(f.type, f.value) for f in facts}
    assert ("email", "info@seewil.ch") in types
    assert ("url", "www.seewil.ch") in types
    assert ("address", "Bahnhofstrasse 12") in types
    assert ("address", "8004 Seewil") in types
    assert ("legal", "Art. 74 SchKG") in types
    assert ("address", "Rue du Marché 5") in types
    assert ("address", "Via Cantonale 15") in types


def test_roles_and_criticality(letter_de):
    facts = extract_facts(letter_de)
    by_norm = {f.normalized: f for f in facts}
    assert by_norm["2026-10-05"].role == "letter_date" and not by_norm["2026-10-05"].critical
    assert by_norm["2026-11-15"].role == "deadline" and by_norm["2026-11-15"].critical
    assert by_norm["2026-07-01"].role == "past" and not by_norm["2026-07-01"].critical
    assert by_norm["P10D"].critical
    assert all(f.critical for f in facts if f.type in {"amount", "iban", "reference"})


def test_appointment_role():
    t = "Seewil, 5. Oktober 2026\n\nWir laden Sie zu einem Gespräch ein.\nDatum: 3. November 2026\nZeit: 09.30 Uhr"
    d = [f for f in extract_facts(t) if f.normalized == "2026-11-03"][0]
    assert d.role == "appointment"


def test_same_fact_shares_one_id(letter_de):
    t = letter_de + "\nNochmals: zahlbar bis 15.11.2026."
    deadline = [f for f in extract_facts(t) if f.normalized == "2026-11-15"]
    assert len(deadline) == 1 and len(deadline[0].spans) == 2


def test_ids_are_typed_and_sequential(letter_de):
    facts = extract_facts(letter_de)
    amounts = sorted(f.id for f in facts if f.type == "amount")
    assert amounts == ["A1", "A2"]
    assert all(f.id[0] in "DNAISRPHEWLG" for f in facts)


def test_parse_date_text_iso():
    assert parse_date_text("2026-11-15") == "2026-11-15"
    assert parse_date_text("15 novembre 2026") == "2026-11-15"
