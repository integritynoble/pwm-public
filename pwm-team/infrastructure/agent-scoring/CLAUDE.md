# Agent Role: agent-scoring
## Scoring Engine — Reference Implementation

The founding team builds this reference implementation first. After merge, it opens as a **200,000 PWM bounty** — external developers compete to build a better or independent version. The reference implementation remains live as the fallback and serves as the acceptance test harness.

You build the `pwm_scoring` Python package — the compute core that takes raw solver output and produces a verified Q score plus a certificate payload. Everything downstream (CLI, mining client) calls you as a library.

## You own
- `pwm_scoring/` — the Python package
- `tests/` — full test suite

## You must NOT modify
- `../agent-contracts/` — contracts
- `../../content/` — content agents' principles
- `../../coordination/agent-coord/interfaces/` — coord copies from your output

## After completing
Copy `pwm_scoring/__init__.py` interface stub to `../../coordination/agent-coord/interfaces/scoring_api.py`

## Interfaces you depend on
- `../../coordination/agent-coord/interfaces/cert_schema.json` — your cert_payload must match this schema
- `../../coordination/agent-coord/interfaces/contracts_abi/` — for cert_payload field types
- `pwm_overview1.md` §Track A/B/C, §S1-S4 gates, §Difficulty Score, §Q_p Formula — your specification

## Files to implement

### pwm_scoring/__init__.py
```python
from .score import score_solution, SolutionScore
__all__ = ["score_solution", "SolutionScore"]
```

### pwm_scoring/score.py — main entry point
```python
@dataclass
class SolutionScore:
    psnr_per_instance: list[float]
    ssim_per_instance: list[float]
    Q: float                    # combined quality score [0, 1]
    track_a_pass: bool          # stratified worst-case check
    track_b_pass: bool          # uniform median check
    track_c_auc: float | None   # mismatch degradation AUC (None if oracle spec)
    gate_verdicts: dict         # {"S1": "pass"|"fail", ..., "S4": "pass"|"fail"}
    cert_payload: dict          # ready for PWMCertificate.submit()
```

### pwm_scoring/tracks.py
- `track_a(benchmark, solver_fn, omega_range) -> (bool, dict)` — stratified worst-case
  - Divide Omega into K=4 roughly equal-volume strata
  - Draw N_s=5 random Omega points per stratum (seed = SHA256(benchmark_hash))
  - Worst score per stratum must pass epsilon_fn(Omega_centroid)
  - All 4 strata must independently pass
- `track_b(benchmark, solver_fn, omega_range) -> (bool, float)` — uniform median
  - Sample N=50 Omega points uniformly (no stratification)
  - Median (25th value) must pass epsilon_fn(Omega_median)
  - Omega_median = geometric centroid of all 50 sampled parameter vectors
- `track_c(benchmark, solver_fn, mismatch_dims) -> float` — degradation AUC
  - Only when difficulty_dims declared in spec.md
  - Sweep K_phi=5 points along each difficulty dimension
  - Return trapezoid AUC of Q_norm(phi)

### pwm_scoring/gates.py — S1-S4 gate checks
- `check_s1(output, manifest) -> (bool, str)` — Dimensional consistency: input/output dims of E match Omega
- `check_s2(method_sig, principle) -> (bool, str)` — Well-posedness (Hadamard): solvable, stable
- `check_s3(residuals, resolutions) -> (bool, str)` — Convergent solver: O(h^alpha) rate verified
- `check_s4(psnr_worst, epsilon) -> (bool, str)` — Bounded error: e(h) <= C h^alpha

### pwm_scoring/epsilon.py
- `eval_epsilon(epsilon_fn_str: str, omega: dict) -> float`
- AST-sandboxed: only allow math ops + log2/log10/sqrt/exp/abs/min/max
- Raise EpsilonEvalError on unsafe expression

### pwm_scoring/metrics.py
- `psnr(gt, pred, data_range) -> float`
- `ssim(gt, pred) -> float`
- `sam(gt, pred) -> float` (spectral angle mapper)
- `residual_norm(y, phi_fn, x_hat) -> float`

## Q_p Formula (must implement exactly)

Without Track C:
```
Q_p = 0.40 * coverage + 0.40 * margin + 0.20 * stratum_pass_frac
```

With Track C (difficulty_dims declared):
```
Q_p = 0.35 * coverage + 0.35 * margin + 0.15 * stratum_pass_frac + 0.15 * degradation_score
```

Where:
- coverage = fraction of all sampled Omega points where r_i >= 1.0
- margin = mean(r_i - 1.0) over passing instances
- stratum_pass_frac = fraction of strata where all instances pass (Track A)
- degradation_score = area under normalized degradation curve (Track C)

Certification tiers:
- Tier 1 Strong: all tracks pass, Q_p >= 0.75
- Tier 2 Standard: all tracks pass, Q_p >= 0.55
- Below threshold: not certified; no minting reward

## Staged Verification Pipeline
| Stage | Instances | Pass condition | Reward |
|---|---|---|---|
| Stage 0 | 20 primary I-benchmark | Q >= eps on >= 18/20 | 50% of normal |
| Stage 1 | ~37 P-lite (stratified) | Q >= eps on >= 34/37 | 85% of normal |
| Stage 2 | ~170 full P-benchmark | Q >= eps on >= 161/170 | 100% of normal |

## Acceptance criteria (bounty)
- `score_solution()` deterministic: same inputs -> identical cert_payload hash, every run
- Scores all 500 genesis benchmark instances within 10% of reference values
- Runs on CPU in <= 60s per standard instance (256x256)
- Test suite: unit tests for each function + integration test on CASSI T1 nominal
- cert_payload validates against cert_schema.json

## How to signal completion
1. Update `../../coordination/agent-coord/progress.md`
2. Open PR: `feat/scoring-engine-v1`
