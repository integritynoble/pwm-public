# Principle #432 — Optimal Control (LQR)

**Domain:** Control Theory & Dynamical Systems | **Carrier:** signal | **Difficulty:** Standard (δ=2)
**DAG:** L.state → E.hermitian → L.gain |  **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.state→E.hermitian→L.gain        LQR-ctrl    LQRBench-10       Riccati/DP
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  OPTIMAL CONTROL (LQR)      P = (E, G, W, C)   Principle #432  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ min J = ∫(xᵀQx + uᵀRu)dt  s.t. dx/dt = Ax + Bu      │
│        │ Solution: u* = −K x,  K = R⁻¹BᵀP                     │
│        │ P from algebraic Riccati: AᵀP + PA − PBR⁻¹BᵀP + Q = 0│
│        │ Inverse: find K given desired closed-loop performance  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.state] ──→ [E.hermitian] ──→ [L.gain]               │
│        │  linear-op  eigensolve  linear-op                       │
│        │ V={L.state, E.hermitian, L.gain}  A={L.state→E.hermitian, E.hermitian→L.gain}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES when (A,B) stabilizable, (A,Q^½) detect.│
│        │ Uniqueness: YES (unique stabilizing solution of ARE)   │
│        │ Stability: guaranteed closed-loop stability            │
│        │ Mismatch: model uncertainty, actuator saturation       │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = quadratic cost J (primary), settling time (second.)│
│        │ q = optimal (global minimum of J for linear-quadratic)│
│        │ T = {cost_J, settling_time, gain_margin}               │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Q ≥ 0, R > 0 dimensions match state/input dims | PASS |
| S2 | (A,B) stabilizable and (A,Q^½) detectable → ARE solvable | PASS |
| S3 | ARE solver (Schur decomposition) converges | PASS |
| S4 | Closed-loop cost J finite and computable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# control/lqr_s1_ideal.yaml
principle_ref: sha256:<p432_hash>
omega:
  description: "Double integrator, n=4 states, m=2 inputs"
  horizon: continuous
E:
  forward: "dx/dt = Ax + Bu; J = integral(xᵀQx + uᵀRu)"
  method: "algebraic Riccati equation"
I:
  dataset: LQRBench_10
  scenarios: 10
  plants: {type: LTI, varied_params: true}
  scenario: ideal
O: [cost_J, settling_time, gain_margin_dB]
epsilon:
  cost_ratio_max: 1.05
  settling_time_max: 2.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Q, R dimensions match n=4, m=2; Q≥0, R>0 | PASS |
| S2 | All 10 plants stabilizable and detectable | PASS |
| S3 | ARE Schur solver converges for all plants | PASS |
| S4 | Cost within 5% of optimum achievable | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# control/benchmark_lqr_s1.yaml
spec_ref: sha256:<spec432_hash>
principle_ref: sha256:<p432_hash>
dataset:
  name: LQRBench_10
  scenarios: 10
  data_hash: sha256:<dataset_432_hash>
baselines:
  - solver: ARE-Schur
    params: {}
    results: {cost_ratio: 1.000, settling: 0.8}
  - solver: LQR-DP
    params: {dt: 0.001}
    results: {cost_ratio: 1.002, settling: 0.82}
  - solver: Pole-Placement
    params: {poles: [-2, -3, -4, -5]}
    results: {cost_ratio: 1.15, settling: 1.1}
quality_scoring:
  - {max_cost_ratio: 1.001, Q: 1.00}
  - {max_cost_ratio: 1.01, Q: 0.90}
  - {max_cost_ratio: 1.05, Q: 0.80}
  - {max_cost_ratio: 1.10, Q: 0.75}
```

**Baseline solver:** ARE-Schur — cost ratio 1.000
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Cost Ratio | Settling (s) | Runtime | Q |
|--------|-----------|-------------|---------|---|
| ARE-Schur | 1.000 | 0.80 | 0.01 s | 1.00 |
| LQR-DP | 1.002 | 0.82 | 0.10 s | 0.98 |
| Pole Placement | 1.150 | 1.10 | 0.01 s | 0.72 |
| RL-Policy | 1.008 | 0.85 | 5.0 s | 0.95 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (ARE):   200 × 1.00 = 200 PWM
Floor:             200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p432_hash>",
  "h_s": "sha256:<spec432_hash>",
  "h_b": "sha256:<bench432_hash>",
  "r": {"cost_ratio": 1.000, "error_bound": 1.05, "ratio": 0.00},
  "c": {"method": "ARE-Schur", "optimal": true, "K": 3},
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
| L4 Solution | — | 150–200 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep optimal_control_lqr
pwm-node verify control/lqr_s1_ideal.yaml
pwm-node mine control/lqr_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
