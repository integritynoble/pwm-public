"""Phase D 3-CP race — three wallets submit L4 certs for CASSI L3-003 concurrently.

Verifies:
  • All 3 submissions are accepted by PWMCertificate.submit() with no revert.
  • The 3 certHashes are distinct (distinguished by cpWallet).
  • No double-submission: the contract does not reject any of them as a dup.

Requires env vars: PWM_RPC_URL and FOUNDER_{2,3,4}_PRIVATE_KEY. Uses the
12-field SubmitArgs struct — shares its hashing convention with
scripts/live_mine_demo_sepolia.py.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import threading
from pathlib import Path

logger = logging.getLogger("phase_d_3cp_race")

WALLET_LABELS = ("FOUNDER_2", "FOUNDER_3", "FOUNDER_4")


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("cannot find repo root")


def _canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _submit_one(label: str, acct, w3, cert_contract, chain_id: int,
                benchmark_hash_bytes: bytes, principle_id: int, delta: int,
                share_ratio_p: int, Q_int: int, results: dict) -> None:
    """Build + sign + send one cert tx from `acct`. Fills results[label]."""
    # Each CP's certHash differs because cpWallet is unique to the wallet.
    preimage = {
        "benchmarkHash": benchmark_hash_bytes.hex(),
        "principleId": principle_id,
        "l1Creator": acct.address,
        "l2Creator": acct.address,
        "l3Creator": acct.address,
        "acWallet": acct.address,
        "cpWallet": acct.address,  # this is what makes each cert unique in the race
        "shareRatioP": share_ratio_p,
        "Q_int": Q_int,
        "delta": delta,
        "rank": 0,
    }
    cert_hash_bytes = w3.keccak(_canonical_json(preimage))

    struct = (
        cert_hash_bytes,
        benchmark_hash_bytes,
        principle_id,
        acct.address,
        acct.address,
        acct.address,
        acct.address,
        acct.address,
        share_ratio_p,
        Q_int,
        delta,
        0,
    )
    fn = cert_contract.functions.submit(struct)

    try:
        gas = fn.estimate_gas({"from": acct.address})
    except Exception as e:
        results[label] = {"error": f"estimate_gas failed: {e}"}
        return

    tx = fn.build_transaction({
        "from": acct.address,
        "chainId": chain_id,
        "nonce": w3.eth.get_transaction_count(acct.address),
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

    logger.info("%s: tx sent %s (certHash=0x%s)", label, tx_hex, cert_hash_bytes.hex())
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    except Exception as e:
        results[label] = {"tx": tx_hex, "error": f"wait failed: {e}",
                          "cert_hash": "0x" + cert_hash_bytes.hex()}
        return
    results[label] = {
        "wallet": acct.address,
        "tx": tx_hex,
        "block": receipt.get("blockNumber"),
        "gas_used": receipt.get("gasUsed"),
        "status": receipt.get("status"),
        "cert_hash": "0x" + cert_hash_bytes.hex(),
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(threadName)s %(message)s")
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

    # Common params — identical across all 3 CPs; only cpWallet differs.
    l3_artifact = json.loads((repo / "pwm-team/pwm_product/genesis/l3/L3-003.json").read_text())
    benchmark_hash_bytes = w3.keccak(_canonical_json(l3_artifact))
    l1_artifact = json.loads((repo / "pwm-team/pwm_product/genesis/l1/L1-003.json").read_text())
    delta = int(l1_artifact.get("difficulty_delta") or 3)
    principle_id = 3
    Q_int = 87   # fresh — differs from earlier demo/CLI runs (85)
    share_ratio_p = 5000

    # Load all three CP accounts.
    accts: list[tuple[str, object]] = []
    for label in WALLET_LABELS:
        pk = os.environ.get(f"{label}_PRIVATE_KEY")
        if not pk:
            logger.error("%s_PRIVATE_KEY not set", label)
            return 1
        if not pk.startswith("0x"):
            pk = "0x" + pk
        a = Account.from_key(pk)
        bal = w3.from_wei(w3.eth.get_balance(a.address), "ether")
        logger.info("%s: %s  bal=%s ETH", label, a.address, bal)
        if float(bal) < 0.001:
            logger.error("%s balance below gas threshold", label)
            return 1
        accts.append((label, a))

    logger.info("L3-003 benchmarkHash: 0x%s  Q_int=%d  delta=%d",
                benchmark_hash_bytes.hex(), Q_int, delta)

    # Fire all 3 in parallel.
    results: dict = {}
    threads: list[threading.Thread] = []
    for label, acct in accts:
        t = threading.Thread(
            name=label,
            target=_submit_one,
            args=(label, acct, w3, cert_contract, chain_id, benchmark_hash_bytes,
                  principle_id, delta, share_ratio_p, Q_int, results),
        )
        threads.append(t)
        t.start()
    for t in threads:
        t.join(timeout=360)

    # Report.
    out = repo / "pwm-team/coordination/agent-coord/reviews/phase_d_3cp_race.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, sort_keys=True))
    logger.info("wrote results to %s", out)

    # Validate the three success properties.
    ok_count = sum(1 for r in results.values() if r.get("status") == 1)
    cert_hashes = {r.get("cert_hash") for r in results.values() if r.get("cert_hash")}
    tx_hashes = {r.get("tx") for r in results.values() if r.get("tx")}
    logger.info("==== summary: %d/%d succeeded; %d distinct certHashes; %d distinct txs ====",
                ok_count, len(results), len(cert_hashes), len(tx_hashes))
    if ok_count != len(WALLET_LABELS):
        logger.error("not all CPs succeeded:\n%s", json.dumps(results, indent=2))
        return 3
    if len(cert_hashes) != len(WALLET_LABELS):
        logger.error("certHash collision:\n%s", json.dumps(results, indent=2))
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
