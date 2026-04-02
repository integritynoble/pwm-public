# Principle #427 — Kalman Filter (State Estimation)

**Domain:** Control Theory & Dynamical Systems | **Carrier:** signal | **Difficulty:** Textbook (δ=1)
**DAG:** L.state → ∂.time → S.observation → L.gain |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.state→∂.time→S.observation→L.gain        KF-est      KalmanTrack-10    KF/RTS
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  KALMAN FILTER              P = (E, G, W, C)   Principle #427   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Predict:  x̂⁻ = A x̂⁺ + B u;  P⁻ = A P⁺ Aᵀ + Q      │
│        │ Update:   K = P⁻ Cᵀ(C P⁻ Cᵀ + R)⁻¹                  │
│        │           x̂⁺ = x̂⁻ + K(y − C x̂⁻);  P⁺ = (I−KC) P⁻  │
│        │ Inverse: recover state trajectory from noisy y         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.state] ──→ [∂.time] ──→ [S.observation] ──→ [L.gain] │
│        │  linear-op  derivative  sample  linear-op               │
│        │ V={L.state, ∂.time, S.observation, L.gain}  A={L.state→∂.time, ∂.time→S.observation, S.observation→L.gain}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (closed-form recursion)                 │
│        │ Uniqueness: YES (BLUE for linear Gaussian)             │
│        │ Stability: YES when (A,C) detectable and (A,Q^½) stab.│
│        │ Mismatch: wrong Q, R, or model order                   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSE of state estimate (primary), NCI (secondary)  │
│        │ q = optimal (Cramér-Rao bound achieved)               │
│        │ T = {residual_norm, innovation_whiteness, NEES}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Dimensions of A, B, C, Q, R consistent; covariance matrices SPD | PASS |
| S2 | (A,C) detectable → bounded error covariance | PASS |
| S3 | Riccati recursion converges to steady-state P | PASS |
| S4 | RMSE at Cramér-Rao bound for Gaussian noise | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# control/kalman_filter_s1_ideal.yaml
principle_ref: sha256:<p427_hash>
omega:
  description: "4-state tracking system, dt=0.01, T=500 steps"
  states: 4
  observations: 2
E:
  forward: "x(k+1) = A x(k) + B u(k) + w; y(k) = C x(k) + v"
  noise: {Q: diag(0.01), R: diag(0.1)}
I:
  dataset: KalmanTrack_10
  trajectories: 10
  noise: {type: gaussian, Q_scale: 1.0, R_scale: 1.0}
  scenario: ideal
O: [RMSE, NEES, innovation_whiteness]
epsilon:
  RMSE_max: 0.05
  NEES_range: [0.8, 1.2]
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | State/observation dimensions match; Q, R positive definite | PASS |
| S2 | (A,C) observable; Riccati converges | PASS |
| S3 | KF recursion converges within 20 steps | PASS |
| S4 | RMSE < 0.05 feasible at specified noise levels | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# control/benchmark_kalman_s1.yaml
spec_ref: sha256:<spec427_hash>
principle_ref: sha256:<p427_hash>
dataset:
  name: KalmanTrack_10
  trajectories: 10
  time_steps: 500
  data_hash: sha256:<dataset_427_hash>
baselines:
  - solver: Kalman-Filter
    params: {known_model: true}
    results: {RMSE: 0.018, NEES: 1.02}
  - solver: RTS-Smoother
    params: {known_model: true}
    results: {RMSE: 0.012, NEES: 0.98}
  - solver: Moving-Average
    params: {window: 10}
    results: {RMSE: 0.065, NEES: 2.10}
quality_scoring:
  - {max_RMSE: 0.010, Q: 1.00}
  - {max_RMSE: 0.020, Q: 0.90}
  - {max_RMSE: 0.040, Q: 0.80}
  - {max_RMSE: 0.060, Q: 0.75}
```

**Baseline solver:** Kalman-Filter — RMSE 0.018
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | RMSE | NEES | Runtime | Q |
|--------|------|------|---------|---|
| Kalman Filter | 0.018 | 1.02 | 0.05 s | 0.92 |
| RTS Smoother | 0.012 | 0.98 | 0.08 s | 0.97 |
| Moving Average | 0.065 | 2.10 | 0.01 s | 0.72 |
| Neural KF | 0.015 | 1.05 | 0.20 s | 0.94 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (RTS):   100 × 0.97 = 97 PWM
Floor:             100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p427_hash>",
  "h_s": "sha256:<spec427_hash>",
  "h_b": "sha256:<bench427_hash>",
  "r": {"residual_norm": 0.012, "error_bound": 0.05, "ratio": 0.24},
  "c": {"fitted_rate": "optimal", "theoretical_rate": "CRB", "K": 3},
  "Q": 0.97,
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
| L4 Solution | — | 75–97 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep kalman_filter
pwm-node verify control/kalman_filter_s1_ideal.yaml
pwm-node mine control/kalman_filter_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
