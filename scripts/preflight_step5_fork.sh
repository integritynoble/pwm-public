#!/usr/bin/env bash
# Pre-flight Step 5 (governance-rehearsal-sepolia) against a Hardhat fork.
#
# Differs from preflight_step8_fork.sh in two ways:
#   1. Forks Base SEPOLIA (not Base mainnet) — same chain you'll target
#      in the real Step 5 rehearsal.
#   2. After the deploy + governance handoff, also exercises the full
#      3-of-5 + 48 h timelock + execute proposal flow that the unblock
#      guide says to run as the rehearsal's seventh procedure step.
#      The 48 h wall-clock wait is skipped via evm_increaseTime, since
#      we're on a fork.
#
# Spends ZERO real Sepolia ETH. Catches issues — gas estimation, RPC
# quirks, founder-signer wiring, proposal lifecycle bugs — before the
# real rehearsal goes on-chain.
#
# Usage:
#   bash scripts/preflight_step5_fork.sh
#
#   # Pin to a specific block:
#   FORK_BLOCK=12345678 bash scripts/preflight_step5_fork.sh
#
#   # Use a higher-quota RPC:
#   BASE_SEPOLIA_RPC_URL=https://base-sepolia.g.alchemy.com/v2/$KEY \
#       bash scripts/preflight_step5_fork.sh
#
# Exit code 0 = green (the real rehearsal will work).
# Exit code 1 = red.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONTRACTS_DIR="${REPO_ROOT}/pwm-team/infrastructure/agent-contracts"
ADDRESSES_FILE="${CONTRACTS_DIR}/addresses.json"
ADDRESSES_BAK="/tmp/pwm_preflight5_addresses.bak.$$"
NODE_LOG="/tmp/pwm_preflight5_hardhat_node.$$.log"
DEPLOY_LOG="/tmp/pwm_preflight5_deploy.$$.log"
VERIFY_LOG="/tmp/pwm_preflight5_verify.$$.log"
PROPOSAL_LOG="/tmp/pwm_preflight5_proposal.$$.log"
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
    echo "    node:     $NODE_LOG"
    echo "    deploy:   $DEPLOY_LOG"
    echo "    verify:   $VERIFY_LOG"
    echo "    proposal: $PROPOSAL_LOG"
    exit $rc
}
trap cleanup EXIT INT TERM

FORK_URL="${BASE_SEPOLIA_RPC_URL:-https://sepolia.base.org}"
HARDHAT_PORT="${HARDHAT_PORT:-8545}"

echo "============================================================"
echo "  Step 5 pre-flight against Hardhat fork of Base Sepolia"
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
    tail -20 "$NODE_LOG" | sed 's/^/   /'
    exit 1
fi
echo "   ✓ RPC ready at http://127.0.0.1:${HARDHAT_PORT}"
echo

# ---- 3. Deploy + governance handoff ------------------------------------
echo "3. Running deploy/testnet.js against forked node"
# Hardhat's first deterministic test account (private key + address pairs).
# These accounts come pre-funded on a hardhat node fork, so they can both
# sign the deploy and act as founders for the proposal-flow rehearsal.
HARDHAT_FIRST_TEST_KEY="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

# Override the .env file's FOUNDER_ADDRESSES (which lists the testnet hot
# wallets) with hardhat's first 5 deterministic addresses, so that the
# proposal flow can use real hardhat signers for each founder.
HARDHAT_FOUNDERS=(
    "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
    "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
    "0x90F79bf6EB2c4f870365E785982E1f101E93b906"
    "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65"
)
HARDHAT_FOUNDERS_CSV="$(IFS=,; echo "${HARDHAT_FOUNDERS[*]}")"
echo "   founders override : $HARDHAT_FOUNDERS_CSV"

PWM_ALLOW_OVERWRITE=1 \
    PWM_PRIVATE_KEY="$HARDHAT_FIRST_TEST_KEY" \
    DEPLOYER_PRIVATE_KEY="$HARDHAT_FIRST_TEST_KEY" \
    FOUNDER_ADDRESSES="$HARDHAT_FOUNDERS_CSV" \
    npx hardhat run deploy/testnet.js --network localhost \
    > "$DEPLOY_LOG" 2>&1
DEPLOY_EXIT=$?

if [[ $DEPLOY_EXIT -ne 0 ]]; then
    echo "   ✗ deploy failed (exit $DEPLOY_EXIT)"
    tail -30 "$DEPLOY_LOG" | sed 's/^/   /'
    exit 1
fi
echo "   ✓ deploy completed"
echo

# ---- 4. Verify governance handoff --------------------------------------
echo "4. Running verify_governance_owns_admin.js"
npx hardhat run scripts/verify_governance_owns_admin.js --network localhost \
    > "$VERIFY_LOG" 2>&1
VERIFY_EXIT=$?

if [[ $VERIFY_EXIT -ne 0 ]]; then
    echo "   ✗ verifier failed (exit $VERIFY_EXIT)"
    cat "$VERIFY_LOG" | sed 's/^/   /'
    exit 1
fi
echo "   ✓ all 5 admin contracts point at PWMGovernance"
echo

# ---- 5. Exercise the 3-of-5 + 48h timelock proposal flow --------------
echo "5. Running proposal lifecycle (propose → 3 approvals → skip 48h → execute)"
npx hardhat run scripts/preflight_proposal_flow.js --network localhost \
    > "$PROPOSAL_LOG" 2>&1
PROP_EXIT=$?

if [[ $PROP_EXIT -ne 0 ]]; then
    echo "   ✗ proposal flow failed (exit $PROP_EXIT)"
    cat "$PROPOSAL_LOG" | sed 's/^/   /'
    exit 1
fi
echo "   ✓ propose → 3-of-5 → execute → parameter set"
# Show the highlights from the proposal log
echo "   ---"
grep -E "^(A|B|C|D|E|F)\." "$PROPOSAL_LOG" | sed 's/^/   /'
echo

# ---- Verdict -----------------------------------------------------------
echo "============================================================"
echo "  ✓ STEP 5 PREFLIGHT GREEN"
echo "============================================================"
echo "  All 7 contracts deploy + wire + hand off to PWMGovernance, AND"
echo "  the full 3-of-5 + 48 h timelock proposal flow executes against"
echo "  forked Base Sepolia state. Parameter setParameter ran end-to-end."
echo
echo "  This means the real Step 5 rehearsal (Base Sepolia, real founder"
echo "  signers, real 48 h wait) will work mechanically. The only"
echo "  remaining unknowns are:"
echo "    - Real Sepolia faucet quotas / RPC throttling"
echo "    - Real founder hardware-wallet UX during signing"
echo
echo "  Logs preserved in /tmp — see cleanup output above."
exit 0
