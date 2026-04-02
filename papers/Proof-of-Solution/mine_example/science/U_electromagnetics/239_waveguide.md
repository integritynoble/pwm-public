# Waveguide Modes — Four-Layer Walkthrough

**Principle #239 · Electromagnetic Waveguide Mode Analysis**
Domain: Electromagnetics & Optics | Carrier: photon/EM-field | Difficulty: standard (δ=3) | DAG: [∂.space.curl] --> [L.sparse.fem] --> [B.wall]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Eigenvalue eqn,  │→│ Rectangular/circ │→│ Analytical cutoff│→│ FEM eigenvalue / │
│ TE/TM modes,     │ │ waveguide spec, │ │ frequencies, β   │ │ mode-matching    │
│ cutoff, β(ω)     │ │ S1-S4 scenarios │ │ baselines        │ │ solver           │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

(∇²_t + k_c²)ψ = 0 on cross-section S, ψ = 0 (TM) or ∂ψ/∂n = 0 (TE) on ∂S
Propagation constant: β = √(k² − k_c²), cutoff: f_c = k_c·c/(2π)
Dispersion relation: β(ω) = √(ω²με − k_c²)

### DAG

```
[∂.space.curl] --> [L.sparse.fem] --> [B.wall]
curl-eigenvalue  FEM-solve  PEC-wall-BC
```

V={∂.space.curl,L.sparse.fem,B.wall}  L_DAG=3.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Compact self-adjoint operator → discrete spectrum |
| Uniqueness | YES | Eigenvalues are unique; modes orthogonal |
| Stability | YES | Eigenvalues depend continuously on geometry |

Mismatch: cross-section tolerance, dielectric loading, surface roughness

### Error Method

e = relative eigenvalue error |Δk_c²|/|k_c²|, mode field correlation
q = 2.0 (linear FEM), q = 4.0 (quadratic)

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #239"
omega:
  waveguide: rectangular
  a_mm: 22.86  # WR-90
  b_mm: 10.16
  n_modes: 10
E:
  forward: "(nabla_t^2 + kc^2)*psi = 0, BCs on boundary"
I:
  scenario: S1_ideal
  material: vacuum
O: [eigenvalue_error_pct, cutoff_freq_error_pct, mode_correlation]
epsilon:
  eigenvalue_error_max_pct: 0.1
  cutoff_error_max_pct: 0.05
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact rectangular | None | eigen err ≤ 0.1% |
| S2 Mismatch | Rounded corners | Δgeometry | eigen err ≤ 1.0% |
| S3 Oracle | Known corner radius | Given perturbation | eigen err ≤ 0.3% |
| S4 Blind Cal | Estimate geometry from modes | Self-cal | recovery ≥ 90% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: waveguide_modes
  cases: 8  # rectangular, circular, ridged, coaxial
  analytical_ref: closed-form TE/TM for rect and circular
baselines:
  - solver: FEM_eigenvalue_p2
    eigen_err_pct: 0.05
    time_s: 10
  - solver: mode_matching
    eigen_err_pct: 0.01
    time_s: 5
quality_scoring:
  metric: eigenvalue_error_pct
  thresholds:
    - {max: 0.01, Q: 1.00}
    - {max: 0.05, Q: 0.90}
    - {max: 0.10, Q: 0.80}
    - {max: 1.00, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | Eigen err | Time | Q | Reward |
|--------|----------|------|---|--------|
| FEM_p2 | 0.05% | 10s | 0.90 | 270 PWM |
| mode_matching | 0.01% | 5s | 1.00 | 300 PWM |
| spectral_element | 0.005% | 15s | 1.00 | 300 PWM |

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q PWM
```

### Certificate

```json
{
  "principle": 239,
  "r": {"residual_norm": 0.0001, "error_bound": 0.001, "ratio": 0.10},
  "c": {"resolutions": [50,100,200], "fitted_rate": 2.0, "theoretical_rate": 2.0},
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
| L4 Solution | — | 270–300 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep waveguide
pwm-node mine waveguide/wr90_s1_ideal.yaml
```
