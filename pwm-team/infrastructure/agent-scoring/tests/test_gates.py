"""Tests for pwm_scoring.gates — S1-S4 checks."""
from __future__ import annotations
import numpy as np
import pytest

from pwm_scoring.gates import check_s1, check_s2, check_s3, check_s4


class TestS1:
    def test_shape_match_from_omega_tier(self):
        out = np.zeros((256, 256, 28), dtype=np.float32)
        manifest = {"omega_tier": {"H": 256, "W": 256, "N_bands": 28}}
        ok, msg = check_s1(out, manifest)
        assert ok, msg

    def test_shape_mismatch(self):
        out = np.zeros((128, 256, 28))
        manifest = {"omega_tier": {"H": 256, "W": 256, "N_bands": 28}}
        ok, msg = check_s1(out, manifest)
        assert not ok
        assert "shape mismatch" in msg

    def test_output_format_override(self):
        out = np.zeros((10, 10))
        manifest = {"output_format": {"shape": [10, 10]}}
        assert check_s1(out, manifest)[0]

    def test_nan_rejected(self):
        out = np.full((16, 16), np.nan)
        manifest = {"omega_tier": {"H": 16, "W": 16}}
        ok, msg = check_s1(out, manifest)
        assert not ok and "NaN" in msg

    def test_inf_rejected(self):
        out = np.array([[1.0, np.inf], [1.0, 1.0]])
        manifest = {"omega_tier": {"H": 2, "W": 2}}
        ok, msg = check_s1(out, manifest)
        assert not ok

    def test_no_expected_shape_accepts(self):
        out = np.zeros((3, 4, 5))
        ok, _ = check_s1(out, {})
        assert ok

    def test_non_ndarray_rejected(self):
        ok, msg = check_s1([1, 2, 3], {"omega_tier": {"H": 3, "W": 1}})
        assert not ok


class TestS2:
    def test_uniqueness_true_accepts_any(self):
        p = {"well_posedness": {"uniqueness": True}}
        assert check_s2("L", p)[0]
        assert check_s2("L+O", p)[0]
        assert check_s2("T+N", p)[0]

    def test_uniqueness_false_rejects_pure_L(self):
        p = {"well_posedness": {"uniqueness": False}}
        ok, msg = check_s2("L", p)
        assert not ok
        assert "uniqueness" in msg.lower() or "regularization" in msg.lower()

    def test_uniqueness_false_accepts_L_plus_O(self):
        p = {"well_posedness": {"uniqueness": False}}
        assert check_s2("L+O", p)[0]

    def test_allowed_whitelist(self):
        p = {"well_posedness": {"allowed_method_sigs": ["L+O", "L+N"]}}
        assert check_s2("L+O", p)[0]
        assert check_s2("O+L", p)[0]        # order-insensitive
        assert not check_s2("T+N", p)[0]

    def test_unknown_letter_rejected(self):
        ok, msg = check_s2("X+L", {})
        assert not ok and "unknown" in msg.lower()

    def test_empty_method_sig_rejected(self):
        assert not check_s2("", {})[0]


class TestS3:
    def test_order_two_convergence_passes(self):
        # r_i ∝ h^2 → slope 2.0
        N = [64, 128, 256, 512]
        r = [1.0 / (n ** 2) for n in N]
        ok, msg = check_s3(r, N)
        assert ok, msg

    def test_linear_convergence_fails_default_threshold(self):
        # slope = 1.0 < 1.8
        N = [64, 128, 256, 512]
        r = [1.0 / n for n in N]
        ok, msg = check_s3(r, N)
        assert not ok

    def test_custom_threshold(self):
        N = [64, 128, 256, 512]
        r = [1.0 / n for n in N]
        assert check_s3(r, N, min_slope=0.8)[0]

    def test_too_few_points(self):
        ok, _ = check_s3([1.0, 0.5], [64, 128])
        assert not ok

    def test_nonpositive_rejected(self):
        ok, _ = check_s3([1.0, 0.5, 0.0], [64, 128, 256])
        assert not ok


class TestS4:
    def test_pass(self):
        ok, _ = check_s4(25.0, 22.0)
        assert ok

    def test_fail(self):
        ok, _ = check_s4(20.0, 22.0)
        assert not ok

    def test_exact_boundary_is_pass(self):
        ok, _ = check_s4(22.0, 22.0)
        assert ok
