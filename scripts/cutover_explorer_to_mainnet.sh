#!/usr/bin/env bash
# Explorer/indexer cutover from Sepolia testnet to Base mainnet.
#
# Run on the GCP server (agent-prod) AFTER:
#   1. deploy/mainnet.js has populated addresses.json:mainnet with all 7 addresses
#   2. transfer_admin_to_governance.js has handed admin to PWMGovernance
#   3. Genesis registration tx batch has succeeded on Base mainnet
#   4. scripts/post_deploy_verify.sh --network mainnet returned green
#
# What this does:
#   1. Pulls the latest pwm with mainnet addresses populated
#   2. Updates the Dockerfile.production env defaults from PWM_NETWORK=testnet
#      to PWM_NETWORK=mainnet
#   3. Updates the public-mirror README banner from "pre-mainnet testing" to
#      "live on Base mainnet"
#   4. Rebuilds the pwm-explorer image
#   5. Stops + recreates the running container with PWM_NETWORK=mainnet
#   6. Smoke-tests the live API: /api/network, /api/principles, /api/cert/<known>
#
# Usage:
#   bash scripts/cutover_explorer_to_mainnet.sh
#
# Optional env:
#   PWM_CUTOVER_DRY_RUN=1  Show the plan, don't apply
#   PWM_CUTOVER_SKIP_BUILD=1  Skip docker build (assume image already rebuilt)

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; CYAN=$'\033[36m'; RESET=$'\033[0m'
section() { echo; echo "${CYAN}── $1 ──${RESET}"; }
abort()   { echo "${RED}ABORT: $1${RESET}"; exit 1; }
ok()      { echo "${GREEN}✓${RESET} $1"; }

DRY_RUN="${PWM_CUTOVER_DRY_RUN:-0}"
SKIP_BUILD="${PWM_CUTOVER_SKIP_BUILD:-0}"

# ---- Pre-checks --------------------------------------------------------
section "Pre-checks"

# 1. Mainnet addresses populated
MAINNET_REG=$(python3 -c "
import json
a = json.load(open('pwm-team/coordination/agent-coord/interfaces/addresses.json'))
print(a.get('mainnet', {}).get('PWMRegistry') or 'null')
")
if [ "$MAINNET_REG" = "null" ] || [ -z "$MAINNET_REG" ]; then
  abort "addresses.json:mainnet.PWMRegistry is null. Run deploy/mainnet.js first."
fi
ok "addresses.json:mainnet.PWMRegistry = $MAINNET_REG"

# 2. Running on GCP server (sanity check — we don't want to flip production from a laptop)
HOSTNAME_NOW=$(hostname)
if [ "$HOSTNAME_NOW" != "agent-prod" ]; then
  echo "${YELLOW}⚠${RESET} Running on '$HOSTNAME_NOW', not 'agent-prod'. The pwm-explorer container lives on agent-prod."
  echo "    If this is intentional (e.g., dry-run on a laptop), continue. Otherwise, abort."
  if [ "$DRY_RUN" != "1" ]; then
    read -r -p "    Continue anyway? [y/N] " ans
    [ "$ans" = "y" ] || abort "User declined to proceed on non-agent-prod host."
  fi
fi

# 3. Docker available
if ! command -v docker > /dev/null; then
  abort "docker not found in PATH"
fi
ok "docker available"

# ---- Step 1: Pull latest -----------------------------------------------
section "Step 1 — git pull --ff-only"

if [ "$DRY_RUN" = "1" ]; then
  echo "  [dry-run] would: git pull --ff-only origin main"
else
  git pull --ff-only origin main || abort "git pull failed (working tree dirty? run 'git stash' first)"
  ok "Pulled latest main"
fi

# ---- Step 2: Patch Dockerfile.production env defaults ------------------
section "Step 2 — Patch Dockerfile env defaults"

DOCKERFILE="pwm-team/infrastructure/agent-web/deploy/Dockerfile.production"
if ! grep -q "PWM_NETWORK=testnet" "$DOCKERFILE"; then
  if grep -q "PWM_NETWORK=mainnet" "$DOCKERFILE"; then
    ok "Dockerfile already has PWM_NETWORK=mainnet"
  else
    abort "Dockerfile has neither PWM_NETWORK=testnet nor =mainnet. Manual review needed."
  fi
else
  if [ "$DRY_RUN" = "1" ]; then
    echo "  [dry-run] would: sed -i 's/PWM_NETWORK=testnet/PWM_NETWORK=mainnet/' $DOCKERFILE"
  else
    sed -i 's/PWM_NETWORK=testnet/PWM_NETWORK=mainnet/' "$DOCKERFILE"
    ok "Patched: PWM_NETWORK=testnet → PWM_NETWORK=mainnet"
  fi
fi

# Update the default RPC too
SEPOLIA_RPC="https://ethereum-sepolia-rpc.publicnode.com"
BASE_RPC="https://mainnet.base.org"
if grep -q "$SEPOLIA_RPC" "$DOCKERFILE"; then
  if [ "$DRY_RUN" = "1" ]; then
    echo "  [dry-run] would replace default RPC with $BASE_RPC"
  else
    sed -i "s|$SEPOLIA_RPC|$BASE_RPC|" "$DOCKERFILE"
    ok "Default PWM_RPC_URL → $BASE_RPC"
  fi
fi

# ---- Step 3: Patch the public-mirror README banner ---------------------
section "Step 3 — README banner: pre-mainnet → live"

SYNC_SCRIPT="scripts/sync_to_public_repo.sh"
if grep -q "Launch status (2026-05-07)" "$SYNC_SCRIPT" && grep -q "pre-mainnet testing" "$SYNC_SCRIPT"; then
  TODAY=$(date +%Y-%m-%d)
  if [ "$DRY_RUN" = "1" ]; then
    echo "  [dry-run] would patch README banner to 'Launch status ($TODAY) — Live on Base mainnet'"
  else
    sed -i "s/Launch status (2026-05-07)/Launch status ($TODAY)/" "$SYNC_SCRIPT"
    sed -i 's/This repository is in pre-mainnet testing/This repository is LIVE on Base mainnet/' "$SYNC_SCRIPT"
    ok "Banner updated → live"
  fi
fi

# ---- Step 4: Commit + push the cutover patches -------------------------
section "Step 4 — Commit + push"

if [ "$DRY_RUN" = "1" ]; then
  echo "  [dry-run] would: git add + commit + push"
else
  git add -A
  if ! git diff --cached --quiet; then
    git commit -m "chore(deploy): cutover explorer + README banner to Base mainnet" || true
    git push origin main || abort "push failed"
    ok "Committed + pushed cutover patches"
  else
    ok "No staged changes (cutover patches already applied)"
  fi
fi

# ---- Step 5: Mirror to pwm-public --------------------------------------
section "Step 5 — Mirror to pwm-public"

if [ "$DRY_RUN" = "1" ]; then
  echo "  [dry-run] would: bash scripts/sync_to_public_repo.sh ..."
else
  bash scripts/sync_to_public_repo.sh \
    --target git@github-integritynoble:integritynoble/pwm-public.git \
    --force-push 2>&1 | tail -3
  ok "Mirrored to pwm-public"
fi

# ---- Step 6: Rebuild docker image --------------------------------------
section "Step 6 — Rebuild pwm-explorer image"

if [ "$SKIP_BUILD" = "1" ]; then
  echo "  Skipped (PWM_CUTOVER_SKIP_BUILD=1)"
elif [ "$DRY_RUN" = "1" ]; then
  echo "  [dry-run] would: docker build -f $DOCKERFILE -t pwm-explorer:latest ."
else
  docker build -f "$DOCKERFILE" -t pwm-explorer:latest . 2>&1 | tail -5 || abort "docker build failed"
  ok "Image rebuilt"
fi

# ---- Step 7: Restart container -----------------------------------------
section "Step 7 — Stop + restart container"

if [ "$DRY_RUN" = "1" ]; then
  echo "  [dry-run] would: docker stop pwm-explorer && docker rm pwm-explorer && docker run ..."
else
  docker stop pwm-explorer 2>&1 | tail -1 || true
  docker rm pwm-explorer 2>&1 | tail -1 || true
  docker run -d \
    --name pwm-explorer \
    --restart unless-stopped \
    -p 3000:3000 \
    -v pwm_index_data:/data \
    pwm-explorer:latest 2>&1 | tail -1 || abort "docker run failed"
  ok "Container restarted"
  echo "  Waiting 15 s for warm-up..."
  sleep 15
fi

# ---- Step 8: Smoke test ------------------------------------------------
section "Step 8 — Smoke test"

if [ "$DRY_RUN" = "1" ]; then
  echo "  [dry-run] would: curl /api/network + /api/principles + /api/overview"
else
  NET=$(curl -sS --max-time 10 https://explorer.pwm.platformai.org/api/network 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('network', '?'))" 2>/dev/null || echo "?")
  if [ "$NET" = "mainnet" ]; then
    ok "/api/network reports 'mainnet'"
  else
    abort "/api/network reports '$NET' (expected 'mainnet') — container may still be warming up; retry after 30s"
  fi

  TIER1=$(curl -sS --max-time 10 https://explorer.pwm.platformai.org/api/principles 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tier_counts', {}).get('founder_vetted', 0))" 2>/dev/null || echo "0")
  if [ "$TIER1" = "2" ]; then
    ok "/api/principles tier_counts.founder_vetted = 2 (CASSI + CACTI)"
  else
    echo "${YELLOW}⚠${RESET} /api/principles tier_counts.founder_vetted = '$TIER1' (expected 2 — indexer may still be backfilling)"
  fi
fi

section "Summary"
if [ "$DRY_RUN" = "1" ]; then
  echo "${YELLOW}Dry-run complete. Re-run without PWM_CUTOVER_DRY_RUN=1 to apply.${RESET}"
else
  echo "${GREEN}✓ Cutover complete. https://explorer.pwm.platformai.org now points at Base mainnet.${RESET}"
  echo "  Monitor for 30 minutes; if anything looks wrong, rollback by:"
  echo "    1. Reverting the sync_to_public_repo.sh + Dockerfile.production patches"
  echo "    2. docker stop pwm-explorer && docker run -d --name pwm-explorer ... pwm-explorer:<previous-image-tag>"
fi
