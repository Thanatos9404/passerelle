#!/usr/bin/env bash
# End-to-end smoke test against a running Passerelle (used by CI with the mock LLM).
# usage: scripts/smoke_test.sh [http://localhost:8080]
set -euo pipefail
BASE="${1:-http://localhost:8080}"
py() { python3 -c "$1"; }

echo "== health"
H=$(curl -sf "$BASE/api/health")
echo "$H"
echo "$H" | py 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="ok" and d["backend_reachable"] is True, d'

echo "== languages / samples"
curl -sf "$BASE/api/languages" | py 'import json,sys; d=json.load(sys.stdin); assert any(x["code"]=="ti" for x in d)'
SID=$(curl -sf "$BASE/api/samples" | py 'import json,sys; d=json.load(sys.stdin); assert len(d)>=36; print(d[0]["id"])')
echo "sample $SID"

echo "== analyze"
A=$(curl -sf -X POST "$BASE/api/analyze" -H 'Content-Type: application/json' -d "{\"sample_id\": \"$SID\"}")
AID=$(echo "$A" | py 'import json,sys; d=json.load(sys.stdin); assert d["facts"] and d["fact_card"]; print(d["analysis_id"])')
echo "analysis $AID"

echo "== explain"
curl -sf -X POST "$BASE/api/explain" -H 'Content-Type: application/json' -d "{\"analysis_id\": \"$AID\", \"target_lang\": \"ti\"}" \
  | py 'import json,sys; d=json.load(sys.stdin); assert d["gate"]["status"] in ("ready","review","interpreter"); assert "explanation" in d and "chrf" in d; print("gate:", d["gate"]["status"], "chrF:", d["chrf"])'

echo "== explain (SSE)"
curl -sfN "$BASE/api/explain/stream?analysis_id=$AID&target_lang=ar" | grep -q "event: result"

echo "== reply / redact / audit"
curl -sf -X POST "$BASE/api/reply" -H 'Content-Type: application/json' -d "{\"analysis_id\": \"$AID\", \"client_message\": \"I will pay next week\", \"client_lang\": \"en\"}" \
  | py 'import json,sys; d=json.load(sys.stdin); assert d["reply_letter"]'
curl -sf -X POST "$BASE/api/redact" -H 'Content-Type: application/json' -d "{\"analysis_id\": \"$AID\"}" | py 'import json,sys; assert "redacted" in json.load(sys.stdin)'
curl -sf "$BASE/api/audit" | py 'import json,sys; d=json.load(sys.stdin); assert d["chain"]["ok"] and d["entries"]'

echo "== static root"
curl -sf -o /dev/null -w "%{http_code}\n" "$BASE/"
echo "SMOKE TEST PASSED"
