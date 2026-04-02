# Principle #446 — Forward Kinematics

**Domain:** Robotics & Mechanical Systems | **Carrier:** mechanical | **Difficulty:** Textbook (δ=1)
**DAG:** [N.trigonometric] --> [L.homogeneous] | **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.trig-->L.homo  FK-pose  FKBench-10  DH/PoE
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  FORWARD KINEMATICS         P = (E, G, W, C)   Principle #446  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ T_0n = Π_{i=1}^{n} A_i(θ_i)  (DH transformations)    │
│        │ A_i = Rot_z(θ_i)·Trans_z(d_i)·Trans_x(a_i)·Rot_x(α_i)│
│        │ p_ee = T_0n · [0,0,0,1]ᵀ (end-effector position)     │
│        │ Forward map: joint angles θ → end-effector pose       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.trig] ──→ [L.homo]                                  │
│        │   joint-angles  SE(3)-chain                             │
│        │ V={N.trig,L.homo}  A={N.trig→L.homo}  L_DAG=1.0                           │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (product of matrices always defined)    │
│        │ Uniqueness: YES (deterministic forward map)            │
│        │ Stability: well-conditioned away from singularities    │
│        │ Mismatch: DH parameter errors, joint flexibility      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = position error ‖p̂−p‖ (primary), orient. err (sec.)│
│        │ q = exact (closed-form matrix product)                │
│        │ T = {position_error, orientation_error}                │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | DH parameters (a, α, d, θ) dimensions match n_joints | PASS |
| S2 | SE(3) group closure → valid transformation matrices | PASS |
| S3 | Matrix multiplication exact (no iterative solver needed) | PASS |
| S4 | Position error = 0 for exact DH parameters | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# robotics/fk_s1_ideal.yaml
principle_ref: sha256:<p446_hash>
omega:
  description: "6-DOF industrial manipulator, DH convention"
  joints: 6
  link_lengths: [0.4, 0.3, 0.2, 0.1, 0.1, 0.05]
E:
  forward: "T_0n = product of A_i(theta_i)"
  convention: "modified DH"
I:
  dataset: FKBench_10
  configurations: 10
  noise: {type: none}
  scenario: ideal
O: [position_error_mm, orientation_error_deg]
epsilon:
  pos_err_max_mm: 0.01
  orient_err_max_deg: 0.01
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 6 joints, DH table complete and consistent | PASS |
| S2 | All transformations in SE(3) | PASS |
| S3 | Exact computation; no convergence issues | PASS |
| S4 | Position error < 0.01 mm (machine precision) | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# robotics/benchmark_fk_s1.yaml
spec_ref: sha256:<spec446_hash>
principle_ref: sha256:<p446_hash>
dataset:
  name: FKBench_10
  configurations: 10
  data_hash: sha256:<dataset_446_hash>
baselines:
  - solver: DH-Matrix
    params: {convention: modified}
    results: {pos_err_mm: 0.0, orient_err_deg: 0.0}
  - solver: PoE-Screw
    params: {}
    results: {pos_err_mm: 0.0, orient_err_deg: 0.0}
  - solver: Dual-Quaternion
    params: {}
    results: {pos_err_mm: 0.0, orient_err_deg: 0.0}
quality_scoring:
  - {max_err_mm: 0.001, Q: 1.00}
  - {max_err_mm: 0.01, Q: 0.90}
  - {max_err_mm: 0.1, Q: 0.80}
  - {max_err_mm: 1.0, Q: 0.75}
```

**Baseline solver:** DH-Matrix — exact
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Pos Error (mm) | Orient Error (deg) | Runtime | Q |
|--------|---------------|-------------------|---------|---|
| DH Matrix | 0.0 | 0.0 | 0.001 s | 1.00 |
| PoE Screw | 0.0 | 0.0 | 0.001 s | 1.00 |
| Dual Quaternion | 0.0 | 0.0 | 0.001 s | 1.00 |
| Neural FK | 0.05 | 0.02 | 0.005 s | 0.88 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (DH):    100 × 1.00 = 100 PWM
Floor:             100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p446_hash>",
  "h_s": "sha256:<spec446_hash>",
  "h_b": "sha256:<bench446_hash>",
  "r": {"pos_error_mm": 0.0, "error_bound": 0.01, "ratio": 0.00},
  "c": {"method": "DH-Matrix", "exact": true, "K": 3},
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
| L4 Solution | — | 75–100 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep forward_kinematics
pwm-node verify robotics/fk_s1_ideal.yaml
pwm-node mine robotics/fk_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
