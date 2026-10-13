"""API contract tests against the mock OpenAI-compatible server (SPEC §2 shapes)."""

import json


def test_health(client):
    r = client.get("/api/health").json()
    assert r["status"] == "ok" and r["model"] == "mock-apertus" and r["backend_reachable"] is True
    assert "allowed_hosts" in r["egress"]


def test_languages(client):
    langs = client.get("/api/languages").json()
    codes = {x["code"] for x in langs}
    assert {"ti", "ar", "prs", "uk", "ta", "tr", "so", "sq", "en", "pt", "es"} <= codes
    ar = next(x for x in langs if x["code"] == "ar")
    assert ar["rtl"] is True and ar["native"] == "العربية" and {"ready", "review"} <= set(ar["gate"])
    assert "quality" in ar


def test_samples_and_analyze_sample(client):
    samples = client.get("/api/samples").json()
    assert len(samples) >= 36
    s0 = samples[0]
    assert {"id", "title", "language", "type"} <= set(s0)
    full = client.get(f"/api/samples/{s0['id']}").json()
    assert full["text"] and full["facts"]
    r = client.post("/api/analyze", json={"sample_id": s0["id"]}).json()
    assert {"analysis_id", "letter_lang", "fact_card", "facts", "disagreements", "timings"} <= set(r)
    for f in r["facts"]:
        assert {"id", "type", "value", "normalized", "span"} <= set(f)
        assert r["text"][f["span"][0]:f["span"][1]] == f["value"]


def test_analyze_text(client, letter_de):
    r = client.post("/api/analyze", json={"text": letter_de}).json()
    assert r["letter_lang"] == "de" and r["llm_ok"] is True
    card = r["fact_card"]
    assert card["deadline"]["date"] == "2026-11-15"
    assert card["letter_type"] == "debt_collection"
    assert {a["value"] for a in card["amounts"]} == {"1250.50", "73.30"}
    assert card["iban"]["value"] == "CH93 0076 2011 6238 5295 7"


def test_analyze_validation(client):
    assert client.post("/api/analyze", json={}).status_code == 422
    assert client.post("/api/analyze", json={"sample_id": "nope"}).status_code == 404


def test_explain_contract(client, letter_de):
    aid = client.post("/api/analyze", json={"text": letter_de}).json()["analysis_id"]
    r = client.post("/api/explain", json={"analysis_id": aid, "target_lang": "ar"})
    assert r.status_code == 200
    d = r.json()
    for k in ("explanation", "masked", "rtl", "back_translation", "chrf", "placeholder_audit", "gate", "timings", "tokens"):
        assert k in d
    assert d["rtl"] is True
    assert set(d["placeholder_audit"]) >= {"missing", "duplicated", "unexpected"}
    assert d["gate"]["status"] in {"ready", "review", "interpreter"} and d["gate"]["reasons"] is not None
    assert "⟦" not in d["explanation"] and "CHF 1'250.50" in d["explanation"]
    for s in d["fact_spans"]:
        assert d["explanation"][s["start"]:s["end"]] == s["value"]


def test_explain_with_text_and_unknown_lang(client, letter_de):
    assert client.post("/api/explain", json={"text": letter_de, "target_lang": "xx"}).status_code == 400
    assert client.post("/api/explain", json={"analysis_id": "missing", "target_lang": "ti"}).status_code == 404
    r = client.post("/api/explain", json={"text": letter_de, "target_lang": "de"}).json()
    assert r["same_language"] is True and r["chrf"] is None


def test_explain_stream(client, letter_de):
    aid = client.post("/api/analyze", json={"text": letter_de}).json()["analysis_id"]
    with client.stream("GET", f"/api/explain/stream?analysis_id={aid}&target_lang=uk") as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        body = "".join(r.iter_text())
    events = [blk.split("\n")[0][7:] for blk in body.strip().split("\n\n")]
    assert events[0] == "stage" and events[-1] == "result" and "token" in events
    result = json.loads(body.strip().split("\n\n")[-1].split("data: ", 1)[1])
    tokens = "".join(json.loads(b.split("data: ", 1)[1])["text"] for b in body.split("\n\n") if b.startswith("event: token"))
    assert tokens.strip() == result["explanation"].strip()


def test_reply(client, letter_de):
    aid = client.post("/api/analyze", json={"text": letter_de}).json()["analysis_id"]
    r = client.post("/api/reply", json={"analysis_id": aid, "client_message": "أستطيع الدفع في ١.١٢.٢٠٢٦", "client_lang": "ar"})
    d = r.json()
    assert r.status_code == 200
    assert "26-104523" in d["reply_letter"]
    assert d["audit"]["needs_caseworker_approval"] is True
    assert any(f["normalized"] == "2026-12-01" for f in d["client_facts"])


def test_audit_endpoint_hash_only(client, letter_de):
    client.post("/api/analyze", json={"text": letter_de})
    d = client.get("/api/audit").json()
    assert d["chain"]["ok"] is True and d["entries"]
    assert "Ahmadi" not in json.dumps(d)


def test_redact_endpoint(client, letter_de):
    d = client.post("/api/redact", json={"text": letter_de}).json()
    assert "Ahmadi" not in d["redacted"] and d["counts"]["name"] >= 1


def test_ingest_text_upload(client, letter_de):
    r = client.post("/api/ingest", files={"file": ("letter.txt", letter_de.encode("utf-8"), "text/plain")})
    assert r.status_code == 200 and r.json()["text"].startswith("Betreibungsamt")


def test_static_ui_served(env, monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    from passerelle.api import create_app
    from passerelle.config import reset_settings

    out = tmp_path / "out"
    (out / "workspace").mkdir(parents=True)
    (out / "index.html").write_text("<h1>home</h1>")
    (out / "workspace" / "index.html").write_text("<h1>ws</h1>")
    (out / "evidence.html").write_text("<h1>ev</h1>")
    monkeypatch.setenv("PASSERELLE_STATIC_DIR", str(out))
    reset_settings()
    with TestClient(create_app()) as c:
        assert "home" in c.get("/").text
        assert "ws" in c.get("/workspace").text
        assert "ev" in c.get("/evidence").text
        assert c.get("/../../etc/passwd").status_code == 404
        assert c.get("/api/nope").status_code == 404
