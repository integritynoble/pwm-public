"""pwm-node verify — local S1-S4 gate check on a solver output.

Offline by design. Uses ``pwm_scoring.gates`` (Bounty 1 reference impl) to run
the four structural checks. Exit code 0 if all gates PASS; 4 if any FAIL.

No chain interaction. No IPFS. A user can run this before paying gas to
submit a certificate.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _load_yaml(path: Path) -> dict:
    import yaml
    return yaml.safe_load(path.read_text())


def run(args: argparse.Namespace) -> int:
    """Run S1-S4 gates on a solver output + benchmark yaml. Returns 0 pass, 4 fail."""
    bench_path: Path = args.benchmark_yaml
    if not bench_path.exists():
        print(f"[pwm-node verify] benchmark file not found: {bench_path}", file=sys.stderr)
        return 1

    try:
        from pwm_scoring.gates import run_all_gates  # type: ignore
        _have_scoring = True
    except ImportError:
        _have_scoring = False

    bench = _load_yaml(bench_path)

    if _have_scoring and not args.solver_output:
        print(
            "[pwm-node verify] --solver-output required when pwm_scoring is installed. "
            "Without it, only structural checks are performed.",
            file=sys.stderr,
        )
        _have_scoring = False

    if _have_scoring:
        try:
            verdict = run_all_gates(bench, args.solver_output)
            all_pass = all(v == "pass" for v in verdict.values())
            print(f"[pwm-node verify] {bench_path.name}: " + ", ".join(f"{k}={v.upper()}" for k, v in verdict.items()))
            return 0 if all_pass else 4
        except Exception as e:
            print(f"[pwm-node verify] scoring engine error: {e}", file=sys.stderr)
            return 5

    required = ("principle_ref", "omega", "E", "O", "epsilon_fn")
    missing = [k for k in required if k not in bench]
    if missing:
        print(f"[pwm-node verify] benchmark yaml missing required fields: {', '.join(missing)}", file=sys.stderr)
        return 4
    print(f"[pwm-node verify] {bench_path.name}: structural checks PASS (install pwm-scoring for full S1-S4)")
    return 0
