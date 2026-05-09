#!/usr/bin/env bash
# Third-party integration smoke test — Etherscan + IPFS gateway reach
# the on-chain state we expect, end-to-end.
#
# Closes P1 row 6 of PWM_PRELAUNCH_POLISH_PRIORITY_2026-05-08.md.
# Cheap pre-flight (~30s) — catches third-party drift before user
# load.
#
# Today's coverage: testnet (Sepolia + Etherscan-Sepolia + public IPFS gateways).
# Mainnet portions (BaseScan, Base IPFS providers) are TODO once D9
# populates addresses.json:mainnet.
#
# Usage: bash scripts/smoke_third_party.sh
#
# Exit 0 on all-green; non-zero with a short diagnostic per failure.

set -uo pipefail
ok=0
fail=0
warn=0

# We use an established, immutable on-chain artifact for the smoke
# checks: the live MST-L cert that's been on Sepolia since 2026-05-05.
# Both sides of every check (the indexer's cached view AND the chain)
# should agree.
CERT_HASH="0x7c7740faad378c8514128903a26165d5e5d303b56e2b5b4649917265c5a3ee13"
TX_HASH="0x8883a90d0e3fd01b8bb4221c9a10331ca9a9cf1532d117320bf2ce90a19e19c5"
EXPECTED_BLOCK="10778856"
EXPECTED_QINT="35"
EXPLORER="https://explorer.pwm.platformai.org"
ETHERSCAN_TX="https://sepolia.etherscan.io/tx/$TX_HASH"

check() {
    local lbl="$1"
    local cond="$2"
    local note="$3"
    if eval "$cond"; then
        printf "  ✓ %s\n" "$lbl"
        ok=$((ok+1))
    else
        printf "  ✗ %s\n     note: %s\n" "$lbl" "$note"
        fail=$((fail+1))
    fi
}

warn() {
    local lbl="$1"; local note="$2"
    printf "  ⚠ %s\n     %s\n" "$lbl" "$note"
    warn=$((warn+1))
}

echo "=== Third-party integration smoke ==="
echo "  Reference cert: $CERT_HASH (MST-L, live on Sepolia since 2026-05-05)"
echo "  Reference tx:   $TX_HASH"
echo

# 1. PWM explorer (our backend) reaches the cert
echo "--- Explorer backend ---"
RESP=$(curl -s --max-time 8 "$EXPLORER/api/cert/$CERT_HASH" 2>/dev/null || echo "{}")
check "explorer /api/cert returns the cert" \
      "[[ \$(echo '$RESP' | python3 -c 'import sys, json; d=json.load(sys.stdin); print(d.get(\"certificate\",d).get(\"q_int\",0))' 2>/dev/null) == '$EXPECTED_QINT' ]]" \
      "explorer or its indexer is degraded"

check "explorer /api/cert exposes solver_label" \
      "[[ \$(echo '$RESP' | python3 -c 'import sys, json; d=json.load(sys.stdin); print(d.get(\"certificate\",d).get(\"solver_label\") or \"\")' 2>/dev/null) == 'MST-L' ]]" \
      "cert-meta annotation lost"

check "explorer /api/health returns ok" \
      "[[ \$(curl -s --max-time 5 \"$EXPLORER/api/health\" | python3 -c 'import sys, json; d=json.load(sys.stdin); print(\"ok\" if d.get(\"ok\") else \"no\")') == 'ok' ]]" \
      "API server down"
echo

# 2. Etherscan reach (the canonical 'someone else'')
echo "--- Etherscan (Sepolia) ---"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 -A "Mozilla/5.0 PWM smoke-test" "$ETHERSCAN_TX" || echo "000")
if [[ "$HTTP_CODE" == "200" ]] || [[ "$HTTP_CODE" == "403" ]]; then
    # 403 is anti-bot block — URL is valid, manual click works.
    if [[ "$HTTP_CODE" == "403" ]]; then
        warn "Etherscan tx URL HTTP $HTTP_CODE" \
             "anti-bot block (curl gets 403 even with UA); the URL is valid — verify manually in a browser"
    else
        printf "  ✓ Etherscan tx URL HTTP 200\n"
        ok=$((ok+1))
    fi
else
    printf "  ✗ Etherscan tx URL HTTP %s\n     note: Etherscan unreachable; check sepolia.etherscan.io is up\n" "$HTTP_CODE"
    fail=$((fail+1))
fi
echo

# 3. Public RPC (publicnode) returns the on-chain receipt for the tx
echo "--- Sepolia RPC ---"
RECEIPT=$(curl -s --max-time 8 -X POST https://ethereum-sepolia-rpc.publicnode.com \
    -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getTransactionReceipt\",\"params\":[\"$TX_HASH\"]}" \
    2>/dev/null || echo "{}")
RECEIPT_BLOCK=$(echo "$RECEIPT" | python3 -c 'import sys, json; d=json.load(sys.stdin); r=d.get("result"); print(int(r["blockNumber"], 16) if r and r.get("blockNumber") else 0)' 2>/dev/null || echo 0)

check "Sepolia RPC returns tx receipt at block $EXPECTED_BLOCK" \
      "[[ '$RECEIPT_BLOCK' == '$EXPECTED_BLOCK' ]]" \
      "publicnode RPC down or returning stale data; got block $RECEIPT_BLOCK"
echo

# 4. IPFS gateway smoke (Cloudflare gateway against the well-known
#    test CID for inter-planetary-file-system project README — this
#    isn't a PWM artifact but proves the gateway works at all)
echo "--- IPFS gateway (smoke) ---"
TEST_CID="QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc"   # IPFS project README test CID
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 12 \
    "https://cloudflare-ipfs.com/ipfs/$TEST_CID/readme" || echo "000")
if [[ "$HTTP_CODE" == "200" ]]; then
    printf "  ✓ IPFS gateway (cloudflare) reachable\n"
    ok=$((ok+1))
else
    warn "IPFS gateway HTTP $HTTP_CODE" \
         "cloudflare-ipfs.com may be slow today; this is a soft check (PWM doesn't pin to IPFS yet — Bounty #6 lands post-D9)"
fi
echo

# 5. Cross-check: indexer block matches RPC head (within 60 blocks)
echo "--- Indexer freshness ---"
HEAD=$(curl -s --max-time 5 -X POST https://ethereum-sepolia-rpc.publicnode.com \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}' \
    | python3 -c 'import sys, json; d=json.load(sys.stdin); print(int(d["result"], 16))' 2>/dev/null || echo 0)
INDEXED=$(curl -s --max-time 5 "$EXPLORER/api/health" \
    | python3 -c 'import sys, json; d=json.load(sys.stdin); print(d.get("last_indexed_block") or 0)' 2>/dev/null || echo 0)
LAG=$((HEAD - INDEXED))
if [[ "$INDEXED" -eq 0 ]] || [[ "$HEAD" -eq 0 ]]; then
    fail=$((fail+1))
    printf "  ✗ Indexer freshness — could not read head/indexed (HEAD=$HEAD, INDEXED=$INDEXED)\n"
elif [[ "$LAG" -lt 60 ]]; then
    printf "  ✓ Indexer within 60 blocks of head (lag=%d, ~%d s)\n" "$LAG" "$((LAG * 12))"
    ok=$((ok+1))
elif [[ "$LAG" -lt 600 ]]; then
    warn "Indexer lag $LAG blocks (~$((LAG * 12)) s)" \
         "tolerable but worth monitoring — re-check before D9"
else
    printf "  ✗ Indexer lagging $LAG blocks (~%d min)\n     note: re-deploy or restart indexer\n" "$((LAG / 5))"
    fail=$((fail+1))
fi
echo

echo "============================================================"
printf "  PASS: %d    WARN: %d    FAIL: %d\n" "$ok" "$warn" "$fail"
echo "============================================================"
if [[ $fail -eq 0 ]]; then
    echo "  ✓ Third-party integrations green; no drift detected."
    exit 0
else
    echo "  ✗ Address the FAIL rows above before D9."
    exit 1
fi
