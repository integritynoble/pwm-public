"""Smoke tests for the CASSI and CACTI reference solvers.

Each test runs the solver on its auto-generated synthetic input (no
files required) and confirms:

  1. Exit code 0
  2. solution.npz written with the expected shape
  3. meta.json parseable and has the right keys
  4. PSNR on the synthetic problem is above a trivial floor — confirms
     the solver isn't just returning zeros or constants
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SOLVERS_DIR = Path(__file__).resolve().parent


def _run_solver(solver_path: Path, tmp_path: Path) -> dict:
    """Invoke one solver. Returns parsed meta.json on success, raises on failure."""
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    output_dir.mkdir()
    res = subprocess.run(
        [sys.executable, str(solver_path),
         "--input", str(input_dir), "--output", str(output_dir)],
        capture_output=True, text=True, timeout=60,
    )
    assert res.returncode == 0, (
        f"solver exited {res.returncode}\n"
        f"stdout: {res.stdout}\nstderr: {res.stderr}"
    )
    assert (output_dir / "solution.npz").is_file(), "solution.npz not written"
    meta_path = output_dir / "meta.json"
    assert meta_path.is_file(), "meta.json not written"
    return json.loads(meta_path.read_text())


def test_cassi_gap_tv(tmp_path):
    try:
        import numpy  # noqa: F401
    except ImportError:
        pytest.skip("numpy not available")

    solver = SOLVERS_DIR / "cassi" / "cassi_gap_tv.py"
    meta = _run_solver(solver, tmp_path)
    assert meta["solver"] == "cassi_gap_tv"
    assert meta["benchmark"] == "L3-003 (CASSI)"
    assert meta["algorithm"] == "GAP-TV"
    assert meta["source"] == "synthetic"
    # Synthetic problem is 32x32x8.
    assert meta["output_shape"] == [32, 32, 8]
    # Verify non-trivial reconstruction (a constant image would score ~6 dB).
    assert meta["psnr_db"] >= 8.0, (
        f"PSNR {meta['psnr_db']} dB too low — solver may be broken"
    )

    # Verify the reconstructed cube loads cleanly.
    import numpy as np
    sol = np.load(tmp_path / "out" / "solution.npz")["cube"]
    assert sol.shape == (32, 32, 8)
    assert sol.dtype == np.float32
    assert np.isfinite(sol).all(), "solution contains NaN/Inf"


def test_cacti_pnp_admm(tmp_path):
    try:
        import numpy  # noqa: F401
    except ImportError:
        pytest.skip("numpy not available")

    solver = SOLVERS_DIR / "cacti" / "cacti_pnp_admm.py"
    meta = _run_solver(solver, tmp_path)
    assert meta["solver"] == "cacti_pnp_admm"
    assert meta["benchmark"] == "L3-004 (CACTI)"
    assert meta["algorithm"] == "PnP-ADMM + 2D TV prior"
    assert meta["source"] == "synthetic"
    # Synthetic problem is 4 frames, 32x32.
    assert meta["output_shape"] == [4, 32, 32]
    assert meta["psnr_db"] >= 10.0, (
        f"PSNR {meta['psnr_db']} dB too low — solver may be broken"
    )

    import numpy as np
    sol = np.load(tmp_path / "out" / "solution.npz")["video"]
    assert sol.shape == (4, 32, 32)
    assert sol.dtype == np.float32
    assert np.isfinite(sol).all(), "solution contains NaN/Inf"
