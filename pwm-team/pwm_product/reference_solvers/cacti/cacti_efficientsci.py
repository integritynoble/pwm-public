"""CACTI improved solver — EfficientSCI via `public/algorithm_base/cacti`.

Director note (2026-05-02): the brief was "use efficientnet to improve
CACTI." EfficientNet (Tan & Le, 2019) is an image-classification
backbone — not directly applicable to coded-aperture compressive
*temporal* video reconstruction. The closest match in the existing
PWM algorithm catalog (already wired in `algorithm_base/cacti`) is
**EfficientSCI** (Wang et al., CVPR 2023), the SOTA efficient
spatial-temporal compressive imaging network. This wrapper uses
EfficientSCI as the "best_quality" solver per the registry.

    PnP-ADMM reference (current floor):  ~22-26 dB PSNR
    EfficientSCI (this file):            ~33-35 dB PSNR (Wang CVPR 2023)

The heavy lifting is delegated to
`algorithm_base.cacti.run_best_quality` which routes to
`pwm_core.recon.efficientsci.run_efficientsci`. Pretrained weights
load from `public/packages/pwm_core/weights/efficientsci/efficientsci_<variant>.pth`
(if present). If weights are missing the wrapper reports a clear
error rather than silently producing garbage.

Contract (matches `pwm-node mine` invocation):

    python cacti_efficientsci.py --input <input_dir> --output <output_dir>

Input dir MUST contain `snapshot.npz` with the same schema as the
PnP-ADMM reference:
    y:     (H, W),         float32  — compressive snapshot
    masks: (T, H, W),      float32  — per-frame masks (binary 0/1)

Output dir gets:
    solution.npz   with key `video`: (T, H, W), float32
    meta.json      solver name, variant, runtime, PSNR-on-reference

Requires PyTorch + EfficientSCI weights.
GPU recommended; CPU works but ~10-30× slower per scene.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "public" / "algorithm_base" / "cacti").is_dir():
            return p
    raise RuntimeError(
        "cannot locate repo root with public/algorithm_base/cacti/; "
        "the wrapper expects to live at "
        "<repo>/pwm-team/pwm_product/reference_solvers/cacti/cacti_efficientsci.py"
    )


def _load_snapshot(input_dir: Path):
    import numpy as np
    snap_path = input_dir / "snapshot.npz"
    if not snap_path.exists():
        raise FileNotFoundError(
            f"missing {snap_path} — pwm-node mine should have placed the "
            "benchmark inputs here."
        )
    with np.load(snap_path) as f:
        y = np.asarray(f["y"], dtype=np.float32)
        masks = np.asarray(f["masks"], dtype=np.float32)
    return y, masks


def _ground_truth_psnr(video_hat, input_dir: Path):
    import numpy as np
    gt_path = input_dir / "ground_truth.npz"
    if not gt_path.exists():
        x_gt = input_dir / "x_gt.npy"
        if x_gt.exists():
            gt = np.load(x_gt)
        else:
            return None
    else:
        with np.load(gt_path) as f:
            gt = np.asarray(f[list(f.keys())[0]], dtype=np.float32)

    gt = gt.astype(np.float32)
    video = video_hat.astype(np.float32)
    if gt.shape != video.shape:
        return None
    mse = float(((gt - video) ** 2).mean())
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
        default="base",
        help="EfficientSCI variant; default 'base' (the published model).",
    )
    args = ap.parse_args(argv)

    args.output.mkdir(parents=True, exist_ok=True)

    here = Path(__file__).resolve()
    repo = _find_repo_root(here)
    sys.path.insert(0, str(repo / "public"))
    sys.path.insert(0, str(repo / "public" / "packages" / "pwm_core"))

    # Use the canonical InverseNet-paper-validated EfficientSCI integration in
    # `pwm_core.recon.cacti_solvers.efficient_sci_cacti`. This loads the
    # original Wang et al. CVPR 2023 model from `public/repos/EfficientSCI/`
    # with weights at `public/checkpoint/EfficientSCI/efficientsci_base.pth`,
    # producing ~35-37 dB on the SCI Video Benchmark. The earlier route via
    # `algorithm_base.cacti.solvers.run_best_quality` → `pwm_core.recon.efficientsci`
    # was a parallel rewrite that didn't reach paper-grade PSNR (~4 dB) due
    # to input-normalization mismatches.
    try:
        from pwm_core.recon.cacti_solvers import efficient_sci_cacti
    except ImportError as e:
        print(f"FATAL: cannot import pwm_core.recon.cacti_solvers: {e}",
              file=sys.stderr)
        return 2

    import numpy as np
    y, masks = _load_snapshot(args.input)
    n_frames = int(masks.shape[0])

    # `efficient_sci_cacti` expects mask shape (H, W, T); InverseNet/demo
    # snapshots store masks as (T, H, W).
    mask_HWT = np.transpose(masks, (1, 2, 0)).astype(np.float32)

    t0 = time.time()
    try:
        video_HWT = efficient_sci_cacti(
            y.astype(np.float32),
            mask_HWT,
            device="cpu",
            variant=args.variant,
        )
    except FileNotFoundError as e:
        print(
            "FATAL: EfficientSCI pretrained weights missing. Expected at:\n"
            f"  public/checkpoint/EfficientSCI/efficientsci_{args.variant}.pth\n"
            f"Underlying error: {e}",
            file=sys.stderr,
        )
        return 3
    elapsed = time.time() - t0

    # `efficient_sci_cacti` returns (H, W, T); transpose back to the wrapper's
    # documented (T, H, W) so the saved solution matches downstream readers.
    video_hat = np.transpose(video_HWT, (2, 0, 1)).astype(np.float32)
    np.savez_compressed(args.output / "solution.npz", video=video_hat)

    psnr = _ground_truth_psnr(video_hat, args.input)
    meta = {
        "solver": "cacti_efficientsci",
        "variant": args.variant,
        "model_reference": "Wang et al., CVPR 2023 — EfficientSCI",
        "runtime_seconds": round(elapsed, 2),
        "n_frames": n_frames,
        "shape": list(video_hat.shape),
        "psnr_db_vs_ground_truth": (round(psnr, 3) if psnr is not None else None),
    }
    (args.output / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")

    print(f"cacti_efficientsci: wrote {args.output}/solution.npz  "
          f"shape={video_hat.shape}  runtime={elapsed:.1f}s  "
          f"psnr={meta['psnr_db_vs_ground_truth']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
