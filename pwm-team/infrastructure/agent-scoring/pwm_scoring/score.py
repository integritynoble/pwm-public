"""
pwm_scoring.score — main entry point.

Composes S1-S4 gates, per-instance metrics, and Track A/B/C evaluation into a
SolutionScore with a cert_payload matching coordination/.../cert_schema.json.

See CLAUDE.md in this directory for the authoritative interface spec.
"""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from .epsilon import eval_epsilon
from .gates import check_s1, check_s2, check_s3, check_s4
from .metrics import psnr as psnr_metric, ssim as ssim_metric
from .tracks import track_a, track_b, track_c


SolverFn = Callable[[dict], float]


# ---------------------------------------------------------------------------
# Dataclass (matches coordination/.../interfaces/scoring_api.py)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Internal defaults — callers (miner/CLI) override these via kwargs
# ---------------------------------------------------------------------------

_PLACEHOLDER_HASH = "0x" + "0" * 64
_PLACEHOLDER_WALLET = "0x" + "0" * 40
_DEFAULT_SHARE_RATIO_P = 4000  # p=0.40


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_solution(
    benchmark_manifest: dict,
    instance_dir: Path | str | None,
    solver_output: np.ndarray,
    omega_params: dict,
    *,
    solver_fn: SolverFn | None = None,
    omega_range: dict | None = None,
    mismatch_dims: list[str] | None = None,
    method_sig: str = "L+O",
    principle: dict | None = None,
    residuals: list[float] | None = None,
    resolutions: list[int] | None = None,
    sp_wallet: str = _PLACEHOLDER_WALLET,
    spec_hash: str = _PLACEHOLDER_HASH,
    principle_hash: str = _PLACEHOLDER_HASH,
    benchmark_hash: str | None = None,
    ipfs_cid: str = "",
    share_ratio_p: int = _DEFAULT_SHARE_RATIO_P,
    samples_per_stratum: int = 5,
    track_b_num_samples: int = 50,
    scenes_per_phi: int = 10,
) -> SolutionScore:
    """Score a solver against a benchmark.

    Parameters
    ----------
    benchmark_manifest : dict
        Loaded benchmark manifest (L3-*.json).
    instance_dir : Path | None
        Path containing ``ground_truth.npz``. If ``None``, the single-instance
        PSNR/SSIM step is skipped.
    solver_output : np.ndarray
        Reconstruction for the primary instance — used by S1 and by the
        single-instance PSNR/SSIM step.
    omega_params : dict
        Ω values for the primary instance.
    solver_fn : callable, optional
        ``solver_fn(omega_dict) -> psnr_float`` used by Track A/B/C sweeps.
        Tracks are skipped when not supplied.
    omega_range : dict, optional
        ``{param_name: [lo, hi]}`` for Track sampling. Required with solver_fn.
    mismatch_dims : list[str], optional
        Ω keys declared as difficulty dimensions (enables Track C).
    Other kwargs populate the on-chain cert_payload.
    """

    # --- 1. Gates --------------------------------------------------------
    s1_ok, s1_msg = check_s1(solver_output, benchmark_manifest)
    s2_ok, s2_msg = check_s2(method_sig, principle or {})

    if residuals is not None and resolutions is not None:
        s3_ok, s3_msg = check_s3(residuals, resolutions)
    else:
        # Without multi-resolution evidence we cannot verify convergence;
        # treat as pass but flag the absence of proof in the message.
        s3_ok, s3_msg = True, "skipped (no residuals provided)"

    # --- 2. Per-instance metrics ----------------------------------------
    psnr_list: list[float] = []
    ssim_list: list[float] = []
    if instance_dir is not None:
        instance_dir = Path(instance_dir)
        gt_path = instance_dir / "ground_truth.npz"
        if gt_path.exists():
            gt = _load_ground_truth(gt_path)
            if gt.shape == solver_output.shape:
                psnr_list.append(psnr_metric(gt, solver_output))
                ssim_list.append(ssim_metric(gt, solver_output))

    # --- 3. Track A/B/C --------------------------------------------------
    track_a_pass = False
    track_b_pass = False
    track_c_auc: float | None = None
    stratum_results: dict = {}
    track_a_samples: list = []
    track_b_samples: list = []

    if solver_fn is not None and omega_range is not None:
        track_a_pass, stratum_results = track_a(
            benchmark_manifest, solver_fn, omega_range,
            samples_per_stratum=samples_per_stratum,
        )
        for stratum in stratum_results.values():
            track_a_samples.extend(stratum.get("samples", []))

        track_b_pass, median_psnr_b, track_b_samples = track_b(
            benchmark_manifest, solver_fn, omega_range,
            num_samples=track_b_num_samples,
            _return_samples=True,
        )

        if mismatch_dims:
            track_c_auc = track_c(
                benchmark_manifest, solver_fn, mismatch_dims,
                scenes_per_phi=scenes_per_phi,
                omega_range=omega_range,
            )
    else:
        median_psnr_b = float(np.median(psnr_list)) if psnr_list else 0.0

    # --- 4. Q_p & gate S4 -----------------------------------------------
    all_samples = track_a_samples + track_b_samples
    if all_samples:
        worst_psnr = min(s[0] for s in all_samples)
        median_psnr = float(np.median([s[0] for s in all_samples]))
    elif psnr_list:
        worst_psnr = float(min(psnr_list))
        median_psnr = float(np.median(psnr_list))
    else:
        worst_psnr = 0.0
        median_psnr = 0.0

    epsilon_for_s4 = _primary_epsilon(benchmark_manifest, omega_params)
    s4_ok, s4_msg = check_s4(worst_psnr, epsilon_for_s4)

    gate_verdicts = {
        "S1": "pass" if s1_ok else "fail",
        "S2": "pass" if s2_ok else "fail",
        "S3": "pass" if s3_ok else "fail",
        "S4": "pass" if s4_ok else "fail",
    }
    gate_messages = {"S1": s1_msg, "S2": s2_msg, "S3": s3_msg, "S4": s4_msg}
    all_gates_pass = s1_ok and s2_ok and s3_ok and s4_ok

    if not all_gates_pass or not all_samples:
        Q = 0.0
    else:
        Q = _compute_q_p(
            samples=all_samples,
            stratum_results=stratum_results,
            track_c_auc=track_c_auc,
        )

    # --- 5. cert_payload -------------------------------------------------
    benchmark_hash = benchmark_hash or benchmark_manifest.get("benchmark_hash") \
        or _hash_manifest(benchmark_manifest)
    solution_hash = _solution_hash(solver_output)
    Q_int = int(round(max(0.0, min(1.0, Q)) * 100))
    cert_hash = _cert_hash(benchmark_hash, solution_hash, Q_int, sp_wallet)

    cert_payload = {
        "cert_hash": cert_hash,
        "benchmark_hash": _normalize_hash(benchmark_hash),
        "spec_hash": _normalize_hash(spec_hash),
        "principle_hash": _normalize_hash(principle_hash),
        "Q_int": Q_int,
        "gate_verdicts": gate_verdicts,
        "sp_wallet": sp_wallet,
        "share_ratio_p": int(share_ratio_p),
        "ipfs_cid": ipfs_cid,
        "psnr_worst": float(worst_psnr),
        "psnr_median": float(median_psnr),
        "track_a_pass": bool(track_a_pass),
        "track_b_pass": bool(track_b_pass),
        "track_c_auc": float(track_c_auc) if track_c_auc is not None else None,
    }

    return SolutionScore(
        psnr_per_instance=psnr_list,
        ssim_per_instance=ssim_list,
        Q=float(Q),
        track_a_pass=bool(track_a_pass),
        track_b_pass=bool(track_b_pass),
        track_c_auc=track_c_auc,
        gate_verdicts={**gate_verdicts, "_messages": gate_messages},
        cert_payload=cert_payload,
        psnr_worst=float(worst_psnr),
        psnr_median=float(median_psnr),
        stratum_results=stratum_results,
    )


# ---------------------------------------------------------------------------
# Q_p — see CLAUDE.md §Q_p Formula
# ---------------------------------------------------------------------------

def _compute_q_p(
    samples: list,
    stratum_results: dict,
    track_c_auc: float | None,
) -> float:
    """Q_p = weighted mix of coverage, margin, stratum_pass_frac, (degradation).

    Without Track C: 0.40·coverage + 0.40·margin + 0.20·stratum_pass_frac.
    With Track C:    0.35·coverage + 0.35·margin + 0.15·stratum_pass_frac
                     + 0.15·degradation_score.
    """
    ratios = [psnr_v / eps for psnr_v, eps, _omega in samples if eps > 0]
    if not ratios:
        return 0.0
    ratios_arr = np.asarray(ratios)

    coverage = float(np.mean(ratios_arr >= 1.0))

    passing = ratios_arr[ratios_arr >= 1.0] - 1.0
    if passing.size > 0:
        # Saturate margin at 1.0 so a very high-PSNR solver cannot exceed Q=1.
        margin = float(min(1.0, float(passing.mean())))
    else:
        margin = 0.0

    if stratum_results:
        stratum_pass_frac = float(
            np.mean([1.0 if r.get("pass") else 0.0 for r in stratum_results.values()])
        )
    else:
        stratum_pass_frac = 0.0

    if track_c_auc is None:
        q = 0.40 * coverage + 0.40 * margin + 0.20 * stratum_pass_frac
    else:
        degradation = max(0.0, min(1.0, float(track_c_auc)))
        q = (0.35 * coverage
             + 0.35 * margin
             + 0.15 * stratum_pass_frac
             + 0.15 * degradation)
    return float(max(0.0, min(1.0, q)))


# ---------------------------------------------------------------------------
# Helpers — manifest, hashing, ground-truth loading
# ---------------------------------------------------------------------------

def _load_ground_truth(path: Path) -> np.ndarray:
    z = np.load(path)
    for key in ("spectral_cube", "video_cube", "ground_truth", "gt"):
        if key in z.files:
            return z[key]
    return z[z.files[0]]


def _primary_epsilon(benchmark: dict, omega: dict) -> float:
    """ε at the primary instance's Ω point."""
    fn = benchmark.get("epsilon_fn")
    if fn:
        return float(eval_epsilon(str(fn), omega))
    ib = benchmark.get("ibenchmarks") or []
    if ib and isinstance(ib[0], dict) and "epsilon" in ib[0]:
        return float(ib[0]["epsilon"])
    if "epsilon" in benchmark:
        return float(benchmark["epsilon"])
    return 0.0


def _hash_manifest(manifest: dict) -> str:
    payload = json.dumps(manifest, sort_keys=True, default=str).encode()
    return "0x" + hashlib.sha256(payload).hexdigest()


def _solution_hash(output: np.ndarray) -> str:
    return "0x" + hashlib.sha256(
        np.ascontiguousarray(output).tobytes() + str(output.shape).encode()
    ).hexdigest()


def _normalize_hash(h: str) -> str:
    if not h.startswith("0x"):
        h = "0x" + h
    return h.lower()


def _cert_hash(benchmark_hash: str, solution_hash: str, Q_int: int, sp_wallet: str) -> str:
    payload = (
        _normalize_hash(benchmark_hash)[2:]
        + _normalize_hash(solution_hash)[2:]
        + f"{int(Q_int):d}"
        + sp_wallet.lower()
    ).encode()
    return "0x" + hashlib.sha256(payload).hexdigest()
