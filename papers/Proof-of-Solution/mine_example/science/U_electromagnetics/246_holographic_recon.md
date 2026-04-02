# Holographic Reconstruction — Four-Layer Walkthrough

**Principle #246 · Holographic Reconstruction**
Domain: Electromagnetics & Optics | Carrier: photon | Difficulty: standard (δ=3) | DAG: [K.green.fresnel] --> [∫.spatial] --> [F.dft]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Interference     │→│ Off-axis / in-   │→│ Simulated holo-  │→│ ASM / convolution│
│ recording, back- │ │ line hologram,   │ │ grams, known     │ │ / phase-shift    │
│ propagation      │ │ S1-S4 scenarios  │ │ objects, baselines│ │ solver           │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

Recording: I(x,y) = |R + O|² = |R|² + |O|² + R*O + RO*
Reconstruction: U_rec(x,y,z) = F⁻¹{F{I · R_ref} · H(f_x,f_y,z)}
Transfer function: H = exp(j2πz√(1/λ² − f_x² − f_y²))

### DAG

```
[K.green.fresnel] --> [∫.spatial] --> [F.dft]
Fresnel-propagator  spatial-integral  spectral-transform
```
V={K.green.fresnel,∫.spatial,F.dft}  L_DAG=3.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Back-propagation always defined |
| Uniqueness | CONDITIONAL | Off-axis: unique sideband; in-line: twin-image problem |
| Stability | YES | Unitary propagation |

Mismatch: reference beam angle, wavelength, propagation distance, aberration

### Error Method

e = amplitude/phase RMSE, SSIM of reconstructed object; q = 2.0

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #246"
omega:
  hologram: off_axis_digital
  pixel_um: 3.45
  sensor: [2048, 2048]
  wavelength_nm: 632.8
  prop_mm: 50.0
E:
  forward: "U_rec = IFFT(FFT(I*R_ref) * H(z))"
I:
  scenario: S1_ideal
O: [amplitude_RMSE, phase_RMSE_rad, SSIM]
epsilon:
  amplitude_RMSE_max: 0.05
  SSIM_min: 0.90
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact λ, z, angle | None | SSIM ≥ 0.90 |
| S2 Mismatch | z ± 0.5mm | Δz | SSIM ≥ 0.75 |
| S3 Oracle | True z given | Known Δz | SSIM ≥ 0.85 |
| S4 Blind Cal | Autofocus from hologram | Self-cal | recovery ≥ 85% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: digital_holography
  cases: 8
  ref: simulated_off_axis_holograms
baselines:
  - solver: ASM_standard
    SSIM: 0.95
  - solver: convolution_method
    SSIM: 0.93
quality_scoring:
  metric: SSIM
  thresholds:
    - {min: 0.98, Q: 1.00}
    - {min: 0.95, Q: 0.90}
    - {min: 0.90, Q: 0.80}
    - {min: 0.80, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | SSIM | Time | Q | Reward |
|--------|------|------|---|--------|
| ASM_standard | 0.95 | 0.5s | 0.90 | 270 PWM |
| convolution | 0.93 | 0.8s | 0.80 | 240 PWM |
| iterative_phase | 0.98 | 5s | 1.00 | 300 PWM |

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q PWM
```

### Certificate

```json
{
  "principle": 246,
  "r": {"residual_norm": 0.02, "error_bound": 0.05, "ratio": 0.40},
  "c": {"resolutions": [512,1024,2048], "fitted_rate": 2.0, "theoretical_rate": 2.0},
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
| L4 Solution | — | 240–300 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep holographic
pwm-node mine holographic/offaxis_s1_ideal.yaml
```
