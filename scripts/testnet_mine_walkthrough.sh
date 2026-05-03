#!/usr/bin/env bash
# Full lifecycle walkthrough: stake -> mine for CASSI + CACTI on Sepolia testnet.
#
# Per Director request 2026-05-03: end-to-end demonstration of all 4 PWM layers
# on Ethereum Sepolia (chainId 11155111). Submits MST-L cert for L3-003 (CASSI)
# and EfficientSCI cert for L3-004 (CACTI), populating the leaderboard with
# real PSNR jumps over the deliberately-weak reference solvers.
#
# What this script does (in order):
#   1. Pre-flight: confirms env vars + funded wallet + CLI installed
#   2. Computes on-chain artifact hashes from genesis JSON manifests
#      (using the keccak256(canonical_json) convention that PWMRegistry expects)
#   3. CASSI lifecycle:
#      a. stake principle L1-003 (~$50 worth of PWM at L1 tier)
#      b. stake benchmark L3-003 (~$1 at L3 tier)
#      c. mine L3-003 using cassi_mst.py (runs solver locally, submits cert)
#   4. CACTI lifecycle (only if SKIP_CACTI is unset and EfficientSCI weights present):
#      a. stake principle L1-004
#      b. stake benchmark L3-004
#      c. mine L3-004 using cacti_efficientsci.py
#   5. Prints next steps (challenge period, finalize, leaderboard URL)
#
# Knobs (env vars):
#   PWM_PRIVATE_KEY       (required) 0x-prefixed hex for your funded Sepolia wallet
#   SEPOLIA_RPC_URL       (required) e.g. https://ethereum-sepolia-rpc.publicnode.com
#   SKIP_STAKE=1          skip the L1+L3 stake steps (mine only)
#   SKIP_CACTI=1          skip CACTI half (CASSI only)
#   CASSI_ONLY=1          alias for SKIP_CACTI=1
#   DRY_RUN=1             pwm-node mine --dry-run (no on-chain tx)
#
# Exit codes:
#   0  all requested steps succeeded
#   1  pre-flight failure (missing env vars, CLI not installed, etc.)
#   2  stake step failed
#   3  mine step failed
#   4  hash computation failed
#
# Usage:
#   export PWM_PRIVATE_KEY=0x<your-funded-Sepolia-key>
#   export SEPOLIA_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
#   bash scripts/testnet_mine_walkthrough.sh
#
#   # CASSI only (skip CACTI which needs EfficientSCI weights):
#   CASSI_ONLY=1 bash scripts/testnet_mine_walkthrough.sh
#
#   # Dry-run (no real txs):
#   DRY_RUN=1 bash scripts/testnet_mine_walkthrough.sh

set -uo pipefail

# ─── Color helpers ──────────────────────────────────────────────────────
if [ -t 1 ]; then
  RED='\033[0;31m'; GRN='\033[0;32m'; YEL='\033[1;33m'; CYN='\033[0;36m'; NC='\033[0m'
else
  RED=''; GRN=''; YEL=''; CYN=''; NC=''
fi

step()  { printf "\n${CYN}═══ %s ═══${NC}\n" "$*"; }
ok()    { printf "${GRN}✓${NC} %s\n" "$*"; }
warn()  { printf "${YEL}⚠${NC}  %s\n" "$*"; }
fail()  { printf "${RED}✗${NC} %s\n" "$*" >&2; }

# ─── Locate repo root ───────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# ─── Step 1: pre-flight ─────────────────────────────────────────────────
step "Step 1 — Pre-flight"

if [ -z "${PWM_PRIVATE_KEY:-}" ]; then
  fail "PWM_PRIVATE_KEY not set. Export your funded Sepolia private key first."
  exit 1
fi
ok "PWM_PRIVATE_KEY set"

if [ -z "${SEPOLIA_RPC_URL:-}" ]; then
  warn "SEPOLIA_RPC_URL not set; defaulting to public node"
  export SEPOLIA_RPC_URL="https://ethereum-sepolia-rpc.publicnode.com"
fi
export PWM_RPC_URL="$SEPOLIA_RPC_URL"
ok "SEPOLIA_RPC_URL: $SEPOLIA_RPC_URL"

if ! command -v pwm-node >/dev/null 2>&1; then
  fail "pwm-node CLI not on PATH. Install with: pip install -e pwm-team/infrastructure/agent-cli"
  exit 1
fi
ok "pwm-node CLI: $(command -v pwm-node)"

if ! python3 -c "import eth_utils" 2>/dev/null; then
  fail "Python eth_utils not installed. Run: pip install eth_utils"
  exit 1
fi
ok "Python eth_utils available"

# Wallet balance sanity-check
WALLET_ADDR=$(python3 -c "
from eth_account import Account
a = Account.from_key('${PWM_PRIVATE_KEY}')
print(a.address)
" 2>/dev/null)

if [ -z "$WALLET_ADDR" ]; then
  fail "Could not derive wallet address from PWM_PRIVATE_KEY"
  exit 1
fi
ok "Wallet address: $WALLET_ADDR"

BALANCE_WEI=$(curl -s "$SEPOLIA_RPC_URL" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_getBalance\",\"params\":[\"$WALLET_ADDR\",\"latest\"],\"id\":1}" \
  | python3 -c "import sys,json; print(int(json.load(sys.stdin)['result'], 16))" 2>/dev/null)

if [ -z "$BALANCE_WEI" ] || [ "$BALANCE_WEI" = "0" ]; then
  fail "Wallet $WALLET_ADDR has 0 Sepolia ETH. Get from a faucet:"
  fail "  https://sepoliafaucet.com    https://www.alchemy.com/faucets/ethereum-sepolia"
  exit 1
fi
BALANCE_ETH=$(python3 -c "print(f'{$BALANCE_WEI / 1e18:.4f}')")
ok "Sepolia ETH balance: $BALANCE_ETH ETH"

# ─── Step 2: compute on-chain artifact hashes ───────────────────────────
step "Step 2 — Compute artifact hashes (keccak256 canonical-JSON)"

HASHES=$(python3 <<'PYEOF' 2>&1
import json, sys
from pathlib import Path

try:
    from eth_utils import keccak
except ImportError:
    print("FATAL: eth_utils not installed", file=sys.stderr)
    sys.exit(1)

repo = Path(".")
for layer, kind in [("l1","003"),("l1","004"),("l2","003"),("l2","004"),("l3","003"),("l3","004")]:
    path = repo / "pwm-team" / "pwm_product" / "genesis" / layer / f"{layer.upper()}-{kind}.json"
    if not path.exists():
        print(f"FATAL: {path} missing", file=sys.stderr)
        sys.exit(2)
    obj = json.loads(path.read_text())
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    h = "0x" + keccak(canonical).hex()
    print(f"export {layer.upper()}{kind}_HASH={h}")
PYEOF
)
HASH_RC=$?
if [ "$HASH_RC" -ne 0 ]; then
  fail "Hash computation failed: $HASHES"
  exit 4
fi

# Source the export lines so the hashes are available as env vars
eval "$HASHES"
ok "L1-003 (CASSI principle):  $L1003_HASH"
ok "L2-003 (CASSI spec):       $L2003_HASH"
ok "L3-003 (CASSI benchmark):  $L3003_HASH"
ok "L1-004 (CACTI principle):  $L1004_HASH"
ok "L2-004 (CACTI spec):       $L2004_HASH"
ok "L3-004 (CACTI benchmark):  $L3004_HASH"

# ─── Step 3: CASSI lifecycle ────────────────────────────────────────────
step "Step 3 — CASSI lifecycle (L1-003 → L3-003 → mine MST-L)"

if [ -z "${SKIP_STAKE:-}" ]; then
  warn "Staking on CASSI principle L1-003 (~\$50 worth of PWM at L1 tier)..."
  if pwm-node --network testnet stake principle "$L1003_HASH"; then
    ok "Staked on L1-003"
  else
    warn "Stake on L1-003 failed (may already be staked — continuing)"
  fi

  warn "Staking on CASSI benchmark L3-003 (~\$1 worth of PWM at L3 tier)..."
  if pwm-node --network testnet stake benchmark "$L3003_HASH"; then
    ok "Staked on L3-003"
  else
    warn "Stake on L3-003 failed (may already be staked — continuing)"
  fi
else
  warn "SKIP_STAKE set — skipping CASSI stake steps"
fi

DRY_FLAG=""
[ -n "${DRY_RUN:-}" ] && DRY_FLAG="--dry-run"

warn "Mining L3-003 with cassi_mst.py (runs solver locally, may take 3-30 min)..."
if pwm-node --network testnet mine L3-003 \
     --solver pwm-team/pwm_product/reference_solvers/cassi/cassi_mst.py \
     $DRY_FLAG; then
  ok "CASSI mining complete"
else
  fail "CASSI mining failed (exit $?)"
  exit 3
fi

# ─── Step 4: CACTI lifecycle (optional) ─────────────────────────────────
if [ -n "${SKIP_CACTI:-}${CASSI_ONLY:-}" ]; then
  warn "SKIP_CACTI / CASSI_ONLY set — skipping CACTI half"
else
  step "Step 4 — CACTI lifecycle (L1-004 → L3-004 → mine EfficientSCI)"

  # Sanity-check EfficientSCI weights are present before attempting
  EFFICIENTSCI_WEIGHTS="public/packages/pwm_core/weights/efficientsci/efficientsci_base.pth"
  if [ ! -f "$EFFICIENTSCI_WEIGHTS" ]; then
    warn "EfficientSCI weights NOT present at $EFFICIENTSCI_WEIGHTS"
    warn "Download from https://github.com/ucaswangls/EfficientSCI before running CACTI"
    warn "Skipping CACTI half. Re-run with weights present, or use CASSI_ONLY=1."
  else
    if [ -z "${SKIP_STAKE:-}" ]; then
      warn "Staking on CACTI principle L1-004..."
      pwm-node --network testnet stake principle "$L1004_HASH" \
        || warn "Stake on L1-004 failed (may already be staked)"

      warn "Staking on CACTI benchmark L3-004..."
      pwm-node --network testnet stake benchmark "$L3004_HASH" \
        || warn "Stake on L3-004 failed (may already be staked)"
    fi

    warn "Mining L3-004 with cacti_efficientsci.py..."
    if pwm-node --network testnet mine L3-004 \
         --solver pwm-team/pwm_product/reference_solvers/cacti/cacti_efficientsci.py \
         $DRY_FLAG; then
      ok "CACTI mining complete"
    else
      fail "CACTI mining failed (exit $?)"
      exit 3
    fi
  fi
fi

# ─── Step 5: next-steps summary ─────────────────────────────────────────
step "Step 5 — Done. Next steps."

cat <<EOF

Submitted certificates enter a ${YEL}7-day challenge period${NC}. During this
window, anyone can challenge by calling
  PWMCertificate.challenge(cert_hash, proof)
If the challenge succeeds (proof of fraud / scoring error), the
submitter loses their stake.

After 7 days with no successful challenge, anyone (including you) calls:
  pwm-node --network testnet finalize <cert_hash>
This triggers PWMReward.distribute() → rank-1 wins 40% of the pool,
rank-2 wins 5%, rank-3 wins 2%, rank-4-10 win 1% each, ~52% rolls over.

${CYN}Verify the submission on-chain:${NC}
  PWMCertificate: https://sepolia.etherscan.io/address/0x8963b60454EC1D9F65eE3cbF7aBC5D1220C3dB08#events
  Wallet history: https://sepolia.etherscan.io/address/$WALLET_ADDR

${CYN}See it on the leaderboard (~1-2 min after tx confirmation):${NC}
  CASSI: https://explorer.pwm.platformai.org/benchmarks/L3-003
  CACTI: https://explorer.pwm.platformai.org/benchmarks/L3-004

${CYN}Enrich the leaderboard row${NC} with solver label + PSNR-as-dB
(after step 1a + 1b of the action checklist):
  bash scripts/submit_cert_meta.sh /tmp/pwm-out/cassi-mst/meta.json

EOF

ok "Walkthrough complete."
