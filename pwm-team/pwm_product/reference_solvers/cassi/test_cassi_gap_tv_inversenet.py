"""Regression test: cassi_gap_tv.py must consume the bundled InverseNet
demo data without errors and produce a finite PSNR.

The bundled `pwm_product/demos/cassi/sample_*/snapshot.npz` files have keys
{y, mask, step} (InverseNet wide-snapshot convention; y is shape
(H, mask_W + (N_bands - 1) * step)). The solver auto-detects this format
and dispatches to forward_wide / adjoint_wide.

This test prevents a regression that broke L4-Test-1 in the customer guide's
hands-on walkthrough on 2026-05-07: the solver had only narrow-form support,
so it crashed with KeyError('shifts') / ValueError(shapes) the moment a
real customer tried to run mining against the bundled demos.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
SOLVER = REPO_ROOT / "pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py"
SAMPLE_01 = REPO_ROOT / "pwm-team/pwm_product/demos/cassi/sample_01"


@pytest.fixture
def work_dir(tmp_path: Path) -> Path:
    """Stage sample_01's snapshot.npz + ground_truth.npz under tmp/input/."""
    in_dir = tmp_path / "input"
    in_dir.mkdir(parents=True)
    for fname in ("snapshot.npz", "ground_truth.npz"):
        (in_dir / fname).write_bytes((SAMPLE_01 / fname).read_bytes())
    (tmp_path / "output").mkdir()
    return tmp_path


def test_inversenet_format_loads_and_runs(work_dir: Path):
    """Solver must consume `step` (scalar) instead of `shifts` (array)."""
    import numpy as np
    snap = np.load(work_dir / "input" / "snapshot.npz")
    assert "step" in snap.files, "Bundled demo should have InverseNet 'step' key"
    assert "shifts" not in snap.files, "Bundled demo should NOT have explicit 'shifts'"

    result = subprocess.run(
        [sys.executable, str(SOLVER),
         "--input", str(work_dir / "input"),
         "--output", str(work_dir / "output"),
         "--iters", "5"],
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, (
        f"solver exited {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )

    sol = work_dir / "output" / "solution.npz"
    assert sol.is_file(), "solver must write solution.npz"
    cube = np.load(sol)["cube"]
    assert cube.shape == (256, 256, 28), f"unexpected cube shape: {cube.shape}"
    assert np.isfinite(cube).all(), "reconstruction has NaN/Inf"


def test_meta_json_psnr_is_finite_and_positive(work_dir: Path):
    """PSNR should be a finite positive number — confirms the iteration is
    not silently NaN-ing out and the wide-form forward/adjoint are mathematically
    consistent (otherwise the residual blows up and PSNR collapses)."""
    subprocess.run(
        [sys.executable, str(SOLVER),
         "--input", str(work_dir / "input"),
         "--output", str(work_dir / "output"),
         "--iters", "20"],
        capture_output=True, text=True, timeout=300, check=True,
    )
    meta = json.loads((work_dir / "output" / "meta.json").read_text())
    assert "psnr_db" in meta, "meta.json should record psnr_db"
    psnr = float(meta["psnr_db"])
    assert 5.0 < psnr < 100.0, (
        f"PSNR {psnr} dB outside sanity range; suggests the iteration "
        f"diverged or the wide-form forward/adjoint are mismatched"
    )


def test_wide_form_dispatch_in_gap_tv():
    """Direct unit test: gap_tv must auto-detect wide form when y is wider than mask."""
    sys.path.insert(0, str(SOLVER.parent))
    import importlib
    import cassi_gap_tv
    importlib.reload(cassi_gap_tv)
    import numpy as np

    H, mask_W, N, step = 32, 32, 8, 2
    rng = np.random.default_rng(0)
    x_true = rng.random((H, mask_W, N), dtype=np.float32)
    mask = (rng.random((H, mask_W)) > 0.5).astype(np.float32)
    shifts = np.array([b * step for b in range(N)], dtype=np.int32)

    # Build a wide-form snapshot
    y_wide = cassi_gap_tv.forward_wide(x_true, mask, shifts)
    assert y_wide.shape == (H, mask_W + (N - 1) * step), \
        f"wide snapshot shape mismatch: {y_wide.shape}"

    # Run gap_tv on it; should auto-dispatch to wide form
    x_hat = cassi_gap_tv.gap_tv(y_wide, mask, shifts, N, n_iters=10)
    assert x_hat.shape == (H, mask_W, N), \
        f"reconstruction shape mismatch: {x_hat.shape}"
    assert np.isfinite(x_hat).all()
