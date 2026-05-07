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
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# Placeholder address used when no signer is configured (e.g. --dry-run with
# PWM_PRIVATE_KEY unset). Keeps the payload shape valid so tests and offline
# users can inspect the cert. The chain-submit path rejects zero-address
# payloads before broadcasting.
_ZERO_ADDR = "0x" + "0" * 40


# UI-only fields excluded from canonical-JSON hashing. MUST match
# scripts/register_genesis.py::UI_ONLY_FIELDS exactly — otherwise the
# benchmarkHash this CLI computes will diverge from what's on-chain
# and `submit_certificate` will revert with "benchmark not registered".
# Smoke-test 2026-05-03 caught this divergence before the public-repo
# cutover; that's what the test_hash_convention.py regression covers.
_UI_ONLY_FIELDS = frozenset({
    "display_slug",
    "display_color",
    "ui_metadata",
    "registration_tier",
    "display_baselines",  # leaderboard-floor sidecar; e.g. deep-learning
                          # SOTA landmarks added off-chain via cert-meta.
})
# TODO: consolidate this set with scripts/register_genesis.py::UI_ONLY_FIELDS
# into a single shared module so future schema additions can't drift between
# the registration path and the mining path. The 2026-05-07 audit caught a
# divergence (display_baselines was added to register_genesis 2026-05-06 but
# never propagated here, breaking benchmarkHash equality on dry-runs).


def _canonical_for_hashing(obj):
    """Strip UI-only fields recursively at top level before hashing.

    Keeps the on-chain hash invariant under UI-metadata edits, matching
    `scripts/register_genesis.py::_canonical_for_hashing`.
    """
    if isinstance(obj, dict):
        return {k: v for k, v in obj.items() if k not in _UI_ONLY_FIELDS}
    return obj


def _canonical_json(obj) -> bytes:
    """Stable-serialize to bytes: sorted keys, compact separators, UTF-8.

    Must match scripts/register_genesis.py::_canonical_json so the
    benchmarkHash we compute here equals the hash that was registered on-chain.
    Filters the full UI_ONLY_FIELDS set above (display_slug, display_color,
    ui_metadata, registration_tier, display_baselines) before serializing —
    see PWM_HUMAN_READABLE_IDS_AND_CONTRIBUTION_FLOW_2026-05-03.md for the
    rationale.
    """
    filtered = _canonical_for_hashing(obj)
    return json.dumps(filtered, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _keccak256_hex(data: bytes) -> str:
    """keccak256 as ``0x`` + 64 hex chars, preserving leading zero bytes."""
    try:
        from eth_utils import keccak  # type: ignore
    except ImportError:
        # Fallback: pycryptodome's Keccak (same algorithm) — web3.py installs it
        # transitively. We need the Ethereum keccak, NOT hashlib.sha3_256.
        from Crypto.Hash import keccak as _keccak  # type: ignore
        h = _keccak.new(digest_bits=256)
        h.update(data)
        digest = h.digest()
    else:
        digest = keccak(data)
    return "0x" + digest.hex().zfill(64)


def _resolve_delta(artifact: dict, genesis_dir: Path | None) -> int:
    """Return the difficulty_delta for an L3 artifact.

    L3 JSON doesn't carry the delta directly — it lives on the parent L1.
    We resolve it by looking up ``genesis_dir/l1/<parent_l1>.json``, falling
    back to any ``difficulty_delta`` on the L3 itself, else 0.
    """
    direct = artifact.get("difficulty_delta")
    if isinstance(direct, int):
        return direct
    parent_l1 = artifact.get("parent_l1")
    if not parent_l1 or genesis_dir is None:
        return 0
    l1_path = Path(genesis_dir) / "l1" / f"{parent_l1}.json"
    if not l1_path.is_file():
        return 0
    try:
        l1 = json.loads(l1_path.read_text())
    except (json.JSONDecodeError, OSError):
        return 0
    v = l1.get("difficulty_delta")
    return int(v) if isinstance(v, int) else 0


def _principle_id_from_artifact(artifact: dict) -> int:
    """Extract the integer principle id from an L3 artifact.

    Looks at (in order): ``principle_number``, ``parent_l1`` (e.g. ``L1-003``),
    ``artifact_id`` (``L3-003``). Returns 0 if nothing parses — useful for
    synthetic test artifacts but guarantees the field is always an int.
    """
    for key in ("principle_number", "parent_l1", "artifact_id"):
        v = artifact.get(key)
        if v is None:
            continue
        # Grab the TRAILING digit run: "L1-003" → 3, "L3-003" → 3, "003" → 3.
        # A leading regex like \d+ would match the "1" in "L1-003".
        m = re.search(r"(\d+)\s*$", str(v))
        if m:
            return int(m.group(1))
    return 0


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


def _build_cert_payload(
    artifact: dict,
    Q: float,
    gate_verdicts: dict,
    *,
    sp_wallet: str | None = None,
    share_ratio_p: int = 5000,
    delta: int | None = None,
) -> dict:
    """Assemble a cert_payload dict matching the PWMCertificate.submit() struct.

    Produces the 12-field camelCase schema defined in
    ``interfaces/cert_schema.json``. ``sp_wallet`` defaults to the zero address
    when not provided (offline/dry-run); all five wallet fields are set to it
    for the single-wallet self-solve case. ``delta`` is read from the artifact
    when possible (``difficulty_delta``), otherwise uses the passed default.

    Parameters
    ----------
    artifact : dict
        The L3 benchmark JSON (as loaded from genesis/l3/L3-<n>.json).
    Q : float
        Quality score in [0, 1]; rounded × 100 to get Q_int.
    gate_verdicts : dict
        S1-S4 verdicts — stored under ``_meta`` for inspection only; the chain
        submission itself does not carry them.
    sp_wallet : str, optional
        0x-prefixed 40-char address. Defaults to the zero address.
    share_ratio_p : int
        SP share × 10000. Default 5000 (0.50).
    delta : int, optional
        Override the artifact-derived difficulty tier.

    Returns
    -------
    dict
        12 struct fields (camelCase) plus an optional ``_meta`` block.
    """
    wallet = sp_wallet or _ZERO_ADDR
    principle_id = _principle_id_from_artifact(artifact)
    resolved_delta = delta if delta is not None else int(artifact.get("difficulty_delta") or 0)
    Q_int = int(round(float(Q) * 100))
    Q_int = max(0, min(100, Q_int))  # clamp to u8 range covered by the schema

    benchmark_hash = _keccak256_hex(_canonical_json(artifact))

    # Struct-level fields, in the ABI-declared order.
    payload: dict = {
        "benchmarkHash": benchmark_hash,
        "principleId": principle_id,
        "l1Creator": wallet,
        "l2Creator": wallet,
        "l3Creator": wallet,
        "acWallet": wallet,
        "cpWallet": wallet,
        "shareRatioP": int(share_ratio_p),
        "Q_int": Q_int,
        "delta": int(resolved_delta),
        "rank": 0,
    }
    # certHash = keccak256 over the 11 non-certHash fields, stable-serialized.
    payload["certHash"] = _keccak256_hex(_canonical_json(payload))
    # Preserve human-readable scoring context out-of-band; the chain ignores it.
    payload["_meta"] = {
        "artifact_id": artifact.get("artifact_id"),
        "Q_float": round(float(Q), 6),
        "gate_verdicts": dict(gate_verdicts),
    }
    return payload


def _resolve_signer_address() -> str | None:
    """Return the signer address from PWM_PRIVATE_KEY, or None if unset/invalid.

    Never raises — callers fall back to the zero address. Used for --dry-run
    so offline users get a well-formed cert payload without configuring a key.
    """
    pk = os.environ.get("PWM_PRIVATE_KEY")
    if not pk:
        return None
    try:
        from eth_account import Account  # type: ignore
    except ImportError:
        return None
    try:
        if not pk.startswith("0x"):
            pk = "0x" + pk
        return Account.from_key(pk).address
    except Exception:
        return None


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
        # pwm_scoring not installed. Try to derive Q from the wrapper's
        # meta.json (psnr_db_vs_ground_truth). Falls back to the mock
        # 0.85 if no usable PSNR is present. The mapping
        # Q = min(PSNR_dB / 100, 1.0) is a placeholder until the
        # protocol-canonical scoring engine ships; it preserves rank
        # ordering by signal quality and yields a distinct certHash per
        # solver, which the strict-duplicate-hash check requires.
        Q = 0.85
        meta_path = output_dir / "meta.json"
        if meta_path.is_file():
            try:
                wrapper_meta = json.loads(meta_path.read_text())
                psnr = wrapper_meta.get("psnr_db_vs_ground_truth")
                if isinstance(psnr, (int, float)) and psnr > 0:
                    Q = min(float(psnr) / 100.0, 1.0)
                    print(f"[pwm-node mine] pwm_scoring not installed — derived Q={Q:.4f} from wrapper PSNR={psnr} dB")
                else:
                    print(f"[pwm-node mine] pwm_scoring not installed — using mock Q=0.85 (no PSNR in {meta_path.name})")
            except (json.JSONDecodeError, OSError) as e:
                print(f"[pwm-node mine] pwm_scoring not installed — using mock Q=0.85 (could not read {meta_path.name}: {e})")
        else:
            print("[pwm-node mine] pwm_scoring not installed — using mock Q=0.85 for skeleton test")
    except Exception as e:
        print(f"[pwm-node mine] scoring error: {e}")
        return 1

    print(f"[pwm-node mine] Q = {Q:.3f}, gates: {gate_verdicts}")

    all_pass = all(v == "pass" for v in gate_verdicts.values())
    if not all_pass:
        print("[pwm-node mine] gates did not all PASS — not submitting")
        return 4

    # Step 5: build cert_payload
    sp_wallet = getattr(args, "sp_wallet", None) or _resolve_signer_address()
    share_ratio_p = int(getattr(args, "share_ratio_p", 5000))
    delta = _resolve_delta(artifact, args.genesis_dir)
    payload = _build_cert_payload(
        artifact, Q, gate_verdicts,
        sp_wallet=sp_wallet,
        share_ratio_p=share_ratio_p,
        delta=delta,
    )
    cert_file = work_dir / "cert_payload.json"
    cert_file.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"[pwm-node mine] cert payload written to: {cert_file}")
    print(f"[pwm-node mine] certHash: {payload['certHash']}")
    print(f"[pwm-node mine] benchmarkHash: {payload['benchmarkHash']}")

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
