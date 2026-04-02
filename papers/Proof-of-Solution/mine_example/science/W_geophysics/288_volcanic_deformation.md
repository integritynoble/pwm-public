# Principle #288 — Volcanic Deformation (Mogi Model)

**Domain:** Geophysics | **Carrier:** N/A (analytical/numerical) | **Difficulty:** Standard (δ=3)
**DAG:** G.point → K.green → O.l2 |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.point→K.green→O.l2      mogi-inv    InSAR-deform      NLLS
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  VOLCANIC DEFORMATION (MOGI)      P = (E,G,W,C)   Principle #288│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ u_r = (3ΔV/4π) r/(r²+d²)^(3/2)  (radial displacement)│
│        │ u_z = (3ΔV/4π) d/(r²+d²)^(3/2)  (vertical)           │
│        │ ΔV = volume change; d = source depth; r = horiz. dist  │
│        │ Forward: given (x₀,y₀,d,ΔV) → predict surface deform  │
│        │ Inverse: given InSAR/GPS → recover source parameters   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.point] ──→ [K.green] ──→ [O.l2]                     │
│        │ source  kernel  optimize                               │
│        │ V={G.point, K.green, O.l2}  A={G.point→K.green, K.green→O.l2}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (closed-form Mogi solution in half-space)│
│        │ Uniqueness: trade-off between d and ΔV at depth        │
│        │ Stability: well-constrained with near-field data       │
│        │ Mismatch: non-spherical source, topography, heterogeneity│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖u_pred − u_obs‖₂ / ‖u_obs‖₂ (displacement misfit)│
│        │ q = 2.0 (NLLS converges quadratically near minimum)   │
│        │ T = {displacement_RMS, depth_error, volume_error}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Mogi displacement equations dimensionally correct for half-space | PASS |
| S2 | 4 parameters (x₀,y₀,d,ΔV) uniquely determined by >10 data points | PASS |
| S3 | Levenberg-Marquardt converges from reasonable initial guess | PASS |
| S4 | Displacement misfit bounded by noise and source model accuracy | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# mogi_inv/insar_s1_ideal.yaml
principle_ref: sha256:<p288_hash>
omega:
  grid: [100, 100]
  domain: 20km_x_20km
  pixel_size: 200  # metres
E:
  forward: "Mogi point source in elastic half-space"
  parameters: [x0, y0, depth, delta_V]
  Poisson_ratio: 0.25
B:
  surface: flat
  half_space: elastic
I:
  scenario: inflation_episode
  true_params: {x0: 10000, y0: 10000, depth: 5000, dV: 1.0e7}
  noise_std: 0.005  # metres (InSAR LOS)
O: [displacement_RMS, depth_error, dV_error]
epsilon:
  RMS_max: 0.01  # metres
  depth_error_max: 200  # metres
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 10000 InSAR pixels; 4 unknowns massively overdetermined | PASS |
| S2 | Single Mogi source well-constrained by radial symmetry | PASS |
| S3 | LM converges from grid-search initial guess in <20 iterations | PASS |
| S4 | Depth error < 200 m with 5 mm noise | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# mogi_inv/benchmark_inflation.yaml
spec_ref: sha256:<spec288_hash>
principle_ref: sha256:<p288_hash>
dataset:
  name: synthetic_mogi_inflation
  reference: "100×100 InSAR grid, single Mogi source"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Grid-Search
    params: {x_range: [8k,12k], d_range: [2k,8k], steps: 50}
    results: {RMS: 0.008, depth_error: 180}
  - solver: Levenberg-Marquardt
    params: {iterations: 20, init: grid_search_best}
    results: {RMS: 0.005, depth_error: 85}
  - solver: MCMC-Bayesian
    params: {samples: 50000, chains: 4}
    results: {RMS: 0.005, depth_error: 60}
quality_scoring:
  - {min_RMS: 0.003, Q: 1.00}
  - {min_RMS: 0.005, Q: 0.90}
  - {min_RMS: 0.010, Q: 0.80}
  - {min_RMS: 0.020, Q: 0.75}
```

**Baseline solver:** LM — RMS 0.005 m
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | RMS (m) | Depth Error (m) | Runtime | Q |
|--------|---------|-----------------|---------|---|
| Grid-Search | 0.008 | 180 | 10 s | 0.80 |
| LM | 0.005 | 85 | 1 s | 0.90 |
| MCMC | 0.005 | 60 | 120 s | 0.90 |
| FEM-Mogi+MCMC | 0.003 | 25 | 600 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (FEM+MCMC): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p288_hash>",
  "h_s": "sha256:<spec288_hash>",
  "h_b": "sha256:<bench288_hash>",
  "r": {"residual_norm": 0.003, "error_bound": 0.01, "ratio": 0.30},
  "c": {"fitted_rate": 1.98, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep mogi_inv
pwm-node verify mogi_inv/insar_s1_ideal.yaml
pwm-node mine mogi_inv/insar_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
