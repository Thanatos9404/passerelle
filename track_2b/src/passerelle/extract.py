"""Fact-card extraction: deterministic Swiss-format facts + Apertus structured extraction, merged.

Merge policy (documented in the technical report):
* Every value Apertus reports is *grounded*: it must match a deterministic fact (same type and
  normalised value) or occur verbatim in the letter.  Ungrounded values are dropped and reported
  as a ``disagreement`` — the model can label and explain, but it cannot introduce a number.
* Apertus contributes what regexes cannot: roles (which date is the deadline / appointment),
  letter type, required action, documents, consequences, purposes of amounts.
* If both sides assign a different role to the same date, Apertus wins and a disagreement is flagged.
* If the LLM is unreachable the card degrades to rules-only (with keyword letter-type guess).
"""

from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import date

from . import facts as F
from .facts import Fact, extract_facts, mark_critical, render_fact
from .ingest import detect_language, normalize_text
from .llm import LLMClient, LLMError
from .prompts import EXTRACT_SCHEMA, LETTER_TYPES, extraction_messages

_TYPE_KEYWORDS = {
    "debt_collection": r"zahlungsbefehl|betreibung|commandement de payer|poursuite|precetto esecutivo|esecuzione",
    "tax_reminder": r"steuererklärung|mahnung.*steuer|déclaration d['’]impôt|dichiarazione d['’]imposta|richiamo",
    "premium_reduction": r"prämienverbilligung|ipv\b|réduction (?:individuelle )?des primes|riduzione (?:individuale )?dei premi",
    "permit_renewal": r"aufenthaltsbewilligung|ausländerausweis|permis de séjour|permesso di dimora|rinnovo del permesso",
    "social_assistance_appointment": r"sozialhilfe|sozialdienst|aide sociale|service social|assistenza sociale|servizio sociale",
    "school_enrolment": r"einschulung|kindergarten|schuleintritt|scolarisation|école enfantine|scuola dell['’]infanzia|iscrizione scolastica",
    "rent_increase": r"mietzins|loyer|pigione|canone di locazione",
    "ahv_contributions": r"ahv-beiträge|beiträge.*nichterwerbstätig|cotisations avs|contributi avs",
    "family_allowance": r"familienzulage|kinderzulage|allocations familiales|assegni familiari",
    "health_insurance_reminder": r"krankenkasse|krankenversicherung|caisse[- ]maladie|assurance[- ]maladie|cassa malati|assicurazione malattie",
    "asylum_interview": r"anhörung|asylgesuch|audition|demande d['’]asile|audizione|domanda d['’]asilo",
    "fine_notice": r"ordnungsbusse|busse\b|amende|multa",
}


def guess_letter_type(text: str) -> str:
    low = text.lower()
    best, score = "other", 0
    for t, rx in _TYPE_KEYWORDS.items():
        n = len(re.findall(rx, low))
        if n > score:
            best, score = t, n
    return best


@dataclass
class Analysis:
    id: str
    text: str
    lang: str
    facts: list[Fact]
    card: dict
    disagreements: list[dict]
    timings: dict
    tokens: dict
    llm_ok: bool
    llm_error: str | None = None
    llm_raw: dict | None = None
    rule_facts: list[Fact] = field(default_factory=list)
    sample_id: str | None = None
    created: float = field(default_factory=time.time)
    cache: dict = field(default_factory=dict)  # per-language source plain explanation etc.

    @property
    def facts_by_id(self) -> dict[str, Fact]:
        return {f.id: f for f in self.facts}

    def to_api(self) -> dict:
        return {
            "analysis_id": self.id,
            "letter_lang": self.lang,
            "text": self.text,
            "sample_id": self.sample_id,
            "fact_card": self.card,
            "facts": [facts_api(f) for f in self.facts],
            "disagreements": [_disagreement_api(d) for d in self.disagreements],
            "llm_ok": self.llm_ok,
            "llm_error": self.llm_error,
            "timings": self.timings,
            "tokens": self.tokens,
        }


def _disagreement_api(d: dict) -> dict:
    """Original fields plus the generic {field, deterministic, llm, note} view used by the UI."""
    return {**d, "field": d.get("type") or d.get("kind"), "deterministic": d.get("rule_value"),
            "llm": d.get("llm_value"), "note": d.get("message")}


def facts_api(f: Fact) -> dict:
    return {
        "id": f.id, "type": f.type, "value": f.value, "normalized": f.normalized, "display": render_fact(f),
        "span": list(f.span), "spans": [list(s) for s in f.spans], "role": f.role, "critical": f.critical,
        "source": "deterministic" if f.source == "rule" else f.source, "meta": {k: v for k, v in f.meta.items() if isinstance(v, (str, int, float, bool))},
    }


# ----------------------------------------------------------------------------- grounding

def _normalize(ftype: str, raw: str, ref: date | None) -> str | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    if ftype == "date":
        return F.parse_date_text(raw, ref)
    if ftype == "amount":
        # A money amount must carry a currency marker or be a plain number (matched against rule facts
        # only); "5 %" or "10 Tage" are not amounts.
        if "%" in raw or re.search(r"[A-Za-zäöüéè]", re.sub(r"(?i)CHF|SFr\.?|Fr\.|Franken|francs?|franchi", "", raw)):
            return None
        return F.parse_amount_text(raw)
    if ftype == "time":
        return F.parse_time_text(raw)
    if ftype == "iban":
        c = re.sub(r"\s", "", raw).upper()
        return c if re.fullmatch(r"(CH|LI)\d{2}[0-9A-Z]{17}", c) else None
    if ftype == "ahv":
        d = re.sub(r"\D", "", raw)
        return F.format_ahv(d) if len(d) == 13 else None
    if ftype == "phone":
        return F.normalize_phone(raw)
    if ftype == "email":
        return raw.lower()
    if ftype == "reference":
        return F.normalize_reference(raw)
    return re.sub(r"\s+", " ", raw)


def _locate(text: str, raw: str) -> tuple[int, int] | None:
    raw = raw.strip()
    if len(raw) < 2:
        return None
    pattern = r"\s*".join(re.escape(p) for p in raw.split())
    m = re.search(pattern, text, re.IGNORECASE)
    return (m.start(), m.end()) if m else None


class _Merger:
    def __init__(self, text: str, facts: list[Fact], ref: date | None):
        self.text, self.facts, self.ref = text, facts, ref
        self.disagreements: list[dict] = []

    def _next_id(self, ftype: str) -> str:
        n = sum(1 for f in self.facts if f.type == ftype)
        return f"{F.PREFIX[ftype]}{n + 1}"

    def ground(self, ftype: str, raw, role: str | None = None) -> Fact | None:
        if raw is None or not str(raw).strip():
            return None
        raw = str(raw)
        norm = _normalize(ftype, raw, self.ref)
        match = None
        if norm:
            for f in self.facts:
                if f.type == ftype and f.normalized == norm:
                    match = f
                    break
            if match is None and ftype == "reference":
                compact = re.sub(r"[\s.\-/]", "", norm)
                for f in self.facts:
                    fc = re.sub(r"[\s.\-/]", "", f.normalized)
                    # same value, or the model copied the label too ("Betreibung Nr. 26-104523")
                    if f.type == "reference" and (fc == compact or (len(fc) >= 4 and compact.endswith(fc))):
                        match = f
                        break
        if match is not None:
            if match.source == "rule":
                match.source = "both"
            if role and role != "other":
                if match.role in {"deadline", "appointment"} and role != match.role and ftype == "date":
                    self.disagreements.append({
                        "kind": "role_conflict", "type": ftype, "fact_id": match.id, "rule_value": match.role,
                        "llm_value": role, "message": f"Rules read {match.id} as {match.role}, Apertus as {role}; using Apertus.",
                    })
                match.role = role
            return match
        span = _locate(self.text, raw)
        if span and norm:
            if any(not (span[1] <= s or span[0] >= e) for f in self.facts for s, e in f.spans):
                self.disagreements.append({
                    "kind": "overlap", "type": ftype, "llm_value": raw,
                    "message": "Apertus value overlaps a different rule-based fact; kept the rule-based one.",
                })
                return None
            f = Fact(id=self._next_id(ftype), type=ftype, value=self.text[span[0]:span[1]], normalized=norm,
                     span=span, spans=[span], source="llm", role=role if role != "other" else None)
            self.facts.append(f)
            self.disagreements.append({
                "kind": "llm_only", "type": ftype, "fact_id": f.id, "llm_value": raw,
                "message": "Found by Apertus only (no rule matched); verify.",
            })
            return f
        self.disagreements.append({
            "kind": "ungrounded", "type": ftype, "llm_value": raw,
            "message": "Apertus reported a value that does not appear in the letter; ignored.",
        })
        return None


def merge(text: str, rule_facts: list[Fact], llm: dict | None) -> tuple[list[Fact], dict, list[dict]]:
    facts = [Fact(**{**f.__dict__, "spans": list(f.spans), "meta": dict(f.meta)}) for f in rule_facts]
    letter_date = next((f for f in facts if f.role == "letter_date"), None)
    ref = date.fromisoformat(letter_date.normalized) if letter_date else None
    m = _Merger(text, facts, ref)
    llm = llm or {}
    amount_purpose: dict[str, str] = {}
    if llm:
        rule_deadlines = {f.id for f in facts if f.type == "date" and f.role == "deadline"}
        llm_deadlines = set()
        for d in llm.get("dates") or []:
            if isinstance(d, dict):
                f = m.ground("date", d.get("text"), d.get("role"))
                if f and d.get("role") == "deadline":
                    llm_deadlines.add(f.id)
        for fid in sorted(rule_deadlines - llm_deadlines):
            f = next(x for x in facts if x.id == fid)
            if f.role == "deadline" and llm_deadlines:
                m.disagreements.append({
                    "kind": "deadline_conflict", "type": "date", "fact_id": fid, "rule_value": "deadline",
                    "llm_value": None, "message": f"Rules consider {fid} a deadline; Apertus chose another date.",
                })
        for t in llm.get("times") or []:
            m.ground("time", t, "appointment")
        for a in llm.get("amounts") or []:
            if isinstance(a, dict):
                f = m.ground("amount", a.get("text"))
                if f and a.get("purpose"):
                    amount_purpose[f.id] = str(a["purpose"])[:80]
        for r in llm.get("references") or []:
            m.ground("reference", r)
        m.ground("iban", llm.get("iban"))
        m.ground("ahv", llm.get("ahv_number"))
        for p in llm.get("phones") or []:
            m.ground("phone", p, "contact")
        for e in llm.get("emails") or []:
            m.ground("email", e)
        place = llm.get("appointment_place")
        if place:
            for f in facts:
                if f.type == "address" and f.normalized.lower() in str(place).lower():
                    f.role = "appointment_place"
        rel = llm.get("deadline_relative")
        if rel:
            span = _locate(text, str(rel))
            for f in facts:
                if f.type == "duration" and span and span[0] <= f.span[0] < span[1]:
                    f.role = "deadline"
                    f.meta["deadline"] = True
    for f in facts:
        if f.id in amount_purpose:
            f.meta["purpose"] = amount_purpose[f.id]
    mark_critical(facts, letter_date.normalized if letter_date else None)
    facts.sort(key=lambda f: f.span[0])
    card = build_card(text, facts, llm)
    return facts, card, m.disagreements


def build_card(text: str, facts: list[Fact], llm: dict | None) -> dict:
    llm = llm or {}
    today = date.today()

    def disp(f: Fact | None) -> dict | None:
        if f is None:
            return None
        return {"value": render_fact(f), "normalized": f.normalized, "fact_id": f.id}

    dates = [f for f in facts if f.type == "date"]
    letter_date = next((f for f in dates if f.role == "letter_date"), None)
    deadlines = sorted([f for f in dates if f.role == "deadline"], key=lambda f: f.normalized)
    deadline = None
    if deadlines:
        d0 = deadlines[0]
        deadline = {"date": d0.normalized, "display": render_fact(d0), "fact_id": d0.id, "text": d0.value,
                    "days_left": (date.fromisoformat(d0.normalized) - today).days, "relative": None}
    else:
        dur = next((f for f in facts if f.type == "duration" and f.role == "deadline"), None)
        if dur:
            deadline = {"date": None, "display": None, "fact_id": dur.id, "text": llm.get("deadline_relative") or dur.value,
                        "days_left": None, "relative": dur.normalized}
    appt_dates = [f for f in dates if f.role == "appointment"]
    appointment = None
    if appt_dates:
        a0 = sorted(appt_dates, key=lambda f: f.normalized)[0]
        t0 = next((f for f in facts if f.type == "time" and 0 <= f.span[0] - a0.span[1] < 40), None) or \
            next((f for f in facts if f.type == "time"), None)
        place = next((f for f in facts if f.type == "address" and f.role == "appointment_place"), None)
        appointment = {
            "date": a0.normalized, "display": render_fact(a0), "time": t0.normalized if t0 else None,
            "place": render_fact(place) if place else llm.get("appointment_place"),
            "fact_ids": [x.id for x in (a0, t0, place) if x],
            "days_left": (date.fromisoformat(a0.normalized) - today).days,
        }
    phones = [f for f in facts if f.type == "phone" and f.role != "fax"]
    emails = [f for f in facts if f.type == "email"]
    deadline_list = [{"label": "deadline", "date": f.normalized, "display": render_fact(f), "relative": None, "fact_id": f.id}
                     for f in deadlines]
    for dur in (f for f in facts if f.type == "duration" and f.role == "deadline"):
        deadline_list.append({"label": "relative deadline", "date": None, "display": None,
                              "relative": f"{dur.value} {dur.meta.get('unit_text', '')}".strip(), "normalized": dur.normalized,
                              "fact_id": dur.id})
    addresses = [f for f in facts if f.type == "address"]
    hours = [f for f in facts if f.type == "time" and f.role != "appointment"]
    return {
        "authority": llm.get("authority"),
        "letter_type": llm.get("letter_type") if llm.get("letter_type") in LETTER_TYPES else guess_letter_type(text),
        "subject": llm.get("subject"),
        "summary": llm.get("summary"),
        "action_required": llm.get("action_required"),
        "required_action": llm.get("action_required"),
        "documents": [str(d) for d in (llm.get("documents") or [])][:12],
        "consequences": llm.get("consequences"),
        "letter_date": letter_date.normalized if letter_date else None,
        "deadline": deadline,
        "deadlines": deadline_list,
        "appointment": appointment,
        "amounts": [{"value": f.normalized, "display": render_fact(f), "purpose": f.meta.get("purpose"),
                     "label": f.meta.get("purpose") or "amount", "currency": "CHF", "fact_id": f.id}
                    for f in facts if f.type == "amount"],
        "references": [{"value": f.value, "label": f.meta.get("label"), "fact_id": f.id} for f in facts if f.type == "reference"],
        "iban": disp(next((f for f in facts if f.type == "iban"), None)),
        "ahv_number": disp(next((f for f in facts if f.type == "ahv"), None)),
        "contact": {
            "person": llm.get("contact_person"),
            "name": llm.get("contact_person") or llm.get("authority"),
            "address": ", ".join(render_fact(f) for f in addresses[:2]) or None,
            "hours": " – ".join(render_fact(f) for f in hours[:2]) or None,
            "phone": render_fact(phones[0]) if phones else None,
            "email": emails[0].normalized if emails else None,
            "fact_ids": [f.id for f in phones[:1] + emails[:1]],
        },
        "source": "merged" if llm else "rules_only",
    }


# ----------------------------------------------------------------------------- pipeline

def llm_extract(text: str, client: LLMClient, lang: str = "de") -> tuple[dict, dict]:
    from .config import get_settings

    obj, res = client.chat_json(extraction_messages(text, lang), task="extract", schema=EXTRACT_SCHEMA,
                                max_tokens=get_settings().max_tokens_extract)
    return obj, res.usage()


def analyze(text: str, *, source_lang: str | None = None, client: LLMClient | None = None,
            use_llm: bool = True, sample_id: str | None = None) -> Analysis:
    t0 = time.perf_counter()
    text = normalize_text(text)
    lang = source_lang if source_lang in {"de", "fr", "it"} else detect_language(text)
    rule_facts = extract_facts(text, lang)
    t_rules = (time.perf_counter() - t0) * 1000
    llm_obj, usage, err = None, {}, None
    t1 = time.perf_counter()
    if use_llm and client is not None:
        try:
            llm_obj, usage = llm_extract(text, client, lang)
        except (LLMError, Exception) as exc:  # degrade gracefully; never lose the rule-based card
            err = f"{type(exc).__name__}: {exc}"[:300]
    t_llm = (time.perf_counter() - t1) * 1000
    facts, card, disagreements = merge(text, rule_facts, llm_obj)
    return Analysis(
        id=uuid.uuid4().hex[:12],
        text=text,
        lang=lang,
        facts=facts,
        card=card,
        disagreements=disagreements,
        timings={"rules_ms": round(t_rules, 1), "llm_ms": round(t_llm, 1), "total_ms": round((time.perf_counter() - t0) * 1000, 1)},
        tokens={"prompt": usage.get("prompt"), "completion": usage.get("completion")},
        llm_ok=llm_obj is not None,
        llm_error=err,
        llm_raw=llm_obj,
        rule_facts=rule_facts,
        sample_id=sample_id,
    )
