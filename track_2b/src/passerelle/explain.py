"""Plain-language explanation in the client's language, with fact-lock and round-trip verification.

Pipeline for one (letter, target language):

1. ``source_plain`` – Apertus rewrites the *masked* letter as a plain-language (CEFR A2)
   explanation in the letter's own language (DE/FR/IT) with five fixed headings.  Cached per
   analysis; the caseworker can read it.  If a critical placeholder is missing, a deterministic
   "Key facts" line is appended so no critical fact can be lost before translation.
2. ``translate`` – Apertus translates that masked text into the target language (streamable).
3. ``back_translate`` – Apertus translates the target text back into the letter's language.
4. ``verify`` – chrF(back-translation, step-1 text) with placeholders stripped, placeholder audit,
   number audit, script/language check → confidence gate (verify.decide).
5. ``unmask`` – placeholders are replaced by verified, locale-safe renderings of the facts.
"""

from __future__ import annotations

import time
from collections.abc import Iterator

from .audit import get_audit_log
from .config import get_settings
from .extract import Analysis
from .factlock import StreamUnmasker, audit, find_placeholders, mask, strip_placeholders, unmask
from .languages import check_output_language, get_language
from .llm import LLMClient
from .prompts import back_translate_messages, plain_messages, translate_messages
from .verify import chrf, decide, unexpected_numbers

KEY_FACTS_LABEL = {"de": "Wichtige Angaben", "fr": "Informations importantes", "it": "Informazioni importanti", "en": "Key facts"}


def source_plain(analysis: Analysis, client: LLMClient) -> dict:
    """Plain-language explanation in the letter's language (masked). Cached on the analysis."""
    if "plain" in analysis.cache:
        return analysis.cache["plain"]
    s = get_settings()
    by_id = analysis.facts_by_id
    critical = [f.id for f in analysis.facts if f.critical]
    masked_letter = mask(analysis.text, analysis.facts)
    res = client.chat(plain_messages(masked_letter, analysis.facts, critical, analysis.lang),
                      task="explain_source", max_tokens=s.max_tokens_explain)
    text = res.text
    a = audit(text, by_id, required=set(critical), offered=set(by_id))
    repaired = list(a.missing)
    if repaired:
        label = KEY_FACTS_LABEL.get(analysis.lang, "Key facts")
        text = text.rstrip() + f"\n{label}: " + ", ".join(f"⟦{i}⟧" for i in repaired)
    out = {
        "masked": text,
        "masked_letter": masked_letter,
        "required": critical,
        "repaired_missing": repaired,
        "audit": a.to_dict(),
        "usage": res.usage(),
    }
    analysis.cache["plain"] = out
    return out


def _ids_in(text: str, known: set[str]) -> set[str]:
    return {h.fid for h in find_placeholders(text, known) if h.fid in known}


def explain_events(analysis: Analysis, target_lang: str, client: LLMClient, stream: bool = False) -> Iterator[tuple[str, dict]]:
    """Yield (event, payload) pairs; the last event is ("result", full_response)."""
    s = get_settings()
    tgt = get_language(target_lang)
    src_code = analysis.lang
    by_id = analysis.facts_by_id
    t0 = time.perf_counter()
    timings: dict[str, float] = {}
    tokens: dict[str, dict] = {}

    yield "stage", {"stage": "source_plain", "message": "Writing the plain-language version"}
    t = time.perf_counter()
    plain = source_plain(analysis, client)
    timings["source_plain_ms"] = round((time.perf_counter() - t) * 1000, 1)
    tokens["source_plain"] = plain["usage"]
    p_masked = plain["masked"]
    yield "source_plain", {"text": unmask(p_masked, by_id)[0], "masked": p_masked}

    in_src = _ids_in(p_masked, set(by_id))
    critical = {f.id for f in analysis.facts if f.critical}
    same_language = tgt.code == src_code

    degenerate = False
    if same_language:
        t_masked = p_masked
        back_masked = None
        score = None
    else:
        yield "stage", {"stage": "translate", "message": f"Translating into {tgt.name}"}
        t = time.perf_counter()
        msgs = translate_messages(p_masked, src_code, tgt.code)
        # cap the length relative to the source (scripts like Ge'ez need ~3-5x more tokens)
        src_tokens = (plain["usage"].get("completion") or len(p_masked) // 3) or 200
        cap = int(min(s.max_tokens_translate, 160 + 6 * src_tokens))
        if stream:
            um = StreamUnmasker(by_id)
            for delta in client.chat_stream(msgs, task="translate", max_tokens=cap):
                ready = um.feed(delta)
                if ready:
                    yield "token", {"text": ready}
            tail = um.flush()
            if tail:
                yield "token", {"text": tail}
            res = client.last_stream
        else:
            res = client.chat_guarded(msgs, task="translate", max_tokens=cap)
        t_masked = res.text
        degenerate = res.finish_reason in {"degenerate", "length"}
        timings["translate_ms"] = round((time.perf_counter() - t) * 1000, 1)
        tokens["translate"] = res.usage()

        yield "stage", {"stage": "back_translate", "message": "Checking the meaning (back-translation)"}
        t = time.perf_counter()
        if res.finish_reason == "degenerate":
            back_masked, score = "", 0.0   # no point in back-translating a repetition loop
        else:
            bres = client.chat_guarded(back_translate_messages(t_masked, tgt.code, src_code), task="back_translate",
                                       max_tokens=int(min(s.max_tokens_translate, 200 + 2 * src_tokens)))
            back_masked = bres.text
            tokens["back_translate"] = bres.usage()
            score = chrf(strip_placeholders(back_masked), strip_placeholders(p_masked))
        timings["back_translate_ms"] = round((time.perf_counter() - t) * 1000, 1)

    yield "stage", {"stage": "verify", "message": "Verifying facts and meaning"}
    t = time.perf_counter()
    pa = audit(t_masked, by_id, required=in_src & critical, offered=in_src)
    explanation, spans = unmask(t_masked, by_id)
    numbers = unexpected_numbers(explanation, analysis.text, analysis.facts,
                                 ignore_spans=[(sp["start"], sp["end"]) for sp in spans])
    script = check_output_language(strip_placeholders(t_masked), tgt.code, src_code)
    gate = decide(tgt.code, score, pa.to_dict(), numbers, script, degenerate=degenerate)
    timings["verify_ms"] = round((time.perf_counter() - t) * 1000, 1)
    timings["total_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    back_unmasked = unmask(back_masked, by_id)[0] if back_masked is not None else None
    total_prompt = sum((u.get("prompt") or 0) for u in tokens.values())
    total_completion = sum((u.get("completion") or 0) for u in tokens.values())
    result = {
        "analysis_id": analysis.id,
        "letter_lang": src_code,
        "target_lang": tgt.code,
        "target_name": tgt.name,
        "target_native": tgt.native,
        "rtl": tgt.rtl,
        "same_language": same_language,
        "explanation": explanation,
        "masked": t_masked,
        "fact_spans": spans,
        "source_plain": unmask(p_masked, by_id)[0],
        "source_explanation": unmask(p_masked, by_id)[0],
        "source_plain_masked": p_masked,
        "source_plain_repaired": plain["repaired_missing"],
        "back_translation": back_unmasked,
        "back_translation_masked": back_masked,
        "chrf": score,
        "placeholder_audit": pa.to_dict(),
        "number_audit": {"unexpected_numbers": numbers},
        "script_check": script,
        "degenerate": degenerate,
        "gate": gate,
        "timings": timings,
        "tokens": {"prompt": total_prompt, "completion": total_completion, "by_step": tokens},
        "model": get_settings().llm_name,
    }
    get_audit_log().record(
        "explain", analysis_id=analysis.id,
        inputs={"letter": analysis.text, "explanation": explanation, "back_translation": back_unmasked or ""},
        meta={"target_lang": tgt.code, "gate": gate["status"], "chrf": score, "missing": len(pa.missing),
              "unexpected_numbers": len(numbers), "model": get_settings().llm_name[:40]},
    )
    yield "result", result


def explain(analysis: Analysis, target_lang: str, client: LLMClient) -> dict:
    result: dict = {}
    for event, payload in explain_events(analysis, target_lang, client, stream=False):
        if event == "result":
            result = payload
    return result
