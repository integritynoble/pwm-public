# Principle #290 — Geothermal Reservoir Modeling

**Domain:** Geophysics | **Carrier:** N/A (coupled PDE) | **Difficulty:** Hard (δ=5)
**DAG:** ∂.time → ∂.space.laplacian → N.pointwise |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→∂.space.laplacian→N.pointwise      geotherm    two-phase-res     TOUGH2
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  GEOTHERMAL RESERVOIR MODELING    P = (E,G,W,C)   Principle #290│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂(φρ)/∂t + ∇·(ρu) = q_m  (mass conservation)         │
│        │ ∂(φρe)/∂t + ∇·(ρhu) − ∇·(K∇T) = q_e (energy)        │
│        │ u = −(k/μ)(∇P − ρg)  (Darcy's law)                    │
│        │ Two-phase: water + steam; relative permeability curves │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [∂.space.laplacian] ──→ [N.pointwise]     │
│        │ derivative  derivative  nonlinear                      │
│        │ V={∂.time, ∂.space.laplacian, N.pointwise}  A={∂.time→∂.space.laplacian, ∂.space.laplacian→N.pointwise}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (parabolic PDE system well-posed)       │
│        │ Uniqueness: YES for single-phase; conditional 2-phase  │
│        │ Stability: depends on time-step and phase transitions  │
│        │ Mismatch: fracture permeability, scaling, mineral ppt  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖P_sim − P_obs‖₂ / ‖P_obs‖₂ (pressure misfit)    │
│        │ q = 1.0 (IFDM), 2.0 (FEM with adaptive)              │
│        │ T = {pressure_drawdown, enthalpy_match, steam_fraction}│
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Mass + energy conservation equations dimensionally consistent | PASS |
| S2 | TOUGH2 integral-FDM framework well-tested for two-phase flow | PASS |
| S3 | Newton-Raphson converges for coupled nonlinear system | PASS |
| S4 | Pressure misfit bounded by permeability uncertainty and grid | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# geotherm/two_phase_s1_ideal.yaml
principle_ref: sha256:<p290_hash>
omega:
  grid: [50, 50, 20]
  domain: 5km_x_5km_x_3km
  time: [0, 3.15e8]  # 10 years in seconds
  dt: adaptive
E:
  forward: "coupled mass+energy with two-phase (TOUGH2-type)"
  permeability: 1e-14  # m²
  porosity: 0.10
  initial_T: 250  # °C
B:
  top: {P: 1e5, T: 20}  # atmospheric
  bottom: heat_flux_0.08  # W/m²
  injection: {rate: 10, T: 60}  # kg/s, °C
I:
  scenario: production_injection
  wells: {production: 3, injection: 2}
  extraction_rate: 30  # kg/s total
O: [pressure_drawdown, enthalpy_output, steam_fraction]
epsilon:
  pressure_error_max: 5.0e-2
  enthalpy_error_max: 5.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 50×50×20 grid with 5 wells; 10-year simulation adequate | PASS |
| S2 | Two-phase thermodynamics fully specified by IAPWS-IF97 | PASS |
| S3 | Newton-Raphson with adaptive dt converges throughout | PASS |
| S4 | Pressure error < 5% matches well-test calibration | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# geotherm/benchmark_production.yaml
spec_ref: sha256:<spec290_hash>
principle_ref: sha256:<p290_hash>
dataset:
  name: synthetic_geothermal_5well
  reference: "TOUGH2 benchmark, 5-well two-phase scenario"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: TOUGH2-IFDM
    params: {grid: 50x50x20, EOS: EOS1}
    results: {pressure_error: 3.5e-2, enthalpy_error: 4.2e-2}
  - solver: FEHM
    params: {grid: 50x50x20, method: CVFE}
    results: {pressure_error: 2.8e-2, enthalpy_error: 3.5e-2}
  - solver: OpenGeoSys
    params: {grid: unstructured, method: FEM}
    results: {pressure_error: 2.2e-2, enthalpy_error: 2.8e-2}
quality_scoring:
  - {min_P_err: 1.0e-2, Q: 1.00}
  - {min_P_err: 3.0e-2, Q: 0.90}
  - {min_P_err: 5.0e-2, Q: 0.80}
  - {min_P_err: 1.0e-1, Q: 0.75}
```

**Baseline solver:** TOUGH2 — pressure error 3.5×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | P Error | h Error | Runtime | Q |
|--------|---------|---------|---------|---|
| TOUGH2 | 3.5e-2 | 4.2e-2 | 300 s | 0.90 |
| FEHM | 2.8e-2 | 3.5e-2 | 250 s | 0.90 |
| OpenGeoSys | 2.2e-2 | 2.8e-2 | 400 s | 0.90 |
| AMR-FEM | 8.5e-3 | 1.2e-2 | 800 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (AMR-FEM): 500 × 1.00 = 500 PWM
Floor:               500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p290_hash>",
  "h_s": "sha256:<spec290_hash>",
  "h_b": "sha256:<bench290_hash>",
  "r": {"residual_norm": 8.5e-3, "error_bound": 5.0e-2, "ratio": 0.17},
  "c": {"fitted_rate": 1.88, "theoretical_rate": 2.0, "K": 4},
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
| L4 Solution | — | 375–500 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep geotherm
pwm-node verify geotherm/two_phase_s1_ideal.yaml
pwm-node mine geotherm/two_phase_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
