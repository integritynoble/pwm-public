# Principle #3 — Confocal Live-Cell Microscopy

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Standard (δ=3)
**DAG:** S.raster --> K.psf.confocal --> ∫.temporal | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.raster-->K.psf.confocal-->∫.temporal  Confocal  LiveCell-8  Deconv+Denoise
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CONFOCAL LIVE-CELL   P = (E, G, W, C)   Principle #3          │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = [PSF_conf(r) ⊛ f(r,t)] + n(r)                 │
│        │ PSF_conf ≈ PSF_ill · PSF_det (confocal sectioning)    │
│        │ f(r,t) time-varying; fast acquisition → low SNR       │
│        │ Inverse: deconvolve + denoise time-lapse f(r,t)       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.raster] ──→ [K.psf.confocal] ──→ [∫.temporal]      │
│        │  Scan(point)  PSF-blur(confocal)   Accumulate(PMT)     │
│        │ V={S,K,∫}  A={S-->K, K-->∫}   L_DAG=2.0              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (PSF_conf narrower than widefield)     │
│        │ Uniqueness: YES within confocal OTF support            │
│        │ Stability: κ ≈ 30 (good pinhole), κ ≈ 90 (fast scan) │
│        │ Mismatch: pinhole size, scan speed, photobleaching    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR, SSIM, temporal-SSIM                         │
│        │ q = 2.0 (RL convergence)                             │
│        │ T = {residual_norm, fitted_rate, K_resolutions}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Confocal PSF dimensions consistent with NA, pinhole, λ | PASS |
| S2 | Confocal OTF support wider than widefield → κ bounded | PASS |
| S3 | RL with early stopping converges for time-lapse data | PASS |
| S4 | PSNR ≥ 28 dB achievable with temporal regularization | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# confocal/livecell_s1_ideal.yaml
principle_ref: sha256:<p003_hash>
omega:
  grid: [256, 256, 20]   # 20 time frames
  pixel_nm: 80
  emission_nm: 515
  NA: 1.4
  pinhole_AU: 1.0
E:
  forward: "y(r,t) = PSF_conf ⊛ f(r,t) + n"
I:
  dataset: LiveCell_Confocal_8
  sequences: 8
  frames_per_seq: 20
  noise: {type: poisson_gaussian, peak: 500, sigma: 1.5}
  scenario: ideal
O: [PSNR, SSIM, temporal_SSIM]
epsilon:
  PSNR_min: 28.0
  SSIM_min: 0.80
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 80 nm pixel, NA=1.4, λ=515 nm: Nyquist satisfied | PASS |
| S2 | Pinhole 1 AU → κ ≈ 30, well-conditioned | PASS |
| S3 | RL converges at O(1/k²) for these SNR levels | PASS |
| S4 | PSNR ≥ 28 dB feasible at 500 peak photons | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# confocal/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec003_hash>
dataset:
  name: LiveCell_Confocal_8
  sequences: 8
  size: [256, 256, 20]
baselines:
  - solver: RL-3D
    params: {n_iter: 40}
    results: {PSNR: 28.9, SSIM: 0.821}
  - solver: Huygens
    params: {method: CMLE, n_iter: 50}
    results: {PSNR: 30.4, SSIM: 0.867}
  - solver: CSBDeep
    params: {pretrained: confocal}
    results: {PSNR: 33.7, SSIM: 0.924}
quality_scoring:
  - {min: 34.0, Q: 1.00}
  - {min: 31.0, Q: 0.90}
  - {min: 28.0, Q: 0.80}
  - {min: 26.0, Q: 0.75}
```

**Baseline:** RL-3D — PSNR 28.9 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| RL-3D | 28.9 | 0.821 | 5 s | 0.80 |
| Huygens CMLE | 30.4 | 0.867 | 12 s | 0.88 |
| CSBDeep | 33.7 | 0.924 | 1 s | 0.98 |
| DeepCAD-RT | 32.5 | 0.901 | 0.8 s | 0.94 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q
Best (CSBDeep):  300 × 0.98 = 294 PWM
Floor:           300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p003_hash>",
  "r": {"residual_norm": 0.012, "error_bound": 0.03, "ratio": 0.40},
  "c": {"fitted_rate": 1.93, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep confocal_live
pwm-node verify confocal/livecell_s1_ideal.yaml
pwm-node mine confocal/livecell_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
