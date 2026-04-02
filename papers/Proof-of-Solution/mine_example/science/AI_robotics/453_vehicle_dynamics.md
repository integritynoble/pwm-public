# Principle #453 — Vehicle Dynamics (Bicycle Model)

**Domain:** Robotics & Mechanical Systems | **Carrier:** mechanical | **Difficulty:** Standard (δ=2)
**DAG:** [N.bilinear] --> [∂.time] --> [L.dense] | **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.bilin-->∂.t-->L.dense  VehDyn  VehBench-10  RK4/EKF
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  VEHICLE DYNAMICS (BICYCLE) P = (E, G, W, C)   Principle #453  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ m(v̇_y + v_x·r) = F_yf + F_yr  (lateral)              │
│        │ I_z·ṙ = l_f·F_yf − l_r·F_yr   (yaw)                  │
│        │ F_y = C_α·α (linear tire model)                       │
│        │ Inverse: estimate tire params or state from sensors    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.bilin] ──→ [∂.t] ──→ [L.dense]                      │
│        │   tire-forces  integration  mass-matrix                 │
│        │ V={N.bilin,∂.t,L.dense}  A={N.bilin→∂.t,∂.t→L.dense}  L_DAG=2.0                     │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear ODE for small angles)           │
│        │ Uniqueness: YES (linear system)                        │
│        │ Stability: understeer → stable; oversteer → cond.     │
│        │ Mismatch: nonlinear tires, load transfer, road grade  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = yaw rate error (primary), sideslip error (second.) │
│        │ q = 2.0 (RK4 integration)                            │
│        │ T = {yaw_rate_error, sideslip_error, path_error}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Vehicle parameters (m, I_z, l_f, l_r, C_α) physical | PASS |
| S2 | Linear model well-posed for |α| < 5° | PASS |
| S3 | RK4 integration stable at dt=1ms | PASS |
| S4 | Yaw rate error < 2% vs measured data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# robotics/vehicle_bicycle_s1_ideal.yaml
principle_ref: sha256:<p453_hash>
omega:
  description: "Sedan, v_x=20 m/s, lane-change maneuver"
  params: {m: 1500, Iz: 2500, lf: 1.2, lr: 1.5, Cf: 80000, Cr: 80000}
E:
  forward: "2-DOF bicycle model, linear tire"
  states: [v_y, yaw_rate]
I:
  dataset: VehBench_10
  maneuvers: 10
  scenario: ideal
O: [yaw_rate_RMSE, sideslip_RMSE]
epsilon:
  yaw_rate_RMSE_max: 0.02
  sideslip_RMSE_max: 0.005
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | All vehicle parameters specified and physical | PASS |
| S2 | Linear tire valid for small-angle maneuvers | PASS |
| S3 | System stable (understeer gradient positive) | PASS |
| S4 | Yaw rate RMSE < 0.02 rad/s feasible | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# robotics/benchmark_vehicle_s1.yaml
spec_ref: sha256:<spec453_hash>
principle_ref: sha256:<p453_hash>
dataset:
  name: VehBench_10
  maneuvers: 10
  data_hash: sha256:<dataset_453_hash>
baselines:
  - solver: Linear-Bicycle
    params: {}
    results: {yaw_RMSE: 0.012, sideslip_RMSE: 0.003}
  - solver: Nonlinear-Pacejka
    params: {tire: MF52}
    results: {yaw_RMSE: 0.005, sideslip_RMSE: 0.001}
  - solver: CarSim-Reference
    params: {}
    results: {yaw_RMSE: 0.002, sideslip_RMSE: 0.0005}
quality_scoring:
  - {max_yaw_RMSE: 0.003, Q: 1.00}
  - {max_yaw_RMSE: 0.008, Q: 0.90}
  - {max_yaw_RMSE: 0.015, Q: 0.80}
  - {max_yaw_RMSE: 0.025, Q: 0.75}
```

**Baseline solver:** Linear-Bicycle — yaw RMSE 0.012
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Yaw RMSE | Sideslip RMSE | Runtime | Q |
|--------|---------|-------------|---------|---|
| Linear Bicycle | 0.012 | 0.003 | 0.01 s | 0.85 |
| Nonlinear Pacejka | 0.005 | 0.001 | 0.05 s | 0.95 |
| CarSim Ref | 0.002 | 0.0005 | 1.0 s | 1.00 |
| Neural VehDyn | 0.004 | 0.001 | 0.02 s | 0.96 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (CarSim): 200 × 1.00 = 200 PWM
Floor:              200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p453_hash>",
  "h_s": "sha256:<spec453_hash>",
  "h_b": "sha256:<bench453_hash>",
  "r": {"yaw_RMSE": 0.002, "error_bound": 0.02, "ratio": 0.10},
  "c": {"method": "CarSim", "fidelity": "high", "K": 3},
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
pwm-node benchmarks | grep vehicle_dynamics
pwm-node verify robotics/vehicle_bicycle_s1_ideal.yaml
pwm-node mine robotics/vehicle_bicycle_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
