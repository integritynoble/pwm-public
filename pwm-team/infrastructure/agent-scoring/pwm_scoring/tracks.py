"""Track A / B / C evaluation — see CLAUDE.md §Q_p Formula and §Tracks.

All tracks accept a ``solver_fn(omega: dict) -> float`` callable that returns
the PSNR (in dB) for a reconstructed sample at the given parameter point.
"""
from __future__ import annotations
import hashlib
import json
import re
from typing import Callable, Iterable

import numpy as np

from .epsilon import eval_epsilon


SolverFn = Callable[[dict], float]

_DEFAULT_SAMPLES_PER_STRATUM = 5
_DEFAULT_TRACK_B_SAMPLES = 50
_DEFAULT_PHI_POINTS = [0.0, 0.25, 0.50, 0.75, 1.0]
_DEFAULT_SCENES_PER_PHI = 10


# ---------------------------------------------------------------------------
# Seeding & sampling
# ---------------------------------------------------------------------------

def _seed_from_benchmark(benchmark: dict, salt: str = "") -> int:
    """Stable per-benchmark seed. Uses explicit benchmark_hash if present,
    else hashes the manifest JSON. The salt namespaces tracks so Track A and
    Track B draw different points from the same benchmark.
    """
    h = benchmark.get("benchmark_hash")
    if not h:
        payload = json.dumps(benchmark, sort_keys=True, default=str).encode()
        h = hashlib.sha256(payload).hexdigest()
    h_clean = h[2:] if h.startswith("0x") else h
    mix = hashlib.sha256((h_clean + "|" + salt).encode()).hexdigest()
    return int(mix, 16) % (2 ** 32)


def _sample_uniform(omega_range: dict, rng: np.random.Generator) -> dict:
    """Draw one Ω vector by uniformly sampling each declared range."""
    omega = {}
    for k, bounds in omega_range.items():
        lo, hi = float(bounds[0]), float(bounds[1])
        if lo == hi:
            omega[k] = lo
        elif k in ("H", "W", "N_bands", "N"):
            omega[k] = float(rng.integers(int(lo), int(hi) + 1))
        else:
            omega[k] = float(rng.uniform(lo, hi))
    return omega


def _centroid(samples: list[dict]) -> dict:
    """Arithmetic mean per key across sampled Ω vectors."""
    keys = samples[0].keys()
    return {k: float(np.mean([s[k] for s in samples])) for k in keys}


# ---------------------------------------------------------------------------
# Stratum parsing (from L3-003-style manifests)
# ---------------------------------------------------------------------------

_STRATUM_RE = re.compile(
    r"(?:(?P<lo>\d+)\s*\^2\s*<\s*HW\s*<=\s*(?P<hi>\d+)\s*\^2)"
    r"|(?:<=\s*(?P<hi_only>\d+)\s*\^2)"
    r"|(?:>\s*(?P<lo_only>\d+)\s*\^2)",
    re.IGNORECASE,
)


def _parse_hw_range(expr: str) -> tuple[float, float]:
    """Turn a string like '256^2 < HW <= 512^2' into numeric (lo, hi) bounds on H*W."""
    m = _STRATUM_RE.search(expr.replace(" ", ""))
    if not m:
        raise ValueError(f"cannot parse H_W_range '{expr}'")
    if m.group("lo") is not None:
        lo = int(m.group("lo")) ** 2
        hi = int(m.group("hi")) ** 2
        return float(lo), float(hi)
    if m.group("hi_only") is not None:
        return 0.0, float(int(m.group("hi_only")) ** 2)
    lo_only = int(m.group("lo_only")) ** 2
    return float(lo_only), float("inf")


def _strata_from_manifest(benchmark: dict) -> list[dict]:
    """Return a list of strata dicts with keys: name, hw_lo, hw_hi."""
    tracks = (benchmark.get("p_benchmark") or {}).get("tracks") or {}
    ta = tracks.get("track_A_stratified_worst_case") or {}
    out = []
    for s in ta.get("strata", []):
        lo, hi = _parse_hw_range(s.get("H_W_range", ""))
        out.append({"name": s["name"], "hw_lo": lo, "hw_hi": hi})
    return out


# ---------------------------------------------------------------------------
# Track A — stratified worst-case
# ---------------------------------------------------------------------------

def track_a(
    benchmark: dict,
    solver_fn: SolverFn,
    omega_range: dict,
    samples_per_stratum: int = _DEFAULT_SAMPLES_PER_STRATUM,
) -> tuple[bool, dict]:
    """Stratified worst-case evaluation.

    For each stratum defined in the manifest, draw N_s samples whose H*W falls
    within the stratum's range, run the solver, and require the worst PSNR to
    clear ε(Ω_centroid). All strata must pass independently.

    Each stratum result includes a ``samples`` list of ``(psnr, epsilon, omega)``
    tuples so callers can reuse the raw data (e.g. for Q_p coverage/margin).
    """
    strata = _strata_from_manifest(benchmark)
    if not strata:
        raise ValueError("benchmark manifest has no Track A strata declared")

    eps_fn = _epsilon_fn_str(benchmark)
    seed = _seed_from_benchmark(benchmark, salt="track_a")
    rng = np.random.default_rng(seed)

    results: dict = {}
    all_pass = True
    for s in strata:
        omegas, psnrs = [], []
        attempts = 0
        while len(omegas) < samples_per_stratum and attempts < 10_000:
            attempts += 1
            o = _sample_uniform(omega_range, rng)
            hw = o.get("H", 0) * o.get("W", 0)
            if s["hw_lo"] < hw <= s["hw_hi"] or (s["hw_lo"] == 0.0 and hw <= s["hw_hi"]):
                omegas.append(o)
                psnrs.append(float(solver_fn(o)))
        if len(omegas) < samples_per_stratum:
            results[s["name"]] = {
                "worst_psnr": float("nan"),
                "epsilon": float("nan"),
                "pass": False,
                "samples": [],
                "reason": "could not fill stratum with declared omega_range",
            }
            all_pass = False
            continue

        worst = float(min(psnrs))
        centroid = _centroid(omegas)
        eps = eval_epsilon(eps_fn, centroid)
        sample_eps = [float(eval_epsilon(eps_fn, o)) for o in omegas]
        passed = worst >= eps
        all_pass = all_pass and passed
        results[s["name"]] = {
            "worst_psnr": worst,
            "epsilon": float(eps),
            "pass": bool(passed),
            "n": len(omegas),
            "samples": list(zip(psnrs, sample_eps, omegas)),
        }
    return bool(all_pass), results


# ---------------------------------------------------------------------------
# Track B — uniform median
# ---------------------------------------------------------------------------

def track_b(
    benchmark: dict,
    solver_fn: SolverFn,
    omega_range: dict,
    num_samples: int = _DEFAULT_TRACK_B_SAMPLES,
    *,
    _return_samples: bool = False,
) -> tuple[bool, float] | tuple[bool, float, list]:
    """Uniform median evaluation across Ω.

    Median PSNR over ``num_samples`` draws must clear ε(Ω_median).

    When ``_return_samples=True`` the return is extended to
    ``(pass, median_psnr, samples)`` where samples is a list of
    ``(psnr, epsilon, omega)`` tuples — used internally by score.py.
    """
    eps_fn = _epsilon_fn_str(benchmark)
    seed = _seed_from_benchmark(benchmark, salt="track_b")
    rng = np.random.default_rng(seed)

    omegas = [_sample_uniform(omega_range, rng) for _ in range(num_samples)]
    psnrs = [float(solver_fn(o)) for o in omegas]
    sample_eps = [float(eval_epsilon(eps_fn, o)) for o in omegas]
    median_psnr = float(np.median(psnrs))
    centroid = _centroid(omegas)
    eps = eval_epsilon(eps_fn, centroid)
    pass_ = bool(median_psnr >= eps)
    if _return_samples:
        return pass_, median_psnr, list(zip(psnrs, sample_eps, omegas))
    return pass_, median_psnr


# ---------------------------------------------------------------------------
# Track C — mismatch degradation AUC
# ---------------------------------------------------------------------------

def track_c(
    benchmark: dict,
    solver_fn: SolverFn,
    mismatch_dims: list[str],
    scenes_per_phi: int = _DEFAULT_SCENES_PER_PHI,
    omega_range: dict | None = None,
) -> float | None:
    """Mismatch degradation curve AUC.

    Returns the trapezoidal AUC of Q_norm(φ) = PSNR(φ) / ε(Ω_at_φ) across the
    sweep points, or ``None`` if the benchmark declares no mismatch dimensions.
    """
    if not mismatch_dims:
        return None

    sweep = _sweep_points(benchmark, mismatch_dims, omega_range or {})
    if not sweep:
        return None

    eps_fn = _epsilon_fn_str(benchmark)
    seed = _seed_from_benchmark(benchmark, salt="track_c")
    rng = np.random.default_rng(seed)

    base_omega = _base_omega(omega_range or {})
    phis, q_norms = [], []
    for pt in sweep:
        phi = float(pt["phi"])
        scene_psnrs = []
        for _ in range(scenes_per_phi):
            omega = {**base_omega}
            omega.update({k: v for k, v in pt.items() if k != "phi"})
            # jitter free dims slightly so repeated calls sample real scenes
            if omega_range:
                jitter = _sample_uniform(
                    {k: omega_range[k] for k in omega_range if k not in omega},
                    rng,
                )
                omega.update(jitter)
            scene_psnrs.append(float(solver_fn(omega)))
        median = float(np.median(scene_psnrs))
        eps = eval_epsilon(eps_fn, {**base_omega, **pt})
        phis.append(phi)
        q_norms.append(median / eps if eps > 0 else 0.0)

    order = np.argsort(phis)
    phis_arr = np.asarray(phis)[order]
    q_arr = np.asarray(q_norms)[order]
    auc = float(np.trapezoid(q_arr, phis_arr))
    # normalize by φ-range so AUC is comparable across benchmarks
    span = float(phis_arr[-1] - phis_arr[0]) or 1.0
    return auc / span


# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------

def _epsilon_fn_str(benchmark: dict) -> str:
    """Pull the ε-formula out of the manifest. Accept a plain float/int by
    wrapping it into a constant expression."""
    fn = benchmark.get("epsilon_fn")
    if fn:
        return str(fn)
    ib = benchmark.get("ibenchmarks") or []
    if ib and isinstance(ib[0], dict) and "epsilon" in ib[0]:
        return str(ib[0]["epsilon"])
    if "epsilon" in benchmark:
        return str(benchmark["epsilon"])
    raise ValueError("benchmark manifest has no epsilon_fn / epsilon")


def _sweep_points(
    benchmark: dict,
    mismatch_dims: list[str],
    omega_range: dict,
) -> list[dict]:
    """Prefer explicit sweep_points from the manifest; else linearly interpolate
    each mismatch dim between 0 and its declared upper bound."""
    tc = (benchmark.get("p_benchmark") or {}).get("tracks", {}).get(
        "track_C_mismatch_degradation"
    ) or {}
    pts = tc.get("sweep_points")
    if pts:
        return [dict(p) for p in pts]

    pts = []
    for phi in _DEFAULT_PHI_POINTS:
        d = {"phi": phi}
        for dim in mismatch_dims:
            hi = float(omega_range.get(dim, [0.0, 0.0])[1])
            d[dim] = phi * hi
        pts.append(d)
    return pts


def _base_omega(omega_range: dict) -> dict:
    """Midpoint of every declared range — used as the baseline Ω for Track C."""
    return {k: 0.5 * (float(v[0]) + float(v[1])) for k, v in omega_range.items()}
