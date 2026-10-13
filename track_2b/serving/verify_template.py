"""Check that the Ollama Modelfile TEMPLATE renders exactly like the GGUF's own Jinja chat template.

Renders the embedded `tokenizer.chat_template` with jinja2 (add_generation_prompt=True, thinking disabled),
sends it to Ollama's /api/generate with raw=true, sends the same messages through /api/chat, and compares
prompt_eval_count. Equal counts (and identical greedy outputs) mean the templates agree token-for-token.

    uv run --with gguf --with jinja2 python serving/verify_template.py models/apertus-v1.5-8b-text-q4_k_m.gguf
"""

import json
import sys
import urllib.request

import jinja2
from gguf import GGUFReader

HOST = "http://127.0.0.1:11435"
MODEL = "apertus-8b"


def post(path, body):
    req = urllib.request.Request(HOST + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))


def main(gguf_path: str) -> int:
    tpl_src = GGUFReader(gguf_path).fields["tokenizer.chat_template"].contents()
    env = jinja2.Environment(trim_blocks=False, lstrip_blocks=False)
    env.globals["raise_exception"] = lambda m: (_ for _ in ()).throw(RuntimeError(m))
    messages = [
        {"role": "system", "content": "You are a professional translator. Output only the translation."},
        {"role": "user", "content": "Translate into French: Bitte zahlen Sie ⟦A1⟧ bis ⟦D1⟧."},
    ]
    rendered = env.from_string(tpl_src).render(messages=messages, add_generation_prompt=True, bos_token="")
    print("rendered (BOS added by tokenizer):", repr(rendered))
    opts = {"temperature": 0, "num_predict": 40, "seed": 1}
    raw = post("/api/generate", {"model": MODEL, "prompt": rendered, "raw": True, "stream": False, "options": opts})
    chat = post("/api/chat", {"model": MODEL, "messages": messages, "stream": False, "options": opts})
    print("raw  prompt_eval_count:", raw["prompt_eval_count"], "->", repr(raw["response"][:120]))
    print("chat prompt_eval_count:", chat["prompt_eval_count"], "->", repr(chat["message"]["content"][:120]))
    same = raw["prompt_eval_count"] == chat["prompt_eval_count"] and raw["response"].strip() == chat["message"]["content"].strip()
    print("MATCH" if same else "MISMATCH")
    return 0 if same else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
