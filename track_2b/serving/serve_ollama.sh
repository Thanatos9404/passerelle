#!/usr/bin/env bash
# Dedicated Ollama instance for Passerelle dev/eval on a 6 GB laptop GPU.
# Flash attention + q8_0 KV cache shrink the KV cache so (almost) all layers fit in VRAM.
export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11435}"
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE="${OLLAMA_KV_CACHE_TYPE:-q8_0}"
export OLLAMA_NUM_PARALLEL="${OLLAMA_NUM_PARALLEL:-1}"
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:-60m}"
exec ollama serve
