"""Fund FOUNDER_{2,3,4} wallets from DEPLOYER for Phase D multi-wallet tests.

One-off. Reads all keys from env (PWM_PRIVATE_KEY for the sender; each
recipient's private key from its corresponding *_PRIVATE_KEY env var so we
can derive the address without any hardcoded list).

Usage::

    # inside the safe-subshell pattern that exports the env
    python3 scripts/phase_d_fund_founders.py

Default: 0.05 ETH per recipient. All amounts in Sepolia ETH — the user owns
every key, so this is just redistributing their own test funds.

Idempotent(-ish): if a recipient already has ≥ --min-balance ETH, skipped.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger("fund_founders")

RECIPIENT_LABELS = ("FOUNDER_2", "FOUNDER_3", "FOUNDER_4")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    ap = argparse.ArgumentParser()
    ap.add_argument("--amount-eth", type=float, default=0.05)
    ap.add_argument(
        "--min-balance-eth",
        type=float,
        default=0.01,
        help="Skip recipient if their existing balance is ≥ this.",
    )
    args = ap.parse_args()

    try:
        from web3 import Web3
        from eth_account import Account
    except ImportError as e:
        logger.error("web3 not installed: %s", e)
        return 1

    rpc_url = os.environ.get("PWM_RPC_URL")
    sender_pk = os.environ.get("PWM_PRIVATE_KEY")
    if not rpc_url or not sender_pk:
        logger.error("PWM_RPC_URL and PWM_PRIVATE_KEY required")
        return 1

    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        logger.error("cannot connect to RPC")
        return 1

    sender = Account.from_key(sender_pk if sender_pk.startswith("0x") else "0x" + sender_pk)
    logger.info("sender: %s  bal=%s ETH", sender.address, w3.from_wei(w3.eth.get_balance(sender.address), "ether"))

    # Resolve recipients by deriving address from their private key env vars.
    recipients: list[tuple[str, str]] = []
    for label in RECIPIENT_LABELS:
        pk = os.environ.get(f"{label}_PRIVATE_KEY")
        if not pk:
            logger.warning("%s_PRIVATE_KEY not set, skipping", label)
            continue
        pk_hex = pk if pk.startswith("0x") else "0x" + pk
        try:
            addr = Account.from_key(pk_hex).address
        except Exception as e:
            logger.error("%s: bad key (%s), skipping", label, e)
            continue
        recipients.append((label, addr))

    if not recipients:
        logger.error("no valid recipients")
        return 1

    amount_wei = w3.to_wei(args.amount_eth, "ether")
    min_balance_wei = w3.to_wei(args.min_balance_eth, "ether")
    nonce = w3.eth.get_transaction_count(sender.address)
    chain_id = w3.eth.chain_id
    gas_price = w3.eth.gas_price

    results: list[dict] = []
    for label, addr in recipients:
        cur_bal = w3.eth.get_balance(addr)
        if cur_bal >= min_balance_wei:
            logger.info("%s (%s): already has %s ETH ≥ min, skipping",
                        label, addr, w3.from_wei(cur_bal, "ether"))
            results.append({"label": label, "address": addr, "skipped": True, "tx": None})
            continue

        logger.info("funding %s (%s) with %s ETH (nonce=%d)...",
                    label, addr, args.amount_eth, nonce)
        tx = {
            "to": w3.to_checksum_address(addr),
            "from": sender.address,
            "value": amount_wei,
            "chainId": chain_id,
            "nonce": nonce,
            "gas": 21000,
            "maxFeePerGas": gas_price * 2,
            "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
        }
        signed = sender.sign_transaction(tx)
        raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
        tx_hash = w3.eth.send_raw_transaction(raw)
        tx_hex = tx_hash.hex() if isinstance(tx_hash, bytes) else str(tx_hash)
        if not tx_hex.startswith("0x"):
            tx_hex = "0x" + tx_hex
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        if receipt.get("status") == 0:
            logger.error("%s: tx REVERTED", label)
            return 2
        new_bal = w3.eth.get_balance(addr)
        logger.info("%s: funded. tx=%s block=%d new_bal=%s ETH",
                    label, tx_hex, receipt.get("blockNumber"), w3.from_wei(new_bal, "ether"))
        results.append({"label": label, "address": addr, "skipped": False, "tx": tx_hex,
                        "block": receipt.get("blockNumber")})
        nonce += 1

    out = Path("pwm-team/coordination/agent-coord/reviews/phase_d_fund_founders.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"sender": sender.address, "results": results}, indent=2))
    logger.info("wrote receipt log to %s", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
