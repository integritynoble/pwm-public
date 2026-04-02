# Principle #49 — Fundus Camera

**Domain:** Medical Imaging | **Carrier:** Photon | **Difficulty:** Basic (δ=2)
**DAG:** [G.broadband] --> [K.scatter.surface] --> [S.detector]

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.broadband --> K.scatter.surface --> S.detector      Fundus-enh   RetinaFundus-20   CLAHE
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  FUNDUS CAMERA   P = (E, G, W, C)   Principle #49              │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = I(r)·R(r)·V(r) + n(r)                          │
│        │ I = illumination, R = retinal reflectance, V = vignette│
│        │ Inverse: recover retinal reflectance R from observed   │
│        │ fundus image y, correcting illumination non-uniformity │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.broadband] ──→ [K.scatter.surface] ──→ [S.detector]│
│        │  Illuminate Modulate Convolve Detect                   │
│        │ V={G.broadband,K.scatter.surface,S.detector}  A={G.broadband→K.scatter.surface, K.scatter.surface→S.detector}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (retinal surface always reflective)     │
│        │ Uniqueness: YES (single 2D reflectance map per channel)│
│        │ Stability: κ ≈ 5 (well-illuminated), κ ≈ 20 (poor)    │
│        │ Mismatch: Δ_pupil (dilation), Δ_media (cataract)      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), SSIM (secondary)                  │
│        │ q = 2.0 (direct division convergence)                 │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Sensor resolution and FOV consistent with retinal anatomy | PASS |
| S2 | Illumination model invertible with vignette correction | PASS |
| S3 | CLAHE / Retinex enhancement converges | PASS |
| S4 | PSNR ≥ 30 dB achievable for well-dilated pupil | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# fundus/retina_s1_ideal.yaml
principle_ref: sha256:<p049_hash>
omega:
  grid: [2048, 2048]
  FOV_deg: 45
  channels: 3
  bit_depth: 8
E:
  forward: "y = I·R·V + n"
  correction: "illumination + vignette normalization"
I:
  dataset: RetinaFundus_20
  images: 20
  noise: {type: gaussian, SNR_dB: 35}
  scenario: ideal
O: [PSNR, SSIM]
epsilon:
  PSNR_min: 30.0
  SSIM_min: 0.85
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 2048×2048 at 45° FOV resolves retinal vessels ~100 μm | PASS |
| S2 | κ ≈ 5 within well-posed regime for uniform illumination | PASS |
| S3 | CLAHE enhancement converges | PASS |
| S4 | PSNR ≥ 30 dB feasible at SNR=35 dB | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# fundus/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec049_hash>
principle_ref: sha256:<p049_hash>
dataset:
  name: RetinaFundus_20
  images: 20
  size: [2048, 2048]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: CLAHE
    params: {clip_limit: 2.0, tile_size: 8}
    results: {PSNR: 30.5, SSIM: 0.87}
  - solver: Retinex
    params: {scales: [15, 80, 250]}
    results: {PSNR: 31.2, SSIM: 0.89}
  - solver: DeepFundus
    params: {pretrained: true}
    results: {PSNR: 35.5, SSIM: 0.95}
quality_scoring:
  - {min: 36.0, Q: 1.00}
  - {min: 33.0, Q: 0.90}
  - {min: 30.0, Q: 0.80}
  - {min: 28.0, Q: 0.75}
```

**Baseline solver:** CLAHE — PSNR 30.5 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| CLAHE | 30.5 | 0.87 | 0.1 s | 0.80 |
| Retinex | 31.2 | 0.89 | 0.3 s | 0.83 |
| DeepFundus (learned) | 35.5 | 0.95 | 0.5 s | 0.98 |
| FundusGAN | 36.2 | 0.96 | 0.8 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (FundusGAN):  200 × 1.00 = 200 PWM
Floor:                  200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p049_hash>",
  "h_s": "sha256:<spec049_hash>",
  "h_b": "sha256:<bench049_hash>",
  "r": {"residual_norm": 0.008, "error_bound": 0.02, "ratio": 0.40},
  "c": {"fitted_rate": 1.98, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 150–200 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep fundus
pwm-node verify fundus/retina_s1_ideal.yaml
pwm-node mine fundus/retina_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
