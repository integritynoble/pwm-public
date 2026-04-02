# Magnetostatics — Four-Layer Walkthrough

**Principle #251 · Magnetostatic Field Solver**
Domain: Electromagnetics & Optics | Carrier: EM-field | Difficulty: basic (δ=2) | DAG: [∂.space.curl] --> [L.sparse.fem] --> [B.dirichlet]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ ∇×H=J, ∇·B=0,   │→│ Solenoid / magnet│→│ Biot-Savart ref, │→│ FEM / Biot-Savart│
│ vector potential,│ │ configuration,   │ │ inductance analyt.│ │ A-formulation    │
│ Biot-Savart      │ │ S1-S4 scenarios  │ │ baselines        │ │ solver           │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

∇×(ν∇×A) = J (vector potential formulation)
∇·B = 0 automatically satisfied: B = ∇×A
Biot-Savart: B(r) = (μ₀/4π) ∫ J(r')×(r−r')/|r−r'|³ dV'

### DAG

```
[∂.space.curl] --> [L.sparse.fem] --> [B.dirichlet]
curl-curl-operator  FEM-solve  flux-BC
```
V={∂.space.curl,L.sparse.fem,B.dirichlet}  L_DAG=1.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | With Coulomb gauge, unique A exists |
| Uniqueness | YES | Gauge condition + BCs |
| Stability | YES | Continuous dependence on J |

Mismatch: permeability μ_r error (nonlinear B-H), geometry tolerance

### Error Method

e = relative B-field error, inductance error %; q = 2.0 (edge elements)

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #251"
omega:
  geometry: solenoid
  turns: 100
  radius_mm: 10
  length_mm: 50
  current_A: 1.0
E:
  forward: "curl(nu*curl(A)) = J, B = curl(A)"
I:
  scenario: S1_ideal
  mu_r: 1.0
O: [B_field_error_pct, inductance_error_pct]
epsilon:
  B_error_max_pct: 0.5
  inductance_error_max_pct: 1.0
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Linear μ_r | None | B err ≤ 0.5% |
| S2 Mismatch | Nonlinear B-H curve | μ_r(B) | B err ≤ 5% |
| S3 Oracle | True B-H given | Known curve | B err ≤ 1% |
| S4 Blind Cal | Estimate B-H from measurements | Self-cal | recovery ≥ 85% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: magnetostatics
  cases: 8  # solenoid, Helmholtz coil, permanent magnet, iron core
  analytical_ref: Biot_Savart_exact, Neumann_formula
baselines:
  - solver: FEM_edge_p1
    B_err_pct: 0.3
  - solver: Biot_Savart_numerical
    B_err_pct: 0.1
quality_scoring:
  metric: B_field_error_pct
  thresholds:
    - {max: 0.05, Q: 1.00}
    - {max: 0.2, Q: 0.90}
    - {max: 0.5, Q: 0.80}
    - {max: 2.0, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | B err | Time | Q | Reward |
|--------|-------|------|---|--------|
| FEM_edge_p1 | 0.3% | 8s | 0.80 | 160 PWM |
| Biot_Savart | 0.1% | 2s | 0.90 | 180 PWM |
| FEM_p2_adaptive | 0.04% | 20s | 1.00 | 200 PWM |

```
R = 100 × 1.0 × 2 × 1.0 × Q = 200 × Q PWM
```

### Certificate

```json
{
  "principle": 251,
  "r": {"residual_norm": 0.001, "error_bound": 0.005, "ratio": 0.20},
  "c": {"resolutions": [500,1000,2000], "fitted_rate": 2.0, "theoretical_rate": 2.0},
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
pwm-node benchmarks | grep magnetostatics
pwm-node mine magnetostatics/solenoid_s1_ideal.yaml
```
