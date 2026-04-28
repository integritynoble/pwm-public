"""Count successful founder mining transactions (DrawSettled) on a PWM network.

Reads PWMReward.DrawSettled events on the chain pointed at by PWM_RPC_URL.
Counts events whose underlying certificate's submitter is in the founders
list from addresses.json. drawAmount > 0 means the founder won a draw and
received a real PWM mining payout.

Per MAINNET_DEPLOY_PLAN.md Stream 5 exit signal #3:
  >= 7 founder mining transactions executed cleanly (zero reverts)

Exit code 0 if count >= --threshold (default 7), 1 otherwise.

Usage:
    export PWM_RPC_URL=https://mainnet.base.org
    python3 scripts/count_founder_mining_txns.py --network base --threshold 7
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger("count_founder_mining")


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
    parser.add_argument("--network", required=True)
    parser.add_argument("--threshold", type=int, default=7)
    parser.add_argument("--since-block", type=int, default=0)
    parser.add_argument("--block-chunk", type=int, default=10_000)
    parser.add_argument("--require-payout", action="store_true",
                        help="only count DrawSettled events with drawAmount > 0")
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
    reward_addr = addrs.get("PWMReward")
    cert_addr = addrs.get("PWMCertificate")
    if not reward_addr or not cert_addr:
        logger.error(f"PWMReward or PWMCertificate is null for network '{args.network}'")
        return 1

    founders = {a.lower() for a in addrs.get("founders", [])}
    deployer = addrs.get("deployer")
    if deployer:
        founders.add(deployer.lower())
    if not founders:
        logger.error(f"No founders configured for '{args.network}'; cannot identify founder draws.")
        return 1

    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 60}))
    if not w3.is_connected():
        logger.error(f"Cannot connect to RPC {rpc_url}")
        return 1

    cert_abi = _load_abi(repo, "PWMCertificate")
    reward_abi = _load_abi(repo, "PWMReward")
    cert = w3.eth.contract(address=Web3.to_checksum_address(cert_addr), abi=cert_abi)
    reward = w3.eth.contract(address=Web3.to_checksum_address(reward_addr), abi=reward_abi)

    # 1) Build certHash -> submitter map by walking PWMCertificate.CertificateSubmitted.
    cert_to_submitter: dict[bytes, str] = {}
    head = w3.eth.block_number
    start = max(args.since_block, 0)
    chunk = args.block_chunk
    cur = start
    while cur <= head:
        end = min(cur + chunk - 1, head)
        try:
            logs = cert.events.CertificateSubmitted.get_logs(from_block=cur, to_block=end)
        except Exception as exc:
            logger.warning(f"cert getLogs {cur}-{end} failed ({exc}); halving chunk")
            if chunk <= 100:
                logger.error("chunk floor reached; aborting")
                return 1
            chunk = max(chunk // 2, 100)
            continue
        for ev in logs:
            cert_to_submitter[ev["args"]["certHash"]] = ev["args"]["submitter"].lower()
        cur = end + 1

    # 2) Walk PWMReward.DrawSettled and count rows whose submitter is a founder.
    chunk = args.block_chunk
    cur = start
    founder_draws = 0
    paid_draws = 0
    while cur <= head:
        end = min(cur + chunk - 1, head)
        try:
            logs = reward.events.DrawSettled.get_logs(from_block=cur, to_block=end)
        except Exception as exc:
            logger.warning(f"reward getLogs {cur}-{end} failed ({exc}); halving chunk")
            if chunk <= 100:
                logger.error("chunk floor reached; aborting")
                return 1
            chunk = max(chunk // 2, 100)
            continue
        for ev in logs:
            ch = ev["args"]["certHash"]
            sub = cert_to_submitter.get(ch)
            if sub is None or sub not in founders:
                continue
            founder_draws += 1
            if int(ev["args"].get("drawAmount", 0)) > 0:
                paid_draws += 1
        cur = end + 1

    count = paid_draws if args.require_payout else founder_draws
    logger.info(f"network={args.network} blocks=[{start},{head}] "
                f"founder_draws={founder_draws} paid_founder_draws={paid_draws} "
                f"counted={count} threshold={args.threshold}")

    print(count)
    return 0 if count >= args.threshold else 1


if __name__ == "__main__":
    sys.exit(main())
