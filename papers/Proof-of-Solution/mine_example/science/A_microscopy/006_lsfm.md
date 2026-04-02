# Principle #6 — Light-Sheet Fluorescence Microscopy (LSFM)

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Standard (δ=3)
**DAG:** G.sheet --> K.psf --> ∫.temporal | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.sheet-->K.psf-->∫.temporal  LSFM  SPIM-Embryo-8  Deconv+Fuse
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LSFM  P = (E, G, W, C)   Principle #6                        │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(x,y,z) = PSF_det(r) ⊛ [S(z) · f(x,y,z)] + n      │
│        │ S(z) = light-sheet profile (Gaussian, ~2-5 μm FWHM)  │
│        │ Inverse: 3D deconvolution with sheet-shaped excitation│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.sheet] ──→ [K.psf] ──→ [∫.temporal]                │
│        │  Source(light-sheet)  PSF-blur(det)  Accumulate(camera) │
│        │ V={G,K,∫}  A={G-->K, K-->∫}   L_DAG=2.5              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (sheet confines excitation)            │
│        │ Uniqueness: YES within detection OTF + sheet support  │
│        │ Stability: κ ≈ 20 (thin sheet); κ ≈ 60 (thick sheet) │
│        │ Mismatch: sheet thickness, sheet tilt, scattering     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR, SSIM, axial_FWHM                           │
│        │ q = 2.0 (3D RL or multi-view fusion)                │
│        │ T = {residual_norm, fitted_rate, K_resolutions}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Sheet thickness + detection NA define 3D PSF consistently | PASS |
| S2 | Thin sheet (2 μm) → κ ≈ 20, well-conditioned | PASS |
| S3 | Multi-view RL converges for dual-view SPIM | PASS |
| S4 | PSNR ≥ 28 dB achievable with multi-view fusion | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# lsfm/embryo_s1_ideal.yaml
principle_ref: sha256:<p006_hash>
omega:
  grid: [512, 512, 200]
  pixel_nm: 406
  z_step_nm: 1000
  sheet_FWHM_um: 3.5
  NA_det: 0.8
E:
  forward: "y = PSF_det ⊛ (S · f) + n"
I:
  dataset: SPIM_Embryo_8
  volumes: 8
  noise: {type: poisson, peak: 3000}
  scenario: ideal
O: [PSNR, SSIM, axial_FWHM_um]
epsilon:
  PSNR_min: 28.0
  SSIM_min: 0.80
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 406 nm pixel at NA=0.8: Nyquist satisfied laterally | PASS |
| S2 | Sheet 3.5 μm, NA_det=0.8: κ ≈ 25 | PASS |
| S3 | RL-3D converges within 40 iterations | PASS |
| S4 | PSNR ≥ 28 dB at 3000 photons | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# lsfm/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec006_hash>
dataset:
  name: SPIM_Embryo_8
  volumes: 8
  size: [512, 512, 200]
baselines:
  - solver: RL-3D
    params: {n_iter: 40}
    results: {PSNR: 28.5, SSIM: 0.812}
  - solver: Multi-View-Fusion
    params: {views: 2, reg: TV}
    results: {PSNR: 31.2, SSIM: 0.878}
  - solver: FlowDec
    params: {method: rl, n_iter: 50}
    results: {PSNR: 29.8, SSIM: 0.851}
quality_scoring:
  - {min: 33.0, Q: 1.00}
  - {min: 30.0, Q: 0.90}
  - {min: 28.0, Q: 0.80}
  - {min: 26.0, Q: 0.75}
```

**Baseline:** RL-3D — PSNR 28.5 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| RL-3D | 28.5 | 0.812 | 25 s | 0.80 |
| Multi-View-Fusion | 31.2 | 0.878 | 40 s | 0.92 |
| FlowDec | 29.8 | 0.851 | 20 s | 0.86 |
| CARE-SPIM | 33.5 | 0.931 | 8 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q
Best (CARE-SPIM):  300 × 1.00 = 300 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p006_hash>",
  "r": {"residual_norm": 0.010, "error_bound": 0.025, "ratio": 0.40},
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
| L4 Solution | — | 225–300 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep lsfm
pwm-node verify lsfm/embryo_s1_ideal.yaml
pwm-node mine lsfm/embryo_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
