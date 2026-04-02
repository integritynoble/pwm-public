# Electrostatics — Four-Layer Walkthrough

**Principle #250 · Electrostatic Poisson/Laplace Solver**
Domain: Electromagnetics & Optics | Carrier: EM-field | Difficulty: basic (δ=2) | DAG: [∂.space.laplacian] --> [B.dirichlet]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Poisson/Laplace, │→│ Capacitor / charge│→│ Analytical paral-│→│ FEM / FDM / BEM  │
│ Gauss's law,     │ │ distribution,    │ │ lel plate, sphere│ │ Poisson solver   │
│ boundary conds   │ │ S1-S4 scenarios  │ │ baselines        │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

∇·(ε∇φ) = −ρ  (Poisson), ∇²φ = 0 (Laplace, charge-free)
E = −∇φ, capacitance C = Q/V

### DAG

```
[∂.space.laplacian] --> [B.dirichlet]
Laplacian-solve  conductor-BC
```
V={∂.space.laplacian,B.dirichlet}  L_DAG=1.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Lax-Milgram for H¹ |
| Uniqueness | YES | Maximum principle |
| Stability | YES | Continuous dependence on ρ, BCs |

Mismatch: permittivity error, geometry simplification, mesh quality

### Error Method

e = relative potential error, capacitance error %; q = 2.0 (linear FEM)

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #250"
omega:
  geometry: parallel_plate_capacitor
  gap_mm: 1.0
  plate_area_mm2: 100
  eps_r: 4.0
E:
  forward: "div(eps*grad(phi)) = -rho"
I:
  scenario: S1_ideal
O: [potential_error_pct, capacitance_error_pct, energy_error_pct]
epsilon:
  capacitance_error_max_pct: 0.5
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact geometry | None | C err ≤ 0.5% |
| S2 Mismatch | ε_r ± 10% | Δε | C err ≤ 5% |
| S3 Oracle | True ε given | Known Δε | C err ≤ 1% |
| S4 Blind Cal | Estimate ε from C measurement | Self-cal | recovery ≥ 90% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: electrostatics
  cases: 8  # parallel plate, coaxial, sphere, point charge
  analytical_ref: closed_form_capacitance
baselines:
  - solver: FEM_p1
    C_err_pct: 0.3
  - solver: FDM_5pt
    C_err_pct: 0.8
quality_scoring:
  metric: capacitance_error_pct
  thresholds:
    - {max: 0.05, Q: 1.00}
    - {max: 0.2, Q: 0.90}
    - {max: 0.5, Q: 0.80}
    - {max: 2.0, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | C err | Time | Q | Reward |
|--------|-------|------|---|--------|
| FEM_p1 | 0.3% | 5s | 0.80 | 160 PWM |
| FEM_p2 | 0.05% | 10s | 1.00 | 200 PWM |
| BEM | 0.1% | 3s | 0.90 | 180 PWM |

```
R = 100 × 1.0 × 2 × 1.0 × Q = 200 × Q PWM
```

### Certificate

```json
{
  "principle": 250,
  "r": {"residual_norm": 0.0005, "error_bound": 0.005, "ratio": 0.10},
  "c": {"resolutions": [20,40,80], "fitted_rate": 2.0, "theoretical_rate": 2.0},
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
| L4 Solution | — | 160–200 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep electrostatics
pwm-node mine electrostatics/capacitor_s1_ideal.yaml
```
