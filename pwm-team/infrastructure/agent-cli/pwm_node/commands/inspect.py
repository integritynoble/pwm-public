"""pwm-node inspect — resolve a hash/id to its artifact (offline).

Offline variant: matches against L1/L2/L3 JSONs in ``--genesis-dir`` by
``artifact_id`` (L1-NNN / L2-NNN / L3-NNN). Chain-connected variant (next
session) will also accept cert_hash and query PWMRegistry via chain.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_layer(genesis_dir: Path, layer: str) -> list[dict]:
    """Read all artifacts for a given layer."""
    d = genesis_dir / layer.lower()
    if not d.is_dir():
        return []
    out = []
    for f in sorted(d.glob(f"{layer}-*.json")):
        try:
            out.append(json.loads(f.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return out


def _find_by_id(genesis_dir: Path, target: str) -> tuple[dict, str] | None:
    """Return (artifact, layer) for the first artifact with artifact_id == target."""
    for layer in ("L1", "L2", "L3"):
        for a in _load_layer(genesis_dir, layer):
            if a.get("artifact_id") == target:
                return a, layer
    return None


def run(args: argparse.Namespace) -> int:
    """Resolve and print an artifact. Returns 0 on hit, 3 on miss."""
    target = args.target
    hit = _find_by_id(args.genesis_dir, target)
    if hit is None:
        print(
            f"[pwm-node inspect] no offline match for '{target}'. "
            f"If this is a cert_hash, retry with --network testnet (not yet implemented in Phase C-stub).",
        )
        return 3

    artifact, layer = hit
    title = artifact.get("title", "?")
    aid = artifact.get("artifact_id", "?")
    slug = artifact.get("display_slug")
    # Title-first inline header (per customer-guide plan task 2.8); the
    # labelled lines below are kept for parser-friendliness.
    print(f"{title} ({aid})")
    if slug:
        print(f"  slug: {slug}")
    print(f"=== {aid} ({layer.upper()}) ===")
    print(f"Title:        {title}")
    print(f"Domain:       {artifact.get('domain', '?')}")
    if artifact.get("sub_domain"):
        print(f"Sub-domain:   {artifact.get('sub_domain')}")
    print(f"Difficulty:   {artifact.get('difficulty_tier', '?')} (δ={artifact.get('difficulty_delta', '?')})")
    print(f"Verification: {artifact.get('verification_status', 'draft')}")

    if artifact.get("verified_by"):
        print(f"Verified by:  {', '.join(artifact['verified_by'])}")
    if artifact.get("verification_date"):
        print(f"Verified on:  {artifact['verification_date']}")

    if layer == "L1":
        e = artifact.get("E", {})
        print(f"Forward:      {e.get('forward_model', '?')}")
        g = artifact.get("G", {})
        print(f"DAG:          {g.get('dag', '?')}")
        print(f"L_DAG:        {g.get('L_DAG', '?')}")
        w = artifact.get("W", {})
        print(f"κ_sys:        {w.get('condition_number_kappa', '?')}")
        print(f"κ_eff:        {w.get('condition_number_effective', '?')}")
        primitives = artifact.get("physics_fingerprint", {}).get("primitives", [])
        if primitives:
            print(f"Primitives:   {', '.join(primitives)}")

    return 0
