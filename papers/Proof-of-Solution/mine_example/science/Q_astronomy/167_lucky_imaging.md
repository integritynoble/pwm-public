# Principle #167 — Lucky Imaging

**Domain:** Astronomy | **Carrier:** Photon | **Difficulty:** Research (δ=2)
**DAG:** K.psf --> S.temporal --> integral.spatial | **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.psf-->S.temporal-->integral.spatial    Lucky       LuckyStar-12      Select+Stack
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LUCKY IMAGING   P = (E, G, W, C)   Principle #167              │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y_k(r) = [PSF_atm_k(r) ⊛ f(r)] + n_k(r)              │
│        │ PSF_atm varies frame-to-frame; select best Strehl      │
│        │ fraction (top ~1-10%) and shift-and-add                 │
│        │ Inverse: quality selection → register → stack → deconv  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.psf] --> [S.temporal] --> [integral.spatial]          │
│        │  AtmPSF  FrameSelect  ShiftAndAdd                      │
│        │ V={K.psf, S.temporal, integral.spatial}  A={K.psf-->S.temporal, S.temporal-->integral.spatial}   L_DAG=1.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (turbulence statistics guarantee lucky   │
│        │   frames with Strehl > threshold)                       │
│        │ Uniqueness: YES after shift-and-add registration        │
│        │ Stability: κ ≈ 10 (good seeing), κ ≈ 25 (poor seeing) │
│        │ Mismatch: anisoplanatism, tip-tilt residuals            │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = FWHM (arcsec), Strehl ratio, PSNR                  │
│        │ q = 0.5 (√N stacking improvement)                    │
│        │ T = {FWHM_arcsec, Strehl, PSNR, selection_pct}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Frame rate > 10 Hz; exposure < r₀/v_wind; D/r₀ ≤ 10 | PASS |
| S2 | Selection of top 1–10% yields near-diffraction Strehl | PASS |
| S3 | Shift-and-add stack converges as √N_selected | PASS |
| S4 | FWHM ≤ 0.15″ at 800 nm on 2.5 m telescope achievable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# lucky_imaging/luckystar_s1_ideal.yaml
principle_ref: sha256:<p167_hash>
omega:
  grid: [512, 512]
  pixel_arcsec: 0.035
  wavelength_nm: 800
  telescope_m: 2.5
  D_r0: 6.0
  exposure_ms: 30
  N_frames: 10000
  selection_pct: 5
E:
  forward: "y_k = PSF_atm_k ⊛ f + n_k"
  selection: "Strehl-ranked top 5%"
I:
  dataset: LuckyStar_12
  targets: 12
  noise: {type: poisson, read_noise_e: 1.0}
  scenario: ideal
O: [FWHM_arcsec, Strehl, PSNR]
epsilon:
  FWHM_max_arcsec: 0.15
  Strehl_min: 0.10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 30 ms exposure, D/r₀=6: frozen turbulence regime | PASS |
| S2 | Top 5% of 10k frames: ~500 frames, Strehl ~0.12 | PASS |
| S3 | Stack of 500 frames: SNR × √500 improvement | PASS |
| S4 | FWHM ≤ 0.15″ at 800 nm feasible with 2.5 m | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# lucky_imaging/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec167_hash>
dataset:
  name: LuckyStar_12
  targets: 12
  frames: 10000
baselines:
  - solver: Shift-and-Add
    params: {selection: 5pct, registration: centroid}
    results: {FWHM: 0.12, Strehl: 0.11, PSNR: 28.5}
  - solver: Drizzle-Lucky
    params: {selection: 5pct, drizzle_factor: 2}
    results: {FWHM: 0.10, Strehl: 0.14, PSNR: 30.8}
  - solver: DL-LuckyNet
    params: {arch: MultiFrameUNet, pretrained: true}
    results: {FWHM: 0.07, Strehl: 0.22, PSNR: 34.2}
quality_scoring:
  - {min: 34.0, Q: 1.00}
  - {min: 30.0, Q: 0.90}
  - {min: 28.0, Q: 0.80}
  - {min: 25.0, Q: 0.75}
```

**Baseline:** Shift-and-Add — PSNR 28.5 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | FWHM (″) | Strehl | PSNR (dB) | Q |
|--------|----------|--------|-----------|---|
| Shift-and-Add | 0.12 | 0.11 | 28.5 | 0.80 |
| Drizzle-Lucky | 0.10 | 0.14 | 30.8 | 0.90 |
| DL-LuckyNet | 0.07 | 0.22 | 34.2 | 1.00 |
| Speckle-Holography | 0.09 | 0.16 | 31.5 | 0.92 |

### Reward Calculation

```
R = 100 × 1.0 × 2 × 1.0 × Q = 200 × Q
Best (DL-LuckyNet):  200 × 1.00 = 200 PWM
Floor:               200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p167_hash>",
  "h_s": "sha256:<spec167_hash>",
  "h_b": "sha256:<bench167_hash>",
  "r": {"residual_norm": 0.008, "error_bound": 0.02, "ratio": 0.40},
  "c": {"fitted_rate": 0.48, "theoretical_rate": 0.5, "K": 4},
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
| L4 Solution | — | 150–200 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep lucky_imaging
pwm-node verify lucky_imaging/luckystar_s1_ideal.yaml
pwm-node mine lucky_imaging/luckystar_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
