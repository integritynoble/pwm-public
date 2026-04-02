# Principle #19 — Dark-Field Microscopy

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Textbook (δ=1)
**DAG:** K.psf.darkfield --> N.pointwise.abs2 | **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.psf.darkfield-->N.pointwise.abs2  DarkField  DF-Nano-10  Scatter-Inv
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  DARK-FIELD   P = (E, G, W, C)   Principle #19                │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = |U_scat(r)|² + n(r)                           │
│        │ Direct beam blocked; only scattered light detected    │
│        │ U_scat ∝ σ_scat(r) · f(r) (scattering cross-section) │
│        │ Inverse: recover scatterer distribution from intensity│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.psf.darkfield] ──→ [N.pointwise.abs2]              │
│        │  PSF-filter(scatter-only)  Intensity(|·|²)             │
│        │ V={K,N}  A={K-->N}   L_DAG=1.0                       │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (scattered intensity ∝ density²)      │
│        │ Uniqueness: YES up to scattering cross-section        │
│        │ Stability: κ ≈ 10 (high contrast against dark bg)    │
│        │ Mismatch: stray light, condenser alignment, bg level  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR, SSIM, detection_F1                          │
│        │ q = 2.0 (direct intensity model)                    │
│        │ T = {residual_norm, fitted_rate, detection_rate}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Condenser NA_ill > objective NA_det: direct beam excluded | PASS |
| S2 | Scattered intensity linear in density for sparse scatterers | PASS |
| S3 | Background subtraction + thresholding converges | PASS |
| S4 | PSNR ≥ 30 dB for isolated scatterers | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# darkfield/nano_s1_ideal.yaml
principle_ref: sha256:<p019_hash>
omega:
  grid: [512, 512]
  pixel_nm: 100
  wavelength_nm: 550
  NA_det: 0.65
  NA_ill: [0.7, 0.9]
E:
  forward: "y = |U_scat|² + n"
I:
  dataset: DF_Nano_10
  images: 10
  noise: {type: poisson_gaussian, peak: 8000, sigma: 1.0}
  scenario: ideal
O: [PSNR, SSIM, detection_F1]
epsilon:
  PSNR_min: 30.0
  SSIM_min: 0.85
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | NA_ill > NA_det: dark-field condition satisfied | PASS |
| S2 | High contrast on dark background: κ ≈ 10 | PASS |
| S3 | Background subtraction is closed-form | PASS |
| S4 | PSNR ≥ 30 dB at 8000 photons | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# darkfield/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec019_hash>
dataset:
  name: DF_Nano_10
  images: 10
  size: [512, 512]
baselines:
  - solver: BG-Subtract
    params: {method: median_filter}
    results: {PSNR: 31.2, SSIM: 0.874}
  - solver: RL-DF
    params: {n_iter: 20, psf: airy}
    results: {PSNR: 33.5, SSIM: 0.915}
  - solver: DF-DL
    params: {arch: UNet}
    results: {PSNR: 36.8, SSIM: 0.958}
quality_scoring:
  - {min: 37.0, Q: 1.00}
  - {min: 34.0, Q: 0.90}
  - {min: 30.0, Q: 0.80}
  - {min: 28.0, Q: 0.75}
```

**Baseline:** BG-Subtract — PSNR 31.2 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| BG-Subtract | 31.2 | 0.874 | 0.01 s | 0.80 |
| RL-DF | 33.5 | 0.915 | 1 s | 0.88 |
| DF-DL | 36.8 | 0.958 | 0.2 s | 0.98 |
| Wavelet-DF | 34.5 | 0.932 | 0.3 s | 0.92 |

### Reward Calculation

```
R = 100 × 1.0 × 1 × 1.0 × Q = 100 × Q
Best (DF-DL):  100 × 0.98 = 98 PWM
Floor:         100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p019_hash>",
  "r": {"residual_norm": 0.004, "error_bound": 0.012, "ratio": 0.33},
  "c": {"fitted_rate": 1.98, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.92,
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
| L4 Solution | — | 75–98 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep darkfield
pwm-node verify darkfield/nano_s1_ideal.yaml
pwm-node mine darkfield/nano_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
