# Fresnel Diffraction — Four-Layer Walkthrough

**Principle #241 · Fresnel Diffraction**
Domain: Electromagnetics & Optics | Carrier: photon | Difficulty: basic (δ=2) | DAG: [K.green.fresnel] --> [∫.spatial]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Fresnel integral,│→│ Aperture + prop  │→│ Analytical slit/ │→│ FFT-based / ASM /│
│ near-field prop, │ │ distance config, │ │ circle solutions │ │ direct integral  │
│ Fresnel number   │ │ S1-S4 scenarios  │ │ baselines        │ │ solver           │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

U(x,y,z) = (1/jλz) ∫∫ U₀(x',y') exp(jπ[(x−x')²+(y−y')²]/(λz)) dx'dy'
Fresnel number: N_F = a²/(λz), where a = aperture half-width
Valid when N_F ~ O(1) (near-field regime)

### DAG

```
[K.green.fresnel] --> [∫.spatial]
Fresnel-propagator  spatial-integration
```

V={K.green.fresnel,∫.spatial}  L_DAG=1.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Convolution integral always exists for L² inputs |
| Uniqueness | YES | Linear propagation is unique |
| Stability | YES | Unitary propagation preserves energy |

Mismatch: propagation distance error, wavelength error, sampling

### Error Method

e = relative intensity error, Fresnel-zone accuracy
q = 2.0 (trapezoidal rule), higher for spectral methods

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #241"
omega:
  aperture: rectangular_slit
  width_mm: 0.5
  wavelength_nm: 632.8
  prop_distance_mm: [10, 50, 200]
E:
  forward: "U(x,z) = (1/jlz) * integral(U0 * exp(j*pi*(x-x')^2/(lz)) dx')"
I:
  scenario: S1_ideal
  sampling: lambda/4
O: [intensity_error_pct, energy_conservation]
epsilon:
  intensity_error_max_pct: 1.0
  energy_conservation: 0.999
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact Fresnel kernel | None | intensity err ≤ 1% |
| S2 Mismatch | Distance ±5% | Δz | intensity err ≤ 5% |
| S3 Oracle | True z given | Known Δz | intensity err ≤ 2% |
| S4 Blind Cal | Estimate z from pattern | Self-cal | recovery ≥ 90% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: fresnel_diffraction
  cases: 8  # slit, circle, square, double-slit
  analytical_ref: Fresnel_integrals_C_S, Lommel_functions
baselines:
  - solver: FFT_Fresnel
    intensity_err_pct: 0.5
    time_s: 0.5
  - solver: ASM
    intensity_err_pct: 0.3
    time_s: 1.0
quality_scoring:
  metric: intensity_error_pct
  thresholds:
    - {max: 0.1, Q: 1.00}
    - {max: 0.3, Q: 0.90}
    - {max: 1.0, Q: 0.80}
    - {max: 3.0, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | Intensity err | Time | Q | Reward |
|--------|--------------|------|---|--------|
| FFT_Fresnel | 0.5% | 0.5s | 0.80 | 160 PWM |
| ASM | 0.3% | 1.0s | 0.90 | 180 PWM |
| spectral_prop | 0.08% | 2.0s | 1.00 | 200 PWM |

```
R = 100 × 1.0 × 2 × 1.0 × Q = 200 × Q PWM
```

### Certificate

```json
{
  "principle": 241,
  "r": {"residual_norm": 0.003, "error_bound": 0.01, "ratio": 0.30},
  "c": {"resolutions": [256,512,1024], "fitted_rate": 2.0, "theoretical_rate": 2.0},
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
| L4 Solution | — | 160–200 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep fresnel
pwm-node mine fresnel/slit_s1_ideal.yaml
```
