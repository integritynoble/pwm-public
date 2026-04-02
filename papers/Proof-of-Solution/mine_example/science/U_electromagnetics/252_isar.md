# ISAR Imaging — Four-Layer Walkthrough

**Principle #252 · Inverse Synthetic Aperture Radar (ISAR)**
Domain: Electromagnetics & Optics | Carrier: EM-field/microwave | Difficulty: hard (δ=5) | DAG: [∂.space] --> [F.dft] --> [K.green.em] --> [∫.spatial]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Range-Doppler,   │→│ Ship/aircraft    │→│ Simulated ISAR   │→│ RD / polar format│
│ motion compensa- │ │ target config,   │ │ returns, known   │ │ / autofocus      │
│ tion, autofocus  │ │ S1-S4 scenarios  │ │ reflectivity map │ │ solver           │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

s(f,θ) = ∫∫ σ(x,y) exp(−j4πf/c · (x cosθ + y sinθ)) dxdy
Range-Doppler: 2D FFT of phase-history data
Motion compensation: phase correction φ_comp = 4πΔR(θ)/λ

### DAG

```
[∂.space] --> [F.dft] --> [K.green.em] --> [∫.spatial]
range-propagation  FFT  Green-kernel  image-integral
```
V={∂.space,F.dft,K.green.em,∫.spatial}  L_DAG=3.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Fourier inversion exists for sufficient angular coverage |
| Uniqueness | CONDITIONAL | Requires sufficient bandwidth and angular span |
| Stability | CONDITIONAL | Motion errors degrade focus; autofocus needed |

Mismatch: uncompensated motion, phase errors, sidelobe contamination

### Error Method

e = image PSNR, cross-range resolution, entropy metric; q = 2.0

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #252"
omega:
  target: ship_model
  bandwidth_GHz: 2.0
  center_freq_GHz: 10.0
  angular_span_deg: 10
E:
  forward: "s(f,theta) = FFT2D of reflectivity"
  motion_comp: phase_gradient_autofocus
I:
  scenario: S1_ideal
O: [image_PSNR, cross_range_res_m, entropy]
epsilon:
  PSNR_min: 25.0
  cross_range_max_m: 0.5
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Perfect motion comp | None | PSNR ≥ 25 dB |
| S2 Mismatch | Uncompensated motion | Phase errors | PSNR ≥ 18 dB |
| S3 Oracle | True motion given | Known trajectory | PSNR ≥ 23 dB |
| S4 Blind Cal | Autofocus from data | PGA/MCA | recovery ≥ 80% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: isar_imaging
  cases: 8
  ref: simulated_point_scatterers_and_extended
baselines:
  - solver: range_doppler_FFT
    PSNR: 28.0
  - solver: polar_format
    PSNR: 26.5
  - solver: sparse_ISAR
    PSNR: 32.0
quality_scoring:
  metric: image_PSNR
  thresholds:
    - {min: 35.0, Q: 1.00}
    - {min: 30.0, Q: 0.90}
    - {min: 25.0, Q: 0.80}
    - {min: 20.0, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | PSNR | Time | Q | Reward |
|--------|------|------|---|--------|
| RD_FFT | 28 dB | 1s | 0.80 | 400 PWM |
| sparse_ISAR | 32 dB | 60s | 0.90 | 450 PWM |
| deep_autofocus | 36 dB | 30s | 1.00 | 500 PWM |

```
R = 100 × 1.0 × 5 × 1.0 × Q = 500 × Q PWM
```

### Certificate

```json
{
  "principle": 252,
  "r": {"residual_norm": 0.01, "error_bound": 0.05, "ratio": 0.20},
  "c": {"resolutions": [128,256,512], "fitted_rate": 2.0, "theoretical_rate": 2.0},
  "Q": 0.90,
  "gates": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"}
}
```

---

## Reward Summary

| Layer | One-time | Ongoing |
|-------|----------|---------|
| L1 Principle | 200 PWM | 5% of L4 mints |
| L2 spec | 150 PWM × 4 | 10% of L4 mints |
| L3 Benchmark | 100 PWM × 4 | 15% of L4 mints |
| L4 Solution | — | 400–500 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep isar
pwm-node mine isar/ship_s1_ideal.yaml
```
