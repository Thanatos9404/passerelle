"""Runtime configuration, read from environment variables.

The three variables required by the Hack Apertus rules are ``LLM_NAME``,
``LLM_BASE_URL`` and ``LLM_API_KEY`` (any OpenAI-compatible endpoint).
Everything else is optional and prefixed ``PASSERELLE_``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
# src/passerelle/config.py -> parents[2] == track_2b/ in a source checkout
PROJECT_DIR = PACKAGE_DIR.parents[1]


def _env(name: str, default: str) -> str:
    value = os.environ.get(name)
    return default if value is None or value.strip() == "" else value.strip()


def _first_existing(*candidates: Path) -> Path:
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


@dataclass(frozen=True)
class Settings:
    llm_name: str
    llm_base_url: str
    llm_api_key: str
    timeout_s: float
    max_retries: int
    temperature: float
    seed: int | None
    json_mode: str  # auto | schema | object | off
    send_task_header: bool
    egress_allow: tuple[str, ...]
    egress_socket_guard: bool
    data_dir: Path
    letters_dir: Path
    static_dir: Path
    thresholds_path: Path
    eval_summary_path: Path
    cors_origins: tuple[str, ...]
    max_tokens_extract: int = 900
    max_tokens_explain: int = 700
    max_tokens_translate: int = 1400
    extra: dict = field(default_factory=dict)

    @property
    def audit_path(self) -> Path:
        return self.data_dir / "audit.jsonl"


def load_settings() -> Settings:
    data_dir = Path(_env("PASSERELLE_DATA_DIR", str(PROJECT_DIR / "var")))
    seed_raw = _env("PASSERELLE_SEED", "7")
    return Settings(
        llm_name=_env("LLM_NAME", "apertus-8b"),
        llm_base_url=_env("LLM_BASE_URL", "http://localhost:11434/v1").rstrip("/"),
        llm_api_key=_env("LLM_API_KEY", "none"),
        timeout_s=float(_env("PASSERELLE_TIMEOUT", "300")),
        max_retries=int(_env("PASSERELLE_MAX_RETRIES", "3")),
        temperature=float(_env("PASSERELLE_TEMPERATURE", "0.1")),
        seed=None if seed_raw.lower() in {"none", "off", ""} else int(seed_raw),
        json_mode=_env("PASSERELLE_JSON_MODE", "auto").lower(),
        send_task_header=_env("PASSERELLE_TASK_HEADER", "1") not in {"0", "false", "no"},
        egress_allow=tuple(h.strip().lower() for h in _env("PASSERELLE_EGRESS_ALLOW", "").split(",") if h.strip()),
        egress_socket_guard=_env("PASSERELLE_EGRESS_SOCKET_GUARD", "1") not in {"0", "false", "no"},
        data_dir=data_dir,
        letters_dir=Path(_env("PASSERELLE_LETTERS_DIR", str(PROJECT_DIR / "data" / "letters"))),
        static_dir=Path(_env("PASSERELLE_STATIC_DIR", str(_first_existing(PROJECT_DIR / "src" / "web" / "out", PROJECT_DIR / "web" / "out")))),
        thresholds_path=Path(_env("PASSERELLE_THRESHOLDS", str(PACKAGE_DIR / "resources" / "gate_thresholds.json"))),
        eval_summary_path=Path(_env("PASSERELLE_EVAL_SUMMARY", str(PROJECT_DIR / "data" / "eval_runs" / "summary.json"))),
        cors_origins=tuple(
            o.strip()
            for o in _env("PASSERELLE_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
            if o.strip()
        ),
        max_tokens_extract=int(_env("PASSERELLE_MAX_TOKENS_EXTRACT", "900")),
        max_tokens_explain=int(_env("PASSERELLE_MAX_TOKENS_EXPLAIN", "700")),
        max_tokens_translate=int(_env("PASSERELLE_MAX_TOKENS_TRANSLATE", "1400")),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()


def reset_settings() -> None:
    """Forget cached settings (tests change env vars)."""
    get_settings.cache_clear()
