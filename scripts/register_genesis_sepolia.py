"""Register CASSI (L1/L2/L3-003) + CACTI (L1/L2/L3-004) on PWMRegistry (Sepolia).

This script unblocks Phase C and Phase D live acceptance per
``DIRECTOR_ACTION_CHECKLIST.md §0.5``. Without these 6 artifacts registered
on-chain, `pwm-node mine L3-003` reverts at the certificate-submission step
(PWMCertificate verifies the h_p / h_s / h_b hashes exist in PWMRegistry).

## Prerequisites

    export PWM_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/<your-alchemy-key>
    export PWM_PRIVATE_KEY=0x<64-hex-testnet-key>

The wallet must hold ≥ 0.01 ETH on Sepolia for gas (6 registrations +
buffer).

## Usage

    python3 scripts/register_genesis_sepolia.py            # live
    python3 scripts/register_genesis_sepolia.py --dry-run  # preview only

## Safety

- ``PWM_PRIVATE_KEY`` is read only from the environment. It is **never**
  logged, printed, included in exceptions, or written to the review file.
- Script checks ``PWMRegistry.exists(hash)`` before each registration and
  skips artifacts already on-chain. Idempotent — safe to re-run.
- Each tx is sent with an explicit nonce + gas price; a failure in the
  middle of 6 txs leaves a clean state for retry.
- Writes a review file at
  ``pwm-team/coordination/agent-coord/reviews/genesis_registration_<YYYY-MM-DD>.md``
  containing only: artifact_id, hash, parent_hash, layer, tx_hash,
  Etherscan URL, block number. No key material ever reaches disk.

## Hash convention

Each artifact's on-chain hash = ``keccak256(canonical_json_bytes)``,
where ``canonical_json_bytes`` is the JSON serialized with
``sort_keys=True`` and ``separators=(',', ':')``. This matches the EVM
bytes32 content-address convention used throughout the PWM contracts.

## Parent chain (from ``MVP_FIRST_STRATEGY.md §Phase E``)

- L1 → parent = 0x0000...0000 (32 zero bytes; principle roots have no parent)
- L2 → parent = L1's computed hash
- L3 → parent = L2's computed hash

This matches the L1→L2→L3 hash chain documented in
``cassi.md §Complete Hash Chain``.
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


# ───── artifacts to register ─────

# (artifact_id, json_path_suffix, layer)
# layer: 0=principle, 1=spec, 2=benchmark per PWM conventions
ARTIFACTS_TO_REGISTER = [
    ("L1-003", "l1/L1-003.json", 0),
    ("L2-003", "l2/L2-003.json", 1),
    ("L3-003", "l3/L3-003.json", 2),
    ("L1-004", "l1/L1-004.json", 0),
    ("L2-004", "l2/L2-004.json", 1),
    ("L3-004", "l3/L3-004.json", 2),
]


# Parent dependency: L2-NNN's parent is L1-NNN's hash; L3-NNN's parent is L2-NNN's.
def _parent_key(artifact_id: str) -> str | None:
    """Return the artifact_id whose hash is this artifact's parent, or None for L1."""
    layer = artifact_id.split("-")[0]  # L1 / L2 / L3
    num = artifact_id.split("-")[1]    # 003 / 004
    if layer == "L1":
        return None
    if layer == "L2":
        return f"L1-{num}"
    if layer == "L3":
        return f"L2-{num}"
    raise ValueError(f"unknown artifact_id format: {artifact_id}")


# ───── helpers ─────


def _repo_root() -> Path:
    """Walk up from this file to find the repo root (contains pwm-team/)."""
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("Cannot find repo root (pwm-team/) from this script's location")


def _load_addresses(repo_root: Path) -> dict:
    path = repo_root / "pwm-team" / "coordination" / "agent-coord" / "interfaces" / "addresses.json"
    return json.loads(path.read_text())


def _load_abi(repo_root: Path, contract_name: str) -> list:
    path = repo_root / "pwm-team" / "coordination" / "agent-coord" / "interfaces" / "contracts_abi" / f"{contract_name}.json"
    raw = json.loads(path.read_text())
    return raw if isinstance(raw, list) else raw.get("abi", [])


def _canonical_json(obj: Any) -> bytes:
    """Stable-serialize a JSON-able object to bytes (sorted keys, compact separators)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _artifact_hash(artifact_obj: dict, w3) -> str:
    """keccak256(canonical_json(obj)) as a 0x-prefixed hex string."""
    return "0x" + w3.keccak(_canonical_json(artifact_obj)).hex().lstrip("0x")


# ───── main registration routine ─────


def run(args: argparse.Namespace) -> int:
    try:
        from web3 import Web3
        from eth_account import Account
    except ImportError as e:
        logger.error("web3 / eth_account not installed. Run: pip install web3 eth_account")
        return 1

    rpc_url = os.environ.get("PWM_RPC_URL")
    if not rpc_url:
        logger.error("PWM_RPC_URL env var not set. Use an Alchemy/Infura endpoint for Sepolia.")
        return 1

    private_key = os.environ.get("PWM_PRIVATE_KEY")
    if not private_key and not args.dry_run:
        logger.error("PWM_PRIVATE_KEY env var not set (required unless --dry-run).")
        return 1

    repo_root = _repo_root()
    genesis_dir = repo_root / "pwm-team" / "pwm_product" / "genesis"
    if not genesis_dir.is_dir():
        logger.error(f"genesis dir not found: {genesis_dir}")
        return 1

    addresses = _load_addresses(repo_root)
    testnet = addresses.get("testnet", {})
    registry_addr = testnet.get("PWMRegistry")
    if not registry_addr:
        logger.error("PWMRegistry address not in addresses.json[testnet]")
        return 1
    chain_id = testnet.get("chainId", 11155111)

    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        logger.error(f"cannot connect to RPC at {rpc_url}")
        return 1
    logger.info(f"connected to Sepolia (chainId {chain_id}), block {w3.eth.block_number}")

    # Account (never log this!)
    acct = Account.from_key(private_key) if private_key else None
    signer_addr = acct.address if acct else "(dry-run; no signer)"
    logger.info(f"signer: {signer_addr}")

    if acct:
        bal_wei = w3.eth.get_balance(acct.address)
        bal_eth = float(w3.from_wei(bal_wei, "ether"))
        logger.info(f"signer balance: {bal_eth:.6f} ETH")
        if bal_eth < 0.005:
            logger.warning(f"balance low ({bal_eth:.4f} ETH); may run out during 6 txs. Fund from faucet.")

    # Contract
    registry_abi = _load_abi(repo_root, "PWMRegistry")
    registry = w3.eth.contract(address=w3.to_checksum_address(registry_addr), abi=registry_abi)

    # Step 1: compute hashes for all 6 artifacts (needed for parent-chain)
    logger.info("loading artifact JSONs + computing hashes...")
    hashes: dict[str, str] = {}
    artifacts: dict[str, dict] = {}
    for artifact_id, rel_path, layer in ARTIFACTS_TO_REGISTER:
        path = genesis_dir / rel_path
        try:
            obj = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"cannot load {path}: {e}")
            return 1
        h = _artifact_hash(obj, w3)
        hashes[artifact_id] = h
        artifacts[artifact_id] = obj
        logger.info(f"  {artifact_id}: hash = {h}")

    # Step 2: registration plan
    ZERO = "0x" + "00" * 32
    plan: list[tuple[str, str, str, int]] = []  # (artifact_id, hash, parent_hash, layer)
    for artifact_id, _, layer in ARTIFACTS_TO_REGISTER:
        parent_key = _parent_key(artifact_id)
        parent_hash = hashes[parent_key] if parent_key else ZERO
        plan.append((artifact_id, hashes[artifact_id], parent_hash, layer))

    logger.info("registration plan:")
    for artifact_id, h, parent_h, layer in plan:
        logger.info(f"  {artifact_id} (layer={layer}) hash={h} parent={parent_h}")

    if args.dry_run:
        logger.info("--dry-run: no transactions sent")
        return 0

    # Step 3: skip already-registered
    to_register = []
    for artifact_id, h, parent_h, layer in plan:
        try:
            exists = registry.functions.exists(h).call()
        except Exception as e:
            logger.warning(f"exists({artifact_id}) check failed: {e} — will attempt registration")
            exists = False
        if exists:
            logger.info(f"  {artifact_id}: already registered on-chain (skip)")
        else:
            to_register.append((artifact_id, h, parent_h, layer))

    if not to_register:
        logger.info("all 6 artifacts already registered — nothing to do")
        _write_review(repo_root, plan, [], signer_addr, all_present=True)
        return 0

    # Step 4: send txs sequentially
    logger.info(f"registering {len(to_register)} artifact(s)...")
    results: list[dict] = []
    nonce = w3.eth.get_transaction_count(acct.address)

    for artifact_id, h, parent_h, layer in to_register:
        logger.info(f"  sending register({artifact_id})...")
        try:
            fn = registry.functions.register(h, parent_h, layer, acct.address)
            tx = fn.build_transaction({
                "from": acct.address,
                "chainId": chain_id,
                "nonce": nonce,
                "gas": 200000,
                "maxFeePerGas": w3.eth.gas_price * 2,
                "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
            })
            signed = acct.sign_transaction(tx)
            raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction  # type: ignore[attr-defined]
            tx_hash = w3.eth.send_raw_transaction(raw)
            tx_hash_hex = tx_hash.hex() if isinstance(tx_hash, bytes) else str(tx_hash)
            if not tx_hash_hex.startswith("0x"):
                tx_hash_hex = "0x" + tx_hash_hex

            logger.info(f"    tx sent: {tx_hash_hex}")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            if receipt.get("status") == 0:
                logger.error(f"    tx REVERTED on-chain for {artifact_id}")
                results.append({
                    "artifact_id": artifact_id, "hash": h, "parent_hash": parent_h,
                    "layer": layer, "tx_hash": tx_hash_hex, "status": "reverted",
                    "block": int(receipt.get("blockNumber", 0)),
                })
                return 2  # abort on revert; user re-runs after diagnosing
            logger.info(f"    confirmed in block {receipt.get('blockNumber')} (gas {receipt.get('gasUsed')})")
            results.append({
                "artifact_id": artifact_id, "hash": h, "parent_hash": parent_h,
                "layer": layer, "tx_hash": tx_hash_hex,
                "block": int(receipt.get("blockNumber", 0)),
                "gas_used": int(receipt.get("gasUsed", 0)),
                "status": "success",
            })
            nonce += 1
        except Exception as e:
            # NB: NOT logging any account details here
            logger.error(f"    registration of {artifact_id} failed: {type(e).__name__}: {e}")
            results.append({
                "artifact_id": artifact_id, "hash": h, "parent_hash": parent_h,
                "layer": layer, "status": "error", "error": f"{type(e).__name__}: {e}"[:200],
            })
            return 3

    logger.info(f"all {len(to_register)} registrations complete")
    _write_review(repo_root, plan, results, signer_addr, all_present=False)
    return 0


def _write_review(repo_root: Path, plan: list, results: list, signer_addr: str, all_present: bool):
    """Write a review file documenting the registration. Never contains key material."""
    review_dir = repo_root / "pwm-team" / "coordination" / "agent-coord" / "reviews"
    review_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    path = review_dir / f"genesis_registration_{today}.md"

    lines = [
        f"# Genesis Registration — CASSI (L1/L2/L3-003) + CACTI (L1/L2/L3-004)",
        "",
        f"**Date:** {today}",
        f"**Registered by:** {signer_addr}",
        f"**Network:** Sepolia (chainId 11155111)",
        "",
        "## Registration plan",
        "",
        "| artifact_id | layer | hash | parent_hash |",
        "|---|---|---|---|",
    ]
    for artifact_id, h, parent_h, layer in plan:
        lines.append(f"| {artifact_id} | {layer} | `{h}` | `{parent_h}` |")

    lines += ["", "## Results", ""]
    if all_present:
        lines.append("All 6 artifacts were already registered on-chain at script invocation. No transactions sent.")
    elif not results:
        lines.append("No registration transactions recorded — likely a dry-run or early abort.")
    else:
        lines += [
            "| artifact_id | status | tx_hash | block | Etherscan |",
            "|---|---|---|---|---|",
        ]
        for r in results:
            tx = r.get("tx_hash", "—")
            block = r.get("block", "—")
            etherscan = f"https://sepolia.etherscan.io/tx/{tx}" if tx.startswith("0x") else "—"
            lines.append(f"| {r['artifact_id']} | {r['status']} | `{tx}` | {block} | {etherscan} |")

    lines += [
        "",
        "## Next steps",
        "",
        "- [ ] Director updates `progress.md` with `GENESIS_REGISTERED = true` signal",
        "- [ ] Phase C acceptance: run `pwm-node --network testnet mine L3-003 --solver examples/demo_solver.py`",
        "- [ ] Phase D acceptance: start miner + run 100-job continuous test",
        "",
        "No private-key material appears in this file by design.",
    ]
    path.write_text("\n".join(lines) + "\n")
    logger.info(f"review written to: {path}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Register CASSI + CACTI artifacts on Sepolia PWMRegistry")
    ap.add_argument("--dry-run", action="store_true", help="Compute hashes + plan but do NOT send txs")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
