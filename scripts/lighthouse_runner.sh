#!/usr/bin/env bash
# Lighthouse mobile runner for Step 4 Criterion 10.
# Per `pwm-team/coordination/MAINNET_DEPLOY_UNBLOCK_STEPS_3_TO_7_2026-04-28.md`
# § "Criterion 10 — Mobile Lighthouse ≥ 80".
#
# Runs Chrome Lighthouse against 6 explorer routes in mobile-emulation mode,
# collects the performance score for each, and exits with non-zero if any
# route is below the threshold. Replaces the manual "open Chrome 6 times"
# Director task (D7 in MAINNET_BLOCKERS_2026-04-30.md) with a one-liner.
#
# Usage:
#
#   # Default: run against canonical explorer URL with threshold 0.80
#   bash scripts/lighthouse_runner.sh
#
#   # Custom URL (e.g., staging)
#   bash scripts/lighthouse_runner.sh https://staging.explorer.pwm.platformai.org
#
#   # Custom threshold (lower for first-pass measurement)
#   THRESHOLD=0.70 bash scripts/lighthouse_runner.sh
#
#   # Skip writing per-route HTML reports (JSON only — faster CI mode)
#   FORMAT=json bash scripts/lighthouse_runner.sh
#
# Outputs:
#   pwm-team/coordination/evidence/step4_lighthouse/lh_<route>.json
#   pwm-team/coordination/evidence/step4_lighthouse/lh_<route>.html  (unless FORMAT=json)
#   pwm-team/coordination/evidence/step4_lighthouse/summary_<DATE>.md
#
# Exit codes:
#   0  all 6 routes >= threshold
#   1  one or more routes below threshold
#   2  lighthouse-cli not installed
#   3  curl/jq not available
#
# Requires:
#   npm install -g lighthouse
#   jq, curl

set -uo pipefail

URL="${1:-https://explorer.pwm.platformai.org}"
THRESHOLD="${THRESHOLD:-0.80}"
FORMAT="${FORMAT:-html,json}"

ROUTES=(
  "/"
  "/match"
  "/demos"
  "/contribute"
  "/use"
  "/roadmap"
)

# Tooling check
if ! command -v lighthouse >/dev/null 2>&1; then
  echo "ERROR: lighthouse-cli not installed. Install via: npm install -g lighthouse" >&2
  exit 2
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq not installed. Install via: apt install jq  OR  brew install jq" >&2
  exit 3
fi
if ! command -v curl >/dev/null 2>&1; then
  echo "ERROR: curl not installed." >&2
  exit 3
fi

# Find repo root + evidence dir
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVIDENCE_DIR="$REPO_ROOT/pwm-team/coordination/evidence/step4_lighthouse"
mkdir -p "$EVIDENCE_DIR"
DATE_TAG="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
SUMMARY="$EVIDENCE_DIR/summary_$DATE_TAG.md"

echo "Lighthouse mobile runner — Step 4 Criterion 10"
echo "URL: $URL"
echo "Threshold: $THRESHOLD"
echo "Output dir: $EVIDENCE_DIR"
echo ""

# Pre-flight: each URL returns 200
echo "Pre-flight: checking each route returns HTTP 200..."
for route in "${ROUTES[@]}"; do
  full_url="${URL}${route}"
  http_code="$(curl -sf -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 30 "$full_url" || echo "000")"
  if [ "$http_code" != "200" ]; then
    echo "  ✗ $route → HTTP $http_code (expected 200) — Lighthouse will fail; investigate first" >&2
    exit 1
  fi
  echo "  ✓ $route → 200"
done
echo ""

# Header for summary file
{
  echo "# Lighthouse mobile sweep — $DATE_TAG"
  echo ""
  echo "**URL:** $URL"
  echo "**Threshold:** $THRESHOLD"
  echo "**Routes:** ${#ROUTES[@]}"
  echo ""
  echo "| Route | Performance | First Contentful Paint | Largest Contentful Paint | Speed Index | Total Blocking Time | Status |"
  echo "|---|---|---|---|---|---|---|"
} > "$SUMMARY"

# Run lighthouse on each route
FAILED=0
for route in "${ROUTES[@]}"; do
  full_url="${URL}${route}"
  safe_route="$(echo "$route" | sed 's|/|_|g; s|^_|root|; s|^$|root|')"
  if [ -z "$safe_route" ] || [ "$safe_route" = "_" ]; then
    safe_route="root"
  fi
  out_path="$EVIDENCE_DIR/lh_${safe_route}_${DATE_TAG}"

  echo "Running Lighthouse on $route..."
  set +e
  lighthouse "$full_url" \
    --emulated-form-factor=mobile \
    --only-categories=performance \
    --output="$FORMAT" \
    --output-path="$out_path" \
    --quiet \
    --chrome-flags="--headless --no-sandbox --disable-gpu" \
    --max-wait-for-load=45000 2>&1 | tail -3
  RC=$?
  set -e

  if [ "$RC" -ne 0 ]; then
    echo "  ✗ Lighthouse failed (exit $RC) for $route" >&2
    echo "| $route | ERROR | — | — | — | — | ✗ FAIL (lighthouse exit $RC) |" >> "$SUMMARY"
    FAILED=1
    continue
  fi

  json_path="${out_path}.report.json"
  if [ ! -f "$json_path" ]; then
    # Some lighthouse versions name the file differently
    json_path="$(ls "${out_path}"*.json 2>/dev/null | head -1)"
  fi
  if [ -z "$json_path" ] || [ ! -f "$json_path" ]; then
    echo "  ✗ JSON output not found for $route (looked for ${out_path}.report.json)" >&2
    FAILED=1
    continue
  fi

  perf=$(jq -r '.categories.performance.score' "$json_path")
  fcp=$(jq -r '.audits["first-contentful-paint"].displayValue // "—"' "$json_path")
  lcp=$(jq -r '.audits["largest-contentful-paint"].displayValue // "—"' "$json_path")
  si=$(jq -r '.audits["speed-index"].displayValue // "—"' "$json_path")
  tbt=$(jq -r '.audits["total-blocking-time"].displayValue // "—"' "$json_path")

  pass=$(awk -v p="$perf" -v t="$THRESHOLD" 'BEGIN{print (p+0 >= t+0) ? "✓ PASS" : "✗ FAIL"}')
  if echo "$pass" | grep -q FAIL; then
    FAILED=1
  fi
  printf "  %s perf=%s  FCP=%s  LCP=%s  SI=%s  TBT=%s\n" "$pass" "$perf" "$fcp" "$lcp" "$si" "$tbt"
  echo "| $route | $perf | $fcp | $lcp | $si | $tbt | $pass |" >> "$SUMMARY"
done

# Overall verdict
echo "" >> "$SUMMARY"
if [ "$FAILED" -eq 0 ]; then
  echo "**Overall: ✓ all $(echo "${#ROUTES[@]}") routes ≥ $THRESHOLD**" >> "$SUMMARY"
else
  echo "**Overall: ✗ one or more routes below threshold $THRESHOLD**" >> "$SUMMARY"
fi
echo "" >> "$SUMMARY"

echo ""
echo "================================="
echo "Summary: $SUMMARY"
if [ "$FAILED" -eq 0 ]; then
  echo "✓ ALL ROUTES PASS THRESHOLD $THRESHOLD"
  exit 0
else
  echo "✗ ONE OR MORE ROUTES FAILED"
  exit 1
fi
