"""Regenerate every CASSI + CACTI demo with the InverseNet paper's exact recipe.

This replaces the legacy `solution.npz` (and, for CACTI, also
`snapshot.npz` and `ground_truth.npz`) under
`pwm-team/pwm_product/demos/{cassi,cacti}/sample_*/` with outputs
that match the InverseNet paper's GAP-TV Scenario I numbers when
graded with the paper's PSNR formula (clip both arrays to [0, 1],
peak = 1).

Why this exists (root-cause review of the legacy demos):

  CASSI:
    - Old `generate_demos.py::generate_cassi_sample` used step=1
      dispersion + iter=15 + tv_lambda=0.005. Public solver (and
      paper) uses step=2 + iter=100 + lam=0.1.
    - Result: legacy demos can't clear 24 dB. New regen matches
      paper claim 24.34 ± 1.90 dB.

  CACTI:
    - Old `generate_demos.py::generate_cacti_sample` saved
      ground_truth.npz['x'] in [0, 255] (raw .mat scale) and the
      solver was fed those un-normalized inputs. solution.npz ends
      up dim ([0, 5.7-ish]).
    - New regen normalizes orig + mask to [0, 1] before forward +
      reconstruction; ground_truth.npz['x'] is also stored in [0, 1]
      (matching the InverseNet paper's data convention). Test PSNR
      now compares like-for-like.

This script imports the same `pwm_core.recon` solvers the InverseNet
paper uses (per `papers/inversenet/scripts/validate_cassi_inversenet.py`'s
`reconstruct_gap_tv`).

Usage:
    python scripts/regenerate_demos_inversenet.py            # CASSI + CACTI all
    python scripts/regenerate_demos_inversenet.py --only cassi
    python scripts/regenerate_demos_inversenet.py --only cacti
    python scripts/regenerate_demos_inversenet.py --dry-run  # report PSNRs without overwriting

Estimated runtime (CPU): ~28 s/sample CASSI × 10 + ~3 s/sample CACTI × 6 ≈ 5 min total.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "public"))
sys.path.insert(0, str(REPO / "public/packages/pwm_core"))

DEMOS_ROOT = REPO / "pwm-team/pwm_product/demos"
RAW_DIR = DEMOS_ROOT / "_raw_src"

CASSI_SCENES = [f"scene{i:02d}" for i in range(1, 11)]
CACTI_SCENES = [
    ("kobe_cacti.mat", "kobe"),
    ("traffic_cacti.mat", "traffic"),
    ("runner8_cacti.mat", "runner"),
    ("drop8_cacti.mat", "drop"),
    ("crash32_cacti.mat", "crash"),
    ("aerial32_cacti.mat", "aerial"),
]

CASSI_ITERS = 100
CASSI_LAM = 0.1
CASSI_STEP = 2
CACTI_ITERS = 100
CACTI_TV_WEIGHT = 0.1


def to_float01(arr: np.ndarray) -> np.ndarray:
    """Normalize an array to [0, 1] using its observed max.

    NOT `array / dtype_max` — that breaks the CACTI mask which is
    stored as uint8 with values 0/1 (max=1, NOT 255). Dividing
    uint8(0/1) by 255 gives [0, 0.0039] — the exact original
    `generate_demos.py` bug.

    Heuristic: if the observed max is > 1.5 (e.g., float orig in
    [0, 255]), divide by max to bring into [0, 1]. Otherwise the
    array is already in [0, 1] and we leave it alone.
    """
    a = arr.astype(np.float32)
    m = float(a.max())
    if m > 1.5:
        return a / max(m, 1e-8)
    return a


def psnr(gt: np.ndarray, sol: np.ndarray) -> float:
    """InverseNet paper compute_psnr: clip both to [0,1], peak=1."""
    gt = np.clip(gt.astype(np.float64), 0.0, 1.0)
    sol = np.clip(sol.astype(np.float64), 0.0, 1.0)
    mse = float(np.mean((gt - sol) ** 2))
    if mse < 1e-10:
        return 100.0
    return float(10.0 * np.log10(1.0 / mse))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save_preview_grayscale(arr2d: np.ndarray, path: Path):
    from PIL import Image
    a = np.asarray(arr2d, dtype=np.float64)
    a = a - a.min()
    if a.max() > 0:
        a = a / a.max()
    Image.fromarray((a * 255.0).clip(0, 255).astype(np.uint8)).save(path)


def regen_cassi(scene_id: str, dry_run: bool) -> dict:
    import scipy.io as sio
    from pwm_core.recon.gap_tv import gap_tv_cassi

    sample_idx = int(scene_id.replace("scene", ""))
    sample_dir = DEMOS_ROOT / "cassi" / f"sample_{sample_idx:02d}"
    if not sample_dir.is_dir():
        raise RuntimeError(f"sample dir missing: {sample_dir}")

    img = to_float01(sio.loadmat(RAW_DIR / f"{scene_id}.mat")["img"])
    mask_2d = to_float01(sio.loadmat(RAW_DIR / "mask.mat")["mask"])
    H, W, N = img.shape

    # Forward with step=2 dispersion (paper convention).
    W_meas = W + (N - 1) * CASSI_STEP
    y = np.zeros((H, W_meas), dtype=np.float32)
    for k in range(N):
        y[:, k * CASSI_STEP:k * CASSI_STEP + W] += mask_2d * img[:, :, k]

    t0 = time.time()
    x_hat = gap_tv_cassi(
        y, mask_2d, n_bands=N,
        iterations=CASSI_ITERS, lam=CASSI_LAM, step=CASSI_STEP, tv_iter=5,
    ).astype(np.float32)
    elapsed = round(time.time() - t0, 1)
    db = round(psnr(img, x_hat), 2)

    if not dry_run:
        np.savez_compressed(sample_dir / "snapshot.npz", y=y, mask=mask_2d, step=np.int32(CASSI_STEP))
        np.savez_compressed(sample_dir / "ground_truth.npz", x=img.astype(np.float32))
        np.savez_compressed(sample_dir / "solution.npz", cube=x_hat)
        save_preview_grayscale(y, sample_dir / "snapshot.png")
        save_preview_grayscale(img.mean(axis=2), sample_dir / "ground_truth.png")
        save_preview_grayscale(np.clip(x_hat, 0, 1).mean(axis=2), sample_dir / "solution.png")
        meta = {
            "benchmark": "L3-003 (CASSI) — InverseNet KAIST-10 benchmark",
            "scene_id": scene_id,
            "tier_approx": "T1_nominal",
            "generated_by": "scripts/regenerate_demos_inversenet.py",
            "solver": "pwm_core.recon.gap_tv.gap_tv_cassi",
            "solver_iterations": CASSI_ITERS,
            "tv_lambda": CASSI_LAM,
            "dispersion_step_px": CASSI_STEP,
            "shape_snapshot": list(y.shape),
            "shape_ground_truth": list(img.shape),
            "shape_solution": list(x_hat.shape),
            "psnr_convention": "InverseNet paper compute_psnr: clip both to [0,1], peak=1",
            "reference_solver_psnr_db": db,
            "solver_elapsed_sec": elapsed,
            "source_dataset": "KAIST-10 hyperspectral CASSI scenes; InverseNet paper KAIST split",
            "citation": "Meng et al. 2020 + KAIST dataset; used in MST/HDNet/CST/DAUHST benchmarks",
            "how_to_run": (
                "python3 scripts/regenerate_demos_inversenet.py --only cassi "
                "(uses pwm_core.recon.gap_tv.gap_tv_cassi)"
            ),
            "sha256": {
                name: sha256_file(sample_dir / name)
                for name in ("snapshot.npz", "ground_truth.npz", "solution.npz")
            },
        }
        (sample_dir / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True))

    return {"sample": sample_dir.name, "scene": scene_id, "psnr_db": db, "seconds": elapsed}


def regen_cacti(mat_name: str, scene_id: str, sample_idx: int, dry_run: bool) -> dict:
    import scipy.io as sio
    from pwm_core.recon.cacti_solvers import gap_tv_cacti

    sample_dir = DEMOS_ROOT / "cacti" / f"sample_{sample_idx:02d}"
    if not sample_dir.is_dir():
        raise RuntimeError(f"sample dir missing: {sample_dir}")

    mat = sio.loadmat(RAW_DIR / mat_name)
    orig = to_float01(mat["orig"])  # (H, W, T)
    mask_stack = to_float01(mat["mask"])  # (H, W, 8)

    # Slice to first 8 frames.
    x_true = orig[:, :, :8].astype(np.float32)  # (H, W, 8) — already [0, 1]
    masks = mask_stack[:, :, :8].astype(np.float32)  # (H, W, 8) — already [0, 1]

    # Forward
    y = np.sum(masks * x_true, axis=2).astype(np.float32)

    t0 = time.time()
    x_hat = gap_tv_cacti(
        y, masks,
        iterations=CACTI_ITERS, tv_weight=CACTI_TV_WEIGHT, tv_iter=5,
    ).astype(np.float32)
    elapsed = round(time.time() - t0, 1)
    db = round(psnr(x_true, x_hat), 2)

    if not dry_run:
        # Store with paper's (T, H, W) convention to match the existing ground_truth schema.
        x_true_THW = np.transpose(x_true, (2, 0, 1)).astype(np.float32)
        x_hat_THW = np.transpose(x_hat, (2, 0, 1)).astype(np.float32)
        masks_THW = np.transpose(masks, (2, 0, 1)).astype(np.float32)
        np.savez_compressed(sample_dir / "snapshot.npz", y=y, masks=masks_THW)
        np.savez_compressed(sample_dir / "ground_truth.npz", x=x_true_THW)
        np.savez_compressed(sample_dir / "solution.npz", video=x_hat_THW)
        save_preview_grayscale(y, sample_dir / "snapshot.png")
        save_preview_grayscale(x_true_THW[4], sample_dir / "ground_truth.png")
        save_preview_grayscale(np.clip(x_hat_THW[4], 0, 1), sample_dir / "solution.png")
        meta = {
            "benchmark": "L3-004 (CACTI) — InverseNet SCI Video Benchmark",
            "scene_id": scene_id,
            "source_mat": mat_name,
            "tier_approx": "T1_nominal",
            "generated_by": "scripts/regenerate_demos_inversenet.py",
            "solver": "pwm_core.recon.cacti_solvers.gap_tv_cacti",
            "solver_iterations": CACTI_ITERS,
            "tv_weight": CACTI_TV_WEIGHT,
            "shape_snapshot": list(y.shape),
            "shape_ground_truth": list(x_true_THW.shape),
            "shape_solution": list(x_hat_THW.shape),
            "data_range": "[0, 1] for both ground_truth and solution (normalized from raw .mat)",
            "psnr_convention": "InverseNet paper compute_psnr: clip both to [0,1], peak=1",
            "reference_solver_psnr_db": db,
            "solver_elapsed_sec": elapsed,
            "source_dataset": (
                "SCI Video Benchmark (Kobe/Traffic/Runner/Drop/Crash/Aerial); "
                "Liu et al. 2019 + Yuan et al. Bell Labs"
            ),
            "citation": "Yuan et al. CACTI; Yang et al. SCI Video Benchmark",
            "how_to_run": (
                "python3 scripts/regenerate_demos_inversenet.py --only cacti "
                "(uses pwm_core.recon.cacti_solvers.gap_tv_cacti)"
            ),
            "sha256": {
                name: sha256_file(sample_dir / name)
                for name in ("snapshot.npz", "ground_truth.npz", "solution.npz")
            },
        }
        (sample_dir / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True))

    return {"sample": sample_dir.name, "scene": scene_id, "psnr_db": db, "seconds": elapsed}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--only", choices=["cassi", "cacti"], help="regenerate only one anchor")
    ap.add_argument("--dry-run", action="store_true", help="compute PSNRs without overwriting files")
    args = ap.parse_args()

    do_cassi = args.only != "cacti"
    do_cacti = args.only != "cassi"
    overall_pass = True

    if do_cassi:
        print("=" * 60)
        print(f"CASSI L3-003 — InverseNet GAP-TV (iter={CASSI_ITERS}, lam={CASSI_LAM}, step={CASSI_STEP})")
        print("=" * 60)
        rows = [regen_cassi(s, args.dry_run) for s in CASSI_SCENES]
        psnrs = [r["psnr_db"] for r in rows]
        avg = np.mean(psnrs)
        for r in rows:
            mark = "PASS" if r["psnr_db"] >= 24.0 else "fail"
            print(f"  [{mark}] {r['sample']} ({r['scene']}): {r['psnr_db']:5.2f} dB  ({r['seconds']:5.1f}s)")
        print(f"  avg = {avg:.2f} dB ({len(rows)} samples; target >= 24)")
        overall_pass = overall_pass and (avg >= 24.0)

    if do_cacti:
        print()
        print("=" * 60)
        print(f"CACTI L3-004 — InverseNet GAP-TV (iter={CACTI_ITERS}, tv_weight={CACTI_TV_WEIGHT})")
        print("=" * 60)
        rows = [regen_cacti(m, n, i + 1, args.dry_run)
                for i, (m, n) in enumerate(CACTI_SCENES)]
        psnrs = [r["psnr_db"] for r in rows]
        avg = np.mean(psnrs)
        for r in rows:
            mark = "PASS" if r["psnr_db"] >= 24.0 else "fail"
            print(f"  [{mark}] {r['sample']} ({r['scene']}): {r['psnr_db']:5.2f} dB  ({r['seconds']:5.1f}s)")
        print(f"  avg = {avg:.2f} dB ({len(rows)} samples; target >= 24)")
        overall_pass = overall_pass and (avg >= 24.0)

    if args.dry_run:
        print("\n(dry-run — no files written)")
    else:
        print("\nRegenerated demos written to pwm-team/pwm_product/demos/{cassi,cacti}/sample_*/")
        print("Run `pytest pwm-team/pwm_product/tests/test_cassi_quality.py "
              "pwm-team/pwm_product/tests/test_cacti_quality.py -v` to confirm.")

    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
