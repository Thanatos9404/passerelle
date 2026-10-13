"""Minimal OpenAI-compatible chat client (llama.cpp server, Ollama, LM Studio, vLLM, gateways).

* The model's own chat template is applied server-side: we only send ``messages``.
* Retries with exponential backoff on transport errors, 429 and 5xx.
* JSON mode: ``response_format`` json_schema (grammar-constrained on llama.cpp/Ollama/vLLM);
  if the server rejects it we fall back to json_object, then to prompt-only JSON, and always
  run a tolerant parser + one model-side repair round.
* Every request passes the egress guard.
"""

from __future__ import annotations

import json
import random
import re
import time
from collections.abc import Iterator
from dataclasses import dataclass, field

import httpx

from . import egress
from .config import Settings, get_settings


class LLMError(RuntimeError):
    pass


@dataclass
class LLMResult:
    text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: float = 0.0
    model: str = ""
    finish_reason: str | None = None
    attempts: int = 1
    extra: dict = field(default_factory=dict)

    def usage(self) -> dict:
        return {"prompt": self.prompt_tokens, "completion": self.completion_tokens, "latency_ms": round(self.latency_ms, 1)}


_RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}
_SPECIAL_TOKENS = re.compile(r"<\|(?:assistant|user|system|developer)_(?:start|end)\|>|<\|inner_(?:prefix|suffix)\|>")


_REPEAT_TAIL = re.compile(r"(.{2,40}?)(?:\s*\1){7,}\s*$", re.S)


def is_degenerate(text: str) -> bool:
    """Detect the repetition loops small models fall into on low-resource languages."""
    tail = text[-600:]
    if len(tail) >= 40 and _REPEAT_TAIL.search(tail):
        return True
    words = text.split()
    if len(words) >= 80:
        window = words[-80:]
        if len(set(window)) / len(window) < 0.15:
            return True
    return False


def clean_output(text: str) -> str:
    """Remove chat-template artefacts some servers leak, and surrounding delimiters."""
    text = _SPECIAL_TOKENS.sub("", text or "")
    text = text.strip()
    for a, b in (("<<<", ">>>"),):
        if text.startswith(a):
            text = text[len(a):]
        if text.endswith(b):
            text = text[: -len(b)]
    return text.strip()


class LLMClient:
    def __init__(self, settings: Settings | None = None, transport: httpx.BaseTransport | None = None):
        self.s = settings or get_settings()
        egress.configure(self.s.llm_base_url, self.s.egress_allow)
        headers = {"Content-Type": "application/json"}
        if self.s.llm_api_key and self.s.llm_api_key.lower() not in {"none", "-", ""}:
            headers["Authorization"] = f"Bearer {self.s.llm_api_key}"
        self._http = httpx.Client(
            base_url=self.s.llm_base_url,
            headers=headers,
            timeout=httpx.Timeout(self.s.timeout_s, connect=10.0),
            transport=transport,
            trust_env=False,
        )
        self._json_mode = self.s.json_mode  # may degrade at runtime: schema -> object -> off

    # ------------------------------------------------------------------ core
    def _payload(self, messages, *, max_tokens, temperature, stop, stream, response_format=None) -> dict:
        p = {
            "model": self.s.llm_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": self.s.temperature if temperature is None else temperature,
            "stream": stream,
        }
        if self.s.seed is not None:
            p["seed"] = self.s.seed
        if stop:
            p["stop"] = stop
        if response_format:
            p["response_format"] = response_format
        if stream:
            p["stream_options"] = {"include_usage": True}
        return p

    def _headers(self, task: str) -> dict:
        return {"X-Passerelle-Task": task} if self.s.send_task_header else {}

    def _post(self, payload: dict, task: str) -> httpx.Response:
        url = self.s.llm_base_url + "/chat/completions"
        egress.check_url(url)
        last_exc: Exception | None = None
        for attempt in range(1, self.s.max_retries + 2):
            try:
                r = self._http.post("/chat/completions", json=payload, headers=self._headers(task))
                if r.status_code in _RETRY_STATUS and attempt <= self.s.max_retries:
                    last_exc = LLMError(f"HTTP {r.status_code}: {r.text[:200]}")
                else:
                    r.attempts = attempt  # type: ignore[attr-defined]
                    return r
            except egress.EgressBlocked:
                raise
            except httpx.TransportError as exc:
                last_exc = exc
                if attempt > self.s.max_retries:
                    break
            time.sleep(min(8.0, 0.5 * 2 ** (attempt - 1)) + random.random() * 0.25)
        raise LLMError(f"LLM request failed after {self.s.max_retries + 1} attempts: {last_exc}")

    def chat(self, messages: list[dict], *, task: str, max_tokens: int = 800, temperature: float | None = None,
             stop: list[str] | None = None, response_format: dict | None = None) -> LLMResult:
        t0 = time.perf_counter()
        payload = self._payload(messages, max_tokens=max_tokens, temperature=temperature, stop=stop,
                                stream=False, response_format=response_format)
        r = self._post(payload, task)
        if r.status_code >= 400:
            raise LLMError(f"HTTP {r.status_code} from LLM endpoint: {r.text[:300]}")
        data = r.json()
        try:
            choice = data["choices"][0]
            text = choice["message"].get("content") or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"malformed LLM response: {str(data)[:300]}") from exc
        usage = data.get("usage") or {}
        return LLMResult(
            text=clean_output(text),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            latency_ms=(time.perf_counter() - t0) * 1000,
            model=data.get("model", self.s.llm_name),
            finish_reason=choice.get("finish_reason"),
            attempts=getattr(r, "attempts", 1),
        )

    def chat_stream(self, messages: list[dict], *, task: str, max_tokens: int = 800,
                    temperature: float | None = None, stop: list[str] | None = None,
                    stop_on_degenerate: bool = True) -> Iterator[str]:
        """Yield text deltas. After exhaustion, ``self.last_stream`` holds an :class:`LLMResult`.

        If the output degenerates into a repetition loop the stream is closed early (which also
        stops generation on llama.cpp/Ollama) and ``finish_reason`` is ``"degenerate"``.
        """
        t0 = time.perf_counter()
        payload = self._payload(messages, max_tokens=max_tokens, temperature=temperature, stop=stop, stream=True)
        url = self.s.llm_base_url + "/chat/completions"
        egress.check_url(url)
        parts: list[str] = []
        usage: dict = {}
        finish = None
        model = self.s.llm_name
        n_chunks = 0
        try:
            with self._http.stream("POST", "/chat/completions", json=payload, headers=self._headers(task)) as r:
                if r.status_code >= 400:
                    r.read()
                    raise LLMError(f"HTTP {r.status_code} from LLM endpoint: {r.text[:300]}")
                for line in r.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    model = chunk.get("model", model)
                    if chunk.get("usage"):
                        usage = chunk["usage"]
                    for ch in chunk.get("choices") or []:
                        delta = (ch.get("delta") or {}).get("content") or ""
                        if ch.get("finish_reason"):
                            finish = ch["finish_reason"]
                        if delta:
                            parts.append(delta)
                            n_chunks += 1
                            yield delta
                    if stop_on_degenerate and n_chunks and n_chunks % 16 == 0 and is_degenerate("".join(parts)):
                        finish = "degenerate"
                        break
        except httpx.TransportError as exc:
            raise LLMError(f"stream failed: {exc}") from exc
        finally:
            self.last_stream = LLMResult(
                text=clean_output("".join(parts)),
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens") or n_chunks or None,
                latency_ms=(time.perf_counter() - t0) * 1000,
                model=model,
                finish_reason=finish,
            )

    def chat_guarded(self, messages: list[dict], *, task: str, max_tokens: int = 800,
                     temperature: float | None = None) -> LLMResult:
        """Non-interactive call that still benefits from early stopping on degenerate output."""
        for _ in self.chat_stream(messages, task=task, max_tokens=max_tokens, temperature=temperature):
            pass
        return self.last_stream

    # ------------------------------------------------------------------ JSON
    def chat_json(self, messages: list[dict], *, task: str, schema: dict, max_tokens: int = 900,
                  temperature: float | None = 0.0) -> tuple[dict, LLMResult]:
        modes = {"auto": ["schema", "object", "off"], "schema": ["schema"], "object": ["object"], "off": ["off"]}
        order = modes.get(self._json_mode, ["schema", "object", "off"])
        res: LLMResult | None = None
        for mode in order:
            rf = None
            if mode == "schema":
                rf = {"type": "json_schema", "json_schema": {"name": task, "schema": schema, "strict": False}}
            elif mode == "object":
                rf = {"type": "json_object"}
            try:
                res = self.chat(messages, task=task, max_tokens=max_tokens, temperature=temperature, response_format=rf)
            except LLMError as exc:
                if re.search(r"HTTP (400|404|415|422|501)", str(exc)) and mode != "off":
                    self._json_mode = "auto"
                    continue  # server does not support this response_format; degrade
                raise
            break
        assert res is not None
        obj = parse_json_lenient(res.text)
        if obj is None:
            repair = messages + [
                {"role": "user", "content": (
                    "Your previous answer was not valid JSON. Here it is:\n<<<\n" + res.text[:3000] + "\n>>>\n"
                    "Return only the corrected JSON object, nothing else.")},
            ]
            # keep the alternating user/assistant structure simple: fold into one user turn
            repair_msgs = [messages[0], {"role": "user", "content": messages[-1]["content"] + "\n\n" + repair[-1]["content"]}]
            res2 = self.chat(repair_msgs, task=task + "_repair", max_tokens=max_tokens, temperature=0.0)
            obj = parse_json_lenient(res2.text)
            res.extra["repair_attempted"] = True
            res.completion_tokens = (res.completion_tokens or 0) + (res2.completion_tokens or 0)
            res.prompt_tokens = (res.prompt_tokens or 0) + (res2.prompt_tokens or 0)
            res.latency_ms += res2.latency_ms
            if obj is None:
                raise LLMError("model did not return parseable JSON after one repair round")
        return obj, res

    # ------------------------------------------------------------------ health
    def ping(self, timeout: float = 3.0) -> bool:
        try:
            egress.check_url(self.s.llm_base_url + "/models")
            r = self._http.get("/models", timeout=timeout)
            return r.status_code < 500
        except Exception:
            return False

    def close(self) -> None:
        self._http.close()


# ---------------------------------------------------------------------- JSON repair

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S | re.I)


def _balanced_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    # unbalanced (truncated output): close open brackets heuristically
    frag = text[start:]
    if in_str:
        frag += '"'
    stack = []
    in_str = esc = False
    for c in frag:
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c in "{[":
            stack.append("}" if c == "{" else "]")
        elif c in "}]" and stack:
            stack.pop()
    frag = re.sub(r",\s*$", "", frag.rstrip())
    return frag + "".join(reversed(stack))


def parse_json_lenient(text: str) -> dict | None:
    if not text:
        return None
    m = _FENCE.search(text)
    candidates = [m.group(1)] if m else []
    candidates.append(text)
    for cand in candidates:
        frag = _balanced_object(cand)
        if not frag:
            continue
        for fixer in (lambda s: s, _fix_common):
            try:
                obj = json.loads(fixer(frag))
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue
    return None


def _fix_common(s: str) -> str:
    s = s.replace("“", '"').replace("”", '"').replace("„", '"')
    s = re.sub(r",\s*([}\]])", r"\1", s)                       # trailing commas
    s = re.sub(r"\bTrue\b", "true", s)
    s = re.sub(r"\bFalse\b", "false", s)
    s = re.sub(r"\bNone\b", "null", s)
    if '"' not in s and "'" in s:                               # single-quoted JSON
        s = s.replace("'", '"')
    s = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)", r'\1"\2"\3', s)  # unquoted keys
    return s
