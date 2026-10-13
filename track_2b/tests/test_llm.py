"""OpenAI-compatible client: retries, JSON repair, response_format fallback, streaming, degeneration."""

import json

import httpx
import pytest

from passerelle.config import load_settings
from passerelle.llm import LLMClient, LLMError, is_degenerate, parse_json_lenient


def _ok(text, usage=True):
    body = {"choices": [{"message": {"content": text}, "finish_reason": "stop"}], "model": "m"}
    if usage:
        body["usage"] = {"prompt_tokens": 10, "completion_tokens": 5}
    return httpx.Response(200, json=body)


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:9/v1")
    monkeypatch.setenv("PASSERELLE_MAX_RETRIES", "3")
    monkeypatch.setenv("PASSERELLE_EGRESS_SOCKET_GUARD", "0")
    return load_settings()


def test_retries_on_5xx(settings, monkeypatch):
    monkeypatch.setattr("passerelle.llm.time.sleep", lambda s: None)
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(503, text="busy") if calls["n"] < 3 else _ok("hello")

    c = LLMClient(settings, transport=httpx.MockTransport(handler))
    r = c.chat([{"role": "user", "content": "hi"}], task="t")
    assert r.text == "hello" and r.attempts == 3 and r.prompt_tokens == 10


def test_gives_up_after_retries(settings, monkeypatch):
    monkeypatch.setattr("passerelle.llm.time.sleep", lambda s: None)
    c = LLMClient(settings, transport=httpx.MockTransport(lambda r: httpx.Response(500, text="err")))
    with pytest.raises(LLMError):
        c.chat([{"role": "user", "content": "hi"}], task="t")


def test_task_header_and_auth(settings, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    s = load_settings()
    seen = {}

    def handler(request):
        seen.update(request.headers)
        seen["body"] = json.loads(request.content)
        return _ok("x")

    LLMClient(s, transport=httpx.MockTransport(handler)).chat([{"role": "user", "content": "q"}], task="extract")
    assert seen["authorization"] == "Bearer sk-test"
    assert seen["x-passerelle-task"] == "extract"
    assert seen["body"]["model"] == s.llm_name and seen["body"]["seed"] == 7


def test_json_schema_fallback_and_repair(settings):
    modes = []

    def handler(request):
        body = json.loads(request.content)
        rf = body.get("response_format")
        modes.append(rf["type"] if rf else None)
        if rf and rf["type"] == "json_schema":
            return httpx.Response(400, text="response_format not supported")
        return _ok('Sure! ```json\n{"a": 1, "b": [1,2,],}\n```')

    obj, res = LLMClient(settings, transport=httpx.MockTransport(handler)).chat_json(
        [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}], task="extract", schema={"type": "object"})
    assert obj == {"a": 1, "b": [1, 2]}
    assert modes[:2] == ["json_schema", "json_object"]


def test_model_side_repair_round(settings):
    answers = iter(["not json at all", '{"ok": true}'])
    c = LLMClient(settings, transport=httpx.MockTransport(lambda r: _ok(next(answers))))
    c._json_mode = "off"
    obj, res = c.chat_json([{"role": "system", "content": "s"}, {"role": "user", "content": "u"}], task="x", schema={})
    assert obj == {"ok": True} and res.extra["repair_attempted"]


@pytest.mark.parametrize("raw,expected", [
    ('{"a": "b"}', {"a": "b"}),
    ("```json\n{\"a\": 1}\n```", {"a": 1}),
    ("Here: {'a': 'b'}", {"a": "b"}),
    ('{"a": True, "b": None}', {"a": True, "b": None}),
    ('{"a": [1, 2', {"a": [1, 2]}),          # truncated output closed heuristically
    ("{a: 1}", {"a": 1}),
    ("no json", None),
])
def test_parse_json_lenient(raw, expected):
    assert parse_json_lenient(raw) == expected


def test_streaming_and_special_tokens(settings):
    chunks = ["Hal", "lo ", "Welt<|assistant_end|>"]
    lines = "".join(f"data: {json.dumps({'choices': [{'delta': {'content': c}}]})}\n\n" for c in chunks)
    lines += "data: " + json.dumps({"choices": [{"delta": {}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 3, "completion_tokens": 3}}) + "\n\n"
    lines += "data: [DONE]\n\n"
    c = LLMClient(settings, transport=httpx.MockTransport(lambda r: httpx.Response(200, text=lines)))
    out = "".join(c.chat_stream([{"role": "user", "content": "x"}], task="t"))
    assert out.startswith("Hallo Welt")
    assert c.last_stream.text == "Hallo Welt" and c.last_stream.completion_tokens == 3


def test_stream_stops_on_degenerate(settings):
    rep = ["ዝተወሰነ "] * 200
    lines = "".join(f"data: {json.dumps({'choices': [{'delta': {'content': c}}]})}\n\n" for c in rep) + "data: [DONE]\n\n"
    c = LLMClient(settings, transport=httpx.MockTransport(lambda r: httpx.Response(200, text=lines)))
    res = c.chat_guarded([{"role": "user", "content": "x"}], task="t")
    assert res.finish_reason == "degenerate" and res.completion_tokens < 200


def test_is_degenerate():
    assert is_degenerate("abc " + "ዝተወሰነ " * 12)
    assert is_degenerate(" ".join(["ok"] * 100))
    assert not is_degenerate("Dies ist ein ganz normaler Text mit verschiedenen Wörtern und Sätzen. " * 2)
