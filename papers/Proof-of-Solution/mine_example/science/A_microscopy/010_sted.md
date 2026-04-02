# Principle #10 — STED Microscopy

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Frontier (δ=5)
**DAG:** G.donut --> N.saturation --> K.psf.airy | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.donut-->N.saturation-->K.psf.airy  STED  STED-Neuro-8  Deconv
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  STED   P = (E, G, W, C)   Principle #10                      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = PSF_STED(r; P_dep) ⊛ f(r) + n                │
│        │ PSF_STED FWHM ≈ λ/(2NA·√(1+P_dep/P_sat))            │
│        │ Depletion beam creates sub-diffraction PSF (~50 nm)   │
│        │ Inverse: deconvolve with STED-PSF (signal-starved)   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.donut] ──→ [N.saturation] ──→ [K.psf.airy]         │
│        │  Source(donut)  Deplete(saturation)  PSF-blur(sub-diff) │
│        │ V={G,N,K}  A={G-->N, N-->K}   L_DAG=4.0              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (sub-diffraction PSF, positive signal)│
│        │ Uniqueness: YES within STED-OTF support               │
│        │ Stability: κ ≈ 60 (moderate depletion);              │
│        │   κ ≈ 200 (high depletion, very few photons)          │
│        │ Mismatch: P_dep fluctuation, donut alignment, bleach  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR, SSIM, resolution_FWHM_nm                   │
│        │ q = 1.5 (RL slow at low photon counts)              │
│        │ T = {residual_norm, fitted_rate, resolution_gain}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | STED-PSF FWHM consistent with P_dep/P_sat and NA | PASS |
| S2 | Sub-diffraction PSF well-posed under sparsity prior | PASS |
| S3 | RL + TV converges for STED low-photon regime | PASS |
| S4 | PSNR ≥ 24 dB achievable; resolution ≤ 60 nm | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# sted/neuro_s1_ideal.yaml
principle_ref: sha256:<p010_hash>
omega:
  grid: [256, 256]
  pixel_nm: 20
  excitation_nm: 635
  depletion_nm: 775
  NA: 1.4
  P_dep_over_P_sat: 10
E:
  forward: "y = PSF_STED(P_dep) ⊛ f + n"
I:
  dataset: STED_Neuro_8
  images: 8
  noise: {type: poisson, peak: 200}
  scenario: ideal
O: [PSNR, SSIM, FWHM_nm]
epsilon:
  PSNR_min: 24.0
  SSIM_min: 0.72
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 20 nm pixel for 50 nm PSF: well-sampled | PASS |
| S2 | 200 photons/px at 50 nm PSF: κ ≈ 80 | PASS |
| S3 | RL + sparsity prior converges within 80 iterations | PASS |
| S4 | PSNR ≥ 24 dB feasible with learned denoiser | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# sted/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec010_hash>
dataset:
  name: STED_Neuro_8
  images: 8
  size: [256, 256]
baselines:
  - solver: RL-STED
    params: {n_iter: 80, reg: TV}
    results: {PSNR: 24.5, SSIM: 0.738}
  - solver: Huygens-STED
    params: {method: CMLE}
    results: {PSNR: 26.2, SSIM: 0.789}
  - solver: STED-DL
    params: {arch: ResUNet}
    results: {PSNR: 29.8, SSIM: 0.891}
quality_scoring:
  - {min: 30.0, Q: 1.00}
  - {min: 27.0, Q: 0.90}
  - {min: 24.0, Q: 0.80}
  - {min: 22.0, Q: 0.75}
```

**Baseline:** RL-STED — PSNR 24.5 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| RL-STED | 24.5 | 0.738 | 10 s | 0.80 |
| Huygens-STED | 26.2 | 0.789 | 20 s | 0.88 |
| STED-DL | 29.8 | 0.891 | 1 s | 0.98 |
| Richardson-Lucy-TV | 25.4 | 0.761 | 15 s | 0.84 |

### Reward Calculation

```
R = 100 × 1.0 × 5 × 1.0 × Q = 500 × Q
Best (STED-DL):  500 × 0.98 = 490 PWM
Floor:           500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p010_hash>",
  "r": {"residual_norm": 0.022, "error_bound": 0.05, "ratio": 0.44},
  "c": {"fitted_rate": 1.42, "theoretical_rate": 1.5, "K": 3},
  "Q": 0.88,
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
| L4 Solution | — | 375–490 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep sted
pwm-node verify sted/neuro_s1_ideal.yaml
pwm-node mine sted/neuro_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
