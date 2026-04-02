# Principle #14 — Expansion Microscopy (ExM)

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Standard (δ=3)
**DAG:** K.psf.airy --> ∫.temporal | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.psf.airy-->∫.temporal  ExM  ExM-Synapse-10  Deconv+Register
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  EXPANSION MICRO  P = (E, G, W, C)   Principle #14            │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = PSF(r) ⊛ f(T(r)/α) + n                       │
│        │ α ≈ 4× expansion factor; T = local deformation field │
│        │ Inverse: deconvolve + correct non-uniform expansion   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.psf.airy] ──→ [∫.temporal]                          │
│        │  PSF-blur(Airy, on expanded sample)  Accumulate        │
│        │ V={K.psf.airy, ∫.temporal}  A={K-->∫}   L_DAG=2.5    │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (expanded sample fits diffraction limit)│
│        │ Uniqueness: YES (known expansion + OTF support)       │
│        │ Stability: κ ≈ 18 (uniform); κ ≈ 70 (distorted)     │
│        │ Mismatch: expansion factor α, distortion field T      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR, SSIM, distortion_error_nm                   │
│        │ q = 2.0 (RL + distortion correction)                │
│        │ T = {residual_norm, fitted_rate, distortion_RMSE}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Expanded pixel size / α consistent with pre-expansion structure | PASS |
| S2 | 4× expansion at NA=1.4 → effective 60 nm resolution: κ ≈ 18 | PASS |
| S3 | RL converges; distortion correction via B-spline registration | PASS |
| S4 | PSNR ≥ 28 dB achievable with distortion correction | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# exm/synapse_s1_ideal.yaml
principle_ref: sha256:<p014_hash>
omega:
  grid: [512, 512]
  pixel_nm: 65
  expansion_factor: 4.0
  effective_resolution_nm: 60
E:
  forward: "y = PSF ⊛ f(T(r)/α) + n"
I:
  dataset: ExM_Synapse_10
  images: 10
  noise: {type: poisson, peak: 3000}
  scenario: ideal
O: [PSNR, SSIM, distortion_RMSE_nm]
epsilon:
  PSNR_min: 28.0
  SSIM_min: 0.80
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 65 nm pixel × 4× expansion: effective 16.25 nm sampling | PASS |
| S2 | High photon count 3000, uniform expansion: κ ≈ 18 | PASS |
| S3 | RL + B-spline converges | PASS |
| S4 | PSNR ≥ 28 dB at 3000 photons/px | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# exm/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec014_hash>
dataset:
  name: ExM_Synapse_10
  images: 10
  size: [512, 512]
baselines:
  - solver: RL+BSpline
    params: {n_iter: 40, bspline_spacing: 32}
    results: {PSNR: 29.1, SSIM: 0.832}
  - solver: ExM-Correct
    params: {method: iterative, n_iter: 60}
    results: {PSNR: 30.8, SSIM: 0.871}
  - solver: DeepExM
    params: {arch: ResUNet}
    results: {PSNR: 33.5, SSIM: 0.928}
quality_scoring:
  - {min: 34.0, Q: 1.00}
  - {min: 31.0, Q: 0.90}
  - {min: 28.0, Q: 0.80}
  - {min: 26.0, Q: 0.75}
```

**Baseline:** RL+BSpline — PSNR 29.1 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| RL+BSpline | 29.1 | 0.832 | 15 s | 0.82 |
| ExM-Correct | 30.8 | 0.871 | 25 s | 0.88 |
| DeepExM | 33.5 | 0.928 | 3 s | 0.98 |
| CARE-ExM | 32.2 | 0.905 | 2 s | 0.92 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q
Best (DeepExM):  300 × 0.98 = 294 PWM
Floor:           300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p014_hash>",
  "r": {"residual_norm": 0.012, "error_bound": 0.03, "ratio": 0.40},
  "c": {"fitted_rate": 1.94, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 225–294 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep expansion
pwm-node verify exm/synapse_s1_ideal.yaml
pwm-node mine exm/synapse_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
