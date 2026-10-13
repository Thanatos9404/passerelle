# Licence — data

Everything in `data/` (synthetic letters and ground truth in `letters/`, evaluation outputs in `eval_runs/`,
the Hugging Face export in `hf_dataset/`) is licensed under the **Community Data License Agreement – Permissive,
Version 2.0 (CDLA-Permissive-2.0)**: https://cdla.dev/permissive-2-0/

The letters are synthetic: all authorities, places, people, account and insurance numbers are fictional (IBAN and
AHV/AVS numbers are random with valid checksums). Model outputs in `eval_runs/` were generated with Apertus v1.5 8B
(Apache-2.0 weights) and, for evaluation labels only, Llama 3 8B via Ollama.
