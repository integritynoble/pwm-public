# Principle #206 — Cryogenic Boil-Off

**Domain:** Heat Transfer | **Carrier:** N/A (PDE-based) | **Difficulty:** Frontier (δ=10)
**DAG:** [∂.time] --> [∂.space.laplacian] --> [N.pointwise.boiloff] --> [B.robin] |  **Reward:** 10× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→∂.space.laplacian→N.pointwise.boiloff→B.robin   CryoBoil    LH2-tank          FVM+VOF
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CRYOGENIC BOIL-OFF   P = (E,G,W,C)   Principle #206            │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ρcₚ(∂T/∂t + u·∇T) = ∇·(k∇T) + Q_phase               │
│        │ Phase change: liquid → vapor at T_sat(p)               │
│        │ Pressure rise: dp/dt = (ṁ_evap · h_fg)/(V_ullage ρ_v) │
│        │ Two-phase: VOF or homogeneous mixture model            │
│        │ Forward: tank geometry/insulation/heat leak → boiloff │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [∂.space.laplacian] --> [N.pointwise.boiloff] --> [B.robin]│
│        │ time  thermal-diffusion  boil-off-rate  convective-BC                   │
│        │ V={∂.time,∂.space.laplacian,N.pointwise.boiloff,B.robin}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (coupled thermal-phase system)          │
│        │ Uniqueness: YES for quasi-steady evaporation           │
│        │ Stability: stiff phase-change source; adaptive dt     │
│        │ Mismatch: insulation k, heat leak paths, ullage model │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = boil-off rate error, pressure rise rate error      │
│        │ q = 1.0-2.0 (FVM with phase change)                  │
│        │ T = {boiloff_rate_error, pressure_rise_error, T_error}│
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Energy + phase change coupling consistent; mass conserved | PASS |
| S2 | Quasi-steady evaporation well-posed; Clausius-Clapeyron valid | PASS |
| S3 | VOF + energy converge; evaporation source bounded | PASS |
| S4 | Boil-off rate error < 10% vs experimental tank data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# cryo_boiloff/lh2_tank_s1.yaml
principle_ref: sha256:<p206_hash>
omega:
  grid: [100, 200]   # radial × axial (axisymmetric)
  domain: cylindrical_tank
  time: [0, 86400]   # 24 hours
E:
  forward: "NS + energy + VOF + evaporation model"
  fluid: {LH2: {T_sat: 20.3, h_fg: 446e3, rho_l: 70.8, rho_v: 1.34}}
B:
  wall: {heat_leak: 2.0}   # W/m²
  top: {pressure_vent: 1.5e5}   # Pa
  IC: {fill_level: 0.9, T_liquid: 20.0, T_ullage: 22.0}
I:
  scenario: self_pressurization_LH2
  heat_leak_W_per_m2: [1, 2, 5]
  mesh_sizes: [50x100, 100x200]
O: [boiloff_rate_error, pressure_rise_error, stratification_T_error]
epsilon:
  boiloff_error_max: 1.0e-1
  pressure_rise_error_max: 1.5e-1
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Axisymmetric tank; LH2 properties at 20K valid | PASS |
| S2 | Self-pressurization model well-posed | PASS |
| S3 | VOF + evaporation source converges with mesh | PASS |
| S4 | Boil-off rate < 10% error vs NASA experimental data | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# cryo_boiloff/benchmark_lh2.yaml
spec_ref: sha256:<spec206_hash>
principle_ref: sha256:<p206_hash>
dataset:
  name: NASA_LH2_tank_experiment
  reference: "NASA MHTB (Multi-purpose Hydrogen Test Bed)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Lumped (0D thermodynamic)
    params: {dt: 60}
    results: {boiloff_err: 15%, pressure_rise_err: 20%}
  - solver: 1D stratified (FLOW-3D)
    params: {grid: 100x200}
    results: {boiloff_err: 8%, pressure_rise_err: 12%}
  - solver: CFD-VOF (OpenFOAM)
    params: {grid: 100x200}
    results: {boiloff_err: 5%, pressure_rise_err: 8%}
quality_scoring:
  - {min_boiloff_err: 3%, Q: 1.00}
  - {min_boiloff_err: 7%, Q: 0.90}
  - {min_boiloff_err: 12%, Q: 0.80}
  - {min_boiloff_err: 20%, Q: 0.75}
```

**Baseline solver:** CFD-VOF — boil-off error 5%
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Boiloff Err | Press Rise Err | Runtime | Q |
|--------|------------|---------------|---------|---|
| Lumped 0D | 15% | 20% | 1 s | 0.75 |
| 1D stratified | 8% | 12% | 30 min | 0.80 |
| CFD-VOF | 5% | 8% | 24 h | 0.90 |
| CFD-VOF (fine) | 2.5% | 4% | 72 h | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 10 × 1.0 × Q
Best case (fine VOF): 1000 × 1.00 = 1000 PWM
Floor:                1000 × 0.75 = 750 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p206_hash>",
  "h_s": "sha256:<spec206_hash>",
  "h_b": "sha256:<bench206_hash>",
  "r": {"residual_norm": 2.5e-2, "error_bound": 1.0e-1, "ratio": 0.25},
  "c": {"fitted_rate": 1.5, "theoretical_rate": 2.0, "K": 2},
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
| L4 Solution | — | 750–1000 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep cryo
pwm-node verify cryo_boiloff/lh2_tank_s1.yaml
pwm-node mine cryo_boiloff/lh2_tank_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
