# Principle #419 — Ocean Circulation Model

**Domain:** Environmental Science | **Carrier:** ocean state (u,T,S) | **Difficulty:** Advanced (δ=5)
**DAG:** ∂.time → N.bilinear.advection → ∂.space → B.surface |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→∂.space→B.surface   ocean-GCM    double-gyre       FDM/FVM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  OCEAN CIRCULATION MODEL        P = (E,G,W,C)   Principle #419 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂u/∂t + (u·∇)u − fv = −(1/ρ₀)∂p/∂x + A_H∇²u + ∂(A_V∂u/∂z)/∂z│
│        │ ∂T/∂t + u·∇T = κ_H∇²T + ∂(κ_V∂T/∂z)/∂z             │
│        │ ∂S/∂t + u·∇S = κ_H∇²S + ∂(κ_V∂S/∂z)/∂z             │
│        │ ρ = ρ(T,S,p)  (equation of state)                     │
│        │ Forward: given wind/heat forcing → u,T,S,η over ocean │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [N.bilinear.advection] ──→ [∂.space] ──→ [B.surface] │
│        │ derivative  nonlinear  derivative  boundary            │
│        │ V={∂.time, N.bilinear.advection, ∂.space, B.surface}  A={∂.time→N.bilinear.advection, N.bilinear.advection→∂.space, ∂.space→B.surface}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (primitive equations, hydrostatic)      │
│        │ Uniqueness: conditional (multiple steady states possible)│
│        │ Stability: barotropic CFL + baroclinic mode constraint │
│        │ Mismatch: vertical mixing, mesoscale eddy closure      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = SST RMSE (°C) or transport error (Sv)             │
│        │ q = resolution and scheme-dependent                   │
│        │ T = {SST_RMSE, MOC_error, transport_error}             │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Velocity, temperature, salinity dimensions consistent | PASS |
| S2 | Hydrostatic primitive equations well-posed with forcing | PASS |
| S3 | Split-explicit barotropic/baroclinic time stepping converges | PASS |
| S4 | SST and MOC computable against Argo/reanalysis data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# ocean_circulation/double_gyre_s1_ideal.yaml
principle_ref: sha256:<p419_hash>
omega:
  grid: [200, 200, 20]
  domain: rectangular_basin
  size: [4000, 4000, 5000]   # km, km, m
  time: [0, 100]   # years (spinup)
  dt: 3600   # s
E:
  forward: "Hydrostatic primitive equations + linear EOS"
  A_H: 1000   # m²/s (horizontal viscosity)
  kappa_H: 500   # m²/s (horizontal diffusivity)
B:
  wind: {zonal_profile: double_cosine}
  surface: {relaxation_to_T_star: true}
  lateral: {no_slip: true}
I:
  scenario: wind_driven_double_gyre
  resolutions: [1.0, 0.5, 0.25]   # degrees
O: [transport_error, SST_RMSE, western_BC_strength]
epsilon:
  transport_error_max: 5.0   # Sv
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200x200x20 grid resolves gyre circulation; dt=1h stable | PASS |
| S2 | Double-gyre has well-defined steady-state circulation | PASS |
| S3 | Split-explicit stepping converges; 100-year spinup adequate | PASS |
| S4 | Transport error < 5 Sv achievable at 0.25-deg resolution | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# ocean_circulation/benchmark_gyre.yaml
spec_ref: sha256:<spec419_hash>
principle_ref: sha256:<p419_hash>
dataset:
  name: double_gyre_reference
  reference: "High-resolution MOM6 reference at 1/10 deg"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: MOM6-1deg
    params: {res: 1.0, GM: true}
    results: {transport_err: 8.0, SST_RMSE: 1.5}
  - solver: MOM6-0.25deg
    params: {res: 0.25, GM: false}
    results: {transport_err: 3.5, SST_RMSE: 0.8}
  - solver: NEMO-0.25deg
    params: {res: 0.25}
    results: {transport_err: 4.0, SST_RMSE: 0.9}
quality_scoring:
  - {max_transport_err: 2.0, Q: 1.00}
  - {max_transport_err: 5.0, Q: 0.90}
  - {max_transport_err: 10.0, Q: 0.80}
  - {max_transport_err: 15.0, Q: 0.75}
```

**Baseline solver:** MOM6-0.25deg — transport error 3.5 Sv
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Transport Err (Sv) | SST RMSE (°C) | Runtime | Q |
|--------|-------------------|---------------|---------|---|
| MOM6-1deg | 8.0 | 1.5 | 1 hr | 0.80 |
| NEMO-0.25deg | 4.0 | 0.9 | 24 hr | 0.90 |
| MOM6-0.25deg | 3.5 | 0.8 | 20 hr | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case: 500 × 0.90 = 450 PWM
Floor:     500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p419_hash>",
  "h_s": "sha256:<spec419_hash>",
  "h_b": "sha256:<bench419_hash>",
  "r": {"transport_err": 3.5, "SST_RMSE": 0.8, "ratio": 0.70},
  "c": {"resolution": "0.25deg", "spinup_years": 100, "K": 3},
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
pwm-node benchmarks | grep ocean_circulation
pwm-node verify AF_environmental_science/ocean_circulation_s1_ideal.yaml
pwm-node mine AF_environmental_science/ocean_circulation_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
