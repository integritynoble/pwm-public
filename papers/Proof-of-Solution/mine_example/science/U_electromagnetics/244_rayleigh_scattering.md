# Rayleigh Scattering — Four-Layer Walkthrough

**Principle #244 · Rayleigh Scattering**
Domain: Electromagnetics & Optics | Carrier: photon | Difficulty: basic (δ=2) | DAG: [K.scatter.rayleigh] --> [∫.angular]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Dipole approx,   │→│ Sub-λ particle   │→│ Analytical λ⁻⁴   │→│ Rayleigh formula │
│ λ⁻⁴ law, polar-  │ │ ensemble config, │ │ cross-sections   │ │ / DDA solver     │
│ izability tensor │ │ S1-S4 scenarios  │ │ baselines        │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

σ_sca = (8π/3)(2πa/λ)⁴ a² |(m²−1)/(m²+2)|²
Valid for x = 2πa/λ ≪ 1; phase function p(θ) ∝ (1 + cos²θ)

### DAG

```
[K.scatter.rayleigh] --> [∫.angular]
Rayleigh-scattering-kernel  angular-integral
```
V={K.scatter.rayleigh,∫.angular}  L_DAG=1.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Closed-form for x ≪ 1 |
| Uniqueness | YES | Unique dipole response |
| Stability | YES | Smooth in a, m, λ |

Mismatch: size distribution, non-sphericity, multiple scattering

### Error Method

e = relative σ_sca error; q = 4.0 (size-parameter expansion)

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #244"
omega:
  particle: {radius_nm: 20, n: 1.45}
  wavelength_nm: [400, 500, 600, 700]
E:
  forward: "sigma = (8pi/3)*(2pi*a/lam)^4 * a^2 * |(m^2-1)/(m^2+2)|^2"
I:
  scenario: S1_ideal
O: [sigma_error_pct, lambda4_fit_R2]
epsilon:
  sigma_error_max_pct: 0.01
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact Rayleigh | None | σ err ≤ 0.01% |
| S2 Mismatch | Polydispersity σ_a=5nm | Distribution | σ err ≤ 5% |
| S3 Oracle | True distribution given | Known PDF | σ err ≤ 0.5% |
| S4 Blind Cal | Estimate a from λ⁻⁴ fit | Self-cal | recovery ≥ 90% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: rayleigh_scattering
  cases: 8
  analytical_ref: exact_Rayleigh_formula
baselines:
  - solver: Rayleigh_analytic
    sigma_err_pct: 0.0
  - solver: DDA_small
    sigma_err_pct: 0.5
quality_scoring:
  metric: sigma_error_pct
  thresholds:
    - {max: 0.001, Q: 1.00}
    - {max: 0.01, Q: 0.90}
    - {max: 0.1, Q: 0.80}
    - {max: 1.0, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | σ err | Time | Q | Reward |
|--------|-------|------|---|--------|
| Rayleigh_analytic | ~0% | <1ms | 1.00 | 200 PWM |
| DDA_small | 0.5% | 10s | 0.75 | 150 PWM |

```
R = 100 × 1.0 × 2 × 1.0 × Q = 200 × Q PWM
```

### Certificate

```json
{
  "principle": 244,
  "r": {"residual_norm": 1e-10, "error_bound": 1e-4, "ratio": 1e-6},
  "c": {"resolutions": [3,5,10], "fitted_rate": 4.0, "theoretical_rate": 4.0},
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
| L4 Solution | — | 150–200 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep rayleigh
pwm-node mine rayleigh/nanoparticle_s1_ideal.yaml
```
