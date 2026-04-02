# Principle #149 — Streak Camera Imaging

**Domain:** Ultrafast Imaging | **Carrier:** Photon → Photoelectron | **Difficulty:** Advanced (δ=3)
**DAG:** L.shear.temporal --> S.raster | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.shear.temporal-->S.raster    Streak      StreakSim-12        Deconv
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  STREAK CAMERA IMAGING   P = (E, G, W, C)   Principle #149     │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I(x, t) = h_streak(t) ⊛ f(x, t) + n                  │
│        │ h_streak = temporal impulse response (ps–fs resolution) │
│        │ Slit maps 1D spatial; sweep maps time to 2nd axis      │
│        │ Inverse: deconvolve f(x,t) from streak image           │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.shear.temporal] --> [S.raster]                        │
│        │  TemporalShear  SweepRead                              │
│        │ V={L.shear.temporal, S.raster}  A={L.shear.temporal-->S.raster}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (photocathode conversion always occurs) │
│        │ Uniqueness: YES (1D spatial + time slit unique map)    │
│        │ Stability: κ ≈ 5 (bright sources), κ ≈ 30 (single-shot│
│        │ Mismatch: jitter, space-charge broadening, nonlinearity│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = temporal RMSE ps (primary), SNR (secondary)        │
│        │ q = 2.0 (Wiener deconvolution exact for known IRF)    │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Sweep speed, slit width, and photocathode sensitivity yield consistent x-t map | PASS |
| S2 | IRF FWHM < event duration; Wiener deconvolution bounded | PASS |
| S3 | Wiener/Richardson-Lucy deconvolution converges for known IRF | PASS |
| S4 | Temporal RMSE ≤ 2 ps for 10 ps events at SNR > 20 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# streak_camera/streaksim_s1.yaml
principle_ref: sha256:<p149_hash>
omega:
  spatial_pixels: 512
  temporal_pixels: 512
  temporal_range_ps: 100
  IRF_FWHM_ps: 2.0
  slit_um: 50
E:
  forward: "I(x,t) = h_streak(t) * f(x,t) + n"
  deconv: "Wiener"
I:
  dataset: StreakSim_12
  images: 12
  noise: {type: poisson, peak: 5000}
  scenario: ideal
O: [temporal_RMSE_ps, SNR]
epsilon:
  temporal_RMSE_max: 3.0
  SNR_min: 15.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 100 ps range with 512 pixels gives 0.2 ps/pixel; IRF = 2 ps | PASS |
| S2 | κ ≈ 5 with Wiener regularization at peak 5000 | PASS |
| S3 | Wiener deconvolution converges in single pass | PASS |
| S4 | Temporal RMSE ≤ 3 ps feasible at 5000 counts | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# streak_camera/benchmark_s1.yaml
spec_ref: sha256:<spec149_hash>
principle_ref: sha256:<p149_hash>
dataset:
  name: StreakSim_12
  images: 12
  size: [512, 512]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Gaussian-Fit
    params: {model: multi_gaussian}
    results: {temporal_RMSE_ps: 3.5, SNR: 18}
  - solver: Wiener-Deconv
    params: {lambda: 0.01}
    results: {temporal_RMSE_ps: 2.0, SNR: 22}
  - solver: RL-Deconv
    params: {n_iter: 50}
    results: {temporal_RMSE_ps: 1.5, SNR: 25}
quality_scoring:
  - {max_RMSE: 1.5, Q: 1.00}
  - {max_RMSE: 2.5, Q: 0.90}
  - {max_RMSE: 3.5, Q: 0.80}
  - {max_RMSE: 5.0, Q: 0.75}
```

**Baseline solver:** Wiener-Deconv — temporal RMSE 2.0 ps
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Temporal RMSE (ps) | SNR | Runtime | Q |
|--------|---------------------|-----|---------|---|
| Gaussian-Fit | 3.5 | 18 | 0.5 s | 0.78 |
| Wiener-Deconv | 2.0 | 22 | 0.1 s | 0.90 |
| RL-Deconv | 1.5 | 25 | 2 s | 1.00 |
| DL-Streak (UNet) | 1.2 | 28 | 0.2 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (RL/DL):     300 × 1.00 = 300 PWM
Floor:                 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p149_hash>",
  "h_s": "sha256:<spec149_hash>",
  "h_b": "sha256:<bench149_hash>",
  "r": {"residual_norm": 0.012, "error_bound": 0.03, "ratio": 0.40},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
  "Q": 1.00,
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
pwm-node benchmarks | grep streak_camera
pwm-node verify streak_camera/streaksim_s1.yaml
pwm-node mine streak_camera/streaksim_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
