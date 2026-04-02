# Principle #143 — Secondary Ion Mass Spectrometry (SIMS) Imaging

**Domain:** Spectroscopy | **Carrier:** Ion | **Difficulty:** Research (δ=5)
**DAG:** G.beam --> K.scatter.inelastic --> S.spectral | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.beam-->K.scatter.inelastic-->S.spectral    SIMS        SIMSSurf-12        Quant
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SIMS IMAGING   P = (E, G, W, C)   Principle #143              │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I_s(m/z, r) = Y(m/z) · C(r) · I_p · α_±(matrix)     │
│        │ Y = sputter yield; α_± = ionisation probability       │
│        │ Matrix effect: α_± varies with local composition       │
│        │ Inverse: quantify C(r) from secondary ion intensities  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.beam] --> [K.scatter.inelastic] --> [S.spectral]      │
│        │  IonBeam  SputterIonize  MassDisperse                  │
│        │ V={G.beam, K.scatter.inelastic, S.spectral}  A={G.beam-->K.scatter.inelastic, K.scatter.inelastic-->S.spectral}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (sputtering always generates sec. ions) │
│        │ Uniqueness: YES (isotope-specific m/z identification)  │
│        │ Stability: κ ≈ 10 (RSF-calibrated), κ ≈ 80 (matrix)   │
│        │ Mismatch: matrix effects, topography, charging         │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = concentration RMSE (primary), spatial res nm (sec.)│
│        │ q = 2.0 (RSF calibration linear)                      │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Primary ion energy, beam size, and mass resolution match target isotopes | PASS |
| S2 | RSF calibration with standards removes matrix effect for single-matrix | PASS |
| S3 | Linear RSF calibration converges; depth profiling steady-state reached | PASS |
| S4 | Concentration RMSE ≤ 10% for implant dose quantification | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# sims_imaging/simssurf_s1.yaml
principle_ref: sha256:<p143_hash>
omega:
  grid: [256, 256]
  pixel_nm: 100
  primary_ion: O2+
  primary_keV: 5.0
  mass_resolution: 5000
  depth_nm_per_frame: 2
E:
  forward: "I_s(m/z, r) = Y * C(r) * I_p * alpha(matrix)"
  calibration: "RSF_implant_standard"
I:
  dataset: SIMSSurf_12
  maps: 12
  noise: {type: poisson, counts_per_pixel: 200}
  scenario: ideal
O: [concentration_RMSE_pct, spatial_res_nm]
epsilon:
  concentration_RMSE_max: 12.0
  spatial_res_max: 200.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | O₂⁺ at 5 keV with m/Δm=5000 resolves isotopic interferences | PASS |
| S2 | RSF calibration with implant standards gives κ ≈ 10 | PASS |
| S3 | Steady-state sputtering reached within 5 nm depth | PASS |
| S4 | RMSE ≤ 12% feasible at 200 counts/pixel | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# sims_imaging/benchmark_s1.yaml
spec_ref: sha256:<spec143_hash>
principle_ref: sha256:<p143_hash>
dataset:
  name: SIMSSurf_12
  maps: 12
  size: [256, 256]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: RSF-Linear
    params: {standards: implant}
    results: {concentration_RMSE_pct: 10.0, spatial_res_nm: 150}
  - solver: MCs+-Correction
    params: {reference: matrix_ion}
    results: {concentration_RMSE_pct: 7.5, spatial_res_nm: 150}
  - solver: ML-SIMS
    params: {model: random_forest, features: multi_ion}
    results: {concentration_RMSE_pct: 5.0, spatial_res_nm: 120}
quality_scoring:
  - {max_RMSE: 5.0, Q: 1.00}
  - {max_RMSE: 8.0, Q: 0.90}
  - {max_RMSE: 12.0, Q: 0.80}
  - {max_RMSE: 18.0, Q: 0.75}
```

**Baseline solver:** MCs⁺-Correction — RMSE 7.5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Conc. RMSE (%) | Spatial res (nm) | Runtime | Q |
|--------|----------------|-------------------|---------|---|
| RSF-Linear | 10.0 | 150 | 1 s | 0.80 |
| MCs⁺-Correction | 7.5 | 150 | 5 s | 0.90 |
| ML-SIMS (RF) | 5.0 | 120 | 10 s | 1.00 |
| DL-SIMS (MultiNet) | 4.5 | 110 | 3 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (ML/DL):     500 × 1.00 = 500 PWM
Floor:                 500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p143_hash>",
  "h_s": "sha256:<spec143_hash>",
  "h_b": "sha256:<bench143_hash>",
  "r": {"residual_norm": 0.045, "error_bound": 0.10, "ratio": 0.45},
  "c": {"fitted_rate": 1.92, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep sims_imaging
pwm-node verify sims_imaging/simssurf_s1.yaml
pwm-node mine sims_imaging/simssurf_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
