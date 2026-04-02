# Principle #433 — Model Predictive Control (MPC)

**Domain:** Control Theory & Dynamical Systems | **Carrier:** signal | **Difficulty:** Research (δ=4)
**DAG:** L.state → ∂.time → N.pointwise → O.l2 |  **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.state→∂.time→N.pointwise→O.l2      MPC-ctrl    MPCBench-10       QP/ADMM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MODEL PREDICTIVE CONTROL   P = (E, G, W, C)   Principle #433  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ At each k: min Σ(xᵀQx + uᵀRu) over horizon N        │
│        │ s.t. x(j+1) = Ax(j) + Bu(j), constraints on u and x  │
│        │ Apply u*(0), shift horizon, re-solve                   │
│        │ Inverse: receding-horizon optimal control with constr. │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.state] ──→ [∂.time] ──→ [N.pointwise] ──→ [O.l2]    │
│        │  linear-op  derivative  nonlinear  optimize             │
│        │ V={L.state, ∂.time, N.pointwise, O.l2}  A={L.state→∂.time, ∂.time→N.pointwise, N.pointwise→O.l2}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (QP feasible with proper terminal set)  │
│        │ Uniqueness: YES (strictly convex QP)                   │
│        │ Stability: YES with terminal cost/constraint (Mayne)   │
│        │ Mismatch: model error, disturbances, computation delay │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = closed-loop cost (primary), constraint violation   │
│        │ q = near-optimal (horizon-dependent sub-optimality)   │
│        │ T = {cost, constraint_violations, solve_time}          │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Horizon N, state/input dims, constraint dimensions consistent | PASS |
| S2 | QP feasible with terminal constraint; Lyapunov stability proof | PASS |
| S3 | QP solver (OSQP/ADMM) converges within time budget | PASS |
| S4 | Closed-loop cost within 10% of infinite-horizon LQR | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# control/mpc_s1_ideal.yaml
principle_ref: sha256:<p433_hash>
omega:
  description: "Constrained double integrator, N=20 horizon"
  states: 4
  inputs: 2
  horizon: 20
  dt: 0.05
E:
  forward: "min Σ(xᵀQx + uᵀRu) s.t. dynamics + box constraints"
  solver: "QP (OSQP)"
I:
  dataset: MPCBench_10
  scenarios: 10
  constraints: {u_max: 1.0, x_max: 5.0}
  scenario: ideal
O: [closed_loop_cost, constraint_violations, solve_time_ms]
epsilon:
  cost_ratio_max: 1.10
  violations: 0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | QP dimensions (N×n states, N×m inputs) consistent | PASS |
| S2 | Terminal set computed; recursive feasibility guaranteed | PASS |
| S3 | OSQP solves within 5 ms per step | PASS |
| S4 | Cost ratio < 1.10 vs unconstrained LQR | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# control/benchmark_mpc_s1.yaml
spec_ref: sha256:<spec433_hash>
principle_ref: sha256:<p433_hash>
dataset:
  name: MPCBench_10
  scenarios: 10
  data_hash: sha256:<dataset_433_hash>
baselines:
  - solver: OSQP-MPC
    params: {horizon: 20}
    results: {cost_ratio: 1.03, violations: 0, solve_ms: 2.1}
  - solver: ADMM-MPC
    params: {horizon: 20}
    results: {cost_ratio: 1.04, violations: 0, solve_ms: 3.5}
  - solver: Explicit-MPC
    params: {regions: precomputed}
    results: {cost_ratio: 1.03, violations: 0, solve_ms: 0.1}
quality_scoring:
  - {max_cost_ratio: 1.01, Q: 1.00}
  - {max_cost_ratio: 1.03, Q: 0.90}
  - {max_cost_ratio: 1.08, Q: 0.80}
  - {max_cost_ratio: 1.12, Q: 0.75}
```

**Baseline solver:** OSQP-MPC — cost ratio 1.03
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Cost Ratio | Violations | Solve (ms) | Q |
|--------|-----------|-----------|-----------|---|
| OSQP-MPC | 1.03 | 0 | 2.1 | 0.90 |
| Explicit-MPC | 1.03 | 0 | 0.1 | 0.90 |
| ADMM-MPC | 1.04 | 0 | 3.5 | 0.88 |
| Neural-MPC | 1.02 | 0 | 0.5 | 0.95 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (Neural): 400 × 0.95 = 380 PWM
Floor:              400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p433_hash>",
  "h_s": "sha256:<spec433_hash>",
  "h_b": "sha256:<bench433_hash>",
  "r": {"cost_ratio": 1.02, "error_bound": 1.10, "ratio": 0.20},
  "c": {"method": "Neural-MPC", "violations": 0, "K": 3},
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
| L4 Solution | — | 300–380 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep model_predictive_control
pwm-node verify control/mpc_s1_ideal.yaml
pwm-node mine control/mpc_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
