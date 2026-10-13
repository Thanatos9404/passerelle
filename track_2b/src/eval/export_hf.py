"""Export the Hugging Face dataset (HackApertus template layout) to data/hf_dataset/.

    python -m eval.export_hf

Files
  evaluation_dataset.jsonl   one row per letter (test cases): text, language, type, split, ground-truth facts and card
  model_responses.jsonl      one row per (letter, target language): Apertus outputs for the naive baseline and the
                             Passerelle fact-lock pipeline (+ back-translation, chrF, gate, metrics)
  metadata.jsonl             one row per letter: instance-level licence, provenance, generator, synthetic flag
  README.md                  dataset card (kept in the repo; this script does not overwrite it)
"""

from __future__ import annotations

import json

from .harness import RUNS, ROOT, load_letters

OUT = ROOT / "data" / "hf_dataset"


def _read(p):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    letters = load_letters()
    scored = {(s["id"], s["target"]): s for s in _read(RUNS / "explain_scored.jsonl")}
    summary = json.loads((RUNS / "summary.json").read_text(encoding="utf-8")) if (RUNS / "summary.json").exists() else {}
    with (OUT / "evaluation_dataset.jsonl").open("w", encoding="utf-8") as fh:
        for x in letters:
            fh.write(json.dumps({
                "id": x["id"], "letter_type": x["letter_type"], "language": x["lang"], "split": x["split"],
                "explain_subset": x.get("explain_subset", False), "text": x["text"], "authority": x["authority"],
                "facts": x["facts"], "card": x["card"], "action_required": x["action_required"],
                "consequence": x["consequence"], "documents": x["documents"],
            }, ensure_ascii=False) + "\n")
    with (OUT / "metadata.jsonl").open("w", encoding="utf-8") as fh:
        for x in letters:
            fh.write(json.dumps({
                "id": x["id"], "license": "CDLA-Permissive-2.0", "synthetic": True,
                "generator": f"eval/make_letters.py v{x['generator_version']}", "personal_data": False,
                "entities": "fictional (authorities, places, people, accounts); IBAN/AHV numbers random with valid checksums",
                "language": x["lang"], "letter_type": x["letter_type"], "split": x["split"],
            }, ensure_ascii=False) + "\n")
    n = 0
    with (OUT / "model_responses.jsonl").open("w", encoding="utf-8") as fh:
        for it in _read(RUNS / "explain_items.jsonl"):
            s = scored.get((it["id"], it["target"]), {})
            fl, nv = it["factlock"], it["naive"]
            fh.write(json.dumps({
                "id": it["id"], "target_language": it["target"], "split": it["split"],
                "model": summary.get("model", "apertus-8b"), "model_file": summary.get("model_file"),
                "naive_output": nv["output"],
                "factlock_source_plain": fl["source_plain"], "factlock_explanation": fl["explanation"],
                "factlock_masked": fl["masked"], "back_translation": fl["back_translation"], "chrf": fl["chrf"],
                "gate": (s.get("factlock") or {}).get("gate"), "gate_reasons": (s.get("factlock") or {}).get("gate_reasons"),
                "naive_fact_preservation": ((s.get("naive") or {}).get("preservation") or {}).get("rate"),
                "factlock_fact_preservation": ((s.get("factlock") or {}).get("preservation") or {}).get("rate"),
                "naive_hallucinated_numbers": (s.get("naive") or {}).get("hallucinated"),
                "factlock_hallucinated_numbers": (s.get("factlock") or {}).get("hallucinated"),
                "judge_score": (s.get("factlock") or {}).get("judge"),
                "license": "CDLA-Permissive-2.0",
            }, ensure_ascii=False) + "\n")
            n += 1
    print(f"exported {len(letters)} letters, {n} responses to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
