# Principle #448 — Forward Dynamics (Lagrangian)

**Domain:** Robotics & Mechanical Systems | **Carrier:** mechanical | **Difficulty:** Standard (δ=3)
**DAG:** [N.bilinear] --> [∂.time] --> [L.dense] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.bilin-->∂.t-->L.dense  FwdDyn  DynBench-10  ABA/CRBA
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  FORWARD DYNAMICS           P = (E, G, W, C)   Principle #448  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ M(q)q̈ + C(q,q̇)q̇ + g(q) = τ                          │
│        │ q̈ = M(q)⁻¹[τ − C(q,q̇)q̇ − g(q)]                     │
│        │ M = mass matrix, C = Coriolis, g = gravity             │
│        │ Forward: given τ, compute q̈ (accelerations)           │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.bilin] ──→ [∂.t] ──→ [L.dense]                      │
│        │   Coriolis  integration  mass-matrix                    │
│        │ V={N.bilin,∂.t,L.dense}  A={N.bilin→∂.t,∂.t→L.dense}  L_DAG=2.0             │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (M(q) always invertible for rigid body) │
│        │ Uniqueness: YES (unique q̈ for given state and τ)      │
│        │ Stability: numerical stability of M⁻¹ depends on cond.│
│        │ Mismatch: friction, joint flexibility, payload errors  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = acceleration error ‖q̈−q̈_ref‖ (primary)            │
│        │ q = O(n) for ABA, O(n³) for CRBA                     │
│        │ T = {accel_error, energy_drift, integration_error}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | M(q) n×n symmetric positive definite; τ, q, q̇ dimensions match | PASS |
| S2 | M(q) SPD → always invertible; unique q̈ | PASS |
| S3 | ABA O(n) algorithm stable and efficient | PASS |
| S4 | Acceleration error < 1e-10 vs symbolic reference | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# robotics/fwd_dynamics_s1_ideal.yaml
principle_ref: sha256:<p448_hash>
omega:
  description: "6-DOF manipulator, gravity-loaded, no friction"
  joints: 6
  dt: 0.001
  simulation_time: 2.0
E:
  forward: "q_ddot = M(q)^{-1} [tau - C(q,qdot)*qdot - g(q)]"
  algorithm: "Articulated Body Algorithm (ABA)"
I:
  dataset: DynBench_10
  trajectories: 10
  torques: random_bounded
  scenario: ideal
O: [accel_error, energy_drift, trajectory_error]
epsilon:
  accel_err_max: 1e-8
  energy_drift_max: 1e-6
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 6-DOF dynamics matrices consistent; dt=1ms adequate | PASS |
| S2 | M(q) SPD verified for all configurations | PASS |
| S3 | ABA produces O(n) exact accelerations | PASS |
| S4 | Acceleration error < 1e-8 achievable | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# robotics/benchmark_fwddyn_s1.yaml
spec_ref: sha256:<spec448_hash>
principle_ref: sha256:<p448_hash>
dataset:
  name: DynBench_10
  trajectories: 10
  data_hash: sha256:<dataset_448_hash>
baselines:
  - solver: ABA
    params: {algorithm: articulated_body}
    results: {accel_err: 1e-12, energy_drift: 1e-10}
  - solver: CRBA
    params: {algorithm: composite_rigid_body}
    results: {accel_err: 1e-12, energy_drift: 1e-10}
  - solver: Direct-M-inv
    params: {method: LU}
    results: {accel_err: 1e-10, energy_drift: 1e-8}
quality_scoring:
  - {max_err: 1e-12, Q: 1.00}
  - {max_err: 1e-9, Q: 0.90}
  - {max_err: 1e-6, Q: 0.80}
  - {max_err: 1e-4, Q: 0.75}
```

**Baseline solver:** ABA — acceleration error 1e-12
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Accel Error | Energy Drift | Runtime | Q |
|--------|-----------|-------------|---------|---|
| ABA | 1e-12 | 1e-10 | 0.01 ms | 1.00 |
| CRBA + Cholesky | 1e-12 | 1e-10 | 0.02 ms | 1.00 |
| Direct LU | 1e-10 | 1e-8 | 0.05 ms | 0.90 |
| Neural Dynamics | 1e-4 | 1e-3 | 0.1 ms | 0.75 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (ABA):   300 × 1.00 = 300 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p448_hash>",
  "h_s": "sha256:<spec448_hash>",
  "h_b": "sha256:<bench448_hash>",
  "r": {"accel_error": 1e-12, "error_bound": 1e-8, "ratio": 1e-4},
  "c": {"method": "ABA", "complexity": "O(n)", "K": 3},
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
| L4 Solution | — | 225–300 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep forward_dynamics
pwm-node verify robotics/fwd_dynamics_s1_ideal.yaml
pwm-node mine robotics/fwd_dynamics_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
