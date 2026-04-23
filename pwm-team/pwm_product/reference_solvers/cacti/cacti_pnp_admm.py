"""CACTI reference solver — PnP-ADMM with TV prior, numpy only.

Minimal, self-contained reference for Coded Aperture Compressive
Temporal Imaging. Sister solver to the CASSI GAP-TV reference: same
contract, same ethos. Not state-of-the-art.

Contract (matches pwm-node mine's subprocess invocation):

    python cacti_pnp_admm.py --input <input_dir> --output <output_dir>

Input dir MUST contain:
    snapshot.npz   with keys:
        y:     shape (H, W),       float32 — compressive snapshot
        masks: shape (T, H, W),    float32 (binary 0/1) — per-frame masks

Output dir gets:
    solution.npz   with key `video`: shape (T, H, W), float32
    meta.json      solver name, version, iterations, PSNR if ground-truth

If `snapshot.npz` is missing, the solver generates a tiny synthetic
problem (4 frames, 32×32) for CI smoke tests.

Forward model:
    y[i, j] = sum_t  masks[t, i, j] * x[t, i, j]
           (the per-frame masks sum together through one exposure)

Adjoint:
    Phi^T(y)[t, i, j] = masks[t, i, j] * y[i, j]

PnP-ADMM iteration (see Chan et al., 2016):
    Given the splitting min_x  1/2 ||Phi x - y||^2 + g(x)
    Introduce z = x, Lagrange multiplier u:
        x^{k+1} = (Phi^T Phi + rho I)^{-1} (Phi^T y + rho(z^k - u^k))
        z^{k+1} = denoise(x^{k+1} + u^k, sigma)
        u^{k+1} = u^k + x^{k+1} - z^{k+1}
    Here `denoise` is a cheap 2D TV prox applied per-frame.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SOLVER_NAME = "cacti_pnp_admm"
SOLVER_VERSION = "1.0.0"


def forward(x, masks):
    """y[i,j] = sum_t masks[t,i,j] * x[t,i,j]."""
    import numpy as np
    return (masks * x).sum(axis=0)


def adjoint(y, masks):
    """Phi^T: scatter y back into every frame weighted by the frame's mask."""
    import numpy as np
    return masks * y[None, :, :]


def tv_prox_2d(u, tau, n_steps=8, step=0.2):
    """Chambolle's dual TV prox, per-frame 2D."""
    import numpy as np
    px = np.zeros_like(u)
    py = np.zeros_like(u)
    for _ in range(n_steps):
        div = np.zeros_like(u)
        div[:, 1:]  += px[:, 1:] - px[:, :-1]
        div[:, 0]   += px[:, 0]
        div[1:, :]  += py[1:, :] - py[:-1, :]
        div[0, :]   += py[0, :]
        tmp = u - tau * div
        gx = np.zeros_like(tmp); gx[:, :-1] = tmp[:, 1:] - tmp[:, :-1]
        gy = np.zeros_like(tmp); gy[:-1, :] = tmp[1:, :] - tmp[:-1, :]
        px_new = px + step * gx
        py_new = py + step * gy
        norm = np.maximum(1.0, np.sqrt(px_new * px_new + py_new * py_new) / tau)
        px = px_new / norm
        py = py_new / norm
    div = np.zeros_like(u)
    div[:, 1:]  += px[:, 1:] - px[:, :-1]
    div[:, 0]   += px[:, 0]
    div[1:, :]  += py[1:, :] - py[:-1, :]
    div[0, :]   += py[0, :]
    return u - tau * div


def tv_denoise_video(v, tau=0.01, n_inner=8):
    """Apply 2D TV per frame. Cheap; ignores inter-frame structure."""
    import numpy as np
    out = np.empty_like(v)
    for t in range(v.shape[0]):
        out[t] = tv_prox_2d(v[t], tau=tau, n_steps=n_inner)
    return out


def pnp_admm(y, masks, n_iters=20, rho=0.05, tv_lambda=0.01,
             tv_decay=0.98, verbose=False):
    """PnP-ADMM with TV prior. Returns reconstructed video (T, H, W)."""
    import numpy as np
    T, H, W = masks.shape
    # Pre-compute per-pixel factor for the x-update.
    # Phi^T Phi acts elementwise: (Phi^T Phi x)_t = masks_t * (sum_t masks_t * x_t)
    # We'll solve (Phi^T Phi + rho I) x = rhs approximately via one Jacobi sweep
    # per iteration — cheap and stable for binary masks.
    sum_mask_sq = (masks ** 2).sum(axis=0)  # (H, W)
    sum_mask_sq = np.maximum(sum_mask_sq, 1e-8)

    # Warm start: back-projection, scaled by number of frames.
    x = adjoint(y, masks) / T
    z = x.copy()
    u = np.zeros_like(x)

    lam = tv_lambda
    for k in range(n_iters):
        # x-update: Jacobi step on (Phi^T Phi + rho I) x = Phi^T y + rho(z - u)
        rhs = adjoint(y, masks) + rho * (z - u)
        # Diagonal factor for Phi^T Phi on a given voxel = masks_t^2 (binary: = masks_t).
        # For element (t,i,j): (Phi^T Phi x)_{t,i,j} = masks_{t,i,j} * sum_s masks_{s,i,j} x_{s,i,j}
        #                                            = masks_{t,i,j} * (Phi x)_{i,j}
        # Approximation: treat Phi^T Phi as diagonal with entries = masks_t * (Phi 1)_{i,j}
        # which equals masks_t * sum_mask_sq at (i,j).
        diag = masks * sum_mask_sq[None, :, :]
        x = rhs / (diag + rho)

        # z-update: denoise x + u
        z = tv_denoise_video(x + u, tau=lam)
        z = np.clip(z, 0.0, None)            # non-negativity

        # u-update
        u = u + x - z

        lam *= tv_decay
        if verbose and (k == 0 or (k + 1) % 5 == 0 or k + 1 == n_iters):
            res = float(np.linalg.norm(y - forward(z, masks)))
            print(f"  iter {k + 1:3d}/{n_iters}  ||r||_2 = {res:.4f}")

    return z


def generate_synthetic_problem(T=4, H=32, W=32, seed=0):
    """Tiny synthetic CACTI problem for CI / smoke tests."""
    import numpy as np
    rng = np.random.default_rng(seed)
    # Ground-truth video: a moving Gaussian blob
    x_true = np.zeros((T, H, W), dtype=np.float32)
    for t in range(T):
        cx = W // 4 + t * (W // (2 * T))  # moves right each frame
        cy = H // 2
        yy, xx = np.mgrid[0:H, 0:W]
        x_true[t] = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * (W / 8) ** 2))
    # Per-frame random binary masks (~50% density)
    masks = (rng.uniform(size=(T, H, W)) > 0.5).astype(np.float32)
    # Snapshot + small noise
    y_clean = forward(x_true, masks)
    noise = rng.normal(scale=0.02 * y_clean.max(), size=y_clean.shape).astype(np.float32)
    y = y_clean + noise
    return {"x_true": x_true, "masks": masks, "y": y.astype(np.float32)}


def psnr_db(x_true, x_hat):
    import numpy as np
    mse = float(np.mean((x_true - x_hat) ** 2))
    if mse == 0:
        return float("inf")
    peak = float(x_true.max())
    if peak <= 0:
        return 0.0
    return float(20.0 * np.log10(peak / np.sqrt(mse)))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--iters", type=int, default=20)
    ap.add_argument("--rho", type=float, default=0.05)
    ap.add_argument("--tv-lambda", type=float, default=0.01)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    try:
        import numpy as np
    except ImportError:
        print(f"[{SOLVER_NAME}] numpy required", file=sys.stderr)
        return 1

    args.output.mkdir(parents=True, exist_ok=True)

    snap_path = args.input / "snapshot.npz"
    gt_path = args.input / "ground_truth.npz"
    if snap_path.is_file():
        data = np.load(snap_path)
        y = data["y"].astype(np.float32)
        masks = data["masks"].astype(np.float32)
        source = "input"
        gt = None
    else:
        print(f"[{SOLVER_NAME}] no snapshot.npz — generating synthetic problem for smoke test")
        synth = generate_synthetic_problem()
        y, masks = synth["y"], synth["masks"]
        source = "synthetic"
        gt = synth["x_true"]
        np.savez_compressed(args.output / "synthetic_ground_truth.npz", x=gt)

    T, H, W = masks.shape
    if args.verbose:
        print(f"[{SOLVER_NAME}] T={T} H={H} W={W} source={source}")

    x_hat = pnp_admm(y, masks, n_iters=args.iters, rho=args.rho,
                    tv_lambda=args.tv_lambda, verbose=args.verbose)

    # Optional PSNR
    psnr = None
    if gt_path.is_file():
        gt = np.load(gt_path)["x"].astype(np.float32)
    if gt is not None:
        xh_n = x_hat / max(x_hat.max(), 1e-8)
        gt_n = gt / max(gt.max(), 1e-8)
        psnr = psnr_db(gt_n, xh_n)

    np.savez_compressed(args.output / "solution.npz", video=x_hat.astype(np.float32))

    meta = {
        "solver": SOLVER_NAME,
        "version": SOLVER_VERSION,
        "benchmark": "L3-004 (CACTI)",
        "algorithm": "PnP-ADMM + 2D TV prior",
        "iters": args.iters,
        "rho": args.rho,
        "tv_lambda": args.tv_lambda,
        "source": source,
        "output_shape": list(x_hat.shape),
    }
    if psnr is not None:
        meta["psnr_db"] = round(psnr, 2)
    (args.output / "meta.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True)
    )
    print(f"[{SOLVER_NAME}] wrote {args.output / 'solution.npz'}"
          + (f"  PSNR={psnr:.2f} dB" if psnr is not None else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
