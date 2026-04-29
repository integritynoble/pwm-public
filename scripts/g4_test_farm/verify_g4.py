"""End-to-end verification that the G4 gate (≥ 20 non-founder L4
submissions on testnet) is cleared.

Per `pwm-team/coordination/STEPS_3_6_7_PLAN.md` § STEP 3 acceptance.
Reuses scripts/count_external_l4.py for the on-chain query.

Usage:
    PWM_RPC_URL=https://...sepolia... python scripts/g4_test_farm/verify_g4.py
    PWM_RPC_URL=... python scripts/g4_test_farm/verify_g4.py --network testnet --threshold 20

Exit code 0 if ≥ threshold non-founder submitters; 1 otherwise.

Prints the unique submitters + which anchor each targeted, so the
output can be pasted into the STEP_3 READY signal's `artifacts` block.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger("g4_verify")


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("cannot find repo root")


def _load_abi(repo: Path, name: str) -> list:
    raw = json.loads(
        (repo / "pwm-team/coordination/agent-coord/interfaces/contracts_abi" / f"{name}.json").read_text()
    )
    return raw if isinstance(raw, list) else raw.get("abi", [])


def _benchmark_hash(repo: Path, w3, anchor: str) -> bytes:
    artifact = json.loads((repo / f"pwm-team/pwm_product/genesis/l3/{anchor}.json").read_text())
    canonical = json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode()
    return w3.keccak(canonical)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--network", default="testnet",
                    help="addresses.json key (default 'testnet' = Ethereum Sepolia per the existing deploy)")
    ap.add_argument("--threshold", type=int, default=20)
    ap.add_argument("--since-block", type=int, default=0)
    ap.add_argument("--rpc-url", default=None)
    args = ap.parse_args()

    try:
        from web3 import Web3
    except ImportError:
        logger.error("web3 not installed")
        return 1

    rpc = args.rpc_url or os.environ.get("PWM_RPC_URL")
    if not rpc:
        logger.error("PWM_RPC_URL env var required (or pass --rpc-url)")
        return 1

    repo = _repo_root()
    addrs_path = repo / "pwm-team/infrastructure/agent-contracts/addresses.json"
    addrs = json.loads(addrs_path.read_text())
    if args.network not in addrs:
        logger.error(f"addresses.json has no '{args.network}' slot")
        return 1
    cert_addr = addrs[args.network].get("PWMCertificate")
    if not cert_addr:
        logger.error(f"PWMCertificate is null for {args.network}")
        return 1
    founders = {a.lower() for a in addrs[args.network].get("founders") or []}
    deployer = (addrs[args.network].get("deployer") or "").lower()
    if deployer:
        founders.add(deployer)

    w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 60}))
    if not w3.is_connected():
        logger.error("RPC unreachable")
        return 1

    cert_abi = _load_abi(repo, "PWMCertificate")
    cert = w3.eth.contract(address=Web3.to_checksum_address(cert_addr), abi=cert_abi)

    bh_cassi = _benchmark_hash(repo, w3, "L3-003")
    bh_cacti = _benchmark_hash(repo, w3, "L3-004")
    bh_to_anchor = {bh_cassi.hex(): "L3-003", bh_cacti.hex(): "L3-004"}

    head = w3.eth.block_number
    start = max(args.since_block, 0)
    chunk = 5000
    rows = []
    submitters_per_anchor: dict[str, set[str]] = {"L3-003": set(), "L3-004": set(), "other": set()}
    cur = start
    while cur <= head:
        end = min(cur + chunk - 1, head)
        try:
            logs = cert.events.CertificateSubmitted.get_logs(from_block=cur, to_block=end)
        except Exception as e:
            logger.warning(f"getLogs {cur}-{end} failed ({e}); halving")
            chunk = max(chunk // 2, 100)
            continue
        for ev in logs:
            sub = ev["args"]["submitter"].lower()
            if sub in founders:
                continue
            bh_hex = ev["args"]["benchmarkHash"].hex()
            anchor = bh_to_anchor.get(bh_hex, "other")
            submitters_per_anchor[anchor].add(sub)
            rows.append({
                "block": ev["blockNumber"],
                "submitter": ev["args"]["submitter"],
                "benchmark_hash": bh_hex,
                "anchor": anchor,
                "tx_hash": ev["transactionHash"].hex(),
            })
        cur = end + 1

    all_submitters = (submitters_per_anchor["L3-003"]
                      | submitters_per_anchor["L3-004"]
                      | submitters_per_anchor["other"])

    print(f"Network: {args.network}  RPC: {rpc}")
    print(f"Block range: [{start}, {head}]")
    print(f"Total CertificateSubmitted events from non-founder addresses: {len(rows)}")
    print(f"Unique non-founder submitters: {len(all_submitters)}")
    print(f"  L3-003 (CASSI): {len(submitters_per_anchor['L3-003'])} unique submitters")
    print(f"  L3-004 (CACTI): {len(submitters_per_anchor['L3-004'])} unique submitters")
    if submitters_per_anchor["other"]:
        print(f"  other:          {len(submitters_per_anchor['other'])} (unrecognized benchmark)")

    print()
    print("Per-anchor unique submitter addresses:")
    for anchor in ("L3-003", "L3-004"):
        for s in sorted(submitters_per_anchor[anchor]):
            print(f"  {anchor}  {s}")

    print()
    if len(all_submitters) >= args.threshold:
        print(f"✓ G4 GATE CLEARED — {len(all_submitters)} ≥ {args.threshold}")
        return 0
    print(f"✗ G4 GATE NOT YET — {len(all_submitters)} < {args.threshold} "
          f"(short by {args.threshold - len(all_submitters)})")
    return 1


if __name__ == "__main__":
    sys.exit(main())
