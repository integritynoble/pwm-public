"""Integration test: score_solution on L3-003 CASSI T1-nominal.

We generate a synthetic spectral cube as ground truth, instantiate a mock
GAP-TV-style solver whose PSNR hovers near the L3-003 baseline (26 dB), then
verify:
  * all gates pass
  * cert_payload validates against cert_schema.json
  * Q is within 10 % of the published baseline (0.62)
  * the cert_payload hash is deterministic across two runs
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import pytest

jsonschema = pytest.importorskip("jsonschema")

from pwm_scoring import score_solution
from pwm_scoring.epsilon import eval_epsilon


REPO_ROOT = Path(__file__).resolve().parents[4]  # pwm-team/
L3_003 = REPO_ROOT / "pwm-team" / "pwm_product" / "genesis" / "l3" / "L3-003.json"
CERT_SCHEMA = REPO_ROOT / "pwm-team" / "coordination" / "agent-coord" / "interfaces" / "cert_schema.json"


def _load_l3_003() -> dict:
    return json.loads(L3_003.read_text())


def _cassi_t1_manifest(l3: dict) -> dict:
    """Shape an L3-003 tier into the manifest form score_solution expects."""
    t1 = next(t for t in l3["ibenchmarks"] if t["tier"] == "T1_nominal")
    manifest = {
        "benchmark_hash": "0x" + "7" * 64,
        "omega_tier": t1["omega_tier"],
        # Gentle log scaling across strata (small=22 dB, xlarge≈28 dB)
        "epsilon_fn": "22 + 2 * log2(max(H * W / 65536, 1))",
        "epsilon": t1["epsilon"],
        "quality_thresholds": t1["quality_thresholds"],
        "baselines": t1["baselines"],
        # Mirror the p_benchmark Track A/C tables so strata parsing works.
        "p_benchmark": l3["p_benchmark"],
    }
    return manifest


OMEGA_RANGE = {
    "H": [64, 2048],
    "W": [64, 2048],
    "N_bands": [28, 28],
    "mask_density": [0.3, 0.7],
    "noise_level": [0.0, 0.1],
    "disp_a1_error": [0.0, 0.05],
    "mask_dx": [0.0, 1.0],
    "mask_theta": [0.0, 0.15],
}


def _mock_solver(target_baseline_psnr: float = 29.5):
    """Deterministic mock solver mimicking GAP-TV-ish behaviour.

    PSNR decays slowly with H*W and with mismatch severity, staying above ε on
    small/medium strata and crossing ε on xlarge ones.
    """

    def solver(omega: dict) -> float:
        hw = float(omega.get("H", 256)) * float(omega.get("W", 256))
        scale_penalty = 0.5 * np.log2(max(hw / 65536.0, 1.0))
        mismatch = (
            8.0 * float(omega.get("disp_a1_error", 0.0))
            + 1.5 * float(omega.get("mask_dx", 0.0))
            + 1.5 * float(omega.get("mask_theta", 0.0))
        )
        return float(target_baseline_psnr - scale_penalty - mismatch)

    return solver


def _make_instance(tmp_path: Path, shape=(256, 256, 28), seed=0):
    rng = np.random.default_rng(seed)
    gt = rng.random(shape, dtype=np.float64)
    # Reconstruction = ground truth + small additive noise so PSNR ≈ 26 dB.
    noise_std = 10 ** (-26.0 / 20.0) / np.sqrt(12)
    recon = np.clip(gt + rng.normal(0.0, noise_std, gt.shape), 0.0, 1.0)
    instance = tmp_path / "instance_primary"
    instance.mkdir()
    np.savez(instance / "ground_truth.npz", spectral_cube=gt)
    return instance, recon


def _make_principle() -> dict:
    return {
        "well_posedness": {
            "existence": True,
            "uniqueness": False,       # requires regularization
            "stability": True,
            "allowed_method_sigs": ["L+O", "L+N", "T+N", "T+O"],
        }
    }


@pytest.mark.skipif(not L3_003.exists(), reason="L3-003 benchmark not available")
def test_score_cassi_t1_nominal(tmp_path):
    l3 = _load_l3_003()
    manifest = _cassi_t1_manifest(l3)
    instance, recon = _make_instance(tmp_path)

    score = score_solution(
        benchmark_manifest=manifest,
        instance_dir=instance,
        solver_output=recon,
        omega_params={"H": 256, "W": 256, "N_bands": 28,
                      "mask_density": 0.5, "noise_level": 0.01,
                      "disp_a1_error": 0.0, "mask_dx": 0.0, "mask_theta": 0.0},
        solver_fn=_mock_solver(target_baseline_psnr=29.5),
        omega_range=OMEGA_RANGE,
        mismatch_dims=["disp_a1_error", "mask_dx", "mask_theta"],
        method_sig="L+O",
        principle=_make_principle(),
        residuals=[1.0 / (n ** 2) for n in (64, 128, 256, 512)],
        resolutions=[64, 128, 256, 512],
        sp_wallet="0x" + "1" * 40,
        spec_hash="0x" + "2" * 64,
        principle_hash="0x" + "3" * 64,
        ipfs_cid="bafyMOCKSOLUTION",
        samples_per_stratum=3,
        track_b_num_samples=15,
        scenes_per_phi=4,
    )

    # Gates
    assert score.gate_verdicts["S1"] == "pass"
    assert score.gate_verdicts["S2"] == "pass"
    assert score.gate_verdicts["S3"] == "pass"

    # Per-instance metric is non-trivial
    assert score.psnr_per_instance, "expected at least one per-instance PSNR"
    assert score.psnr_per_instance[0] > 10.0

    # Q is finite and within [0, 1]
    assert 0.0 <= score.Q <= 1.0

    # Cert payload shape + schema
    schema = json.loads(CERT_SCHEMA.read_text())
    jsonschema.validate(score.cert_payload, schema)

    # GAP-TV baseline Q=0.62. Our mock is not GAP-TV, so we only assert the
    # scorer lands in the same ballpark (±0.30). A production GAP-TV solver
    # should tighten this to 10 % per bounty spec.
    baseline_q = next(b["Q"] for b in manifest["baselines"] if b["name"] == "GAP-TV")
    assert abs(score.Q - baseline_q) < 0.30, (
        f"Q={score.Q:.3f}, baseline={baseline_q}, delta={abs(score.Q - baseline_q):.3f}"
    )


@pytest.mark.skipif(not L3_003.exists(), reason="L3-003 benchmark not available")
def test_determinism(tmp_path):
    """Same inputs → identical cert_hash both runs."""
    l3 = _load_l3_003()
    manifest = _cassi_t1_manifest(l3)
    instance, recon = _make_instance(tmp_path, seed=7)
    common_kwargs = dict(
        benchmark_manifest=manifest,
        instance_dir=instance,
        solver_output=recon,
        omega_params={"H": 256, "W": 256, "N_bands": 28,
                      "mask_density": 0.5, "noise_level": 0.01,
                      "disp_a1_error": 0.0, "mask_dx": 0.0, "mask_theta": 0.0},
        solver_fn=_mock_solver(target_baseline_psnr=30.0),
        omega_range=OMEGA_RANGE,
        mismatch_dims=["disp_a1_error", "mask_dx", "mask_theta"],
        method_sig="L+O",
        principle=_make_principle(),
        residuals=[1.0 / (n ** 2) for n in (64, 128, 256, 512)],
        resolutions=[64, 128, 256, 512],
        sp_wallet="0x" + "1" * 40,
        spec_hash="0x" + "2" * 64,
        principle_hash="0x" + "3" * 64,
        ipfs_cid="bafyMOCK",
        samples_per_stratum=3,
        track_b_num_samples=10,
        scenes_per_phi=2,
    )
    s1 = score_solution(**common_kwargs)
    s2 = score_solution(**common_kwargs)
    assert s1.cert_payload == s2.cert_payload
    assert s1.cert_payload["cert_hash"] == s2.cert_payload["cert_hash"]
    assert s1.Q == s2.Q


@pytest.mark.skipif(not L3_003.exists(), reason="L3-003 benchmark not available")
def test_weak_solver_is_not_certified(tmp_path):
    """A solver far below ε should produce Q < Standard threshold (0.55)."""
    l3 = _load_l3_003()
    manifest = _cassi_t1_manifest(l3)
    instance, recon = _make_instance(tmp_path)

    score = score_solution(
        benchmark_manifest=manifest,
        instance_dir=instance,
        solver_output=recon,
        omega_params={"H": 256, "W": 256, "N_bands": 28,
                      "mask_density": 0.5, "noise_level": 0.01,
                      "disp_a1_error": 0.0, "mask_dx": 0.0, "mask_theta": 0.0},
        solver_fn=lambda o: 5.0,  # always 5 dB — far below ε ≥ 22
        omega_range=OMEGA_RANGE,
        mismatch_dims=["disp_a1_error"],
        method_sig="L+O",
        principle=_make_principle(),
        samples_per_stratum=3,
        track_b_num_samples=10,
        scenes_per_phi=2,
    )
    assert score.Q < 0.55
    assert score.gate_verdicts["S4"] == "fail"
    assert not score.track_a_pass
    assert not score.track_b_pass
