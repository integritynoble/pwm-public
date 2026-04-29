"""Verify each candidate founder address has at least one self-sent
transaction on Base Sepolia.

Per `pwm-team/coordination/STEPS_3_6_7_PLAN.md` § STEP 6 acceptance
criterion #3: "each device has signed at least one Sepolia tx (proof
of custody — the holder controls the private key)".

A self-sent tx (`from == to`, value any amount) proves:
  - The private key holder has the device set up correctly (the
    address printed on the device matches the address signing).
  - The device can produce a valid Ethereum signature.
  - The address is funded enough to pay gas (smallest possible cost
    on Base Sepolia is fractions of a cent).

Usage:
    python scripts/proof_of_custody.py 0xAddr1 0xAddr2 ...
    python scripts/proof_of_custody.py --from-signers-md
    python scripts/proof_of_custody.py --network sepolia 0xAddr1

Exit code 0 if every address has ≥ 1 self-tx. Exit 1 on any miss.

The default network is Base Sepolia (chainId 84532). Override with
`--network sepolia` for Ethereum Sepolia or `--network base` for
mainnet (mainnet check is unusual but supported for verification
after key migration).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

logger = logging.getLogger("proof_of_custody")

DEFAULT_RPC = {
    "baseSepolia": "https://sepolia.base.org",
    "sepolia": "https://ethereum-sepolia-rpc.publicnode.com",
    "base": "https://mainnet.base.org",
    "mainnet": "https://eth.llamarpc.com",
}


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("cannot find repo root")


def _addresses_in_signers_md() -> list[str]:
    """Pull all 0x... addresses out of multisig/signers.md."""
    p = _repo_root() / "pwm-team/infrastructure/agent-contracts/multisig/signers.md"
    if not p.exists():
        return []
    text = p.read_text()
    return list({a for a in re.findall(r"0x[0-9a-fA-F]{40}", text)
                 if a.lower() != "0x" + "_" * 40 and a != "0x____________________________________________"})


CHAINID = {
    "baseSepolia": 84532,
    "sepolia": 11155111,
    "base": 8453,
    "mainnet": 1,
}


def _check_self_tx_etherscan(network: str, address: str, api_key: str) -> dict | None:
    """Query Etherscan v2 multi-chain API for an address's tx list and look
    for a self-tx (from == to). Returns the same dict shape as the
    block-walking version, or None if the API call fails (caller falls back).
    """
    import json
    from urllib.parse import urlencode
    from urllib.request import urlopen

    chainid = CHAINID.get(network)
    if not chainid:
        return None
    qs = urlencode({
        "chainid": chainid,
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 100,
        "sort": "desc",
        "apikey": api_key,
    })
    url = f"https://api.etherscan.io/v2/api?{qs}"
    try:
        with urlopen(url, timeout=15) as r:
            data = json.loads(r.read())
    except Exception as e:
        logger.warning(f"Etherscan v2 API failed for {address}: {e}")
        return None
    if data.get("status") not in ("1", 1, "0", 0):
        logger.warning(f"Etherscan v2 API unexpected response: {data}")
        return None
    txs = data.get("result") or []
    if not isinstance(txs, list):
        return None
    found = None
    for tx in txs:
        tx_from = (tx.get("from") or "").lower()
        tx_to = (tx.get("to") or "").lower()
        if tx_from == address.lower() and tx_to == address.lower():
            found = {
                "tx_hash": tx.get("hash"),
                "block": int(tx.get("blockNumber", 0)),
                "value_wei": int(tx.get("value", 0)),
            }
            break
    return {
        "address": address,
        "tx_count_total": int(txs[0].get("nonce", 0)) + 1 if txs else 0,
        "found_self_tx": found is not None,
        "self_tx": found,
    }


def _check_self_tx(w3, address: str, lookback_blocks: int, network: str = "") -> dict:
    """Look for a self-sent tx from `address`.

    Tries Etherscan v2 multi-chain API first (fast). Falls back to
    walking recent blocks via the RPC (slow but works without API key).
    """
    import os
    api_key = os.environ.get("ETHERSCAN_API_KEY") or os.environ.get("BASESCAN_API_KEY")
    if api_key and network:
        result = _check_self_tx_etherscan(network, address, api_key)
        if result is not None:
            return result
        logger.info(f"Etherscan v2 lookup failed; falling back to RPC block-walk for {address}")

    # Fallback: walk blocks via RPC.
    head = w3.eth.block_number
    start = max(0, head - lookback_blocks)
    nonce = w3.eth.get_transaction_count(address)
    found = None
    for blk_n in range(head, start - 1, -1):
        try:
            blk = w3.eth.get_block(blk_n, full_transactions=True)
        except Exception as e:
            logger.debug(f"get_block({blk_n}) failed: {e}")
            continue
        for tx in blk.transactions:
            tx_from = (tx.get("from") or "").lower()
            tx_to = (tx.get("to") or "").lower()
            if tx_from == address.lower() and tx_to == address.lower():
                found = {
                    "tx_hash": tx["hash"].hex() if hasattr(tx["hash"], "hex") else str(tx["hash"]),
                    "block": blk_n,
                    "value_wei": int(tx.get("value", 0)),
                }
                break
        if found:
            break
    return {
        "address": address,
        "tx_count_total": nonce,
        "found_self_tx": found is not None,
        "self_tx": found,
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("addresses", nargs="*",
                        help="addresses to verify; 0x-prefixed checksummed or lowercase")
    parser.add_argument("--from-signers-md", action="store_true",
                        help="read addresses from pwm-team/infrastructure/agent-contracts/multisig/signers.md")
    parser.add_argument("--network", default="baseSepolia",
                        choices=list(DEFAULT_RPC.keys()),
                        help="network to query (default: baseSepolia)")
    parser.add_argument("--rpc-url", default=None)
    parser.add_argument("--lookback-blocks", type=int, default=5_000,
                        help="RPC block-walk lookback (default: 5000 ≈ ~3 hours on Base Sepolia, ~17 hours on Sepolia). "
                             "Only used when ETHERSCAN_API_KEY is unset; with a key, the Etherscan v2 API does the lookup in one call.")
    args = parser.parse_args()

    try:
        from web3 import Web3
    except ImportError:
        logger.error("web3 not installed. pip install web3")
        return 1

    addresses = list(args.addresses)
    if args.from_signers_md:
        addresses += _addresses_in_signers_md()
    if not addresses:
        logger.error("No addresses provided. Pass them as args or --from-signers-md.")
        return 1

    rpc = args.rpc_url or os.environ.get("PWM_RPC_URL") or DEFAULT_RPC[args.network]
    w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 60}))
    if not w3.is_connected():
        logger.error(f"Cannot connect to {rpc}")
        return 1

    print(f"Network: {args.network}  RPC: {rpc}")
    print(f"Lookback: {args.lookback_blocks} blocks (head = {w3.eth.block_number})\n")

    rows = []
    fails = 0
    for raw in addresses:
        try:
            addr = Web3.to_checksum_address(raw)
        except Exception:
            print(f"  ✗ {raw}: not a valid Ethereum address")
            fails += 1
            continue
        r = _check_self_tx(w3, addr, args.lookback_blocks, network=args.network)
        rows.append(r)
        if r["found_self_tx"]:
            tx = r["self_tx"]
            print(f"  ✓ {addr}  tx_count={r['tx_count_total']}  self-tx=0x{tx['tx_hash'].lstrip('0x')}  block={tx['block']}")
        else:
            print(f"  ✗ {addr}  tx_count={r['tx_count_total']}  no self-tx in last {args.lookback_blocks} blocks")
            fails += 1

    print()
    print(f"Verified: {len(rows) - fails} / {len(rows)}")
    if fails:
        print(f"Missing proof-of-custody for {fails} address(es). Have each holder send "
              f"a self-tx (any value, even 0 wei) and re-run.")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
