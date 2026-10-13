# Passerelle — run everything from track_2b/
#   make run         start the app in Docker against LLM_BASE_URL / LLM_NAME / LLM_API_KEY (judges)
#   make run-local   air-gapped: llama.cpp server + Apertus GGUF in Docker (CPU); run-local-gpu for NVIDIA
#   make test        unit + API contract tests (mock LLM, no GPU, no network)
#   make eval        full evaluation (needs an Apertus endpoint; see technical_report.md §7)
#   make model       download the Apertus Q4_K_M GGUF into ./models (build time only)
#   make report      technical_report.md -> StackUnderflow_Report.pdf (needs Chrome/Chromium)

SHELL := /bin/bash
COMPOSE ?= docker compose
MODEL_REPO ?= Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF
MODEL_FILE ?= apertus-v1.5-8b-text-q4_k_m.gguf
MODEL_URL ?= https://huggingface.co/$(MODEL_REPO)/resolve/main/$(MODEL_FILE)
UV := $(shell command -v uv 2>/dev/null)
ifeq ($(UV),)
  PY_RUN = python -m
  PY_SETUP = python -m pip install -q -e ".[eval]" pytest hypothesis
else
  PY_RUN = uv run --extra eval --group dev python -m
  PY_SETUP = uv sync -q --extra eval --group dev
endif

.PHONY: run run-local run-local-gpu stop test eval figures model report mock serve lock

run:
	$(COMPOSE) up --build

run-local: model
	LLM_BASE_URL=http://llm:8080/v1 LLM_NAME=apertus-8b LLM_API_KEY=none $(COMPOSE) --profile local-llm up --build

run-local-gpu: model
	LLM_BASE_URL=http://llm:8080/v1 LLM_NAME=apertus-8b LLM_API_KEY=none $(COMPOSE) --profile local-llm-gpu up --build

stop:
	$(COMPOSE) --profile local-llm --profile local-llm-gpu down

test:
	$(PY_SETUP)
	$(PY_RUN) pytest

eval:
	$(PY_SETUP)
	$(PY_RUN) eval.run_eval all
	$(PY_RUN) eval.figures

figures:
	$(PY_RUN) eval.figures

# Weights are fetched at build/provisioning time, never at runtime. The GGUF repo is public; if you use a
# gated upstream repo (e.g. swiss-ai/Apertus-*), accept its licence on huggingface.co and export HF_TOKEN.
model:
	@mkdir -p models
	@if [ -f models/$(MODEL_FILE) ]; then echo "models/$(MODEL_FILE) present"; else \
	  echo "downloading $(MODEL_URL) (~5 GB)"; \
	  curl -L --fail --retry 3 -o models/$(MODEL_FILE).part $${HF_TOKEN:+-H "Authorization: Bearer $$HF_TOKEN"} "$(MODEL_URL)" \
	  && mv models/$(MODEL_FILE).part models/$(MODEL_FILE); fi

report:
	$(PY_RUN) eval.build_report

# Local development without Docker
mock:
	$(PY_RUN) eval.mock_llm --port 8099

serve:
	$(PY_RUN) passerelle.cli serve --port 8080

lock:
	uv lock && uv export --no-dev --no-emit-project --format requirements-txt -o requirements.lock
