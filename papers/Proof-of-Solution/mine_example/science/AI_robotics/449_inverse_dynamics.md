# Principle #449 — Inverse Dynamics (Newton-Euler)

**Domain:** Robotics & Mechanical Systems | **Carrier:** mechanical | **Difficulty:** Standard (δ=2)
**DAG:** [N.bilinear] --> [L.dense] | **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.bilin-->L.dense  InvDyn  IDynBench-10  RNEA
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  INVERSE DYNAMICS (N-E)     P = (E, G, W, C)   Principle #449  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ τ = M(q)q̈ + C(q,q̇)q̇ + g(q)                          │
│        │ RNEA: outward pass (velocities, accels) → inward pass │
│        │ (forces, torques) in O(n) time                         │
│        │ Inverse: given desired (q,q̇,q̈), compute required τ   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.bilin] ──→ [L.dense]                                │
│        │   Coriolis  mass-matrix                                 │
│        │ V={N.bilin,L.dense}  A={N.bilin→L.dense}  L_DAG=1.0                       │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (direct evaluation, no inversion)       │
│        │ Uniqueness: YES (τ uniquely determined by q,q̇,q̈)     │
│        │ Stability: numerically stable (no matrix inversion)    │
│        │ Mismatch: inertial parameter errors, friction models   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = torque error ‖τ̂−τ_ref‖ (primary)                  │
│        │ q = exact (O(n) recursive algorithm)                  │
│        │ T = {torque_error, tracking_error}                     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Inertial parameters, link masses, CoM positions consistent | PASS |
| S2 | RNEA well-defined for any kinematic tree | PASS |
| S3 | O(n) recursion; no iterative convergence needed | PASS |
| S4 | Torque error = 0 for exact inertial parameters | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# robotics/inv_dynamics_s1_ideal.yaml
principle_ref: sha256:<p449_hash>
omega:
  description: "6-DOF manipulator, prescribed trajectory"
  joints: 6
  trajectory_points: 1000
E:
  forward: "tau = M(q)*q_ddot + C(q,qdot)*qdot + g(q)"
  algorithm: "RNEA"
I:
  dataset: IDynBench_10
  trajectories: 10
  scenario: ideal
O: [torque_error, tracking_error_mm]
epsilon:
  torque_err_max: 1e-8
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 6 joints, full inertial parameter set provided | PASS |
| S2 | RNEA applies to serial chain | PASS |
| S3 | Exact computation in O(n) per time step | PASS |
| S4 | Torque error < 1e-8 (machine precision) | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# robotics/benchmark_idyn_s1.yaml
spec_ref: sha256:<spec449_hash>
principle_ref: sha256:<p449_hash>
dataset:
  name: IDynBench_10
  trajectories: 10
  data_hash: sha256:<dataset_449_hash>
baselines:
  - solver: RNEA
    params: {}
    results: {torque_err: 1e-14}
  - solver: Lagrangian-Symbolic
    params: {}
    results: {torque_err: 1e-14}
  - solver: Regressor-LS
    params: {estimated_params: true}
    results: {torque_err: 0.5}
quality_scoring:
  - {max_err: 1e-10, Q: 1.00}
  - {max_err: 1e-6, Q: 0.90}
  - {max_err: 0.01, Q: 0.80}
  - {max_err: 1.0, Q: 0.75}
```

**Baseline solver:** RNEA — torque error 1e-14
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Torque Error | Runtime | Q |
|--------|-------------|---------|---|
| RNEA | 1e-14 | 0.005 ms | 1.00 |
| Lagrangian Symbolic | 1e-14 | 0.05 ms | 1.00 |
| Regressor LS | 0.50 | 0.01 ms | 0.75 |
| Neural ID | 0.10 | 0.1 ms | 0.80 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (RNEA):  200 × 1.00 = 200 PWM
Floor:             200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p449_hash>",
  "h_s": "sha256:<spec449_hash>",
  "h_b": "sha256:<bench449_hash>",
  "r": {"torque_error": 1e-14, "error_bound": 1e-8, "ratio": 1e-6},
  "c": {"method": "RNEA", "complexity": "O(n)", "K": 3},
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
pwm-node benchmarks | grep inverse_dynamics
pwm-node verify robotics/inv_dynamics_s1_ideal.yaml
pwm-node mine robotics/inv_dynamics_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
