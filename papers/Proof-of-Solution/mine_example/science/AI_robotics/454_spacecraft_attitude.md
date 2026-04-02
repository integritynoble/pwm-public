# Principle #454 — Spacecraft Attitude Dynamics

**Domain:** Robotics & Mechanical Systems | **Carrier:** mechanical | **Difficulty:** Standard (δ=3)
**DAG:** [N.bilinear.quaternion] --> [∂.time] --> [N.bilinear] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.bilin.quat-->∂.t-->N.bilin  AttDyn  AttBench-10  RK4/Quat
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SPACECRAFT ATTITUDE DYN.   P = (E, G, W, C)   Principle #454  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I ω̇ = −ω × (I ω) + τ_ext   (Euler's equations)       │
│        │ q̇ = ½ Ω(ω) q   (quaternion kinematics)               │
│        │ τ_ext = gravity gradient + magnetic + thruster torques │
│        │ Inverse: estimate attitude/rates from sensor data      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.bilin.quat] ──→ [∂.t] ──→ [N.bilin]                 │
│        │   quaternion  integration  gravity-gradient             │
│        │ V={N.bilin.quat,∂.t,N.bilin}  A={N.bilin.quat→∂.t,∂.t→N.bilin}  L_DAG=2.0             │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (smooth ODE)                            │
│        │ Uniqueness: YES (Lipschitz RHS)                        │
│        │ Stability: depends on spin axis and inertia ratios     │
│        │ Mismatch: flexible appendages, fuel slosh, J2 torque   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = pointing error (primary), rate error (secondary)   │
│        │ q = 4th-order (RK4 with quat. normalization)          │
│        │ T = {pointing_error_deg, rate_error, quat_norm}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Inertia tensor SPD; quaternion unit-norm maintained | PASS |
| S2 | Euler equations well-posed; torques bounded | PASS |
| S3 | RK4 + quaternion renormalization converges | PASS |
| S4 | Pointing error < 0.1° achievable for known torques | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# robotics/attitude_s1_ideal.yaml
principle_ref: sha256:<p454_hash>
omega:
  description: "3-axis stabilized satellite, LEO, T=1 orbit"
  inertia: [50, 60, 40]  # kg·m²
  orbit_period: 5400  # s
E:
  forward: "I*omega_dot = -omega x (I*omega) + tau"
  kinematics: "quaternion propagation"
I:
  dataset: AttBench_10
  scenarios: 10
  torques: [gravity_gradient, magnetic]
  scenario: ideal
O: [pointing_error_deg, rate_error_deg_s]
epsilon:
  pointing_max_deg: 0.1
  rate_max_deg_s: 0.01
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Inertia tensor diagonal, orbit parameters consistent | PASS |
| S2 | Gravity gradient and magnetic torques bounded | PASS |
| S3 | RK4 at dt=0.1s converges for orbital period | PASS |
| S4 | Pointing < 0.1° feasible with attitude control | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# robotics/benchmark_attitude_s1.yaml
spec_ref: sha256:<spec454_hash>
principle_ref: sha256:<p454_hash>
dataset:
  name: AttBench_10
  scenarios: 10
  data_hash: sha256:<dataset_454_hash>
baselines:
  - solver: RK4-Quat
    params: {dt: 0.1}
    results: {pointing_deg: 0.02, rate_err: 0.002}
  - solver: RK78-Quat
    params: {adaptive: true}
    results: {pointing_deg: 0.005, rate_err: 0.0005}
  - solver: Forward-Euler
    params: {dt: 0.1}
    results: {pointing_deg: 0.15, rate_err: 0.02}
quality_scoring:
  - {max_pointing: 0.005, Q: 1.00}
  - {max_pointing: 0.02, Q: 0.90}
  - {max_pointing: 0.08, Q: 0.80}
  - {max_pointing: 0.15, Q: 0.75}
```

**Baseline solver:** RK4-Quat — pointing 0.02°
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Pointing (deg) | Rate Error | Runtime | Q |
|--------|---------------|-----------|---------|---|
| RK4-Quat | 0.020 | 0.002 | 0.5 s | 0.90 |
| RK78-Adaptive | 0.005 | 0.0005 | 1.0 s | 1.00 |
| Forward Euler | 0.150 | 0.020 | 0.1 s | 0.75 |
| Lie-Group Integrator | 0.008 | 0.001 | 0.8 s | 0.96 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (RK78):  300 × 1.00 = 300 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p454_hash>",
  "h_s": "sha256:<spec454_hash>",
  "h_b": "sha256:<bench454_hash>",
  "r": {"pointing_deg": 0.005, "error_bound": 0.1, "ratio": 0.05},
  "c": {"method": "RK78-Adaptive", "quat_norm": 1.0, "K": 3},
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
pwm-node benchmarks | grep spacecraft_attitude
pwm-node verify robotics/attitude_s1_ideal.yaml
pwm-node mine robotics/attitude_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
