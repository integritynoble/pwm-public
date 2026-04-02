# Principle #77 — Coded Exposure / Flutter Shutter

**Domain:** Computational Photography | **Carrier:** Photon | **Difficulty:** Hard (δ=5)
**DAG:** L.diag.binary --> K.psf.motion --> integral.temporal | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │         L.diag.binary-->K.psf.motion-->integral.temporal    CodedExp    FlutterShut-15    Wiener-CE
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CODED EXPOSURE / FLUTTER SHUTTER   P = (E, G, W, C)   #77     │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = [h_code(t) ⊛_t x(r,t)] + n(r)                 │
│        │ h_code = binary temporal shutter code                   │
│        │ Motion blur kernel shaped by code → broadband MTF       │
│        │ Inverse: deconvolve motion blur using known code        │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.diag.binary] --> [K.psf.motion] --> [integral.temporal]│
│        │  ShutterCode  MotionBlur  Integrate                     │
│        │ V={L.diag.binary, K.psf.motion, integral.temporal}  A={L.diag.binary-->K.psf.motion, K.psf.motion-->integral.temporal}   L_DAG=4.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (code MTF has no zeros in passband)     │
│        │ Uniqueness: YES for broadband codes (flat spectrum)     │
│        │ Stability: κ ≈ 8 (optimal code), κ ≈ 50 (poor code)   │
│        │ Mismatch: code timing jitter, non-linear motion         │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), SSIM (secondary)                   │
│        │ q = 2.0 (Wiener deconvolution with known code MTF)    │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Code length matches exposure time; MTF bandwidth covers motion range | PASS |
| S2 | Code MTF has no zeros → invertible with Wiener filter | PASS |
| S3 | Wiener deconvolution converges; regularization stabilizes high freq | PASS |
| S4 | PSNR ≥ 28 dB achievable for 52-bit broadband code | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# coded_exposure/flutter_s1_ideal.yaml
principle_ref: sha256:<p077_hash>
omega:
  grid: [640, 480]
  pixel_um: 5.0
  code_bits: 52
  exposure_ms: 40
  motion_px: [0, 30]
E:
  forward: "y = h_code ⊛_t x + n"
  code: "Optimized 52-bit binary sequence (Raskar 2006)"
I:
  dataset: FlutterShut_15
  images: 15
  noise: {type: gaussian, sigma: 0.01}
  scenario: ideal
O: [PSNR, SSIM]
epsilon:
  PSNR_min: 28.0
  SSIM_min: 0.82
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 52-bit code at 40 ms exposure; motion up to 30 px covered | PASS |
| S2 | κ ≈ 8 for optimized broadband code | PASS |
| S3 | Wiener filter converges for σ=0.01 noise level | PASS |
| S4 | PSNR ≥ 28 dB feasible for 30 px motion at σ=0.01 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# coded_exposure/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec077_hash>
principle_ref: sha256:<p077_hash>
dataset:
  name: FlutterShut_15
  images: 15
  size: [640, 480]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Wiener-CE
    params: {lambda: 0.005}
    results: {PSNR: 28.5, SSIM: 0.84}
  - solver: ADMM-L1
    params: {n_iter: 100, tau: 0.001}
    results: {PSNR: 30.2, SSIM: 0.88}
  - solver: DeblurGAN-CE
    params: {pretrained: true}
    results: {PSNR: 33.5, SSIM: 0.93}
quality_scoring:
  - {min: 33.0, Q: 1.00}
  - {min: 30.0, Q: 0.90}
  - {min: 28.0, Q: 0.80}
  - {min: 26.0, Q: 0.75}
```

**Baseline solver:** Wiener-CE — PSNR 28.5 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| Wiener-CE | 28.5 | 0.84 | 0.05 s | 0.80 |
| ADMM-L1 | 30.2 | 0.88 | 3 s | 0.90 |
| DeblurGAN-CE | 33.5 | 0.93 | 0.6 s | 0.98 |
| HyperLaplacian | 29.8 | 0.86 | 1.5 s | 0.87 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (DeblurGAN-CE): 500 × 0.98 = 490 PWM
Floor:                    500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p077_hash>",
  "h_s": "sha256:<spec077_hash>",
  "h_b": "sha256:<bench077_hash>",
  "r": {"residual_norm": 0.009, "error_bound": 0.025, "ratio": 0.36},
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
| L4 Solution | — | 375–490 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep coded_exposure
pwm-node verify coded_exposure/flutter_s1_ideal.yaml
pwm-node mine coded_exposure/flutter_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
