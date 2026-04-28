#!/usr/bin/env bash
# Verify all 7 PWM contracts on Basescan (or Etherscan for L1).
#
# Usage:
#   bash scripts/verify_basescan.sh <network>
# where <network> is one of: base, baseSepolia, mainnet, testnet
#
# Reads addresses from pwm-team/infrastructure/agent-contracts/addresses.json
# and queries the appropriate explorer's getsourcecode endpoint. Prints
# one line per contract; exits 0 only if all 7 are verified.
#
# Required env:
#   BASESCAN_API_KEY  (for base / baseSepolia)
#   ETHERSCAN_API_KEY (for mainnet / testnet)
#
# Per MAINNET_DEPLOY_PLAN.md exit signal #1:
#   "All 7 contracts return verified-source-code = true"

set -uo pipefail

NETWORK="${1:-}"
if [[ -z "$NETWORK" ]]; then
    echo "Usage: $0 <network> (base | baseSepolia | mainnet | testnet)"
    exit 2
fi

case "$NETWORK" in
    base)
        API_HOST="https://api.basescan.org/api"
        API_KEY="${BASESCAN_API_KEY:-}"
        EXPLORER_HOST="https://basescan.org"
        ;;
    baseSepolia)
        API_HOST="https://api-sepolia.basescan.org/api"
        API_KEY="${BASESCAN_API_KEY:-}"
        EXPLORER_HOST="https://sepolia.basescan.org"
        ;;
    mainnet)
        API_HOST="https://api.etherscan.io/api"
        API_KEY="${ETHERSCAN_API_KEY:-}"
        EXPLORER_HOST="https://etherscan.io"
        ;;
    testnet)
        API_HOST="https://api-sepolia.etherscan.io/api"
        API_KEY="${ETHERSCAN_API_KEY:-}"
        EXPLORER_HOST="https://sepolia.etherscan.io"
        ;;
    *)
        echo "Unsupported network: $NETWORK"
        exit 2
        ;;
esac

if [[ -z "$API_KEY" ]]; then
    echo "Missing API key env var for $NETWORK."
    echo "Set BASESCAN_API_KEY (for base*) or ETHERSCAN_API_KEY (for mainnet/testnet)."
    exit 2
fi

# Find addresses.json by walking up from this script.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADDR_FILE="$SCRIPT_DIR/../addresses.json"
if [[ ! -f "$ADDR_FILE" ]]; then
    echo "addresses.json not found at $ADDR_FILE"
    exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "jq required (apt install jq)"
    exit 2
fi

CONTRACTS=(
    PWMGovernance
    PWMRegistry
    PWMTreasury
    PWMReward
    PWMStaking
    PWMCertificate
    PWMMinting
)

PASS=0
FAIL=0

for c in "${CONTRACTS[@]}"; do
    addr=$(jq -r ".\"${NETWORK}\".\"${c}\" // empty" "$ADDR_FILE")
    if [[ -z "$addr" || "$addr" == "null" ]]; then
        echo "  ✗ $c: address is null in addresses.json[$NETWORK]"
        FAIL=$((FAIL + 1))
        continue
    fi

    resp=$(curl -ks --max-time 30 \
        "${API_HOST}?module=contract&action=getsourcecode&address=${addr}&apikey=${API_KEY}")
    src_len=$(echo "$resp" | jq -r '.result[0].SourceCode // "" | length' 2>/dev/null || echo 0)

    if [[ "${src_len:-0}" -gt 0 ]]; then
        echo "  ✓ $c: verified ($EXPLORER_HOST/address/$addr)"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $c: UNVERIFIED at $addr"
        FAIL=$((FAIL + 1))
    fi
done

echo
echo "================================================================"
echo "Network: $NETWORK"
echo "Verified: $PASS / 7"
echo "Unverified: $FAIL"

if (( FAIL > 0 )); then
    exit 1
fi
exit 0
