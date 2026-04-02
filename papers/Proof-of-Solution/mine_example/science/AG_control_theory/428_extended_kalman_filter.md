# Principle #428 — Extended Kalman Filter (EKF)

**Domain:** Control Theory & Dynamical Systems | **Carrier:** signal | **Difficulty:** Standard (δ=2)
**DAG:** L.state → ∂.time → S.observation → L.gain |  **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.state→∂.time→S.observation→L.gain      EKF-est     NonlinTrack-10    EKF/IEKF
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  EXTENDED KALMAN FILTER     P = (E, G, W, C)   Principle #428   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ x(k+1) = f(x(k), u(k)) + w;  y(k) = h(x(k)) + v     │
│        │ Linearize: F = ∂f/∂x|x̂, H = ∂h/∂x|x̂                 │
│        │ Apply Kalman predict-update with F, H at each step     │
│        │ Inverse: estimate nonlinear state from noisy y         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.state] ──→ [∂.time] ──→ [S.observation] ──→ [L.gain] │
│        │  linear-op  derivative  sample  linear-op               │
│        │ V={L.state, ∂.time, S.observation, L.gain}  A={L.state→∂.time, ∂.time→S.observation, S.observation→L.gain}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (recursion well-defined for smooth f,h) │
│        │ Uniqueness: APPROX (local linearization, not global)   │
│        │ Stability: CONDITIONAL on mild nonlinearity and SNR    │
│        │ Mismatch: Jacobian errors, unmodeled dynamics          │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSE of state estimate (primary), NEES (secondary) │
│        │ q = 1.5 (sub-optimal due to linearization)            │
│        │ T = {residual_norm, innovation_whiteness, NEES}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Jacobians F, H dimensions consistent with state/obs dims | PASS |
| S2 | Linearized system observable at nominal trajectory | PASS |
| S3 | EKF converges for mildly nonlinear systems with sufficient SNR | PASS |
| S4 | RMSE below 10% of state magnitude achievable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# control/ekf_s1_ideal.yaml
principle_ref: sha256:<p428_hash>
omega:
  description: "Nonlinear tracking (e.g., range-bearing), n=4, p=2"
  time_steps: 500
  dt: 0.01
E:
  forward: "x(k+1) = f(x,u) + w; y = h(x) + v"
  nonlinearity: "quadratic (range-bearing observation)"
I:
  dataset: NonlinTrack_10
  trajectories: 10
  noise: {type: gaussian, Q_scale: 0.01, R_scale: 0.1}
  scenario: ideal
O: [RMSE, NEES]
epsilon:
  RMSE_max: 0.08
  NEES_range: [0.7, 1.4]
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | State/observation dimensions match nonlinear model | PASS |
| S2 | Local observability verified along nominal trajectory | PASS |
| S3 | EKF converges within 30 steps for this noise level | PASS |
| S4 | RMSE < 0.08 feasible for given nonlinearity | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# control/benchmark_ekf_s1.yaml
spec_ref: sha256:<spec428_hash>
principle_ref: sha256:<p428_hash>
dataset:
  name: NonlinTrack_10
  trajectories: 10
  time_steps: 500
  data_hash: sha256:<dataset_428_hash>
baselines:
  - solver: EKF
    params: {linearization: first_order}
    results: {RMSE: 0.042, NEES: 1.15}
  - solver: IEKF
    params: {iterations: 5}
    results: {RMSE: 0.030, NEES: 1.05}
  - solver: Particle-Filter
    params: {N_particles: 1000}
    results: {RMSE: 0.025, NEES: 1.02}
quality_scoring:
  - {max_RMSE: 0.020, Q: 1.00}
  - {max_RMSE: 0.035, Q: 0.90}
  - {max_RMSE: 0.060, Q: 0.80}
  - {max_RMSE: 0.080, Q: 0.75}
```

**Baseline solver:** EKF — RMSE 0.042
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | RMSE | NEES | Runtime | Q |
|--------|------|------|---------|---|
| EKF | 0.042 | 1.15 | 0.08 s | 0.85 |
| IEKF | 0.030 | 1.05 | 0.15 s | 0.92 |
| Particle Filter | 0.025 | 1.02 | 1.5 s | 0.95 |
| UKF | 0.028 | 1.04 | 0.12 s | 0.93 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (PF):    200 × 0.95 = 190 PWM
Floor:             200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p428_hash>",
  "h_s": "sha256:<spec428_hash>",
  "h_b": "sha256:<bench428_hash>",
  "r": {"residual_norm": 0.025, "error_bound": 0.08, "ratio": 0.31},
  "c": {"fitted_rate": 1.45, "theoretical_rate": 1.5, "K": 3},
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
| L4 Solution | — | 150–190 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep extended_kalman
pwm-node verify control/ekf_s1_ideal.yaml
pwm-node mine control/ekf_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
