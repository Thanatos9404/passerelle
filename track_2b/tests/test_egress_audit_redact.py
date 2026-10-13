"""Egress guard, hash-only audit log, redaction."""

import json
import socket

import pytest

from passerelle import egress
from passerelle.audit import AuditLog, sha256
from passerelle.redact import redact


@pytest.fixture
def guard():
    egress.configure("http://llm.internal:8080/v1", ("extra.internal",))
    egress.install_socket_guard()
    yield
    egress.uninstall_socket_guard()


def test_check_url_allows_only_llm_host(guard):
    egress.check_url("http://llm.internal:8080/v1/chat/completions")
    egress.check_url("http://extra.internal/x")
    egress.check_url("http://127.0.0.1:9999/x")
    with pytest.raises(egress.EgressBlocked):
        egress.check_url("https://api.openai.com/v1/chat/completions")


def test_socket_guard_blocks_public_ip(guard):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(egress.EgressBlocked):
            s.connect(("93.184.216.34", 443))  # blocked before any packet is sent
        assert egress.status()["blocked_attempts"] >= 1
    finally:
        s.close()


def test_socket_guard_allows_loopback(guard, mock_llm_url):
    port = int(mock_llm_url.split(":")[2].split("/")[0])
    with socket.create_connection(("127.0.0.1", port), timeout=2):
        pass


def test_llm_client_refuses_foreign_host(monkeypatch, tmp_path):
    from passerelle.config import load_settings
    from passerelle.llm import LLMClient

    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:1/v1")
    monkeypatch.setenv("PASSERELLE_DATA_DIR", str(tmp_path))
    c = LLMClient(load_settings())
    c.s = c.s.__class__(**{**c.s.__dict__, "llm_base_url": "https://evil.example.com/v1"})
    with pytest.raises(egress.EgressBlocked):
        c.chat([{"role": "user", "content": "x"}], task="t")


def test_audit_chain_and_tamper(tmp_path):
    log = AuditLog(tmp_path / "audit.jsonl")
    log.record("analyze", analysis_id="a1", inputs={"letter": "secret letter"}, meta={"lang": "de", "free": "x" * 100})
    log.record("explain", analysis_id="a1", inputs={"explanation": "text"}, meta={"gate": "ready", "chrf": 61.2})
    assert log.verify() == {"ok": True, "entries": 2}
    raw = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "secret letter" not in raw and sha256("secret letter") in raw
    assert "free" not in raw  # long free text dropped from meta
    lines = raw.splitlines()
    e = json.loads(lines[0])
    e["meta"]["lang"] = "fr"
    (tmp_path / "audit.jsonl").write_text(json.dumps(e) + "\n" + lines[1] + "\n", encoding="utf-8")
    assert log.verify()["ok"] is False
    # a fresh instance continues the chain from the file tail
    log2 = AuditLog(tmp_path / "audit2.jsonl")
    log2.record("a")
    log3 = AuditLog(tmp_path / "audit2.jsonl")
    log3.record("b")
    assert log3.verify() == {"ok": True, "entries": 2}


def test_redact(letter_de):
    r = redact(letter_de)
    out = r["redacted"]
    assert "Ahmadi" not in out and "Amina" not in out
    assert "Rosenweg 4" not in out and "CH93 0076" not in out
    assert "[NAME]" in out and "[ADDRESS]" in out and "[IBAN]" in out
    assert "CHF 1'250.50" in out  # amounts are kept
    fr = redact("Madame Hawa Abdi, née le 3.4.1990, N° AVS 756.1234.5678.97")["redacted"]
    assert "Hawa" not in fr and "1990" not in fr and "756.1234" not in fr
    only_names = redact(letter_de, kinds=("name",))["redacted"]
    assert "Rosenweg 4" in only_names and "Ahmadi" not in only_names
