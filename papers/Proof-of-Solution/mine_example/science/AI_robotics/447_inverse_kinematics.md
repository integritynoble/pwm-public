# Principle #447 — Inverse Kinematics

**Domain:** Robotics & Mechanical Systems | **Carrier:** mechanical | **Difficulty:** Standard (δ=3)
**DAG:** [N.trigonometric] --> [L.homogeneous] --> [O.l2] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.trig-->L.homo-->O.l2  IK-solve  IKBench-10  Newton/CCD
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  INVERSE KINEMATICS         P = (E, G, W, C)   Principle #447  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Find θ s.t. FK(θ) = T_desired (target pose)           │
│        │ Jacobian: J(θ) = ∂FK/∂θ;  Δθ = J⁺ Δx                 │
│        │ Multiple solutions possible (redundancy/elbow up-down) │
│        │ Inverse: map desired end-effector pose → joint angles  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.trig] ──→ [L.homo] ──→ [O.l2]                       │
│        │   joint-angles  SE(3)-chain  residual                   │
│        │ V={N.trig,L.homo,O.l2}  A={N.trig→L.homo,L.homo→O.l2}  L_DAG=2.0             │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: within workspace (reachability check)       │
│        │ Uniqueness: NO (multiple IK solutions generically)     │
│        │ Stability: ill-conditioned near kinematic singularities│
│        │ Mismatch: joint limits, self-collision constraints     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = pose error ‖FK(θ̂)−T_des‖ (primary), joint dist.  │
│        │ q = quadratic (Newton-Raphson on Jacobian)            │
│        │ T = {pose_error, iterations, singularity_measure}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Target pose within manipulator workspace | PASS |
| S2 | Jacobian full rank at initial guess (non-singular) | PASS |
| S3 | Damped least-squares / Newton converges in < 50 iterations | PASS |
| S4 | Pose error < 0.1 mm achievable for reachable targets | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# robotics/ik_s1_ideal.yaml
principle_ref: sha256:<p447_hash>
omega:
  description: "6-DOF manipulator, 10 target poses within workspace"
  joints: 6
  targets: 10
E:
  forward: "FK(theta) = T_desired"
  method: "Damped least-squares Jacobian"
I:
  dataset: IKBench_10
  poses: 10
  joint_limits: true
  scenario: ideal
O: [pose_error_mm, orient_error_deg, iterations]
epsilon:
  pose_err_max_mm: 0.1
  orient_err_max_deg: 0.1
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | All 10 targets verified inside workspace | PASS |
| S2 | Jacobian non-singular for initial guesses | PASS |
| S3 | Convergence within 30 iterations for all targets | PASS |
| S4 | Pose error < 0.1 mm feasible | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# robotics/benchmark_ik_s1.yaml
spec_ref: sha256:<spec447_hash>
principle_ref: sha256:<p447_hash>
dataset:
  name: IKBench_10
  poses: 10
  data_hash: sha256:<dataset_447_hash>
baselines:
  - solver: Damped-LS
    params: {lambda: 0.01}
    results: {pose_err_mm: 0.02, iterations: 12}
  - solver: CCD
    params: {}
    results: {pose_err_mm: 0.05, iterations: 25}
  - solver: Analytic-6DOF
    params: {}
    results: {pose_err_mm: 0.0, iterations: 1}
quality_scoring:
  - {max_err_mm: 0.005, Q: 1.00}
  - {max_err_mm: 0.02, Q: 0.90}
  - {max_err_mm: 0.05, Q: 0.80}
  - {max_err_mm: 0.10, Q: 0.75}
```

**Baseline solver:** Damped-LS — 0.02 mm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Pose Error (mm) | Iterations | Runtime | Q |
|--------|----------------|-----------|---------|---|
| Analytic 6-DOF | 0.0 | 1 | 0.001 s | 1.00 |
| Damped LS | 0.02 | 12 | 0.01 s | 0.92 |
| CCD | 0.05 | 25 | 0.02 s | 0.82 |
| Neural IK | 0.08 | 1 | 0.005 s | 0.78 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (Analytic): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p447_hash>",
  "h_s": "sha256:<spec447_hash>",
  "h_b": "sha256:<bench447_hash>",
  "r": {"pose_error_mm": 0.0, "error_bound": 0.1, "ratio": 0.00},
  "c": {"method": "Analytic-6DOF", "solutions": 8, "K": 3},
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
pwm-node benchmarks | grep inverse_kinematics
pwm-node verify robotics/ik_s1_ideal.yaml
pwm-node mine robotics/ik_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
