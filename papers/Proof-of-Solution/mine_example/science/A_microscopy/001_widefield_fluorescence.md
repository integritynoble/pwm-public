# Principle #1 — Widefield Fluorescence Microscopy

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Textbook (δ=1)
**DAG:** K.psf.airy --> ∫.temporal | **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.psf.airy-->∫.temporal  WF-fluor  FluoCells-10  Deconv
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  WIDEFIELD FLUORESCENCE   P = (E, G, W, C)   Principle #1      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = [PSF(r) ⊛ f(r)] + n(r)                        │
│        │ PSF = Airy disk, NA-dependent; f = fluorophore density │
│        │ Inverse: deconvolve f from blurred noisy snapshot y    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.psf.airy] ──→ [∫.temporal]                          │
│        │  PSF-blur(Airy)   Accumulate(camera)                   │
│        │ V={K.psf.airy, ∫.temporal}  A={K-->∫}   L_DAG=1.0    │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (band-limited PSF, non-zero OTF)       │
│        │ Uniqueness: YES within OTF support                     │
│        │ Stability: κ ≈ 15 (well-sampled), κ ≈ 80 (under-sam.) │
│        │ Mismatch: Δz (defocus), σ_bg (background)             │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), SSIM (secondary)                  │
│        │ q = 2.0 (Richardson-Lucy O(1/k²) convergence)        │
│        │ T = {residual_norm, fitted_rate, K_resolutions}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | PSF dimensions match spatial grid; OTF bandwidth consistent with NA | PASS |
| S2 | OTF non-zero over support → bounded inverse with Wiener filter | PASS |
| S3 | Richardson-Lucy converges monotonically for Poisson noise model | PASS |
| S4 | PSNR ≥ 30 dB achievable for SNR > 20 images | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# widefield/fluocells_s1_ideal.yaml
principle_ref: sha256:<p001_hash>
omega:
  grid: [512, 512]
  pixel_nm: 65
  emission_nm: 525
  NA: 1.4
E:
  forward: "y = PSF ⊛ f + n"
  PSF: "Airy, NA=1.4, λ_em=525 nm, pixel=65 nm"
I:
  dataset: FluoCells_10
  images: 10
  noise: {type: poisson, peak: 1000}
  scenario: ideal
O: [PSNR, SSIM]
epsilon:
  PSNR_min: 30.0
  SSIM_min: 0.85
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid 512×512 at 65 nm satisfies Nyquist for NA=1.4, λ=525 nm | PASS |
| S2 | κ ≈ 15 within well-posed regime | PASS |
| S3 | Richardson-Lucy converges for Poisson model at these parameters | PASS |
| S4 | PSNR ≥ 30 dB feasible for peak=1000 photons | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# widefield/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec001_hash>
principle_ref: sha256:<p001_hash>
dataset:
  name: FluoCells_10
  images: 10
  size: [512, 512]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Richardson-Lucy
    params: {n_iter: 50}
    results: {PSNR: 31.2, SSIM: 0.872}
  - solver: Wiener
    params: {lambda: 0.001}
    results: {PSNR: 30.5, SSIM: 0.854}
  - solver: CARE-UNet
    params: {pretrained: true}
    results: {PSNR: 35.8, SSIM: 0.941}
quality_scoring:
  - {min: 36.0, Q: 1.00}
  - {min: 33.0, Q: 0.90}
  - {min: 30.0, Q: 0.80}
  - {min: 28.0, Q: 0.75}
```

**Baseline solver:** Richardson-Lucy — PSNR 31.2 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| Wiener | 30.5 | 0.854 | 0.1 s | 0.80 |
| Richardson-Lucy | 31.2 | 0.872 | 2 s | 0.82 |
| CARE-UNet | 35.8 | 0.941 | 0.5 s | 0.98 |
| Noise2Void | 34.1 | 0.918 | 1.2 s | 0.92 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (CARE):  100 × 0.98 = 98 PWM
Floor:             100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p001_hash>",
  "h_s": "sha256:<spec001_hash>",
  "h_b": "sha256:<bench001_hash>",
  "r": {"residual_norm": 0.008, "error_bound": 0.02, "ratio": 0.40},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.98,
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
pwm-node benchmarks | grep widefield
pwm-node verify widefield/fluocells_s1_ideal.yaml
pwm-node mine widefield/fluocells_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
