# Principle #420 — Sea Ice Modeling

**Domain:** Environmental Science | **Carrier:** ice thickness/concentration | **Difficulty:** Advanced (δ=5)
**DAG:** ∂.time → N.pointwise → ∂.space |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.pointwise→∂.space   sea-ice      Arctic-extent      VP/EVP
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SEA ICE MODELING               P = (E,G,W,C)   Principle #420 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂h/∂t + ∇·(hu) = S_h        (thickness)              │
│        │ ∂A/∂t + ∇·(Au) = S_A        (concentration)           │
│        │ m ∂u/∂t = τ_a + τ_w − mfk×u − mg∇η + ∇·σ (momentum)│
│        │ σ = viscous-plastic rheology (Hibler 1979)             │
│        │ Forward: given forcing → h, A, u over ice domain      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [N.pointwise] ──→ [∂.space]               │
│        │ derivative  nonlinear  derivative                      │
│        │ V={∂.time, N.pointwise, ∂.space}  A={∂.time→N.pointwise, N.pointwise→∂.space}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (coupled PDE system with VP rheology)   │
│        │ Uniqueness: conditional (VP solver may have mult. sols)│
│        │ Stability: EVP subcycling stabilizes VP; CFL on advect│
│        │ Mismatch: rheology choice (VP vs EAP), albedo feedback │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ice extent error (10⁶ km²) or thickness RMSE (m)  │
│        │ q = resolution-dependent                              │
│        │ T = {extent_error, thickness_RMSE, drift_error}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Ice thickness, concentration, stress tensor dimensions consistent | PASS |
| S2 | VP rheology with EVP subcycling well-posed | PASS |
| S3 | EVP solver converges within subcycling iterations | PASS |
| S4 | Ice extent and thickness computable against satellite observations | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# sea_ice/arctic_s1_ideal.yaml
principle_ref: sha256:<p420_hash>
omega:
  grid: [360, 180]
  domain: Arctic_polar_stereographic
  time: [0, 365]   # days (1 year)
  dt: 3600   # s
E:
  forward: "Ice dynamics (VP/EVP) + thermodynamics (Bitz-Lipscomb)"
  rheology: EVP
  ice_categories: 5
B:
  forcing: {atm: ERA5, ocean: PHC_climatology}
  initial: {h: satellite_Oct1, A: satellite_Oct1}
I:
  scenario: Arctic_annual_cycle
  resolutions: [1.0, 0.5, 0.25]   # degrees
O: [extent_error, thickness_RMSE, September_minimum_error]
epsilon:
  extent_error_max: 0.5   # 10⁶ km²
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 5 ice categories resolve thickness distribution; 1-hr timestep | PASS |
| S2 | EVP subcycling converges within 120 iterations | PASS |
| S3 | Annual cycle forced by ERA5 — realistic ice evolution | PASS |
| S4 | Extent error < 0.5×10⁶ km² vs satellite at September minimum | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# sea_ice/benchmark_arctic.yaml
spec_ref: sha256:<spec420_hash>
principle_ref: sha256:<p420_hash>
dataset:
  name: NSIDC_sea_ice_extent
  reference: "NSIDC satellite-derived ice extent (1979-present)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: CICE6-1deg
    params: {categories: 5, EVP: true}
    results: {extent_err: 0.6, h_RMSE: 0.35}
  - solver: CICE6-0.25deg
    params: {categories: 5, EVP: true}
    results: {extent_err: 0.3, h_RMSE: 0.20}
  - solver: SI3-NEMO
    params: {categories: 5}
    results: {extent_err: 0.4, h_RMSE: 0.25}
quality_scoring:
  - {max_extent_err: 0.2, Q: 1.00}
  - {max_extent_err: 0.5, Q: 0.90}
  - {max_extent_err: 1.0, Q: 0.80}
  - {max_extent_err: 2.0, Q: 0.75}
```

**Baseline solver:** CICE6-0.25deg — extent error 0.3×10⁶ km²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Extent Error (10⁶ km²) | h RMSE (m) | Runtime | Q |
|--------|----------------------|-----------|---------|---|
| CICE6-1deg | 0.6 | 0.35 | 1 hr | 0.90 |
| SI3-NEMO | 0.4 | 0.25 | 4 hr | 0.90 |
| CICE6-0.25deg | 0.3 | 0.20 | 12 hr | 0.90 |

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
  "h_p": "sha256:<p420_hash>",
  "h_s": "sha256:<spec420_hash>",
  "h_b": "sha256:<bench420_hash>",
  "r": {"extent_err": 0.3, "h_RMSE": 0.20, "ratio": 0.60},
  "c": {"categories": 5, "annual_cycle": true, "K": 3},
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
pwm-node benchmarks | grep sea_ice
pwm-node verify AF_environmental_science/sea_ice_s1_ideal.yaml
pwm-node mine AF_environmental_science/sea_ice_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
