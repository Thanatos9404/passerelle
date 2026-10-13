# Passerelle web UI

Next.js 15 (App Router, TypeScript strict, Tailwind v4, Radix/shadcn-style primitives, `motion`, Lenis), exported as a **static site** (`out/`) that FastAPI serves at `/`. The API is same-origin under `/api/*`. No runtime requests leave the machine: fonts (Open Runde, Noto Sans Ethiopic/Tamil, Noto Naskh Arabic, all SIL OFL) and photos are bundled.

Pages: `/` (landing), `/workspace/` (caseworker app), `/evidence/` (evaluation results).

## Run

```bash
npm ci
npm run dev            # http://localhost:3000, mock data by default
npm run build          # copies ../../data/eval_runs/summary.json -> public/eval/, then exports ./out
npm run serve          # serve ./out on :4321 (no API; add ?data=mock to any URL)
npm run lint && npm run typecheck
npm run shots          # Playwright QA screenshots -> screenshots/ (node scripts/screenshots.mjs <base> [--query=data=mock])
```

With the backend: `python -m passerelle.cli serve --port 8080` serves `src/web/out` and `/api/*` from one origin.

## Data source

| Setting | Effect |
|---|---|
| `NEXT_PUBLIC_DATA_SOURCE=mock` | in-browser mock: 4 synthetic DE/FR/IT letters, hand-written explanations (Tigrinya, Arabic, Dari, Tamil, Ukrainian, Turkish, English), simulated streaming, real chrF on the mock texts |
| `NEXT_PUBLIC_DATA_SOURCE=api` | FastAPI backend (SPEC §2) |
| unset | `mock` under `next dev`, `api` in production builds |
| `?data=mock` / `?data=api` | runtime override per page load (demos) |
| `NEXT_PUBLIC_API_BASE` | API origin; empty = same origin. For `next dev` against a local backend: `http://localhost:8080` (add the dev origin to `PASSERELLE_CORS_ORIGINS`) |

The workspace header always shows which source is active ("Mock data" vs the model name).

## API contract used (see `src/lib/api/`)

All payloads go through `normalize.ts`, which accepts the backend's shapes and fills documented defaults.

- `GET /api/health`, `GET /api/languages`, `GET /api/samples`
- `POST /api/analyze {sample_id | text}` → needs `analysis_id`, `text` and fact `span`s (or `spans`); uses `display`, `fact_card.{deadlines, appointment, amounts, references, iban, ahv_number, documents, contact}`, `llm_ok`
- `POST /api/explain/stream` (SSE): `stage {stage}`, `token {text}`, `result <ExplainResponse>`, `error {message}`; falls back to `POST /api/explain` on 404/405. Uses `fact_spans` for exact fact chips, `source_plain_masked` / `back_translation_masked` for the side-by-side, `gate.{status,reasons,thresholds}`, `*_ms` timings
- `POST /api/reply`, `GET /api/audit`, `POST /api/ingest` (multipart PDF/TXT)
- `GET /api/eval/summary` → falls back to `/eval/summary.json`; `src/lib/eval.ts` adapts the `score.py` schema. Missing numbers render as an em dash — nothing is typed in by hand.

Photo credits: `public/photos/CREDITS.md`.
