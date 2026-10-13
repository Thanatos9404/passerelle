"""Confidence gate logic and verification helpers."""

from passerelle.facts import extract_facts
from passerelle.languages import check_output_language, script_ratio
from passerelle.verify import chrf, decide, unexpected_numbers

TH = {"ready": 50.0, "review": 35.0, "floor": "ready", "calibrated": True}
OK_AUDIT = {"missing": [], "unexpected": [], "duplicated": []}
OK_SCRIPT = {"ok": True}


def test_ready_when_everything_passes():
    g = decide("ar", 70.0, OK_AUDIT, [], OK_SCRIPT, TH)
    assert g["status"] == "ready" and g["label"] == "Ready"


def test_borderline_chrf_is_review_and_low_is_interpreter():
    assert decide("ar", 45.0, OK_AUDIT, [], OK_SCRIPT, TH)["status"] == "review"
    assert decide("ar", 20.0, OK_AUDIT, [], OK_SCRIPT, TH)["status"] == "interpreter"


def test_missing_fact_requires_review():
    g = decide("ar", 80.0, {**OK_AUDIT, "missing": ["D1"]}, [], OK_SCRIPT, TH)
    assert g["status"] == "review" and any(r["code"] == "fact_missing" for r in g["details"])


def test_unexpected_numbers_and_placeholders_require_review():
    assert decide("ar", 80.0, OK_AUDIT, ["2027"], OK_SCRIPT, TH)["status"] == "review"
    assert decide("ar", 80.0, {**OK_AUDIT, "unexpected": ["D9"]}, [], OK_SCRIPT, TH)["status"] == "review"


def test_duplicates_are_informational():
    g = decide("ar", 80.0, {**OK_AUDIT, "duplicated": ["A1"]}, [], OK_SCRIPT, TH)
    assert g["status"] == "ready" and any(r["severity"] == "info" for r in g["details"])


def test_wrong_script_and_degenerate_go_to_interpreter():
    assert decide("ti", 90.0, OK_AUDIT, [], {"ok": False}, TH)["status"] == "interpreter"
    assert decide("ti", 90.0, OK_AUDIT, [], OK_SCRIPT, TH, degenerate=True)["status"] == "interpreter"


def test_language_floor():
    g = decide("ti", 95.0, OK_AUDIT, [], OK_SCRIPT, {**TH, "floor": "interpreter"})
    assert g["status"] == "interpreter" and g["details"][-1]["code"] == "language_floor"


def test_status_never_decreases():
    g = decide("so", 10.0, {**OK_AUDIT, "missing": ["A1"]}, ["99"], {"ok": False}, {**TH, "floor": "review"})
    assert g["status"] == "interpreter"


def test_chrf_bounds():
    assert chrf("Sie müssen bezahlen.", "Sie müssen bezahlen.") == 100.0
    assert chrf("", "x") == 0.0
    assert 0 < chrf("Sie müssen zahlen.", "Sie müssen bezahlen.") < 100


def test_unexpected_numbers():
    src = "Bitte zahlen Sie CHF 1'250.50 bis 15.11.2026."
    facts = extract_facts(src)
    assert unexpected_numbers("Pay CHF 1250.50 by 15/11/2026, 2026-11-15", src, facts) == []
    assert unexpected_numbers("Pay CHF 1350.50 by 16.11.2026", src, facts) == ["1350.50", "16.11.2026"]
    assert unexpected_numbers("ادفع ١٢٥٠٫٥٠ فرنك", src, facts) == []  # Arabic-Indic digits normalised


def test_script_check():
    assert script_ratio("ይህ ደብዳቤ ነው", "Ethi") > 0.9
    assert check_output_language("هذه رسالة رسمية من المكتب", "ar", "de")["ok"]
    assert not check_output_language("Das ist ein Brief vom Amt.", "ar", "de")["ok"]
    assert not check_output_language("Das ist ein Brief und Sie müssen bis Montag die Rechnung bezahlen.", "so", "de")["ok"]
    assert check_output_language("Waraaqdan waa amar lacag bixin ah oo aad ku bixinayso lacagta.", "so", "de")["ok"]
