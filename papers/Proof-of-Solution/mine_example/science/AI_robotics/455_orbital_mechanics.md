# Principle #455 — Orbital Mechanics (Two-Body)

**Domain:** Robotics & Mechanical Systems | **Carrier:** gravitational | **Difficulty:** Standard (δ=2)
**DAG:** [N.bilinear.pair] --> [∂.time.symplectic] | **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.bilin.pair-->∂.t.symp  Orbit  OrbitBench-10  Kepler/RK
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ORBITAL MECHANICS          P = (E, G, W, C)   Principle #455  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ r̈ = −μ r/|r|³ + a_pert  (Newton's gravitation)        │
│        │ Kepler elements: (a, e, i, Ω, ω, ν) → (r, v)         │
│        │ Perturbations: J2, drag, SRP, third-body              │
│        │ Inverse: orbit determination from tracking data        │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.bilin.pair] ──→ [∂.t.symp]                          │
│        │   joint-pair  symplectic-step                           │
│        │ V={N.bilin.pair,∂.t.symp}  A={N.bilin.pair→∂.t.symp}  L_DAG=1.0                     │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (analytic for two-body)                 │
│        │ Uniqueness: YES (6 orbital elements from 6-state IC)  │
│        │ Stability: bounded orbits for E < 0                    │
│        │ Mismatch: perturbation modeling errors, drag uncert.   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = position error (primary), velocity error (second.) │
│        │ q = analytic (two-body); O(h⁴) for numerical (RK4)   │
│        │ T = {position_error_km, velocity_error, energy_drift}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Gravitational parameter μ, initial (r,v) consistent | PASS |
| S2 | Two-body analytic solution (Kepler equation) unique | PASS |
| S3 | Kepler equation solvable by Newton in < 10 iterations | PASS |
| S4 | Position error < 1 m for unperturbed 1-orbit propagation | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# robotics/orbital_s1_ideal.yaml
principle_ref: sha256:<p455_hash>
omega:
  description: "LEO satellite, a=7000 km, e=0.001, 10 orbits"
  mu: 398600.4418  # km³/s²
  orbits: 10
E:
  forward: "r_ddot = -mu*r/|r|^3"
  method: "Kepler equation + RK78 with perturbations"
I:
  dataset: OrbitBench_10
  orbits: 10
  perturbations: {J2: true, drag: false}
  scenario: ideal
O: [position_error_m, velocity_error_m_s, energy_drift]
epsilon:
  pos_err_max_m: 1.0
  energy_drift_max: 1e-8
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Orbital elements physical; μ matches Earth | PASS |
| S2 | Kepler equation well-posed for e=0.001 | PASS |
| S3 | RK78 adaptive integrator converges | PASS |
| S4 | Position error < 1 m feasible for 10 orbits | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# robotics/benchmark_orbital_s1.yaml
spec_ref: sha256:<spec455_hash>
principle_ref: sha256:<p455_hash>
dataset:
  name: OrbitBench_10
  orbits: 10
  data_hash: sha256:<dataset_455_hash>
baselines:
  - solver: Kepler-Analytic
    params: {}
    results: {pos_err_m: 0.0, vel_err: 0.0}
  - solver: RK78
    params: {tol: 1e-12}
    results: {pos_err_m: 0.001, vel_err: 1e-6}
  - solver: RK4
    params: {dt: 10}
    results: {pos_err_m: 5.0, vel_err: 0.005}
quality_scoring:
  - {max_pos_m: 0.01, Q: 1.00}
  - {max_pos_m: 0.1, Q: 0.90}
  - {max_pos_m: 1.0, Q: 0.80}
  - {max_pos_m: 10.0, Q: 0.75}
```

**Baseline solver:** Kepler-Analytic — exact
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Pos Error (m) | Vel Error | Runtime | Q |
|--------|-------------|----------|---------|---|
| Kepler Analytic | 0.0 | 0.0 | 0.001 s | 1.00 |
| RK78 Adaptive | 0.001 | 1e-6 | 0.5 s | 0.98 |
| RK4 (dt=10s) | 5.0 | 0.005 | 0.1 s | 0.78 |
| SGP4 | 100 | 0.1 | 0.001 s | 0.72 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (Kepler): 200 × 1.00 = 200 PWM
Floor:              200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p455_hash>",
  "h_s": "sha256:<spec455_hash>",
  "h_b": "sha256:<bench455_hash>",
  "r": {"pos_error_m": 0.0, "error_bound": 1.0, "ratio": 0.00},
  "c": {"method": "Kepler-Analytic", "exact": true, "K": 3},
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
pwm-node benchmarks | grep orbital_mechanics
pwm-node verify robotics/orbital_s1_ideal.yaml
pwm-node mine robotics/orbital_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
