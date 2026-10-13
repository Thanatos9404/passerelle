"""Draft a formal reply (in the authority's language) from the client's message (in their language).

Facts from the original letter keep their placeholders (``⟦R1⟧`` …); numbers the client writes
(dates, amounts, phone numbers — Arabic-Indic/Persian digits are normalised first) are locked as
``⟦K1⟧``, ``⟦K2⟧`` … so the model cannot alter them.  The draft always requires caseworker approval.
"""

from __future__ import annotations

import time

from .audit import get_audit_log
from .config import get_settings
from .extract import Analysis, facts_api
from .facts import Fact, extract_facts
from .factlock import audit, find_placeholders, mask, unmask
from .ingest import normalize_text, to_ascii_digits
from .languages import get_language
from .llm import LLMClient
from .prompts import reply_messages
from .verify import unexpected_numbers


def client_facts(message: str) -> list[Fact]:
    facts = extract_facts(message)
    out = []
    for i, f in enumerate(f for f in facts if f.type not in {"legal", "address", "url"}):
        f.id = f"K{i + 1}"
        f.source = "client"
        out.append(f)
    return out


def draft_reply(analysis: Analysis, client_message: str, client_lang: str, client: LLMClient) -> dict:
    t0 = time.perf_counter()
    get_language(client_lang)  # validates the code
    msg = normalize_text(to_ascii_digits(client_message))
    cfacts = client_facts(msg)
    client_masked = mask(msg, cfacts)
    masked_letter = mask(analysis.text, analysis.facts)
    refs = [f.id for f in analysis.facts if f.type == "reference"][:2]
    msgs = reply_messages(masked_letter, client_masked, client_lang, analysis.lang,
                          analysis.card.get("authority"), refs)
    res = client.chat(msgs, task="reply", max_tokens=get_settings().max_tokens_explain)
    all_facts = {**analysis.facts_by_id, **{f.id: f for f in cfacts}}
    pa = audit(res.text, all_facts, required=set(refs), offered=set(all_facts))
    letter, spans = unmask(res.text, all_facts)
    numbers = unexpected_numbers(letter, analysis.text + "\n" + msg, analysis.facts + cfacts,
                                 ignore_spans=[(s["start"], s["end"]) for s in spans])
    used_ids = {h.fid for h in find_placeholders(res.text, set(all_facts))}
    result = {
        "analysis_id": analysis.id,
        "letter_lang": analysis.lang,
        "client_lang": client_lang,
        "reply_letter": letter,
        "masked": res.text,
        "fact_spans": spans,
        "facts_used": [facts_api(f) for fid, f in all_facts.items() if fid in used_ids],
        "client_facts": [facts_api(f) for f in cfacts],
        "audit": {
            "placeholders": pa.to_dict(),
            "unexpected_numbers": numbers,
            "needs_caseworker_approval": True,
            "status": "draft" if pa.ok and not numbers else "draft_with_warnings",
        },
        "timings": {"total_ms": round((time.perf_counter() - t0) * 1000, 1)},
        "tokens": res.usage(),
    }
    get_audit_log().record(
        "reply", analysis_id=analysis.id, inputs={"client_message": msg, "reply": letter},
        meta={"client_lang": client_lang, "status": result["audit"]["status"], "missing": len(pa.missing)},
    )
    return result
