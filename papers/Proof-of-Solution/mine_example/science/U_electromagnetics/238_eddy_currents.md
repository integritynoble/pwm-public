# Eddy Currents — Four-Layer Walkthrough

**Principle #238 · Eddy-Current Simulation**
Domain: Electromagnetics & Optics | Carrier: EM-field | Difficulty: standard (δ=3) | DAG: [∂.time] --> [∂.space.curl] --> [L.sparse.fem] --> [B.surface]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Diffusion eqn,   │→│ Conducting plate │→│ Analytical skin  │→│ FEM / A-V formu- │
│ skin depth, A-V  │ │ + coil config,  │ │ depth solutions  │ │ lation solver    │
│ formulation      │ │ S1-S4 scenarios │ │ baselines        │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

∇×(ν∇×A) + σ∂A/∂t = J_src   (A-formulation)
Quasi-static approximation: displacement current neglected (ωε ≪ σ)
Skin depth: δ_s = √(2/(ωμσ))

### DAG

```
[∂.time] --> [∂.space.curl] --> [L.sparse.fem] --> [B.surface]
time-harmonic  curl-curl-operator  FEM-solve  conductor-BC
```

V={∂.time,∂.space.curl,L.sparse.fem,B.surface}  L_DAG=3.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Parabolic PDE, well-posed with gauging |
| Uniqueness | YES | Coulomb gauge + BCs yield unique A |
| Stability | YES | Dissipative system, continuous dependence on data |

Mismatch: conductivity σ error, permeability μ_r error, skin depth vs mesh size

### Error Method

e = relative impedance error |ΔZ|/|Z|, loss density error
q = 2.0 (linear edge elements)

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #238"
omega:
  geometry: conducting_plate_above_coil
  sigma_S_m: 5.8e7  # copper
  freq_Hz: 1000
  skin_depth_mm: 2.1
E:
  forward: "curl(nu*curl(A)) + sigma*dA/dt = J_src"
I:
  scenario: S1_ideal
  coil: {turns: 100, current_A: 1.0, radius_mm: 10}
O: [impedance_error_pct, loss_error_pct, skin_depth_accuracy]
epsilon:
  impedance_error_max_pct: 2.0
  loss_error_max_pct: 3.0
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | True σ, μ_r | None | Z err ≤ 2% |
| S2 Mismatch | σ ± 10% | Δσ | Z err ≤ 8% |
| S3 Oracle | True σ given | Known Δσ | Z err ≤ 3% |
| S4 Blind Cal | Estimate σ from impedance | Self-cal | recovery ≥ 85% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: eddy_current_NDE
  cases: 8  # plate, pipe, crack detection
  analytical_ref: Dodd_Deeds_solutions
baselines:
  - solver: FEM_AV_edge
    Z_err_pct: 1.5
    time_s: 60
  - solver: BEM_eddy
    Z_err_pct: 2.0
    time_s: 40
quality_scoring:
  metric: impedance_error_pct
  thresholds:
    - {max: 0.5, Q: 1.00}
    - {max: 1.0, Q: 0.90}
    - {max: 2.0, Q: 0.80}
    - {max: 5.0, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | Z err | Time | Q | Reward |
|--------|-------|------|---|--------|
| FEM_AV_edge | 1.5% | 60s | 0.80 | 240 PWM |
| BEM_eddy | 2.0% | 40s | 0.80 | 240 PWM |
| hp-FEM_eddy | 0.4% | 120s | 1.00 | 300 PWM |

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q PWM
```

### Certificate

```json
{
  "principle": 238,
  "r": {"residual_norm": 0.004, "error_bound": 0.02, "ratio": 0.20},
  "c": {"resolutions": [1000,2000,4000], "fitted_rate": 2.0, "theoretical_rate": 2.0},
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
| L4 Solution | — | 240–300 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep eddy
pwm-node mine eddy/plate_coil_s1_ideal.yaml
```
