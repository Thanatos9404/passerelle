# syntax=docker/dockerfile:1.7
# Passerelle — FastAPI backend + static Next.js UI in one non-root image.
# Build time needs the network (npm, PyPI). Runtime needs only LLM_BASE_URL (or nothing else in air-gapped mode).

# ---------------------------------------------------------------- 1) web UI (optional)
FROM node:22-alpine AS web
WORKDIR /build
COPY src/ ./src/
# the UI build (scripts/sync-eval.mjs) embeds the evaluation summary into the static export
COPY data/eval_runs/ ./data/eval_runs/
RUN if [ -f src/web/package.json ]; then \
      cd src/web && (npm ci --no-audit --no-fund || npm install --no-audit --no-fund) \
      && NEXT_TELEMETRY_DISABLED=1 npm run build \
      && if [ ! -d out ]; then echo "src/web build produced no out/ (Next.js needs output: 'export')" >&2; exit 1; fi; \
    else \
      echo "no src/web/package.json — building API-only image"; mkdir -p src/web/out; \
    fi

# ---------------------------------------------------------------- 2) python dependencies
FROM python:3.12-slim AS py
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY requirements.lock ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --require-hashes -r requirements.lock
COPY pyproject.toml ./
COPY src/passerelle src/passerelle
COPY src/eval src/eval
RUN /opt/venv/bin/pip install --no-deps .

# ---------------------------------------------------------------- 3) runtime
FROM python:3.12-slim AS runtime
LABEL org.opencontainers.image.title="Passerelle" \
      org.opencontainers.image.description="Explain Swiss official letters in the client's language with Apertus (fact-lock + verification)" \
      org.opencontainers.image.licenses="Apache-2.0"
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    PASSERELLE_DATA_DIR=/var/lib/passerelle \
    PASSERELLE_LETTERS_DIR=/app/data/letters \
    PASSERELLE_STATIC_DIR=/app/web/out \
    PASSERELLE_EVAL_SUMMARY=/app/data/eval_runs/summary.json
RUN useradd --create-home --uid 10001 passerelle \
    && mkdir -p /var/lib/passerelle && chown passerelle:passerelle /var/lib/passerelle
COPY --from=py /opt/venv /opt/venv
WORKDIR /app
COPY data/ data/
COPY --from=web /build/src/web/out /app/web/out
USER passerelle
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=4).status == 200 else 1)"
CMD ["passerelle", "serve", "--host", "0.0.0.0", "--port", "8080"]
