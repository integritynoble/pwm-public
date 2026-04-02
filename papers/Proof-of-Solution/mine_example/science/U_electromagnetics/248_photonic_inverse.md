# Photonic Inverse Design — Four-Layer Walkthrough

**Principle #248 · Photonic Crystal / Inverse Design**
Domain: Electromagnetics & Optics | Carrier: photon | Difficulty: hard (δ=5) | DAG: [∂.time] --> [∂.space.curl] --> [O.adjoint]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Band structure,  │→│ Target bandgap / │→│ Known PhC band   │→│ FDTD / RCWA /    │
│ Bloch theorem,   │ │ transmission,    │ │ structures, ref  │ │ topology opt.    │
│ topology opt     │ │ S1-S4 scenarios  │ │ baselines        │ │ solver           │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

∇×(1/ε(r))∇×H = (ω/c)²H, with Bloch: H_k(r) = e^{ik·r} u_k(r)
Inverse: find ε(r) to achieve target band structure or transmission spectrum
Adjoint-based gradient: ∂J/∂ε via adjoint field solve

### DAG

```
[∂.time] --> [∂.space.curl] --> [O.adjoint]
forward-FDTD  curl-operators  adjoint-gradient
```
V={∂.time,∂.space.curl,O.adjoint}  L_DAG=5.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | CONDITIONAL | Not all targets achievable; feasibility depends on ε contrast |
| Uniqueness | NO | Multiple designs can achieve same target |
| Stability | CONDITIONAL | Sensitive to ε(r) perturbations near band edges |

Mismatch: fabrication error, ε tolerance, etching imprecision

### Error Method

e = bandgap error (%), transmission spectrum RMSE; q = 2.0 (FDTD)

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #248"
omega:
  lattice: square_2D
  period_nm: 400
  material: {high: Si_3.5, low: air_1.0}
  target: complete_bandgap_TE
E:
  forward: "curl(1/eps * curl(H)) = (omega/c)^2 * H, Bloch BCs"
I:
  scenario: S1_ideal
  resolution: 32_pts_per_period
O: [bandgap_ratio, transmission_error, design_binary_pct]
epsilon:
  bandgap_ratio_min: 0.10
  transmission_error_max: 0.05
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact ε(r) | None | gap ratio ≥ 0.10 |
| S2 Mismatch | Etch bias ±10nm | Δr | gap ratio ≥ 0.05 |
| S3 Oracle | True etch bias given | Known Δr | gap ratio ≥ 0.08 |
| S4 Blind Cal | Robust design under uncertainty | Stochastic opt | recovery ≥ 75% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: photonic_inverse_design
  cases: 8  # bandgap, waveguide bend, splitter, filter
  ref: published_PhC_designs
baselines:
  - solver: FDTD_bandsolve
    bandgap_ratio: 0.12
  - solver: RCWA
    transmission_err: 0.03
  - solver: topology_opt_SIMP
    bandgap_ratio: 0.15
quality_scoring:
  metric: bandgap_ratio
  thresholds:
    - {min: 0.20, Q: 1.00}
    - {min: 0.15, Q: 0.90}
    - {min: 0.10, Q: 0.80}
    - {min: 0.05, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | Gap ratio | Time | Q | Reward |
|--------|----------|------|---|--------|
| FDTD_bandsolve | 0.12 | 300s | 0.80 | 400 PWM |
| topology_opt | 0.15 | 1800s | 0.90 | 450 PWM |
| adjoint_level_set | 0.22 | 3600s | 1.00 | 500 PWM |

```
R = 100 × 1.0 × 5 × 1.0 × Q = 500 × Q PWM
```

### Certificate

```json
{
  "principle": 248,
  "r": {"residual_norm": 0.03, "error_bound": 0.05, "ratio": 0.60},
  "c": {"resolutions": [16,32,64], "fitted_rate": 2.0, "theoretical_rate": 2.0},
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
| L4 Solution | — | 400–500 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep photonic_inverse
pwm-node mine photonic/bandgap_s1_ideal.yaml
```
