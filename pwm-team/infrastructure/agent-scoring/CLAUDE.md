# Agent Role: agent-scoring
## Scoring Engine Developer

You build the `pwm_scoring` Python package — the compute core that takes raw solver output and produces a verified Q score plus a certificate payload. Everything downstream (CLI, mining client) calls you as a library.

## You own
- `pwm_scoring/` — the Python package
- `tests/` — full test suite

## You must NOT modify
- `../agent-contracts/` — contracts
- `../agent-cli/` — CLI (it imports you, you don't import it)
- `../agent-miner/` — mining client
- `../agent-web/` — web explorer
- `../agent-*/principles/` — content

## After completing M1.2
Copy `pwm_scoring/__init__.py` interface stub to `../agent-coord/interfaces/scoring_api.py`

## Interfaces you depend on
- `../agent-coord/interfaces/cert_schema.json` — your cert_payload must match this schema
- `pwm_overview1.md` §Track A/B/C, §S1-S4 gates, §Difficulty Score — your specification

## Files to implement

### pwm_scoring/__init__.py
```python
from .score import score_solution, SolutionScore
__all__ = ["score_solution", "SolutionScore"]
```

### pwm_scoring/score.py — main entry point
```python
from dataclasses import dataclass
from pathlib import Path
import numpy as np

@dataclass
class SolutionScore:
    psnr_per_instance: list[float]
    ssim_per_instance: list[float]
    Q: float                    # combined quality score [0, 1]
    track_a_pass: bool          # stratified worst-case check
    track_b_pass: bool          # uniform median check
    track_c_auc: float | None   # mismatch degradation AUC (None if oracle spec)
    gate_verdicts: dict         # {"S1": "pass"|"fail", "S2": ..., "S3": ..., "S4": ...}
    cert_payload: dict          # ready for PWMCertificate.submit()

def score_solution(
    benchmark_manifest: dict,
    instance_dir: Path,
    solver_output: np.ndarray,
    omega_params: dict,
) -> SolutionScore:
    ...  # TODO: implement
```

### pwm_scoring/tracks.py
- `track_a(benchmark, solver_fn, omega_range) -> (bool, dict)` — stratified worst-case
  - Divide Ω into strata by H×W (CASSI/CACTI) or primary difficulty dim
  - Draw 5 random Ω points per stratum (seed = SHA256(benchmark_hash))
  - Worst score per stratum must pass epsilon_fn(Ω_centroid)
  - All strata must independently pass
- `track_b(benchmark, solver_fn, omega_range) -> (bool, float)` — uniform median
  - Sample 50 Ω points uniformly
  - Median must pass epsilon_fn(Ω_median)
- `track_c(benchmark, solver_fn, mismatch_dims) -> float` — degradation AUC
  - Sweep phi ∈ {0, 0.25, 0.50, 0.75, 1.0}
  - At each phi: 10 scenes, record median PSNR
  - Return trapezoid AUC of Q_norm(phi) = PSNR(phi) / epsilon_fn(Omega at phi)

### pwm_scoring/gates.py
- `check_s1(output, manifest) -> (bool, str)` — dimensions, mask consistency
- `check_s2(method_sig, principle) -> (bool, str)` — solver method vs well-posedness
- `check_s3(residuals, resolutions) -> (bool, str)` — O(h²) convergence rate
- `check_s4(psnr_worst, epsilon) -> (bool, str)` — worst PSNR ≥ ε

### pwm_scoring/epsilon.py
- `eval_epsilon(epsilon_fn_str: str, omega: dict) -> float`
- AST-sandboxed: only allow math ops + log2/log10/sqrt; no imports, no exec
- Raise EpsilonEvalError on unsafe expression

### pwm_scoring/metrics.py
- `psnr(gt: np.ndarray, pred: np.ndarray) -> float`
- `ssim(gt: np.ndarray, pred: np.ndarray) -> float`
- `sam(gt: np.ndarray, pred: np.ndarray) -> float`  (spectral angle mapper)
- `residual_norm(y: np.ndarray, phi: np.ndarray, x_hat: np.ndarray) -> float`

## Definition of done
- `score_solution()` deterministic: same inputs → identical cert_payload hash, every run
- Scores all CASSI and CACTI genesis benchmarks within 10% of reference values
- Runs on CPU in ≤60s per standard instance (256×256)
- Test suite: unit tests for each function + integration test on CASSI T1 nominal
- cert_payload validates against ../agent-coord/interfaces/cert_schema.json

## How to signal completion
1. Update `../agent-coord/progress.md` — mark M1.2 DONE
2. Open PR: `feat/scoring-engine-v1`
