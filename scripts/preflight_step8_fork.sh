#!/usr/bin/env bash
# Pre-flight Step 8 (contracts-deployed) against a Hardhat fork of Base mainnet.
#
# Spends ZERO real ETH. Catches deploy-time issues — gas estimation,
# RPC quirks, contract size limits, library wiring — before mainnet day.
#
# Flow:
#   1. Snapshot addresses.json (will be overwritten by the deploy)
#   2. Start `hardhat node --fork https://mainnet.base.org` in background
#   3. Run deploy/testnet.js against `--network localhost` (which is
#      the forked Base mainnet under the hood)
#   4. Read addresses from addresses.json[local]
#   5. Run verify_governance_owns_admin.js to confirm Step 9 wiring
#   6. Restore addresses.json regardless of pass/fail
#
# Requirements:
#   - Network access to https://mainnet.base.org (or BASE_RPC_URL)
#   - npm packages installed in pwm-team/infrastructure/agent-contracts
#   - jq available
#
# Usage:
#   bash scripts/preflight_step8_fork.sh
#
#   # Pin to a specific block for reproducibility:
#   FORK_BLOCK=12345678 bash scripts/preflight_step8_fork.sh
#
#   # Use an Alchemy / QuickNode RPC for higher rate limits:
#   BASE_RPC_URL=https://base-mainnet.g.alchemy.com/v2/$KEY \
#       bash scripts/preflight_step8_fork.sh
#
# Exit code 0 = green (Step 8 will work on mainnet).
# Exit code 1 = red (Step 8 has a problem).

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONTRACTS_DIR="${REPO_ROOT}/pwm-team/infrastructure/agent-contracts"
ADDRESSES_FILE="${CONTRACTS_DIR}/addresses.json"
ADDRESSES_BAK="/tmp/pwm_preflight_addresses.bak.$$"
NODE_LOG="/tmp/pwm_preflight_hardhat_node.$$.log"
DEPLOY_LOG="/tmp/pwm_preflight_deploy.$$.log"
VERIFY_LOG="/tmp/pwm_preflight_verify.$$.log"
NODE_PID=""

cleanup() {
    local rc=$?
    echo
    echo "--- cleanup ---"
    if [[ -n "$NODE_PID" ]] && kill -0 "$NODE_PID" 2>/dev/null; then
        echo "  stopping hardhat node (pid $NODE_PID)"
        kill "$NODE_PID" 2>/dev/null || true
        wait "$NODE_PID" 2>/dev/null || true
    fi
    if [[ -f "$ADDRESSES_BAK" ]]; then
        echo "  restoring addresses.json from snapshot"
        cp "$ADDRESSES_BAK" "$ADDRESSES_FILE"
        rm -f "$ADDRESSES_BAK"
    fi
    echo "  log files:"
    echo "    node:    $NODE_LOG"
    echo "    deploy:  $DEPLOY_LOG"
    echo "    verify:  $VERIFY_LOG"
    exit $rc
}
trap cleanup EXIT INT TERM

FORK_URL="${BASE_RPC_URL:-https://mainnet.base.org}"
HARDHAT_PORT="${HARDHAT_PORT:-8545}"

echo "============================================================"
echo "  Step 8 pre-flight against Hardhat fork of Base mainnet"
echo "============================================================"
echo "  fork URL : $FORK_URL"
echo "  port     : $HARDHAT_PORT"
[[ -n "${FORK_BLOCK:-}" ]] && echo "  block    : $FORK_BLOCK"
echo

# ---- 1. Snapshot ---------------------------------------------------------
echo "1. Snapshotting addresses.json"
cp "$ADDRESSES_FILE" "$ADDRESSES_BAK"
echo "   ✓ saved to $ADDRESSES_BAK"
echo

# ---- 2. Start hardhat node fork -----------------------------------------
echo "2. Starting hardhat node (forked from $FORK_URL)"
cd "$CONTRACTS_DIR"

NODE_CMD=(npx hardhat node
          --hostname 127.0.0.1
          --port "$HARDHAT_PORT"
          --fork "$FORK_URL")
[[ -n "${FORK_BLOCK:-}" ]] && NODE_CMD+=(--fork-block-number "$FORK_BLOCK")

"${NODE_CMD[@]}" > "$NODE_LOG" 2>&1 &
NODE_PID=$!
echo "   started pid $NODE_PID; waiting up to 60 s for RPC..."

READY=false
for i in $(seq 1 60); do
    response=$(curl -s -o /dev/null -w "%{http_code}" \
                    -X POST -H "Content-Type: application/json" \
                    --max-time 2 \
                    --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}' \
                    "http://127.0.0.1:${HARDHAT_PORT}" 2>/dev/null \
                || echo "000")
    if [[ "$response" == "200" ]]; then
        READY=true
        break
    fi
    sleep 1
done

if [[ "$READY" != "true" ]]; then
    echo "   ✗ hardhat node did not become ready"
    echo "   --- last 20 lines of node log ---"
    tail -20 "$NODE_LOG" | sed 's/^/   /'
    exit 1
fi
echo "   ✓ RPC ready at http://127.0.0.1:${HARDHAT_PORT}"

# Confirm we're really forking from Base
chain_id_hex=$(curl -s -X POST \
                    -H "Content-Type: application/json" \
                    --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}' \
                    "http://127.0.0.1:${HARDHAT_PORT}" \
               | jq -r '.result // "null"')
chain_id=$((chain_id_hex))
echo "   chainId reported by node: $chain_id"
# Hardhat default is 31337; the forked state is Base mainnet's, but the local
# node always reports its own chain ID (31337). That's fine for preflight —
# we're testing deploy mechanics, not chainId-dependent logic.

echo

# ---- 3. Run deploy ------------------------------------------------------
echo "3. Running deploy/testnet.js against forked node"
echo "   (PWM_ALLOW_OVERWRITE=1 — addresses.json[local] will be overwritten and restored after)"

# Use the hardhat default first signer's known test key (no real funds).
# This key is one of hardhat's deterministic 20 accounts; it's funded
# in the local node by default but holds no real-world ETH.
HARDHAT_FIRST_TEST_KEY="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

PWM_ALLOW_OVERWRITE=1 \
    PWM_PRIVATE_KEY="$HARDHAT_FIRST_TEST_KEY" \
    DEPLOYER_PRIVATE_KEY="$HARDHAT_FIRST_TEST_KEY" \
    npx hardhat run deploy/testnet.js --network localhost \
    > "$DEPLOY_LOG" 2>&1
DEPLOY_EXIT=$?

if [[ $DEPLOY_EXIT -ne 0 ]]; then
    echo "   ✗ deploy failed (exit $DEPLOY_EXIT)"
    echo "   --- last 30 lines of deploy log ---"
    tail -30 "$DEPLOY_LOG" | sed 's/^/   /'
    exit 1
fi
echo "   ✓ deploy completed"

# ---- 4. Verify addresses written ---------------------------------------
echo
echo "4. Verifying all 7 contract addresses in addresses.json[local]"
MISSING=()
for k in PWMRegistry PWMMinting PWMStaking PWMCertificate \
         PWMReward PWMTreasury PWMGovernance; do
    addr=$(jq -r ".local.${k} // \"null\"" "$ADDRESSES_FILE")
    if [[ "$addr" == "null" || -z "$addr" || "$addr" == "0x0000000000000000000000000000000000000000" ]]; then
        echo "   ✗ $k: $addr"
        MISSING+=("$k")
    else
        echo "   ✓ $k: $addr"
    fi
done
if [[ ${#MISSING[@]} -gt 0 ]]; then
    echo "   ✗ missing: ${MISSING[*]}"
    exit 1
fi

# ---- 5. Run verify_governance_owns_admin.js ----------------------------
echo
echo "5. Running verify_governance_owns_admin.js (post-handoff state)"
# IMPORTANT: must use `npx hardhat run --network localhost` (not bare `node`)
# so the script connects to our forked node at 127.0.0.1:8545 rather than
# spinning up hardhat's in-process network with no deployed contracts.
npx hardhat run scripts/verify_governance_owns_admin.js --network localhost \
    > "$VERIFY_LOG" 2>&1
VERIFY_EXIT=$?

if [[ $VERIFY_EXIT -ne 0 ]]; then
    echo "   ✗ verifier failed (exit $VERIFY_EXIT)"
    echo "   --- verify log ---"
    cat "$VERIFY_LOG" | sed 's/^/   /'
    exit 1
fi
echo "   ✓ all 5 admin contracts point at PWMGovernance"

# ---- Verdict -----------------------------------------------------------
echo
echo "============================================================"
echo "  ✓ PREFLIGHT GREEN"
echo "============================================================"
echo "  All 7 contracts deploy, wire, and hand off to PWMGovernance"
echo "  successfully against forked Base mainnet state."
echo
echo "  This means Step 8 + 9 will work mechanically on real Base"
echo "  mainnet. (Step 10's 48-h timelock is the only remaining"
echo "  wall-clock blocker before Step 11.)"
echo
echo "  Logs preserved in /tmp — see cleanup output above."
exit 0
