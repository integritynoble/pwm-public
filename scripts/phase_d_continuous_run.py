"""Phase D continuous-submission proxy — N certs from one wallet, sequentially.

Lightweight proxy for the 100-job acceptance criterion. The full 100-job
criterion depends on an active external job queue + additional funding;
this script exercises the CLI/contract under repeated submission to verify
no resource leaks, no cumulative gas anomalies, and no mid-run reverts.

Each cert is uniquely keyed by a different Q_int (81, 82, ... 80+N), so no
two certHashes collide and the contract's duplicate check never triggers.

Requires env: PWM_RPC_URL, PWM_PRIVATE_KEY (funded Sepolia wallet).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

logger = logging.getLogger("phase_d_continuous")


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
    ap.add_argument("--count", type=int, default=10)
    ap.add_argument("--start-q", type=int, default=81,
                    help="First Q_int in the sweep; increments by 1 per cert.")
    args = ap.parse_args()

    try:
        from web3 import Web3
        from eth_account import Account
    except ImportError as e:
        logger.error("web3 not installed: %s", e)
        return 1

    rpc_url = os.environ.get("PWM_RPC_URL")
    priv = os.environ.get("PWM_PRIVATE_KEY")
    if not rpc_url or not priv:
        logger.error("PWM_RPC_URL and PWM_PRIVATE_KEY required")
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

    if not priv.startswith("0x"):
        priv = "0x" + priv
    acct = Account.from_key(priv)
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

    start_bal = w3.from_wei(w3.eth.get_balance(acct.address), "ether")
    logger.info("signer: %s  bal=%s ETH  count=%d", acct.address, start_bal, args.count)

    chain_id = testnet["chainId"]
    nonce = w3.eth.get_transaction_count(acct.address)
    results: list[dict] = []
    t0 = time.monotonic()

    for i in range(args.count):
        Q_int = args.start_q + i
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
            gas = fn.estimate_gas({"from": acct.address})
        except Exception as e:
            logger.error("[%d/%d] Q=%d estimate_gas failed: %s", i+1, args.count, Q_int, e)
            results.append({"i": i, "Q_int": Q_int, "error": str(e)})
            continue

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
        logger.info("[%d/%d] Q=%d  tx=%s  block=%d  gas=%d  status=%s",
                    i+1, args.count, Q_int, tx_hex, block, gas_used, status)
        results.append({
            "i": i, "Q_int": Q_int, "tx": tx_hex, "block": block,
            "gas_used": gas_used, "status": status,
            "cert_hash": "0x" + cert_hash_bytes.hex(),
        })
        nonce += 1

    elapsed = time.monotonic() - t0
    end_bal = w3.from_wei(w3.eth.get_balance(acct.address), "ether")
    ok_count = sum(1 for r in results if r.get("status") == 1)
    gas_sum = sum(r.get("gas_used") or 0 for r in results)
    avg_gas = gas_sum // max(1, ok_count)
    logger.info("==== %d/%d succeeded in %.1fs; avg gas=%d; start_bal=%s → end_bal=%s ETH ====",
                ok_count, args.count, elapsed, avg_gas, start_bal, end_bal)

    out = repo / "pwm-team/coordination/agent-coord/reviews/phase_d_continuous_run.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "signer": acct.address,
        "count": args.count,
        "elapsed_s": round(elapsed, 2),
        "start_bal_eth": str(start_bal),
        "end_bal_eth": str(end_bal),
        "avg_gas": avg_gas,
        "results": results,
    }, indent=2, sort_keys=True))
    logger.info("wrote results to %s", out)
    return 0 if ok_count == args.count else 5


if __name__ == "__main__":
    sys.exit(main())
