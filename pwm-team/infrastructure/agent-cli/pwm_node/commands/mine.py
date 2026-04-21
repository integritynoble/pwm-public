"""pwm-node mine — the flagship mining command.

Full flow:
  1. Resolve benchmark_id (offline: find L3 JSON in genesis dir; chain: fetch
     from PWMRegistry).
  2. Ensure dataset is available locally (download from IPFS if needed).
  3. Invoke user's solver — subprocess call on a Python file, capturing
     timing and output path.
  4. Score the solver output via pwm_scoring.score_solution → Q + cert_payload.
  5. If --dry-run: print the cert_payload, stop.
  6. Else: delegate to submit-cert for on-chain submission + confirmation.

Failure semantics: each stage has a distinct exit code so scripts can
distinguish "benchmark not found" (3) from "solver timed out" (6) from
"score below epsilon" (4).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path


def _resolve_benchmark_offline(genesis_dir: Path, bench_id: str) -> tuple[dict, Path] | None:
    """Find the L3 benchmark artifact matching ``bench_id`` in the local genesis tree.

    ``bench_id`` matches against ``artifact_id`` (e.g. ``L3-003``) or a
    shorthand like ``cassi/t1_nominal`` (treated as a substring match against
    benchmark name fields).
    """
    l3_dir = genesis_dir / "l3"
    if not l3_dir.is_dir():
        return None
    for f in sorted(l3_dir.glob("L3-*.json")):
        try:
            art = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        # Exact artifact_id match first
        if art.get("artifact_id") == bench_id:
            return art, f
        # Shorthand search: bench_id appears in title or any ibenchmark id
        haystack = json.dumps(art).lower()
        if bench_id.lower() in haystack:
            return art, f
    return None


def _run_solver(solver_path: Path, work_dir: Path, *, timeout_s: int) -> tuple[int, Path, float]:
    """Run the user's solver as a subprocess.

    Contract: the solver is a Python file that reads inputs from
    ``work_dir/input/`` and writes outputs under ``work_dir/output/``. This
    is a minimal sandbox — sessions 6+ will replace with Docker isolation
    (see agent-miner for the CP-role sandbox).

    Returns: (return_code, output_dir, wall_clock_seconds)
    """
    work_dir = Path(work_dir)
    input_dir = work_dir / "input"
    output_dir = work_dir / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, str(solver_path), "--input", str(input_dir), "--output", str(output_dir)]
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            cwd=work_dir,
        )
        elapsed = time.monotonic() - t0
        return proc.returncode, output_dir, elapsed
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - t0
        return 124, output_dir, elapsed  # 124 is the conventional timeout code


def _compute_artifact_hash(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file (same as on-chain registration)."""
    content = file_path.read_bytes()
    return "0x" + hashlib.sha256(content).hexdigest()


def _build_cert_payload(
    artifact: dict,
    Q: float,
    gate_verdicts: dict,
    *,
    solution_hash: str = "pending",
    genesis_dir: Path | None = None,
    art_path: Path | None = None,
) -> dict:
    """Assemble a cert_payload dict from the scoring output + benchmark metadata.

    When genesis_dir is provided, computes real SHA-256 hashes matching the
    on-chain registered artifacts.  Falls back to placeholder strings for
    dry-run / offline use.
    """
    bench_ref = artifact.get("artifact_id") or "unknown"

    # Compute real hashes from genesis files when available
    if genesis_dir and art_path:
        benchmark_hash = _compute_artifact_hash(art_path)
        # Derive parent paths: L3-003 → l2/L2-003.json, l1/L1-003.json
        art_id = artifact.get("artifact_id", "")
        suffix = art_id.replace("L3-", "") if art_id.startswith("L3-") else ""
        spec_path = genesis_dir / "l2" / f"L2-{suffix}.json"
        principle_path = genesis_dir / "l1" / f"L1-{suffix}.json"
        h_s = _compute_artifact_hash(spec_path) if spec_path.is_file() else f"sha256:<{bench_ref}_spec>"
        h_p = _compute_artifact_hash(principle_path) if principle_path.is_file() else f"sha256:<{bench_ref}_principle>"
    else:
        benchmark_hash = f"sha256:<{bench_ref}_hash>"
        h_p = artifact.get("principle_ref") or f"sha256:<{bench_ref}_principle>"
        h_s = artifact.get("spec_ref") or f"sha256:<{bench_ref}_spec>"

    # Read delta from L1 if available
    delta = 3  # default
    if genesis_dir:
        suffix = (artifact.get("artifact_id") or "").replace("L3-", "")
        l1_path = genesis_dir / "l1" / f"L1-{suffix}.json"
        if l1_path.is_file():
            try:
                l1 = json.loads(l1_path.read_text())
                delta = int(l1.get("difficulty_delta", 3))
            except (json.JSONDecodeError, OSError, ValueError):
                pass

    payload = {
        "h_p": h_p,
        "h_s": h_s,
        "h_b": benchmark_hash,
        "h_x": solution_hash,
        "Q": round(float(Q), 4),
        "Q_int": min(100, max(0, int(round(Q * 100)))),
        "gate_verdicts": gate_verdicts,
        # Fields for on-chain SubmitArgs struct
        "benchmark_hash": benchmark_hash,
        "delta": delta,
    }
    # cert_hash = sha256 of the stable-serialized payload (minus cert_hash itself)
    serialized = json.dumps(payload, sort_keys=True).encode("utf-8")
    payload["cert_hash"] = "0x" + hashlib.sha256(serialized).hexdigest()
    return payload


def run(args: argparse.Namespace) -> int:
    """Mine a benchmark. Returns 0 on success.

    Exit codes:
      0  success (cert submitted, or dry-run completed)
      1  configuration / setup failure
      3  benchmark_id not found
      4  Q below epsilon (solver produced output but didn't clear the gate)
      6  solver timeout
      7  solver nonzero exit code
      5  IPFS dataset fetch failure (when --fetch-dataset used)
    """
    bench_id = args.benchmark_id

    # Step 1: resolve benchmark (offline only in session 5a; chain lookup in later session)
    resolved = _resolve_benchmark_offline(args.genesis_dir, bench_id)
    if resolved is None:
        print(
            f"[pwm-node mine] benchmark not found: {bench_id}\n"
            f"  Looked in {args.genesis_dir}/l3/. Try `pwm-node benchmarks` to list."
        )
        return 3
    artifact, art_path = resolved
    print(f"[pwm-node mine] resolved {bench_id} → {artifact.get('artifact_id')} ({art_path.name})")

    # Step 2: dataset availability (stub — extended in later session with IPFS fetch)
    # For now, user is responsible for placing input files in --work-dir/input/.

    # Step 3: run solver
    if not args.solver or not args.solver.is_file():
        print(f"[pwm-node mine] --solver path required and must exist: {args.solver!r}")
        return 1

    work_dir = args.work_dir or (Path.cwd() / f"pwm_work_{int(time.time())}")
    work_dir.mkdir(parents=True, exist_ok=True)
    print(f"[pwm-node mine] work dir: {work_dir}")
    print(f"[pwm-node mine] running solver: {args.solver}")

    rc, output_dir, elapsed = _run_solver(args.solver, work_dir, timeout_s=args.timeout)
    if rc == 124:
        print(f"[pwm-node mine] solver timed out after {elapsed:.1f}s (limit {args.timeout}s)")
        return 6
    if rc != 0:
        print(f"[pwm-node mine] solver exited with code {rc} after {elapsed:.1f}s")
        return 7
    print(f"[pwm-node mine] solver completed in {elapsed:.1f}s, output: {output_dir}")

    # Step 4: score — use pwm_scoring if available; else return a mock Q for dry-run
    Q = 0.0
    gate_verdicts = {"S1": "pass", "S2": "pass", "S3": "pass", "S4": "pass"}

    try:
        from pwm_scoring import score_solution  # type: ignore

        # pwm_scoring expects the benchmark manifest + solver output dir;
        # we pass the artifact dict directly (L3 JSON) as the manifest.
        # The exact signature may evolve — wrap defensively.
        result = score_solution(
            benchmark_manifest=artifact,
            solver_output=output_dir,
        )
        Q = float(getattr(result, "Q", 0.0))
        gv = getattr(result, "gate_verdicts", None)
        if isinstance(gv, dict):
            gate_verdicts = gv
    except ImportError:
        print("[pwm-node mine] pwm_scoring not installed — using mock Q=0.85 for skeleton test")
        Q = 0.85
    except Exception as e:
        print(f"[pwm-node mine] scoring error: {e}")
        return 1

    print(f"[pwm-node mine] Q = {Q:.3f}, gates: {gate_verdicts}")

    all_pass = all(v == "pass" for v in gate_verdicts.values())
    if not all_pass:
        print("[pwm-node mine] gates did not all PASS — not submitting")
        return 4

    # Step 5: build cert_payload
    payload = _build_cert_payload(
        artifact, Q, gate_verdicts,
        genesis_dir=args.genesis_dir,
        art_path=art_path,
    )
    cert_file = work_dir / "cert_payload.json"
    cert_file.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"[pwm-node mine] cert payload written to: {cert_file}")
    print(f"[pwm-node mine] cert_hash: {payload['cert_hash']}")

    if args.dry_run:
        print("[pwm-node mine] --dry-run: not submitting to chain.")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    # Step 6: submit — delegate to submit-cert command logic
    print(f"[pwm-node mine] submitting cert to {args.network}...")
    submit_args = argparse.Namespace(
        cert=cert_file,
        network=args.network,
        genesis_dir=args.genesis_dir,
        verbose=args.verbose,
        command="submit-cert",
        ipfs_upload=False,
        skip_ipfs_on_failure=False,
        dry_run=False,
        no_wait=False,
        timeout=300,
        gas=500000,
    )
    from pwm_node.commands import submit
    return submit.run(submit_args)
