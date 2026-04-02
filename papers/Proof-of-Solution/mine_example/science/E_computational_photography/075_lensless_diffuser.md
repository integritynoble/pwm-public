# Principle #75 — Lensless (Diffuser Camera) Imaging

**Domain:** Computational Photography | **Carrier:** Photon | **Difficulty:** Hard (δ=5)
**DAG:** K.psf.caustic --> integral.temporal | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │         K.psf.caustic-->integral.temporal    Lensless    DiffCam-20        ADMM-TV
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LENSLESS DIFFUSER IMAGING   P = (E, G, W, C)   Principle #75   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = [PSF_diff(r) ⊛ x(r)] + n(r)                   │
│        │ PSF_diff = calibrated caustic pattern of diffuser       │
│        │ x = scene irradiance; y = sensor measurement            │
│        │ Inverse: deconvolve x from y using calibrated PSF       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.psf.caustic] --> [integral.temporal]                  │
│        │  DiffuserPSF  Integrate                                 │
│        │ V={K.psf.caustic, integral.temporal}  A={K.psf.caustic-->integral.temporal}   L_DAG=4.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (diffuser PSF has broadband support)    │
│        │ Uniqueness: YES within PSF bandwidth                    │
│        │ Stability: κ ≈ 25 (well-calibrated), κ ≈ 200 (poor)   │
│        │ Mismatch: PSF calibration drift, depth-dependent PSF    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), SSIM (secondary)                   │
│        │ q = 2.0 (ADMM with TV prior convergence)              │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | PSF calibration grid matches sensor pitch; diffuser coverage spans FOV | PASS |
| S2 | PSF Fourier support non-zero over target bandwidth → bounded inverse | PASS |
| S3 | ADMM-TV converges monotonically under ADMM splitting | PASS |
| S4 | PSNR ≥ 25 dB achievable for well-calibrated diffuser at SNR > 15 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# lensless/diffcam_s1_ideal.yaml
principle_ref: sha256:<p075_hash>
omega:
  grid: [512, 512]
  pixel_um: 3.45
  diffuser_type: pseudo-random
  wavelength_nm: 550
E:
  forward: "y = PSF_diff ⊛ x + n"
  PSF: "Calibrated caustic, random phase mask"
I:
  dataset: DiffCam_20
  images: 20
  noise: {type: gaussian, sigma: 0.02}
  scenario: ideal
O: [PSNR, SSIM]
epsilon:
  PSNR_min: 25.0
  SSIM_min: 0.78
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 512×512 at 3.45 μm; PSF calibrated at same pitch | PASS |
| S2 | κ ≈ 25 within well-posed regime for σ=0.02 | PASS |
| S3 | ADMM-TV converges within 200 iterations | PASS |
| S4 | PSNR ≥ 25 dB feasible for Gaussian σ=0.02 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# lensless/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec075_hash>
principle_ref: sha256:<p075_hash>
dataset:
  name: DiffCam_20
  images: 20
  size: [512, 512]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Wiener
    params: {lambda: 0.01}
    results: {PSNR: 22.1, SSIM: 0.68}
  - solver: ADMM-TV
    params: {n_iter: 200, tau: 0.001}
    results: {PSNR: 26.3, SSIM: 0.81}
  - solver: U-Net-Lensless
    params: {pretrained: true}
    results: {PSNR: 30.2, SSIM: 0.90}
quality_scoring:
  - {min: 30.0, Q: 1.00}
  - {min: 27.0, Q: 0.90}
  - {min: 25.0, Q: 0.80}
  - {min: 22.0, Q: 0.75}
```

**Baseline solver:** ADMM-TV — PSNR 26.3 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| Wiener | 22.1 | 0.68 | 0.05 s | 0.75 |
| ADMM-TV | 26.3 | 0.81 | 5 s | 0.82 |
| U-Net-Lensless | 30.2 | 0.90 | 0.8 s | 0.97 |
| FlatNet | 28.8 | 0.87 | 1.2 s | 0.92 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (U-Net-Lensless): 500 × 0.97 = 485 PWM
Floor:                      500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p075_hash>",
  "h_s": "sha256:<spec075_hash>",
  "h_b": "sha256:<bench075_hash>",
  "r": {"residual_norm": 0.012, "error_bound": 0.03, "ratio": 0.40},
  "c": {"fitted_rate": 1.92, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.97,
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
| L4 Solution | — | 375–485 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep lensless
pwm-node verify lensless/diffcam_s1_ideal.yaml
pwm-node mine lensless/diffcam_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
