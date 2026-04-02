# Principle #22 — Spinning Disk Confocal Microscopy

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Textbook (δ=1)
**DAG:** S.raster.disk --> K.psf.confocal --> ∫.temporal | **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.raster.disk-->K.psf.confocal-->∫.temporal  SpinDisk  SD-LiveCell-10  Deconv
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SPINNING DISK CONFOCAL   P = (E, G, W, C)   Principle #22      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = PSF_SD(r) ⊛ f(r) + n(r)                       │
│        │ PSF_SD ≈ PSF_exc · PSF_det (Yokogawa dual-disk)        │
│        │ Pinhole array enables parallel confocal sectioning      │
│        │ Inverse: 3D deconvolution with spinning-disk PSF        │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.raster.disk]──→[K.psf.confocal]──→[∫.temporal]      │
│        │  Sample(Nipkow-disk)  PSF-blur(confocal)  Accumulate   │
│        │ V={S,K,∫}  A={S-->K, K-->∫}   L_DAG=1.0              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (optical sectioning via pinhole array)  │
│        │ Uniqueness: YES within confocal OTF support            │
│        │ Stability: κ ≈ 14 (pinhole cross-talk at depth)       │
│        │ Mismatch: pinhole spacing, cross-talk, disk speed      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR, SSIM                                         │
│        │ q = 2.0 (RL convergence, confocal-like)              │
│        │ T = {residual_norm, fitted_rate, sectioning_ratio}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Pinhole size ≈ 1 Airy unit; disk spacing prevents severe cross-talk | PASS |
| S2 | Confocal OTF with parallel acquisition; κ ≈ 14 | PASS |
| S3 | RL converges for spinning-disk PSF model | PASS |
| S4 | PSNR ≥ 30 dB achievable at moderate photon counts | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# spinning_disk/livecell_s1_ideal.yaml
principle_ref: sha256:<p022_hash>
omega:
  grid: [512, 512, 30]
  pixel_nm: 130
  z_step_nm: 300
  emission_nm: 525
  NA: 1.3
  pinhole_um: 50
  disk_speed_rpm: 5000
E:
  forward: "y = PSF_SD ⊛ f + n"
I:
  dataset: SD_LiveCell_10
  volumes: 10
  noise: {type: poisson, peak: 2000}
  scenario: ideal
O: [PSNR, SSIM]
epsilon:
  PSNR_min: 30.0
  SSIM_min: 0.85
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 130 nm pixel at NA=1.3, λ=525 nm: Nyquist satisfied | PASS |
| S2 | 2000 photons with confocal sectioning: κ ≈ 14 | PASS |
| S3 | RL converges within 40 iterations | PASS |
| S4 | PSNR ≥ 30 dB feasible | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# spinning_disk/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec022_hash>
dataset:
  name: SD_LiveCell_10
  volumes: 10
  size: [512, 512, 30]
baselines:
  - solver: RL-3D
    params: {n_iter: 40, psf: spinning_disk}
    results: {PSNR: 30.8, SSIM: 0.862}
  - solver: Wiener-3D
    params: {lambda: 0.001}
    results: {PSNR: 29.9, SSIM: 0.842}
  - solver: CARE-SD
    params: {arch: 3D-UNet, pretrained: true}
    results: {PSNR: 35.5, SSIM: 0.948}
quality_scoring:
  - {min: 36.0, Q: 1.00}
  - {min: 33.0, Q: 0.90}
  - {min: 30.0, Q: 0.80}
  - {min: 28.0, Q: 0.75}
```

**Baseline:** RL-3D — PSNR 30.8 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| Wiener-3D | 29.9 | 0.842 | 0.5 s | 0.78 |
| RL-3D | 30.8 | 0.862 | 8 s | 0.82 |
| CARE-SD | 35.5 | 0.948 | 1 s | 0.98 |
| Noise2Void | 33.8 | 0.921 | 2 s | 0.92 |

### Reward Calculation

```
R = 100 × 1.0 × 1 × 1.0 × Q = 100 × Q
Best (CARE-SD):  100 × 0.98 = 98 PWM
Floor:           100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p022_hash>",
  "h_s": "sha256:<spec022_hash>",
  "h_b": "sha256:<bench022_hash>",
  "r": {"residual_norm": 0.007, "error_bound": 0.018, "ratio": 0.39},
  "c": {"fitted_rate": 1.96, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep spinning_disk
pwm-node verify spinning_disk/livecell_s1_ideal.yaml
pwm-node mine spinning_disk/livecell_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
