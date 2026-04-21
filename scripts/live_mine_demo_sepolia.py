"""Live Phase C demo: submit a PWMCertificate against CASSI L3-003 on Sepolia.

This is a one-off script to prove Phase C live acceptance works at the chain
layer. Uses the 12-field struct the deployed PWMCertificate.submit() actually
expects (NOT the whitepaper schema the CLI currently produces — that's a
known mismatch in the reference impl, filed as a follow-up).

Prerequisites:
    export PWM_RPC_URL=<Alchemy/Infura Sepolia>
    export PWM_PRIVATE_KEY=<deployer key>  (or any funded Sepolia wallet)

Usage:
    python3 scripts/live_mine_demo_sepolia.py

The script is idempotent with respect to state — each run constructs a fresh
cert_hash (from keccak over the struct fields), so running twice just
creates two certificates. Useful for the 3-CP race test in Phase D: run this
from 3 different wallets concurrently, see that exactly one wins.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger("live_mine_demo")


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("cannot find repo root")


def _artifact_hash(obj: dict, w3) -> bytes:
    """keccak256 of canonical-JSON serialized artifact → 32 bytes."""
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return w3.keccak(canonical)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

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
    cert_abi = json.loads(
        (repo / "pwm-team/coordination/agent-coord/interfaces/contracts_abi/PWMCertificate.json").read_text()
    )
    cert_abi = cert_abi if isinstance(cert_abi, list) else cert_abi.get("abi", [])

    testnet = addresses["testnet"]
    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        logger.error("cannot connect to RPC")
        return 1

    acct = Account.from_key(priv)
    logger.info("signer: %s  block: %d  chainId: %d",
                acct.address, w3.eth.block_number, testnet["chainId"])

    cert_contract = w3.eth.contract(
        address=w3.to_checksum_address(testnet["PWMCertificate"]),
        abi=cert_abi,
    )

    # Load the CASSI L3-003 artifact; compute its hash (already registered from
    # the earlier genesis-registration script).
    l3_artifact = json.loads((repo / "pwm-team/pwm_product/genesis/l3/L3-003.json").read_text())
    benchmark_hash_bytes = _artifact_hash(l3_artifact, w3)
    logger.info("L3-003 benchmarkHash: 0x%s", benchmark_hash_bytes.hex())

    # Build the 12-field cert struct per PWMCertificate.submit(tuple)
    principle_id = 3  # CASSI is Principle #003
    Q_int = 85          # mock Q = 0.85 × 100
    delta = 3           # CASSI difficulty tier
    share_ratio_p = 5000  # 0.50 × 10000 — SP gets 50% of 55%, CP gets 50%

    # certHash = keccak256 over the 11 non-cert_hash fields (deterministic + unique per run)
    # Include block number to avoid duplicates across runs.
    cert_preimage = json.dumps({
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
        "block": w3.eth.block_number,
    }, sort_keys=True).encode()
    cert_hash_bytes = w3.keccak(cert_preimage)
    logger.info("certHash: 0x%s", cert_hash_bytes.hex())

    # Build the struct in ABI-declared order
    struct = (
        cert_hash_bytes,
        benchmark_hash_bytes,
        principle_id,
        acct.address,  # l1Creator
        acct.address,  # l2Creator
        acct.address,  # l3Creator
        acct.address,  # acWallet
        acct.address,  # cpWallet
        share_ratio_p,
        Q_int,
        delta,
        0,  # rank
    )

    logger.info("submitting cert to PWMCertificate...")
    fn = cert_contract.functions.submit(struct)

    try:
        gas = fn.estimate_gas({"from": acct.address})
        logger.info("gas estimate: %d", gas)
    except Exception as e:
        logger.error("gas estimate failed (likely will revert): %s", e)
        return 2

    tx = fn.build_transaction({
        "from": acct.address,
        "chainId": testnet["chainId"],
        "nonce": w3.eth.get_transaction_count(acct.address),
        "gas": int(gas * 1.2),
        "maxFeePerGas": w3.eth.gas_price * 2,
        "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
    })
    signed = acct.sign_transaction(tx)
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    tx_hash = w3.eth.send_raw_transaction(raw)
    tx_hash_hex = tx_hash.hex() if isinstance(tx_hash, bytes) else str(tx_hash)
    if not tx_hash_hex.startswith("0x"):
        tx_hash_hex = "0x" + tx_hash_hex
    logger.info("tx sent: %s", tx_hash_hex)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    if receipt.get("status") == 0:
        logger.error("tx REVERTED on-chain")
        return 3
    logger.info(
        "confirmed in block %d (gas used %d). Etherscan: https://sepolia.etherscan.io/tx/%s",
        receipt.get("blockNumber"), receipt.get("gasUsed"), tx_hash_hex,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
