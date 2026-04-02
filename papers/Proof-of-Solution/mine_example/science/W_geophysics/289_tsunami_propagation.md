# Principle #289 — Tsunami Propagation

**Domain:** Geophysics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** ∂.time → N.flux → ∂.space → B.coast |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.flux→∂.space→B.coast      tsunami     ocean-basin        SWE-FDM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  TSUNAMI PROPAGATION              P = (E,G,W,C)   Principle #289│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂η/∂t + ∇·[(h+η)u] = 0   (continuity)                │
│        │ ∂u/∂t + (u·∇)u = −g∇η − τ_b/(ρh) (momentum)          │
│        │ Linear limit: c = √(gh), long-wave approximation       │
│        │ Forward: given initial η₀(x,y) + bathymetry → η(x,y,t)│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [N.flux] ──→ [∂.space] ──→ [B.coast]      │
│        │ derivative  nonlinear  derivative  boundary            │
│        │ V={∂.time, N.flux, ∂.space, B.coast}  A={∂.time→N.flux, N.flux→∂.space, ∂.space→B.coast}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (shallow water equations well-posed)    │
│        │ Uniqueness: YES for given IC/BC and bathymetry          │
│        │ Stability: CFL condition c·dt/dx < 1                   │
│        │ Mismatch: dispersive effects, wetting/drying, friction │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖η_sim − η_obs‖₂ / ‖η_obs‖₂ (wave height misfit) │
│        │ q = 2.0 (leap-frog), 1.0 (upwind)                    │
│        │ T = {arrival_time_error, max_amplitude, inundation}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Shallow water equations dimensionally consistent; CFL well-defined | PASS |
| S2 | Linear SWE analytical solution exists for flat bathymetry | PASS |
| S3 | Staggered-grid FDM (MOST/COMCOT) converges for ocean-basin scale | PASS |
| S4 | Wave height error bounded by grid resolution and source model | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# tsunami/ocean_basin_s1_ideal.yaml
principle_ref: sha256:<p289_hash>
omega:
  grid: [1800, 900]
  domain: Pacific_basin
  resolution: 2_arcmin
  time: [0, 36000]  # 10 hours in seconds
  dt: 2.0
E:
  forward: "nonlinear shallow water equations"
  bathymetry: GEBCO_2023
  manning_n: 0.025
B:
  open_boundary: radiation
  coast: wetting_drying
I:
  scenario: subduction_earthquake_Mw9
  source: Okada_model
  fault_length: 500  # km
  slip: 15  # metres
O: [arrival_time_error, max_amplitude_error, inundation_extent]
epsilon:
  arrival_error_max: 60  # seconds
  amplitude_error_max: 0.15  # relative
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 2-arcmin grid resolves wavelengths >10 km; CFL satisfied at dt=2 s | PASS |
| S2 | Okada source model provides consistent initial displacement | PASS |
| S3 | Leap-frog FDM stable and convergent for 10-hour simulation | PASS |
| S4 | Arrival time error < 60 s achievable at 2-arcmin resolution | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# tsunami/benchmark_pacific.yaml
spec_ref: sha256:<spec289_hash>
principle_ref: sha256:<p289_hash>
dataset:
  name: DART_buoy_Tohoku_2011
  reference: "DART buoy records for 2011 Tohoku tsunami"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Linear-SWE-FDM
    params: {grid: 4arcmin, dt: 4s}
    results: {arrival_error: 120, amplitude_error: 0.25}
  - solver: Nonlinear-SWE-FDM
    params: {grid: 2arcmin, dt: 2s}
    results: {arrival_error: 45, amplitude_error: 0.12}
  - solver: Boussinesq-FDM
    params: {grid: 1arcmin, dt: 1s}
    results: {arrival_error: 30, amplitude_error: 0.08}
quality_scoring:
  - {min_arrival: 20, Q: 1.00}
  - {min_arrival: 45, Q: 0.90}
  - {min_arrival: 90, Q: 0.80}
  - {min_arrival: 180, Q: 0.75}
```

**Baseline solver:** Nonlinear-SWE — arrival error 45 s
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Arrival Err (s) | Ampl. Error | Runtime | Q |
|--------|----------------|-------------|---------|---|
| Linear-SWE 4' | 120 | 0.25 | 30 s | 0.80 |
| NL-SWE 2' | 45 | 0.12 | 300 s | 0.90 |
| Boussinesq 1' | 30 | 0.08 | 1800 s | 0.90 |
| AMR-Boussinesq | 15 | 0.05 | 900 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (AMR-Bouss): 300 × 1.00 = 300 PWM
Floor:                 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p289_hash>",
  "h_s": "sha256:<spec289_hash>",
  "h_b": "sha256:<bench289_hash>",
  "r": {"residual_norm": 15.0, "error_bound": 60.0, "ratio": 0.25},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep tsunami
pwm-node verify tsunami/ocean_basin_s1_ideal.yaml
pwm-node mine tsunami/ocean_basin_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
