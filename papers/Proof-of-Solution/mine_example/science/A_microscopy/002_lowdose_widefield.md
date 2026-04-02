# Principle #2 — Low-Dose Widefield Microscopy

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Standard (δ=3)
**DAG:** K.psf.airy --> ∫.temporal | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.psf.airy-->∫.temporal  LowDose  BioSR-LD-10  Denoise+Deconv
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LOW-DOSE WIDEFIELD   P = (E, G, W, C)   Principle #2          │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = Poisson(α · [PSF ⊛ f](r)) + N(0, σ_read²)    │
│        │ α ≪ 1 (low photon budget); f = fluorophore density    │
│        │ Inverse: joint denoise + deconvolve from ~50 photon/px│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.psf.airy] ──→ [∫.temporal]                          │
│        │  PSF-blur(Airy)   Accumulate(low-count)                │
│        │ V={K.psf.airy, ∫.temporal}  A={K-->∫}   L_DAG=2.5    │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (positive PSF, Poisson likelihood)     │
│        │ Uniqueness: YES under sparsity/TV prior                │
│        │ Stability: κ ≈ 120 (shot-noise-limited)               │
│        │ Mismatch: α (dose), σ_read (read noise), PSF width    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR, SSIM, NRMSE                                 │
│        │ q = 1.5 (Poisson MAP slower convergence)             │
│        │ T = {residual_norm, fitted_rate, K_resolutions}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Poisson noise model dimensionally consistent with photon count α | PASS |
| S2 | Bounded inverse exists under TV/sparsity prior at κ ≈ 120 | PASS |
| S3 | SPIRAL-TAP converges for Poisson + Gaussian model | PASS |
| S4 | PSNR ≥ 25 dB achievable at 50 photons/px with learned prior | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# lowdose/biosr_s1_ideal.yaml
principle_ref: sha256:<p002_hash>
omega:
  grid: [256, 256]
  pixel_nm: 65
  emission_nm: 510
  NA: 1.3
E:
  forward: "y = Poisson(α·PSF⊛f) + N(0,σ²)"
  photon_budget: 50
  read_noise_e: 2.0
I:
  dataset: BioSR_LowDose_10
  images: 10
  noise: {type: poisson_gaussian, alpha: 50, sigma: 2.0}
  scenario: ideal
O: [PSNR, SSIM, NRMSE]
epsilon:
  PSNR_min: 25.0
  SSIM_min: 0.70
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid 256² at 65 nm satisfies Nyquist for NA=1.3 | PASS |
| S2 | 50 photons/px with read noise 2 e⁻: κ ≈ 120, regularizable | PASS |
| S3 | SPIRAL-TAP + BM3D converge at O(1/k^1.5) | PASS |
| S4 | PSNR ≥ 25 dB feasible with learned denoisers | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# lowdose/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec002_hash>
dataset:
  name: BioSR_LowDose_10
  images: 10
  size: [256, 256]
baselines:
  - solver: SPIRAL-TAP
    params: {n_iter: 100, lambda_tv: 0.05}
    results: {PSNR: 25.8, SSIM: 0.712}
  - solver: BM3D+RL
    params: {bm3d_sigma: 25, rl_iter: 30}
    results: {PSNR: 27.3, SSIM: 0.764}
  - solver: Noise2Fast
    params: {epochs: 50}
    results: {PSNR: 30.1, SSIM: 0.856}
quality_scoring:
  - {min: 32.0, Q: 1.00}
  - {min: 28.0, Q: 0.90}
  - {min: 25.0, Q: 0.80}
  - {min: 23.0, Q: 0.75}
```

**Baseline solver:** SPIRAL-TAP — PSNR 25.8 dB
**Layer 3 reward:** 60 PWM + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| SPIRAL-TAP | 25.8 | 0.712 | 8 s | 0.80 |
| BM3D+RL | 27.3 | 0.764 | 5 s | 0.86 |
| Noise2Fast | 30.1 | 0.856 | 3 s | 0.94 |
| HDN (VAE) | 31.5 | 0.892 | 2 s | 0.98 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q
Best (HDN):  300 × 0.98 = 294 PWM
Floor:       300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p002_hash>",
  "r": {"residual_norm": 0.031, "error_bound": 0.06, "ratio": 0.52},
  "c": {"fitted_rate": 1.48, "theoretical_rate": 1.5, "K": 3},
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
pwm-node benchmarks | grep lowdose
pwm-node verify lowdose/biosr_s1_ideal.yaml
pwm-node mine lowdose/biosr_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
