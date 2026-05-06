#!/usr/bin/env bash
# Download / verify reference-solver pretrained weights for pwm-public.
#
# The weights ship via Git LFS (.gitattributes + .pth filter in the
# `public` submodule), so a fresh
#
#   git clone --recursive https://github.com/integritynoble/pwm-public.git
#
# typically picks them up automatically. This script is the fallback
# for the common cases where:
#
#   - Git LFS isn't installed on the cloning machine
#   - The clone wasn't recursive (`public/` submodule empty)
#   - The clone was shallow / partial / had network issues mid-pull
#
# It detects the failure mode and either fixes it via `git lfs pull`
# or prints exact filenames + authors' release URLs so a manual
# download can drop the right files in the right place.
#
# Usage:
#   bash scripts/download_weights.sh
#
# Exit codes:
#   0 — all expected weights are present and full-size
#   1 — weights missing AND auto-fix could not apply (manual download needed)

set -uo pipefail

# Locate repo root (the script is at <repo>/scripts/download_weights.sh).
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

WEIGHTS_DIR="public/packages/pwm_core/weights"

# Color helpers (skip on non-tty).
if [ -t 1 ]; then
  RED=$'\033[0;31m'; GRN=$'\033[0;32m'; YEL=$'\033[1;33m'; CYN=$'\033[0;36m'; NC=$'\033[0m'
else
  RED=''; GRN=''; YEL=''; CYN=''; NC=''
fi
ok()   { printf "${GRN}OK${NC}   %s\n" "$*"; }
warn() { printf "${YEL}WARN${NC} %s\n" "$*"; }
fail() { printf "${RED}FAIL${NC} %s\n" "$*" >&2; }
info() { printf "${CYN}INFO${NC} %s\n" "$*"; }

# Each entry is "path:min_bytes:source_label".
EXPECTED=(
  "$WEIGHTS_DIR/mst/mst_l.pth:5000000:Cai et al., CVPR 2022 (MST-L)"
  "$WEIGHTS_DIR/mst/mst_s.pth:2000000:Cai et al., CVPR 2022 (MST-S)"
  "$WEIGHTS_DIR/efficientsci/efficientsci_base.pth:20000000:Wang et al., CVPR 2023 (EfficientSCI)"
)

# A real .pth is megabytes; an LFS pointer file is ~134 bytes. Anything
# under min_bytes/10 is treated as missing-or-pointer; under min_bytes
# is treated as suspect and reported.
file_size() {
  if [ -f "$1" ]; then
    stat -c%s "$1" 2>/dev/null || stat -f%z "$1" 2>/dev/null || echo 0
  else
    echo 0
  fi
}

missing=()
pointer=()
ok_count=0

for entry in "${EXPECTED[@]}"; do
  path="${entry%%:*}"
  rest="${entry#*:}"
  min_bytes="${rest%%:*}"
  label="${rest#*:}"
  size=$(file_size "$path")
  if [ "$size" -ge "$min_bytes" ]; then
    ok "$path  ($(numfmt --to=iec --suffix=B "$size" 2>/dev/null || echo "${size} B"))"
    ok_count=$((ok_count + 1))
  elif [ "$size" -gt 0 ] && [ "$size" -lt 1000 ]; then
    pointer+=("$path|$label")
    warn "$path  ($size B — looks like an LFS pointer)"
  else
    missing+=("$path|$label")
    fail "$path  (missing or truncated: $size B)"
  fi
done

if [ ${#missing[@]} -eq 0 ] && [ ${#pointer[@]} -eq 0 ]; then
  echo
  ok "all reference-solver weights present ($ok_count files)"
  exit 0
fi

echo
echo "─── Auto-fix attempt ───"

# Step 1: ensure submodule is initialized.
if [ ! -d public/.git ] && [ ! -f public/.git ]; then
  info "submodule 'public' isn't initialized; running submodule update..."
  if git submodule update --init --recursive public 2>&1 | tail -5; then
    ok "submodule initialized"
  else
    fail "submodule init failed; check network + git auth"
  fi
fi

# Step 2: try `git lfs pull` inside the public submodule.
if command -v git-lfs >/dev/null 2>&1; then
  info "git lfs found; running 'git lfs pull' inside public/..."
  if (cd public && git lfs install --local >/dev/null 2>&1 && git lfs pull 2>&1); then
    ok "git lfs pull completed"
  else
    fail "git lfs pull failed (LFS quota / network / auth)"
  fi
else
  warn "git-lfs not installed on this machine"
  info "Install: see https://git-lfs.com — typically:"
  info "  Ubuntu:   sudo apt install git-lfs"
  info "  macOS:    brew install git-lfs"
  info "  Windows:  bundled with Git for Windows; otherwise from git-lfs.com"
  info "Then re-run: bash scripts/download_weights.sh"
fi

# Re-check after auto-fix.
echo
echo "─── Re-verify after auto-fix ───"
all_good=1
for entry in "${EXPECTED[@]}"; do
  path="${entry%%:*}"
  rest="${entry#*:}"
  min_bytes="${rest%%:*}"
  label="${rest#*:}"
  size=$(file_size "$path")
  if [ "$size" -ge "$min_bytes" ]; then
    ok "$path"
  else
    all_good=0
    fail "$path still ($size B)"
  fi
done

if [ "$all_good" = 1 ]; then
  echo
  ok "all reference-solver weights now present"
  exit 0
fi

# Step 3: manual-download fallback.
echo
echo "─── Manual download (last resort) ───"
echo "If 'git lfs pull' didn't fix it, download the original release"
echo "weights from the authors and place them at the paths below:"
echo
for entry in "${EXPECTED[@]}"; do
  path="${entry%%:*}"
  rest="${entry#*:}"
  min_bytes="${rest%%:*}"
  label="${rest#*:}"
  if [ "$(file_size "$path")" -lt "$min_bytes" ]; then
    echo "  • $path"
    echo "       — $label"
  fi
done
echo
echo "Author release URLs:"
echo "  MST (Cai et al. CVPR 2022):           https://github.com/caiyuanhao1998/MST"
echo "  EfficientSCI (Wang et al. CVPR 2023): https://github.com/ucaswangls/EfficientSCI"
echo
echo "Both releases publish pretrained checkpoints in their model-zoo"
echo "section. Filenames in those releases may differ; rename to match"
echo "the paths above so cassi_mst.py / cacti_efficientsci.py find them."
exit 1
