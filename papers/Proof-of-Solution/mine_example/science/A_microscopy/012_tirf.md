# Principle #12 — TIRF Microscopy

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Textbook (δ=1)
**DAG:** G.evanescent --> K.psf.airy --> ∫.temporal | **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.evanescent-->K.psf.airy-->∫.temporal  TIRF  TIRF-Membrane-10  Deconv
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  TIRF  P = (E, G, W, C)   Principle #12                       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = PSF_TIRF(r) ⊛ [f(r) · exp(-z/d)] + n         │
│        │ d ≈ 100 nm evanescent penetration depth               │
│        │ Inverse: 2D deconvolution (z-sectioned by evanescent) │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.evanescent] ──→ [K.psf.airy] ──→ [∫.temporal]      │
│        │  Source(evanescent)  PSF-blur(Airy)  Accumulate(camera) │
│        │ V={G,K,∫}  A={G-->K, K-->∫}   L_DAG=1.0              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (widefield-like, thin section)         │
│        │ Uniqueness: YES within OTF support                    │
│        │ Stability: κ ≈ 12 (high contrast, low background)    │
│        │ Mismatch: incidence angle θ, penetration depth d      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR, SSIM                                        │
│        │ q = 2.0 (RL convergence, standard)                  │
│        │ T = {residual_norm, fitted_rate, K_resolutions}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | TIRF PSF consistent with high-NA objective, λ, pixel size | PASS |
| S2 | Low background + thin section → κ ≈ 12, well-conditioned | PASS |
| S3 | RL converges rapidly due to high SNR | PASS |
| S4 | PSNR ≥ 32 dB achievable (high SNR regime) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# tirf/membrane_s1_ideal.yaml
principle_ref: sha256:<p012_hash>
omega:
  grid: [512, 512]
  pixel_nm: 65
  emission_nm: 510
  NA: 1.49
  penetration_nm: 100
E:
  forward: "y = PSF_TIRF ⊛ (f · exp(-z/d)) + n"
I:
  dataset: TIRF_Membrane_10
  images: 10
  noise: {type: poisson, peak: 5000}
  scenario: ideal
O: [PSNR, SSIM]
epsilon:
  PSNR_min: 32.0
  SSIM_min: 0.88
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 65 nm pixel at NA=1.49: well-sampled | PASS |
| S2 | High photon count 5000: κ ≈ 12 | PASS |
| S3 | RL converges in < 30 iterations | PASS |
| S4 | PSNR ≥ 32 dB at SNR ~70 | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# tirf/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec012_hash>
dataset:
  name: TIRF_Membrane_10
  images: 10
  size: [512, 512]
baselines:
  - solver: RL
    params: {n_iter: 30}
    results: {PSNR: 33.1, SSIM: 0.901}
  - solver: Wiener
    params: {lambda: 0.0005}
    results: {PSNR: 32.4, SSIM: 0.889}
  - solver: CARE
    params: {pretrained: TIRF}
    results: {PSNR: 37.2, SSIM: 0.958}
quality_scoring:
  - {min: 37.0, Q: 1.00}
  - {min: 35.0, Q: 0.90}
  - {min: 32.0, Q: 0.80}
  - {min: 30.0, Q: 0.75}
```

**Baseline:** RL — PSNR 33.1 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| Wiener | 32.4 | 0.889 | 0.05 s | 0.80 |
| RL | 33.1 | 0.901 | 1 s | 0.82 |
| CARE | 37.2 | 0.958 | 0.3 s | 1.00 |
| Noise2Void | 35.6 | 0.938 | 0.8 s | 0.92 |

### Reward Calculation

```
R = 100 × 1.0 × 1 × 1.0 × Q = 100 × Q
Best (CARE):  100 × 1.00 = 100 PWM
Floor:        100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p012_hash>",
  "r": {"residual_norm": 0.005, "error_bound": 0.015, "ratio": 0.33},
  "c": {"fitted_rate": 1.98, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 75–100 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep tirf
pwm-node verify tirf/membrane_s1_ideal.yaml
pwm-node mine tirf/membrane_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
