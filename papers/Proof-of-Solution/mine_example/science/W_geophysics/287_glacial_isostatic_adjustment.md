# Principle #287 — Glacial Isostatic Adjustment (GIA)

**Domain:** Geophysics | **Carrier:** N/A (viscoelastic forward) | **Difficulty:** Hard (δ=5)
**DAG:** ∂.time → N.pointwise → ∫.volume |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.pointwise→∫.volume      gia-sim     sea-level          normal-mode
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  GLACIAL ISOSTATIC ADJUSTMENT     P = (E,G,W,C)   Principle #287│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∇·σ + ρg = 0 (momentum); σ = elastic + viscous creep  │
│        │ u(t) = Σ r_k [1 − exp(−s_k t)] (normal mode expansion)│
│        │ Forward: given ice history + mantle viscosity → uplift  │
│        │ Inverse: given RSL data → constrain η(r) profile       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [N.pointwise] ──→ [∫.volume]              │
│        │ derivative  nonlinear  integrate                       │
│        │ V={∂.time, N.pointwise, ∫.volume}  A={∂.time→N.pointwise, N.pointwise→∫.volume}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear viscoelastic response well-posed)│
│        │ Uniqueness: trade-off between lithosphere and η_LM    │
│        │ Stability: moderately ill-posed; requires RSL data     │
│        │ Mismatch: ice history uncertainty, lateral η variation │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖RSL_pred − RSL_obs‖₂ / ‖RSL_obs‖₂ (relative)    │
│        │ q = 1.0 (1-D η profile), 2.0 (3-D lateral η)         │
│        │ T = {RSL_misfit, uplift_rate, geoid_change}            │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Viscoelastic momentum equation with surface load well-formed | PASS |
| S2 | Normal mode method converges for Maxwell viscoelastic Earth | PASS |
| S3 | SELEN/TABOO reproduce benchmark RSL curves for ICE-5G | PASS |
| S4 | RSL misfit bounded by ice model uncertainty and η resolution | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# gia_sim/sea_level_s1_ideal.yaml
principle_ref: sha256:<p287_hash>
omega:
  SH_degree_max: 256
  domain: global
  time_span: [-120000, 0]  # years BP
  dt: 500  # years
E:
  forward: "normal-mode viscoelastic response to ice loading"
  earth_model: VM5a
  ice_model: ICE-6G_D
  lithosphere_thickness: 96  # km
B:
  surface: ocean_function_time_dependent
  shoreline_migration: true
I:
  scenario: Laurentide_deglaciation
  viscosity_UM: 5e20  # Pa·s
  viscosity_LM: 3e21  # Pa·s
O: [RSL_misfit, present_uplift_rate, geoid_rate]
epsilon:
  RSL_misfit_max: 5.0  # metres
  uplift_rate_error: 0.5  # mm/yr
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | SH degree 256 yields ~80 km resolution; dt=500 yr adequate | PASS |
| S2 | VM5a viscosity profile reproduces Hudson Bay RSL | PASS |
| S3 | SELEN converges in <5 sea-level equation iterations | PASS |
| S4 | RSL misfit < 5 m for Laurentide region with VM5a | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# gia_sim/benchmark_laurentide.yaml
spec_ref: sha256:<spec287_hash>
principle_ref: sha256:<p287_hash>
dataset:
  name: North_American_RSL_database
  reference: "Compiled RSL data for Laurentide (Engelhart & Horton 2012)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: TABOO-1D
    params: {modes: 200, l_max: 128}
    results: {RSL_misfit: 8.5, uplift_error: 0.8}
  - solver: SELEN-2.9
    params: {l_max: 256, iterations: 5}
    results: {RSL_misfit: 4.2, uplift_error: 0.4}
  - solver: VILMA-3D
    params: {lateral_viscosity: true, grid: 50km}
    results: {RSL_misfit: 3.1, uplift_error: 0.3}
quality_scoring:
  - {min_RSL: 2.0, Q: 1.00}
  - {min_RSL: 4.0, Q: 0.90}
  - {min_RSL: 6.0, Q: 0.80}
  - {min_RSL: 10.0, Q: 0.75}
```

**Baseline solver:** SELEN-2.9 — RSL misfit 4.2 m
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | RSL Misfit (m) | Uplift Error (mm/yr) | Runtime | Q |
|--------|----------------|----------------------|---------|---|
| TABOO-1D | 8.5 | 0.8 | 30 s | 0.80 |
| SELEN-2.9 | 4.2 | 0.4 | 300 s | 0.90 |
| VILMA-3D | 3.1 | 0.3 | 3600 s | 0.90 |
| 3D-FE+MCMC | 1.8 | 0.15 | 7200 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (3D-FE): 500 × 1.00 = 500 PWM
Floor:             500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p287_hash>",
  "h_s": "sha256:<spec287_hash>",
  "h_b": "sha256:<bench287_hash>",
  "r": {"residual_norm": 1.8, "error_bound": 5.0, "ratio": 0.36},
  "c": {"fitted_rate": 1.90, "theoretical_rate": 2.0, "K": 4},
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
pwm-node benchmarks | grep gia_sim
pwm-node verify gia_sim/sea_level_s1_ideal.yaml
pwm-node mine gia_sim/sea_level_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
