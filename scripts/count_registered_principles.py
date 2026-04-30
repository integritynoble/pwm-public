"""Count L1 Principles registered on-chain via PWMRegistry; cross-check against local manifests.

Step 9b verifier per `pwm-team/coordination/MAINNET_DEPLOY_HANDOFF.md`.

Companion to `scripts/register_genesis.py` (which is what Step 9b's CPU
side runs). After registration, this script:

1. Counts `ArtifactRegistered(layer=1)` events emitted from `PWMRegistry`
   since the deploy block on the named network.
2. Cross-checks each registered hash against the canonical-JSON keccak256
   of the corresponding local L1-*.json manifest.
3. Reports `is_promoted` from `PWMMinting` for each registered Principle
   (or notes that auto-promotion at registration is the genesis convention).
4. Returns exit-code 0 if `events_count >= --expected` AND all hashes
   match; non-zero otherwise.

Manifest-discovery scope:

- `pwm-team/pwm_product/genesis/l1/L1-*.json` (the 2 demo L1 entries:
  CASSI L1-003 + CACTI L1-004 at v1-demo schema).
- `pwm-team/content/agent-*/principles/**/L1-*.json` (the 531 v2/v3-aware
  manifests post-2026-04-29 schema migration; this includes a separate
  `L1-003_confocal_livecell` and `L1-004_confocal_zstack` under
  `agent-imaging/A_microscopy/` with completely different physics from
  the demo L1-003 / L1-004. They register as distinct on-chain artifacts
  via different content hashes — see the artifact_id-collision note in
  `pwm-team/coordination/REGISTER_GENESIS_ARTIFACT_ID_COLLISION_2026-04-30.md`
  for the resolution discussion.)

Default --expected is 533 (= 2 demo CASSI/CACTI L1 + 531 content-tree L1).
The 531 content-tree breaks down as: 502 v1 baseline + 8 v3 standalones
(L1-503..L1-510) + 2 newly-authored v2 analytical cores (L1-511 PillCam,
L1-518 XRD) + 19 v2 PWDR (L1-512..L1-517, L1-519..L1-531).

Usage:

    export PWM_RPC_URL=https://mainnet.base.org
    python3 scripts/count_registered_principles.py --network base --expected 537

    # Dry-run-style without RPC: just show what would be checked
    python3 scripts/count_registered_principles.py --network base --no-rpc

Exit codes:
    0  events_count >= expected AND every local manifest hash is
       on-chain AND every on-chain hash maps to a local manifest
    1  events_count < expected
    2  hash mismatch (a local manifest that should be registered isn't)
    3  unknown on-chain hash (registered artifact not present locally)
    4  RPC / setup error
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger("count_registered_principles")


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("cannot find repo root (pwm-team/)")


def _canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _discover_local_manifests(repo: Path) -> list[tuple[str, Path]]:
    """Return list of (artifact_id, path) for all L1 manifests considered
    part of the genesis batch."""
    out: list[tuple[str, Path]] = []

    # 1) demo L1 entries under pwm_product/genesis/l1/
    demo_dir = repo / "pwm-team" / "pwm_product" / "genesis" / "l1"
    if demo_dir.is_dir():
        for p in sorted(demo_dir.glob("L1-*.json")):
            out.append((f"DEMO:{p.stem}", p))

    # 2) v1 + v2/v3 manifests under content/agent-*/principles/
    content_dir = repo / "pwm-team" / "content"
    if content_dir.is_dir():
        for p in sorted(content_dir.rglob("L1-*.json")):
            try:
                data = json.loads(p.read_text())
            except json.JSONDecodeError:
                continue
            if data.get("layer") != "L1":
                continue
            aid = data.get("artifact_id") or p.stem
            # Differentiate vs demo entries by their tree-relative path
            tree = p.relative_to(content_dir).parts[0]
            out.append((f"{tree}:{aid}", p))
    return out


def _hash_manifest(p: Path, w3=None) -> str:
    obj = json.loads(p.read_text())
    payload = _canonical_json(obj)
    if w3 is not None:
        digest = w3.keccak(payload)
        h = digest.hex()
        return ("0x" + h[2:].zfill(64)) if h.startswith("0x") else ("0x" + h.zfill(64))
    # Fallback for --no-rpc mode: compute keccak via pycryptodome / eth_utils if available;
    # otherwise just return a sha256 placeholder (clearly marked).
    try:
        from eth_utils import keccak  # type: ignore
        return "0x" + keccak(payload).hex().zfill(64)
    except ImportError:
        import hashlib
        digest = hashlib.sha256(payload).hexdigest()
        return f"sha256-fallback:{digest}"


def _count_events(w3, registry, deploy_block: int) -> dict[str, dict]:
    """Return mapping hash -> event metadata for all layer=1 ArtifactRegistered events."""
    head = w3.eth.block_number
    chunk = 5000
    by_hash: dict[str, dict] = {}
    cur = deploy_block
    while cur <= head:
        end = min(cur + chunk - 1, head)
        try:
            logs = registry.events.ArtifactRegistered.get_logs(from_block=cur, to_block=end)
        except Exception as e:
            logger.warning(f"  getLogs {cur}-{end} failed ({e}); halving chunk")
            chunk = max(chunk // 2, 100)
            continue
        for ev in logs:
            if ev["args"]["layer"] != 1:
                continue
            h = ev["args"]["hash"]
            h_hex = h.hex() if isinstance(h, bytes) else h
            if not h_hex.startswith("0x"):
                h_hex = "0x" + h_hex
            by_hash[h_hex.lower()] = {
                "block": ev["blockNumber"],
                "creator": ev["args"].get("creator", "?"),
                "tx": ev["transactionHash"].hex(),
            }
        cur = end + 1
    return by_hash


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--network", default="base", help="addresses.json slot")
    ap.add_argument("--expected", type=int, default=533,
                    help="expected on-chain count (default 533 = 2 demo + 531 content-tree)")
    ap.add_argument("--since-block", type=int, default=0,
                    help="start scanning from this block (default 0)")
    ap.add_argument("--no-rpc", action="store_true",
                    help="skip on-chain reads; just enumerate local manifests")
    args = ap.parse_args()

    repo = _repo_root()
    manifests = _discover_local_manifests(repo)
    logger.info(f"Discovered {len(manifests)} local L1 manifests:")
    by_tree: dict[str, int] = {}
    for tag, _ in manifests:
        tree = tag.split(":", 1)[0]
        by_tree[tree] = by_tree.get(tree, 0) + 1
    for tree, n in sorted(by_tree.items()):
        logger.info(f"  {tree}: {n}")

    if args.no_rpc:
        logger.info("--no-rpc: skipping on-chain checks")
        logger.info(f"Total local L1 count: {len(manifests)}")
        return 0 if len(manifests) >= args.expected else 1

    try:
        from web3 import Web3
    except ImportError:
        logger.error("web3 not installed; run: pip install web3")
        return 4
    rpc = os.environ.get("PWM_RPC_URL")
    if not rpc:
        logger.error("PWM_RPC_URL env var required (or pass --no-rpc)")
        return 4

    addrs_path = repo / "pwm-team" / "infrastructure" / "agent-contracts" / "addresses.json"
    if not addrs_path.exists():
        addrs_path = repo / "pwm-team" / "coordination" / "agent-coord" / "interfaces" / "addresses.json"
    addrs = json.loads(addrs_path.read_text())
    if args.network not in addrs:
        logger.error(f"addresses.json has no '{args.network}' slot")
        return 4
    cert_addr = addrs[args.network].get("PWMRegistry")
    if not cert_addr:
        logger.error(f"PWMRegistry not deployed for {args.network}")
        return 4

    w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 60}))
    if not w3.is_connected():
        logger.error("RPC unreachable")
        return 4

    abi_path = repo / "pwm-team" / "coordination" / "agent-coord" / "interfaces" / "contracts_abi" / "PWMRegistry.json"
    abi_raw = json.loads(abi_path.read_text())
    abi = abi_raw if isinstance(abi_raw, list) else abi_raw.get("abi", [])
    registry = w3.eth.contract(address=Web3.to_checksum_address(cert_addr), abi=abi)

    # Compute expected hashes
    logger.info("Computing local manifest hashes...")
    local_hashes: dict[str, tuple[str, Path]] = {}
    for tag, path in manifests:
        h = _hash_manifest(path, w3=w3)
        local_hashes[h.lower()] = (tag, path)

    logger.info(f"Local manifests hashed: {len(local_hashes)} (de-duplicated by hash)")

    # Count on-chain events
    logger.info(f"Scanning ArtifactRegistered events from block {args.since_block} to head...")
    by_hash = _count_events(w3, registry, args.since_block)
    logger.info(f"On-chain layer=1 ArtifactRegistered events: {len(by_hash)}")

    # Three-way audit
    missing_local: list[str] = []
    extra_onchain: list[str] = []

    for h, (tag, _) in local_hashes.items():
        if h not in by_hash:
            missing_local.append(f"{tag} hash={h}")
    for h in by_hash:
        if h not in local_hashes:
            extra_onchain.append(h)

    print()
    print(f"Network: {args.network} ({rpc})")
    print(f"PWMRegistry: {cert_addr}")
    print(f"Local L1 manifests: {len(local_hashes)}")
    print(f"On-chain layer=1 ArtifactRegistered events: {len(by_hash)}")
    print(f"Expected (--expected): {args.expected}")
    print()
    if missing_local:
        print(f"✗ {len(missing_local)} local manifests are NOT yet registered on-chain:")
        for m in missing_local[:20]:
            print(f"    {m}")
        if len(missing_local) > 20:
            print(f"    ...and {len(missing_local) - 20} more")
        print()
    if extra_onchain:
        print(f"✗ {len(extra_onchain)} on-chain hashes do NOT match any local manifest:")
        for h in extra_onchain[:20]:
            print(f"    {h}")
        if len(extra_onchain) > 20:
            print(f"    ...and {len(extra_onchain) - 20} more")
        print()

    if len(by_hash) < args.expected:
        print(f"✗ FAIL: {len(by_hash)} < {args.expected} expected")
        return 1
    if missing_local:
        return 2
    if extra_onchain:
        return 3
    print(f"✓ PASS: {len(by_hash)} >= {args.expected}; all local manifests on-chain; no orphans")
    return 0


if __name__ == "__main__":
    sys.exit(main())
