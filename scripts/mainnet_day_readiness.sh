#!/usr/bin/env bash
# Mainnet-day readiness check — one command.
#
# Verifies all gates that should clear before executing Step 8
# (`contracts-deployed`) from MAINNET_DEPLOY_HANDOFF.md. Green means
# you can run `npx hardhat run deploy/mainnet.js --network base` today
# without surprises.
#
# Checks:
#   1. STEP_{1..7}__*.PASS.json files exist in handoffs/ or _archive/
#   2. The unblock_steps test suite passes (407+ tests)
#   3. No TODO/FIXME/XXX/HACK markers in the deploy + verifier scripts
#   4. The mainnet-v1.0.0 git tag exists and resolves to a commit
#   5. addresses.json[base] is unpopulated (so Step 8 isn't a re-run)
#
# Usage:
#   bash scripts/mainnet_day_readiness.sh
#
# Exit code 0 = all gates green. Exit code 1 = at least one red gate.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

GREEN_COUNT=0
RED_COUNT=0
WARN_COUNT=0
LINES=()
RED_REASONS=()

ok()    { LINES+=("  ✓ $*"); GREEN_COUNT=$((GREEN_COUNT + 1)); }
bad()   { LINES+=("  ✗ $*"); RED_COUNT=$((RED_COUNT + 1)); RED_REASONS+=("$*"); }
warn()  { LINES+=("  ⚠ $*"); WARN_COUNT=$((WARN_COUNT + 1)); }
note()  { LINES+=("    $*"); }
section() { LINES+=(""); LINES+=("=== $1 ==="); }

# ---- 1. PASS files for Steps 1-7 ----------------------------------------
section "1. Pre-deploy gate PASS files (Steps 1-7)"

for step in 1 2 3 4 5 6 7; do
    found=$(find pwm-team/coordination/handoffs \
                -maxdepth 2 \
                -name "STEP_${step}__*.PASS.json" 2>/dev/null \
            | head -1)
    if [[ -z "$found" ]]; then
        # Distinguish "no READY committed" from "READY committed but not yet PASSed"
        ready=$(find pwm-team/coordination/handoffs \
                    -maxdepth 2 \
                    -name "STEP_${step}__*.READY.json" 2>/dev/null \
                | head -1)
        if [[ -n "$ready" ]]; then
            bad "STEP_${step}: READY committed but no PASS yet (${ready#"$REPO_ROOT/"})"
        else
            bad "STEP_${step}: no READY/PASS in handoffs/"
        fi
    else
        slug=$(basename "$found" \
               | sed -E 's/^STEP_[0-9]+__([^.]+)\.PASS\.json$/\1/')
        ok "STEP_${step} (${slug})"
        note "${found#"$REPO_ROOT/"}"
    fi
done

# ---- 2. Unblock-steps test suite ----------------------------------------
section "2. Unblock-steps test suite"

PYTEST_OUT=$(python3 -m pytest pwm-team/coordination/tests/unblock_steps \
                 --override-ini="addopts=" -q 2>&1)
PYTEST_EXIT=$?

# Extract the summary line (last non-empty line that mentions passed/failed/error)
SUMMARY=$(echo "$PYTEST_OUT" \
          | grep -E "passed|failed|error" \
          | tail -1)

if [[ $PYTEST_EXIT -eq 0 ]]; then
    ok "pytest: ${SUMMARY:-passed}"
else
    bad "pytest: exit code $PYTEST_EXIT — ${SUMMARY:-no summary}"
    # On failure, surface the FAILED lines for debugging
    echo "$PYTEST_OUT" | grep -E "FAILED|ERROR" | head -10 \
        | while IFS= read -r ln; do LINES+=("    ${ln}"); done
fi

# ---- 3. Static check: no TODO/FIXME/XXX/HACK in deploy + verifier scripts ---
section "3. Static check on deploy + verifier scripts"

DEPLOY_FILES=(
    pwm-team/infrastructure/agent-contracts/deploy/mainnet.js
    pwm-team/infrastructure/agent-contracts/deploy/l2.js
    pwm-team/infrastructure/agent-contracts/deploy/testnet.js
    pwm-team/infrastructure/agent-contracts/scripts/transfer_admin_to_governance.js
    pwm-team/infrastructure/agent-contracts/scripts/verify_governance_owns_admin.js
    pwm-team/infrastructure/agent-contracts/scripts/verify-all.js
    pwm-team/infrastructure/agent-contracts/scripts/export-abis.js
    pwm-team/infrastructure/agent-contracts/scripts/verify_basescan.sh
    scripts/verify_l2_deploy.py
    scripts/count_external_l4.py
    scripts/count_founder_mining_txns.py
)

# Pattern: word-boundary-anchored TODO/FIXME/XXX/HACK
PATTERN='\b(TODO|FIXME|XXX|HACK)\b'

for f in "${DEPLOY_FILES[@]}"; do
    if [[ ! -f "$f" ]]; then
        bad "$f: not found"
        continue
    fi
    hits=$(grep -nE "$PATTERN" "$f" 2>/dev/null || true)
    if [[ -n "$hits" ]]; then
        bad "$f: $(echo "$hits" | wc -l | tr -d ' ') TODO/FIXME marker(s)"
        echo "$hits" | head -3 \
            | while IFS= read -r ln; do LINES+=("    ${ln}"); done
        if [[ $(echo "$hits" | wc -l) -gt 3 ]]; then
            note "(... and more)"
        fi
    else
        ok "$f"
    fi
done

# ---- 4. mainnet-v1.0.0 tag exists ---------------------------------------
section "4. mainnet-v1.0.0 git tag"

if sha=$(git rev-parse mainnet-v1.0.0^{commit} 2>/dev/null); then
    ok "mainnet-v1.0.0 → ${sha:0:12}"
    if ! git merge-base --is-ancestor "$sha" HEAD 2>/dev/null; then
        warn "mainnet-v1.0.0 is not an ancestor of HEAD — audit lineage may be off"
    fi
else
    bad "mainnet-v1.0.0 tag not found"
fi

# ---- 5. addresses.json[base] is unpopulated -----------------------------
section "5. Pre-deploy state (addresses.json[base])"

ADDRS_BASE_STATE=$(python3 - <<'PY' 2>&1
import json, sys
p = "pwm-team/infrastructure/agent-contracts/addresses.json"
addrs = json.load(open(p))
base = addrs.get("base") or {}
contract_keys = ["PWMRegistry","PWMMinting","PWMStaking",
                 "PWMCertificate","PWMReward","PWMTreasury","PWMGovernance"]
populated = [k for k in contract_keys if base.get(k)]
if populated:
    print(f"POPULATED:{','.join(populated)}")
    sys.exit(1)
print("UNPOPULATED")
PY
)
if [[ "$ADDRS_BASE_STATE" == "UNPOPULATED" ]]; then
    ok "addresses.json[base] is unpopulated (Step 8 has not run)"
elif [[ "$ADDRS_BASE_STATE" == POPULATED:* ]]; then
    bad "addresses.json[base] is already populated — Step 8 may have run"
    note "populated keys: ${ADDRS_BASE_STATE#POPULATED:}"
    note "If this is a re-deploy, verify intent before continuing"
else
    bad "addresses.json[base] state check errored: ${ADDRS_BASE_STATE}"
fi

# ---- 6. Optional: signers.md fully populated ----------------------------
section "6. multisig/signers.md state"

SIGNERS_STATE=$(python3 - <<'PY' 2>&1
import re
p = "pwm-team/infrastructure/agent-contracts/multisig/signers.md"
text = open(p).read()
populated = re.findall(r"^\|\s*[1-5]\s*\|\s*0x[0-9a-fA-F]{40}", text, re.MULTILINE)
print(f"{len(populated)}")
PY
)
case "$SIGNERS_STATE" in
    5) ok "multisig/signers.md has 5 populated founder rows" ;;
    0) bad "multisig/signers.md is in template state (Step 6 not done)" ;;
    *) bad "multisig/signers.md has $SIGNERS_STATE populated rows (expected 0 or 5)" ;;
esac

# ---- Verdict -------------------------------------------------------------
echo
echo "============================================================"
echo "  Mainnet-day readiness check"
echo "============================================================"
for line in "${LINES[@]}"; do
    echo "$line"
done
echo
echo "  Green: ${GREEN_COUNT}    Red: ${RED_COUNT}    Warn: ${WARN_COUNT}"
echo "------------------------------------------------------------"

if [[ $RED_COUNT -gt 0 ]]; then
    echo "  ✗ NOT READY for Step 8."
    echo "  Reasons:"
    for r in "${RED_REASONS[@]}"; do
        echo "    - $r"
    done
    exit 1
fi

cat <<'NEXT'
  ✓ All gates green — you can run Step 8 today.

  Next:
    cd pwm-team/infrastructure/agent-contracts
    git checkout mainnet-v1.0.0
    npm ci
    PWM_PRIVATE_KEY=$DEPLOYER_PK \
      FOUNDER_ADDRESSES="$(comma-joined 5 addresses from multisig/signers.md)" \
      npx hardhat run deploy/mainnet.js --network base

  Then verify:
    BASESCAN_API_KEY=$KEY \
      bash pwm-team/infrastructure/agent-contracts/scripts/verify_basescan.sh base
    PWM_RPC_URL=https://mainnet.base.org \
      python scripts/verify_l2_deploy.py --network base

NEXT
exit 0
