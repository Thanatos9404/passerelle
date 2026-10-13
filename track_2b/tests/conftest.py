import socket
import threading
import time

import pytest
import uvicorn


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def mock_llm_url():
    from eval.mock_llm import app

    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}/v1"
    server.should_exit = True


@pytest.fixture
def env(mock_llm_url, tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", mock_llm_url)
    monkeypatch.setenv("LLM_NAME", "mock-apertus")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("PASSERELLE_DATA_DIR", str(tmp_path / "var"))
    monkeypatch.setenv("PASSERELLE_EGRESS_SOCKET_GUARD", "0")
    monkeypatch.setenv("PASSERELLE_MAX_RETRIES", "1")
    from passerelle import samples, verify
    from passerelle.config import reset_settings

    reset_settings()
    verify._load_thresholds.cache_clear()
    samples._index.cache_clear()
    yield tmp_path
    reset_settings()


@pytest.fixture
def client(env):
    from fastapi.testclient import TestClient

    from passerelle.api import create_app

    with TestClient(create_app()) as c:
        yield c


LETTER_DE = """Betreibungsamt Seewil
Bahnhofstrasse 12
8004 Seewil
Tel. 044 123 45 67
betreibungsamt@seewil.ch

Frau
Amina Ahmadi
Rosenweg 4
8004 Seewil

Seewil, 5. Oktober 2026

Zahlungsbefehl
Betreibung Nr. 26-104523

Sehr geehrte Frau Ahmadi

Die Gläubigerin verlangt CHF 1'250.50 nebst Zins seit 1. Juli 2026 sowie Kosten von CHF 73.30.
Bitte bezahlen Sie bis 15.11.2026 auf IBAN CH93 0076 2011 6238 5295 7.
Sie können innert 10 Tagen Rechtsvorschlag erheben (Art. 74 SchKG).

Freundliche Grüsse
Betreibungsamt Seewil
"""


@pytest.fixture
def letter_de():
    return LETTER_DE
