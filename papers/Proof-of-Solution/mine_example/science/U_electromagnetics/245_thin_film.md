# Thin-Film Interference — Four-Layer Walkthrough

**Principle #245 · Thin-Film Multilayer Optics**
Domain: Electromagnetics & Optics | Carrier: photon | Difficulty: standard (δ=3) | DAG: [L.transfer] --> [∫.spectral]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Transfer matrix, │→│ AR/HR coating    │→│ Analytical single│→│ TMM / Rouard /   │
│ Fresnel coeffs,  │ │ stack design,    │ │ layer + measured │ │ characteristic   │
│ multilayer stack  │ │ S1-S4 scenarios │ │ baselines        │ │ matrix solver    │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

Transfer matrix per layer: M_j = [[cos δ_j, −j sin δ_j/η_j],[−jη_j sin δ_j, cos δ_j]]
Phase: δ_j = 2πn_j d_j cos θ_j / λ
Total: M = ∏ M_j, reflectance R = |r|², r = (η₀M₁₁+η₀η_s M₁₂−M₂₁−η_s M₂₂)/(...)

### DAG

```
[L.transfer] --> [∫.spectral]
transfer-matrix-multiply  spectral-integration
```
V={L.transfer,∫.spectral}  L_DAG=1.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Matrix product always defined |
| Uniqueness | YES | Forward model deterministic |
| Stability | YES | Continuous in n_j, d_j |

Mismatch: layer thickness error, refractive index error, angle of incidence

### Error Method

e = spectral reflectance error max|ΔR(λ)|; q = exponential (spectral in n_layers)

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #245"
omega:
  stack: [MgF2, ZnS, MgF2]  # 3-layer AR coating
  thicknesses_nm: [100, 50, 100]
  substrate: BK7
  wavelength_nm: [400, 800, 1]  # range, step
E:
  forward: "M = prod(M_j), R = |r|^2 from boundary conditions"
I:
  scenario: S1_ideal
O: [reflectance_error, transmittance_error]
epsilon:
  R_error_max: 0.001
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact n_j, d_j | None | R err ≤ 0.001 |
| S2 Mismatch | d_j ± 2nm | Δd | R err ≤ 0.02 |
| S3 Oracle | True d_j given | Known Δd | R err ≤ 0.003 |
| S4 Blind Cal | Fit d_j from R(λ) | Self-cal | recovery ≥ 85% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: thin_film_coatings
  cases: 10  # AR, HR, bandpass, notch, dichroic
  analytical_ref: single_layer_exact, Macleod_solutions
baselines:
  - solver: TMM_standard
    R_error: 1e-10
    time_s: 0.01
  - solver: FDTD_thin_film
    R_error: 0.005
    time_s: 60
quality_scoring:
  metric: reflectance_error
  thresholds:
    - {max: 1e-8, Q: 1.00}
    - {max: 1e-4, Q: 0.90}
    - {max: 0.001, Q: 0.80}
    - {max: 0.01, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | R error | Time | Q | Reward |
|--------|---------|------|---|--------|
| TMM_standard | 1e-10 | 0.01s | 1.00 | 300 PWM |
| FDTD_thin_film | 0.005 | 60s | 0.75 | 225 PWM |

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q PWM
```

### Certificate

```json
{
  "principle": 245,
  "r": {"residual_norm": 1e-10, "error_bound": 0.001, "ratio": 1e-7},
  "c": {"resolutions": [3,5,10], "fitted_rate": "exponential"},
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
pwm-node benchmarks | grep thin_film
pwm-node mine thin_film/ar_coating_s1_ideal.yaml
```
