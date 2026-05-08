"""pwm-node entry point.

Dispatches subcommands implemented in pwm_node.commands.*.

Architecture: argparse top-level with one subparser per mandatory command from
the bounty spec (`pwm-team/bounties/03-pwm-node-cli.md`). Offline commands
(benchmarks, inspect, verify) work without any chain or IPFS dependency.
Online commands (mine, submit-cert, sp register, balance) require --network
flag and a configured wallet.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pwm_node.commands import balance, benchmarks, inspect, match, mine, sp, stake, submit, verify


# All commands are now live. _CHAIN_COMMANDS kept for backward compat.
_CHAIN_COMMANDS: set[str] = set()


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

    from pwm_node import __version__

    p = argparse.ArgumentParser(
        prog="pwm-node",
        description="PWM protocol CLI — discover benchmarks, verify solvers, mine certificates.",
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"pwm-node {__version__}",
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

    # benchmarks — list available L3 benchmarks (offline). Walks
    # genesis/l3/ and prints L3-flavoured columns. Per smoke-test F1.
    bp = sub.add_parser(
        "benchmarks",
        help="List available L3 benchmarks (parent L1/L2, rho, T1 epsilon, T1 baseline).",
    )
    bp.add_argument("--domain", help="Filter by title/slug substring (e.g. cassi, compressive).")
    bp.add_argument("--spec", help="Filter by parent L2 ID (e.g. L2-003).")
    bp.set_defaults(handler=benchmarks._run_benchmarks)

    # principles — list available L1 Principles (offline). Same behaviour
    # the historical `benchmarks` command had pre-2026-05-04, just under
    # the more accurate name. Per smoke-test F1.
    pp = sub.add_parser(
        "principles",
        help="List available L1 Principles (domain, difficulty, verification).",
    )
    pp.add_argument("--domain", help="Filter by domain (e.g. imaging, compressive).")
    pp.add_argument("--spec", help="Filter by spec ID (e.g. L2-003).")
    pp.set_defaults(handler=benchmarks._run_principles)

    # inspect — resolve a hash/id to its artifact (offline variant reads genesis dir)
    ip = sub.add_parser(
        "inspect",
        help="Look up a principle/spec/benchmark/cert by id, slug, or hash.",
    )
    ip.add_argument(
        "target",
        help="Artifact id (L1-003, L2-003, L3-003), slug (cassi, cacti, spc), or cert_hash.",
    )
    ip.add_argument(
        "--layer",
        choices=["L1", "L2", "L3", "l1", "l2", "l3", "1", "2", "3"],
        default=None,
        help="When the target is a slug that matches multiple layers (e.g. 'cassi' "
             "matches L1-003 + L2-003 + L3-003), pick which layer to return. "
             "Default: L1 (the Principle), matching the web /principles/<slug> route.",
    )
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

    # match — faceted (LLM-free) benchmark matcher (reference impl)
    matp = sub.add_parser(
        "match",
        help="Match a free-text prompt or structured filters to benchmarks (faceted, no LLM).",
    )
    matp.add_argument("--prompt", help="Free-text description of your data / problem.")
    # Also accept a positional form: `pwm-node match "compressive sensing"`
    # or unquoted `pwm-node match compressive sensing`. Joined with a space
    # and used only when --prompt is not given.
    matp.add_argument(
        "prompt_words",
        nargs="*",
        metavar="PROMPT",
        help="Free-text description as a positional argument (alternative to --prompt).",
    )
    matp.add_argument("--domain", help="L1 domain filter (e.g. imaging, spectroscopy).")
    matp.add_argument("--modality", help="Benchmark_type filter (e.g. snapshot, tomography).")
    matp.add_argument("--h", type=int, help="Preferred image height.")
    matp.add_argument("--w", type=int, help="Preferred image width.")
    matp.add_argument("--noise", type=float,
                      help="Max noise level you need the benchmark to tolerate.")
    matp.add_argument("--json", action="store_true",
                      help="Emit JSON output (matches 08-llm-matcher.md wire schema).")
    matp.add_argument(
        "--cards-dir",
        type=Path,
        default=default_root / "pwm-team" / "pwm_product" / "benchmark_cards",
        help=f"Benchmark-cards directory (default: {default_root}/pwm-team/pwm_product/benchmark_cards).",
    )
    matp.set_defaults(handler=match.run)

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
    mp.add_argument(
        "--sp-wallet",
        dest="sp_wallet",
        help="Override the SP/CP/creator wallet used in the cert (default: PWM_PRIVATE_KEY signer, else 0x00…00).",
    )
    mp.add_argument(
        "--share-ratio-p",
        dest="share_ratio_p",
        type=int,
        default=5000,
        help="SP share p × 10000. Range [0, 10000]. Default 5000 (p=0.50).",
    )
    mp.set_defaults(handler=mine.run)

    # stake — view required / stake on principle|spec|benchmark
    stp = sub.add_parser(
        "stake",
        help="Show required stake or stake on a principle/spec/benchmark artifact.",
    )
    stake_sub = stp.add_subparsers(dest="stake_sub", required=True, metavar="<subcommand>")
    # stake quote [--layer N]
    q = stake_sub.add_parser("quote", help="Print required stake (in ETH) per layer.")
    q.add_argument("--layer", type=int, choices=[0, 1, 2], help="Limit to one layer (0=principle,1=spec,2=benchmark).")
    # stake principle|spec|benchmark <artifact_hash>
    for layer_name in ("principle", "spec", "benchmark"):
        sp_ = stake_sub.add_parser(layer_name, help=f"Stake on a {layer_name} artifact.")
        sp_.add_argument("artifact_hash", help="32-byte artifact hash (0x-prefixed or hex).")
        sp_.add_argument("--dry-run", action="store_true", help="Print plan; do not broadcast.")
        sp_.add_argument("--no-wait", action="store_true", help="Do not wait for tx confirmation.")
        sp_.add_argument("--timeout", type=int, default=300, help="Tx wait timeout in seconds.")
        sp_.add_argument("--gas", type=int, default=200000, help="Gas budget.")
    stp.set_defaults(handler=stake.run)

    # sp — declare SP compute manifest (local config, not a chain call)
    spp = sub.add_parser(
        "sp",
        help="Solution Provider config: register / show / remove.",
    )
    sp_sub = spp.add_subparsers(dest="sp_sub", required=True, metavar="<subcommand>")
    reg = sp_sub.add_parser("register", help="Declare your compute manifest.")
    reg.add_argument("--entry-point", required=True, help="Path to your solver .py file.")
    reg.add_argument("--share-ratio", type=float, required=True, help="Your share p ∈ [0.10, 0.90].")
    reg.add_argument("--min-vram-gb", type=int, default=0, help="Minimum GPU VRAM required (GB).")
    reg.add_argument("--recommended-vram-gb", type=int, help="Recommended VRAM (GB).")
    reg.add_argument("--cpu-only", action="store_true", help="Solver runs on CPU only (no GPU).")
    reg.add_argument("--min-ram-gb", type=int, help="Minimum system RAM (GB).")
    reg.add_argument(
        "--framework",
        choices=["pytorch", "jax", "numpy", "tensorflow", "classical"],
        help="Runtime framework.",
    )
    reg.add_argument("--expected-runtime-s", type=int, help="Expected solver runtime per instance.")
    reg.add_argument("--precision", choices=["float32", "float16", "bfloat16"], help="Numeric precision.")
    reg.add_argument("--output", help="Custom output path (default: ~/.pwm-node/sp_manifest.json).")
    spp.set_defaults(handler=sp.run)

    return p


def _chain_stub(args: argparse.Namespace) -> int:
    """Placeholder for chain-dependent commands. Returns exit code 2 (not implemented)."""
    print(
        f"[pwm-node] command '{args.command}' requires chain integration (not implemented yet). "
        f"Tracking: MVP_FIRST_STRATEGY.md Phase C.",
        file=sys.stderr,
    )
    return 2


def _ensure_utf8_stdio() -> None:
    """Reconfigure sys.stdout / sys.stderr to UTF-8 if the terminal default
    can't handle non-Latin-1 characters (e.g. Greek letters in error labels,
    em-dashes in match output).

    Per smoke-test finding F2 (PWM_PUBLIC_REPO_SMOKE_TEST_RESULTS_2026-05-03.md):
    Windows shells default to cp1252/charmap, which crashes on output like
    "(δ=3)". The agent-cli CLAUDE.md requires "Works on Linux, macOS,
    Windows" — this shim is what makes the contract hold.

    `errors='replace'` keeps the program running if a truly unencodable
    glyph slips through, rather than crashing on it.
    """
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None:
            continue
        encoding = getattr(stream, "encoding", None) or ""
        if encoding.lower().replace("-", "") == "utf8":
            continue
        # Python 3.7+ has sys.stdout.reconfigure on TextIOWrapper.
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
                continue
            except Exception:
                pass
        # Fallback: replace with a TextIOWrapper around the underlying buffer.
        buf = getattr(stream, "buffer", None)
        if buf is not None:
            try:
                import io
                setattr(sys, name, io.TextIOWrapper(
                    buf, encoding="utf-8", errors="replace", line_buffering=True))
            except Exception:
                pass


def main(argv: list[str] | None = None) -> int:
    """Main entry point. Returns the exit code."""
    _ensure_utf8_stdio()
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
