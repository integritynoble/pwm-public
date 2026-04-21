"""pwm-node entry point.

Dispatches subcommands implemented in pwm_node.commands.*.

Architecture: argparse top-level with one subparser per mandatory command from
the bounty spec (interfaces/bounties/03-pwm-node-cli.md). Offline commands
(benchmarks, inspect, verify) work without any chain or IPFS dependency.
Online commands (mine, submit-cert, sp register, balance) require --network
flag and a configured wallet.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pwm_node.commands import balance, benchmarks, inspect, mine, submit, verify


# Online commands — stubbed pending further sessions
_CHAIN_COMMANDS = {"sp", "stake"}


def _repo_root_default() -> Path:
    """Find the repository root by walking up from $CWD looking for pwm-team/.

    This lets ``pwm-node`` work from anywhere inside the monorepo without a
    global config file during development. In production installs, users pass
    --genesis-dir explicitly.
    """
    cur = Path.cwd().resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team" / "coordination" / "agent-coord").is_dir():
            return p
    return cur


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argparse parser."""
    default_root = _repo_root_default()
    default_genesis = default_root / "pwm-team" / "pwm_product" / "genesis"

    p = argparse.ArgumentParser(
        prog="pwm-node",
        description="PWM protocol CLI — discover benchmarks, verify solvers, mine certificates.",
    )
    p.add_argument(
        "--network",
        choices=["testnet", "mainnet", "offline"],
        default="offline",
        help="Target network (default: offline — for local verification only).",
    )
    p.add_argument(
        "--genesis-dir",
        type=Path,
        default=default_genesis,
        help=f"Path to genesis L1/L2/L3 JSON artifacts (default: {default_genesis}).",
    )
    p.add_argument("--verbose", "-v", action="count", default=0, help="-v, -vv for more log detail.")

    sub = p.add_subparsers(dest="command", required=True, metavar="<command>")

    # benchmarks — list available benchmarks (offline)
    bp = sub.add_parser("benchmarks", help="List available benchmarks.")
    bp.add_argument("--domain", help="Filter by domain (e.g. imaging, compressive).")
    bp.add_argument("--spec", help="Filter by spec ID (e.g. L2-003).")
    bp.set_defaults(handler=benchmarks.run)

    # inspect — resolve a hash/id to its artifact (offline variant reads genesis dir)
    ip = sub.add_parser(
        "inspect",
        help="Look up a principle/spec/benchmark/cert by id or hash.",
    )
    ip.add_argument("target", help="cert_hash, benchmark_id, spec_id, or principle_id.")
    ip.set_defaults(handler=inspect.run)

    # verify — run local S1-S4 check on a solver output (offline)
    vp = sub.add_parser(
        "verify",
        help="Run S1-S4 gate check on a local solver output (no chain interaction).",
    )
    vp.add_argument("benchmark_yaml", type=Path, help="Path to the benchmark spec YAML.")
    vp.add_argument("--solver-output", type=Path, help="Solver output directory to check.")
    vp.set_defaults(handler=verify.run)

    # balance — show native ETH balance (requires --network testnet/mainnet)
    balp = sub.add_parser(
        "balance",
        help="Show native ETH balance on testnet/mainnet (--network required).",
    )
    balp.add_argument("--address", help="Address to query (defaults to PWM_PRIVATE_KEY signer).")
    balp.set_defaults(handler=balance.run)

    # submit-cert — upload and submit a signed L4 certificate
    scp = sub.add_parser(
        "submit-cert",
        help="Submit a signed L4 certificate to PWMCertificate on testnet/mainnet.",
    )
    scp.add_argument("--cert", type=Path, required=True, help="Path to cert_payload JSON file.")
    scp.add_argument(
        "--ipfs-upload",
        action="store_true",
        help="Upload the cert payload to IPFS before submitting (adds ipfs_cid to payload).",
    )
    scp.add_argument(
        "--skip-ipfs-on-failure",
        action="store_true",
        help="If --ipfs-upload fails, continue submission without CID instead of aborting.",
    )
    scp.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print payload but do not broadcast the submit tx.",
    )
    scp.add_argument("--no-wait", action="store_true", help="Do not wait for tx confirmation.")
    scp.add_argument("--timeout", type=int, default=300, help="Tx wait timeout in seconds.")
    scp.add_argument("--gas", type=int, default=500000, help="Gas budget for the submit tx.")
    scp.set_defaults(handler=submit.run)

    # mine — the flagship: resolve benchmark, run solver, score, submit
    mp = sub.add_parser(
        "mine",
        help="Mine a benchmark end-to-end: resolve → solve → score → submit.",
    )
    mp.add_argument("benchmark_id", help="Benchmark to mine (e.g. L3-003 or cassi/t1_nominal).")
    mp.add_argument("--solver", type=Path, required=True, help="Path to solver .py file.")
    mp.add_argument("--work-dir", type=Path, help="Working directory for input/output (default: $CWD/pwm_work_<ts>).")
    mp.add_argument("--dry-run", action="store_true", help="Score and build cert but do not submit.")
    mp.add_argument("--timeout", type=int, default=600, help="Solver wall-clock timeout in seconds.")
    mp.set_defaults(handler=mine.run)

    # Stubs for remaining chain-dependent commands
    for cmd in ["stake", "sp"]:
        s = sub.add_parser(cmd, help=f"[Phase C stub] {cmd} — chain-dependent; next session.")
        s.add_argument("args", nargs="*")
        s.set_defaults(handler=_chain_stub)

    return p


def _chain_stub(args: argparse.Namespace) -> int:
    """Placeholder for chain-dependent commands. Returns exit code 2 (not implemented)."""
    print(
        f"[pwm-node] command '{args.command}' requires chain integration (not implemented yet). "
        f"Tracking: MVP_FIRST_STRATEGY.md Phase C.",
        file=sys.stderr,
    )
    return 2


def main(argv: list[str] | None = None) -> int:
    """Main entry point. Returns the exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args) or 0)
    except Exception as e:  # command handlers should catch their own; this is a fallback
        if args.verbose >= 1:
            raise
        print(f"[pwm-node] error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
