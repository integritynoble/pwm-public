#!/usr/bin/env bash
# Pre-mainnet Go/No-Go gate.
#
# Run this BEFORE broadcasting any mainnet tx. Each check is read-only and
# fails the whole script with exit code 1 the moment any single check fails.
# A green run is the necessary (not sufficient) condition for proceeding to
# the dress-rehearsal + deploy steps in DIRECTOR_RUNBOOK_D1_TO_D10.
#
# Usage:
#   bash scripts/preflight_mainnet.sh
#
# Optional env vars:
#   PWM_PREFLIGHT_RPC_BASE        Base mainnet RPC (default: https://mainnet.base.org)
#   PWM_PREFLIGHT_DEPLOYER_ADDR   Deployer wallet to balance-check (default: from addresses.json)
#   PWM_PREFLIGHT_SKIP_RPC=1      Skip live RPC checks (for offline pre-validation)

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# ---- Python interpreter resolution (venv-aware) -------------------------
# Prefer a project venv over PATH. On Windows the venv ships only `python.exe`,
# and the bare `python3` lookup falls through to the Microsoft Store stub which
# has none of our deps (web3, pytest). Detect once and shadow `python3` so all
# call sites below stay unchanged.
if [ -z "${PYTHON:-}" ]; then
  if   [ -x ".venv/Scripts/python.exe" ]; then PYTHON=".venv/Scripts/python.exe"  # Windows venv
  elif [ -x ".venv/bin/python3"        ]; then PYTHON=".venv/bin/python3"          # Unix venv
  elif [ -x "venv/Scripts/python.exe"  ]; then PYTHON="venv/Scripts/python.exe"
  elif [ -x "venv/bin/python3"         ]; then PYTHON="venv/bin/python3"
  elif command -v python3 >/dev/null 2>&1; then PYTHON="python3"
  elif command -v python  >/dev/null 2>&1; then PYTHON="python"
  else
    echo "ERROR: no python3 / python found. Activate a venv or set \$PYTHON." >&2
    exit 1
  fi
fi
python3() { "$PYTHON" "$@"; }

# ---- ANSI helpers --------------------------------------------------------
RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; CYAN=$'\033[36m'; RESET=$'\033[0m'
PASS_COUNT=0; FAIL_COUNT=0; WARN_COUNT=0

pass() { echo "  ${GREEN}✓${RESET} $1"; PASS_COUNT=$((PASS_COUNT+1)); }
fail() { echo "  ${RED}✗${RESET} $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }
warn() { echo "  ${YELLOW}⚠${RESET} $1"; WARN_COUNT=$((WARN_COUNT+1)); }
section() { echo; echo "${CYAN}── $1 ──${RESET}"; }

# ---- 1. Hash drift on the 6 founder-vetted Sepolia registrations ---------
section "1. Sepolia hash-drift check (must match on-chain)"

if python3 -m pytest scripts/test_register_genesis.py -q > /tmp/preflight_step1.txt 2>&1; then
  TESTS=$(grep -oE '[0-9]+ passed' /tmp/preflight_step1.txt | head -1)
  pass "scripts/test_register_genesis.py — $TESTS"
else
  fail "scripts/test_register_genesis.py FAILED"
  echo "    stash output: cat /tmp/preflight_step1.txt"
fi

# Cross-check actual L1-003 + L1-004 + L3-003 + L3-004 hashes inline
python3 - <<'PY' && pass "L1-003, L1-004, L3-003, L3-004 hashes match Sepolia on-chain values" || fail "Tier 1 hash drift detected — manifest changed since registration"
import json, sys
sys.path.insert(0, "scripts")
from register_genesis import _canonical_json
from web3 import Web3
EXPECTED = {
    "l1/L1-003.json": "0xe3b1328c66835cd729fa50650ef1d1bac4aa407807d6d97d4979e988a99a51ea",
    "l1/L1-004.json": "0xa2ae37946ef2822a308a4e60245dd2655070190cf8f3913559ae36286b26a56b",
    "l3/L3-003.json": "0xdc8ad0dc68682eff750188c8d4d84179b3f7deddee1af562bc3b085794048b4a",
    "l3/L3-004.json": "0x052324ba0585e4cf320914e117bf9b08656d602b9ac753b289a6a75ba926eab4",
}
for relpath, expected in EXPECTED.items():
    m = json.load(open(f"pwm-team/pwm_product/genesis/{relpath}"))
    got = "0x" + Web3.keccak(_canonical_json(m)).hex().lstrip("0x").zfill(64)
    if got != expected:
        sys.exit(f"DRIFT: {relpath} computed={got} expected={expected}")
PY

# ---- 2. Canonical primitives — all 533 L1 ---------------------------------
section "2. Canonical-primitive compliance (all 533 L1)"

if python3 -m pytest scripts/test_canonical_primitives.py -q > /tmp/preflight_step2.txt 2>&1; then
  TESTS=$(grep -oE '[0-9]+ passed' /tmp/preflight_step2.txt | head -1)
  pass "scripts/test_canonical_primitives.py — $TESTS"
else
  fail "scripts/test_canonical_primitives.py FAILED — non-canonical primitive detected"
fi

# ---- 3. Working tree is clean (no uncommitted changes) -------------------
section "3. Working-tree state"

if git diff --quiet HEAD 2>/dev/null && git diff --cached --quiet 2>/dev/null; then
  pass "Working tree clean (no uncommitted changes)"
else
  warn "Uncommitted changes exist — confirm intentional before deploy day"
fi

# ---- 4. mainnet-v1.0.0 audit tag is reachable ---------------------------
section "4. Audit tag presence"

if git rev-parse --verify mainnet-v1.0.0 > /dev/null 2>&1; then
  TAG_SHA=$(git rev-parse mainnet-v1.0.0)
  HEAD_SHA=$(git rev-parse HEAD)
  pass "mainnet-v1.0.0 tag exists at $(git rev-parse --short mainnet-v1.0.0)"
  if [ "$TAG_SHA" = "$HEAD_SHA" ]; then
    pass "HEAD = mainnet-v1.0.0 (deploying audit-clean tag)"
  else
    warn "HEAD ($(git rev-parse --short HEAD)) is NOT on mainnet-v1.0.0 — deploy commits beyond audit have not been re-audited"
  fi
else
  fail "mainnet-v1.0.0 tag not found — anything you deploy is unaudited"
fi

# ---- 5. addresses.json:mainnet is null at start -------------------------
section "5. addresses.json:mainnet pre-deploy state"

MAINNET_REGISTRY=$(python3 -c "import json; print(json.load(open('pwm-team/coordination/agent-coord/interfaces/addresses.json'))['mainnet']['PWMRegistry'])" 2>/dev/null)
if [ "$MAINNET_REGISTRY" = "None" ] || [ -z "$MAINNET_REGISTRY" ]; then
  pass "addresses.json:mainnet.PWMRegistry is null (correct pre-deploy state)"
else
  warn "addresses.json:mainnet.PWMRegistry already set to $MAINNET_REGISTRY — confirm deploy already happened or roll back"
fi

# ---- 6. Founder addresses set in env (or 5-element list) ----------------
section "6. Founder-multisig addresses"

if [ -n "${FOUNDER_ADDRESSES:-}" ]; then
  N=$(echo "$FOUNDER_ADDRESSES" | tr ',' '\n' | wc -l)
  if [ "$N" -eq 5 ]; then
    pass "FOUNDER_ADDRESSES env var has 5 entries"
  else
    fail "FOUNDER_ADDRESSES has $N entries (need exactly 5)"
  fi
else
  warn "FOUNDER_ADDRESSES env not set — deploy/testnet.js will fail at line 41 unless you export it before mainnet.js runs"
fi

# ---- 7. Deployer balance on Base mainnet --------------------------------
section "7. Deployer balance on Base mainnet"

if [ "${PWM_PREFLIGHT_SKIP_RPC:-}" = "1" ]; then
  warn "Skipped (PWM_PREFLIGHT_SKIP_RPC=1)"
else
  RPC="${PWM_PREFLIGHT_RPC_BASE:-https://mainnet.base.org}"
  DEPLOYER="${PWM_PREFLIGHT_DEPLOYER_ADDR:-$(python3 -c "import json; print(json.load(open('pwm-team/coordination/agent-coord/interfaces/addresses.json'))['testnet']['deployer'])" 2>/dev/null)}"
  if [ -z "$DEPLOYER" ]; then
    warn "Cannot determine deployer address (set PWM_PREFLIGHT_DEPLOYER_ADDR)"
  else
    BAL_WEI=$(python3 - "$RPC" "$DEPLOYER" <<'PY' 2>/dev/null
import sys
from web3 import Web3
rpc, addr = sys.argv[1], sys.argv[2]
w3 = Web3(Web3.HTTPProvider(rpc))
print(w3.eth.get_balance(Web3.to_checksum_address(addr)))
PY
)
    if [ -n "$BAL_WEI" ] && [ "$BAL_WEI" != "0" ]; then
      BAL_ETH=$(python3 -c "print(round(int('$BAL_WEI') / 1e18, 4))")
      MIN_BAL_WEI=50000000000000000  # 0.05 ETH
      if [ "$BAL_WEI" -ge "$MIN_BAL_WEI" ] 2>/dev/null; then
        pass "Deployer $DEPLOYER on Base mainnet has $BAL_ETH ETH (≥ 0.05 ETH minimum)"
      else
        fail "Deployer $DEPLOYER has only $BAL_ETH ETH on Base mainnet (need ≥ 0.05 ETH for 7 deploys + retries)"
      fi
    else
      fail "Deployer $DEPLOYER has 0 ETH on Base mainnet (or RPC error)"
    fi
  fi
fi

# ---- 8. Smart-contract test suite --------------------------------------
section "8. Smart-contract test suite (Hardhat)"

CONTRACTS_DIR="pwm-team/infrastructure/agent-contracts"
if [ -d "$CONTRACTS_DIR/node_modules" ]; then
  if (cd "$CONTRACTS_DIR" && npx hardhat test --network hardhat > /tmp/preflight_step8.txt 2>&1); then
    TESTS=$(grep -oE '[0-9]+ passing' /tmp/preflight_step8.txt | head -1)
    pass "Hardhat suite — $TESTS"
  else
    fail "Hardhat suite FAILED (output in /tmp/preflight_step8.txt)"
  fi
else
  warn "$CONTRACTS_DIR/node_modules not installed — run 'npm ci' before deploy day"
fi

# ---- 9. ABI files synced to interfaces/ --------------------------------
section "9. ABI files in interfaces/"

ABI_DIR="pwm-team/coordination/agent-coord/interfaces/contracts_abi"
EXPECTED_ABIS=(PWMRegistry PWMCertificate PWMReward PWMTreasury PWMMinting PWMStaking PWMGovernance)
ALL_PRESENT=1
for c in "${EXPECTED_ABIS[@]}"; do
  if [ ! -f "$ABI_DIR/$c.json" ]; then
    fail "Missing ABI: $ABI_DIR/$c.json"
    ALL_PRESENT=0
  fi
done
[ "$ALL_PRESENT" = "1" ] && pass "All 7 ABIs present in $ABI_DIR/"

# ---- Summary ------------------------------------------------------------
section "Summary"

echo "  Passed: $PASS_COUNT"
echo "  Warned: $WARN_COUNT"
echo "  Failed: $FAIL_COUNT"
echo

if [ "$FAIL_COUNT" -gt 0 ]; then
  echo "${RED}✗ NO-GO — fix the $FAIL_COUNT failure(s) above before mainnet deploy.${RESET}"
  exit 1
elif [ "$WARN_COUNT" -gt 0 ]; then
  echo "${YELLOW}⚠ CONDITIONAL GO — $WARN_COUNT warning(s) need acknowledgment.${RESET}"
  echo "  Common warnings (FOUNDER_ADDRESSES unset, dress-rehearsal env vars) are"
  echo "  not blockers — they just need to be set before you run deploy/mainnet.js."
  exit 0
else
  echo "${GREEN}✓ GO — all $PASS_COUNT preflight checks passed.${RESET}"
  echo "  Next: Phase 1 (Base Sepolia dress rehearsal). See"
  echo "  pwm-team/coordination/DIRECTOR_RUNBOOK_D1_TO_D10_2026-05-01.md."
  exit 0
fi
