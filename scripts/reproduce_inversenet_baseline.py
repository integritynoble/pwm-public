"""Single-sample reproduction of InverseNet GAP-TV Scenario I baseline.

Demonstrates that the CASSI and CACTI reference algorithms in
`public/algorithm_base/` clear the 24 dB Stream-1 target on at least
one sample each, when fed properly normalized inputs and the canonical
hyperparameters from the InverseNet paper.

Per `MAINNET_DEPLOY_PLAN.md` Stream 1 done criterion (a).

Usage:
    python scripts/reproduce_inversenet_baseline.py

Expected output:
    CASSI sample_01: 25.66 dB (target >= 24 dB; InverseNet GAP-TV
                                 Scenario I claim: 24.34 +/- 1.90 dB)
    CACTI sample_01 (Kobe): 27.99 dB (target >= 24 dB; InverseNet
                                       GAP-TV Scenario I claim:
                                       26.75 +/- 4.48 dB)

The key fixes vs the existing demos at
`pwm-team/pwm_product/demos/{cassi,cacti}/sample_01/`:

CASSI:
  - Public solver expects step-2 spectral dispersion (snapshot width
    = 256 + 27*2 = 310). PWM demo generator uses step=1.
  - Public solver expects 100 iterations + lam=0.1. PWM uses 15 +
    lam=0.005 -> only ~19 dB.

CACTI:
  - Public solver expects masks normalized to [0, 1] and ground truth
    normalized to [0, 1]. PWM demos store masks at uint8-scaled
    floats (~[0, 0.0039]) and ground truth in [0, 255].
  - Public solver uses Nesterov-accelerated GAP with per-iteration
    clip to [0, 1]. PWM PnP-ADMM lacks the clip and amplifies output
    to [0, 5+] -> low PSNR after normalization.

To clear the Stream-1 target on all 16 samples, regenerate
`pwm-team/pwm_product/demos/{cassi,cacti}/sample_*/{snapshot,solution}.npz`
using these algorithms + the matching forward model.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "public"))
sys.path.insert(0, str(REPO / "public/packages/pwm_core"))


def psnr(gt: np.ndarray, sol: np.ndarray, peak: float | None = None) -> float:
    mse = float(np.mean((gt - sol) ** 2))
    if mse == 0:
        return float("inf")
    if peak is None:
        peak = float(gt.max() - gt.min()) or 1.0
    return float(10.0 * np.log10(peak ** 2 / mse))


def cassi_sample_01() -> float:
    from pwm_core.recon.gap_tv import gap_tv_cassi

    sample = REPO / "pwm-team/pwm_product/demos/cassi/sample_01"
    gt = np.load(sample / "ground_truth.npz")["x"].astype(np.float32)  # (256, 256, 28) in [0, 1]
    mask = np.load(sample / "snapshot.npz")["mask"].astype(np.float32)  # (256, 256)

    H, W, N = gt.shape
    step = 2
    W_meas = W + (N - 1) * step
    y = np.zeros((H, W_meas), dtype=np.float32)
    for k in range(N):
        y[:, k * step:k * step + W] += mask * gt[:, :, k]

    t0 = time.time()
    xh = gap_tv_cassi(y, mask, n_bands=N, iterations=100, lam=0.1, step=step, tv_iter=5)
    elapsed = time.time() - t0

    db = psnr(gt, xh)
    print(
        f"CASSI sample_01: {db:6.2f} dB  ({elapsed:5.1f}s; "
        f"GAP-TV iter=100 lam=0.1 step=2; "
        f"target >= 24, InverseNet claim 24.34 +/- 1.90)"
    )
    return db


def cacti_sample_01_kobe() -> float:
    from pwm_core.recon.cacti_solvers import gap_tv_cacti

    sample = REPO / "pwm-team/pwm_product/demos/cacti/sample_01"
    gt_pwm = np.load(sample / "ground_truth.npz")["x"].astype(np.float32)  # (8, 256, 256) in [0, 255]
    masks_pwm = np.load(sample / "snapshot.npz")["masks"].astype(np.float32)  # (8, 256, 256)

    # Normalize: gt to [0, 1]; masks to [0, 1].
    gt = gt_pwm / 255.0
    masks_pwm = masks_pwm / max(float(masks_pwm.max()), 1e-8)

    # Public solver expects (H, W, T) layout.
    masks = np.transpose(masks_pwm, (1, 2, 0))
    gt_hwT = np.transpose(gt, (1, 2, 0))
    y = np.sum(masks * gt_hwT, axis=2).astype(np.float32)

    t0 = time.time()
    xh = gap_tv_cacti(y, masks, iterations=100, tv_weight=0.1, tv_iter=5)
    elapsed = time.time() - t0

    db = psnr(gt_hwT, xh)
    print(
        f"CACTI sample_01 [kobe]: {db:6.2f} dB  ({elapsed:5.1f}s; "
        f"GAP-TV iter=100 tv_weight=0.1; "
        f"target >= 24, InverseNet claim 26.75 +/- 4.48)"
    )
    return db


if __name__ == "__main__":
    cassi_db = cassi_sample_01()
    cacti_db = cacti_sample_01_kobe()
    print()
    cassi_pass = cassi_db >= 24.0
    cacti_pass = cacti_db >= 24.0
    print(f"  CASSI {'PASS' if cassi_pass else 'fail'} (target 24 dB)")
    print(f"  CACTI {'PASS' if cacti_pass else 'fail'} (target 24 dB)")
    sys.exit(0 if (cassi_pass and cacti_pass) else 1)
