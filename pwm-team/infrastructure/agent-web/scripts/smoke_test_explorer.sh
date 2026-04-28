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

echo "[2] /match returns L3-003 (CASSI) as strong match for structured query"
match_body=$(http_body "${BASE_URL}/api/match?modality=hyperspectral&domain=imaging")
if [[ -n "$match_body" ]] && command -v jq >/dev/null 2>&1; then
    top_id=$(echo "$match_body" | jq -r '.candidates[0].benchmark_id // empty' 2>/dev/null)
    top_score=$(echo "$match_body" | jq -r '.candidates[0].score // 0' 2>/dev/null || echo 0)
    top_band=$(echo "$match_body" | jq -r '.candidates[0].score_band // empty' 2>/dev/null)
    if [[ "$top_id" == "L3-003" ]] && awk -v c="$top_score" 'BEGIN{exit !(c+0 >= 2.0)}'; then
        ok "/match returns L3-003 with score=${top_score} band=${top_band}"
    else
        bad "/match top result is '${top_id}' score=${top_score} band=${top_band} (expected L3-003 with score >= 2.0)"
    fi
else
    bad "/match returned empty body or jq missing (got ${#match_body} bytes)"
fi
echo

echo "[3] /demos serves snapshot/solution PNGs for all 16 samples"
for i in 01 02 03 04 05 06 07 08 09 10 ; do
    for kind in snapshot solution ; do
        code=$(http_code "${BASE_URL}/api/demos/cassi/sample_${i}/${kind}.png")
        if [[ "$code" == "200" ]]; then
            ok "cassi sample_${i} ${kind}.png HTTP 200"
        else
            bad "cassi sample_${i} ${kind}.png HTTP ${code}"
        fi
    done
done
for i in 01 02 03 04 05 06 ; do
    for kind in snapshot solution ; do
        code=$(http_code "${BASE_URL}/api/demos/cacti/sample_${i}/${kind}.png")
        if [[ "$code" == "200" ]]; then
            ok "cacti sample_${i} ${kind}.png HTTP 200"
        else
            bad "cacti sample_${i} ${kind}.png HTTP ${code}"
        fi
    done
done
echo

echo "[4] /api/network reports current network"
net_body=$(http_body "${BASE_URL}/api/network")
if [[ -n "$net_body" ]] && command -v jq >/dev/null 2>&1; then
    net_name=$(echo "$net_body" | jq -r '.network // empty' 2>/dev/null)
    if [[ -n "$net_name" ]]; then
        ok "/api/network reports network='${net_name}'"
    else
        bad "/api/network response missing 'network' field (body: $(echo "$net_body" | head -c 80))"
    fi
else
    bad "/api/network returned empty body or jq missing"
fi
echo

echo "[5] Demo index lists CASSI + CACTI"
demos_body=$(http_body "${BASE_URL}/api/demos")
if [[ -n "$demos_body" ]] && command -v jq >/dev/null 2>&1; then
    cassi_present=$(echo "$demos_body" | jq -r '.demos[]?.name | select(. == "cassi")' 2>/dev/null)
    cacti_present=$(echo "$demos_body" | jq -r '.demos[]?.name | select(. == "cacti")' 2>/dev/null)
    if [[ "$cassi_present" == "cassi" && "$cacti_present" == "cacti" ]]; then
        ok "/api/demos lists both 'cassi' and 'cacti'"
    else
        bad "/api/demos missing cassi or cacti (cassi='${cassi_present}' cacti='${cacti_present}')"
    fi
else
    bad "/api/demos returned empty body or jq missing"
fi
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
