"""Generate canonical CASSI + CACTI demo datasets (2 samples per benchmark).

Each benchmark ships TWO independent sample instances (different seeds)
so users can see that results aren't cherry-picked. Each sample has both
the .npz data files (for solver input / scoring) AND small pre-rendered
PNG previews (for the web explorer to display without a Python runtime).

Layout after generation::

    pwm-team/pwm_product/demos/<name>/
        README.md                    # benchmark-level intro
        sample_01/
            snapshot.npz
            ground_truth.npz
            solution.npz             # reference solver output
            snapshot.png             # preview (grayscale 2D)
            ground_truth.png         # preview (grayscale; mean across bands/frames)
            meta.json                # provenance, shapes, PSNR, SHA-256
        sample_02/
            ... same structure, different seed

Usage::

    python3 scripts/generate_demos.py          # all benchmarks
    python3 scripts/generate_demos.py --cassi  # CASSI only
    python3 scripts/generate_demos.py --check  # dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


BASE_SEED = 42            # sample_01 uses this; sample_02 uses BASE_SEED+1; etc.
N_SAMPLES = 2
PREVIEW_UPSCALE = 8       # 32x32 -> 256x256 PNG (PIL NEAREST)


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("cannot find repo root")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _save_preview(arr, out_path: Path, upscale: int = PREVIEW_UPSCALE) -> None:
    """Save a 2-D numpy array as a grayscale PNG, normalized to 0-255 and upscaled."""
    import numpy as np
    from PIL import Image
    a = arr.astype(np.float32)
    mn, mx = float(a.min()), float(a.max())
    if mx > mn:
        a = (a - mn) / (mx - mn)
    u8 = (a * 255.0).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(u8, mode="L")
    if upscale > 1:
        img = img.resize((u8.shape[1] * upscale, u8.shape[0] * upscale),
                         resample=Image.NEAREST)
    img.save(out_path, format="PNG", optimize=True)


def generate_cassi_sample(out_dir: Path, seed: int) -> dict:
    """Write one CASSI sample (snapshot+gt+solution+previews+meta) at out_dir."""
    import numpy as np
    sys.path.insert(0, str(_repo_root() / "pwm-team/pwm_product/reference_solvers/cassi"))
    from cassi_gap_tv import generate_synthetic_problem, gap_tv, psnr_db

    problem = generate_synthetic_problem(H=32, W=32, N=8, seed=seed)
    y, mask, shifts, x_true = problem["y"], problem["mask"], problem["shifts"], problem["x_true"]

    x_hat = gap_tv(y, mask, shifts, n_bands=len(shifts), n_iters=30,
                   tv_lambda=0.005, verbose=False)

    xh_n = x_hat / max(x_hat.max(), 1e-8)
    gt_n = x_true / max(x_true.max(), 1e-8)
    psnr = round(psnr_db(gt_n, xh_n), 2)

    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_dir / "snapshot.npz", y=y, mask=mask, shifts=shifts)
    np.savez_compressed(out_dir / "ground_truth.npz", x=x_true)
    np.savez_compressed(out_dir / "solution.npz", cube=x_hat.astype(np.float32))

    _save_preview(y, out_dir / "snapshot.png")
    _save_preview(x_true.mean(axis=2), out_dir / "ground_truth.png")

    meta = {
        "benchmark": "L3-003 (CASSI) — DEMO (not the real benchmark)",
        "tier_approx": "T1_nominal-equivalent",
        "generated_by": "scripts/generate_demos.py",
        "seed": seed,
        "shape_snapshot": list(y.shape),
        "shape_ground_truth": list(x_true.shape),
        "shape_solution": list(x_hat.shape),
        "reference_solver": "pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py",
        "reference_solver_psnr_db": psnr,
        "how_to_run":
            "python3 pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py "
            f"--input pwm-team/pwm_product/demos/cassi/{out_dir.name} --output /tmp/out",
        "sha256": {
            name: _sha256_file(out_dir / name)
            for name in ("snapshot.npz", "ground_truth.npz", "solution.npz")
        },
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True))
    return {"sample": out_dir.name, "psnr_db": psnr, "seed": seed}


def generate_cacti_sample(out_dir: Path, seed: int) -> dict:
    """Write one CACTI sample (snapshot+gt+solution+previews+meta) at out_dir."""
    import numpy as np
    sys.path.insert(0, str(_repo_root() / "pwm-team/pwm_product/reference_solvers/cacti"))
    from cacti_pnp_admm import generate_synthetic_problem, pnp_admm, psnr_db

    problem = generate_synthetic_problem(T=4, H=32, W=32, seed=seed)
    y, masks, x_true = problem["y"], problem["masks"], problem["x_true"]

    x_hat = pnp_admm(y, masks, n_iters=20, rho=0.05, tv_lambda=0.01, verbose=False)

    xh_n = x_hat / max(x_hat.max(), 1e-8)
    gt_n = x_true / max(x_true.max(), 1e-8)
    psnr = round(psnr_db(gt_n, xh_n), 2)

    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_dir / "snapshot.npz", y=y, masks=masks)
    np.savez_compressed(out_dir / "ground_truth.npz", x=x_true)
    np.savez_compressed(out_dir / "solution.npz", video=x_hat.astype(np.float32))

    # ground_truth may be (T, H, W) or (H, W, T). Take the middle frame on whichever
    # axis is the time axis (typically the smallest dimension in our demo config).
    if x_true.ndim == 3:
        if x_true.shape[0] < x_true.shape[2]:
            gt_preview = x_true[x_true.shape[0] // 2]
        else:
            gt_preview = x_true[:, :, x_true.shape[2] // 2]
    else:
        gt_preview = x_true
    _save_preview(y, out_dir / "snapshot.png")
    _save_preview(gt_preview, out_dir / "ground_truth.png")

    meta = {
        "benchmark": "L3-004 (CACTI) — DEMO (not the real benchmark)",
        "tier_approx": "T1_nominal-equivalent",
        "generated_by": "scripts/generate_demos.py",
        "seed": seed,
        "shape_snapshot": list(y.shape),
        "shape_ground_truth": list(x_true.shape),
        "shape_solution": list(x_hat.shape),
        "reference_solver": "pwm-team/pwm_product/reference_solvers/cacti/cacti_pnp_admm.py",
        "reference_solver_psnr_db": psnr,
        "how_to_run":
            "python3 pwm-team/pwm_product/reference_solvers/cacti/cacti_pnp_admm.py "
            f"--input pwm-team/pwm_product/demos/cacti/{out_dir.name} --output /tmp/out",
        "sha256": {
            name: _sha256_file(out_dir / name)
            for name in ("snapshot.npz", "ground_truth.npz", "solution.npz")
        },
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True))
    return {"sample": out_dir.name, "psnr_db": psnr, "seed": seed}


def _write_readme(benchmark_dir: Path, benchmark_id: str, anchor: str,
                  solver_path: str, samples: list[dict]) -> None:
    lines = [
        f"# {anchor.upper()} demo datasets — `{benchmark_id}`",
        "",
        f"Canonical, committed-to-repo inputs + reference outputs for `{benchmark_id}`.",
        f"**{N_SAMPLES} independent samples** (different RNG seeds) so external users",
        "can see the reference solver is deterministic and not cherry-picked.",
        "",
        f"**⚠ These are NOT the real {benchmark_id} benchmark.** They are small",
        f"(32×32) synthetic problems created by `scripts/generate_demos.py`.",
        "Use them to verify the pipeline end-to-end; do NOT submit cert_hashes",
        "computed against them.",
        "",
        "## Samples",
        "",
        "| Sample | Seed | Reference PSNR |",
        "|--------|------|----------------|",
    ]
    for s in samples:
        lines.append(f"| `{s['sample']}/` | {s['seed']} | {s['psnr_db']} dB |")
    lines.extend([
        "",
        "## Files in each sample",
        "",
        "| File | Purpose |",
        "|------|---------|",
        "| `snapshot.npz`     | Solver input |",
        "| `ground_truth.npz` | True cube/video (for PSNR scoring) |",
        "| `solution.npz`     | Pre-computed output from the reference solver |",
        "| `snapshot.png`     | Rendered preview of the input |",
        "| `ground_truth.png` | Rendered preview of the target |",
        "| `meta.json`        | Provenance + SHA-256 hashes |",
        "",
        "## Run the reference solver on sample_01",
        "",
        "```bash",
        f"python3 {solver_path} \\",
        f"    --input  pwm-team/pwm_product/demos/{anchor}/sample_01 \\",
        "    --output /tmp/out",
        "cat /tmp/out/meta.json",
        "```",
        "",
        "Each sample is byte-stable across runs at the same git SHA.",
        "",
    ])
    (benchmark_dir / "README.md").write_text("\n".join(lines))


def generate_benchmark(anchor: str, benchmark_dir: Path, check: bool) -> dict:
    if anchor == "cassi":
        sample_fn = generate_cassi_sample
        solver = "pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py"
        bench_id = "L3-003"
    elif anchor == "cacti":
        sample_fn = generate_cacti_sample
        solver = "pwm-team/pwm_product/reference_solvers/cacti/cacti_pnp_admm.py"
        bench_id = "L3-004"
    else:
        raise ValueError(f"unknown anchor {anchor!r}")

    results = []
    for i in range(1, N_SAMPLES + 1):
        sample_dir = benchmark_dir / f"sample_{i:02d}"
        if check:
            missing = [n for n in ("snapshot.npz", "ground_truth.npz",
                                    "solution.npz", "snapshot.png",
                                    "ground_truth.png", "meta.json")
                       if not (sample_dir / n).is_file()]
            results.append({"sample": sample_dir.name, "missing": missing})
        else:
            results.append(sample_fn(sample_dir, seed=BASE_SEED + (i - 1)))

    if not check:
        _write_readme(benchmark_dir, bench_id, anchor, solver, results)
    return {"anchor": anchor, "benchmark_id": bench_id, "samples": results}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cassi", action="store_true", help="Regenerate CASSI only")
    ap.add_argument("--cacti", action="store_true", help="Regenerate CACTI only")
    ap.add_argument("--check", action="store_true",
                    help="Dry-run: report missing files, write nothing.")
    args = ap.parse_args()

    repo = _repo_root()
    demos_root = repo / "pwm-team" / "pwm_product" / "demos"

    do_cassi = args.cassi or not args.cacti
    do_cacti = args.cacti or not args.cassi

    if do_cassi:
        res = generate_benchmark("cassi", demos_root / "cassi", check=args.check)
        print(f"CASSI: {res}")
    if do_cacti:
        res = generate_benchmark("cacti", demos_root / "cacti", check=args.check)
        print(f"CACTI: {res}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
