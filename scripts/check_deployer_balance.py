"""Check that the deployer wallet has enough Base mainnet ETH for the
7-contract mainnet deploy.

Per `pwm-team/coordination/STEPS_3_6_7_PLAN.md` § STEP 7. The HANDOFF
done criterion is `deployer-funded`: ≥ 0.012 ETH on Base mainnet at
the deployer address recorded in `addresses.json[testnet].deployer`
(same key for testnet + mainnet).

Usage:
    python scripts/check_deployer_balance.py
    python scripts/check_deployer_balance.py --network base --threshold 0.012
    python scripts/check_deployer_balance.py --address 0x...
    python scripts/check_deployer_balance.py --rpc-url https://mainnet.base.org

Exit code 0 if balance >= threshold, 1 otherwise.

The script also prints USD-equivalent (via free CoinGecko price endpoint).
USD lookup is best-effort — if CoinGecko is unreachable, the script
still returns the balance and exit code; just skips the USD line.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from urllib.request import urlopen

logger = logging.getLogger("check_deployer_balance")

DEFAULT_RPC = {
    "base": "https://mainnet.base.org",
    "baseSepolia": "https://sepolia.base.org",
    "mainnet": "https://eth.llamarpc.com",
    "sepolia": "https://ethereum-sepolia-rpc.publicnode.com",
}

NETWORK_TO_SLOT = {
    "base": "base",
    "baseSepolia": "baseSepolia",
    "mainnet": "mainnet",
    "sepolia": "testnet",
}


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("cannot find repo root")


def _load_addresses() -> dict:
    p = _repo_root() / "pwm-team/infrastructure/agent-contracts/addresses.json"
    return json.loads(p.read_text())


def _eth_usd_price() -> float | None:
    """Best-effort fetch from CoinGecko. Returns None on any failure."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
        with urlopen(url, timeout=5) as r:
            data = json.loads(r.read())
        return float(data.get("ethereum", {}).get("usd", 0)) or None
    except Exception:
        return None


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--network", default="base",
                        choices=list(DEFAULT_RPC.keys()),
                        help="network to query (default: base)")
    parser.add_argument("--threshold", type=float, default=0.012,
                        help="minimum required balance in ETH (default: 0.012)")
    parser.add_argument("--address", default=None,
                        help="deployer address override (default: read from addresses.json[testnet].deployer)")
    parser.add_argument("--rpc-url", default=None,
                        help="RPC URL override (default: per-network in DEFAULT_RPC; or PWM_RPC_URL env var)")
    args = parser.parse_args()

    try:
        from web3 import Web3
    except ImportError:
        logger.error("web3 not installed. pip install web3")
        return 1

    rpc = args.rpc_url or os.environ.get("PWM_RPC_URL") or DEFAULT_RPC[args.network]

    if args.address:
        addr = args.address
    else:
        slot = NETWORK_TO_SLOT[args.network]
        addrs = _load_addresses()
        # On a network where contracts haven't been deployed yet, addresses.json
        # may have a null deployer field. Fall back to the testnet deployer (the
        # same private key is reused across networks).
        addr = addrs.get(slot, {}).get("deployer") or addrs.get("testnet", {}).get("deployer")
        if not addr:
            logger.error("Cannot resolve deployer address from addresses.json. "
                         "Pass --address explicitly.")
            return 1

    addr = Web3.to_checksum_address(addr)
    w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        logger.error(f"Cannot connect to {rpc}")
        return 1

    bal_wei = w3.eth.get_balance(addr)
    bal_eth = float(w3.from_wei(bal_wei, "ether"))

    print(f"Network:        {args.network}")
    print(f"RPC:            {rpc}")
    print(f"Deployer:       {addr}")
    print(f"Balance:        {bal_eth:.6f} ETH ({bal_wei} wei)")

    price = _eth_usd_price()
    if price is not None:
        usd = bal_eth * price
        print(f"USD-equivalent: ${usd:,.2f}  (ETH @ ${price:,.2f})")

    print(f"Threshold:      {args.threshold:.6f} ETH")

    if bal_eth >= args.threshold:
        print(f"\n✓ OK — balance {bal_eth:.6f} ≥ threshold {args.threshold:.6f}")
        return 0
    else:
        short_wei = w3.to_wei(args.threshold, "ether") - bal_wei
        short_eth = float(w3.from_wei(short_wei, "ether"))
        print(f"\n✗ INSUFFICIENT — short by {short_eth:.6f} ETH "
              f"({short_wei} wei). Send more ETH to {addr} on {args.network}.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
