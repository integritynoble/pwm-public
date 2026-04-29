"""Submit one L4 certificate from each G4 farm wallet.

Per `pwm-team/coordination/STEPS_3_6_7_PLAN.md` § STEP 3 Path B.

10 wallets target L3-003 (CASSI), 10 target L3-004 (CACTI). Each cert is
unique (certHash includes the wallet index + block height + a random salt
so re-runs don't collide).

Usage:
    PWM_RPC_URL=https://...sepolia... python scripts/g4_test_farm/submit_l4s.py
    PWM_RPC_URL=... python scripts/g4_test_farm/submit_l4s.py --dry-run
    PWM_RPC_URL=... python scripts/g4_test_farm/submit_l4s.py --start-from 0 --end-at 5

Env / args:
    PWM_RPC_URL    — Sepolia RPC endpoint
    --network      — sepolia | baseSepolia (default: sepolia, matching addresses.json[testnet])
    --wallets-file — default ~/.pwm/g4-farm/wallets.json

Idempotent: a wallet that already has a certificate on record (per
PWMCertificate.CertificateSubmitted event for its address) is skipped.

After completion, run:
    python scripts/g4_test_farm/verify_g4.py
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import secrets
import sys
import time
from pathlib import Path

logger = logging.getLogger("g4_submit")

DEFAULT_RPC = {
    "sepolia": "https://ethereum-sepolia-rpc.publicnode.com",
    "baseSepolia": "https://sepolia.base.org",
}
NETWORK_TO_SLOT = {"sepolia": "testnet", "baseSepolia": "baseSepolia"}
DEFAULT_WALLETS = Path.home() / ".pwm" / "g4-farm" / "wallets.json"


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


def _load_addresses(repo: Path) -> dict:
    return json.loads(
        (repo / "pwm-team/coordination/agent-coord/interfaces/addresses.json").read_text()
    )


def _benchmark_hash(repo: Path, w3, anchor: str) -> bytes:
    """Compute the on-chain registered hash for an L3 anchor.

    Matches the pattern in scripts/live_mine_demo_sepolia.py:
    keccak256 over the canonical-JSON serialization of the L3 artifact.
    """
    artifact = json.loads(
        (repo / f"pwm-team/pwm_product/genesis/l3/{anchor}.json").read_text()
    )
    canonical = json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode()
    return w3.keccak(canonical)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--network", default="sepolia", choices=list(DEFAULT_RPC.keys()))
    ap.add_argument("--wallets-file", type=Path, default=DEFAULT_WALLETS)
    ap.add_argument("--rpc-url", default=None)
    ap.add_argument("--start-from", type=int, default=0)
    ap.add_argument("--end-at", type=int, default=None,
                    help="exclusive upper bound (default: len(wallets))")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    try:
        from web3 import Web3
        from eth_account import Account
    except ImportError as e:
        logger.error("missing deps: %s", e)
        return 1

    if not args.wallets_file.exists():
        logger.error(f"wallets file not found: {args.wallets_file}\n"
                     f"Run generate_wallets.py first.")
        return 1
    wallets = json.loads(args.wallets_file.read_text())

    rpc = args.rpc_url or os.environ.get("PWM_RPC_URL") or DEFAULT_RPC[args.network]
    repo = _repo_root()
    addrs = _load_addresses(repo)
    slot = NETWORK_TO_SLOT[args.network]
    if slot not in addrs:
        logger.error(f"addresses.json has no '{slot}' slot")
        return 1
    cert_addr = addrs[slot].get("PWMCertificate")
    chain_id = addrs[slot].get("chainId")
    if not cert_addr or not chain_id:
        logger.error(f"addresses.json[{slot}] missing PWMCertificate or chainId")
        return 1

    w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        logger.error(f"cannot connect to {rpc}")
        return 1

    cert_abi = _load_abi(repo, "PWMCertificate")
    cert = w3.eth.contract(address=Web3.to_checksum_address(cert_addr), abi=cert_abi)

    bh_cassi = _benchmark_hash(repo, w3, "L3-003")
    bh_cacti = _benchmark_hash(repo, w3, "L3-004")
    logger.info(f"L3-003 (CASSI) benchmarkHash: 0x{bh_cassi.hex()}")
    logger.info(f"L3-004 (CACTI) benchmarkHash: 0x{bh_cacti.hex()}")

    # Build a set of submitter-addresses that already have certs on chain
    # (idempotency). This is best-effort; a full event scan can be slow on
    # public RPCs. Walk recent blocks only.
    head = w3.eth.block_number
    try:
        already_submitters = set()
        # Walk last 10000 blocks (~30 h on Sepolia 12s) for prior submissions.
        chunk = 2000
        cur = max(head - 10000, 0)
        while cur <= head:
            end = min(cur + chunk - 1, head)
            try:
                logs = cert.events.CertificateSubmitted.get_logs(from_block=cur, to_block=end)
                for ev in logs:
                    already_submitters.add(ev["args"]["submitter"].lower())
            except Exception as e:
                logger.warning(f"events.get_logs {cur}-{end} failed: {e}")
            cur = end + 1
        logger.info(f"Already-submitted submitters in last 10k blocks: {len(already_submitters)}")
    except Exception as e:
        logger.warning(f"prior-submitter scan failed: {e}; treating all as fresh")
        already_submitters = set()

    end_at = args.end_at if args.end_at is not None else len(wallets)
    submitted = 0
    skipped = 0
    failed = 0

    for wal in wallets[args.start_from:end_at]:
        idx = wal["index"]
        addr = Web3.to_checksum_address(wal["address"])
        anchor = wal.get("anchor", "L3-003" if idx < 10 else "L3-004")
        bh = bh_cassi if anchor == "L3-003" else bh_cacti
        principle_id = 3 if anchor == "L3-003" else 4

        if addr.lower() in already_submitters:
            logger.info(f"  [{idx:2d}] {addr} already submitted — skip")
            skipped += 1
            continue

        # Build cert struct (matches live_mine_demo_sepolia.py shape).
        salt = secrets.token_hex(8)
        cert_preimage = json.dumps({
            "wallet_idx": idx,
            "wallet_addr": addr,
            "benchmarkHash": bh.hex(),
            "principleId": principle_id,
            "block": w3.eth.block_number,
            "salt": salt,
        }, sort_keys=True).encode()
        cert_hash = w3.keccak(cert_preimage)

        struct = (
            cert_hash,    # certHash
            bh,           # benchmarkHash
            principle_id, # principleId
            addr,         # l1Creator
            addr,         # l2Creator
            addr,         # l3Creator
            addr,         # acWallet
            addr,         # cpWallet
            5000,         # shareRatioP (50/50)
            85,           # Q_int (0.85 × 100)
            0 if anchor == "L3-003" else 1,  # delta
            0,            # rank (chosen later by scoring)
        )

        if args.dry_run:
            logger.info(f"  [{idx:2d}] {addr} would-submit cert 0x{cert_hash.hex()[:16]}… "
                        f"to {anchor}")
            submitted += 1
            continue

        try:
            wallet_acct = Account.from_key(wal["private_key"])
            fn = cert.functions.submit(struct)
            try:
                gas = fn.estimate_gas({"from": addr})
            except Exception as e:
                logger.error(f"  [{idx:2d}] {addr} gas estimate failed (will revert): {e}")
                failed += 1
                continue
            tx = fn.build_transaction({
                "from": addr,
                "chainId": chain_id,
                "nonce": w3.eth.get_transaction_count(addr),
                "gas": int(gas * 1.2),
                "maxFeePerGas": w3.eth.gas_price * 2,
                "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
            })
            signed = wallet_acct.sign_transaction(tx)
            raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
            tx_hash = w3.eth.send_raw_transaction(raw)
            tx_hash_hex = tx_hash.hex() if isinstance(tx_hash, bytes) else str(tx_hash)
            if not tx_hash_hex.startswith("0x"):
                tx_hash_hex = "0x" + tx_hash_hex
            logger.info(f"  [{idx:2d}] {addr} → cert 0x{cert_hash.hex()[:16]}… "
                        f"({anchor})  tx {tx_hash_hex}")
            submitted += 1
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"  [{idx:2d}] {addr} submit FAILED: {e}")
            failed += 1

    logger.info("")
    logger.info(f"Submitted: {submitted}   Skipped: {skipped}   Failed: {failed}")
    if args.dry_run:
        logger.info("(dry-run)")
    elif submitted > 0:
        logger.info("Wait ~1 min for txs to confirm, then:")
        logger.info("    python scripts/g4_test_farm/verify_g4.py")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
