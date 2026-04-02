# Principle #452 — Multibody System Dynamics

**Domain:** Robotics & Mechanical Systems | **Carrier:** mechanical | **Difficulty:** Research (δ=4)
**DAG:** [N.bilinear] --> [∂.time] --> [L.dense] --> [B.contact] | **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.bilin-->∂.t-->L.dense-->B.cont  MBD-sim  MBDBench-10  DAE/Baumg.
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MULTIBODY SYSTEM DYNAMICS  P = (E, G, W, C)   Principle #452  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ M(q)q̈ + Φ_qᵀ λ = Q(q,q̇,t)                           │
│        │ Φ(q,t) = 0  (holonomic constraints)                   │
│        │ Index-3 DAE → stabilized with Baumgarte or index red. │
│        │ Inverse: simulate coupled rigid/flexible body systems  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.bilin] ──→ [∂.t] ──→ [L.dense] ──→ [B.cont]         │
│        │   Coriolis  integration  mass-matrix  contact           │
│        │ V={N.bilin,∂.t,L.dense,B.cont}  A={N.bilin→∂.t,∂.t→L.dense,L.dense→B.cont}  L_DAG=3.0             │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (DAE solvable for consistent IC)        │
│        │ Uniqueness: YES (constraints + dynamics determine q̈,λ)│
│        │ Stability: index-3 DAE needs stabilization             │
│        │ Mismatch: contact models, joint clearance, flexibility │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = constraint drift (primary), energy error (second.) │
│        │ q = 2nd-order (BDF-2 or Newmark)                      │
│        │ T = {constraint_drift, energy_error, penetration}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Constraint Jacobian Φ_q full rank; mass matrix SPD | PASS |
| S2 | Index reduction or Baumgarte stabilization applied | PASS |
| S3 | BDF-2 / HHT-α integrator converges with Newton | PASS |
| S4 | Constraint drift < 1e-6 maintained over simulation | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# robotics/multibody_s1_ideal.yaml
principle_ref: sha256:<p452_hash>
omega:
  description: "Double pendulum with revolute joints, T=5 s"
  bodies: 3
  constraints: 4
  dt: 0.001
E:
  forward: "M*q_ddot + Phi_q'*lambda = Q; Phi(q)=0"
  stabilization: "Baumgarte (alpha=beta=5)"
I:
  dataset: MBDBench_10
  scenarios: 10
  scenario: ideal
O: [constraint_drift, energy_error, trajectory_error]
epsilon:
  constraint_drift_max: 1e-6
  energy_err_max: 1e-4
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 3 bodies, 4 constraints, DOF = 2 consistent | PASS |
| S2 | Baumgarte parameters tuned for stability | PASS |
| S3 | Newmark integrator converges at each step | PASS |
| S4 | Constraint drift < 1e-6 achievable | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# robotics/benchmark_mbd_s1.yaml
spec_ref: sha256:<spec452_hash>
principle_ref: sha256:<p452_hash>
dataset:
  name: MBDBench_10
  scenarios: 10
  data_hash: sha256:<dataset_452_hash>
baselines:
  - solver: Baumgarte-BDF2
    params: {alpha: 5, beta: 5}
    results: {drift: 1e-7, energy_err: 1e-5}
  - solver: Index-1-DAE
    params: {reduction: GGL}
    results: {drift: 1e-10, energy_err: 1e-6}
  - solver: Penalty-Method
    params: {stiffness: 1e6}
    results: {drift: 1e-4, energy_err: 1e-3}
quality_scoring:
  - {max_drift: 1e-9, Q: 1.00}
  - {max_drift: 1e-7, Q: 0.90}
  - {max_drift: 1e-5, Q: 0.80}
  - {max_drift: 1e-3, Q: 0.75}
```

**Baseline solver:** Baumgarte-BDF2 — drift 1e-7
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Drift | Energy Error | Runtime | Q |
|--------|-------|-------------|---------|---|
| Baumgarte-BDF2 | 1e-7 | 1e-5 | 0.5 s | 0.92 |
| Index-1 GGL | 1e-10 | 1e-6 | 1.0 s | 1.00 |
| Penalty | 1e-4 | 1e-3 | 0.3 s | 0.78 |
| Variational Integrator | 1e-9 | 1e-8 | 0.8 s | 0.98 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (GGL):   400 × 1.00 = 400 PWM
Floor:             400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p452_hash>",
  "h_s": "sha256:<spec452_hash>",
  "h_b": "sha256:<bench452_hash>",
  "r": {"drift": 1e-10, "error_bound": 1e-6, "ratio": 1e-4},
  "c": {"method": "Index-1-GGL", "order": 2, "K": 3},
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
| L4 Solution | — | 300–400 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep multibody
pwm-node verify robotics/multibody_s1_ideal.yaml
pwm-node mine robotics/multibody_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
