"""pwm-node benchmarks — list available benchmarks from local genesis/ dir.

Offline by design. Reads L1/L2/L3 JSON artifacts from ``--genesis-dir`` and
prints a concise table. In a chain-connected version (next session), the same
command will overlay on-chain state (registered/promoted/active ρ values).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_l1_artifacts(genesis_dir: Path) -> list[dict]:
    """Read every L1-*.json in genesis_dir/l1/."""
    l1_dir = genesis_dir / "l1"
    if not l1_dir.is_dir():
        return []
    out = []
    for f in sorted(l1_dir.glob("L1-*.json")):
        try:
            out.append(json.loads(f.read_text()))
        except (json.JSONDecodeError, OSError):
            continue  # skip corrupt files in listing; users can inspect individually
    return out


def run(args: argparse.Namespace) -> int:
    """List benchmarks. Returns 0 on success."""
    arts = _load_l1_artifacts(args.genesis_dir)
    if not arts:
        print(
            f"[pwm-node benchmarks] no L1 artifacts found under {args.genesis_dir}/l1/. "
            "Pass --genesis-dir to point elsewhere.",
            file=None,
        )
        return 0

    if args.domain:
        needle = args.domain.lower()
        arts = [a for a in arts if needle in a.get("domain", "").lower() or needle in a.get("sub_domain", "").lower()]

    if args.spec:
        arts = [a for a in arts if a.get("artifact_id") == args.spec or f"L2-{a.get('principle_number')}" == args.spec]

    if not arts:
        print("[pwm-node benchmarks] filter matched zero artifacts.")
        return 0

    # Print concise table
    header = f"{'ID':<10} {'Domain':<22} {'Tier':<10} {'Title':<52} {'Verification':<20}"
    print(header)
    print("-" * len(header))
    for a in arts:
        aid = a.get("artifact_id", "?")
        dom = (a.get("domain", "?"))[:22]
        tier = a.get("difficulty_tier", "?")[:10]
        title = (a.get("title", "?"))[:52]
        verif = a.get("verification_status", "draft")[:20]
        print(f"{aid:<10} {dom:<22} {tier:<10} {title:<52} {verif:<20}")

    return 0
