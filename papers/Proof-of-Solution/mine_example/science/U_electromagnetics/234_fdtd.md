# FDTD — Four-Layer Walkthrough

**Principle #234 · Finite-Difference Time-Domain**
Domain: Electromagnetics & Optics | Carrier: photon/EM-field | Difficulty: standard (δ=3) | DAG: [∂.time.explicit] --> [∂.space.staggered] --> [B.absorbing]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Yee grid, leapfrog│→│ Pulse in cavity, │→│ Analytical mode  │→│ Yee / ADI-FDTD / │
│ CFL, PML/ABC     │ │ waveguide config │ │ refs, time series│ │ GPU-FDTD solver  │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

∂E/∂t = (1/ε)∇×H − σE/ε,   ∂H/∂t = −(1/μ)∇×E
Yee discretization: staggered grid, leapfrog time-stepping
CFL condition: Δt ≤ Δx/(c√d), d = spatial dimension

### DAG

```
[∂.time.explicit] --> [∂.space.staggered] --> [B.absorbing]
leapfrog-time  Yee-staggered-grid  PML-absorbing
```

V={∂.time.explicit,∂.space.staggered,B.absorbing}  L_DAG=3.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Explicit time-marching, always produces solution |
| Uniqueness | YES | Initial-value problem with unique forward evolution |
| Stability | CONDITIONAL | Requires CFL: Δt ≤ Δx/(c√3) in 3D |

Mismatch: CFL violation, PML reflection, numerical dispersion, staircasing error

### Error Method

e = relative field error, numerical dispersion error per wavelength
q = 2.0 (standard Yee), q = 4.0 (higher-order FDTD)
Convergence via Δx-refinement across K ≥ 3 grids

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #234"
omega:
  domain: [0.1, 0.1, 0.1]  # 10cm³ cavity
  time_ns: 10.0
  grid: [100, 100, 100]
  dt: CFL_limited
E:
  forward: "Yee leapfrog: dE/dt = curl(H)/eps, dH/dt = -curl(E)/mu"
  material: {eps_r: 1.0, mu_r: 1.0, sigma: 0.0}
  boundary: PML_8_layers
I:
  source: {type: gaussian_pulse, center_GHz: 5.0, BW_GHz: 3.0}
  scenario: S1_ideal
O: [relative_field_error, energy_conservation, numerical_dispersion]
epsilon:
  rel_err_max: 0.02
  energy_conservation: 0.999
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact Yee + CFL | None | rel_err ≤ 0.02 |
| S2 Mismatch | Coarse grid (λ/5) | Δx error | rel_err ≤ 0.08 |
| S3 Oracle | Compensated dispersion | Known Δx | rel_err ≤ 0.04 |
| S4 Blind Cal | Adaptive mesh | Auto-refine | recovery ≥ 85% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: fdtd_cavity_3D
  cases: 6
  analytical_ref: resonant_modes_PEC_cavity
baselines:
  - solver: Yee_standard
    rel_err: 0.018
    time_s: 90
  - solver: ADI_FDTD
    rel_err: 0.025
    time_s: 60
quality_scoring:
  metric: relative_field_error
  thresholds:
    - {max: 0.005, Q: 1.00}
    - {max: 0.010, Q: 0.90}
    - {max: 0.020, Q: 0.80}
    - {max: 0.050, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | rel_err | Time | Q | Reward |
|--------|---------|------|---|--------|
| Yee_standard | 0.018 | 90s | 0.80 | 240 PWM |
| ADI_FDTD | 0.025 | 60s | 0.75 | 225 PWM |
| GPU_FDTD_HO | 0.004 | 45s | 1.00 | 300 PWM |

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q PWM
```

### Certificate

```json
{
  "principle": 234,
  "r": {"residual_norm": 0.004, "error_bound": 0.02, "ratio": 0.20},
  "c": {"resolutions": [50,100,200], "fitted_rate": 2.02, "theoretical_rate": 2.0},
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
pwm-node benchmarks | grep fdtd
pwm-node mine fdtd/cavity_s1_ideal.yaml
```
