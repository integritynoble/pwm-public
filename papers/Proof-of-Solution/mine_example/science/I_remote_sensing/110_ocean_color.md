# Principle #110 — Ocean Color Remote Sensing

**Domain:** Remote Sensing | **Carrier:** Photon (VIS) | **Difficulty:** Standard (δ=3)
**DAG:** L.diag.spectral --> K.psf --> integral.spatial | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.diag.spectral-->K.psf-->integral.spatial    OcColor    MODIS-CHL           Retrieval
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  OCEAN COLOR   P = (E, G, W, C)   Principle #110               │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ R_rs(λ) = f(b_b(λ), a(λ)) / Q                        │
│        │ R_rs = remote-sensing reflectance; a = absorption      │
│        │ b_b = backscattering; both f(Chl, CDOM, TSS)           │
│        │ Inverse: retrieve Chl-a concentration from R_rs(λ)    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.diag.spectral] --> [K.psf] --> [integral.spatial]     │
│        │ SpectralBands  AtmTransfer  PixelInteg                  │
│        │ V={L.diag.spectral, K.psf, integral.spatial}  A={L.diag.spectral-->K.psf, K.psf-->integral.spatial}   L_DAG=2.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (R_rs→Chl via band ratios)              │
│        │ Uniqueness: YES for Case-1 waters                       │
│        │ Stability: κ ≈ 10 (open ocean), κ ≈ 60 (coastal)      │
│        │ Mismatch: atmospheric correction error, sun glint       │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = Chl RMSE (primary), bias (secondary)               │
│        │ q = 2.0 (empirical/semi-analytical convergence)       │
│        │ T = {log_RMSE, bias, K_resolutions}                    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Spectral bands cover Chl-a absorption (443, 490, 555 nm) | PASS |
| S2 | Band-ratio algorithm well-conditioned for Case-1 | PASS |
| S3 | OC4 / QAA algorithm converges for calibrated R_rs | PASS |
| S4 | log RMSE < 0.25 achievable for open ocean | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# ocean_color/modis_s1_ideal.yaml
principle_ref: sha256:<p110_hash>
omega:
  grid: [2030, 1354]
  bands: [412, 443, 469, 488, 531, 547, 555, 645, 667, 678]
  pixel_m: 1000
E:
  forward: "R_rs(λ) = f(a(λ), b_b(λ))/Q"
I:
  dataset: MODIS_CHL
  scenes: 60
  noise: {type: gaussian, SNR: 500}
  scenario: ideal
O: [log_RMSE, bias, R_squared]
epsilon:
  log_RMSE_max: 0.25
  R_squared_min: 0.85
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 10 bands covering 412–678 nm; 1 km pixel | PASS |
| S2 | Band-ratio well-conditioned; κ ≈ 10 | PASS |
| S3 | OC4 algorithm converges | PASS |
| S4 | log RMSE < 0.25 feasible for open ocean | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# ocean_color/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec110_hash>
principle_ref: sha256:<p110_hash>
dataset:
  name: MODIS_CHL
  scenes: 60
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: OC4-BandRatio
    results: {log_RMSE: 0.22, R_squared: 0.87}
  - solver: QAA
    results: {log_RMSE: 0.18, R_squared: 0.91}
  - solver: OceanNet
    results: {log_RMSE: 0.12, R_squared: 0.95}
quality_scoring:
  - {max_logRMSE: 0.10, Q: 1.00}
  - {max_logRMSE: 0.18, Q: 0.90}
  - {max_logRMSE: 0.25, Q: 0.80}
  - {max_logRMSE: 0.35, Q: 0.75}
```

**Baseline:** OC4 — log RMSE 0.22 | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | log RMSE | R² | Q |
|--------|----------|----|---|
| OC4 | 0.22 | 0.87 | 0.80 |
| QAA | 0.18 | 0.91 | 0.90 |
| OceanNet | 0.12 | 0.95 | 0.95 |
| OceanFormer | 0.09 | 0.96 | 1.00 |

### Reward: `R = 100 × 3 × q` → Best: 300 PWM | Floor: 225 PWM

```json
{
  "h_p": "sha256:<p110_hash>", "Q": 0.95,
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

## Quick-Start

```bash
pwm-node benchmarks | grep ocean_color
pwm-node mine ocean_color/modis_s1_ideal.yaml
```
