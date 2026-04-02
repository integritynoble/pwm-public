# Principle #426 — Linear State-Space Model

**Domain:** Control Theory & Dynamical Systems | **Carrier:** signal | **Difficulty:** Textbook (δ=1)
**DAG:** L.state → ∂.time |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.state→∂.time        LTI-SS      StateSpace-10     Kalman/SID
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LINEAR STATE-SPACE MODEL   P = (E, G, W, C)   Principle #426   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ dx/dt = A x + B u ;  y = C x + D u + n                │
│        │ A ∈ R^{n×n}, B ∈ R^{n×m}, C ∈ R^{p×n}, D ∈ R^{p×m}  │
│        │ Inverse: estimate x(t) and/or (A,B,C,D) from (u,y)    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.state] ──→ [∂.time]                                 │
│        │  linear-op  derivative                                  │
│        │ V={L.state, ∂.time}  A={L.state→∂.time}  L_DAG=1.0     │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (matrix exponential for any A)          │
│        │ Uniqueness: YES when (A,C) observable                  │
│        │ Stability: κ depends on eigenvalues of A               │
│        │ Mismatch: model-order error, unmodeled nonlinearities  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative state error ‖x̂−x‖/‖x‖ (primary)         │
│        │ q = 2.0 (second-order for balanced truncation)        │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | State, input, output dimensions consistent across A,B,C,D | PASS |
| S2 | Observability rank condition → bounded state estimation | PASS |
| S3 | Matrix exponential convergent; Kalman filter stable for observable pairs | PASS |
| S4 | Relative state error achievable below 5% for SNR > 20 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# control/linear_ss_s1_ideal.yaml
principle_ref: sha256:<p426_hash>
omega:
  description: "LTI system, n=4 states, m=2 inputs, p=3 outputs"
  time_steps: 500
  dt: 0.01
E:
  forward: "dx/dt = A x + B u; y = C x + D u + n"
  system: "stable LTI, eigenvalues in left half-plane"
I:
  dataset: StateSpace_10
  trajectories: 10
  noise: {type: gaussian, SNR_dB: 30}
  scenario: ideal
O: [relative_state_error, output_fit_percent]
epsilon:
  state_err_max: 0.05
  output_fit_min: 90.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | System matrices consistent with n=4, m=2, p=3 | PASS |
| S2 | Observable pair (A,C); controllable pair (A,B) | PASS |
| S3 | Kalman filter converges for given noise level | PASS |
| S4 | State error < 5% feasible at SNR=30 dB | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# control/benchmark_linear_ss_s1.yaml
spec_ref: sha256:<spec426_hash>
principle_ref: sha256:<p426_hash>
dataset:
  name: StateSpace_10
  trajectories: 10
  time_steps: 500
  data_hash: sha256:<dataset_426_hash>
baselines:
  - solver: Kalman-Filter
    params: {known_model: true}
    results: {state_err: 0.012, output_fit: 98.5}
  - solver: Subspace-ID (N4SID)
    params: {order: 4}
    results: {state_err: 0.035, output_fit: 94.2}
  - solver: ERA
    params: {order: 4}
    results: {state_err: 0.040, output_fit: 93.1}
quality_scoring:
  - {max_err: 0.01, Q: 1.00}
  - {max_err: 0.03, Q: 0.90}
  - {max_err: 0.05, Q: 0.80}
  - {max_err: 0.08, Q: 0.75}
```

**Baseline solver:** Kalman-Filter — state error 0.012
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | State Error | Output Fit % | Runtime | Q |
|--------|-------------|-------------|---------|---|
| Kalman Filter | 0.012 | 98.5 | 0.1 s | 0.95 |
| N4SID | 0.035 | 94.2 | 0.5 s | 0.85 |
| ERA | 0.040 | 93.1 | 0.3 s | 0.82 |
| LSTM-SSM | 0.018 | 97.0 | 2.0 s | 0.92 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (Kalman):  100 × 0.95 = 95 PWM
Floor:               100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p426_hash>",
  "h_s": "sha256:<spec426_hash>",
  "h_b": "sha256:<bench426_hash>",
  "r": {"residual_norm": 0.012, "error_bound": 0.05, "ratio": 0.24},
  "c": {"fitted_rate": 1.98, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 75–95 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep linear_state_space
pwm-node verify control/linear_ss_s1_ideal.yaml
pwm-node mine control/linear_ss_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
