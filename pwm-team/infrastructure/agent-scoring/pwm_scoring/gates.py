"""S1-S4 gate checks."""
from __future__ import annotations
import numpy as np


def check_s1(solver_output: np.ndarray, manifest: dict) -> tuple[bool, str]:
    """S1: output dimensions match spec; masks/dispersion consistent."""
    # TODO: implement
    raise NotImplementedError


def check_s2(method_sig: str, principle: dict) -> tuple[bool, str]:
    """S2: solver method consistent with Principle's well-posedness."""
    # TODO: implement
    raise NotImplementedError


def check_s3(residuals: list[float], resolutions: list[int]) -> tuple[bool, str]:
    """S3: residual decreases monotonically; convergence rate ≈ q=2.0."""
    # TODO: implement
    raise NotImplementedError


def check_s4(psnr_worst: float, epsilon: float) -> tuple[bool, str]:
    """S4: worst PSNR ≥ ε across all instances."""
    pass_ = psnr_worst >= epsilon
    msg = f"worst PSNR {psnr_worst:.2f} dB {'≥' if pass_ else '<'} ε {epsilon:.2f} dB"
    return pass_, msg
