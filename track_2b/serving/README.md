# Serving Apertus locally (dev / eval / air-gapped)

Passerelle talks to any OpenAI-compatible endpoint (`LLM_BASE_URL`, `LLM_NAME`, `LLM_API_KEY`). For local use
we serve the 5.1 GB **Apertus v1.5 8B Q4_K_M GGUF** (`Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF`, converted from
`andreasmartin/apertus-v1.5-8b-text`; Apache-2.0). Fetch it at build/provisioning time with `make model`.

## Option 1 — llama.cpp server (Docker, used by `make run-local`)

```bash
make run-local            # CPU: llama.cpp server + app, internal network only
make run-local-gpu        # NVIDIA: server-cuda image, all layers on GPU, q8_0 KV cache
```
The server is started with `--jinja`, i.e. it applies the chat template embedded in the GGUF.

## Option 2 — Ollama (what we used for development and the evaluation)

```bash
# dedicated instance on :11435 with flash attention + q8_0 KV cache (fits 33/33 layers in 6 GB VRAM)
./serving/serve_ollama.sh &
OLLAMA_HOST=127.0.0.1:11435 ollama create apertus-8b -f serving/Modelfile
export LLM_BASE_URL=http://127.0.0.1:11435/v1 LLM_NAME=apertus-8b LLM_API_KEY=none
```
`Modelfile` re-implements Apertus' chat template (system → developer block with *Deliberation: disabled* →
user → assistant). `verify_template.py` renders the GGUF's own Jinja template and checks, via Ollama's raw
mode, that both paths produce the same prompt tokens and the same greedy output (result: **MATCH**, 55/55 tokens).

Measured on an RTX 4050 Laptop GPU (6 GB): 33/33 layers on GPU, 5.5 GB VRAM, **~34.5 tokens/s** generation and
~500 tokens/s prompt processing for a single stream (26/33 layers with Ollama's default memory estimate: ~19.5 tok/s;
default Ollama settings without flash attention: ~12.9 tok/s).

## Option 3 — LM Studio CLI

`lms load` the GGUF and `lms server start` (OpenAI API on :1234); LM Studio applies the embedded template.
Not used for our numbers.
