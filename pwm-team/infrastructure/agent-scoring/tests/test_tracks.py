"""Tests for pwm_scoring.tracks — Track A/B/C evaluation."""
from __future__ import annotations
import numpy as np
import pytest

from pwm_scoring.tracks import (
    track_a,
    track_b,
    track_c,
    _parse_hw_range,
    _strata_from_manifest,
    _seed_from_benchmark,
)


BENCHMARK = {
    "benchmark_hash": "0x" + "a" * 64,
    "epsilon_fn": "22 + 3 * log2(H*W / 4096)",
    "p_benchmark": {
        "tracks": {
            "track_A_stratified_worst_case": {
                "strata": [
                    {"name": "S1_small",  "H_W_range": "<= 256^2"},
                    {"name": "S2_medium", "H_W_range": "256^2 < HW <= 512^2"},
                    {"name": "S3_large",  "H_W_range": "512^2 < HW <= 1024^2"},
                    {"name": "S4_xlarge", "H_W_range": "> 1024^2"},
                ],
                "samples_per_stratum": 5,
            },
            "track_C_mismatch_degradation": {
                "sweep_points": [
                    {"phi": 0.0,  "disp_a1_error": 0.0},
                    {"phi": 0.25, "disp_a1_error": 0.0125},
                    {"phi": 0.50, "disp_a1_error": 0.025},
                    {"phi": 0.75, "disp_a1_error": 0.0375},
                    {"phi": 1.0,  "disp_a1_error": 0.05},
                ],
                "scenes_per_point": 4,
            },
        },
    },
}


OMEGA_RANGE = {
    "H": [64, 2048],
    "W": [64, 2048],
    "N_bands": [28, 28],
    "mask_density": [0.3, 0.7],
    "noise_level": [0.0, 0.1],
    "disp_a1_error": [0.0, 0.05],
}


class TestParseHWRange:
    def test_le_form(self):
        lo, hi = _parse_hw_range("<= 256^2")
        assert lo == 0 and hi == 65536

    def test_interval_form(self):
        lo, hi = _parse_hw_range("256^2 < HW <= 512^2")
        assert lo == 65536 and hi == 262144

    def test_gt_form(self):
        lo, hi = _parse_hw_range("> 1024^2")
        assert lo == 1048576 and hi == float("inf")

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            _parse_hw_range("not a range")


class TestStrataFromManifest:
    def test_all_four_strata(self):
        s = _strata_from_manifest(BENCHMARK)
        assert [x["name"] for x in s] == ["S1_small", "S2_medium", "S3_large", "S4_xlarge"]


class TestSeed:
    def test_deterministic(self):
        assert _seed_from_benchmark(BENCHMARK) == _seed_from_benchmark(BENCHMARK)

    def test_salt_differs(self):
        a = _seed_from_benchmark(BENCHMARK, salt="track_a")
        b = _seed_from_benchmark(BENCHMARK, salt="track_b")
        assert a != b


def _mock_solver_constant(psnr_value: float):
    """Return a solver that always yields the same PSNR."""
    return lambda omega: psnr_value


def _mock_solver_degrades(base_psnr: float, *, per_hw: float = 1e-5):
    """PSNR that drops as H*W grows — mimics a weaker solver at scale."""
    return lambda omega: base_psnr - per_hw * (omega["H"] * omega["W"])


class TestTrackA:
    def test_strong_solver_passes_all_strata(self):
        # 80 dB is far above any ε(Ω) the log-formula produces on OMEGA_RANGE
        ok, results = track_a(BENCHMARK, _mock_solver_constant(80.0), OMEGA_RANGE)
        assert ok, results
        assert all(r["pass"] for r in results.values())

    def test_weak_solver_fails_some_strata(self):
        ok, results = track_a(BENCHMARK, _mock_solver_constant(10.0), OMEGA_RANGE)
        assert not ok
        assert any(not r["pass"] for r in results.values())

    def test_determinism(self):
        solver = _mock_solver_degrades(35.0)
        r1 = track_a(BENCHMARK, solver, OMEGA_RANGE)
        r2 = track_a(BENCHMARK, solver, OMEGA_RANGE)
        # Exactly the same sampled omegas → exactly the same results.
        assert r1 == r2


class TestTrackB:
    def test_strong_solver_passes(self):
        ok, median = track_b(BENCHMARK, _mock_solver_constant(80.0), OMEGA_RANGE, num_samples=10)
        assert ok and median == 80.0

    def test_weak_solver_fails(self):
        ok, median = track_b(BENCHMARK, _mock_solver_constant(5.0), OMEGA_RANGE, num_samples=10)
        assert not ok and median == 5.0


class TestTrackC:
    def test_none_when_no_mismatch(self):
        assert track_c(BENCHMARK, _mock_solver_constant(30.0), mismatch_dims=[]) is None

    def test_flat_solver_produces_finite_auc(self):
        auc = track_c(
            BENCHMARK,
            _mock_solver_constant(30.0),
            mismatch_dims=["disp_a1_error"],
            scenes_per_phi=4,
            omega_range=OMEGA_RANGE,
        )
        assert isinstance(auc, float)
        assert 0.0 < auc < 5.0

    def test_degrading_solver_lowers_auc(self):
        strong = _mock_solver_constant(40.0)
        # solver whose PSNR falls linearly with disp error
        def weak(o):
            return 40.0 - 500.0 * float(o.get("disp_a1_error", 0.0))
        auc_strong = track_c(BENCHMARK, strong, ["disp_a1_error"],
                             scenes_per_phi=4, omega_range=OMEGA_RANGE)
        auc_weak = track_c(BENCHMARK, weak, ["disp_a1_error"],
                           scenes_per_phi=4, omega_range=OMEGA_RANGE)
        assert auc_weak < auc_strong
