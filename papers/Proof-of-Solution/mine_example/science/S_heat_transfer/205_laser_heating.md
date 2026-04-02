# Principle #205 — Laser Heating (Volumetric Absorption)

**Domain:** Heat Transfer | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [G.pulse.laser] --> [N.pointwise.exp] --> [∂.time] --> [∂.space] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.pulse.laser→N.pointwise.exp→∂.time→∂.space      LaserHeat   surface-melt      FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LASER HEATING   P = (E,G,W,C)   Principle #205                 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ρcₚ ∂T/∂t = ∇·(k∇T) + Q_laser(x,t)                  │
│        │ Q = αI₀ exp(−αz) · f(r) · g(t)                        │
│        │ Beer-Lambert absorption; Gaussian beam profile         │
│        │ Phase change: enthalpy method if T > T_melt            │
│        │ Forward: laser params/material → T(x,t) + melt pool   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse.laser] --> [N.pointwise.exp] --> [∂.time] --> [∂.space]│
│        │ laser-source  Beer-Lambert-absorption  time-stepping  spatial-diffusion│
│        │ V={G.pulse.laser,N.pointwise.exp,∂.time,∂.space}  L_DAG=3.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (parabolic with smooth source)          │
│        │ Uniqueness: YES (maximum principle)                    │
│        │ Stability: adaptive dt near peak temperature           │
│        │ Mismatch: absorptivity α, beam profile, emissivity   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = peak temperature error, melt pool depth error      │
│        │ q = 2.0 (FEM with adaptive mesh)                      │
│        │ T = {T_peak_error, melt_depth_error, energy_balance}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Beer-Lambert source consistent; Gaussian beam well-defined | PASS |
| S2 | Parabolic PDE with bounded source; unique solution | PASS |
| S3 | FEM + adaptive time stepping converges | PASS |
| S4 | Peak T error bounded; Rosenthal solution as limiting case | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# laser_heating/surface_melt_s1.yaml
principle_ref: sha256:<p205_hash>
omega:
  grid: [100, 100, 50]
  domain: [0.001, 0.001, 0.0005]   # 1mm × 1mm × 0.5mm
  time: [0, 0.001]   # 1 ms pulse
E:
  forward: "ρcₚ ∂T/∂t = ∇·(k∇T) + Q_laser"
  material: {k: 30, rho_cp: 4.5e6, T_melt: 1700}
  laser: {power: 200, radius: 100e-6, absorption: 0.35}
B:
  surface: {convection: {h: 10, T_inf: 300}, radiation: {emissivity: 0.3}}
  bottom: {T: 300}
  IC: {T: 300}
I:
  scenario: pulsed_laser_surface_heating
  fluence: 6.4e6   # J/m²
  mesh_sizes: [50x50x25, 100x100x50]
O: [T_peak_error, melt_depth_error, cooling_rate_error]
epsilon:
  T_peak_error_max: 5.0e-2
  melt_depth_error_max: 1.0e-1
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 3D mesh resolves beam radius; time steps resolve pulse | PASS |
| S2 | Parabolic well-posed; Rosenthal analytical check | PASS |
| S3 | FEM + BDF2 converges; adaptive dt at pulse peak | PASS |
| S4 | Peak T error < 5% vs fine-mesh reference | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# laser_heating/benchmark_melt.yaml
spec_ref: sha256:<spec205_hash>
principle_ref: sha256:<p205_hash>
dataset:
  name: Laser_surface_melt_ref
  reference: "Rosenthal (1946) + numerical convergence study"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-P1 (fixed dt)
    params: {grid: 100x100x50, dt: 1e-6}
    results: {T_peak_err: 3.8e-2, melt_depth_err: 8.5e-2}
  - solver: FEM-P2 (adaptive dt)
    params: {grid: 50x50x25}
    results: {T_peak_err: 2.1e-2, melt_depth_err: 5.2e-2}
  - solver: FVM (AMR)
    params: {base_grid: 50x50x25, levels: 3}
    results: {T_peak_err: 1.5e-2, melt_depth_err: 3.8e-2}
quality_scoring:
  - {min_T_peak_err: 1.0e-2, Q: 1.00}
  - {min_T_peak_err: 3.0e-2, Q: 0.90}
  - {min_T_peak_err: 5.0e-2, Q: 0.80}
  - {min_T_peak_err: 1.0e-1, Q: 0.75}
```

**Baseline solver:** FVM AMR — T peak error 1.5×10⁻²
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | T Peak Err | Melt Depth Err | Runtime | Q |
|--------|-----------|---------------|---------|---|
| FEM-P1 (fixed dt) | 3.8e-2 | 8.5e-2 | 120 s | 0.80 |
| FEM-P2 (adaptive) | 2.1e-2 | 5.2e-2 | 90 s | 0.90 |
| FVM (AMR) | 1.5e-2 | 3.8e-2 | 60 s | 0.90 |
| FEM-P2 (fine+AMR) | 8.5e-3 | 1.8e-2 | 300 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case: 300 × 1.00 = 300 PWM
Floor:     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p205_hash>",
  "h_s": "sha256:<spec205_hash>",
  "h_b": "sha256:<bench205_hash>",
  "r": {"residual_norm": 8.5e-3, "error_bound": 5.0e-2, "ratio": 0.17},
  "c": {"fitted_rate": 1.92, "theoretical_rate": 2.0, "K": 2},
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
pwm-node benchmarks | grep laser_heat
pwm-node verify laser_heating/surface_melt_s1.yaml
pwm-node mine laser_heating/surface_melt_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
