# Principle #429 — Unscented Kalman Filter (UKF)

**Domain:** Control Theory & Dynamical Systems | **Carrier:** signal | **Difficulty:** Standard (δ=2)
**DAG:** L.state → S.random → S.observation → L.gain |  **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.state→S.random→S.observation→L.gain      UKF-est     SigmaTrack-10     UKF/CKF
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  UNSCENTED KALMAN FILTER    P = (E, G, W, C)   Principle #429   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ x(k+1) = f(x(k), u(k)) + w;  y(k) = h(x(k)) + v     │
│        │ Sigma points: χ_i = x̂ ± √((n+λ)P), propagate through │
│        │ f and h to capture mean and covariance to 2nd order    │
│        │ Inverse: estimate nonlinear state without Jacobians    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.state] ──→ [S.random] ──→ [S.observation] ──→ [L.gain] │
│        │  linear-op  sample  sample  linear-op                   │
│        │ V={L.state, S.random, S.observation, L.gain}  A={L.state→S.random, S.random→S.observation, S.observation→L.gain}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (deterministic sampling always defined) │
│        │ Uniqueness: YES (mean/cov unique for given sigma pts)  │
│        │ Stability: CONDITIONAL on positive-definite covariance │
│        │ Mismatch: kurtosis mismatch, non-Gaussian tails        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSE of state estimate (primary), NEES (secondary) │
│        │ q = 2.0 (second-order accuracy in mean)               │
│        │ T = {residual_norm, innovation_whiteness, NEES}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | 2n+1 sigma points consistent with state dimension n | PASS |
| S2 | Covariance remains positive definite through recursion | PASS |
| S3 | UKF converges for moderate nonlinearities without Jacobians | PASS |
| S4 | RMSE comparable to or better than EKF for same problem | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# control/ukf_s1_ideal.yaml
principle_ref: sha256:<p429_hash>
omega:
  description: "Nonlinear tracking, n=6, range-bearing-elevation"
  time_steps: 500
  dt: 0.01
E:
  forward: "x(k+1) = f(x,u) + w; y = h(x) + v"
  sigma_params: {alpha: 1e-3, beta: 2, kappa: 0}
I:
  dataset: SigmaTrack_10
  trajectories: 10
  noise: {type: gaussian, Q_scale: 0.01, R_scale: 0.1}
  scenario: ideal
O: [RMSE, NEES]
epsilon:
  RMSE_max: 0.06
  NEES_range: [0.7, 1.3]
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 13 sigma points for n=6; weights sum to 1 | PASS |
| S2 | Covariance positive definite at specified noise levels | PASS |
| S3 | UKF converges within 25 steps | PASS |
| S4 | RMSE < 0.06 feasible at given SNR | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# control/benchmark_ukf_s1.yaml
spec_ref: sha256:<spec429_hash>
principle_ref: sha256:<p429_hash>
dataset:
  name: SigmaTrack_10
  trajectories: 10
  time_steps: 500
  data_hash: sha256:<dataset_429_hash>
baselines:
  - solver: UKF
    params: {alpha: 1e-3, beta: 2}
    results: {RMSE: 0.028, NEES: 1.05}
  - solver: CKF
    params: {cubature: true}
    results: {RMSE: 0.026, NEES: 1.03}
  - solver: EKF
    params: {linearization: first_order}
    results: {RMSE: 0.045, NEES: 1.20}
quality_scoring:
  - {max_RMSE: 0.018, Q: 1.00}
  - {max_RMSE: 0.030, Q: 0.90}
  - {max_RMSE: 0.050, Q: 0.80}
  - {max_RMSE: 0.070, Q: 0.75}
```

**Baseline solver:** UKF — RMSE 0.028
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | RMSE | NEES | Runtime | Q |
|--------|------|------|---------|---|
| UKF | 0.028 | 1.05 | 0.10 s | 0.92 |
| CKF | 0.026 | 1.03 | 0.10 s | 0.93 |
| EKF | 0.045 | 1.20 | 0.06 s | 0.82 |
| Gauss-Hermite KF | 0.022 | 1.01 | 0.30 s | 0.96 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (GHKF):  200 × 0.96 = 192 PWM
Floor:             200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p429_hash>",
  "h_s": "sha256:<spec429_hash>",
  "h_b": "sha256:<bench429_hash>",
  "r": {"residual_norm": 0.022, "error_bound": 0.06, "ratio": 0.37},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.96,
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
| L4 Solution | — | 150–192 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep unscented_kalman
pwm-node verify control/ukf_s1_ideal.yaml
pwm-node mine control/ukf_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
