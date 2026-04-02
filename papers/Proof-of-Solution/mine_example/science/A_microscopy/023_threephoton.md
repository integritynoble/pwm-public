# Principle #23 — Three-Photon Microscopy

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Frontier (δ=5)
**DAG:** N.pointwise.power --> K.psf.gaussian --> ∫.temporal | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pointwise.power-->K.psf.gaussian-->∫.temporal  3P  3P-Brain-6  Deconv+Scatter
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  THREE-PHOTON MICROSCOPY   P = (E, G, W, C)   Principle #23     │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = PSF_3P(r) ⊛ [f(r) · S₃(z)] + n                │
│        │ PSF_3P ∝ |PSF_exc|⁶ (third-order nonlinear excitation) │
│        │ S₃(z) = depth-dependent scattering at 1300-1700 nm      │
│        │ Inverse: deconvolve + depth-scatter compensation        │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pointwise.power]──→[K.psf.gaussian]──→[∫.temporal]  │
│        │  Nonlinear(I³)    PSF-blur(3P-Gaussian)  Accumulate    │
│        │ V={N,K,∫}  A={N-->K, K-->∫}   L_DAG=4.5              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (inherent 3P sectioning, deeper than 2P)│
│        │ Uniqueness: YES within 3P-PSF support                  │
│        │ Stability: κ ≈ 35 (shallow); κ ≈ 150 (>500 μm depth) │
│        │ Mismatch: scattering μ_s, pulse dispersion, heating    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR, SSIM, depth_penetration_um                   │
│        │ q = 1.5 (RL for very low photon counts at depth)     │
│        │ T = {residual_norm, fitted_rate, max_depth_PSNR}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | 3P-PSF = |PSF_exc|⁶ consistent with λ_exc/3 resolution | PASS |
| S2 | 3P sectioning superior to 2P; κ bounded at moderate depth | PASS |
| S3 | RL + scatter compensation converges for 3P model | PASS |
| S4 | PSNR ≥ 24 dB at depths ≤ 500 μm achievable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# threephoton/brain_s1_ideal.yaml
principle_ref: sha256:<p023_hash>
omega:
  grid: [256, 256, 120]
  pixel_nm: 400
  z_step_um: 2.0
  lambda_exc_nm: 1300
  NA: 1.0
  max_depth_um: 500
E:
  forward: "y = PSF_3P ⊛ (f · S₃) + n"
I:
  dataset: 3P_Brain_6
  volumes: 6
  noise: {type: poisson, peak: 200}
  scenario: ideal
O: [PSNR, SSIM]
epsilon:
  PSNR_min: 24.0
  SSIM_min: 0.72
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 400 nm pixel at NA=1.0, λ/3≈433 nm: adequate sampling | PASS |
| S2 | 200 photons at depth with scatter correction: κ ≈ 80 | PASS |
| S3 | RL + depth-weighting converges within 60 iterations | PASS |
| S4 | PSNR ≥ 24 dB at 200 photons with scatter model | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# threephoton/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec023_hash>
dataset:
  name: 3P_Brain_6
  volumes: 6
  size: [256, 256, 120]
baselines:
  - solver: RL-3P
    params: {n_iter: 60, psf: 3P, scatter: true}
    results: {PSNR: 24.8, SSIM: 0.741}
  - solver: DeepCAD-3P
    params: {pretrained: 3P}
    results: {PSNR: 28.5, SSIM: 0.842}
  - solver: ScatterComp-3P
    params: {n_iter: 50, scatter_order: 3}
    results: {PSNR: 26.2, SSIM: 0.788}
quality_scoring:
  - {min: 29.0, Q: 1.00}
  - {min: 26.0, Q: 0.90}
  - {min: 24.0, Q: 0.80}
  - {min: 22.0, Q: 0.75}
```

**Baseline:** RL-3P — PSNR 24.8 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| RL-3P | 24.8 | 0.741 | 45 s | 0.80 |
| ScatterComp-3P | 26.2 | 0.788 | 60 s | 0.90 |
| DeepCAD-3P | 28.5 | 0.842 | 5 s | 0.96 |
| Self-Sup-3P | 27.1 | 0.812 | 8 s | 0.92 |

### Reward Calculation

```
R = 100 × 1.0 × 5 × 1.0 × Q = 500 × Q
Best (DeepCAD-3P):  500 × 0.96 = 480 PWM
Floor:              500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p023_hash>",
  "h_s": "sha256:<spec023_hash>",
  "h_b": "sha256:<bench023_hash>",
  "r": {"residual_norm": 0.025, "error_bound": 0.05, "ratio": 0.50},
  "c": {"fitted_rate": 1.42, "theoretical_rate": 1.5, "K": 3},
  "Q": 0.90,
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
| L4 Solution | — | 375–480 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep threephoton
pwm-node verify threephoton/brain_s1_ideal.yaml
pwm-node mine threephoton/brain_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
