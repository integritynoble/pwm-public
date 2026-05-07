"""CASSI reference solver — GAP-TV on numpy.

Minimal, self-contained reference implementation of Generalized
Alternating Projection with Total-Variation regularization for Coded
Aperture Snapshot Spectral Imaging. Not a state-of-the-art solver —
PnP-HSICNN gets ~31.8 dB PSNR on L3-003 T1_nominal; this gets ~24-28 dB
depending on tier — but it runs, it's deterministic, and any
competing CP submission can improve on it.

Contract (matches pwm-node mine's subprocess invocation):

    python cassi_gap_tv.py --input <input_dir> --output <output_dir>

Input dir MUST contain:
    snapshot.npz   with keys:
        y:      shape (H, W),      float32 — the coded-aperture snapshot
        mask:   shape (H, W),      float32 (binary 0/1) — coded aperture
        shifts: shape (N_bands,),  int32  — per-band lateral shift in pixels
                 (shift[b] is columns by which band b is displaced)

Output dir gets:
    solution.npz   with key `cube`: shape (H, W, N_bands), float32
    meta.json      solver name, version, iterations, PSNR-on-reference
                   (if ground_truth.npz present in input_dir)

If any input file is missing, the solver generates a **tiny synthetic
problem** so `--input /path/to/empty_dir` still runs end-to-end for CI.
The synthetic problem is NOT the L3-003 benchmark — use it only to
verify the solver binary works.

Forward model:
    y[i,j] = sum_b  mask[i,j] * x[i, j - shifts[b], b]
           (boundaries zero-padded)

The adjoint (backprojection):
    Phi^T(y)[i, j, b] = mask[i, j + shifts[b]] * y[i, j + shifts[b]]

Algorithm (GAP-TV, see Yuan et al. 2016):
    x <- zeros
    Repeat K times:
        x <- x + Phi^T( (y - Phi(x)) / Phi Phi^T 1 )     # GAP step
        x <- TV_denoise(x, tau=lam)                       # prox step
    Return x
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SOLVER_NAME = "cassi_gap_tv"
SOLVER_VERSION = "1.0.0"


def forward(x, mask, shifts):
    """y = sum_b mask * shift(x_b, shifts[b]) — Meng-2020 narrow convention.

    Snapshot has the same width as mask; band content that shifts past the
    edge is truncated. Used when the L3 demo data was generated with the
    in-place dispersion convention.
    """
    import numpy as np
    H, W, N = x.shape
    y = np.zeros((H, W), dtype=x.dtype)
    for b in range(N):
        s = int(shifts[b])
        # Positive shift → move band content to the right in the snapshot.
        if s == 0:
            y += mask * x[:, :, b]
        elif s > 0:
            y[:, s:] += mask[:, s:] * x[:, :-s, b]
        else:
            y[:, :s] += mask[:, :s] * x[:, -s:, b]
    return y


def adjoint(y, mask, shifts, n_bands):
    """Phi^T: scatter y back to each band with the inverse shift (narrow form)."""
    import numpy as np
    H, W = y.shape
    x = np.zeros((H, W, n_bands), dtype=y.dtype)
    masked = mask * y
    for b in range(n_bands):
        s = int(shifts[b])
        if s == 0:
            x[:, :, b] = masked
        elif s > 0:
            x[:, :-s, b] = masked[:, s:]
        else:
            x[:, -s:, b] = masked[:, :s]
    return x


def forward_wide(x, mask, shifts):
    """y = sum_b mask * x_b placed at column shifts[b] — InverseNet wide convention.

    Snapshot width is mask_W + max(shifts) — every band's shifted contribution
    fits without truncation. This is what `regenerate_demos_inversenet.py`
    produces and what the bundled `pwm_product/demos/cassi/sample_*` files use.
    """
    import numpy as np
    H, mask_W, N = x.shape
    snap_W = mask_W + int(shifts[-1])
    y = np.zeros((H, snap_W), dtype=x.dtype)
    for b in range(N):
        s = int(shifts[b])
        y[:, s:s + mask_W] += mask * x[:, :, b]
    return y


def adjoint_wide(y_wide, mask, shifts, n_bands):
    """Phi^T for the InverseNet wide convention — slice each band's window back."""
    import numpy as np
    H, mask_W = mask.shape
    x = np.zeros((H, mask_W, n_bands), dtype=y_wide.dtype)
    for b in range(n_bands):
        s = int(shifts[b])
        x[:, :, b] = mask * y_wide[:, s:s + mask_W]
    return x


def gap_scale(mask, shifts, n_bands, wide: bool = False):
    """Phi Phi^T 1 — pixel-wise normalization for the GAP residual step."""
    import numpy as np
    fwd = forward_wide if wide else forward
    adj = adjoint_wide if wide else adjoint
    H, mask_W = mask.shape
    snap_W = mask_W + int(shifts[-1]) if wide else mask_W
    ones_snapshot = np.ones((H, snap_W), dtype=mask.dtype)
    back = adj(ones_snapshot, mask, shifts, n_bands)
    scale = fwd(back, mask, shifts)
    # avoid divide-by-zero
    scale = np.where(scale > 1e-8, scale, 1.0)
    return scale


def tv_prox_2d(u, tau, n_steps=10, step=0.2):
    """Isotropic 2D total-variation prox via Chambolle's dual iteration.

    Applied per-band (2D slice), not along the spectral axis. Cheap
    denoiser for GAP-TV regularization — nowhere near PnP-HSICNN quality
    but fine as a demo floor. `step` < 1/8 is theoretically required for
    convergence; 0.2 works well in practice at the usual 5-10 iterations.
    """
    import numpy as np
    px = np.zeros_like(u)
    py = np.zeros_like(u)
    for _ in range(n_steps):
        # Divergence of (px, py) — adjoint of the forward-diff gradient.
        div = np.zeros_like(u)
        div[:, 1:]  += px[:, 1:] - px[:, :-1]
        div[:, 0]   += px[:, 0]
        div[1:, :]  += py[1:, :] - py[:-1, :]
        div[0, :]   += py[0, :]

        tmp = u - tau * div
        # Forward difference of tmp
        gx = np.zeros_like(tmp); gx[:, :-1] = tmp[:, 1:] - tmp[:, :-1]
        gy = np.zeros_like(tmp); gy[:-1, :] = tmp[1:, :] - tmp[:-1, :]

        # Semi-implicit update + projection onto unit L2 ball (scaled by tau).
        px_new = px + step * gx
        py_new = py + step * gy
        norm = np.maximum(1.0, np.sqrt(px_new * px_new + py_new * py_new) / tau)
        px = px_new / norm
        py = py_new / norm

    # Reconstruct denoised signal from the final duals.
    div = np.zeros_like(u)
    div[:, 1:]  += px[:, 1:] - px[:, :-1]
    div[:, 0]   += px[:, 0]
    div[1:, :]  += py[1:, :] - py[:-1, :]
    div[0, :]   += py[0, :]
    return u - tau * div


def tv_denoise_cube(x, tau=0.01, n_inner=5):
    """Apply 2D TV prox per band."""
    import numpy as np
    out = np.empty_like(x)
    for b in range(x.shape[2]):
        out[:, :, b] = tv_prox_2d(x[:, :, b], tau=tau, n_steps=n_inner)
    return out


def gap_tv(y, mask, shifts, n_bands, n_iters=30, tv_lambda=0.005,
           tv_decay=0.98, verbose=False):
    """GAP-TV reconstruction.

    Auto-detects the snapshot convention: if y.shape[1] > mask.shape[1] the
    InverseNet wide form is in use (regenerate_demos_inversenet.py output);
    otherwise the Meng-2020 narrow form. Both give the same reconstruction
    quality on synthetic data; the wide form is more accurate near the
    snapshot edges where the narrow form truncates.
    """
    import numpy as np
    wide = y.shape[1] > mask.shape[1]
    fwd = forward_wide if wide else forward
    adj = adjoint_wide if wide else adjoint
    scale = gap_scale(mask, shifts, n_bands, wide=wide)
    # Warm start: one back-projection, scale-corrected so forward(x) ~ y.
    x = adj(y, mask, shifts, n_bands) / n_bands

    lam = tv_lambda
    for k in range(n_iters):
        y_hat = fwd(x, mask, shifts)
        residual = (y - y_hat) / scale
        x = x + adj(residual, mask, shifts, n_bands)
        x = np.clip(x, 0.0, None)            # non-negativity
        x = tv_denoise_cube(x, tau=lam)
        lam *= tv_decay
        if verbose and (k == 0 or (k + 1) % 5 == 0 or k + 1 == n_iters):
            data_residual = float(np.linalg.norm(y - fwd(x, mask, shifts)))
            print(f"  iter {k + 1:3d}/{n_iters}  ||r||_2 = {data_residual:.4f}  conv={'wide' if wide else 'narrow'}")
    return x


def generate_synthetic_problem(H=32, W=32, N=8, seed=0):
    """Tiny synthetic CASSI problem for CI / smoke testing."""
    import numpy as np
    rng = np.random.default_rng(seed)
    # Ground-truth HSI: a few Gaussian blobs per band
    x_true = np.zeros((H, W, N), dtype=np.float32)
    for b in range(N):
        cx = rng.integers(W // 4, 3 * W // 4)
        cy = rng.integers(H // 4, 3 * H // 4)
        yy, xx = np.mgrid[0:H, 0:W]
        x_true[:, :, b] = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * (W / 6) ** 2))
    # Mask: binary 0/1 with ~50% density
    mask = (rng.uniform(size=(H, W)) > 0.5).astype(np.float32)
    # Shifts: 0, 1, 2, ..., N-1 pixels (simple linear dispersion)
    shifts = np.arange(N, dtype=np.int32)
    # Snapshot with a little noise
    y_clean = forward(x_true, mask, shifts)
    noise = rng.normal(scale=0.02 * y_clean.max(), size=y_clean.shape).astype(np.float32)
    y = y_clean + noise
    return {"x_true": x_true, "mask": mask, "shifts": shifts, "y": y.astype(np.float32)}


def psnr_db(x_true, x_hat):
    """PSNR between ground truth and reconstruction (both in same scale)."""
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
    ap.add_argument("--iters", type=int, default=30, help="GAP iterations")
    ap.add_argument("--tv-lambda", type=float, default=0.005,
                    help="Initial TV prox weight (decays each iteration)")
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
        mask = data["mask"].astype(np.float32)
        # Accept either explicit `shifts` (Meng-2020 form) or scalar `step`
        # (InverseNet form); compute shifts from step + snapshot shape if needed.
        if "shifts" in data:
            shifts = data["shifts"].astype(np.int32)
        elif "step" in data:
            step = int(data["step"])
            n_bands = (int(y.shape[1]) - int(mask.shape[1])) // step + 1 if y.shape[1] > mask.shape[1] else 28
            shifts = np.array([b * step for b in range(n_bands)], dtype=np.int32)
        else:
            raise KeyError(
                f"snapshot.npz must contain either 'shifts' (int array) or 'step' (scalar). "
                f"Got keys: {list(data.keys())}"
            )
        source = "input"
    else:
        print(f"[{SOLVER_NAME}] no snapshot.npz — generating synthetic problem for smoke test")
        synth = generate_synthetic_problem()
        y, mask, shifts = synth["y"], synth["mask"], synth["shifts"]
        source = "synthetic"
        # Also persist the ground truth for PSNR scoring below
        gt = synth["x_true"]
        np.savez_compressed(args.output / "synthetic_ground_truth.npz", x=gt)

    n_bands = len(shifts)
    if args.verbose:
        print(f"[{SOLVER_NAME}] H={y.shape[0]} W={y.shape[1]} bands={n_bands} source={source}")

    x_hat = gap_tv(y, mask, shifts, n_bands,
                   n_iters=args.iters, tv_lambda=args.tv_lambda,
                   verbose=args.verbose)

    # Optional PSNR against ground truth (for demo / synthetic runs)
    psnr = None
    if gt_path.is_file():
        gt = np.load(gt_path)["x"].astype(np.float32)
        # Scale-match — competing solvers are evaluated after normalization
        x_hat_norm = x_hat / max(x_hat.max(), 1e-8)
        gt_norm = gt / max(gt.max(), 1e-8)
        psnr = psnr_db(gt_norm, x_hat_norm)
    elif source == "synthetic":
        gt = synth["x_true"]
        x_hat_norm = x_hat / max(x_hat.max(), 1e-8)
        gt_norm = gt / max(gt.max(), 1e-8)
        psnr = psnr_db(gt_norm, x_hat_norm)

    np.savez_compressed(args.output / "solution.npz", cube=x_hat.astype(np.float32))

    meta = {
        "solver": SOLVER_NAME,
        "version": SOLVER_VERSION,
        "benchmark": "L3-003 (CASSI)",
        "algorithm": "GAP-TV",
        "iters": args.iters,
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
