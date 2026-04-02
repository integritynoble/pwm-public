# Principle #4 — Confocal 3D Z-Stack

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Standard (δ=3)
**DAG:** S.raster --> K.psf.confocal --> ∫.temporal | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.raster-->K.psf.confocal-->∫.temporal  Z-stack  ConfocalZ-12  3D-Deconv
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CONFOCAL Z-STACK   P = (E, G, W, C)   Principle #4            │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(x,y,z) = PSF_3D(x,y,z) ⊛ f(x,y,z) + n            │
│        │ PSF_3D elongated axially (z-res ~ 3× worse than xy)  │
│        │ Inverse: 3D deconvolution to recover isotropic f      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.raster] ──→ [K.psf.confocal] ──→ [∫.temporal]      │
│        │  Scan(3D)     PSF-blur(confocal-3D)  Accumulate        │
│        │ V={S,K,∫}  A={S-->K, K-->∫}   L_DAG=2.5              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (3D OTF has non-zero support)          │
│        │ Uniqueness: YES within 3D OTF bandwidth               │
│        │ Stability: κ ≈ 45 (axial elongation raises κ)        │
│        │ Mismatch: spherical aberration, RI mismatch, Δz step  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR, SSIM, axial_resolution_ratio                │
│        │ q = 2.0 (3D RL convergence)                          │
│        │ T = {residual_norm, fitted_rate, K_resolutions}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | 3D PSF shape [Nx,Ny,Nz] consistent with NA, λ, RI, z-step | PASS |
| S2 | 3D OTF non-zero → bounded inverse with Tikhonov/TV | PASS |
| S3 | 3D RL converges monotonically | PASS |
| S4 | PSNR ≥ 27 dB achievable for typical confocal z-stacks | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# confocal_zstack/s1_ideal.yaml
principle_ref: sha256:<p004_hash>
omega:
  grid: [256, 256, 64]
  pixel_nm: 80
  z_step_nm: 200
  emission_nm: 520
  NA: 1.4
  RI: 1.515
E:
  forward: "y = PSF_3D ⊛ f + n"
I:
  dataset: ConfocalZ_12
  volumes: 12
  noise: {type: poisson_gaussian, peak: 800, sigma: 2.0}
  scenario: ideal
O: [PSNR, SSIM, axial_FWHM_ratio]
epsilon:
  PSNR_min: 27.0
  SSIM_min: 0.78
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Voxel 80×80×200 nm, NA=1.4: axial Nyquist marginal but valid | PASS |
| S2 | κ ≈ 45, spherical aberration bounded for RI=1.515 | PASS |
| S3 | 3D RL converges within 60 iterations | PASS |
| S4 | PSNR ≥ 27 dB feasible at 800 photons/voxel | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# confocal_zstack/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec004_hash>
dataset:
  name: ConfocalZ_12
  volumes: 12
  size: [256, 256, 64]
baselines:
  - solver: RL-3D
    params: {n_iter: 60}
    results: {PSNR: 27.8, SSIM: 0.801}
  - solver: Huygens-MLE
    params: {n_iter: 80, bg: auto}
    results: {PSNR: 29.5, SSIM: 0.845}
  - solver: DL-3DDeconv
    params: {arch: UNet3D}
    results: {PSNR: 32.6, SSIM: 0.912}
quality_scoring:
  - {min: 33.0, Q: 1.00}
  - {min: 30.0, Q: 0.90}
  - {min: 27.0, Q: 0.80}
  - {min: 25.0, Q: 0.75}
```

**Baseline:** RL-3D — PSNR 27.8 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| RL-3D | 27.8 | 0.801 | 30 s | 0.80 |
| Huygens-MLE | 29.5 | 0.845 | 45 s | 0.88 |
| DL-3DDeconv | 32.6 | 0.912 | 5 s | 0.98 |
| CARE-3D | 31.4 | 0.889 | 4 s | 0.94 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q
Best (DL-3DDeconv):  300 × 0.98 = 294 PWM
Floor:               300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p004_hash>",
  "r": {"residual_norm": 0.015, "error_bound": 0.035, "ratio": 0.43},
  "c": {"fitted_rate": 1.91, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 225–294 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep confocal_zstack
pwm-node verify confocal_zstack/s1_ideal.yaml
pwm-node mine confocal_zstack/s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
