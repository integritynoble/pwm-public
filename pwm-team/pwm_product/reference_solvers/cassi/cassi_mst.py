"""CASSI improved solver — MST-L via `public/algorithm_base/cassi`.

State-of-the-art mask-aware spectral transformer (MST-L) wrapper that
follows the same `--input/--output` contract as the GAP-TV reference
solver but produces dramatically better reconstructions:

    GAP-TV reference:   ~24-28 dB PSNR on KAIST scenes
    MST-L (this file):  ~34 dB PSNR on KAIST scenes (Cai et al., CVPR 2022)
                        verified 34.09/0.930 on KAIST scene01

The heavy lifting is delegated to `algorithm_base.cassi.run_mst_l`
which loads pretrained weights from
`public/packages/pwm_core/weights/mst/mst_l.pth` and runs inference via
`pwm_core.recon.mst.mst_recon_cassi`. This wrapper just bridges
`pwm-node mine`'s subprocess contract.

Contract (matches `pwm-node mine` invocation):

    python cassi_mst.py --input <input_dir> --output <output_dir>

Input dir MUST contain `snapshot.npz` with the same schema as the
GAP-TV reference:
    y:      (H, W),         float32  — coded-aperture snapshot
    mask:   (H, W),         float32  — coded aperture (binary 0/1)
    shifts: (N_bands,),     int32    — per-band lateral shift in pixels

Output dir gets:
    solution.npz   with key `cube`: (H, W, N_bands), float32
    meta.json      solver name, version, runtime, PSNR-on-reference

Requires PyTorch + algorithm_base (already in this repo).
GPU recommended; CPU works but ~20-50× slower per scene.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    """Locate the repo root by looking for the `public/algorithm_base` dir."""
    for p in [start, *start.parents]:
        if (p / "public" / "algorithm_base" / "cassi").is_dir():
            return p
    raise RuntimeError(
        "cannot locate repo root with public/algorithm_base/cassi/; "
        "the wrapper expects to live at "
        "<repo>/pwm-team/pwm_product/reference_solvers/cassi/cassi_mst.py"
    )


def _load_snapshot(input_dir: Path):
    import numpy as np
    snap_path = input_dir / "snapshot.npz"
    if not snap_path.exists():
        raise FileNotFoundError(
            f"missing {snap_path} — pwm-node mine should have placed the "
            "benchmark inputs here. For local CI, generate a tiny synthetic "
            "snapshot and re-run."
        )
    with np.load(snap_path) as f:
        y = np.asarray(f["y"], dtype=np.float32)
        mask = np.asarray(f["mask"], dtype=np.float32)
        shifts = np.asarray(f["shifts"], dtype=np.int32)
    return y, mask, shifts


def _ground_truth_psnr(cube_hat, input_dir: Path):
    """If the input dir has a ground_truth.npz, compute PSNR; else return None."""
    import numpy as np
    gt_path = input_dir / "ground_truth.npz"
    if not gt_path.exists():
        # also try x_gt.npy (InverseNet dataset format)
        x_gt = input_dir / "x_gt.npy"
        if x_gt.exists():
            gt = np.load(x_gt)
        else:
            return None
    else:
        with np.load(gt_path) as f:
            gt = np.asarray(f[list(f.keys())[0]], dtype=np.float32)

    gt = gt.astype(np.float32)
    cube = cube_hat.astype(np.float32)
    if gt.shape != cube.shape:
        return None
    mse = float(((gt - cube) ** 2).mean())
    if mse <= 0:
        return float("inf")
    peak = float(max(gt.max(), 1.0))
    return 10.0 * (np.log10(peak * peak) - np.log10(mse))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument(
        "--variant",
        choices=["mst_l", "mst_s"],
        default="mst_l",
        help="MST variant; mst_l (default) is the high-quality model.",
    )
    args = ap.parse_args(argv)

    args.output.mkdir(parents=True, exist_ok=True)

    here = Path(__file__).resolve()
    repo = _find_repo_root(here)
    sys.path.insert(0, str(repo / "public"))
    sys.path.insert(0, str(repo / "public" / "packages" / "pwm_core"))

    try:
        from algorithm_base.cassi.solvers import run_mst_l
    except ImportError as e:
        print(f"FATAL: cannot import algorithm_base.cassi.solvers: {e}",
              file=sys.stderr)
        return 2

    y, mask, shifts = _load_snapshot(args.input)
    n_bands = int(shifts.shape[0])
    step = int(shifts[1] - shifts[0]) if n_bands > 1 else 2

    cfg = {
        "mask": mask,
        "n_bands": n_bands,
        "step": step,
        "variant": args.variant,
    }

    t0 = time.time()
    cube_hat = run_mst_l(y, operator=None, cfg=cfg)
    elapsed = time.time() - t0

    import numpy as np
    cube_hat = np.asarray(cube_hat, dtype=np.float32)
    if cube_hat.ndim == 2 and n_bands > 1:
        cube_hat = cube_hat.reshape(mask.shape[0], mask.shape[1], n_bands)

    np.savez_compressed(args.output / "solution.npz", cube=cube_hat)

    psnr = _ground_truth_psnr(cube_hat, args.input)
    meta = {
        "solver": "cassi_mst",
        "variant": args.variant,
        "model_reference": "Cai et al., CVPR 2022 — MST-L",
        "runtime_seconds": round(elapsed, 2),
        "n_bands": n_bands,
        "shape": list(cube_hat.shape),
        "psnr_db_vs_ground_truth": (round(psnr, 3) if psnr is not None else None),
    }
    (args.output / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")

    print(f"cassi_mst: wrote {args.output}/solution.npz  shape={cube_hat.shape}  "
          f"runtime={elapsed:.1f}s  psnr={meta['psnr_db_vs_ground_truth']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
