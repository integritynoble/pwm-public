"""
score_solution() — main entry point for pwm_scoring.
See interfaces/scoring_api.py for the full interface contract.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np

from .tracks import track_a, track_b, track_c
from .gates import check_s1, check_s2, check_s3, check_s4
from .metrics import psnr, ssim
from .epsilon import eval_epsilon


@dataclass
class SolutionScore:
    psnr_per_instance: list[float]
    ssim_per_instance: list[float]
    Q: float
    track_a_pass: bool
    track_b_pass: bool
    track_c_auc: float | None
    gate_verdicts: dict
    cert_payload: dict
    psnr_worst: float = 0.0
    psnr_median: float = 0.0
    stratum_results: dict = field(default_factory=dict)


def score_solution(
    benchmark_manifest: dict,
    instance_dir: Path,
    solver_output: np.ndarray,
    omega_params: dict,
) -> SolutionScore:
    # TODO: implement full scoring pipeline
    # 1. Load ground truth from instance_dir/ground_truth.npz
    # 2. Run S1-S4 gates
    # 3. Compute per-instance PSNR/SSIM
    # 4. Run Track A (stratified worst-case)
    # 5. Run Track B (uniform median)
    # 6. Run Track C if mismatch spec (degradation AUC)
    # 7. Compute Q from quality_thresholds
    # 8. Build cert_payload (validate against cert_schema.json)
    raise NotImplementedError
