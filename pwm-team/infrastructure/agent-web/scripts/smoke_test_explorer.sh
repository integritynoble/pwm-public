#!/usr/bin/env bash
# Smoke test the PWM explorer.
#
# Usage:
#   bash scripts/smoke_test_explorer.sh [BASE_URL]
# Default BASE_URL: https://explorer.pwm.platformai.org
#
# Exit 0 = all checks pass. Exit 1 = one or more checks fail.
#
# Per MAINNET_DEPLOY_PLAN.md Stream 3 done criterion: this script is the
# canonical "did we ship a working explorer?" gate. Used in:
#   - Stream 3 weekly Tue/Thu/Sat smoke test loop
#   - Mainnet day runbook step 9 (announcement) gating
#   - Site-2 verifying standards (`explorer.pwm.platformai.org`)

set -uo pipefail

BASE_URL="${1:-https://explorer.pwm.platformai.org}"
TIMEOUT=15

PASS=0
FAIL=0
FAIL_REASONS=()

# --- helpers -----------------------------------------------------------

ok() {
    PASS=$((PASS + 1))
    echo "  ✓ $*"
}

bad() {
    FAIL=$((FAIL + 1))
    FAIL_REASONS+=("$*")
    echo "  ✗ $*"
}

http_code() {
    # $1: URL → echoes HTTP status code, or 000 on failure
    curl -ks -o /dev/null --max-time "$TIMEOUT" -w "%{http_code}" "$1"
}

http_body() {
    # $1: URL → echoes body, empty on failure
    curl -ks --max-time "$TIMEOUT" "$1" 2>/dev/null
}

require_200() {
    local label="$1" url="$2"
    local code
    code=$(http_code "$url")
    if [[ "$code" == "200" ]]; then
        ok "${label}: HTTP 200"
    else
        bad "${label}: expected 200, got ${code} (${url})"
    fi
}

require_substring() {
    local label="$1" url="$2" needle="$3"
    local body
    body=$(http_body "$url")
    if [[ "$body" == *"$needle"* ]]; then
        ok "${label}: contains '${needle}'"
    else
        bad "${label}: missing '${needle}' (${url})"
    fi
}

# --- checks ------------------------------------------------------------

echo "Smoke testing $BASE_URL"
echo

echo "[1] Top-level routes return 200"
for path in "/" "/match" "/demos" "/contribute" "/use" "/roadmap" \
            "/walkthroughs/cassi" "/walkthroughs/cacti" \
            "/benchmarks/L3-003" "/benchmarks/L3-004" \
            "/principles" ; do
    require_200 "GET $path" "${BASE_URL}${path}"
done
echo

echo "[2] /match API returns confidence > 2.0 for hyperspectral query"
match_body=$(http_body "${BASE_URL}/api/match?q=hyperspectral+snapshot")
if [[ -n "$match_body" ]] && command -v jq >/dev/null 2>&1; then
    conf=$(echo "$match_body" | jq -r '.results[0].confidence // 0' 2>/dev/null || echo 0)
    if awk -v c="$conf" 'BEGIN{exit !(c+0 > 2.0)}'; then
        ok "/match top result confidence=${conf} > 2.0"
    else
        bad "/match top result confidence=${conf} <= 2.0"
    fi
else
    bad "/match returned empty body or jq missing (got ${#match_body} bytes)"
fi
echo

echo "[3] /demos serves all 16 sample previews"
for i in 01 02 03 04 05 06 07 08 09 10 ; do
    code=$(http_code "${BASE_URL}/api/demos/cassi/sample_${i}/preview.png")
    if [[ "$code" == "200" ]]; then
        ok "cassi sample_${i} preview HTTP 200"
    else
        bad "cassi sample_${i} preview HTTP ${code}"
    fi
done
for i in 01 02 03 04 05 06 ; do
    code=$(http_code "${BASE_URL}/api/demos/cacti/sample_${i}/preview.png")
    if [[ "$code" == "200" ]]; then
        ok "cacti sample_${i} preview HTTP 200"
    else
        bad "cacti sample_${i} preview HTTP ${code}"
    fi
done
echo

echo "[4] /api/network reports current network"
net_body=$(http_body "${BASE_URL}/api/network")
if [[ -n "$net_body" ]]; then
    ok "/api/network responsive (body: $(echo "$net_body" | head -c 80))"
else
    bad "/api/network returned empty body"
fi
echo

echo "[5] Health endpoint"
require_200 "GET /health" "${BASE_URL}/health"
echo

# --- summary -----------------------------------------------------------
echo "================================================================"
echo "PASS: ${PASS}"
echo "FAIL: ${FAIL}"
if (( FAIL > 0 )); then
    echo
    echo "Failures:"
    for r in "${FAIL_REASONS[@]}"; do
        echo "  - $r"
    done
    exit 1
fi
echo "All explorer smoke checks passed."
exit 0
