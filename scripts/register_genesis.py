"""Register CASSI + CACTI (L1/L2/L3 each) on PWMRegistry — any network.

Generalized successor to ``scripts/register_genesis_sepolia.py``. Takes a
``--network`` argument and resolves the right PWMRegistry address from
``addresses.json`` for that slot.

Same keccak256(canonical_json) hashing convention as
``register_genesis_sepolia.py`` and ``pwm-node mine`` — this MUST match, or
certs submitted via the CLI will fail benchmarkHash lookup.

## Why not scripts/register_genesis.js?

The JavaScript version uses ``JSON.stringify`` which cannot faithfully
reproduce Python's ``json.dumps(sort_keys=True, separators=(",", ":"))``.
Specifically: JS Numbers lose the int/float distinction at parse time, so
``26.0`` serializes as ``"26"`` in JS and ``"26.0"`` in Python. The
hashes diverge. Use this Python script for any on-chain registration.

## Supported networks

- ``testnet`` — Ethereum Sepolia (chainId 11155111)
- ``baseSepolia`` — Base Sepolia (chainId 84532)
- ``arbSepolia`` — Arbitrum Sepolia (chainId 421614)
- ``base`` — Base mainnet (chainId 8453)
- ``arbitrum`` — Arbitrum One (chainId 42161)
- ``optimism`` — Optimism mainnet (chainId 10)
- ``mainnet`` — Ethereum mainnet (chainId 1)
- ``local`` — Hardhat local (chainId 31337)

## Usage

    # Dry-run: compute hashes + plan, no txs
    python3 scripts/register_genesis.py --network baseSepolia --dry-run

    # Live on Base Sepolia
    export PWM_RPC_URL=https://sepolia.base.org
    export PWM_PRIVATE_KEY=0x<your-64-hex>
    python3 scripts/register_genesis.py --network baseSepolia

Each network's slot in ``addresses.json`` must have a non-zero
``PWMRegistry`` address. Run the L2 deploy first
(``npx hardhat run deploy/l2.js --network <net>``).

## Safety

Same as ``register_genesis_sepolia.py``: no key material is ever logged,
printed, or written to disk. Each tx checks ``exists()`` before sending
to stay idempotent. Writes a review file with tx hashes + network
explorer URLs to
``pwm-team/coordination/agent-coord/reviews/genesis_registration_<network>_<date>.md``.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any

logger = logging.getLogger("register_genesis")


ARTIFACTS_TO_REGISTER = [
    ("L1-003", "l1/L1-003.json", 1),
    ("L2-003", "l2/L2-003.json", 2),
    ("L3-003", "l3/L3-003.json", 3),
    ("L1-004", "l1/L1-004.json", 1),
    ("L2-004", "l2/L2-004.json", 2),
    ("L3-004", "l3/L3-004.json", 3),
]


# Per-network metadata. Only drives pretty-printing + explorer URLs;
# actual RPC comes from env (PWM_RPC_URL) and chainId from addresses.json.
NETWORK_META = {
    "testnet":     {"display": "Ethereum Sepolia",  "explorer": "https://sepolia.etherscan.io/tx/"},
    "mainnet":     {"display": "Ethereum Mainnet",  "explorer": "https://etherscan.io/tx/"},
    "base":        {"display": "Base Mainnet",       "explorer": "https://basescan.org/tx/"},
    "baseSepolia": {"display": "Base Sepolia",       "explorer": "https://sepolia.basescan.org/tx/"},
    "arbitrum":    {"display": "Arbitrum One",       "explorer": "https://arbiscan.io/tx/"},
    "arbSepolia":  {"display": "Arbitrum Sepolia",   "explorer": "https://sepolia.arbiscan.io/tx/"},
    "optimism":    {"display": "Optimism Mainnet",   "explorer": "https://optimistic.etherscan.io/tx/"},
    "local":       {"display": "Hardhat Local",      "explorer": ""},
}


def _parent_key(artifact_id: str) -> str | None:
    layer_prefix, num = artifact_id.split("-")
    if layer_prefix == "L1":
        return None
    if layer_prefix == "L2":
        return f"L1-{num}"
    if layer_prefix == "L3":
        return f"L2-{num}"
    raise ValueError(f"unknown artifact_id format: {artifact_id}")


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("Cannot find repo root (pwm-team/)")


def _load_addresses(repo_root: Path) -> dict:
    path = repo_root / "pwm-team" / "coordination" / "agent-coord" / "interfaces" / "addresses.json"
    return json.loads(path.read_text())


def _load_abi(repo_root: Path, contract_name: str) -> list:
    path = repo_root / "pwm-team" / "coordination" / "agent-coord" / "interfaces" / "contracts_abi" / f"{contract_name}.json"
    raw = json.loads(path.read_text())
    return raw if isinstance(raw, list) else raw.get("abi", [])


# UI-only fields excluded from canonical-JSON hashing. Adding a slug or
# rebuilding the title for display purposes must NOT change the on-chain
# artifact hash — otherwise existing registrations would orphan and
# `pwm-node mine` would fail with "benchmark not registered". Keep this
# set small and only extend it for fields that are pure presentation.
UI_ONLY_FIELDS = frozenset({
    "display_slug",
    "display_color",
    "ui_metadata",
    "registration_tier",
})


def _canonical_for_hashing(obj: dict) -> dict:
    """Strip UI-only fields before computing the canonical hash.

    The chain stores keccak256(canonical_json(manifest)). Manifests authored
    after 2026-05-03 may include human-readable display fields that DID NOT
    exist when earlier artifacts were registered. To keep hash-invariance
    across schema additions, we filter those fields out before hashing.
    """
    return {k: v for k, v in obj.items() if k not in UI_ONLY_FIELDS}


def _canonical_json(obj: Any) -> bytes:
    filtered = _canonical_for_hashing(obj) if isinstance(obj, dict) else obj
    return json.dumps(filtered, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _artifact_hash(obj: dict, w3) -> str:
    digest = w3.keccak(_canonical_json(obj))
    hex_str = digest.hex()
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    return "0x" + hex_str.zfill(64)


def _write_review(repo_root: Path, network: str, plan: list, results: list,
                  signer_addr: str, all_present: bool, chain_id: int) -> None:
    review_dir = repo_root / "pwm-team" / "coordination" / "agent-coord" / "reviews"
    review_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    path = review_dir / f"genesis_registration_{network}_{today}.md"
    meta = NETWORK_META.get(network, {})
    explorer = meta.get("explorer", "")

    lines = [
        "# Genesis Registration — CASSI (L1/L2/L3-003) + CACTI (L1/L2/L3-004)",
        "",
        f"**Date:** {today}",
        f"**Network:** {meta.get('display', network)} (slot `{network}`, chainId {chain_id})",
        f"**Registered by:** {signer_addr}",
        "",
        "## Plan",
        "",
        "| artifact_id | layer | hash | parent_hash |",
        "|---|---|---|---|",
    ]
    for artifact_id, h, parent_h, layer in plan:
        lines.append(f"| {artifact_id} | {layer} | `{h}` | `{parent_h}` |")

    lines += ["", "## Results", ""]
    if all_present:
        lines.append("All 6 artifacts already registered on-chain. No transactions sent.")
    elif not results:
        lines.append("No registration transactions (dry-run or early abort).")
    else:
        lines += [
            "| artifact_id | status | tx_hash | block | Explorer |",
            "|---|---|---|---|---|",
        ]
        for r in results:
            tx = r.get("tx_hash", "—")
            block = r.get("block", "—")
            link = f"{explorer}{tx}" if explorer and tx.startswith("0x") else "—"
            lines.append(f"| {r['artifact_id']} | {r['status']} | `{tx}` | {block} | {link} |")

    lines += ["", "No private-key material appears in this file by design.", ""]
    path.write_text("\n".join(lines) + "\n")
    logger.info(f"review written to: {path}")


def run(args: argparse.Namespace) -> int:
    try:
        from web3 import Web3
        from eth_account import Account
    except ImportError:
        logger.error("web3 / eth_account not installed. pip install web3 eth_account")
        return 1

    rpc_url = os.environ.get("PWM_RPC_URL")
    if not rpc_url:
        logger.error("PWM_RPC_URL env var not set.")
        return 1

    private_key = os.environ.get("PWM_PRIVATE_KEY")
    if not private_key and not args.dry_run:
        logger.error("PWM_PRIVATE_KEY env var not set (required unless --dry-run).")
        return 1

    network = args.network
    if network not in NETWORK_META:
        logger.error(f"unsupported --network={network}. Pick from: {list(NETWORK_META)}")
        return 1

    repo_root = _repo_root()
    genesis_dir = repo_root / "pwm-team" / "pwm_product" / "genesis"
    if not genesis_dir.is_dir():
        logger.error(f"genesis dir not found: {genesis_dir}")
        return 1

    addresses = _load_addresses(repo_root)
    slot = addresses.get(network, {})
    registry_addr = slot.get("PWMRegistry")
    if not registry_addr:
        logger.error(
            f"addresses.json[{network}].PWMRegistry not set. "
            f"Run the deploy first: npx hardhat run deploy/l2.js --network {network}"
        )
        return 1
    chain_id = slot.get("chainId") or 0

    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        logger.error(f"cannot connect to RPC at {rpc_url}")
        return 1
    live_chain_id = w3.eth.chain_id
    if chain_id and live_chain_id != chain_id:
        logger.error(
            f"chainId mismatch: addresses.json[{network}].chainId={chain_id} but RPC reports {live_chain_id}. "
            f"Wrong PWM_RPC_URL?"
        )
        return 1
    logger.info(f"connected to {NETWORK_META[network]['display']} (chainId {live_chain_id}), block {w3.eth.block_number}")

    acct = Account.from_key(private_key) if private_key else None
    signer_addr = acct.address if acct else "(dry-run; no signer)"
    logger.info(f"signer: {signer_addr}")

    if acct:
        bal_eth = float(w3.from_wei(w3.eth.get_balance(acct.address), "ether"))
        logger.info(f"signer balance: {bal_eth:.6f} ETH")

    registry_abi = _load_abi(repo_root, "PWMRegistry")
    registry = w3.eth.contract(address=w3.to_checksum_address(registry_addr), abi=registry_abi)

    # Step 1: compute hashes
    logger.info("loading artifacts + computing hashes...")
    hashes: dict[str, str] = {}
    for artifact_id, rel_path, _layer in ARTIFACTS_TO_REGISTER:
        path = genesis_dir / rel_path
        try:
            obj = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"cannot load {path}: {e}")
            return 1
        h = _artifact_hash(obj, w3)
        hashes[artifact_id] = h
        logger.info(f"  {artifact_id}: {h}")

    # Step 2: plan
    ZERO = "0x" + "00" * 32
    plan: list[tuple[str, str, str, int]] = []
    for artifact_id, _, layer in ARTIFACTS_TO_REGISTER:
        parent_key = _parent_key(artifact_id)
        parent_hash = hashes[parent_key] if parent_key else ZERO
        plan.append((artifact_id, hashes[artifact_id], parent_hash, layer))

    if args.dry_run:
        logger.info("--dry-run: no transactions sent")
        _write_review(repo_root, network, plan, [], signer_addr, False, live_chain_id)
        return 0

    # Step 3: skip existing
    to_register = []
    for artifact_id, h, parent_h, layer in plan:
        try:
            exists = registry.functions.exists(bytes.fromhex(h[2:])).call()
        except Exception as e:
            logger.warning(f"exists({artifact_id}) check failed ({type(e).__name__}) — will attempt registration")
            exists = False
        if exists:
            logger.info(f"  {artifact_id}: already registered (skip)")
        else:
            to_register.append((artifact_id, h, parent_h, layer))

    if not to_register:
        logger.info("all 6 artifacts already registered")
        _write_review(repo_root, network, plan, [], signer_addr, True, live_chain_id)
        return 0

    # Step 4: send
    logger.info(f"registering {len(to_register)} artifact(s) on {NETWORK_META[network]['display']}...")
    results: list[dict] = []
    nonce = w3.eth.get_transaction_count(acct.address)
    for artifact_id, h, parent_h, layer in to_register:
        logger.info(f"  sending register({artifact_id})...")
        try:
            h_bytes = bytes.fromhex(h[2:])
            parent_bytes = bytes.fromhex(parent_h[2:])
            fn = registry.functions.register(h_bytes, parent_bytes, layer, acct.address)
            tx = fn.build_transaction({
                "from": acct.address,
                "chainId": live_chain_id,
                "nonce": nonce,
                "gas": 200000,
                "maxFeePerGas": w3.eth.gas_price * 2,
                "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
            })
            signed = acct.sign_transaction(tx)
            raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction  # type: ignore[attr-defined]
            tx_hash = w3.eth.send_raw_transaction(raw)
            tx_hex = tx_hash.hex() if isinstance(tx_hash, bytes) else str(tx_hash)
            if not tx_hex.startswith("0x"):
                tx_hex = "0x" + tx_hex
            logger.info(f"    tx sent: {tx_hex}")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            if receipt.get("status") == 0:
                logger.error(f"    tx REVERTED for {artifact_id}")
                results.append({"artifact_id": artifact_id, "hash": h, "parent_hash": parent_h,
                                "layer": layer, "tx_hash": tx_hex, "status": "reverted",
                                "block": int(receipt.get("blockNumber", 0))})
                _write_review(repo_root, network, plan, results, signer_addr, False, live_chain_id)
                return 2
            logger.info(f"    confirmed block {receipt.get('blockNumber')} (gas {receipt.get('gasUsed')})")
            results.append({"artifact_id": artifact_id, "hash": h, "parent_hash": parent_h,
                            "layer": layer, "tx_hash": tx_hex,
                            "block": int(receipt.get("blockNumber", 0)),
                            "gas_used": int(receipt.get("gasUsed", 0)),
                            "status": "success"})
            nonce += 1
        except Exception as e:
            logger.error(f"    {artifact_id} failed: {type(e).__name__}: {e}")
            results.append({"artifact_id": artifact_id, "hash": h, "parent_hash": parent_h,
                            "layer": layer, "status": "error",
                            "error": f"{type(e).__name__}: {e}"[:200]})
            _write_review(repo_root, network, plan, results, signer_addr, False, live_chain_id)
            return 3

    logger.info(f"all {len(to_register)} registrations complete")
    _write_review(repo_root, network, plan, results, signer_addr, False, live_chain_id)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Register CASSI + CACTI artifacts on a PWMRegistry deployment")
    ap.add_argument("--network", required=True, choices=sorted(NETWORK_META.keys()),
                    help="Target network (must match an addresses.json slot with PWMRegistry set)")
    ap.add_argument("--dry-run", action="store_true", help="Compute hashes + plan, do NOT send txs")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
