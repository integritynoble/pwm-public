"""Generate demo datasets from the canonical InverseNet benchmark data.

Replaces the earlier 32×32 synthetic demos with the real 10-scene KAIST-style
CASSI benchmark and the 6-video SCI Video Benchmark for CACTI — the exact
data used in the InverseNet paper (`papers/inversenet/`).

Raw sources (staged in `pwm-team/pwm_product/demos/_raw_src/`, git-ignored):

| Anchor  | Source                                                        | Count |
|---------|---------------------------------------------------------------|-------|
| CASSI   | public/datasets/benchmark/cassi/standard/_raw_src/scene{01..10}.mat + mask.mat | 10    |
| CACTI   | STFormer test_datasets/simulation/{kobe,traffic,runner8,drop8,crash32,aerial32}_cacti.mat | 6     |

Citations (keep in each meta.json):
- CASSI scenes: KAIST-10 hyperspectral set, used by Meng et al. MST / HDNet / DAUHST / CST
- CACTI videos: SCI Video Benchmark, Liu et al. 2019 + Yuan et al. Bell Labs;
  redistributed with every major SCI paper (PnP-FFDNet, STFormer, EfficientSCI).

Layout after generation::

    pwm-team/pwm_product/demos/<anchor>/
        README.md                    # benchmark-level intro + citation
        sample_01/
            snapshot.npz             # solver input (2D coded measurement)
            ground_truth.npz         # full cube / video
            solution.npz             # GAP-TV (CASSI) or PnP-ADMM (CACTI) reconstruction
            snapshot.png             # preview (grayscale)
            ground_truth.png         # preview (mean across bands / middle frame)
            solution.png             # preview of reconstruction
            meta.json                # provenance, shapes, PSNR, SHA-256
        sample_02/  ...  (up to sample_10 for CASSI, sample_06 for CACTI)

Usage::

    python3 scripts/generate_demos.py          # all anchors
    python3 scripts/generate_demos.py --cassi  # CASSI only
    python3 scripts/generate_demos.py --cacti  # CACTI only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path


CASSI_N_ITERS = 15        # GAP-TV iterations; gives ~24-27 dB PSNR at 256x256x28
CACTI_N_ITERS = 12        # PnP-ADMM iterations
PREVIEW_UPSCALE = 1       # images are already 256x256 — large enough

CASSI_SCENES = [f"scene{i:02d}" for i in range(1, 11)]  # 10 KAIST scenes
CACTI_SCENES = [
    # (mat_filename, pretty_name)
    ("kobe_cacti.mat",     "kobe"),
    ("traffic_cacti.mat",  "traffic"),
    ("runner8_cacti.mat",  "runner"),
    ("drop8_cacti.mat",    "drop"),
    ("crash32_cacti.mat",  "crash"),
    ("aerial32_cacti.mat", "aerial"),
]


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("cannot find repo root")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _save_preview(arr, out_path: Path, upscale: int = PREVIEW_UPSCALE) -> None:
    """Save a 2-D numpy array as a grayscale PNG, normalized to 0-255."""
    import numpy as np
    from PIL import Image
    a = arr.astype(np.float32)
    mn, mx = float(a.min()), float(a.max())
    if mx > mn:
        a = (a - mn) / (mx - mn)
    u8 = (a * 255.0).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(u8, mode="L")
    if upscale > 1:
        img = img.resize(
            (u8.shape[1] * upscale, u8.shape[0] * upscale),
            resample=Image.NEAREST,
        )
    img.save(out_path, format="PNG", optimize=True)


def _to_float01(arr):
    """Normalize uint8/uint16/float arrays to float32 in [0, 1]."""
    import numpy as np
    a = arr.astype(np.float32)
    if np.issubdtype(arr.dtype, np.integer):
        info = np.iinfo(arr.dtype)
        a = a / float(info.max)
    return a


def generate_cassi_sample(scene_id: str, raw_dir: Path, out_dir: Path) -> dict:
    """Load a KAIST CASSI scene, apply forward model, run GAP-TV, save everything."""
    import numpy as np
    import scipy.io as sio
    sys.path.insert(0, str(_repo_root() / "pwm-team/pwm_product/reference_solvers/cassi"))
    from cassi_gap_tv import forward, gap_tv, psnr_db

    t0 = time.time()
    img = _to_float01(sio.loadmat(raw_dir / f"{scene_id}.mat")["img"])  # (256, 256, 28)
    mask_2d = _to_float01(sio.loadmat(raw_dir / "mask.mat")["mask"])    # (256, 256)
    N = img.shape[2]
    shifts = np.arange(N, dtype=np.int32)

    y = forward(img, mask_2d, shifts).astype(np.float32)
    x_hat = gap_tv(y, mask_2d, shifts, n_bands=N,
                   n_iters=CASSI_N_ITERS, tv_lambda=0.005, verbose=False)

    xh_n = x_hat / max(x_hat.max(), 1e-8)
    gt_n = img / max(img.max(), 1e-8)
    psnr = round(psnr_db(gt_n, xh_n), 2)

    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_dir / "snapshot.npz", y=y, mask=mask_2d, shifts=shifts)
    np.savez_compressed(out_dir / "ground_truth.npz", x=img.astype(np.float32))
    np.savez_compressed(out_dir / "solution.npz", cube=x_hat.astype(np.float32))

    _save_preview(y, out_dir / "snapshot.png")
    _save_preview(img.mean(axis=2), out_dir / "ground_truth.png")
    _save_preview(x_hat.mean(axis=2), out_dir / "solution.png")

    elapsed = round(time.time() - t0, 1)
    meta = {
        "benchmark": "L3-003 (CASSI) — InverseNet KAIST-10 benchmark",
        "scene_id": scene_id,
        "tier_approx": "T1_nominal",
        "generated_by": "scripts/generate_demos.py",
        "solver_iterations": CASSI_N_ITERS,
        "shape_snapshot": list(y.shape),
        "shape_ground_truth": list(img.shape),
        "shape_solution": list(x_hat.shape),
        "reference_solver": "pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py",
        "reference_solver_psnr_db": psnr,
        "solver_elapsed_sec": elapsed,
        "source_dataset": "KAIST-10 CASSI scenes; see InverseNet paper (papers/inversenet/)",
        "citation": "Meng et al. 2020 + KAIST dataset; used in MST/HDNet/CST/DAUHST benchmarks",
        "how_to_run":
            "python3 pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py "
            f"--input pwm-team/pwm_product/demos/cassi/{out_dir.name} --output /tmp/out",
        "sha256": {
            name: _sha256_file(out_dir / name)
            for name in ("snapshot.npz", "ground_truth.npz", "solution.npz")
        },
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True))
    return {"sample": out_dir.name, "scene": scene_id, "psnr_db": psnr, "seconds": elapsed}


def generate_cacti_sample(mat_name: str, pretty_name: str,
                           raw_dir: Path, out_dir: Path) -> dict:
    """Load one CACTI video, extract first 8-frame block, run PnP-ADMM, save."""
    import numpy as np
    import scipy.io as sio
    sys.path.insert(0, str(_repo_root() / "pwm-team/pwm_product/reference_solvers/cacti"))
    from cacti_pnp_admm import forward, pnp_admm, psnr_db

    t0 = time.time()
    mat = sio.loadmat(raw_dir / mat_name)
    orig = _to_float01(mat["orig"])            # (256, 256, T) — T >= 8
    mask_stack = _to_float01(mat["mask"])      # (256, 256, 8)

    # Transpose to (T, H, W) for the solver
    x_true = orig[:, :, :8].transpose(2, 0, 1).astype(np.float32)  # (8, 256, 256)
    masks  = mask_stack.transpose(2, 0, 1).astype(np.float32)       # (8, 256, 256)

    y = forward(x_true, masks).astype(np.float32)                   # (256, 256)
    x_hat = pnp_admm(y, masks, n_iters=CACTI_N_ITERS,
                     rho=0.05, tv_lambda=0.01, verbose=False)

    xh_n = x_hat / max(x_hat.max(), 1e-8)
    gt_n = x_true / max(x_true.max(), 1e-8)
    psnr = round(psnr_db(gt_n, xh_n), 2)

    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_dir / "snapshot.npz", y=y, masks=masks)
    np.savez_compressed(out_dir / "ground_truth.npz", x=x_true)
    np.savez_compressed(out_dir / "solution.npz", video=x_hat.astype(np.float32))

    _save_preview(y, out_dir / "snapshot.png")
    _save_preview(x_true[4], out_dir / "ground_truth.png")   # middle frame
    _save_preview(x_hat[4], out_dir / "solution.png")        # middle frame

    elapsed = round(time.time() - t0, 1)
    meta = {
        "benchmark": "L3-004 (CACTI) — InverseNet SCI Video Benchmark",
        "scene_id": pretty_name,
        "source_mat": mat_name,
        "tier_approx": "T1_nominal",
        "generated_by": "scripts/generate_demos.py",
        "solver_iterations": CACTI_N_ITERS,
        "shape_snapshot": list(y.shape),
        "shape_ground_truth": list(x_true.shape),
        "shape_solution": list(x_hat.shape),
        "reference_solver": "pwm-team/pwm_product/reference_solvers/cacti/cacti_pnp_admm.py",
        "reference_solver_psnr_db": psnr,
        "solver_elapsed_sec": elapsed,
        "source_dataset":
            "SCI Video Benchmark (Kobe/Traffic/Runner/Drop/Crash/Aerial); "
            "Liu et al. 2019 + Yuan et al. Bell Labs; redistributed in every major "
            "SCI paper (PnP-FFDNet, STFormer, EfficientSCI, DeepBC, BIRNAT).",
        "citation": "Yuan et al. CACTI, Yang et al. SCI Video Benchmark",
        "how_to_run":
            "python3 pwm-team/pwm_product/reference_solvers/cacti/cacti_pnp_admm.py "
            f"--input pwm-team/pwm_product/demos/cacti/{out_dir.name} --output /tmp/out",
        "sha256": {
            name: _sha256_file(out_dir / name)
            for name in ("snapshot.npz", "ground_truth.npz", "solution.npz")
        },
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True))
    return {"sample": out_dir.name, "scene": pretty_name, "psnr_db": psnr, "seconds": elapsed}


def _write_readme(benchmark_dir: Path, anchor: str, results: list[dict]) -> None:
    if anchor == "cassi":
        intro = (
            f"# CASSI — `L3-003` — InverseNet KAIST-10 benchmark\n"
            f"\n"
            f"{len(results)} standard hyperspectral scenes from the KAIST-10 benchmark\n"
            f"(used in MST, HDNet, CST, DAUHST, and the InverseNet paper).\n"
            f"Each 256×256×28 scene is reconstructed from a coded-aperture snapshot\n"
            f"by the reference GAP-TV solver with {CASSI_N_ITERS} iterations.\n"
        )
    else:
        intro = (
            f"# CACTI — `L3-004` — InverseNet SCI Video Benchmark\n"
            f"\n"
            f"{len(results)} standard coded-aperture temporal imaging videos from the SCI\n"
            f"Video Benchmark (Kobe, Traffic, Runner, Drop, Crash, Aerial). Each sample\n"
            f"is one 256×256×8 block reconstructed from a single coded snapshot by the\n"
            f"reference PnP-ADMM solver with {CACTI_N_ITERS} iterations.\n"
        )

    lines = [intro, "", "## Samples", "",
             "| Sample | Scene | Reference PSNR | Solver time |",
             "|--------|-------|----------------|-------------|"]
    for r in results:
        lines.append(f"| `{r['sample']}/` | {r['scene']} | {r['psnr_db']} dB | {r['seconds']}s |")
    lines.extend(["",
        "## Files per sample", "",
        "| File | Purpose |",
        "|------|---------|",
        "| `snapshot.npz`     | Solver input: 2D coded-aperture measurement |",
        "| `ground_truth.npz` | Full hyperspectral cube (CASSI) / 8-frame video (CACTI) |",
        "| `solution.npz`     | Reference-solver reconstruction |",
        "| `snapshot.png`     | Rendered preview of the snapshot |",
        "| `ground_truth.png` | Rendered preview of the target (mean bands / middle frame) |",
        "| `solution.png`     | Rendered preview of the reconstruction |",
        "| `meta.json`        | Provenance, SHA-256 hashes, PSNR |",
        "",
        "## Attribution",
        "",
        "Source datasets are widely-redistributed academic benchmarks used in every",
        "major CASSI/CACTI paper. See each sample's `meta.json` for the canonical",
        "citation. Redistribution here follows standard academic-comparison practice.",
        "",
    ])
    (benchmark_dir / "README.md").write_text("\n".join(lines))


def generate_benchmark(anchor: str, benchmark_dir: Path, raw_dir: Path) -> dict:
    results = []
    if anchor == "cassi":
        for i, scene_id in enumerate(CASSI_SCENES, start=1):
            sample_dir = benchmark_dir / f"sample_{i:02d}"
            results.append(generate_cassi_sample(scene_id, raw_dir, sample_dir))
            print(f"  CASSI {scene_id} → {results[-1]['psnr_db']} dB in {results[-1]['seconds']}s")
    elif anchor == "cacti":
        for i, (mat_name, pretty_name) in enumerate(CACTI_SCENES, start=1):
            sample_dir = benchmark_dir / f"sample_{i:02d}"
            results.append(generate_cacti_sample(mat_name, pretty_name, raw_dir, sample_dir))
            print(f"  CACTI {pretty_name} → {results[-1]['psnr_db']} dB in {results[-1]['seconds']}s")
    else:
        raise ValueError(f"unknown anchor {anchor!r}")

    _write_readme(benchmark_dir, anchor, results)
    return {"anchor": anchor, "samples": results}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cassi", action="store_true", help="Regenerate CASSI only")
    ap.add_argument("--cacti", action="store_true", help="Regenerate CACTI only")
    args = ap.parse_args()

    repo = _repo_root()
    demos_root = repo / "pwm-team" / "pwm_product" / "demos"
    raw_dir = demos_root / "_raw_src"

    if not raw_dir.is_dir():
        print(f"ERROR: raw-source dir missing: {raw_dir}", file=sys.stderr)
        print("Stage the upstream .mat files there before running this script.", file=sys.stderr)
        return 2

    do_cassi = args.cassi or not args.cacti
    do_cacti = args.cacti or not args.cassi

    if do_cassi:
        print("Generating CASSI demos (10 scenes)...")
        generate_benchmark("cassi", demos_root / "cassi", raw_dir)
    if do_cacti:
        print("Generating CACTI demos (6 scenes)...")
        generate_benchmark("cacti", demos_root / "cacti", raw_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
