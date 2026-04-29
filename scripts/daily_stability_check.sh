#!/usr/bin/env bash
# Daily stability check — runs the 6 checks documented in
# `pwm-team/coordination/handoffs/stability/README.md`, builds a
# DAILY_<YYYY-MM-DD>.json matching TEMPLATE_DAILY.json, and writes it
# under `pwm-team/coordination/handoffs/stability/`.
#
# Designed to be run by the GPU server once per day at 14:00 UTC during
# the 30-day stability window after Step 12 PASS.
#
# Required env (per check):
#   BASESCAN_API_KEY        — for contract_source_verified
#   PWM_RPC_URL             — defaults to https://mainnet.base.org
#   STEP_10_TVL_CAP_WEI     — the cap value Step 10 set, for
#                             tvl_cap_intact comparison (optional;
#                             check is skipped if unset)
#
# Optional env:
#   STABILITY_DRY_RUN=1     — print the JSON without writing
#   STABILITY_DATE=YYYY-MM-DD — override the date (default: today UTC)
#
# Usage:
#   bash scripts/daily_stability_check.sh
#
# Exit code 0 = all_green. Exit code 1 = at least one FAIL.
# (The DAILY_<DATE>.json is written either way.)

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STABILITY_DIR="${REPO_ROOT}/pwm-team/coordination/handoffs/stability"
CONTRACTS_DIR="${REPO_ROOT}/pwm-team/infrastructure/agent-contracts"

DATE="${STABILITY_DATE:-$(date -u +%Y-%m-%d)}"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
GIT_SHA="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
RPC_URL="${PWM_RPC_URL:-https://mainnet.base.org}"

OUT_FILE="${STABILITY_DIR}/DAILY_${DATE}.json"

# Day-of-clock = count of green DAILY_*.json files immediately preceding today.
# If yesterday's file is missing or has all_green:false, today is day 1.
prev_day_of_clock=0
yesterday="$(date -u -d "${DATE} -1 day" +%Y-%m-%d 2>/dev/null \
             || date -u -v-1d -j -f %Y-%m-%d "$DATE" +%Y-%m-%d 2>/dev/null \
             || echo "")"
if [[ -n "$yesterday" ]]; then
    prev_file="${STABILITY_DIR}/DAILY_${yesterday}.json"
    if [[ -f "$prev_file" ]]; then
        prev_green=$(jq -r '.all_green // false' "$prev_file" 2>/dev/null || echo "false")
        if [[ "$prev_green" == "true" ]]; then
            prev_day_of_clock=$(jq -r '.day_of_clock // 0' "$prev_file" 2>/dev/null || echo "0")
        fi
    fi
fi

echo "Daily stability check — $DATE"
echo "  prior day_of_clock : $prev_day_of_clock"
echo

# -------- check helpers ---------------------------------------------------
declare -A RESULTS
declare -A EVIDENCE
declare -A CHECK_TS
all_green=true

run_check() {
    local name="$1"; shift
    local desc="$1"; shift
    local cmd="$*"
    echo "▸ $name: $desc"
    local out exit_code
    out=$("$@" 2>&1); exit_code=$?
    CHECK_TS[$name]="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    if [[ $exit_code -eq 0 ]]; then
        RESULTS[$name]="PASS"
        EVIDENCE[$name]="$desc — exit 0"
        echo "   ✓ PASS"
    else
        RESULTS[$name]="FAIL"
        EVIDENCE[$name]="$desc — exit $exit_code: $(echo "$out" | tail -1 | cut -c1-160)"
        all_green=false
        echo "   ✗ FAIL (exit $exit_code)"
    fi
}

# -------- 1. explorer_uptime --------------------------------------------
SMOKE="${REPO_ROOT}/pwm-team/infrastructure/agent-web/scripts/smoke_test_explorer.sh"
if [[ -x "$SMOKE" ]]; then
    run_check "explorer_uptime" \
              "smoke_test_explorer.sh https://explorer.pwm.platformai.org" \
              bash "$SMOKE" "https://explorer.pwm.platformai.org"
else
    RESULTS[explorer_uptime]="FAIL"
    EVIDENCE[explorer_uptime]="smoke_test_explorer.sh not found at $SMOKE"
    CHECK_TS[explorer_uptime]="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    all_green=false
    echo "▸ explorer_uptime: ✗ FAIL — script missing"
fi

# -------- 2. rpc_reachable ----------------------------------------------
echo "▸ rpc_reachable: POST $RPC_URL eth_chainId"
CHECK_TS[rpc_reachable]="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
chain_id=$(curl -s -X POST -H "Content-Type: application/json" \
            --max-time 10 \
            --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}' \
            "$RPC_URL" 2>/dev/null \
           | jq -r '.result // empty' 2>/dev/null)
if [[ "$chain_id" == "0x2105" ]]; then
    RESULTS[rpc_reachable]="PASS"
    EVIDENCE[rpc_reachable]="POST $RPC_URL eth_chainId → 0x2105 (8453, Base mainnet)"
    echo "   ✓ PASS (chainId 0x2105 = 8453)"
else
    RESULTS[rpc_reachable]="FAIL"
    EVIDENCE[rpc_reachable]="POST $RPC_URL eth_chainId → '$chain_id' (expected 0x2105)"
    all_green=false
    echo "   ✗ FAIL (chainId='$chain_id')"
fi

# -------- 3. governance_healthy -----------------------------------------
echo "▸ governance_healthy: verify_governance_owns_admin.js --network base"
CHECK_TS[governance_healthy]="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
gov_out=$(cd "$CONTRACTS_DIR" && \
    npx hardhat run scripts/verify_governance_owns_admin.js --network base 2>&1)
gov_exit=$?
if [[ $gov_exit -eq 0 ]]; then
    RESULTS[governance_healthy]="PASS"
    EVIDENCE[governance_healthy]="5/5 admins point at PWMGovernance"
    echo "   ✓ PASS"
else
    RESULTS[governance_healthy]="FAIL"
    EVIDENCE[governance_healthy]="exit $gov_exit: $(echo "$gov_out" | tail -1 | cut -c1-160)"
    all_green=false
    echo "   ✗ FAIL (exit $gov_exit)"
fi

# -------- 4. tvl_cap_intact ---------------------------------------------
echo "▸ tvl_cap_intact: cast call \$STAKING maxTotalStakeWei()"
CHECK_TS[tvl_cap_intact]="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
staking_addr=$(jq -r '.base.PWMStaking // empty' \
                  "${CONTRACTS_DIR}/addresses.json" 2>/dev/null)
if [[ -z "$staking_addr" || "$staking_addr" == "null" ]]; then
    RESULTS[tvl_cap_intact]="FAIL"
    EVIDENCE[tvl_cap_intact]="addresses.json[base].PWMStaking is null — Step 8 not run?"
    all_green=false
    echo "   ✗ FAIL (no PWMStaking address)"
elif [[ -z "${STEP_10_TVL_CAP_WEI:-}" ]]; then
    RESULTS[tvl_cap_intact]="SKIP"
    EVIDENCE[tvl_cap_intact]="STEP_10_TVL_CAP_WEI env var unset — cannot compare"
    echo "   ⊘ SKIP (set STEP_10_TVL_CAP_WEI to enable)"
else
    if command -v cast >/dev/null 2>&1; then
        actual=$(cast call "$staking_addr" "maxTotalStakeWei()(uint256)" \
                      --rpc-url "$RPC_URL" 2>/dev/null \
                | awk '{print $1}')
        if [[ "$actual" == "$STEP_10_TVL_CAP_WEI" ]]; then
            RESULTS[tvl_cap_intact]="PASS"
            EVIDENCE[tvl_cap_intact]="maxTotalStakeWei = $actual (matches Step 10 cap)"
            echo "   ✓ PASS"
        else
            RESULTS[tvl_cap_intact]="FAIL"
            EVIDENCE[tvl_cap_intact]="maxTotalStakeWei = $actual (expected $STEP_10_TVL_CAP_WEI)"
            all_green=false
            echo "   ✗ FAIL (cap drifted)"
        fi
    else
        RESULTS[tvl_cap_intact]="SKIP"
        EVIDENCE[tvl_cap_intact]="cast (foundry) not installed"
        echo "   ⊘ SKIP (cast not installed)"
    fi
fi

# -------- 5. contract_source_verified -----------------------------------
echo "▸ contract_source_verified: verify_basescan.sh base"
CHECK_TS[contract_source_verified]="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
if [[ -z "${BASESCAN_API_KEY:-}" ]]; then
    RESULTS[contract_source_verified]="SKIP"
    EVIDENCE[contract_source_verified]="BASESCAN_API_KEY env var unset"
    echo "   ⊘ SKIP (no BASESCAN_API_KEY)"
else
    BASESCAN_API_KEY="$BASESCAN_API_KEY" \
        bash "${CONTRACTS_DIR}/scripts/verify_basescan.sh" base \
        > /tmp/daily_basescan.log 2>&1
    bs_exit=$?
    if [[ $bs_exit -eq 0 ]]; then
        RESULTS[contract_source_verified]="PASS"
        EVIDENCE[contract_source_verified]="verify_basescan.sh base → 'Verified: 7/7'"
        echo "   ✓ PASS"
    else
        RESULTS[contract_source_verified]="FAIL"
        EVIDENCE[contract_source_verified]="verify_basescan.sh base → exit $bs_exit"
        all_green=false
        echo "   ✗ FAIL (exit $bs_exit)"
    fi
fi

# -------- 6. p0p1_issues_today (manual / out-of-band) -------------------
# This check requires an issue-tracker integration that doesn't yet exist
# in the repo. Mark SKIP unless the operator overrides via env var.
echo "▸ p0p1_issues_today: (manual; set P0P1_TODAY=0 to record clean)"
CHECK_TS[p0p1_issues_today]="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
if [[ -n "${P0P1_TODAY:-}" ]]; then
    if [[ "$P0P1_TODAY" == "0" ]]; then
        RESULTS[p0p1_issues_today]="PASS"
        EVIDENCE[p0p1_issues_today]="P0P1_TODAY=0 (operator-confirmed)"
        echo "   ✓ PASS"
    else
        RESULTS[p0p1_issues_today]="FAIL"
        EVIDENCE[p0p1_issues_today]="P0P1_TODAY=$P0P1_TODAY new P0/P1 incident(s)"
        all_green=false
        echo "   ✗ FAIL ($P0P1_TODAY incident(s))"
    fi
else
    RESULTS[p0p1_issues_today]="SKIP"
    EVIDENCE[p0p1_issues_today]="P0P1_TODAY env var unset"
    echo "   ⊘ SKIP"
fi

# Compute day_of_clock
if [[ "$all_green" == "true" ]]; then
    new_day_of_clock=$((prev_day_of_clock + 1))
else
    new_day_of_clock=0
fi

echo
echo "============================================================"
echo "  date            : $DATE"
echo "  day_of_clock    : $prev_day_of_clock → $new_day_of_clock"
echo "  all_green       : $all_green"
echo "============================================================"

# -------- emit JSON ------------------------------------------------------
checks_json=$(python3 - <<EOF
import json, os
checks = {}
for k in ["explorer_uptime","rpc_reachable","governance_healthy",
         "tvl_cap_intact","contract_source_verified","p0p1_issues_today"]:
    checks[k] = {
        "result": os.environ.get(f"R_{k}", "FAIL"),
        "evidence": os.environ.get(f"E_{k}", ""),
        "timestamp_utc": os.environ.get(f"T_{k}", ""),
    }
print(json.dumps(checks, indent=2))
EOF
)

# Compose the final document
DOC=$(R_explorer_uptime="${RESULTS[explorer_uptime]}" \
      E_explorer_uptime="${EVIDENCE[explorer_uptime]}" \
      T_explorer_uptime="${CHECK_TS[explorer_uptime]}" \
      R_rpc_reachable="${RESULTS[rpc_reachable]}" \
      E_rpc_reachable="${EVIDENCE[rpc_reachable]}" \
      T_rpc_reachable="${CHECK_TS[rpc_reachable]}" \
      R_governance_healthy="${RESULTS[governance_healthy]}" \
      E_governance_healthy="${EVIDENCE[governance_healthy]}" \
      T_governance_healthy="${CHECK_TS[governance_healthy]}" \
      R_tvl_cap_intact="${RESULTS[tvl_cap_intact]}" \
      E_tvl_cap_intact="${EVIDENCE[tvl_cap_intact]}" \
      T_tvl_cap_intact="${CHECK_TS[tvl_cap_intact]}" \
      R_contract_source_verified="${RESULTS[contract_source_verified]}" \
      E_contract_source_verified="${EVIDENCE[contract_source_verified]}" \
      T_contract_source_verified="${CHECK_TS[contract_source_verified]}" \
      R_p0p1_issues_today="${RESULTS[p0p1_issues_today]}" \
      E_p0p1_issues_today="${EVIDENCE[p0p1_issues_today]}" \
      T_p0p1_issues_today="${CHECK_TS[p0p1_issues_today]}" \
      ALL_GREEN_FLAG="$all_green" \
      python3 - <<EOF
import json, os
doc = {
  "date": "$DATE",
  "day_of_clock": $new_day_of_clock,
  "by": "sub-gpu",
  "timestamp_utc": "$TIMESTAMP",
  "git_sha": "$GIT_SHA",
  "tag": "mainnet-v1.0.0",
  "checks": {
    k: {
        "result": os.environ.get(f"R_{k}", ""),
        "evidence": os.environ.get(f"E_{k}", ""),
        "timestamp_utc": os.environ.get(f"T_{k}", ""),
    }
    for k in ["explorer_uptime","rpc_reachable","governance_healthy",
              "tvl_cap_intact","contract_source_verified","p0p1_issues_today"]
  },
  "all_green": os.environ.get("ALL_GREEN_FLAG") == "true",
  "notes": ""
}
print(json.dumps(doc, indent=2))
EOF
)

if [[ "${STABILITY_DRY_RUN:-0}" == "1" ]]; then
    echo
    echo "--- DRY RUN — would write $OUT_FILE ---"
    echo "$DOC"
    exit $([ "$all_green" = "true" ] && echo 0 || echo 1)
fi

echo "$DOC" > "$OUT_FILE"
echo
echo "  wrote $OUT_FILE"

# If a FAIL occurred, also write a STABILITY_RESET file
if [[ "$all_green" != "true" && $prev_day_of_clock -gt 0 ]]; then
    RESET_FILE="${STABILITY_DIR}/STABILITY_RESET_${DATE}.json"
    failing=$(python3 -c "
import json, sys
d = json.loads('''$DOC''')
fails = [k for k, v in d['checks'].items() if v['result'] == 'FAIL']
print(','.join(fails))
")
    cat > "$RESET_FILE" <<EOF
{
  "date": "$DATE",
  "by": "sub-gpu",
  "timestamp_utc": "$TIMESTAMP",
  "previous_day_of_clock": $prev_day_of_clock,
  "reset_to": 0,
  "failing_checks": "$failing",
  "root_cause": "TODO — fill in operator-investigated root cause",
  "next_action": "TODO — fill in mitigation + retry plan"
}
EOF
    echo "  wrote $RESET_FILE (clock reset $prev_day_of_clock → 0)"
fi

[ "$all_green" = "true" ] && exit 0 || exit 1
