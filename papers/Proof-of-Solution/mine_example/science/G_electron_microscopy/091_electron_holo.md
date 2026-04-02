# Principle #91 — Electron Holography

**Domain:** Electron Microscopy | **Carrier:** Electron | **Difficulty:** Hard (δ=5)
**DAG:** K.green.fresnel --> L.mix --> N.pointwise.abs2 | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │         K.green.fresnel-->L.mix-->N.pointwise.abs2    EH-phase   EH-MagneticDomain  PhaseUnwrap
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ELECTRON HOLOGRAPHY   P = (E, G, W, C)   Principle #91        │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I(r) = 1 + V·cos(2π·q_c·x + Δφ(r)) + n(r)           │
│        │ Off-axis: biprism creates interference fringes          │
│        │ Δφ = phase shift from EM potentials in specimen         │
│        │ Inverse: recover phase φ(r) from hologram I(r)         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.green.fresnel] --> [L.mix] --> [N.pointwise.abs2]     │
│        │  FresnelProp  BiprismMix  ModSq                         │
│        │ V={K.green.fresnel, L.mix, N.pointwise.abs2}  A={K.green.fresnel-->L.mix, L.mix-->N.pointwise.abs2}   L_DAG=4.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (sideband in Fourier space isolable)    │
│        │ Uniqueness: YES for sufficient fringe visibility V>0.1 │
│        │ Stability: κ ≈ 12 (V>0.3), κ ≈ 80 (V<0.1)            │
│        │ Mismatch: biprism voltage error, Fresnel fringes        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = phase RMSE (primary), PSNR (secondary)             │
│        │ q = 2.0 (FFT sideband extraction + filtering)         │
│        │ T = {residual_norm, phase_precision, K_resolutions}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Fringe spacing consistent with biprism voltage; detector resolves fringes | PASS |
| S2 | Sideband isolated in Fourier space → unique phase recovery | PASS |
| S3 | FFT sideband method converges; iterative refinement monotonic | PASS |
| S4 | Phase precision < 0.05 rad achievable at V > 0.2 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# electron_holo/magnetic_s1_ideal.yaml
principle_ref: sha256:<p091_hash>
omega:
  grid: [2048, 2048]
  pixel_nm: 0.5
  fringe_spacing_nm: 3.0
  biprism_V: 200
E:
  forward: "I = 1 + V·cos(2π·q_c·x + Δφ) + n"
  visibility: 0.25
I:
  dataset: EH_MagneticDomain
  holograms: 20
  noise: {type: poisson_gaussian, dose_e_per_A2: 500}
  scenario: ideal
O: [phase_RMSE_rad, PSNR]
epsilon:
  phase_RMSE_max: 0.08
  PSNR_min: 28.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 3 nm fringes at 0.5 nm pixels → 6 px/fringe (Nyquist OK) | PASS |
| S2 | V=0.25 → sideband SNR sufficient; κ ≈ 15 | PASS |
| S3 | FFT sideband + Butterworth filter converges | PASS |
| S4 | Phase RMSE < 0.08 rad feasible at 500 e⁻/Å² | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# electron_holo/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec091_hash>
principle_ref: sha256:<p091_hash>
dataset:
  name: EH_MagneticDomain
  holograms: 20
  size: [2048, 2048]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FFT-Sideband
    params: {mask_radius: 0.3}
    results: {phase_RMSE: 0.065, PSNR: 29.3}
  - solver: Iterative-Holo
    params: {n_iter: 50}
    results: {phase_RMSE: 0.048, PSNR: 31.2}
  - solver: HoloNet
    params: {pretrained: true}
    results: {phase_RMSE: 0.032, PSNR: 33.8}
quality_scoring:
  - {max_RMSE: 0.03, Q: 1.00}
  - {max_RMSE: 0.05, Q: 0.90}
  - {max_RMSE: 0.07, Q: 0.80}
  - {max_RMSE: 0.10, Q: 0.75}
```

**Baseline solver:** FFT-Sideband — phase RMSE 0.065 rad
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Phase RMSE | PSNR (dB) | Runtime | Q |
|--------|------------|-----------|---------|---|
| FFT-Sideband | 0.065 | 29.3 | 1 s | 0.80 |
| Iterative-Holo | 0.048 | 31.2 | 15 s | 0.90 |
| HoloNet | 0.032 | 33.8 | 3 s | 0.97 |
| PhaseFormer | 0.025 | 35.1 | 5 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (PhaseFormer): 500 × 1.00 = 500 PWM
Floor:                   500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p091_hash>",
  "h_s": "sha256:<spec091_hash>",
  "h_b": "sha256:<bench091_hash>",
  "r": {"residual_norm": 0.008, "error_bound": 0.02, "ratio": 0.40},
  "c": {"fitted_rate": 1.97, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.97,
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
| L4 Solution | — | 375–500 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep electron_holo
pwm-node verify electron_holo/magnetic_s1_ideal.yaml
pwm-node mine electron_holo/magnetic_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
