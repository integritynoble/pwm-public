# Principle #451 — Rigid Body Dynamics

**Domain:** Robotics & Mechanical Systems | **Carrier:** mechanical | **Difficulty:** Standard (δ=2)
**DAG:** [N.bilinear.quaternion] --> [∂.time] --> [N.bilinear] | **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.bilin.quat-->∂.t-->N.bilin  RBD-sim  RBDBench-10  Euler/Verlet
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  RIGID BODY DYNAMICS        P = (E, G, W, C)   Principle #451  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ F = m a;  τ = I ω̇ + ω × (I ω)  (Newton-Euler)       │
│        │ Quaternion kinematics: q̇ = ½ ω ⊗ q                   │
│        │ Coupled translation + rotation in SE(3)                │
│        │ Forward: given forces/torques, integrate trajectory    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.bilin.quat] ──→ [∂.t] ──→ [N.bilin]                 │
│        │   quaternion  integration  gyroscopic                   │
│        │ V={N.bilin.quat,∂.t,N.bilin}  A={N.bilin.quat→∂.t,∂.t→N.bilin}  L_DAG=2.0                     │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (ODE with Lipschitz RHS)                │
│        │ Uniqueness: YES (Picard-Lindelof)                      │
│        │ Stability: symplectic integrators conserve energy       │
│        │ Mismatch: deformation, contact mechanics               │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = trajectory error (primary), energy drift (second.) │
│        │ q = 2-4 (depending on integrator order)               │
│        │ T = {trajectory_error, energy_drift, quaternion_norm}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Mass, inertia tensor SPD, force/torque dimensions match | PASS |
| S2 | ODE Lipschitz continuous → unique solution | PASS |
| S3 | RK4 / symplectic Euler converges at known order | PASS |
| S4 | Trajectory error and energy drift computable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# robotics/rigid_body_s1_ideal.yaml
principle_ref: sha256:<p451_hash>
omega:
  description: "Tumbling rigid body, torque-free, T=10 s"
  states: 13  # (pos3, quat4, vel3, omega3)
  dt: 0.001
E:
  forward: "Newton-Euler + quaternion kinematics"
  integrator: "symplectic Euler or RK4"
I:
  dataset: RBDBench_10
  scenarios: 10
  scenario: ideal
O: [trajectory_error, energy_drift, quat_norm_drift]
epsilon:
  energy_drift_max: 1e-6
  quat_norm_max: 1e-8
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 13-state vector consistent; inertia tensor SPD | PASS |
| S2 | Torque-free Euler equations have known analytic solution | PASS |
| S3 | RK4 at dt=1ms gives O(h⁴) convergence | PASS |
| S4 | Energy drift < 1e-6 over 10 s | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# robotics/benchmark_rbd_s1.yaml
spec_ref: sha256:<spec451_hash>
principle_ref: sha256:<p451_hash>
dataset:
  name: RBDBench_10
  scenarios: 10
  data_hash: sha256:<dataset_451_hash>
baselines:
  - solver: RK4
    params: {dt: 0.001}
    results: {energy_drift: 5e-8, traj_err: 1e-6}
  - solver: Symplectic-Euler
    params: {dt: 0.001}
    results: {energy_drift: 1e-10, traj_err: 5e-4}
  - solver: Verlet
    params: {dt: 0.001}
    results: {energy_drift: 1e-10, traj_err: 1e-5}
quality_scoring:
  - {max_energy_drift: 1e-10, Q: 1.00}
  - {max_energy_drift: 1e-7, Q: 0.90}
  - {max_energy_drift: 1e-5, Q: 0.80}
  - {max_energy_drift: 1e-3, Q: 0.75}
```

**Baseline solver:** RK4 — energy drift 5e-8
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Energy Drift | Traj Error | Runtime | Q |
|--------|-------------|-----------|---------|---|
| RK4 | 5e-8 | 1e-6 | 0.1 s | 0.92 |
| Symplectic Euler | 1e-10 | 5e-4 | 0.05 s | 1.00 |
| Stormer-Verlet | 1e-10 | 1e-5 | 0.08 s | 1.00 |
| Forward Euler | 1e-2 | 1e-1 | 0.03 s | 0.72 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (Sympl.): 200 × 1.00 = 200 PWM
Floor:              200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p451_hash>",
  "h_s": "sha256:<spec451_hash>",
  "h_b": "sha256:<bench451_hash>",
  "r": {"energy_drift": 1e-10, "error_bound": 1e-6, "ratio": 1e-4},
  "c": {"method": "Symplectic-Euler", "dt": 0.001, "K": 3},
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
pwm-node benchmarks | grep rigid_body_dynamics
pwm-node verify robotics/rigid_body_s1_ideal.yaml
pwm-node mine robotics/rigid_body_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
