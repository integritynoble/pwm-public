"""Prepare workdirs for `pwm-node mine` invocations.

Repackages the existing canonical 256x256 demo data into the schema
the cassi_mst.py / cacti_efficientsci.py wrappers expect.

Outputs:
    /tmp/pwm-out/cassi-mst/input/snapshot.npz       (y, mask, shifts)
    /tmp/pwm-out/cassi-mst/input/ground_truth.npz   (passthrough)
    /tmp/pwm-out/cacti-eff/input/snapshot.npz       (passthrough — already matches)
    /tmp/pwm-out/cacti-eff/input/ground_truth.npz   (passthrough)

Run from repo root:  python scripts/prep_mine_workdirs.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
DEMOS = REPO / "pwm-team" / "pwm_product" / "demos"
OUT = REPO / "pwm_work"  # in-repo, predictable on both Python + Bash on Windows

OUT.mkdir(parents=True, exist_ok=True)


def prep_cassi():
    src_dir = DEMOS / "cassi" / "sample_01"
    dst_dir = OUT / "cassi-mst" / "input"
    dst_dir.mkdir(parents=True, exist_ok=True)

    with np.load(src_dir / "snapshot.npz") as f:
        y = np.asarray(f["y"], dtype=np.float32)
        mask = np.asarray(f["mask"], dtype=np.float32)
        step = int(np.asarray(f["step"]).item())

    # n_bands derived from y vs mask: y is (H, H+step*(n_bands-1))
    H = mask.shape[0]
    n_bands = (y.shape[1] - H) // step + 1
    shifts = (np.arange(n_bands, dtype=np.int32) * step)
    print(f"[cassi] H={H} n_bands={n_bands} step={step} shifts={shifts.tolist()}")
    print(f"[cassi] y.shape={y.shape} mask.shape={mask.shape}")

    np.savez_compressed(dst_dir / "snapshot.npz", y=y, mask=mask, shifts=shifts)
    shutil.copy2(src_dir / "ground_truth.npz", dst_dir / "ground_truth.npz")
    print(f"[cassi] wrote {dst_dir}/{{snapshot.npz, ground_truth.npz}}")


def prep_cacti():
    src_dir = DEMOS / "cacti" / "sample_01"
    dst_dir = OUT / "cacti-eff" / "input"
    dst_dir.mkdir(parents=True, exist_ok=True)

    with np.load(src_dir / "snapshot.npz") as f:
        y = np.asarray(f["y"], dtype=np.float32)
        masks = np.asarray(f["masks"], dtype=np.float32)
    print(f"[cacti] y.shape={y.shape} masks.shape={masks.shape}")

    np.savez_compressed(dst_dir / "snapshot.npz", y=y, masks=masks)
    shutil.copy2(src_dir / "ground_truth.npz", dst_dir / "ground_truth.npz")
    print(f"[cacti] wrote {dst_dir}/{{snapshot.npz, ground_truth.npz}}")


if __name__ == "__main__":
    prep_cassi()
    prep_cacti()
    print("done")
