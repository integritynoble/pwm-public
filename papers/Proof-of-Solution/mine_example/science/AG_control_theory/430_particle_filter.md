# Principle #430 — Particle Filter (Sequential Monte Carlo)

**Domain:** Control Theory & Dynamical Systems | **Carrier:** signal | **Difficulty:** Standard (δ=3)
**DAG:** S.random → N.pointwise → ∫.ensemble |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.random→N.pointwise→∫.ensemble      PF-est      NonGaussTrack-10  SIR/APF
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PARTICLE FILTER (SMC)      P = (E, G, W, C)   Principle #430   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ x(k+1) ~ p(x(k+1)|x(k));  y(k) ~ p(y(k)|x(k))       │
│        │ Approximate p(x(k)|y(1:k)) with weighted particles    │
│        │ x̂ = Σ wᵢ xᵢ;  resample when N_eff < threshold        │
│        │ Inverse: full posterior over nonlinear/non-Gaussian x  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.random] ──→ [N.pointwise] ──→ [∫.ensemble]          │
│        │  sample  nonlinear  integrate                           │
│        │ V={S.random, N.pointwise, ∫.ensemble}  A={S.random→N.pointwise, N.pointwise→∫.ensemble}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (for bounded likelihood)                │
│        │ Uniqueness: asymptotic (N→∞ converges to true post.)   │
│        │ Stability: CONDITIONAL on particle degeneracy control  │
│        │ Mismatch: proposal distribution, model errors          │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSE (primary), effective sample size (secondary)  │
│        │ q = O(1/√N) convergence rate in particle count        │
│        │ T = {residual_norm, N_eff, ESS, NEES}                  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Particle count N and state dimension consistent; weights sum to 1 | PASS |
| S2 | Likelihood bounded → importance weights finite | PASS |
| S3 | SIR with systematic resampling controls degeneracy | PASS |
| S4 | RMSE decreases as O(1/√N) verified empirically | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# control/particle_filter_s1_ideal.yaml
principle_ref: sha256:<p430_hash>
omega:
  description: "Bimodal tracking, n=4, non-Gaussian posterior"
  time_steps: 200
  dt: 0.05
E:
  forward: "x(k+1) ~ p(x|x_prev); y ~ p(y|x)"
  likelihood: "mixture of Gaussians"
I:
  dataset: NonGaussTrack_10
  trajectories: 10
  noise: {type: non_gaussian, mixture_components: 2}
  scenario: ideal
O: [RMSE, ESS, log_likelihood]
epsilon:
  RMSE_max: 0.10
  ESS_min: 0.3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | N=1000 particles for n=4 state space sufficient | PASS |
| S2 | Mixture likelihood bounded; weights computable | PASS |
| S3 | ESS stays above 30% with resampling | PASS |
| S4 | RMSE < 0.10 feasible with N=1000 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# control/benchmark_pf_s1.yaml
spec_ref: sha256:<spec430_hash>
principle_ref: sha256:<p430_hash>
dataset:
  name: NonGaussTrack_10
  trajectories: 10
  time_steps: 200
  data_hash: sha256:<dataset_430_hash>
baselines:
  - solver: SIR-PF
    params: {N: 1000, resampling: systematic}
    results: {RMSE: 0.052, ESS: 0.45}
  - solver: APF
    params: {N: 1000}
    results: {RMSE: 0.038, ESS: 0.55}
  - solver: EKF
    params: {}
    results: {RMSE: 0.120, ESS: null}
quality_scoring:
  - {max_RMSE: 0.025, Q: 1.00}
  - {max_RMSE: 0.040, Q: 0.90}
  - {max_RMSE: 0.070, Q: 0.80}
  - {max_RMSE: 0.100, Q: 0.75}
```

**Baseline solver:** SIR-PF — RMSE 0.052
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | RMSE | ESS | Runtime | Q |
|--------|------|-----|---------|---|
| SIR-PF (N=1000) | 0.052 | 0.45 | 2.0 s | 0.83 |
| APF (N=1000) | 0.038 | 0.55 | 2.5 s | 0.91 |
| Rao-Blackwellized PF | 0.030 | 0.60 | 3.0 s | 0.94 |
| EKF | 0.120 | — | 0.05 s | 0.72 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (RBPF):  300 × 0.94 = 282 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p430_hash>",
  "h_s": "sha256:<spec430_hash>",
  "h_b": "sha256:<bench430_hash>",
  "r": {"residual_norm": 0.030, "error_bound": 0.10, "ratio": 0.30},
  "c": {"fitted_rate": 0.48, "theoretical_rate": 0.50, "K": 4},
  "Q": 0.94,
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"}
}
```

---

## Reward Summary

| Layer | Seed Reward | Ongoing Royalties |
|-------|-------------|-------------------|
| L1 Principle | 200 PWM | 5% of L4 mints |
| L2 spec.md | 105 PWM | 10% of L4 mints |
| L3 Benchmark | 60 PWM | 15% of L4 mints |
| L4 Solution | — | 225–282 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep particle_filter
pwm-node verify control/particle_filter_s1_ideal.yaml
pwm-node mine control/particle_filter_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
