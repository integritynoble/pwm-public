"""Evaluation metrics: PSNR, SSIM, SAM, residual norm."""
from __future__ import annotations
import numpy as np


def psnr(gt: np.ndarray, pred: np.ndarray, data_range: float = 1.0) -> float:
    """Peak Signal-to-Noise Ratio (dB)."""
    mse = np.mean((gt.astype(np.float64) - pred.astype(np.float64)) ** 2)
    if mse == 0:
        return float("inf")
    return float(10.0 * np.log10(data_range ** 2 / mse))


def ssim(gt: np.ndarray, pred: np.ndarray) -> float:
    """Structural Similarity Index. TODO: implement full SSIM."""
    # TODO: implement using scikit-image or manual SSIM formula
    raise NotImplementedError


def sam(gt: np.ndarray, pred: np.ndarray) -> float:
    """
    Spectral Angle Mapper (degrees).
    gt, pred: shape (..., N_bands)
    Returns mean angle in degrees across all spatial positions.
    """
    dot = np.sum(gt * pred, axis=-1)
    norm_gt = np.linalg.norm(gt, axis=-1)
    norm_pred = np.linalg.norm(pred, axis=-1)
    cos_angle = np.clip(dot / (norm_gt * norm_pred + 1e-10), -1.0, 1.0)
    return float(np.mean(np.degrees(np.arccos(cos_angle))))


def residual_norm(
    y: np.ndarray,
    phi_fn,  # callable: x -> Phi(x)
    x_hat: np.ndarray,
) -> float:
    """
    Normalised residual: ||y - Phi(x_hat)||_2 / ||y||_2
    phi_fn is the forward operator callable.
    """
    residual = y - phi_fn(x_hat)
    return float(np.linalg.norm(residual) / (np.linalg.norm(y) + 1e-10))
