# Principle #9 — Two-Photon Microscopy

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Standard (δ=3)
**DAG:** N.pointwise.power --> K.psf.gaussian --> ∫.temporal | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pointwise.power-->K.psf.gaussian-->∫.temporal  2P  DeepTissue-10  Deconv+Scatter
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  TWO-PHOTON   P = (E, G, W, C)   Principle #9                 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = [PSF_2P(r) ⊛ f(r)] · S(z) + n                │
│        │ PSF_2P ∝ |PSF_exc|⁴ (nonlinear excitation)           │
│        │ S(z) = depth-dependent scattering attenuation         │
│        │ Inverse: deconvolve + compensate scattering           │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pointwise.power]──→[K.psf.gaussian]──→[∫.temporal]  │
│        │  Nonlinear(I²)    PSF-blur(2P-Gaussian)  Accumulate    │
│        │ V={N,K,∫}  A={N-->K, K-->∫}   L_DAG=2.5              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (inherent optical sectioning)          │
│        │ Uniqueness: YES within 2P-PSF support                 │
│        │ Stability: κ ≈ 25 (shallow); κ ≈ 100 (deep tissue)  │
│        │ Mismatch: scattering coefficient μ_s, aberrations     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR, SSIM                                        │
│        │ q = 2.0 (RL convergence for 2P-PSF)                 │
│        │ T = {residual_norm, fitted_rate, depth_PSNR}          │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | 2P-PSF = |PSF_exc|⁴ dimensionally consistent with λ_exc/2 | PASS |
| S2 | Intrinsic sectioning → no pinhole needed; κ bounded | PASS |
| S3 | RL converges for depth-compensated 2P model | PASS |
| S4 | PSNR ≥ 27 dB at depths ≤ 200 μm | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# twophoton/deeptissue_s1_ideal.yaml
principle_ref: sha256:<p009_hash>
omega:
  grid: [256, 256, 100]
  pixel_nm: 300
  z_step_um: 1.0
  lambda_exc_nm: 920
  NA: 1.0
E:
  forward: "y = PSF_2P ⊛ (f · S) + n"
I:
  dataset: DeepTissue_2P_10
  volumes: 10
  max_depth_um: 200
  noise: {type: poisson, peak: 500}
  scenario: ideal
O: [PSNR, SSIM]
epsilon:
  PSNR_min: 27.0
  SSIM_min: 0.78
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 300 nm pixel at NA=1.0, λ/2=460 nm: Nyquist satisfied | PASS |
| S2 | Depth 200 μm, scatter-compensated: κ ≈ 60 | PASS |
| S3 | RL + depth-weighting converges within 50 iterations | PASS |
| S4 | PSNR ≥ 27 dB at 500 photons with scatter correction | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# twophoton/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec009_hash>
dataset:
  name: DeepTissue_2P_10
  volumes: 10
  size: [256, 256, 100]
baselines:
  - solver: RL-3D
    params: {n_iter: 50, psf: 2P}
    results: {PSNR: 27.6, SSIM: 0.792}
  - solver: DeepCAD
    params: {pretrained: 2P}
    results: {PSNR: 31.2, SSIM: 0.878}
  - solver: ScatterComp-RL
    params: {n_iter: 40, scatter_model: true}
    results: {PSNR: 29.4, SSIM: 0.841}
quality_scoring:
  - {min: 32.0, Q: 1.00}
  - {min: 29.0, Q: 0.90}
  - {min: 27.0, Q: 0.80}
  - {min: 25.0, Q: 0.75}
```

**Baseline:** RL-3D — PSNR 27.6 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| RL-3D | 27.6 | 0.792 | 20 s | 0.80 |
| ScatterComp-RL | 29.4 | 0.841 | 35 s | 0.90 |
| DeepCAD | 31.2 | 0.878 | 3 s | 0.96 |
| SelfSuper2P | 30.5 | 0.862 | 5 s | 0.92 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q
Best (DeepCAD):  300 × 0.96 = 288 PWM
Floor:           300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p009_hash>",
  "r": {"residual_norm": 0.019, "error_bound": 0.04, "ratio": 0.48},
  "c": {"fitted_rate": 1.90, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 225–288 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep twophoton
pwm-node verify twophoton/deeptissue_s1_ideal.yaml
pwm-node mine twophoton/deeptissue_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
