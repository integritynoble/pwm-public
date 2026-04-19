"""Track A, B, C evaluation implementations."""
from __future__ import annotations
import numpy as np


def track_a(benchmark: dict, solver_fn, omega_range: dict) -> tuple[bool, dict]:
    """
    Stratified worst-case evaluation.
    Divide Ω into strata by H×W. Draw 5 random instances per stratum.
    Worst score per stratum must pass epsilon_fn(Ω_centroid).
    All strata must independently pass.
    Returns (pass: bool, stratum_results: dict)
    """
    # TODO: implement
    raise NotImplementedError


def track_b(benchmark: dict, solver_fn, omega_range: dict) -> tuple[bool, float]:
    """
    Uniform median evaluation.
    Sample 50 Ω points uniformly. Median must pass epsilon_fn(Ω_median).
    Returns (pass: bool, median_psnr: float)
    """
    # TODO: implement
    raise NotImplementedError


def track_c(benchmark: dict, solver_fn, mismatch_dims: list[str]) -> float:
    """
    Mismatch degradation curve AUC.
    Sweep phi ∈ {0, 0.25, 0.50, 0.75, 1.0}.
    At each phi: 10 scenes, record median PSNR.
    Return trapezoid AUC of Q_norm(phi) = PSNR(phi) / epsilon_fn(Omega at phi).
    Returns None if oracle spec (no mismatch dims in Omega).
    """
    # TODO: implement
    raise NotImplementedError
