"""Minimal demo solver for pwm-node mine.

Writes a deterministic output file that downstream scoring can consume.
This exists to exercise the CLI's end-to-end flow; real solvers will
replace this with an actual reconstruction algorithm (e.g., GAP-TV for
CASSI).

Contract (matches pwm-node mine's subprocess call):
    python demo_solver.py --input <input_dir> --output <output_dir>

Inputs: files the benchmark placed in input_dir. This solver ignores them
and writes a fixed output.

Outputs: writes output/solution.npz plus output/meta.json so the scoring
engine has something structured to read.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility.")
    args = ap.parse_args(argv)

    args.output.mkdir(parents=True, exist_ok=True)

    # Try to produce a numpy output if numpy is available; else just meta.
    try:
        import numpy as np
        rng = np.random.default_rng(args.seed)
        # A trivial 64x64 "reconstruction" — shape chosen to be tiny for CI
        data = rng.standard_normal((64, 64)).astype("float32")
        np.savez_compressed(args.output / "solution.npz", data=data)
        shape = list(data.shape)
        dtype = str(data.dtype)
    except ImportError:
        shape = [0]
        dtype = "unavailable"
        # Write an empty placeholder so the file exists for scoring
        (args.output / "solution.npz").write_bytes(b"")

    (args.output / "meta.json").write_text(
        json.dumps(
            {
                "solver": "demo_solver",
                "version": "1.0",
                "seed": args.seed,
                "output_shape": shape,
                "output_dtype": dtype,
                "note": "Demo solver for pwm-node CLI e2e test. Replace with a real reconstruction.",
            },
            indent=2,
            sort_keys=True,
        )
    )
    print(f"[demo_solver] wrote {args.output / 'solution.npz'} and meta.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
