"""Tests for pwm_scoring.metrics — PSNR, SSIM, SAM, residual_norm."""
from __future__ import annotations
import math
import numpy as np
import pytest

from pwm_scoring.metrics import psnr, ssim, sam, residual_norm


rng = np.random.default_rng(0)


class TestPSNR:
    def test_identical_is_inf(self):
        gt = rng.random((64, 64))
        assert math.isinf(psnr(gt, gt))

    def test_known_value_constant_error(self):
        # Uniform error e in [0, 1] float: MSE = e^2, PSNR = -20*log10(e)
        gt = np.full((8, 8), 0.5)
        pred = gt + 0.1
        assert abs(psnr(gt, pred) - (-20.0 * np.log10(0.1))) < 1e-9

    def test_shape_mismatch_raises(self):
        with pytest.raises(ValueError):
            psnr(np.zeros((8, 8)), np.zeros((8, 7)))

    def test_data_range_respected(self):
        # With uint-like data_range, PSNR scales by 20*log10(range)
        gt = np.full((8, 8), 100.0)
        pred = gt + 10.0
        v = psnr(gt, pred, data_range=255.0)
        expected = 20.0 * np.log10(255.0 / 10.0)
        assert abs(v - expected) < 1e-9


class TestSSIM:
    def test_identical_is_one(self):
        gt = rng.random((64, 64)).astype(np.float64)
        assert abs(ssim(gt, gt) - 1.0) < 1e-6

    def test_drops_below_one_with_noise(self):
        gt = rng.random((64, 64))
        pred = gt + 0.1 * rng.standard_normal((64, 64))
        v = ssim(gt, pred)
        assert 0.0 < v < 1.0

    def test_multichannel(self):
        gt = rng.random((32, 32, 3))
        assert abs(ssim(gt, gt) - 1.0) < 1e-6

    def test_hyperspectral_cube(self):
        gt = rng.random((16, 16, 28))
        pred = gt + 0.01 * rng.standard_normal((16, 16, 28))
        assert 0.5 < ssim(gt, pred) < 1.0


class TestSAM:
    def test_identical_is_zero(self):
        gt = rng.random((8, 8, 28)) + 0.1  # avoid zero vectors
        assert abs(sam(gt, gt)) < 1e-3  # arccos(~1) precision floor

    def test_orthogonal_is_90(self):
        a = np.zeros((1, 1, 4))
        a[0, 0, 0] = 1.0
        b = np.zeros((1, 1, 4))
        b[0, 0, 1] = 1.0
        assert abs(sam(a, b) - 90.0) < 1e-6

    def test_scale_invariance(self):
        # Scaling preserves spectral angle
        gt = rng.random((4, 4, 8)) + 0.1
        pred = 3.7 * gt
        assert abs(sam(gt, pred)) < 1e-3


class TestResidualNorm:
    def test_zero_for_exact_solution(self):
        Phi = rng.standard_normal((32, 64))
        x = rng.standard_normal(64)
        y = Phi @ x
        assert residual_norm(y, Phi, x) < 1e-10

    def test_callable_phi(self):
        Phi = rng.standard_normal((32, 64))
        x = rng.standard_normal(64)
        y = Phi @ x
        r = residual_norm(y, lambda v: Phi @ v, x)
        assert r < 1e-10

    def test_nonzero_residual(self):
        Phi = rng.standard_normal((32, 64))
        x = rng.standard_normal(64)
        y = Phi @ x
        x_bad = x + 0.5 * rng.standard_normal(64)
        assert residual_norm(y, Phi, x_bad) > 0.01
