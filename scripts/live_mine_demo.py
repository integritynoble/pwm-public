"""Cross-chain live-mine demo — submit an L4 PWMCertificate on any network.

Generalizes ``scripts/live_mine_demo_sepolia.py`` to take ``--network``.
Submits one certificate for CASSI L3-003 (by default) using the deployed
PWMRegistry + PWMCertificate on the target network. Useful as a
smoke-test the moment a new L2 deployment is verified.

Prerequisites:
  1. PWM contracts deployed on <net> (run ``deploy/l2.js``).
  2. CASSI + CACTI genesis registered on <net> (run
     ``scripts/register_genesis.py --network <net>``).
  3. ``addresses.json[<net>]`` populated.
  4. Signer funded on <net>.

Usage::

    export PWM_RPC_URL=https://sepolia.base.org
    export PWM_PRIVATE_KEY=0x<deployer-key>
    python3 scripts/live_mine_demo.py --network baseSepolia

Each run produces a unique certHash because ``--q-int`` defaults to a
value derived from the current block number — so running twice in a row
won't collide.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger("live_mine_demo")


SUPPORTED_SLOTS = (
    "testnet", "mainnet",
    "base", "baseSepolia",
    "arbitrum", "arbSepolia",
    "optimism",
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
    ap.add_argument("--network", required=True, choices=sorted(SUPPORTED_SLOTS))
    ap.add_argument("--benchmark", default="L3-003",
                    help="Artifact id to mine against (default L3-003 = CASSI)")
    ap.add_argument("--principle-id", type=int, default=3,
                    help="Integer principle id (default 3 for CASSI).")
    ap.add_argument("--q-int", type=int, default=None,
                    help="Q × 100. Default: block_number mod 100 (keeps successive runs unique).")
    ap.add_argument("--share-ratio-p", type=int, default=5000,
                    help="SP share × 10000, range [1000, 9000] per contract.")
    args = ap.parse_args()

    try:
        from web3 import Web3
        from eth_account import Account
    except ImportError:
        logger.error("web3 not installed")
        return 1

    rpc = os.environ.get("PWM_RPC_URL")
    pk = os.environ.get("PWM_PRIVATE_KEY")
    if not (rpc and pk):
        logger.error("PWM_RPC_URL and PWM_PRIVATE_KEY required")
        return 1

    repo = _repo_root()
    addresses = json.loads(
        (repo / "pwm-team/coordination/agent-coord/interfaces/addresses.json").read_text()
    )
    slot = addresses.get(args.network, {})
    if not slot.get("PWMCertificate"):
        logger.error(f"addresses.json[{args.network}].PWMCertificate not set")
        return 2
    cert_abi = json.loads(
        (repo / "pwm-team/coordination/agent-coord/interfaces/contracts_abi/PWMCertificate.json").read_text()
    )
    cert_abi = cert_abi if isinstance(cert_abi, list) else cert_abi.get("abi", [])

    w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        logger.error(f"cannot connect to RPC {rpc}")
        return 2
    chain_id = w3.eth.chain_id
    declared = slot.get("chainId")
    if declared and chain_id != declared:
        logger.error(f"chainId mismatch: slot says {declared}, RPC says {chain_id}")
        return 2
    logger.info(f"connected to {args.network} (chainId {chain_id}), block {w3.eth.block_number}")

    if not pk.startswith("0x"):
        pk = "0x" + pk
    acct = Account.from_key(pk)
    logger.info(f"signer: {acct.address}  bal={w3.from_wei(w3.eth.get_balance(acct.address), 'ether')} ETH")

    cert_contract = w3.eth.contract(
        address=w3.to_checksum_address(slot["PWMCertificate"]),
        abi=cert_abi,
    )

    # Load the L3 artifact and compute benchmarkHash (MUST match what
    # register_genesis.py produced for this network).
    layer, num = args.benchmark.split("-")
    l3_path = repo / "pwm-team/pwm_product/genesis" / layer.lower() / f"{args.benchmark}.json"
    if not l3_path.is_file():
        logger.error(f"benchmark json not found: {l3_path}")
        return 2
    l3_artifact = json.loads(l3_path.read_text())
    benchmark_hash_bytes = w3.keccak(_canonical_json(l3_artifact))
    logger.info(f"{args.benchmark} benchmarkHash: 0x{benchmark_hash_bytes.hex()}")

    # Read delta from parent L1 (what the CLI does).
    l1_path = repo / "pwm-team/pwm_product/genesis/l1" / f"L1-{num}.json"
    delta = 3
    if l1_path.is_file():
        try:
            delta = int(json.loads(l1_path.read_text()).get("difficulty_delta", 3))
        except (json.JSONDecodeError, ValueError):
            pass

    Q_int = args.q_int if args.q_int is not None else (w3.eth.block_number % 100)
    Q_int = max(1, min(100, Q_int))
    logger.info(f"principleId={args.principle_id}  delta={delta}  Q_int={Q_int}  shareRatioP={args.share_ratio_p}")

    # Build 11-field preimage → certHash.
    preimage = {
        "benchmarkHash": benchmark_hash_bytes.hex(),
        "principleId": args.principle_id,
        "l1Creator": acct.address,
        "l2Creator": acct.address,
        "l3Creator": acct.address,
        "acWallet": acct.address,
        "cpWallet": acct.address,
        "shareRatioP": args.share_ratio_p,
        "Q_int": Q_int,
        "delta": delta,
        "rank": 0,
    }
    cert_hash_bytes = w3.keccak(_canonical_json(preimage))
    logger.info(f"certHash: 0x{cert_hash_bytes.hex()}")

    struct = (
        cert_hash_bytes, benchmark_hash_bytes, args.principle_id,
        acct.address, acct.address, acct.address, acct.address, acct.address,
        args.share_ratio_p, Q_int, delta, 0,
    )
    fn = cert_contract.functions.submit(struct)
    try:
        gas = fn.estimate_gas({"from": acct.address})
    except Exception as e:
        logger.error(f"estimate_gas failed (likely revert): {e}")
        return 3
    logger.info(f"gas estimate: {gas}")

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
    logger.info(f"tx sent: {tx_hex}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    if receipt.get("status") == 0:
        logger.error("tx REVERTED on-chain")
        return 3
    logger.info(f"confirmed block {receipt.get('blockNumber')} (gas {receipt.get('gasUsed')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
