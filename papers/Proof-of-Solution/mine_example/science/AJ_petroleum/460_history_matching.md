# Principle #460 — History Matching (Reservoir Inverse)

**Domain:** Petroleum Engineering | **Carrier:** N/A (inverse problem) | **Difficulty:** Advanced (δ=4)
**DAG:** [∂.time] --> [N.darcy] --> [∂.space] --> [O.bayesian] | **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.t-->N.darcy-->∂.x-->O.bayes  HistMatch  PUNQ-S3  EnKF/adjoint
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  HISTORY MATCHING (RESERVOIR INVERSE) P = (E,G,W,C) Princ. #460│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ min_m J(m) = ½‖d_obs − g(m)‖²_{C_d} + ½‖m−m_pr‖²_{C_m}│
│        │ g(m) = forward reservoir simulator output              │
│        │ m = {permeability, porosity, rel-perm params}          │
│        │ d_obs = observed production data (rates, pressures)    │
│        │ Inverse: given d_obs → estimate m that minimizes J     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.t] ──→ [N.darcy] ──→ [∂.x] ──→ [O.bayes]            │
│        │  time-step  Darcy-flux  spatial-disc  history-match    │
│        │ V={∂.t,N.darcy,∂.x,O.bayes}  A={∂.t→N.darcy,N.darcy→∂.x,∂.x→O.bayes}  L_DAG=3.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (minimizer of J exists for bounded m)   │
│        │ Uniqueness: NO (ill-posed; regularization required)    │
│        │ Stability: depends on C_m regularization strength      │
│        │ Mismatch: model error, non-Gaussian parameter priors   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = data misfit ‖d_obs − g(m*)‖₂/‖d_obs‖₂ (primary)  │
│        │ q = N/A (iterative); convergence by J reduction       │
│        │ T = {J_reduction, data_misfit, param_uncertainty}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Objective J well-formed; covariance matrices SPD | PASS |
| S2 | Regularization ensures bounded minimizer; Tikhonov-type | PASS |
| S3 | EnKF and adjoint-gradient methods converge for PUNQ-class | PASS |
| S4 | Data misfit reduction measurable; posterior uncertainty quantified | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# hist_match/punqs3_s1_ideal.yaml
principle_ref: sha256:<p460_hash>
omega:
  grid: [19, 28, 5]
  domain: PUNQ_S3_reservoir
  time: [0, 5475.0]
  observations: 89_production_data_points
E:
  inverse: "min J = ½‖d−g(m)‖²_Cd + ½‖m−m_pr‖²_Cm"
  parameters: [log_permeability, porosity]
  n_params: 1761
B:
  wells: 6_producers
  observations: [BHP, WOR, GOR]
I:
  scenario: PUNQ_S3_history_match
  ensemble_sizes: [50, 100, 200]
O: [data_misfit, param_RMSE, P10_P50_P90_forecast]
epsilon:
  data_misfit_max: 1.5
  param_RMSE_max: 0.3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 89 observations, 1761 parameters; C_d from measurement error | PASS |
| S2 | Prior regularization ensures bounded inverse; ensemble ≥ 50 | PASS |
| S3 | EnKF converges within 10 assimilation steps | PASS |
| S4 | Data misfit < 1.5 (χ² normalized) achievable | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# hist_match/benchmark_punqs3.yaml
spec_ref: sha256:<spec460_hash>
principle_ref: sha256:<p460_hash>
dataset:
  name: PUNQ_S3_benchmark
  reference: "Floris et al. (2001) PUNQ-S3 history matching benchmark"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: EnKF (N=50)
    params: {ensemble: 50, localization: distance_based}
    results: {data_misfit: 2.1, param_RMSE: 0.28}
  - solver: EnKF (N=100)
    params: {ensemble: 100, localization: distance_based}
    results: {data_misfit: 1.4, param_RMSE: 0.22}
  - solver: Adjoint-gradient (L-BFGS)
    params: {max_iter: 50}
    results: {data_misfit: 0.95, param_RMSE: 0.18}
quality_scoring:
  - {min_misfit: 0.8, Q: 1.00}
  - {min_misfit: 1.2, Q: 0.90}
  - {min_misfit: 1.8, Q: 0.80}
  - {min_misfit: 2.5, Q: 0.75}
```

**Baseline solver:** EnKF (N=100) — data misfit 1.4
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Data Misfit | Param RMSE | Runtime | Q |
|--------|-------------|------------|---------|---|
| EnKF (N=50) | 2.1 | 0.28 | 120 s | 0.75 |
| EnKF (N=100) | 1.4 | 0.22 | 240 s | 0.90 |
| EnKF (N=200) | 1.1 | 0.19 | 480 s | 0.90 |
| Adjoint (L-BFGS) | 0.95 | 0.18 | 350 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (adjoint): 400 × 1.00 = 400 PWM
Floor:               400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p460_hash>",
  "h_s": "sha256:<spec460_hash>",
  "h_b": "sha256:<bench460_hash>",
  "r": {"data_misfit": 0.95, "error_bound": 1.5, "ratio": 0.633},
  "c": {"J_reduction": 0.92, "forecast_spread": 0.15, "K": 3},
  "Q": 1.00,
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
| L4 Solution | — | 300–400 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep hist_match
pwm-node verify hist_match/punqs3_s1_ideal.yaml
pwm-node mine hist_match/punqs3_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
