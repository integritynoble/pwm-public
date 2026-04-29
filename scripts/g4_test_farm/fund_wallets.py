"""Send Sepolia ETH from the FUNDER wallet to each G4 test-farm wallet.

Per `pwm-team/coordination/STEPS_3_6_7_PLAN.md` § STEP 3 Path B.

Usage:
    PWM_PRIVATE_KEY=0x... python scripts/g4_test_farm/fund_wallets.py
    PWM_RPC_URL=https://...sepolia... PWM_PRIVATE_KEY=0x... \
        python scripts/g4_test_farm/fund_wallets.py --amount 0.025 --network sepolia

Env / args:
    PWM_PRIVATE_KEY  — funder wallet private key (default: $PWM_PRIVATE_KEY env)
    PWM_RPC_URL      — RPC endpoint
    --amount         — ETH per wallet (default 0.025; 20 wallets × 0.025 = 0.5 ETH)
    --network        — sepolia | baseSepolia (default sepolia)
    --wallets-file   — path to wallets.json (default ~/.pwm/g4-farm/wallets.json)

Idempotent: skips wallets whose balance is already ≥ amount.

After completion, run:
    python scripts/g4_test_farm/submit_l4s.py
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

logger = logging.getLogger("g4_fund")

DEFAULT_RPC = {
    "sepolia": "https://ethereum-sepolia-rpc.publicnode.com",
    "baseSepolia": "https://sepolia.base.org",
}
CHAINID = {"sepolia": 11155111, "baseSepolia": 84532}
DEFAULT_WALLETS = Path.home() / ".pwm" / "g4-farm" / "wallets.json"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--amount", type=float, default=0.025,
                    help="ETH per wallet (default 0.025)")
    ap.add_argument("--network", default="sepolia", choices=list(DEFAULT_RPC.keys()))
    ap.add_argument("--wallets-file", type=Path, default=DEFAULT_WALLETS)
    ap.add_argument("--rpc-url", default=None)
    ap.add_argument("--funder-key", default=None,
                    help="override funder priv key (default: PWM_PRIVATE_KEY env)")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be sent without broadcasting")
    args = ap.parse_args()

    try:
        from web3 import Web3
        from eth_account import Account
    except ImportError as e:
        logger.error("missing deps: %s. pip install web3 eth_account", e)
        return 1

    if not args.wallets_file.exists():
        logger.error(f"wallets file not found: {args.wallets_file}\n"
                     f"Run generate_wallets.py first.")
        return 1
    wallets = json.loads(args.wallets_file.read_text())

    rpc = args.rpc_url or os.environ.get("PWM_RPC_URL") or DEFAULT_RPC[args.network]
    funder_key = args.funder_key or os.environ.get("PWM_PRIVATE_KEY")
    if not funder_key:
        logger.error("Funder private key required: --funder-key or PWM_PRIVATE_KEY env var")
        return 1

    w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        logger.error(f"cannot connect to RPC {rpc}")
        return 1

    funder = Account.from_key(funder_key)
    funder_bal = w3.eth.get_balance(funder.address)
    funder_bal_eth = float(w3.from_wei(funder_bal, "ether"))
    needed = args.amount * len(wallets)
    logger.info(f"Funder: {funder.address}  balance: {funder_bal_eth:.4f} ETH")
    logger.info(f"Wallets: {len(wallets)}  amount each: {args.amount}  total needed: {needed:.4f} ETH")
    logger.info(f"Network: {args.network} (chainId={CHAINID[args.network]})")

    if funder_bal_eth < needed and not args.dry_run:
        logger.warning(f"Funder balance {funder_bal_eth:.4f} < needed {needed:.4f} — "
                       f"some sends will fail. Consider faucet top-up first.")

    chain_id = CHAINID[args.network]
    amount_wei = w3.to_wei(args.amount, "ether")
    skip_threshold_wei = w3.to_wei(args.amount * 0.4, "ether")  # already-funded if ≥ 40% of target

    sent = 0
    skipped = 0
    failed = 0
    nonce = w3.eth.get_transaction_count(funder.address)

    for i, wal in enumerate(wallets):
        addr = Web3.to_checksum_address(wal["address"])
        cur = w3.eth.get_balance(addr)
        cur_eth = float(w3.from_wei(cur, "ether"))
        if cur >= skip_threshold_wei:
            logger.info(f"  [{i+1:2d}/{len(wallets)}] {addr} already funded ({cur_eth:.4f} ETH) — skip")
            skipped += 1
            continue

        if args.dry_run:
            logger.info(f"  [{i+1:2d}/{len(wallets)}] {addr}  would-send {args.amount} ETH (cur={cur_eth:.4f})")
            sent += 1
            continue

        try:
            tx = {
                "from": funder.address,
                "to": addr,
                "value": amount_wei,
                "gas": 21000,
                "maxFeePerGas": w3.eth.gas_price * 2,
                "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
                "nonce": nonce,
                "chainId": chain_id,
            }
            signed = funder.sign_transaction(tx)
            raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
            tx_hash = w3.eth.send_raw_transaction(raw)
            tx_hash_hex = tx_hash.hex() if isinstance(tx_hash, bytes) else str(tx_hash)
            if not tx_hash_hex.startswith("0x"):
                tx_hash_hex = "0x" + tx_hash_hex
            logger.info(f"  [{i+1:2d}/{len(wallets)}] {addr}  → tx {tx_hash_hex}")
            nonce += 1
            sent += 1
            # Brief pause to avoid swamping the RPC.
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"  [{i+1:2d}/{len(wallets)}] {addr}  FAILED: {e}")
            failed += 1

    logger.info("")
    logger.info(f"Sent: {sent}   Skipped (already funded): {skipped}   Failed: {failed}")
    if args.dry_run:
        logger.info("(dry-run — no transactions broadcast)")
    elif sent > 0:
        logger.info(f"Wait ~30 s for txs to confirm, then run:")
        logger.info(f"    python scripts/g4_test_farm/submit_l4s.py")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
