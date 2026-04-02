# Principle #164 — Near-field Scanning Optical Microscopy (NSOM)

**Domain:** Scanning Probe | **Carrier:** Photon (evanescent) | **Difficulty:** Advanced (δ=3)
**DAG:** K.psf --> S.raster --> integral.temporal | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.psf-->S.raster-->integral.temporal    NSOM        NSOMNano-8        Deconv+Map
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  NSOM   P = (E, G, W, C)   Principle #164                       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = ∫ E_near(r,r')·χ(r') dr' + n(r)                │
│        │ E_near = evanescent field from sub-λ aperture/tip      │
│        │ Resolution ≈ aperture diameter a ≪ λ (not diffraction) │
│        │ Inverse: deconvolve near-field PSF to recover χ(r)     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.psf] --> [S.raster] --> [integral.temporal]           │
│        │  NearFieldCoupling  RasterScan  PhotonCount            │
│        │ V={K.psf, S.raster, integral.temporal}  A={K.psf-->S.raster, S.raster-->integral.temporal}   L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (evanescent coupling in near-field)     │
│        │ Uniqueness: YES for tip-sample distance < a/2          │
│        │ Stability: κ ≈ 12 (aperture NSOM), κ ≈ 20 (apertureless)│
│        │ Mismatch: tip-sample distance variation, topographic   │
│        │   cross-talk, far-field background                      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), lateral_res_nm (secondary)         │
│        │ q = 1.5 (near-field deconvolution convergence)       │
│        │ T = {PSNR, lat_res_nm, topo_crosstalk_dB, contrast}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Aperture diameter a < λ/10; tip-sample gap < a | PASS |
| S2 | Near-field PSF bounded for stable gap; κ ≈ 12 | PASS |
| S3 | Deconvolution converges with regularization for near-field kernel | PASS |
| S4 | Resolution ≤ 50 nm at λ = 532 nm achievable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# nsom/nsomnano_s1_ideal.yaml
principle_ref: sha256:<p164_hash>
omega:
  grid: [256, 256]
  scan_um: [5.0, 5.0]
  pixel_nm: 19.5
  aperture_nm: 50
  wavelength_nm: 532
  tip_sample_gap_nm: 10
  mode: aperture_collection
E:
  forward: "y(r) = ∫ E_near(r,r')·χ(r') dr' + n"
  psf: "evanescent, FWHM ≈ aperture diameter"
I:
  dataset: NSOMNano_8
  samples: 8
  noise: {type: poisson, background: 20}
  scenario: ideal
O: [PSNR, lateral_res_nm]
epsilon:
  PSNR_min: 25.0
  lateral_res_max_nm: 50.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 50 nm aperture at 532 nm: a/λ ≈ 0.094, valid near-field | PASS |
| S2 | 10 nm gap < a/2: κ ≈ 12 | PASS |
| S3 | Near-field deconvolution converges with Tikhonov | PASS |
| S4 | PSNR ≥ 25 dB and res ≤ 50 nm feasible | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# nsom/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec164_hash>
dataset:
  name: NSOMNano_8
  samples: 8
  size: [256, 256]
baselines:
  - solver: Raw-NearField
    params: {processing: background_subtract}
    results: {PSNR: 25.5, lat_res: 48}
  - solver: Wiener-NF
    params: {lambda: 0.005}
    results: {PSNR: 28.8, lat_res: 40}
  - solver: DL-NSOMNet
    params: {arch: UNet, pretrained: true}
    results: {PSNR: 32.5, lat_res: 30}
quality_scoring:
  - {min: 32.0, Q: 1.00}
  - {min: 28.0, Q: 0.90}
  - {min: 25.0, Q: 0.80}
  - {min: 22.0, Q: 0.75}
```

**Baseline:** Raw-NearField — PSNR 25.5 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | Lat res (nm) | Runtime | Q |
|--------|-----------|-------------|---------|---|
| Raw-NearField | 25.5 | 48 | 0.1 s | 0.80 |
| Wiener-NF | 28.8 | 40 | 0.3 s | 0.90 |
| DL-NSOMNet | 32.5 | 30 | 0.5 s | 1.00 |
| Lucy-NF | 27.2 | 42 | 1.5 s | 0.85 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q
Best (DL-NSOMNet):  300 × 1.00 = 300 PWM
Floor:              300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p164_hash>",
  "h_s": "sha256:<spec164_hash>",
  "h_b": "sha256:<bench164_hash>",
  "r": {"residual_norm": 0.008, "error_bound": 0.02, "ratio": 0.40},
  "c": {"fitted_rate": 1.45, "theoretical_rate": 1.5, "K": 3},
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
pwm-node benchmarks | grep nsom
pwm-node verify nsom/nsomnano_s1_ideal.yaml
pwm-node mine nsom/nsomnano_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
