"""Generate canonical CASSI + CACTI demo datasets.

Writes small (< 50KB), committed-to-repo inputs that any external user
can point the reference solvers at with one command:

    python3 pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py \
        --input pwm-team/pwm_product/demos/cassi \
        --output /tmp/out

Each demo dir contains:
    snapshot.npz     — solver input (matches the input contract in each
                       solver's README)
    ground_truth.npz — the true HSI cube / video (for PSNR scoring)
    solution.npz     — pre-computed output from the reference solver
                       (so static demos don't require a live Python runtime)
    meta.json        — provenance, dimensions, reference PSNR

Regenerate by re-running this script. The generated files are
deterministic (fixed seed) so CI diffs on byte-for-byte equality.

Usage::

    python3 scripts/generate_demos.py          # all demos
    python3 scripts/generate_demos.py --cassi  # cassi only
    python3 scripts/generate_demos.py --check  # dry-run, report what would change
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


DEMO_SEED = 42  # fixed so demos are byte-stable across runs


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pwm-team").is_dir():
            return p
    raise RuntimeError("cannot find repo root")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate_cassi_demo(out_dir: Path, check: bool = False) -> dict:
    """Write snapshot.npz + ground_truth.npz + solution.npz for CASSI demo."""
    import numpy as np
    # Import the solver's synthetic generator + algorithm.
    sys.path.insert(0, str(_repo_root() / "pwm-team/pwm_product/reference_solvers/cassi"))
    from cassi_gap_tv import generate_synthetic_problem, gap_tv, psnr_db

    problem = generate_synthetic_problem(H=32, W=32, N=8, seed=DEMO_SEED)
    y = problem["y"]
    mask = problem["mask"]
    shifts = problem["shifts"]
    x_true = problem["x_true"]

    # Run the reference solver once to pre-compute output.
    x_hat = gap_tv(y, mask, shifts, n_bands=len(shifts), n_iters=30,
                   tv_lambda=0.005, verbose=False)

    # PSNR (normalized)
    xh_n = x_hat / max(x_hat.max(), 1e-8)
    gt_n = x_true / max(x_true.max(), 1e-8)
    psnr = round(psnr_db(gt_n, xh_n), 2)

    out_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "snapshot.npz":     lambda p: np.savez_compressed(p, y=y, mask=mask, shifts=shifts),
        "ground_truth.npz": lambda p: np.savez_compressed(p, x=x_true),
        "solution.npz":     lambda p: np.savez_compressed(p, cube=x_hat.astype(np.float32)),
    }

    if check:
        missing = [n for n in files if not (out_dir / n).is_file()]
        return {"missing": missing, "would_regen": True}

    for name, writer in files.items():
        writer(out_dir / name)

    meta = {
        "benchmark": "L3-003 (CASSI) — DEMO (not the real benchmark)",
        "tier_approx": "T1_nominal-equivalent",
        "generated_by": "scripts/generate_demos.py",
        "seed": DEMO_SEED,
        "shape_snapshot": list(y.shape),
        "shape_ground_truth": list(x_true.shape),
        "shape_solution": list(x_hat.shape),
        "reference_solver": "pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py",
        "reference_solver_psnr_db": psnr,
        "how_to_run":
            "python3 pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py "
            "--input pwm-team/pwm_product/demos/cassi --output /tmp/out",
        "sha256": {
            "snapshot.npz":     _sha256_file(out_dir / "snapshot.npz"),
            "ground_truth.npz": _sha256_file(out_dir / "ground_truth.npz"),
            "solution.npz":     _sha256_file(out_dir / "solution.npz"),
        },
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True))
    return {"wrote": list(files), "psnr_db": psnr, "out_dir": str(out_dir)}


def generate_cacti_demo(out_dir: Path, check: bool = False) -> dict:
    """Write snapshot.npz + ground_truth.npz + solution.npz for CACTI demo."""
    import numpy as np
    sys.path.insert(0, str(_repo_root() / "pwm-team/pwm_product/reference_solvers/cacti"))
    from cacti_pnp_admm import generate_synthetic_problem, pnp_admm, psnr_db

    problem = generate_synthetic_problem(T=4, H=32, W=32, seed=DEMO_SEED)
    y = problem["y"]
    masks = problem["masks"]
    x_true = problem["x_true"]

    x_hat = pnp_admm(y, masks, n_iters=20, rho=0.05, tv_lambda=0.01,
                     verbose=False)

    xh_n = x_hat / max(x_hat.max(), 1e-8)
    gt_n = x_true / max(x_true.max(), 1e-8)
    psnr = round(psnr_db(gt_n, xh_n), 2)

    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "snapshot.npz":     lambda p: np.savez_compressed(p, y=y, masks=masks),
        "ground_truth.npz": lambda p: np.savez_compressed(p, x=x_true),
        "solution.npz":     lambda p: np.savez_compressed(p, video=x_hat.astype(np.float32)),
    }

    if check:
        missing = [n for n in files if not (out_dir / n).is_file()]
        return {"missing": missing, "would_regen": True}

    for name, writer in files.items():
        writer(out_dir / name)

    meta = {
        "benchmark": "L3-004 (CACTI) — DEMO (not the real benchmark)",
        "tier_approx": "T1_nominal-equivalent",
        "generated_by": "scripts/generate_demos.py",
        "seed": DEMO_SEED,
        "shape_snapshot": list(y.shape),
        "shape_ground_truth": list(x_true.shape),
        "shape_solution": list(x_hat.shape),
        "reference_solver": "pwm-team/pwm_product/reference_solvers/cacti/cacti_pnp_admm.py",
        "reference_solver_psnr_db": psnr,
        "how_to_run":
            "python3 pwm-team/pwm_product/reference_solvers/cacti/cacti_pnp_admm.py "
            "--input pwm-team/pwm_product/demos/cacti --output /tmp/out",
        "sha256": {
            "snapshot.npz":     _sha256_file(out_dir / "snapshot.npz"),
            "ground_truth.npz": _sha256_file(out_dir / "ground_truth.npz"),
            "solution.npz":     _sha256_file(out_dir / "solution.npz"),
        },
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True))
    return {"wrote": list(files), "psnr_db": psnr, "out_dir": str(out_dir)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cassi", action="store_true", help="Regenerate CASSI demo only")
    ap.add_argument("--cacti", action="store_true", help="Regenerate CACTI demo only")
    ap.add_argument("--check", action="store_true",
                    help="Dry-run: report missing files, write nothing.")
    args = ap.parse_args()

    repo = _repo_root()
    demos_root = repo / "pwm-team" / "pwm_product" / "demos"

    do_cassi = args.cassi or not args.cacti
    do_cacti = args.cacti or not args.cassi

    if do_cassi:
        res = generate_cassi_demo(demos_root / "cassi", check=args.check)
        print(f"CASSI: {res}")
    if do_cacti:
        res = generate_cacti_demo(demos_root / "cacti", check=args.check)
        print(f"CACTI: {res}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
