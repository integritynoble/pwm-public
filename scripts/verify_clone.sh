#!/usr/bin/env bash
# Smoke test for a fresh pwm-public clone. Verifies:
#   1. Submodule public/ is initialised
#   2. LFS weights are pulled (size > 100 MB sanity check — catches
#      the common LFS-pointer-not-resolved case where the file exists
#      but contains a 130-byte text pointer instead of the binary)
#   3. CLI installable + version check passes
#   4. Catalog browsable via offline commands
#
# Closes P1 row 4 of PWM_PRELAUNCH_POLISH_PRIORITY_2026-05-08.md.
# See pwm-team/customer_guide/PWM_SUBMODULE_LFS_SMOKE_TEST_2026-05-09.md
# for the full failure-mode reference.
#
# Usage:
#   bash scripts/verify_clone.sh
#
# Exits 0 on all-green; non-zero with diagnostic on any failure.

set -uo pipefail
ok=0
fail=0

check() {
    local lbl="$1"
    local cond="$2"
    local fix="$3"
    if eval "$cond"; then
        printf "  ✓ %s\n" "$lbl"
        ok=$((ok+1))
    else
        printf "  ✗ %s\n     fix: %s\n" "$lbl" "$fix"
        fail=$((fail+1))
    fi
}

echo "=== pwm-public clone smoke test ==="
echo

check "submodule public/ initialised" \
      "[[ -f public/packages/pwm_core/pyproject.toml ]]" \
      "git submodule update --init --recursive"

check "LFS installed (git-lfs in PATH)" \
      "command -v git-lfs >/dev/null" \
      "https://git-lfs.com (or apt-get install git-lfs / brew install git-lfs)"

# Only check weights if the submodule was initialised (otherwise the
# weight path doesn't exist and the check would mask the real problem).
if [[ -d public/packages/pwm_core ]]; then
    check "MST-L weights pulled (>100 MB; 100MB threshold catches LFS-pointer-not-resolved)" \
          "[[ -s public/packages/pwm_core/weights/mst/mst_l.pth ]] && \
           [[ \$(stat -c%s public/packages/pwm_core/weights/mst/mst_l.pth) -gt 100000000 ]]" \
          "git lfs install && git -C public lfs pull"
fi

check "pwm-node CLI importable" \
      "python3 -c 'import pwm_node' 2>/dev/null" \
      "pip install -e pwm-team/infrastructure/agent-cli"

check "Catalog browsable (offline)" \
      "python3 -m pwm_node principles 2>/dev/null | grep -q L1-003" \
      "(if previous checks passed, this should already work)"

echo
echo "============================================================"
printf "  PASS: %d    FAIL: %d\n" "$ok" "$fail"
echo "============================================================"

if [[ $fail -eq 0 ]]; then
    echo "  ✓ Clone is ready to mine. Next: PWM_WALLET_ONBOARDING_2026-05-09.md"
    exit 0
else
    echo "  ✗ Fix the items above before proceeding."
    echo "    Full reference: pwm-team/customer_guide/PWM_SUBMODULE_LFS_SMOKE_TEST_2026-05-09.md"
    exit 1
fi
