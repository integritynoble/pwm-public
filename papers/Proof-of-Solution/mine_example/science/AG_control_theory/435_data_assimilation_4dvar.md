# Principle #435 — Data Assimilation (4D-Var)

**Domain:** Control Theory & Dynamical Systems | **Carrier:** signal | **Difficulty:** Research (δ=5)
**DAG:** ∂.time → L.state → S.observation → O.adjoint |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→L.state→S.observation→O.adjoint      4DVar       Assim-10          Adjoint/L-BFGS
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  DATA ASSIMILATION (4D-VAR)  P = (E, G, W, C)  Principle #435  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ min J(x₀) = ½(x₀−xb)ᵀB⁻¹(x₀−xb)                    │
│        │   + ½ Σ (H(xₖ)−yₖ)ᵀR⁻¹(H(xₖ)−yₖ)                   │
│        │ s.t. xₖ₊₁ = M(xₖ) (model propagation)                │
│        │ Inverse: optimal initial condition from observations   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [L.state] ──→ [S.observation] ──→ [O.adjoint] │
│        │  derivative  linear-op  sample  optimize                │
│        │ V={∂.time, L.state, S.observation, O.adjoint}  A={∂.time→L.state, L.state→S.observation, S.observation→O.adjoint}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (cost bounded below)                    │
│        │ Uniqueness: CONDITIONAL (convexity near truth)         │
│        │ Stability: depends on observation density and B, R     │
│        │ Mismatch: model error, observation operator bias       │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = analysis RMSE (primary), forecast skill (secondary)│
│        │ q = problem-dependent (adjoint gradient accuracy)     │
│        │ T = {analysis_RMSE, forecast_RMSE, cost_reduction}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | State dimension, observation counts, window length consistent | PASS |
| S2 | B, R positive definite; cost function bounded below | PASS |
| S3 | Adjoint model + L-BFGS converges within iteration budget | PASS |
| S4 | Analysis RMSE < background RMSE (positive skill) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# control/4dvar_s1_ideal.yaml
principle_ref: sha256:<p435_hash>
omega:
  description: "Lorenz-96 model, n=40, 6-hour window, obs every grid point"
  states: 40
  window_steps: 50
  obs_density: 1.0
E:
  forward: "dx_i/dt = (x_{i+1}-x_{i-2})x_{i-1} - x_i + F"
  adjoint: "tangent-linear and adjoint of Lorenz-96"
I:
  dataset: Assim_10
  experiments: 10
  noise: {type: gaussian, obs_error: 1.0}
  scenario: ideal
O: [analysis_RMSE, forecast_RMSE_24h]
epsilon:
  analysis_RMSE_max: 0.30
  forecast_skill_min: 0.50
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 40 state variables, observation operator H consistent | PASS |
| S2 | B climatological, R=I; cost well-posed | PASS |
| S3 | L-BFGS converges in < 50 iterations | PASS |
| S4 | Analysis RMSE < 0.30 feasible with full obs | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# control/benchmark_4dvar_s1.yaml
spec_ref: sha256:<spec435_hash>
principle_ref: sha256:<p435_hash>
dataset:
  name: Assim_10
  experiments: 10
  data_hash: sha256:<dataset_435_hash>
baselines:
  - solver: 4D-Var (L-BFGS)
    params: {max_iter: 50}
    results: {analysis_RMSE: 0.15, forecast_RMSE: 0.45}
  - solver: 3D-Var
    params: {cycling: true}
    results: {analysis_RMSE: 0.25, forecast_RMSE: 0.65}
  - solver: EnKF
    params: {ensemble: 40}
    results: {analysis_RMSE: 0.18, forecast_RMSE: 0.50}
quality_scoring:
  - {max_RMSE: 0.10, Q: 1.00}
  - {max_RMSE: 0.15, Q: 0.90}
  - {max_RMSE: 0.25, Q: 0.80}
  - {max_RMSE: 0.35, Q: 0.75}
```

**Baseline solver:** 4D-Var — analysis RMSE 0.15
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Analysis RMSE | Forecast RMSE | Runtime | Q |
|--------|--------------|--------------|---------|---|
| 4D-Var (L-BFGS) | 0.15 | 0.45 | 30 s | 0.90 |
| 3D-Var (cycling) | 0.25 | 0.65 | 5 s | 0.80 |
| EnKF (N=40) | 0.18 | 0.50 | 10 s | 0.88 |
| Hybrid 4DEnVar | 0.12 | 0.40 | 45 s | 0.95 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (Hybrid): 500 × 0.95 = 475 PWM
Floor:              500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p435_hash>",
  "h_s": "sha256:<spec435_hash>",
  "h_b": "sha256:<bench435_hash>",
  "r": {"analysis_RMSE": 0.12, "error_bound": 0.30, "ratio": 0.40},
  "c": {"method": "Hybrid-4DEnVar", "iterations": 35, "K": 3},
  "Q": 0.95,
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
| L4 Solution | — | 375–475 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep data_assimilation_4dvar
pwm-node verify control/4dvar_s1_ideal.yaml
pwm-node mine control/4dvar_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
