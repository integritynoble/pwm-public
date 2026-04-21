"""Phase D 100-job ecosystem run — 4 wallets × 25 certs each, concurrent.

Exercises the full Phase D "100 consecutive jobs on Sepolia" criterion as
a multi-party run: DEPLOYER, FOUNDER_2, FOUNDER_3, FOUNDER_4 each submit
N certs in their own thread against the same benchmark (CASSI L3-003).
Each (wallet, i) pair has a distinct Q_int → distinct certHash; no wallet
submits a duplicate of any other wallet's cert.

Requires env: PWM_RPC_URL, PWM_PRIVATE_KEY (=DEPLOYER), and
FOUNDER_{2,3,4}_PRIVATE_KEY. Use the standard safe-subshell pattern.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import threading
import time
from pathlib import Path

logger = logging.getLogger("phase_d_100_job")

# (label, env_var_for_key); order matters for Q_int namespacing.
WALLETS = (
    ("DEPLOYER",  "PWM_PRIVATE_KEY"),
    ("FOUNDER_2", "FOUNDER_2_PRIVATE_KEY"),
    ("FOUNDER_3", "FOUNDER_3_PRIVATE_KEY"),
    ("FOUNDER_4", "FOUNDER_4_PRIVATE_KEY"),
)


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("cannot find repo root")


def _canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _submit_batch(label: str, acct, w3, cert_contract, chain_id: int,
                  benchmark_hash_bytes: bytes, principle_id: int, delta: int,
                  share_ratio_p: int, q_start: int, n: int,
                  results: dict) -> None:
    """Submit `n` certs from `acct`, Q_int = q_start..q_start+n-1."""
    nonce = w3.eth.get_transaction_count(acct.address)
    out: list[dict] = []
    for i in range(n):
        Q_int = q_start + i
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
            logger.error("%s[%d]: estimate_gas failed Q=%d: %s", label, i, Q_int, e)
            out.append({"i": i, "Q_int": Q_int, "error": str(e)})
            continue
        try:
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
            logger.info("%s[%d/%d] Q=%d tx=%s block=%d gas=%d",
                        label, i + 1, n, Q_int, tx_hex,
                        receipt.get("blockNumber"), receipt.get("gasUsed"))
            out.append({
                "i": i, "Q_int": Q_int, "tx": tx_hex,
                "block": receipt.get("blockNumber"),
                "gas_used": receipt.get("gasUsed"),
                "status": receipt.get("status"),
                "cert_hash": "0x" + cert_hash_bytes.hex(),
            })
            nonce += 1
        except Exception as e:
            logger.error("%s[%d]: send/wait failed Q=%d: %s", label, i, Q_int, e)
            out.append({"i": i, "Q_int": Q_int, "error": str(e)})
    results[label] = out


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(threadName)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-wallet", type=int, default=25,
                    help="Certs per wallet (default 25; 4 wallets → 100 total).")
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

    # Load accounts.
    accts: list[tuple[str, object]] = []
    for label, env in WALLETS:
        pk = os.environ.get(env)
        if not pk:
            logger.error("%s: %s not set", label, env)
            return 1
        if not pk.startswith("0x"):
            pk = "0x" + pk
        a = Account.from_key(pk)
        bal = w3.from_wei(w3.eth.get_balance(a.address), "ether")
        logger.info("%s: %s  bal=%s ETH", label, a.address, bal)
        if float(bal) < 0.01:
            logger.error("%s balance below gas budget", label)
            return 1
        accts.append((label, a))

    logger.info("benchmarkHash=0x%s  per_wallet=%d  total=%d",
                benchmark_hash_bytes.hex(), args.per_wallet, args.per_wallet * len(accts))

    # Q_int namespacing: prevents cross-wallet collision IN ADDITION to the
    # cpWallet distinction (defence in depth).
    #   DEPLOYER : 100..100+N-1
    #   FOUNDER_2: 150..150+N-1
    #   FOUNDER_3: 180..180+N-1
    #   FOUNDER_4: 210..210+N-1
    # (each wallet's cpWallet is different so certHashes differ even with
    # overlapping Q_int; the namespacing is just belt-and-braces.)
    q_starts = {"DEPLOYER": 100, "FOUNDER_2": 150, "FOUNDER_3": 180, "FOUNDER_4": 210}

    # Check Q_int stays within u8 range.
    if max(q_starts.values()) + args.per_wallet - 1 > 255:
        logger.error("per_wallet too large: Q_int would overflow u8")
        return 1

    results: dict = {}
    threads: list[threading.Thread] = []
    t0 = time.monotonic()
    for label, acct in accts:
        q_start = q_starts[label]
        t = threading.Thread(
            name=label, target=_submit_batch,
            args=(label, acct, w3, cert_contract, chain_id, benchmark_hash_bytes,
                  principle_id, delta, share_ratio_p, q_start, args.per_wallet, results),
        )
        threads.append(t)
        t.start()
    for t in threads:
        t.join(timeout=60 * 60)
    elapsed = time.monotonic() - t0

    # Summary.
    total = sum(len(rs) for rs in results.values())
    ok = sum(1 for rs in results.values() for r in rs if r.get("status") == 1)
    errors = [(label, r) for label, rs in results.items() for r in rs if r.get("status") != 1]
    all_tx = {r.get("tx") for rs in results.values() for r in rs if r.get("tx")}
    all_ch = {r.get("cert_hash") for rs in results.values() for r in rs if r.get("cert_hash")}
    logger.info("==== %d/%d succeeded in %.1fs; %d distinct txs; %d distinct certHashes ====",
                ok, total, elapsed, len(all_tx), len(all_ch))
    if errors:
        logger.error("%d failures:", len(errors))
        for label, r in errors[:5]:
            logger.error("  %s: %s", label, r)

    # End balances.
    for label, acct in accts:
        bal = w3.from_wei(w3.eth.get_balance(acct.address), "ether")
        logger.info("end balance %s: %s ETH", label, bal)

    out = repo / "pwm-team/coordination/agent-coord/reviews/phase_d_100_job_run.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "per_wallet": args.per_wallet,
        "total_target": args.per_wallet * len(accts),
        "confirmed": ok,
        "elapsed_s": round(elapsed, 2),
        "distinct_txs": len(all_tx),
        "distinct_cert_hashes": len(all_ch),
        "results": results,
    }, indent=2, sort_keys=True))
    logger.info("wrote results to %s", out)
    return 0 if ok == total else 5


if __name__ == "__main__":
    sys.exit(main())
