# Mie Scattering — Four-Layer Walkthrough

**Principle #243 · Mie Scattering Theory**
Domain: Electromagnetics & Optics | Carrier: photon | Difficulty: standard (δ=3) | DAG: [K.scatter.mie] --> [∫.angular]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Vector spherical │→│ Sphere/core-shell│→│ Analytical Mie   │→│ Mie series /     │
│ harmonics, Mie   │ │ particle config, │ │ coefficients,    │ │ T-matrix / DDA   │
│ coefficients     │ │ S1-S4 scenarios  │ │ Q_ext, Q_sca     │ │ solver           │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

Mie coefficients: a_n = [m ψ_n(mx) ψ'_n(x) − ψ_n(x) ψ'_n(mx)] / [m ψ_n(mx) ξ'_n(x) − ξ_n(x) ψ'_n(mx)]
Size parameter: x = 2πa/λ, relative index: m = n_p/n_m
Q_ext = (2/x²) Σ(2n+1) Re(a_n + b_n)

### DAG

```
[K.scatter.mie] --> [∫.angular]
Mie-scattering-kernel  angular-cross-section-integral
```

V={K.scatter.mie,∫.angular}  L_DAG=1.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Mie series converges for all x, m |
| Uniqueness | YES | Spherical harmonic expansion is unique |
| Stability | CONDITIONAL | Large x requires many terms; numerical stability of Bessel functions |

Mismatch: particle size error, refractive index error, non-sphericity

### Error Method

e = relative error in Q_ext, phase function correlation
q = exponential convergence (spectral in n_max)

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #243"
omega:
  particle: dielectric_sphere
  radius_nm: [50, 100, 500, 1000]
  n_particle: 1.5
  n_medium: 1.0
  wavelength_nm: 550
E:
  forward: "Mie series: Q_ext, Q_sca, phase function"
I:
  scenario: S1_ideal
  n_max: auto  # x + 4*x^(1/3) + 2
O: [Q_ext_error, Q_sca_error, phase_fn_correlation]
epsilon:
  Q_ext_error_max: 1e-8
  phase_fn_corr_min: 0.9999
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact sphere | None | Q err ≤ 1e-8 |
| S2 Mismatch | Radius ± 5% | Δa | Q err ≤ 5e-3 |
| S3 Oracle | True a given | Known Δa | Q err ≤ 1e-5 |
| S4 Blind Cal | Estimate a from Q_ext spectrum | Self-cal | recovery ≥ 90% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: mie_scattering
  cases: 12  # small to large x, absorbing, core-shell
  analytical_ref: exact_Mie_series
baselines:
  - solver: Mie_Bohren_Huffman
    Q_ext_err: 1e-12
    time_s: 0.01
  - solver: T_matrix
    Q_ext_err: 1e-6
    time_s: 5
  - solver: DDA
    Q_ext_err: 0.02
    time_s: 120
quality_scoring:
  metric: Q_ext_error
  thresholds:
    - {max: 1e-10, Q: 1.00}
    - {max: 1e-8, Q: 0.90}
    - {max: 1e-5, Q: 0.80}
    - {max: 0.01, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | Q_ext err | Time | Q | Reward |
|--------|----------|------|---|--------|
| Mie_BH | 1e-12 | 0.01s | 1.00 | 300 PWM |
| T_matrix | 1e-6 | 5s | 0.80 | 240 PWM |
| DDA | 0.02 | 120s | 0.75 | 225 PWM |

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q PWM
```

### Certificate

```json
{
  "principle": 243,
  "r": {"residual_norm": 1e-12, "error_bound": 1e-8, "ratio": 1e-4},
  "c": {"resolutions": [10,20,40], "fitted_rate": "exponential", "theoretical_rate": "spectral"},
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
| L4 Solution | — | 225–300 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep mie
pwm-node mine mie/sphere_s1_ideal.yaml
```
