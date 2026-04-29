"""End-to-end check that `multisig/signers.md` is ready for STEP 6 PASS.

Per `pwm-team/coordination/STEPS_3_6_7_PLAN.md` § STEP 6 done criterion:
  (a) 5 founder addresses recorded in multisig/signers.md
  (b) None equals the deployer or any known hot wallet
  (c) Each has ≥ 1 self-sent tx on Base Sepolia (proof of custody)
  (d) `verify_signers_md.py` exits 0

Usage:
    python scripts/verify_signers_md.py
    python scripts/verify_signers_md.py --network sepolia  # if testing against eth-sepolia instead

Exit code 0 if all criteria pass, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

# Reuse helpers from proof_of_custody.py (sibling script).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from proof_of_custody import _check_self_tx, DEFAULT_RPC

logger = logging.getLogger("verify_signers_md")


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("cannot find repo root")


def _signers_path() -> Path:
    return _repo_root() / "pwm-team/infrastructure/agent-contracts/multisig/signers.md"


def _addresses_path() -> Path:
    return _repo_root() / "pwm-team/infrastructure/agent-contracts/addresses.json"


def _parse_signers_md() -> list[str]:
    """Pull all 0x40-hex addresses out of signers.md, dedup."""
    text = _signers_path().read_text()
    found = re.findall(r"0x[0-9a-fA-F]{40}", text)
    placeholder = "0x" + "_" * 40
    return [a for a in dict.fromkeys(found) if a != placeholder]


def _known_disallowed_addresses() -> set[str]:
    """The deployer + any address recorded as a 'founders' on a testnet
    deploy. These are hot wallets — they MUST NOT be reused as mainnet
    multisig founders."""
    addrs = json.loads(_addresses_path().read_text())
    disallowed: set[str] = set()
    for slot in ("testnet", "baseSepolia", "local", "base", "mainnet"):
        s = addrs.get(slot, {})
        deployer = (s.get("deployer") or "")
        if deployer:
            disallowed.add(deployer.lower())
        for a in s.get("founders", []) or []:
            disallowed.add(a.lower())
    return disallowed


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--network", default="baseSepolia",
                        choices=list(DEFAULT_RPC.keys()))
    parser.add_argument("--rpc-url", default=None)
    parser.add_argument("--lookback-blocks", type=int, default=5_000,
                        help="RPC block-walk lookback (default: 5000). Only used when ETHERSCAN_API_KEY is unset.")
    args = parser.parse_args()

    try:
        from web3 import Web3
    except ImportError:
        logger.error("web3 not installed. pip install web3")
        return 1

    fails = 0

    # (a) 5 addresses present?
    addrs = _parse_signers_md()
    print(f"Found {len(addrs)} unique non-placeholder address(es) in signers.md")
    if len(addrs) < 5:
        print(f"  ✗ Need exactly 5; have {len(addrs)}. "
              f"Replace placeholder lines (0x____...) with real addresses.")
        fails += 1
    elif len(addrs) > 5:
        print(f"  ✗ Found {len(addrs)} addresses — exactly 5 required.")
        fails += 1
    else:
        print(f"  ✓ exactly 5 addresses found")

    # (b) None in disallowed (deployer + testnet founders)?
    disallowed = _known_disallowed_addresses()
    print(f"\nCross-checking against {len(disallowed)} known hot-wallet addresses...")
    for a in addrs:
        if a.lower() in disallowed:
            print(f"  ✗ {a} appears in addresses.json as deployer/founder hot wallet — "
                  f"DO NOT use as a mainnet multisig founder")
            fails += 1
        else:
            print(f"  ✓ {a} not in disallow list")

    # (c) Each has ≥ 1 self-tx on the chosen network (proof of custody)?
    if addrs:
        rpc = args.rpc_url or DEFAULT_RPC[args.network]
        w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 60}))
        if not w3.is_connected():
            print(f"\n✗ Cannot connect to {rpc} for proof-of-custody check")
            fails += 1
        else:
            print(f"\nProof-of-custody check on {args.network} ({rpc})...")
            print(f"  lookback: {args.lookback_blocks} blocks (head={w3.eth.block_number})")
            for raw in addrs:
                addr = Web3.to_checksum_address(raw)
                r = _check_self_tx(w3, addr, args.lookback_blocks, network=args.network)
                if r["found_self_tx"]:
                    tx = r["self_tx"]
                    print(f"  ✓ {addr}  self-tx 0x{tx['tx_hash'].lstrip('0x')[:16]}…  block {tx['block']}")
                else:
                    print(f"  ✗ {addr}  no self-tx in last {args.lookback_blocks} blocks "
                          f"(have the holder send any-value self-tx)")
                    fails += 1

    print()
    if fails == 0:
        print("✓ ALL CHECKS PASSED — multisig/signers.md is ready for Step 6.")
        return 0
    print(f"✗ {fails} check(s) failed. See above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
