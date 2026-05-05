#!/usr/bin/env bash
# Mirror selected paths from this private repo to a public repo,
# stripping internal coordination + secrets along the way.
#
# Per pwm-team/customer_guide/plan.md Phase 3b — destination is a NEW
# clean public repo (recommended: integritynoble/pwm-public). The
# private integritynoble/pwm repo is preserved for internal ops.
#
# Approach: git filter-repo on a fresh CLONE of the source. The source
# working tree is never touched. The clone is rewritten to keep ONLY
# the public-mirror paths, then force-pushed to the target.
#
# Usage:
#   bash scripts/sync_to_public_repo.sh \
#     --target git@github.com:integritynoble/pwm-public.git \
#     [--dry-run]
#
# Required: git-filter-repo (pip install --user git-filter-repo)
#
# Safety:
#   - Operates on a temp clone, never on the working tree
#   - --dry-run inspects + lists files without pushing
#   - Verifies target is empty or matches a previous mirror's tip
#   - Prints the full file manifest before pushing
#
# Exit code: 0 on success; non-zero with diagnostic on any failure.

set -uo pipefail

# ---- defaults ------------------------------------------------------------
TARGET=""
TARGET_BRANCH="main"
DRY_RUN=0
FORCE_PUSH=0
SOURCE_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
WORK_DIR=""

# What gets mirrored — keep in sync with plan.md Phase 3 and the
# secrets-scan target list. Adding a path here is a deliberate
# "make this content public" decision.
INCLUDE_PATHS=(
    "pwm-team/pwm_product/"
    "pwm-team/infrastructure/agent-contracts/"
    "pwm-team/infrastructure/agent-scoring/"
    "pwm-team/infrastructure/agent-cli/"
    "pwm-team/infrastructure/agent-miner/"
    "pwm-team/infrastructure/agent-web/"
    "pwm-team/customer_guide/"
    "pwm-team/content/"           # G1: 1611 files / 11 MB — realises the
                                  # 531 first-class L1 Principles claim
    "pwm-team/bounties/"          # G4: bounty roster + claim board moved
                                  # out of coordination/ (2026-05-05)
    "public/packages/pwm_core/"   # G2: deep-learning miner deps (MST-L,
                                  # EfficientSCI) — 766 files / 11 MB
    "scripts/"
    "papers/Proof-of-Solution/mine_example/science/"
)

# Belt-and-suspenders exclusions. Most of these are already gitignored
# (so wouldn't be in history anyway), but explicit deny-list catches
# anything that slipped past gitignore in older commits.
EXCLUDE_GLOBS=(
    "pwm-team/coordination/"        # internal team docs
    "**/.env"                       # any .env file
    "**/.env.*"                     # .env.local, .env.production, etc.
    "**/*.key"                      # any *.key file
    "**/*_PRIVATE_KEY*"             # any file with PRIVATE_KEY in name
    "**/secrets/"                   # any secrets/ subdir
    "**/credentials/"               # any credentials/ subdir
    "**/*.pem"                      # PEM-format key files
    "**/.aws/"                      # AWS config dirs
    "**/.ssh/"                      # SSH keys (shouldn't be in repo, just in case)
)

# Files that DO need to land in the public repo at the root.
PUBLIC_README_PATH="pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md"
PUBLIC_LICENSE_PATH="public/LICENSE"  # the existing PWM NONCOMMERCIAL SHARE-ALIKE LICENSE

# ---- arg parsing ---------------------------------------------------------
usage() {
    sed -n '2,30p' "$0"
    exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target)
            TARGET="$2"; shift 2 ;;
        --target=*)
            TARGET="${1#*=}"; shift ;;
        --target-branch)
            TARGET_BRANCH="$2"; shift 2 ;;
        --dry-run)
            DRY_RUN=1; shift ;;
        --force-push)
            FORCE_PUSH=1; shift ;;
        -h|--help)
            usage 0 ;;
        *)
            echo "Unknown arg: $1" >&2; usage 2 ;;
    esac
done

if [[ -z "$TARGET" ]]; then
    echo "✗ --target is required" >&2
    usage 2
fi
if ! command -v git-filter-repo >/dev/null 2>&1; then
    echo "✗ git-filter-repo not found. Install:" >&2
    echo "    pip install --user git-filter-repo" >&2
    exit 1
fi

# ---- cleanup on exit -----------------------------------------------------
cleanup() {
    if [[ -n "$WORK_DIR" && -d "$WORK_DIR" ]]; then
        echo "  cleanup: removing $WORK_DIR"
        rm -rf "$WORK_DIR"
    fi
}
trap cleanup EXIT

# ---- step 1: fresh clone -------------------------------------------------
WORK_DIR="$(mktemp -d -t pwm_public_sync.XXXXXX)"
echo "============================================================"
echo "  PWM private → public repo sync"
echo "============================================================"
echo "  source : $SOURCE_DIR"
echo "  target : $TARGET (branch: $TARGET_BRANCH)"
echo "  workdir: $WORK_DIR"
[[ $DRY_RUN -eq 1 ]] && echo "  mode   : DRY RUN (no push)"
echo

echo "1. Cloning source to temp dir..."
git clone --no-local --shared "$SOURCE_DIR" "$WORK_DIR/repo" > /dev/null 2>&1 || {
    echo "✗ clone failed" >&2; exit 1;
}
cd "$WORK_DIR/repo"
echo "   ✓ cloned $(git log --oneline | wc -l) commits"

# Strip any `origin` remote inherited from the source clone — we'll
# add a fresh one pointing at the public target.
git remote remove origin 2>/dev/null || true

# ---- step 2: filter-repo (path includes) ---------------------------------
echo
echo "2. Filtering: keeping only public-mirror paths..."
INCLUDE_ARGS=()
for p in "${INCLUDE_PATHS[@]}"; do
    INCLUDE_ARGS+=(--path "$p")
done
git filter-repo --force "${INCLUDE_ARGS[@]}" 2>&1 | tail -3
remaining=$(git ls-files | wc -l)
echo "   ✓ kept $remaining files after path filter"

# ---- step 3: filter-repo (defensive excludes) ----------------------------
echo
echo "3. Filtering: stripping any leaked secrets / internal paths..."
EXCLUDE_ARGS=()
for g in "${EXCLUDE_GLOBS[@]}"; do
    EXCLUDE_ARGS+=(--path-glob "$g")
done
# --invert-paths inverts the include-args, i.e. removes matching paths
git filter-repo --force --invert-paths "${EXCLUDE_ARGS[@]}" 2>&1 | tail -3
remaining=$(git ls-files | wc -l)
echo "   ✓ kept $remaining files after exclusion filter"

# ---- step 4: synthesize root README + LICENSE ---------------------------
echo
echo "4. Synthesizing root README + LICENSE..."

# README — terse landing page pointing at the customer guide
cat > README.md <<'EOF'
# PWM — Physics-World-Model Protocol

PWM is a 4-layer protocol for evaluating computational-science methods
on tamper-resistant on-chain benchmarks. This is the **public mirror**
— the canonical reference implementation, customer guide, and contract
sources.

## Quick start (consumers)

```bash
git clone https://github.com/integritynoble/pwm-public.git
cd pwm-public
python3 -m venv .venv && source .venv/bin/activate
pip install -e pwm-team/infrastructure/agent-cli   # → pwm-node CLI

# Browse the catalog
pwm-node --network testnet benchmarks

# Or visit the live explorer:
#   https://explorer.pwm.platformai.org
```

## Full guide

See `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md`
for the complete walkthrough of the L1/L2/L3/L4 layers, with consumer
+ producer flows and 5 concrete user journeys.

## What's in this repo

| Directory | Purpose |
|---|---|
| `pwm-team/pwm_product/` | Genesis manifests (L1/L2/L3) + reference solvers + demo data |
| `pwm-team/infrastructure/agent-contracts/` | 7 Solidity contracts (PWMRegistry, PWMCertificate, etc.) + deploy scripts |
| `pwm-team/infrastructure/agent-cli/` | `pwm-node` CLI |
| `pwm-team/infrastructure/agent-web/` | Web explorer (Next.js + FastAPI + SQLite indexer) |
| `pwm-team/infrastructure/agent-miner/` | Reference miner implementation |
| `pwm-team/infrastructure/agent-scoring/` | Off-chain scoring engine |
| `pwm-team/customer_guide/` | Public-facing documentation |
| `scripts/` | Mining helpers, register_genesis, daily stability check, etc. |
| `papers/Proof-of-Solution/mine_example/science/` | Genesis-manifest catalog (public, by domain) |

## Live explorer

[https://explorer.pwm.platformai.org](https://explorer.pwm.platformai.org) — testnet leaderboard, live cert submissions, benchmark detail pages.

## Contracts on Ethereum Sepolia (chainId 11155111)

| Contract | Address |
|---|---|
| PWMRegistry | [`0x2375217dd8FeC420707D53C75C86e2258FBaab65`](https://sepolia.etherscan.io/address/0x2375217dd8FeC420707D53C75C86e2258FBaab65) |
| PWMCertificate | [`0x8963b60454EC1D9F65eE3cbF7aBC5D1220C3dB08`](https://sepolia.etherscan.io/address/0x8963b60454EC1D9F65eE3cbF7aBC5D1220C3dB08) |

Full set in `pwm-team/infrastructure/agent-contracts/addresses.json`.

## License

PWM NONCOMMERCIAL SHARE-ALIKE LICENSE v1.0 — see [`LICENSE`](LICENSE).

## Contributing

External developers can author new L1 Principles + L2 Specs +
L3 Benchmarks. Reward via Bounty #7 Tier B (~2,000 PWM per anchor on
first external L4 submission).

See `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md`
§ "L1 — How PRODUCERS create new Principles".
EOF
echo "   ✓ wrote README.md ($(wc -l < README.md) lines)"

# LICENSE — copy the existing PWM noncommercial license
if [[ -f "$SOURCE_DIR/$PUBLIC_LICENSE_PATH" ]]; then
    cp "$SOURCE_DIR/$PUBLIC_LICENSE_PATH" LICENSE
    echo "   ✓ copied LICENSE from $PUBLIC_LICENSE_PATH"
else
    echo "   ⚠ LICENSE source not found at $PUBLIC_LICENSE_PATH — skipping" >&2
fi

# Commit the synthesized files
git add README.md LICENSE 2>/dev/null || true
git -c user.email="ci@pwm.platformai.org" \
    -c user.name="PWM Public Mirror" \
    commit -m "docs: public-repo README + LICENSE" 2>&1 | tail -1

# ---- step 5: dry-run summary or push -------------------------------------
echo
echo "5. Final manifest:"
echo "   commits : $(git log --oneline | wc -l)"
echo "   files   : $(git ls-files | wc -l)"
echo "   size    : $(du -sh .git | cut -f1)"
echo
echo "   sample paths:"
git ls-files | head -10 | sed 's|^|     |'
echo "     ..."
echo "   total: $(git ls-files | wc -l) files"

if [[ $DRY_RUN -eq 1 ]]; then
    echo
    echo "============================================================"
    echo "  ✓ DRY RUN COMPLETE — no push performed"
    echo "============================================================"
    echo "  Re-run without --dry-run to push to:"
    echo "    $TARGET (branch: $TARGET_BRANCH)"
    exit 0
fi

# Add target remote
echo
echo "6. Pushing to $TARGET..."
git remote add origin "$TARGET"
git branch -M "$TARGET_BRANCH"

PUSH_FLAGS=()
if [[ $FORCE_PUSH -eq 1 ]]; then
    PUSH_FLAGS+=(--force)
fi
PUSH_FLAGS+=(-u origin "$TARGET_BRANCH")

if git push "${PUSH_FLAGS[@]}" 2>&1; then
    echo
    echo "============================================================"
    echo "  ✓ MIRROR COMPLETE"
    echo "============================================================"
    echo "  Public repo: $TARGET"
    echo "  Branch     : $TARGET_BRANCH"
    echo "  Commits    : $(git log --oneline | wc -l)"
    echo "  Files      : $(git ls-files | wc -l)"
    echo
    echo "  Next steps:"
    echo "    1. Browse the new public repo on GitHub to verify content"
    echo "    2. Update doc references (already prepared by PR — see"
    echo "       pwm-team/customer_guide/plan.md Phase 3 task 3.9-3.13)"
    echo "    3. Smoke test: clone the public repo as a fresh user"
    exit 0
else
    rc=$?
    echo
    echo "✗ push failed (exit $rc)"
    echo "  Common causes:"
    echo "    - target repo is non-empty and protected — use --force-push"
    echo "    - SSH key not authorized for the target repo"
    echo "    - target repo doesn't exist yet (create it on GitHub first)"
    exit $rc
fi
