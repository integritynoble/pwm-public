# X-ray Phase Contrast — Four-Layer Walkthrough

**Principle #254 · X-ray Phase-Contrast Imaging**
Domain: Electromagnetics & Optics | Carrier: photon (X-ray) | Difficulty: hard (δ=5) | DAG: [K.green.fresnel] --> [∂.space] --> [∫.spatial] --> [F.dft]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Transport of     │→│ Grating / propa- │→│ Simulated phase  │→│ TIE / Talbot /   │
│ intensity, TIE,  │ │ gation-based,    │ │ phantoms, known  │ │ iterative phase  │
│ grating interfer.│ │ S1-S4 scenarios  │ │ δ,β maps         │ │ retrieval solver │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

TIE: −k ∂I/∂z = ∇·(I∇φ) (transport of intensity equation)
Phase shift: φ = −(2π/λ)∫δ(x,y,z)dz
Absorption: I = I₀ exp(−(4π/λ)∫β dz)

### DAG

```
[K.green.fresnel] --> [∂.space] --> [∫.spatial] --> [F.dft]
Fresnel-propagator  spatial-derivative  Talbot-integral  phase-retrieval
```
V={K.green.fresnel,∂.space,∫.spatial,F.dft}  L_DAG=3.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | TIE has solution for I > 0 everywhere |
| Uniqueness | CONDITIONAL | TIE unique up to constant; grating: unique with 3-step |
| Stability | CONDITIONAL | Low-frequency noise amplification in TIE |

Mismatch: source coherence, detector PSF, grating alignment

### Error Method

e = phase RMSE (rad), δ map relative error; q = 2.0

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #254"
omega:
  method: propagation_based
  energy_keV: 20
  pixel_um: 1.0
  distances_mm: [50, 100, 200]
E:
  forward: "TIE: -k*dI/dz = div(I*grad(phi))"
I:
  scenario: S1_ideal
  phantom: Shepp_Logan_phase
O: [phase_RMSE_rad, delta_error_pct, SSIM]
epsilon:
  phase_RMSE_max_rad: 0.1
  SSIM_min: 0.90
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known distances, coherent | None | φ RMSE ≤ 0.1 rad |
| S2 Mismatch | Partial coherence | Source size | φ RMSE ≤ 0.3 rad |
| S3 Oracle | True coherence given | Known σ_src | φ RMSE ≤ 0.15 rad |
| S4 Blind Cal | Estimate coherence | Self-cal | recovery ≥ 80% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: xray_phase_contrast
  cases: 8
  ref: simulated_TIE_phantoms
baselines:
  - solver: TIE_FFT
    phase_RMSE: 0.08
  - solver: iterative_Paganin
    phase_RMSE: 0.05
quality_scoring:
  metric: phase_RMSE_rad
  thresholds:
    - {max: 0.02, Q: 1.00}
    - {max: 0.05, Q: 0.90}
    - {max: 0.10, Q: 0.80}
    - {max: 0.30, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | φ RMSE | Time | Q | Reward |
|--------|--------|------|---|--------|
| TIE_FFT | 0.08 | 1s | 0.80 | 400 PWM |
| iterative_Paganin | 0.05 | 10s | 0.90 | 450 PWM |
| multi_distance_opt | 0.015 | 30s | 1.00 | 500 PWM |

```
R = 100 × 1.0 × 5 × 1.0 × Q = 500 × Q PWM
```

### Certificate

```json
{
  "principle": 254,
  "r": {"residual_norm": 0.015, "error_bound": 0.10, "ratio": 0.15},
  "c": {"resolutions": [128,256,512], "fitted_rate": 2.0, "theoretical_rate": 2.0},
  "Q": 1.00,
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
pwm-node benchmarks | grep xray_phase
pwm-node mine xray_phase/propagation_s1_ideal.yaml
```
