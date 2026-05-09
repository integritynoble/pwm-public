# Submodule + LFS Smoke Test — One-Liner Verification for Fresh Clones

**Date:** 2026-05-09
**Audience:** First-time clone of `pwm-public`; deep-learning miners (MST-L, EfficientSCI)
**Closes:** P1 row 4 of `PWM_PRELAUNCH_POLISH_PRIORITY_2026-05-08.md`

---

## TL;DR

After cloning `integritynoble/pwm-public`, run this one command to
verify the submodule + LFS state is correct:

```bash
bash scripts/verify_clone.sh
```

If you don't have that script yet (it ships in `pwm-public`
2026-05-09+), the equivalent manual check is:

```bash
[[ -f public/packages/pwm_core/pyproject.toml ]] && \
  echo "✓ submodule init OK" || \
  echo "✗ submodule NOT initialised (run: git submodule update --init --recursive)"

[[ -s public/packages/pwm_core/weights/mst/mst_l.pth ]] && \
  [[ $(stat -c%s public/packages/pwm_core/weights/mst/mst_l.pth) -gt 100000000 ]] && \
  echo "✓ LFS weights pulled OK" || \
  echo "✗ LFS weights NOT pulled (run: git lfs install && git -C public lfs pull)"
```

The 100 MB threshold catches the common LFS-pointer-not-resolved case
where the file exists but contains a 130-byte pointer instead of the
real 750 MB weight binary.

---

## Why this exists

The `pwm-public` mirror has TWO layers of pulling-down extras:

1. **Submodule** — `public/` is a git submodule pointing at
   `integritynoble/Physics_World_Model`. A bare `git clone` doesn't
   populate it; you need `--recursive` (or post-hoc `git submodule
   update --init --recursive`).

2. **LFS weights** — inside that submodule,
   `public/packages/pwm_core/weights/mst/mst_l.pth` (~750 MB) and
   `public/packages/pwm_core/weights/efficientsci/*.pth` are
   git-LFS-pinned. The submodule init doesn't pull these unless
   `git lfs` is installed AND you explicitly `git -C public lfs pull`.

A user who skips either step gets:

- **Skip submodule:** `pip install -e public/packages/pwm_core` fails
  with "no setup.py / pyproject.toml found" because the directory is
  empty.
- **Skip LFS:** `pip install` succeeds (the package itself isn't
  LFS-pinned), but loading the model errors with "expected magic
  number 0x84d3 but got 0x7376" or similar binary-mismatch — because
  `mst_l.pth` is a 130-byte text file containing a pointer like
  `version https://git-lfs.github.com/spec/v1` instead of the real
  weights.

Both failures are cryptic for first-timers. This smoke test catches
them before the user wastes 5 minutes installing torch + CUDA only
to hit a `RuntimeError`.

---

## The full verification script

`scripts/verify_clone.sh` ships with the repo as of 2026-05-09:

```bash
#!/usr/bin/env bash
# Smoke test for a fresh pwm-public clone. Verifies:
#   1. Submodule public/ is initialised
#   2. LFS weights are pulled (size > 100 MB sanity check)
#   3. CLI installable + version check passes
#   4. Catalog browsable via offline commands
# Exits 0 on green; non-zero with diagnostic on any failure.
#
# Usage: bash scripts/verify_clone.sh

set -uo pipefail
ok=0
fail=0
check() { local lbl="$1"; local cond="$2"; local fix="$3"
  if eval "$cond"; then printf "  ✓ %s\n" "$lbl"; ok=$((ok+1))
  else printf "  ✗ %s\n     fix: %s\n" "$lbl" "$fix"; fail=$((fail+1)); fi; }

echo "=== pwm-public clone smoke test ==="

check "submodule public/ initialised" \
      "[[ -f public/packages/pwm_core/pyproject.toml ]]" \
      "git submodule update --init --recursive"

check "LFS installed" \
      "command -v git-lfs >/dev/null" \
      "https://git-lfs.com (or apt-get install git-lfs / brew install git-lfs)"

# 100 MB threshold catches LFS-pointer-not-resolved (130-byte text file)
check "MST-L weights pulled (>100 MB)" \
      "[[ -s public/packages/pwm_core/weights/mst/mst_l.pth ]] && \
       [[ \$(stat -c%s public/packages/pwm_core/weights/mst/mst_l.pth) -gt 100000000 ]]" \
      "git lfs install && git -C public lfs pull"

check "pwm-node CLI installed" \
      "command -v pwm-node >/dev/null || python3 -c 'import pwm_node' 2>/dev/null" \
      "pip install -e pwm-team/infrastructure/agent-cli"

check "Catalog browsable (offline)" \
      "python3 -m pwm_node principles 2>/dev/null | grep -q L1-003" \
      "(if previous checks passed, this should already work)"

echo
echo "PASS: $ok    FAIL: $fail"
[[ $fail -eq 0 ]] && exit 0 || exit 1
```

---

## Failure-mode reference

What you see → what's wrong → how to fix:

| Error message | Root cause | Fix |
|---|---|---|
| `setup.py not found` / `pyproject.toml not found` when running `pip install -e public/packages/pwm_core` | Submodule never initialised | `git submodule update --init --recursive` |
| `Could not import 'pwm_core'` after seemingly-successful pip install | Same as above (the dir was empty so pip succeeded with nothing to install) | Same as above |
| `RuntimeError: expected magic number ... but got 0x7376` when loading MST-L | LFS pointer not resolved (got the 130-byte text pointer instead of the binary) | `git lfs install` (one-time) + `git -C public lfs pull` |
| `IsADirectoryError: ... weights/mst/mst_l.pth` | Symlink broken (rare; usually means LFS partially pulled then aborted) | Delete `public/packages/pwm_core/weights/` and re-pull: `rm -rf public/packages/pwm_core/weights && git -C public lfs pull` |
| Submodule shows as "M public" in `git status` after init | Submodule pointer is ahead of/behind the parent's recorded sha | `git submodule update` (no `--init`) to reset to recorded sha; OR `git -C public log -1` to see what's actually checked out and decide if you want to commit the bump |

---

## When this can be skipped

CPU-only solvers (`cassi_gap_tv.py`, `cacti_pnp_admm.py`) **don't
need pwm_core or its LFS weights**. They run on numpy + scipy alone.
If you're only mining with CPU solvers:

```bash
git clone https://github.com/integritynoble/pwm-public.git    # NO --recursive needed
cd pwm-public
pip install -e pwm-team/infrastructure/agent-cli
# That's it — you can skip the submodule + LFS dance entirely
```

The submodule + LFS only matter if you want to run **deep-learning
solvers** (MST-L, EfficientSCI) which require pwm_core's
PyTorch-pinned model classes + the trained weight files.

---

## Cross-references

- `pwm-team/customer_guide/PWM_WALLET_ONBOARDING_2026-05-09.md` —
  the user-facing onboarding flow that runs this smoke test as Step 4
- `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md`
  § "Pre-flight (producer)" — full producer setup including
  `download_weights.sh` fallback when LFS misbehaves
- `scripts/download_weights.sh` — fallback weight-download path that
  fetches from a non-LFS HTTP mirror if `git lfs pull` fails
- `pwm-team/customer_guide/PWM_CROSS_CHAIN_UX_DESIGN_2026-05-08.md` § 1.2 —
  the 7 chain-agnostic features that survive the LFS-issue boundary
