"""Evaluation metrics: PSNR, SSIM, SAM, residual norm."""
from __future__ import annotations
import numpy as np
from skimage.metrics import structural_similarity as _sk_ssim


def _align(gt: np.ndarray, pred: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if gt.shape != pred.shape:
        raise ValueError(f"shape mismatch: gt={gt.shape}, pred={pred.shape}")
    return gt.astype(np.float64, copy=False), pred.astype(np.float64, copy=False)


def psnr(gt: np.ndarray, pred: np.ndarray, data_range: float = 1.0) -> float:
    """Peak Signal-to-Noise Ratio (dB). Identical inputs return +inf."""
    g, p = _align(gt, pred)
    mse = float(np.mean((g - p) ** 2))
    if mse == 0.0:
        return float("inf")
    return float(10.0 * np.log10(data_range ** 2 / mse))


def ssim(gt: np.ndarray, pred: np.ndarray, data_range: float = 1.0) -> float:
    """Structural Similarity Index (mean across channels for multichannel inputs)."""
    g, p = _align(gt, pred)
    if g.ndim == 2:
        return float(_sk_ssim(g, p, data_range=data_range))
    return float(_sk_ssim(g, p, data_range=data_range, channel_axis=-1))


def sam(gt: np.ndarray, pred: np.ndarray) -> float:
    """
    Spectral Angle Mapper (degrees).
    gt, pred: shape (..., N_bands). Returns mean angle over spatial positions.
    """
    g, p = _align(gt, pred)
    dot = np.sum(g * p, axis=-1)
    norm_gt = np.linalg.norm(g, axis=-1)
    norm_pred = np.linalg.norm(p, axis=-1)
    cos_angle = np.clip(dot / (norm_gt * norm_pred + 1e-12), -1.0, 1.0)
    return float(np.mean(np.degrees(np.arccos(cos_angle))))


def residual_norm(y: np.ndarray, phi_fn, x_hat: np.ndarray) -> float:
    """
    Relative residual ||y - Phi(x_hat)||_2 / ||y||_2.
    phi_fn may be a callable x -> Phi@x or a 2D matrix.
    """
    if callable(phi_fn):
        pred = phi_fn(x_hat)
    else:
        pred = phi_fn @ x_hat
    y_flat = np.asarray(y, dtype=np.float64).ravel()
    pred_flat = np.asarray(pred, dtype=np.float64).ravel()
    num = float(np.linalg.norm(y_flat - pred_flat))
    den = float(np.linalg.norm(y_flat))
    if den == 0.0:
        return float("inf") if num > 0 else 0.0
    return num / den
