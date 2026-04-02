# Principle #169 — Solar EUV/X-ray Imaging

**Domain:** Astronomy | **Carrier:** Photon (EUV + X-ray) | **Difficulty:** Research (δ=2)
**DAG:** L.diag.spectral --> K.psf --> integral.temporal | **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.diag.spectral-->K.psf-->integral.temporal    SolEUV      SolarEUV-12       Enhance+Recon
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SOLAR EUV/X-RAY IMAGING   P = (E, G, W, C)   Principle #169    │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r,λ) = ∫ R(T)·DEM(T,r) dT + n(r)                   │
│        │ R(T) = temperature response function per EUV channel    │
│        │ DEM = differential emission measure                     │
│        │ Inverse: recover DEM(T,r) from multi-channel EUV data   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.diag.spectral] --> [K.psf] --> [integral.temporal]    │
│        │  NarrowbandFilter  TelescopePSF  TemporalStack         │
│        │ V={L.diag.spectral, K.psf, integral.temporal}  A={L.diag.spectral-->K.psf, K.psf-->integral.temporal}   L_DAG=1.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (response functions span log T = 5.5–7) │
│        │ Uniqueness: YES with ≥ 6 channels (AIA-like)           │
│        │ Stability: κ ≈ 15 (6 channels), κ ≈ 30 (3 channels)  │
│        │ Mismatch: atomic data uncertainties, multithermal bias  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSE_DEM (primary), χ²_channels (secondary)        │
│        │ q = 2.0 (regularized DEM inversion convergence)      │
│        │ T = {RMSE_DEM, chi2_ch, T_peak_accuracy, EM_loci}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | 6 EUV channels span log T 5.5–7.0; pixel scale consistent | PASS |
| S2 | Response matrix R has rank ≥ 5 → DEM recoverable; κ ≈ 15 | PASS |
| S3 | Tikhonov-regularized DEM converges monotonically | PASS |
| S4 | χ² ≤ 1.5 per channel and DEM RMSE ≤ 10% achievable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# solar_euv/solareuv_s1_ideal.yaml
principle_ref: sha256:<p169_hash>
omega:
  grid: [4096, 4096]
  pixel_arcsec: 0.6
  channels_A: [94, 131, 171, 193, 211, 335]
  instrument: SDO_AIA
  cadence_s: 12
E:
  forward: "y(r,λ) = ∫ R(T)·DEM(T,r) dT + n"
  response: "AIA temperature response functions (CHIANTI v10)"
I:
  dataset: SolarEUV_12
  regions: 12
  noise: {type: poisson, read_noise_DN: 1.2}
  scenario: ideal
O: [RMSE_DEM_pct, chi2_channel]
epsilon:
  RMSE_DEM_max_pct: 10.0
  chi2_max: 1.5
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 6 AIA channels at 0.6″/px; response functions from CHIANTI | PASS |
| S2 | 6 channels → rank 5–6 matrix; κ ≈ 15 | PASS |
| S3 | Regularized inversion converges for typical coronal DEM | PASS |
| S4 | RMSE ≤ 10% and χ² ≤ 1.5 feasible for active regions | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# solar_euv/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec169_hash>
dataset:
  name: SolarEUV_12
  regions: 12
  channels: 6
baselines:
  - solver: EM-Loci
    params: {method: ratio_pairs}
    results: {RMSE_DEM: 15.2, chi2: 2.1}
  - solver: xrt_dem_iterative2
    params: {regularization: L2, lambda: 0.1}
    results: {RMSE_DEM: 8.5, chi2: 1.3}
  - solver: DeepDEM
    params: {arch: MLP, pretrained: true}
    results: {RMSE_DEM: 5.2, chi2: 1.05}
quality_scoring:
  metric: RMSE_DEM_pct
  thresholds:
    - {max: 5.5, Q: 1.00}
    - {max: 8.0, Q: 0.90}
    - {max: 10.0, Q: 0.80}
    - {max: 15.0, Q: 0.75}
```

**Baseline:** EM-Loci — RMSE 15.2% | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | RMSE DEM (%) | χ² | Runtime | Q |
|--------|-------------|-----|---------|---|
| EM-Loci | 15.2 | 2.10 | 0.1 s | 0.75 |
| xrt_dem_iterative2 | 8.5 | 1.30 | 5 s | 0.90 |
| DeepDEM | 5.2 | 1.05 | 0.2 s | 1.00 |
| Sparse-DEM | 7.1 | 1.20 | 3 s | 0.92 |

### Reward Calculation

```
R = 100 × 1.0 × 2 × 1.0 × Q = 200 × Q
Best (DeepDEM):  200 × 1.00 = 200 PWM
Floor:           200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p169_hash>",
  "h_s": "sha256:<spec169_hash>",
  "h_b": "sha256:<bench169_hash>",
  "r": {"residual_norm": 5.2, "error_bound": 10.0, "ratio": 0.52},
  "c": {"fitted_rate": 1.92, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.94,
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
| L4 Solution | — | 150–200 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep solar_euv
pwm-node verify solar_euv/solareuv_s1_ideal.yaml
pwm-node mine solar_euv/solareuv_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
