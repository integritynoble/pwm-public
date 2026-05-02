#!/usr/bin/env bash
# Submit off-chain cert metadata (solver name + PSNR-as-dB) to the
# explorer's POST /api/cert-meta/{cert_hash} endpoint.
#
# Companion to the leaderboard-solver-labels patch (PR
# feat/leaderboard-solver-labels). The patch adds a write endpoint
# that lets you label your already-on-chain cert with a human-meaningful
# solver name + PSNR — the leaderboard then renders 'MST-L 34.1 dB'
# instead of just a shortened cert hash.
#
# Usage:
#   bash scripts/submit_cert_meta.sh <meta.json> [--explorer URL]
#
# Examples:
#   # After running pwm-node mine on CASSI MST-L:
#   bash scripts/submit_cert_meta.sh /tmp/pwm-out/cassi-mst/meta.json
#
#   # Against a different explorer (e.g., a staging instance):
#   bash scripts/submit_cert_meta.sh ./meta.json \
#       --explorer https://staging-explorer.pwm.platformai.org
#
#   # Override fields the meta.json doesn't have:
#   SOLVER_LABEL="MST-L (custom build)" PSNR_DB=34.5 \
#       bash scripts/submit_cert_meta.sh ./meta.json
#
# Required env / fields (read from meta.json or env):
#   cert_hash        — 0x-prefixed 64-hex; the on-chain cert hash
#   solver_label     — human-readable; e.g. 'MST-L'
#
# Optional fields (read from meta.json or env):
#   psnr_db          — PSNR in dB (e.g. 34.13)
#   runtime_sec      — solver runtime (e.g. 12.3)
#   framework        — e.g. 'PyTorch 2.1 + CUDA 12.1'
#   meta_url         — pointer to full meta.json (IPFS / GCS / etc.)
#
# Exit code 0 on success; non-zero with diagnostic on any failure.

set -uo pipefail

DEFAULT_EXPLORER="https://explorer.pwm.platformai.org"
EXPLORER="${PWM_EXPLORER_URL:-$DEFAULT_EXPLORER}"
META_FILE=""

# ---- arg parsing --------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --explorer)
            EXPLORER="$2"
            shift 2
            ;;
        --explorer=*)
            EXPLORER="${1#*=}"
            shift
            ;;
        -h|--help)
            sed -n '2,30p' "$0"
            exit 0
            ;;
        -*)
            echo "Unknown option: $1" >&2
            exit 2
            ;;
        *)
            if [[ -z "$META_FILE" ]]; then
                META_FILE="$1"
            else
                echo "Unexpected positional arg: $1" >&2
                exit 2
            fi
            shift
            ;;
    esac
done

if [[ -z "$META_FILE" ]]; then
    echo "Usage: $0 <meta.json> [--explorer URL]" >&2
    exit 2
fi
if [[ ! -f "$META_FILE" ]]; then
    echo "✗ meta file not found: $META_FILE" >&2
    exit 1
fi

# ---- dependency check ---------------------------------------------------
if ! command -v jq >/dev/null 2>&1; then
    echo "✗ jq is required (apt-get install jq | brew install jq)" >&2
    exit 1
fi
if ! command -v curl >/dev/null 2>&1; then
    echo "✗ curl is required" >&2
    exit 1
fi

# ---- read fields from meta.json (env overrides) ------------------------
get_field() {
    local key="$1"
    local env_override="${2:-}"
    if [[ -n "$env_override" ]]; then
        printf '%s' "$env_override"
        return
    fi
    jq -r ".${key} // empty" "$META_FILE" 2>/dev/null
}

CERT_HASH="$(get_field cert_hash "${CERT_HASH:-}")"
SOLVER_LABEL="$(get_field solver_label "${SOLVER_LABEL:-}")"
PSNR_DB="$(get_field psnr_db "${PSNR_DB:-}")"
RUNTIME_SEC="$(get_field runtime_sec "${RUNTIME_SEC:-}")"
FRAMEWORK="$(get_field framework "${FRAMEWORK:-}")"
META_URL="$(get_field meta_url "${META_URL:-}")"

# Some meta.json schemas use different keys; fall back to common alternatives.
if [[ -z "$SOLVER_LABEL" ]]; then
    SOLVER_LABEL="$(jq -r '.solver // .model // .algorithm // empty' "$META_FILE" 2>/dev/null)"
fi
if [[ -z "$PSNR_DB" ]]; then
    PSNR_DB="$(jq -r '.psnr // .reference_solver_psnr_db // empty' "$META_FILE" 2>/dev/null)"
fi

# ---- validation --------------------------------------------------------
fail=0
if [[ -z "$CERT_HASH" ]]; then
    echo "✗ cert_hash missing — set in meta.json or via CERT_HASH env" >&2
    fail=1
fi
if [[ -z "$SOLVER_LABEL" ]]; then
    echo "✗ solver_label missing — set in meta.json or via SOLVER_LABEL env" >&2
    fail=1
fi
if ! [[ "$CERT_HASH" =~ ^0x[0-9a-fA-F]{64}$ ]]; then
    echo "✗ cert_hash invalid: '$CERT_HASH' (expected 0x + 64 hex chars)" >&2
    fail=1
fi
[[ $fail -eq 1 ]] && exit 1

# ---- build request body -------------------------------------------------
BODY=$(jq -n \
    --arg solver_label "$SOLVER_LABEL" \
    --arg psnr_db "$PSNR_DB" \
    --arg runtime_sec "$RUNTIME_SEC" \
    --arg framework "$FRAMEWORK" \
    --arg meta_url "$META_URL" \
    '{
        solver_label: $solver_label,
        psnr_db:     (if $psnr_db == "" then null else ($psnr_db|tonumber) end),
        runtime_sec: (if $runtime_sec == "" then null else ($runtime_sec|tonumber) end),
        framework:   (if $framework == "" then null else $framework end),
        meta_url:    (if $meta_url == "" then null else $meta_url end)
     } | with_entries(select(.value != null or .key == "solver_label"))')

URL="${EXPLORER%/}/api/cert-meta/${CERT_HASH}"

echo "→ POST $URL"
echo "  solver_label : $SOLVER_LABEL"
[[ -n "$PSNR_DB"     ]] && echo "  psnr_db      : $PSNR_DB"
[[ -n "$RUNTIME_SEC" ]] && echo "  runtime_sec  : $RUNTIME_SEC"
[[ -n "$FRAMEWORK"   ]] && echo "  framework    : $FRAMEWORK"
echo

# ---- POST and report ---------------------------------------------------
RESP_FILE="$(mktemp)"
HTTP_CODE=$(curl -s -o "$RESP_FILE" -w "%{http_code}" \
    -X POST "$URL" \
    -H "Content-Type: application/json" \
    -d "$BODY")

case "$HTTP_CODE" in
    200)
        echo "✓ submitted"
        jq . "$RESP_FILE" 2>/dev/null || cat "$RESP_FILE"
        rm -f "$RESP_FILE"

        # Try to find the L3 ref this cert is associated with for a clickable link.
        BENCH_HASH=$(curl -s "${EXPLORER%/}/api/cert/${CERT_HASH}" \
            | jq -r '.certificate.benchmark_hash // empty' 2>/dev/null)
        if [[ -n "$BENCH_HASH" ]]; then
            echo
            echo "  view leaderboard:"
            echo "    ${EXPLORER%/}/leaderboard/${BENCH_HASH}"
        fi
        exit 0
        ;;
    400)
        echo "✗ 400 Bad Request — cert_hash format invalid" >&2
        cat "$RESP_FILE" >&2
        rm -f "$RESP_FILE"
        exit 1
        ;;
    404)
        echo "✗ 404 Not Found" >&2
        echo "  Either:" >&2
        echo "    (a) the cert isn't on-chain yet OR the indexer hasn't caught up — wait 1-2 min and retry, or" >&2
        echo "    (b) the explorer at $EXPLORER hasn't been updated to include the /api/cert-meta/ endpoint yet" >&2
        echo "        (PR feat/leaderboard-solver-labels not yet merged + redeployed)" >&2
        cat "$RESP_FILE" >&2
        rm -f "$RESP_FILE"
        exit 1
        ;;
    422)
        echo "✗ 422 Validation Error — payload malformed" >&2
        jq . "$RESP_FILE" 2>/dev/null >&2 || cat "$RESP_FILE" >&2
        rm -f "$RESP_FILE"
        exit 1
        ;;
    *)
        echo "✗ HTTP $HTTP_CODE — unexpected" >&2
        head -c 500 "$RESP_FILE" >&2
        rm -f "$RESP_FILE"
        exit 1
        ;;
esac
