# Principle #341 — Additive Manufacturing Process Simulation

**Domain:** Materials Science | **Carrier:** thermal/stress field | **Difficulty:** Frontier (δ=5)
**DAG:** G.pulse.laser → ∂.time → ∂.space → N.enthalpy |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.pulse.laser→∂.time→∂.space→N.enthalpy     AM-sim      LPBF-Ti64          FEM/thermo
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ADDITIVE MANUFACTURING SIM     P = (E,G,W,C)   Principle #341 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ρc_p ∂T/∂t = ∇·(k∇T) + Q_laser(x,t)                 │
│        │ Phase: φ(T) = 0 (solid), 1 (liquid), latent heat L    │
│        │ ∂σ/∂t = C : (ε̇_total − ε̇_thermal − ε̇_plastic)       │
│        │ Forward: given laser path, power → T(x,t), σ_residual │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse.laser] ──→ [∂.time] ──→ [∂.space] ──→ [N.enthalpy] │
│        │ source  derivative  derivative  nonlinear              │
│        │ V={G.pulse.laser, ∂.time, ∂.space, N.enthalpy}  A={G.pulse.laser→∂.time, ∂.time→∂.space, ∂.space→N.enthalpy}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (coupled thermo-mechanical PDE system)  │
│        │ Uniqueness: YES (for given laser parameters and BCs)   │
│        │ Stability: time-step limited by thermal diffusivity    │
│        │ Mismatch: powder properties, absorptivity, convection  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖T_sim − T_expt‖₂ / ‖T_expt‖₂ (primary)         │
│        │ q = 2.0 (FEM), 1.0 (inherent strain method)         │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Thermal and mechanical fields coupled consistently | PASS |
| S2 | Parabolic heat equation + quasi-static stress well-posed | PASS |
| S3 | FEM with adaptive meshing converges for moving heat source | PASS |
| S4 | Melt pool dimensions and residual stress measurable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# am_sim/lpbf_ti64_s1_ideal.yaml
principle_ref: sha256:<p341_hash>
omega:
  grid: [200, 100, 50]
  domain: [2.0, 1.0, 0.5]  # mm
  time: [0, 0.01]  # single track
  dt: 1.0e-6
E:
  forward: "ρc_p ∂T/∂t = ∇·(k∇T) + Q_laser"
  material: Ti-6Al-4V
B:
  substrate: {T: 473}  # preheat K
  top_surface: {radiation: true, convection: true}
I:
  scenario: single_track_LPBF
  laser_power: 200  # W
  scan_speed: 1.0  # m/s
  spot_diameter: 80e-6  # m
O: [melt_pool_depth, melt_pool_width, peak_temperature]
epsilon:
  melt_pool_error_max: 0.10  # relative
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid resolves melt pool (~100 μm); dt captures laser transit | PASS |
| S2 | Ti-6Al-4V thermo-physical properties well-tabulated | PASS |
| S3 | FEM with Goldak/Gaussian source converges | PASS |
| S4 | Melt pool dimensions within 10% of experiment | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# am_sim/benchmark_lpbf_ti64.yaml
spec_ref: sha256:<spec341_hash>
principle_ref: sha256:<p341_hash>
dataset:
  name: lpbf_ti64_melt_pool
  reference: "Cunningham et al. (2019) synchrotron X-ray imaging"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM (Abaqus DFLUX)
    params: {mesh: 20um, source: Goldak}
    results: {depth_error: 0.12, width_error: 0.08}
  - solver: FEM (FLOW-3D)
    params: {mesh: 10um, multiphysics: true}
    results: {depth_error: 0.06, width_error: 0.05}
  - solver: Analytical (Rosenthal)
    params: {}
    results: {depth_error: 0.25, width_error: 0.20}
quality_scoring:
  - {min_pool_error: 0.03, Q: 1.00}
  - {min_pool_error: 0.08, Q: 0.90}
  - {min_pool_error: 0.15, Q: 0.80}
  - {min_pool_error: 0.25, Q: 0.75}
```

**Baseline solver:** FEM (FLOW-3D) — depth error 6%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Depth Error | Width Error | Runtime | Q |
|--------|-----------|-----------|---------|---|
| Rosenthal | 0.25 | 0.20 | 0.01 s | 0.75 |
| FEM (Abaqus) | 0.12 | 0.08 | 2 h | 0.80 |
| FEM (FLOW-3D) | 0.06 | 0.05 | 8 h | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (FLOW-3D): 500 × 0.90 = 450 PWM
Floor:               500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p341_hash>",
  "h_s": "sha256:<spec341_hash>",
  "h_b": "sha256:<bench341_hash>",
  "r": {"residual_norm": 0.06, "error_bound": 0.10, "ratio": 0.60},
  "c": {"fitted_rate": 2.0, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.90,
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
| L4 Solution | — | 375–450 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep am_sim
pwm-node verify am_sim/lpbf_ti64_s1_ideal.yaml
pwm-node mine am_sim/lpbf_ti64_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
