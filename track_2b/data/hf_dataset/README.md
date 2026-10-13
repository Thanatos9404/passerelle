---
license: cdla-permissive-2.0
language:
- de
- fr
- it
- ti
- ar
- prs
- uk
- ta
- tr
- so
- sq
- en
- pt
- es
pretty_name: Passerelle — Swiss official letters, fact-locked explanations
size_categories:
- n<1K
task_categories:
- text-generation
- translation
- token-classification
tags:
- apertus
- hackapertus
- public-sector
- plain-language
- low-resource-languages
- synthetic
configs:
- config_name: evaluation_dataset
  data_files: evaluation_dataset.jsonl
- config_name: model_responses
  data_files: model_responses.jsonl
- config_name: metadata
  data_files: metadata.jsonl
---

# Dataset Card for Passerelle Swiss Letters

Synthetic Swiss official letters (German, French, Italian) with exact ground-truth facts, plus Apertus v1.5 8B
explanations of those letters in 11 target languages produced (a) naively and (b) with Passerelle's fact-lock and
round-trip verification. Built for the Hack Apertus online challenge, Track 2B.

## Dataset Details

- **Curated by:** Stack Underflow (Hack Apertus 2026, Track 2B)
- **Funded by [optional]:** none
- **Shared by [optional]:** Stack Underflow
- **Language(s) (NLP):** letters in de, fr, it; model responses in ti (Tigrinya), ar (Arabic), prs (Dari), uk (Ukrainian),
  ta (Tamil), tr (Turkish), so (Somali), sq (Albanian), and the high-resource controls en, pt, es; back-translations in de/fr/it.
- **License:** CDLA-Permissive-2.0 (every instance; see `metadata.jsonl`)
- **Git repository:** GIT_REPO_URL (folder `track_2b/`; generator `src/eval/make_letters.py`)

## Uses

### Direct Use

- Evaluating whether an LLM preserves critical facts (deadlines, CHF amounts, IBAN, AHV/AVS numbers, reference
  numbers, phone numbers, times) when it explains or translates official letters.
- Evaluating fact extraction from Swiss-format letters (precision/recall per fact type).
- Studying round-trip (back-translation) checks and confidence gates for low-resource target languages.

### Out-of-Scope Use

- Not legal advice and not a source of real administrative procedures: authorities, amounts and rules are fictional
  simplifications.
- Not a measure of general translation quality in the target languages (only 24 test letters per language; no human
  reference translations).
- Model responses must not be shown to real clients as authoritative translations.

### Specifications

- `evaluation_dataset.jsonl`: 72 letters (12 letter types × 3 languages × 2 instances). Fields: `id`, `letter_type`,
  `language`, `split` (`dev` 12 / `test` 60), `explain_subset` (24 test letters used for the explanation ablation),
  `text`, `facts` (type, surface `value`, `normalized`, `role`, `critical`, character `spans`), `card`,
  `action_required`, `consequence`, `documents`.
- `model_responses.jsonl`: one row per (letter, target language) for 12 dev + 24 test letters × 11 languages:
  `naive_output`, `factlock_source_plain`, `factlock_explanation`, `back_translation`, `chrf`, `gate`, metrics.
- `metadata.jsonl`: instance-level licence and provenance.

## Dataset Structure

Fact types: `date`, `duration`, `amount`, `iban`, `ahv`, `reference`, `phone`, `time`, `email`, `address`, `legal`.
Normalised forms: ISO dates (`2026-11-15`), CHF with two decimals (`1250.50`), ISO-8601 durations (`P30D`), E.164
phones, compact IBAN, dotted AHV/AVS. Letter types: tax reminder, health-insurance premium reduction, residence-permit
renewal, social-assistance appointment, school enrolment, debt collection (payment order), rent increase, AHV/AVS
contributions, family allowance, health-insurance reminder, asylum interview summons, parking fine.

## Dataset Creation

### Curation Rationale

Migrants and asylum seekers in Switzerland receive official letters in German, French or Italian; misreading a
deadline or an amount has real consequences. Real letters contain special categories of personal data and cannot be
shared, so we wrote realistic templates and generated letters with known ground truth.

### Source Data

#### Data Collection

36 letter templates (12 types × DE/FR/IT) were hand-written to resemble Swiss municipal, cantonal and federal letters
(letterhead, date line, reference, salutation, body, deadline, amount, contact, signature). A seeded generator fills
slots with fictional values in varied Swiss surface formats (numeric vs long dates, `CHF 1'250.50` / `Fr. 80.–` /
`1 250.50 CHF`, `+41`/`0xx` phones, number words for durations, …) and records ground truth directly from the slots.

#### Source Data Producers and Data Subjects

Templates written by the team; no real persons. Names are common first/last names combined at random; authorities,
communes and cantons are invented.

#### Ownership and Consent Management

Created by the team for this dataset; no third-party content; no consent required (no data subjects).

#### Data Processing and Quality Control

Automated checks (`tests/test_dataset.py`): every ground-truth span matches the letter text; every type × language
combination is present; dev/test splits are disjoint; size < 100 MB.

#### Data Instance Licenses

All instances: CDLA-Permissive-2.0 (also stated per row in `metadata.jsonl`). Model responses were generated with
Apertus v1.5 8B (Apache-2.0 weights).

### Annotations

#### Annotation Process

No manual annotation: facts are known by construction. Round-trip quality labels in `model_responses.jsonl`
(`judge_score`) come from an automatic helper judge (another open model, `llama3` 8B via Ollama) and are noisy.

#### Annotator Details

Not applicable (automatic).

## Risks, Bias, and Limitations

### Personally Identifiable Information

None. IBAN and AHV/AVS numbers are random with valid checksums; any match with a real account or person is coincidental.

### Sensitive Information

The letter themes (asylum, debt collection, social assistance) are sensitive by nature, but all content is fictional.

### Recommendations

Users should be made aware of the risks, biases and limitations of the dataset. In particular: the letters are
template-based and cleaner than real scanned letters; the deterministic extractors in the Passerelle repository were
developed alongside these templates, so their scores here are optimistic; model-response quality for low-resource
languages was not checked by native speakers.

## Citations [optional]

**BibTeX:**

```bibtex
@misc{passerelle2026,
  title  = {Passerelle: fact-locked explanations of Swiss official letters with Apertus},
  author = {Stack Underflow},
  year   = {2026},
  note   = {Hack Apertus 2026, Track 2B}
}
```

**APA:** Stack Underflow. (2026). *Passerelle: fact-locked explanations of Swiss official letters with Apertus* [Data set].

## Glossary [optional]

- **Fact-lock:** replacing critical facts by placeholders (`⟦D1⟧`) before generation and re-inserting verified values after.
- **chrF:** character n-gram F-score (sacrebleu) between the back-translation and the plain-language source text.
- **Gate:** Ready / Review with client / Use a human interpreter.

## More Information [optional]

See `track_2b/technical_report.md` in the Git repository for the evaluation protocol and results.

## Dataset Card Authors [optional]

Stack Underflow

## Dataset Card Contact

Stack Underflow (see Git repository)
