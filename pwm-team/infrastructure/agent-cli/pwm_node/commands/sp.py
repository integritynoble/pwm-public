"""pwm-node sp register — declare your Solution Provider compute manifest.

There is no dedicated on-chain SP-registration contract method in the current
deployment. Instead, the "SP identity" is declared via a local
compute_manifest file that pwm-node picks up when you submit certificates.
This file declares the hardware requirements CPs (Compute Providers) must
meet to run your solver, plus your SP share ratio p ∈ [0.10, 0.90].

Storage:
  - Default: ~/.pwm-node/sp_manifest.json
  - Override with --output <path>

Usage:
  pwm-node sp register \\
    --entry-point /path/to/solve.py \\
    --share-ratio 0.5 \\
    --min-vram-gb 4 \\
    --framework pytorch
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def _default_manifest_path() -> Path:
    return Path(os.environ.get("HOME", ".")) / ".pwm-node" / "sp_manifest.json"


def run(args: argparse.Namespace) -> int:
    """Write a compute_manifest to disk. Returns 0 on success."""
    if args.sp_sub != "register":
        print(f"[pwm-node sp] unknown sub-command: {args.sp_sub}")
        return 1

    # Validate share_ratio
    p = float(args.share_ratio)
    if not (0.10 <= p <= 0.90):
        print(f"[pwm-node sp register] --share-ratio must be in [0.10, 0.90], got {p}")
        return 1

    # Validate entry-point path
    entry = Path(args.entry_point)
    if not entry.is_file():
        print(f"[pwm-node sp register] --entry-point file not found: {entry}")
        return 1

    # Validate framework
    allowed = {"pytorch", "jax", "numpy", "tensorflow", "classical"}
    if args.framework and args.framework not in allowed:
        print(
            f"[pwm-node sp register] --framework must be one of {sorted(allowed)}, "
            f"got {args.framework!r}"
        )
        return 1

    manifest = {
        "entry_point": str(entry.resolve()),
        "share_ratio_p": round(p, 4),
        "min_vram_gb": int(args.min_vram_gb) if args.min_vram_gb is not None else 0,
        "recommended_vram_gb": int(args.recommended_vram_gb)
        if args.recommended_vram_gb is not None
        else int(args.min_vram_gb or 0),
        "cpu_only": bool(args.cpu_only),
        "min_ram_gb": int(args.min_ram_gb) if args.min_ram_gb is not None else 4,
        "framework": args.framework or "classical",
        "expected_runtime_s": int(args.expected_runtime_s)
        if args.expected_runtime_s is not None
        else 60,
        "precision": args.precision or "float32",
        "ipfs_cid": None,  # populated at submit time if --ipfs-upload
    }

    out_path = Path(args.output) if args.output else _default_manifest_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))

    print(f"[pwm-node sp register] compute manifest written to: {out_path}")
    print(f"  entry_point:      {manifest['entry_point']}")
    print(f"  share_ratio_p:    {manifest['share_ratio_p']}  (SP {int(p * 55)}% / CP {int((1 - p) * 55)}%)")
    print(f"  min_vram_gb:      {manifest['min_vram_gb']}")
    print(f"  framework:        {manifest['framework']}")
    print(f"  expected_runtime_s: {manifest['expected_runtime_s']}")
    print(
        "\nThis manifest is embedded in cert payloads automatically by "
        "`pwm-node submit-cert --include-manifest`."
    )
    return 0
