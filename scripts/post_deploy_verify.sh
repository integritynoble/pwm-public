#!/usr/bin/env bash
# Post-deploy verification — read freshly-deployed mainnet contracts and
# assert each peer-pointer matches addresses.json.
#
# This is the runtime answer to "did the cross-contract wiring complete
# correctly?" — deploy/testnet.js calls 11 setX() functions to wire the
# 7 contracts together; if any of those wiring txs silently no-op'd or
# pointed at the wrong address, mining will fail mysteriously days later.
#
# Run AFTER deploy/mainnet.js completes successfully but BEFORE running
# transfer_admin_to_governance.js. Catches:
#   1. Cross-contract pointer mismatches (PWMReward.registry() != PWMRegistry)
#   2. addresses.json drift from on-chain reality
#   3. Admin still pointing at deployer EOA instead of PWMGovernance
#
# Usage:
#   bash scripts/post_deploy_verify.sh [--network <slot>]
#
# Defaults: --network mainnet. Use --network testnet to run against Sepolia,
# or --network baseSepolia for the dress rehearsal.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

NETWORK="mainnet"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --network) NETWORK="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# ---- Resolve RPC + addresses for the chosen slot ------------------------
case "$NETWORK" in
  testnet)      RPC_DEFAULT="https://ethereum-sepolia-rpc.publicnode.com" ;;
  baseSepolia)  RPC_DEFAULT="https://sepolia.base.org" ;;
  base|mainnet) RPC_DEFAULT="https://mainnet.base.org" ;;
  arbSepolia)   RPC_DEFAULT="https://sepolia-rollup.arbitrum.io/rpc" ;;
  arbitrum)     RPC_DEFAULT="https://arb1.arbitrum.io/rpc" ;;
  optimism)     RPC_DEFAULT="https://mainnet.optimism.io" ;;
  *) echo "Unknown network: $NETWORK"; exit 1 ;;
esac

RPC="${PWM_RPC_URL:-$RPC_DEFAULT}"
ADDR_FILE="pwm-team/coordination/agent-coord/interfaces/addresses.json"

# ---- ANSI helpers --------------------------------------------------------
RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; CYAN=$'\033[36m'; RESET=$'\033[0m'
PASS=0; FAIL=0

ok()   { echo "  ${GREEN}✓${RESET} $1"; PASS=$((PASS+1)); }
err()  { echo "  ${RED}✗${RESET} $1"; FAIL=$((FAIL+1)); }
section() { echo; echo "${CYAN}── $1 ──${RESET}"; }

echo "Network: $NETWORK"
echo "RPC:     $RPC"
echo "Slot:    addresses.json[$NETWORK]"
echo

# ---- Load contract addresses --------------------------------------------
ADDRS=$(python3 -c "
import json, sys
a = json.load(open('$ADDR_FILE'))['$NETWORK']
for k in ('PWMGovernance','PWMRegistry','PWMTreasury','PWMReward',
          'PWMStaking','PWMCertificate','PWMMinting'):
    v = a.get(k)
    if not v or v in ('null', None):
        print(f'MISSING {k}', file=sys.stderr)
        sys.exit(2)
    print(f'{k}={v}')
")
if [ $? -ne 0 ]; then
  err "addresses.json[$NETWORK] missing one or more contract addresses — deploy/mainnet.js must complete first"
  echo "Network slot $NETWORK is not fully populated. Did deploy succeed?"
  exit 1
fi
eval "$ADDRS"
echo "Addresses loaded:"
echo "  PWMGovernance:  $PWMGovernance"
echo "  PWMRegistry:    $PWMRegistry"
echo "  PWMTreasury:    $PWMTreasury"
echo "  PWMReward:      $PWMReward"
echo "  PWMStaking:     $PWMStaking"
echo "  PWMCertificate: $PWMCertificate"
echo "  PWMMinting:     $PWMMinting"

# ---- Cross-contract pointer assertions + admin + multisig ------------
# All assertions run via web3.py to avoid the Foundry-cast dependency.
# A single Python block does the work and reports per-row results.
section "Cross-contract wiring + admin + multisig"

PY_RESULT=$(python3 - "$RPC" "$PWMGovernance" "$PWMRegistry" "$PWMTreasury" \
                       "$PWMReward" "$PWMStaking" "$PWMCertificate" "$PWMMinting" <<'PY'
import json, sys
from web3 import Web3

(rpc, gov, registry, treasury, reward, staking, cert, minting) = sys.argv[1:9]
w3 = Web3(Web3.HTTPProvider(rpc))
if not w3.is_connected():
    print(f"ERR|RPC unreachable: {rpc}")
    sys.exit(2)

# Minimal ABI fragments — just the view functions we assert on
GOV_ABI = [
    {"inputs": [], "name": "NUM_FOUNDERS",      "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "REQUIRED_APPROVALS", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
]
PEER_ABI = lambda name: {"inputs": [], "name": name, "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"}

def call(addr, abi, fn):
    try:
        c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=abi)
        return c.functions[fn]().call()
    except Exception as e:
        return f"ERR:{type(e).__name__}"

def lc(a):
    return a.lower() if isinstance(a, str) else str(a).lower()

# ---- 11 cross-contract pointer assertions ----
assertions = [
    ("PWMReward.certificate()",      reward,    "certificate", cert),
    ("PWMReward.staking()",          reward,    "staking",     staking),
    ("PWMReward.minting()",          reward,    "minting",     minting),
    ("PWMReward.treasury()",         reward,    "treasury",    treasury),
    ("PWMTreasury.reward()",         treasury,  "reward",      reward),
    ("PWMStaking.reward()",          staking,   "reward",      reward),
    ("PWMCertificate.registry()",    cert,      "registry",    registry),
    ("PWMCertificate.reward()",      cert,      "reward",      reward),
    ("PWMCertificate.minting()",     cert,      "minting",     minting),
    ("PWMMinting.certificate()",     minting,   "certificate", cert),
    ("PWMMinting.reward()",          minting,   "reward",      reward),
]
for label, addr, fn, expected in assertions:
    abi = [PEER_ABI(fn)]
    actual = call(addr, abi, fn)
    if isinstance(actual, str) and actual.startswith("ERR:"):
        print(f"ERR|{label} — call reverted ({actual})")
    elif lc(actual) == lc(expected):
        print(f"OK|{label} = {expected}")
    else:
        print(f"BAD|{label} MISMATCH: got={actual} expected={expected}")

# ---- 5 admin checks ----
admin_targets = [
    ("PWMTreasury",    treasury),
    ("PWMReward",      reward),
    ("PWMStaking",     staking),
    ("PWMCertificate", cert),
    ("PWMMinting",     minting),
]
for name, addr in admin_targets:
    actual = call(addr, [PEER_ABI("governance")], "governance")
    if isinstance(actual, str) and actual.startswith("ERR:"):
        print(f"ERR|{name}.governance() — call reverted ({actual})")
    elif lc(actual) == lc(gov):
        print(f"OK|{name}.governance() = PWMGovernance")
    else:
        print(f"BAD|{name}.governance() = {actual} (expected {gov} — admin NOT transferred)")

# ---- Multisig 3-of-5 ----
nf = call(gov, GOV_ABI, "NUM_FOUNDERS")
if isinstance(nf, str) and nf.startswith("ERR:"):
    print(f"ERR|PWMGovernance.NUM_FOUNDERS() — call reverted ({nf})")
elif nf == 5:
    print(f"OK|PWMGovernance.NUM_FOUNDERS() = 5 (multisig fully populated)")
else:
    print(f"BAD|PWMGovernance.NUM_FOUNDERS() = {nf} (expected 5)")

ra = call(gov, GOV_ABI, "REQUIRED_APPROVALS")
if isinstance(ra, str) and ra.startswith("ERR:"):
    print(f"ERR|PWMGovernance.REQUIRED_APPROVALS() — call reverted ({ra})")
elif ra == 3:
    print(f"OK|PWMGovernance.REQUIRED_APPROVALS() = 3 (3-of-5 multisig)")
else:
    print(f"BAD|PWMGovernance.REQUIRED_APPROVALS() = {ra} (expected 3)")
PY
)

while IFS='|' read -r status msg; do
  case "$status" in
    OK)  ok "$msg" ;;
    BAD|ERR) err "$msg" ;;
  esac
done <<< "$PY_RESULT"

# ---- Genesis registration check (best-effort) -------------------------
section "Genesis artifact registration"

# Compute the expected hashes from local manifests and ask PWMRegistry.exists()
python3 - <<PY 2>/dev/null && ok "Genesis L1-003, L1-004, L3-003, L3-004 all registered on-chain" || err "One or more genesis artifacts NOT registered yet — run register_genesis.py"
import json, sys
sys.path.insert(0, "scripts")
from register_genesis import _canonical_json
from web3 import Web3
import json as j

w3 = Web3(Web3.HTTPProvider("$RPC"))
abi_raw = j.load(open("pwm-team/coordination/agent-coord/interfaces/contracts_abi/PWMRegistry.json"))
abi = abi_raw["abi"] if isinstance(abi_raw, dict) and "abi" in abi_raw else abi_raw
registry = w3.eth.contract(
    address=Web3.to_checksum_address("$PWMRegistry"),
    abi=abi,
)
all_ok = True
for relpath in ("l1/L1-003.json", "l1/L1-004.json", "l3/L3-003.json", "l3/L3-004.json"):
    m = j.load(open(f"pwm-team/pwm_product/genesis/{relpath}"))
    h = Web3.keccak(_canonical_json(m))
    exists = registry.functions.exists(h).call()
    if not exists:
        all_ok = False
        break
sys.exit(0 if all_ok else 1)
PY

# ---- Summary ----------------------------------------------------------
section "Summary"
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
echo

if [ "$FAIL" -eq 0 ]; then
  echo "${GREEN}✓ Post-deploy verification GREEN — all wiring + admin pointers correct.${RESET}"
  echo "  Next: fund T_k pools, flip explorer to mainnet, update README banner."
  exit 0
else
  echo "${RED}✗ $FAIL post-deploy check(s) FAILED — investigate before going live.${RESET}"
  echo "  Most-common cause: a setX() wiring tx silently no-op'd or pointed at the wrong addr."
  echo "  Recovery: PWMGovernance multisig can correct any wiring via setX() — but pause first."
  exit 1
fi
