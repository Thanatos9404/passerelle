"""Fact-lock integrity: property-style tests with Hypothesis."""

import re

from hypothesis import given, settings
from hypothesis import strategies as st

from passerelle.facts import extract_facts
from passerelle.factlock import StreamUnmasker, audit, find_placeholders, mask, strip_placeholders, unmask

FACT_POOL = [
    "15.11.2026", "3. November 2026", "1er décembre 2026", "CHF 1'250.50", "Fr. 80.–", "CH93 0076 2011 6238 5295 7",
    "756.1234.5678.97", "044 123 45 67", "+41 31 321 12 34", "14:30", "info@seewil.ch", "Referenz: SOZ-2026-04512",
    "innert 30 Tagen", "entro 10 giorni", "Bahnhofstrasse 12",
]
FILLER = st.text(alphabet=st.sampled_from(list("abcdefghij klmnop äöü,;")), min_size=1, max_size=25)


@st.composite
def letters(draw):
    parts = [draw(FILLER)]
    for _ in range(draw(st.integers(1, 6))):
        parts.append(" " + draw(st.sampled_from(FACT_POOL)) + " ")
        parts.append(draw(FILLER))
    return "".join(parts)


@settings(max_examples=150, deadline=None)
@given(letters())
def test_mask_unmask_surface_roundtrip(text):
    facts = extract_facts(text)
    masked = mask(text, facts)
    assert unmask(masked, {f.id: f for f in facts}, mode="surface")[0] == text


@settings(max_examples=150, deadline=None)
@given(letters())
def test_masked_text_contains_no_fact_digits(text):
    facts = extract_facts(text)
    masked = mask(text, facts)
    for f in facts:
        if f.type in {"date", "amount", "iban", "ahv", "phone"}:
            assert f.value not in masked


@settings(max_examples=150, deadline=None)
@given(letters(), st.data())
def test_audit_detects_deletion_duplication_invention(text, data):
    facts = extract_facts(text)
    by_id = {f.id: f for f in facts}
    if not facts:
        return
    masked = mask(text, facts)
    ids = sorted({h.fid for h in find_placeholders(masked)})
    a = audit(masked, by_id, required=set(ids))
    assert a.ok and not a.missing and not a.unexpected
    victim = data.draw(st.sampled_from(ids))
    deleted = masked.replace(f"⟦{victim}⟧", "")
    assert victim in audit(deleted, by_id, required=set(ids)).missing
    dup = masked + f" ⟦{victim}⟧"
    assert victim in audit(dup, by_id, required=set(ids)).duplicated
    invented = masked + " ⟦Z9⟧"
    assert "Z9" in audit(invented, by_id, required=set(ids)).unexpected


@settings(max_examples=100, deadline=None)
@given(letters(), st.lists(st.integers(1, 9), min_size=1, max_size=40))
def test_stream_unmasker_equals_batch(text, cuts):
    facts = extract_facts(text)
    by_id = {f.id: f for f in facts}
    masked = mask(text, facts)
    um = StreamUnmasker(by_id)
    out, i = [], 0
    for c in cuts * 50:
        if i >= len(masked):
            break
        out.append(um.feed(masked[i:i + c]))
        i += c
    out.append(um.feed(masked[i:]))
    out.append(um.flush())
    assert "".join(out) == unmask(masked, by_id)[0]


def test_tolerant_variants_are_repaired():
    facts = extract_facts("Bitte zahlen Sie CHF 80.00 bis 15.11.2026.")
    by_id = {f.id: f for f in facts}
    variants = "Zahlen Sie [A1] bis ⟦D1⟩ und 【A1】 oder ⟦D١⟧."
    a = audit(variants, by_id, required={"A1", "D1"})
    assert a.ok and set(a.repaired) == {"A1", "D1"}
    text, spans = unmask(variants, by_id)
    assert "CHF 80.00" in text and "15.11.2026" in text and "⟦" not in text
    assert all(text[s["start"]:s["end"]] == s["value"] for s in spans)


def test_unknown_bracket_tokens_ignored():
    facts = extract_facts("Bitte zahlen Sie CHF 80.00.")
    a = audit("Papierformat [A4] und ⟦A1⟧", {f.id: f for f in facts}, required={"A1"})
    assert a.ok and a.unexpected == []


def test_render_is_locale_safe():
    facts = extract_facts("bis 15. November 2026 zahlen Sie Fr. 1250.– innert zehn Tagen")
    by_id = {f.id: f for f in facts}
    out, _ = unmask("⟦D1⟧ ⟦A1⟧ ⟦N1⟧", by_id)
    assert out == "15.11.2026 CHF 1'250.00 10"


def test_strip_placeholders():
    assert strip_placeholders("bis ⟦D1⟧ zahlen [A2] Sie") == "bis zahlen Sie"
    assert not re.search(r"\d", strip_placeholders("⟦D1⟧ ⟦A12⟧"))
