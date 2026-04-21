"""Sequential top-up to hit 100 total Phase D ecosystem submissions.

Follow-up to scripts/phase_d_100_job_run.py. That concurrent script
landed 41/100 certs before the public RPC (publicnode.com) started 429-ing
under parallel load, which cascaded into nonce-race failures.

This script is strictly sequential: it round-robins through the 4 funded
wallets one cert at a time, waiting for each receipt before moving on.
Rate is bounded by Sepolia block time (~12 s/tx) rather than RPC limits.

Q_int ranges are chosen to NOT collide with any certHash already produced
by the concurrent run (which used 100-124 / 150-174 / 180-204 / 210-234).
We use the safely-unused bands:
    DEPLOYER : 1..40   (fresh; 40 certs)
    FOUNDER_2: 41..50  (10 certs)
    FOUNDER_3: 51..70  (20 certs, FOUNDER_3 had low success in concurrent run)
    FOUNDER_4: 71..90  (20 certs)
  → 90 certs total, added to 41 already = 131 > 100 target.

Tunable via --per-wallet overrides. Default reaches the 100-threshold
with a small safety margin.

Requires env: PWM_RPC_URL, PWM_PRIVATE_KEY, FOUNDER_{2,3,4}_PRIVATE_KEY.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

logger = logging.getLogger("phase_d_100_seq")

WALLET_PLAN = (
    # (label, env_var, q_start, count)
    ("DEPLOYER",  "PWM_PRIVATE_KEY",     1,  25),
    ("FOUNDER_2", "FOUNDER_2_PRIVATE_KEY", 41, 5),
    ("FOUNDER_3", "FOUNDER_3_PRIVATE_KEY", 51, 15),
    ("FOUNDER_4", "FOUNDER_4_PRIVATE_KEY", 71, 15),
)


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("cannot find repo root")


def _canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=59, help="Target confirmed certs.")
    args = ap.parse_args()

    try:
        from web3 import Web3
        from eth_account import Account
    except ImportError as e:
        logger.error("web3 not installed: %s", e)
        return 1

    rpc_url = os.environ.get("PWM_RPC_URL")
    if not rpc_url:
        logger.error("PWM_RPC_URL required")
        return 1

    repo = _repo_root()
    addresses = json.loads(
        (repo / "pwm-team/coordination/agent-coord/interfaces/addresses.json").read_text()
    )
    cert_abi_raw = json.loads(
        (repo / "pwm-team/coordination/agent-coord/interfaces/contracts_abi/PWMCertificate.json").read_text()
    )
    cert_abi = cert_abi_raw if isinstance(cert_abi_raw, list) else cert_abi_raw.get("abi", [])
    testnet = addresses["testnet"]
    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        logger.error("cannot connect to RPC")
        return 1
    chain_id = testnet["chainId"]
    cert_contract = w3.eth.contract(
        address=w3.to_checksum_address(testnet["PWMCertificate"]),
        abi=cert_abi,
    )

    l3_artifact = json.loads((repo / "pwm-team/pwm_product/genesis/l3/L3-003.json").read_text())
    benchmark_hash_bytes = w3.keccak(_canonical_json(l3_artifact))
    l1_artifact = json.loads((repo / "pwm-team/pwm_product/genesis/l1/L1-003.json").read_text())
    delta = int(l1_artifact.get("difficulty_delta") or 3)
    principle_id = 3
    share_ratio_p = 5000

    # Build the ordered job list: round-robin across wallets.
    accts: dict[str, object] = {}
    for label, env, _, _ in WALLET_PLAN:
        pk = os.environ.get(env)
        if not pk:
            logger.error("%s: %s not set", label, env)
            return 1
        if not pk.startswith("0x"):
            pk = "0x" + pk
        accts[label] = Account.from_key(pk)
        bal = w3.from_wei(w3.eth.get_balance(accts[label].address), "ether")
        logger.info("%s: %s  bal=%s ETH", label, accts[label].address, bal)

    # Interleave: [W0[0], W1[0], W2[0], W3[0], W0[1], W1[1], ...]
    jobs: list[tuple[str, int]] = []
    max_per = max(count for _, _, _, count in WALLET_PLAN)
    for i in range(max_per):
        for label, _, q_start, count in WALLET_PLAN:
            if i < count:
                jobs.append((label, q_start + i))
    logger.info("planned %d jobs total (target confirmed: %d)", len(jobs), args.target)

    results: list[dict] = []
    t0 = time.monotonic()
    ok_count = 0

    for idx, (label, Q_int) in enumerate(jobs):
        if ok_count >= args.target:
            logger.info("hit target of %d confirmed certs, stopping early", args.target)
            break
        acct = accts[label]
        preimage = {
            "benchmarkHash": benchmark_hash_bytes.hex(),
            "principleId": principle_id,
            "l1Creator": acct.address,
            "l2Creator": acct.address,
            "l3Creator": acct.address,
            "acWallet": acct.address,
            "cpWallet": acct.address,
            "shareRatioP": share_ratio_p,
            "Q_int": Q_int,
            "delta": delta,
            "rank": 0,
        }
        cert_hash_bytes = w3.keccak(_canonical_json(preimage))
        struct = (
            cert_hash_bytes, benchmark_hash_bytes, principle_id,
            acct.address, acct.address, acct.address, acct.address, acct.address,
            share_ratio_p, Q_int, delta, 0,
        )
        fn = cert_contract.functions.submit(struct)
        try:
            # Fresh nonce every submission — we're fully sequential so no stale risk.
            nonce = w3.eth.get_transaction_count(acct.address)
            gas = fn.estimate_gas({"from": acct.address})
            tx = fn.build_transaction({
                "from": acct.address,
                "chainId": chain_id,
                "nonce": nonce,
                "gas": int(gas * 1.2),
                "maxFeePerGas": w3.eth.gas_price * 2,
                "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
            })
            signed = acct.sign_transaction(tx)
            raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
            tx_hash = w3.eth.send_raw_transaction(raw)
            tx_hex = tx_hash.hex() if isinstance(tx_hash, bytes) else str(tx_hash)
            if not tx_hex.startswith("0x"):
                tx_hex = "0x" + tx_hex
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            block = receipt.get("blockNumber")
            gas_used = receipt.get("gasUsed")
            status = receipt.get("status")
            if status == 1:
                ok_count += 1
            logger.info("[%d/%d → ok=%d] %s Q=%d  tx=%s  block=%d  gas=%d  status=%s",
                        idx + 1, len(jobs), ok_count, label, Q_int, tx_hex,
                        block, gas_used, status)
            results.append({
                "idx": idx, "label": label, "wallet": acct.address,
                "Q_int": Q_int, "tx": tx_hex, "block": block,
                "gas_used": gas_used, "status": status,
                "cert_hash": "0x" + cert_hash_bytes.hex(),
            })
        except Exception as e:
            logger.error("[%d/%d] %s Q=%d: %s", idx + 1, len(jobs), label, Q_int, e)
            results.append({"idx": idx, "label": label, "Q_int": Q_int, "error": str(e)})
            # Small backoff on RPC hiccup; sequential pace anyway.
            time.sleep(2.0)

    elapsed = time.monotonic() - t0
    logger.info("==== sequential top-up: %d confirmed in %.1fs ====", ok_count, elapsed)
    for label, acct in accts.items():
        bal = w3.from_wei(w3.eth.get_balance(acct.address), "ether")
        logger.info("end balance %s: %s ETH", label, bal)

    out = repo / "pwm-team/coordination/agent-coord/reviews/phase_d_100_sequential_topup.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "target": args.target,
        "confirmed": ok_count,
        "elapsed_s": round(elapsed, 2),
        "results": results,
    }, indent=2, sort_keys=True))
    logger.info("wrote results to %s", out)
    return 0 if ok_count >= args.target else 5


if __name__ == "__main__":
    sys.exit(main())
