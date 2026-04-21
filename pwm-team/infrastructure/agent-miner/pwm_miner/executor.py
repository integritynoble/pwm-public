"""executor.py — sandboxed solver execution for the PWM mining client.

Fetches a solver binary from IPFS (via ipfs_fetch, which verifies its SHA-256
hash), then runs it inside a restricted Docker container and returns an
ExecutionResult.

Security invariants (must NEVER be relaxed):
  - VerificationError from fetch_solver propagates immediately; container is
    never launched for an unverified binary.
  - Every docker run call includes --network none (solver cannot exfiltrate).
  - Every docker run call includes --user 1000:1000 (non-root).
  - Container image is always "pwm-sandbox".
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from .ipfs_fetch import VerificationError, fetch_solver  # noqa: F401 — re-exported

__all__ = [
    "ResourceLimits",
    "ExecutionResult",
    "execute_solver",
]

SANDBOX_IMAGE = "pwm-sandbox"
_NON_NEGOTIABLE_FLAGS = ["--network", "none", "--user", "1000:1000"]


@dataclass
class ResourceLimits:
    memory_mb: int = 4096
    timeout_seconds: int = 300
    gpu_spec: str = "none"  # "none", "all", "device=0", etc.


@dataclass
class ExecutionResult:
    success: bool
    output_path: Path
    stdout: str
    stderr: str
    runtime_seconds: float
    memory_peak_mb: float = 0.0  # 0.0 if unavailable


def _build_docker_cmd(
    solver_path: Path,
    instance_dir: Path,
    output_dir: Path,
    limits: ResourceLimits,
) -> list[str]:
    """Return the docker run argument list (does NOT include the executable itself)."""
    cmd: list[str] = [
        "docker", "run", "--rm",
        # --- non-negotiable security flags ---
        "--network", "none",
        "--user", "1000:1000",
        # --- resource limits ---
        "--memory", f"{limits.memory_mb}m",
        "--memory-swap", f"{limits.memory_mb}m",
        # --- volume mounts ---
        "-v", f"{solver_path}:/input/solve.py:ro",
        "-v", f"{instance_dir}:/input:ro",
        "-v", f"{output_dir}:/output",
    ]

    # GPU passthrough only when explicitly requested
    if limits.gpu_spec != "none":
        cmd += ["--gpus", limits.gpu_spec]

    cmd.append(SANDBOX_IMAGE)
    return cmd


def execute_solver(
    solver_cid: str,
    expected_hash: str,
    instance_dir: Path,
    output_dir: Path,
    limits: ResourceLimits | None = None,
) -> ExecutionResult:
    """Fetch, verify, and execute a solver inside the pwm-sandbox container.

    Steps:
      1. Call fetch_solver(solver_cid, expected_hash).
         Raises VerificationError if the SHA-256 of the downloaded binary does
         not match expected_hash — propagated immediately; container never runs.
      2. Build the docker run command with all security and resource flags.
      3. Run the container with subprocess.run, capturing stdout/stderr.
      4. Return an ExecutionResult.

    Args:
        solver_cid:    IPFS content identifier for the solver binary.
        expected_hash: Expected SHA-256 hex digest (must match on-chain record).
        instance_dir:  Host path mounted read-only at /input inside container.
        output_dir:    Host path mounted read-write at /output inside container.
        limits:        Resource constraints; defaults to ResourceLimits() if None.

    Returns:
        ExecutionResult describing the run outcome.

    Raises:
        VerificationError: If the downloaded binary's hash does not match
            expected_hash.  The container is never started in this case.
    """
    if limits is None:
        limits = ResourceLimits()

    # Step 1 — fetch and verify.  VerificationError propagates untouched.
    solver_path: Path = fetch_solver(solver_cid, expected_hash)

    # Step 2 — build command.
    cmd = _build_docker_cmd(solver_path, instance_dir, output_dir, limits)

    # Step 3 — execute.
    start = time.monotonic()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=limits.timeout_seconds,
    )
    runtime = time.monotonic() - start

    # Step 4 — package result.
    return ExecutionResult(
        success=result.returncode == 0,
        output_path=output_dir,
        stdout=result.stdout,
        stderr=result.stderr,
        runtime_seconds=runtime,
        memory_peak_mb=0.0,  # Docker does not surface peak RSS in subprocess output
    )
