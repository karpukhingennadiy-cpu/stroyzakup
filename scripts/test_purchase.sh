#!/bin/bash
# QA: end-to-end test purchase flow via REST API.
# Flow: auth -> create request -> parse -> match suppliers -> send RFQ.
# Requires: curl, jq. Backend must be running on $BASE_API.
set -uo pipefail

BASE_API="${BASE_API:-http://localhost:8000/api}"
EMAIL="${TEST_EMAIL:-demo@minitender.ru}"
PASSWORD="${TEST_PASSWORD:-demo1234}"
RAW_TEXT="${RAW_TEXT:-Керамогранит серый 600x600 — 150 м²; Бетон М300 — 12 м³}"
POLL_MAX=10
POLL_INTERVAL=2

fail() { echo "  [FAIL] $*" >&2; exit 1; }
ok()   { echo "  [OK]   $*"; }

echo "=== TEST PURCHASE E2E ==="
echo "Backend: $BASE_API"
echo "User:    $EMAIL"
echo

# ---------- 1. Auth (JWT) ----------
echo "[1/5] Auth (JWT)"
TOKEN=""
for url in "$BASE_API/auth/login/" "$BASE_API/auth/token/"; do
    for payload in \
        "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
        "{\"username\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
        "{\"username\":\"$EMAIL\",\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"; do
        RESP=$(curl -s -w "\n%{http_code}" -X POST "$url" \
            -H "Content-Type: application/json" -d "$payload")
        CODE=$(echo "$RESP" | tail -1)
        BODY=$(echo "$RESP" | head -n -1)
        TOKEN=$(echo "$BODY" | jq -r '.access // empty' 2>/dev/null)
        if [ -n "$TOKEN" ] && [ "$CODE" = "200" ]; then
            break 2
        fi
    done
done
[ -n "$TOKEN" ] || fail "could not obtain JWT access token"
ok "access token obtained (${TOKEN:0:16}...)"

# ---------- 2. Create request ----------
echo "[2/5] Create request"
RESP=$(curl -s -X POST "$BASE_API/requests/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --arg rt "$RAW_TEXT" '{raw_text: $rt}')")
REQ_ID=$(echo "$RESP" | jq -r '.id // empty')
REQ_CODE=$(echo "$RESP" | jq -r '.code // empty')
[ -n "$REQ_ID" ] || fail "create request failed: $(echo "$RESP" | head -c 300)"
STATUS=$(echo "$RESP" | jq -r '.status')
INIT_STATUS="$STATUS"
echo "  request id: $REQ_ID (code $REQ_CODE), status: $STATUS"

# ---------- 3. Parse ----------
echo "[3/5] Parse items"
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_API/requests/$REQ_ID/parse/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" -d '{}')
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | head -n -1)
PSTATUS=$(echo "$BODY" | jq -r '.status // "?"')
echo "  parse response: HTTP $CODE, status: $PSTATUS"

# Handle 202 (async) by polling request status
for i in $(seq 1 "$POLL_MAX"); do
    STATUS=$(curl -s "$BASE_API/requests/$REQ_ID/" \
        -H "Authorization: Bearer $TOKEN" | jq -r '.status')
    if [ "$STATUS" != "parsing" ] && [ "$STATUS" != "draft" ]; then
        break
    fi
    echo "  poll $i/$POLL_MAX: status=$STATUS, waiting ${POLL_INTERVAL}s..."
    sleep "$POLL_INTERVAL"
done
echo "  final parse status: $STATUS"
case "$STATUS" in parsed|confirmed) ;; *) fail "parse did not finish (got: $STATUS)" ;; esac

ITEMS=$(curl -s "$BASE_API/requests/$REQ_ID/" -H "Authorization: Bearer $TOKEN" | jq -r '.items | length')
ok "parse ok, status: $STATUS, items: $ITEMS"

# ---------- 4. Match suppliers ----------
echo "[4/5] Match suppliers"
RESP=$(curl -s -X POST "$BASE_API/requests/$REQ_ID/match_suppliers/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" -d '{"limit": 20}')
MSTATUS=$(echo "$RESP" | jq -r '.status // "?"')
for i in $(seq 1 "$POLL_MAX"); do
    if [ "$MSTATUS" != "matching" ] && [ "$MSTATUS" != "accepted" ]; then
        break
    fi
    echo "  poll $i/$POLL_MAX: status=$MSTATUS, waiting ${POLL_INTERVAL}s..."
    sleep "$POLL_INTERVAL"
    RESP=$(curl -s -X POST "$BASE_API/requests/$REQ_ID/match_suppliers/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" -d '{"limit": 20}')
    MSTATUS=$(echo "$RESP" | jq -r '.status // "?"')
done
SUPPLIERS=$(echo "$RESP" | jq -c '.suppliers // []' 2>/dev/null)
COUNT=$(echo "$SUPPLIERS" | jq 'length')
echo "  match status: $MSTATUS, suppliers: $COUNT"
[ "$COUNT" -ge 3 ] || fail "expected >= 3 suppliers, got $COUNT"

echo "  top-3 suppliers by score:"
echo "$SUPPLIERS" | jq -r 'sort_by(-.total_score)[0:3][] | "    \(.name) (id=\(.supplier_id)) total_score=\(.total_score) category_score=\(.category_score) distance_score=\(.distance_score)"'
TOP3_IDS=$(echo "$SUPPLIERS" | jq -c 'sort_by(-.total_score)[0:3] | map(.supplier_id)')
ok "matched $COUNT suppliers, top-3 ids: $TOP3_IDS"

# ---------- 5. Send RFQ ----------
echo "[5/5] Send RFQ"
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_API/requests/$REQ_ID/send_rfq/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --argjson ids "$TOP3_IDS" '{supplier_ids: $ids}')")
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | head -n -1)
FSTATUS=$(echo "$BODY" | jq -r '.status // "?"')
echo "  rfq response: HTTP $CODE, status: $FSTATUS"
echo "$BODY" | jq -r '.results[]? | "    \(.supplier): \(.status)\(.error // "" | if .=="" then "" else " (error: "+.+")" end)"' 2>/dev/null
[ "$CODE" = "200" ] || [ "$FSTATUS" = "rfq_sent" ] || fail "send_rfq failed (HTTP $CODE, status '$FSTATUS')"

# Final request status
FINAL=$(curl -s "$BASE_API/requests/$REQ_ID/" -H "Authorization: Bearer $TOKEN" | jq -r '.status')

echo
echo "=== E2E REPORT ==="
echo "  request id:    $REQ_ID (code $REQ_CODE)"
echo "  statuses:      create=$INIT_STATUS parse=$STATUS match=$MSTATUS final=$FINAL"
echo "  supplier count: $COUNT"
echo "  top-3 suppliers:"
echo "$SUPPLIERS" | jq -r 'sort_by(-.total_score)[0:3][] | "    \(.name) — total_score \(.total_score)"'
echo "  final status:  $FINAL"
echo
ok "TEST PURCHASE E2E PASSED"
