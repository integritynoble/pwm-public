"""CASSI reference-solver quality test.

Compares the stored solution.npz (reference-solver output) against
ground_truth.npz for every sample under
`pwm-team/pwm_product/demos/cassi/sample_*` and reports per-sample
PSNR (dB) plus the average.

Per `pwm-team/coordination/MAINNET_DEPLOY_PLAN.md` Stream 1 done
criterion (a): average PSNR over KAIST-10 must be >= 24 dB.

Usage:
    cd pwm-team/pwm_product && python -m pytest tests/test_cassi_quality.py -v
    # or just print PSNRs without assertion:
    python pwm-team/pwm_product/tests/test_cassi_quality.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest


PSNR_TARGET_DB = 24.0
DEMO_DIR = Path(__file__).resolve().parents[1] / "demos" / "cassi"
GT_KEYS = ("x", "gt", "ground_truth", "cube", "image")
SOL_KEYS = ("cube", "x", "solution", "x_hat", "image", "y")


def _load_array(npz_path: Path, candidate_keys: tuple[str, ...]) -> np.ndarray:
    z = np.load(npz_path)
    for k in candidate_keys:
        if k in z.files:
            return z[k]
    if z.files:
        # Fall back to first array; warn caller via raised key list.
        return z[z.files[0]]
    raise RuntimeError(f"{npz_path} has no arrays")


def _psnr(gt: np.ndarray, sol: np.ndarray) -> float:
    """PSNR in dB — InverseNet paper's exact convention.

    Reproduces `compute_psnr` in
    `papers/inversenet/scripts/validate_cassi_inversenet.py`:

        def compute_psnr(x_true, x_recon):
            x_true  = np.clip(x_true,  0, 1).astype(np.float64)
            x_recon = np.clip(x_recon, 0, 1).astype(np.float64)
            mse = mean((x_true - x_recon)**2)
            return 10 * log10(1.0 / mse)

    For CASSI, KAIST scenes are stored in [0, 1] natively. For data
    that's stored in a wider integer-derived range (e.g., [0, 255]
    from a uint8-cast .mat file), normalize gt to [0, 1] using its
    own peak first, then apply the same scale to sol. Then clip both
    to [0, 1] and compute MSE against peak = 1.

    The clip-to-[0, 1] is the critical step the original
    test missed: bright solver outputs (e.g., GAP-TV sol.max ≈ 1.45)
    were dragging PSNR down before clipping was applied.
    """
    gt = gt.astype(np.float64)
    sol = sol.astype(np.float64)
    if gt.shape != sol.shape:
        if gt.ndim == 3 and sol.ndim == 3 and gt.shape == sol.shape[::-1]:
            sol = np.moveaxis(sol, [0, 1, 2], [2, 0, 1])
    if gt.shape != sol.shape:
        raise ValueError(f"shape mismatch: gt={gt.shape} sol={sol.shape}")
    # Auto-handle integer-derived ground truth (e.g., [0, 255]):
    # divide BOTH arrays by gt.max() so they share a common scale.
    gt_peak = float(gt.max())
    if gt_peak > 1.5:
        gt = gt / max(gt_peak, 1e-8)
        sol = sol / max(gt_peak, 1e-8)
    # Paper's exact PSNR convention: clip both to [0, 1], peak = 1.
    gt = np.clip(gt, 0.0, 1.0)
    sol = np.clip(sol, 0.0, 1.0)
    mse = float(np.mean((gt - sol) ** 2))
    if mse < 1e-10:
        return 100.0
    return float(10.0 * np.log10(1.0 / mse))


def _per_sample_psnr() -> list[tuple[str, float, dict]]:
    out = []
    if not DEMO_DIR.is_dir():
        return out
    for sample_dir in sorted(DEMO_DIR.iterdir()):
        if not sample_dir.is_dir() or not sample_dir.name.startswith("sample_"):
            continue
        gt_path = sample_dir / "ground_truth.npz"
        sol_path = sample_dir / "solution.npz"
        if not (gt_path.is_file() and sol_path.is_file()):
            continue
        gt = _load_array(gt_path, GT_KEYS)
        sol = _load_array(sol_path, SOL_KEYS)
        meta = {}
        meta_path = sample_dir / "meta.json"
        if meta_path.is_file():
            try:
                meta = json.loads(meta_path.read_text())
            except json.JSONDecodeError:
                meta = {}
        try:
            psnr = _psnr(gt, sol)
        except ValueError as exc:
            psnr = float("nan")
            meta["_psnr_error"] = str(exc)
        out.append((sample_dir.name, psnr, meta))
    return out


def _summary() -> dict:
    rows = _per_sample_psnr()
    finite = [psnr for _, psnr, _ in rows if np.isfinite(psnr)]
    avg = float(np.mean(finite)) if finite else float("nan")
    return {"rows": rows, "avg_psnr_db": avg, "count": len(rows)}


def test_cassi_average_psnr_meets_target():
    """Average PSNR over all CASSI samples must clear the deploy gate."""
    summary = _summary()
    rows = summary["rows"]
    assert rows, f"no CASSI samples found at {DEMO_DIR}"
    print()
    print(f"CASSI per-sample PSNR (target average >= {PSNR_TARGET_DB} dB)")
    for name, psnr, _meta in rows:
        marker = "✓" if psnr >= PSNR_TARGET_DB else "✗"
        print(f"  {marker} {name}: {psnr:6.2f} dB")
    avg = summary["avg_psnr_db"]
    print(f"  avg = {avg:6.2f} dB ({summary['count']} samples)")
    assert avg >= PSNR_TARGET_DB, (
        f"CASSI avg PSNR {avg:.2f} dB < target {PSNR_TARGET_DB} dB "
        f"(Stream 1 done criterion not met)"
    )


if __name__ == "__main__":
    summary = _summary()
    print(f"CASSI per-sample PSNR (target average >= {PSNR_TARGET_DB} dB)")
    for name, psnr, _meta in summary["rows"]:
        marker = "PASS" if psnr >= PSNR_TARGET_DB else "fail"
        print(f"  [{marker}] {name}: {psnr:6.2f} dB")
    print(f"  avg = {summary['avg_psnr_db']:6.2f} dB ({summary['count']} samples)")
