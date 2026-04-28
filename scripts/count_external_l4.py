"""Count non-founder L4 certificate submissions on a PWM network.

Reads PWMCertificate.CertificateSubmitted events on the chain pointed at by
PWM_RPC_URL, counts unique submitter addresses that are NOT in the founders
list from addresses.json.

Per MAINNET_DEPLOY_PLAN.md Stream 1 / Stream 5 exit signal #4:
- Stream 1 done criterion (b): >= 20 non-founder L4 submissions on Base Sepolia
- Stream 5 exit signal #4: >= 1 external (non-founder) wallet has called a
  state-changing function on mainnet

Exit code 0 if count >= --threshold (default 1), 1 otherwise.

Usage:
    export PWM_RPC_URL=https://sepolia.base.org
    python3 scripts/count_external_l4.py --network baseSepolia --threshold 20
    python3 scripts/count_external_l4.py --network base --threshold 1 --since-block 12345678
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger("count_external_l4")


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("cannot find repo root")


def _load_addresses(repo_root: Path, network: str) -> dict:
    path = repo_root / "pwm-team/infrastructure/agent-contracts/addresses.json"
    data = json.loads(path.read_text())
    if network not in data:
        raise SystemExit(f"network '{network}' not in addresses.json. "
                         f"Available: {sorted(data.keys())}")
    return data[network]


def _load_abi(repo_root: Path, name: str) -> list:
    path = repo_root / "pwm-team/coordination/agent-coord/interfaces/contracts_abi" / f"{name}.json"
    raw = json.loads(path.read_text())
    return raw if isinstance(raw, list) else raw.get("abi", [])


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--network", required=True,
                        help="addresses.json key (testnet, baseSepolia, base, mainnet, ...)")
    parser.add_argument("--threshold", type=int, default=1,
                        help="exit 0 if count >= threshold (default: 1)")
    parser.add_argument("--since-block", type=int, default=0,
                        help="only count events at or after this block (default: 0 = from genesis)")
    parser.add_argument("--block-chunk", type=int, default=10_000,
                        help="getLogs chunk size (default: 10000)")
    parser.add_argument("--show-submitters", action="store_true",
                        help="print each unique submitter address")
    args = parser.parse_args()

    try:
        from web3 import Web3
    except ImportError:
        logger.error("web3 not installed. pip install web3")
        return 1

    rpc_url = os.environ.get("PWM_RPC_URL")
    if not rpc_url:
        logger.error("PWM_RPC_URL env var required")
        return 1

    repo = _repo_root()
    addrs = _load_addresses(repo, args.network)
    cert_addr = addrs.get("PWMCertificate")
    if not cert_addr:
        logger.error(f"PWMCertificate is null for network '{args.network}'")
        return 1

    founders = {a.lower() for a in addrs.get("founders", [])}
    deployer = addrs.get("deployer")
    if deployer:
        founders.add(deployer.lower())
    if not founders:
        logger.warning(f"No founders configured for '{args.network}'. "
                       "Every submitter will count as non-founder.")

    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 60}))
    if not w3.is_connected():
        logger.error(f"Cannot connect to RPC {rpc_url}")
        return 1

    abi = _load_abi(repo, "PWMCertificate")
    cert = w3.eth.contract(address=Web3.to_checksum_address(cert_addr), abi=abi)

    head = w3.eth.block_number
    start = max(args.since_block, 0)
    if start > head:
        logger.info(f"since-block ({start}) > head ({head}); no events possible.")
        print(0)
        return 1 if args.threshold > 0 else 0

    submitters: set[str] = set()
    cert_count = 0
    cur = start
    while cur <= head:
        end = min(cur + args.block_chunk - 1, head)
        try:
            logs = cert.events.CertificateSubmitted.get_logs(from_block=cur, to_block=end)
        except Exception as exc:  # web3 raises various provider errors
            logger.warning(f"getLogs {cur}-{end} failed ({exc}); halving chunk")
            if args.block_chunk <= 100:
                logger.error("chunk floor reached; aborting")
                return 1
            args.block_chunk = max(args.block_chunk // 2, 100)
            continue
        for ev in logs:
            cert_count += 1
            sub = ev["args"]["submitter"].lower()
            if sub not in founders:
                submitters.add(sub)
        cur = end + 1

    logger.info(f"network={args.network} blocks=[{start},{head}] "
                f"total_submissions={cert_count} non_founder_submitters={len(submitters)}")

    if args.show_submitters:
        for s in sorted(submitters):
            print(s)

    print(len(submitters))

    return 0 if len(submitters) >= args.threshold else 1


if __name__ == "__main__":
    sys.exit(main())
