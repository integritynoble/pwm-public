# Helmholtz Scattering — Four-Layer Walkthrough

**Principle #233 · Helmholtz Electromagnetic Scattering**
Domain: Electromagnetics & Optics | Carrier: photon/EM-field | Difficulty: standard (δ=3) | DAG: [∂.space.laplacian] --> [L.sparse.fem] --> [B.absorbing]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Helmholtz eqn,   │→│ 2D/3D scatterer  │→│ Mie/cylinder ref │→│ FEM / BEM / MoM  │
│ Sommerfeld BC,   │ │ geometry + freq,  │ │ solutions, grids │ │ solver, certif.  │
│ RCS definition   │ │ S1-S4 scenarios  │ │ baselines        │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

(∇² + k²)u_s = 0 in Ω_ext,  u_s + u_inc = u_total on Γ
Sommerfeld radiation: r^{(d-1)/2}(∂u_s/∂r − iku_s) → 0 as r → ∞

### DAG

```
[∂.space.laplacian] --> [L.sparse.fem] --> [B.absorbing]
Helmholtz-operator  FEM-solve  radiation-BC
```

V={∂.space.laplacian,L.sparse.fem,B.absorbing}  L_DAG=3.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Rellich uniqueness + Fredholm theory |
| Uniqueness | YES | Unique for all k > 0 (no interior resonance in exterior problem) |
| Stability | YES | Bounded via limiting absorption principle |

Mismatch: wavenumber k error, geometry perturbation, truncation distance

### Error Method

e = relative far-field error ‖σ_num − σ_ref‖/‖σ_ref‖, RCS error in dB
q = 2.0 (linear elements), higher for hp-FEM

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #233"
omega:
  domain: 2D_exterior
  scatterer: {shape: circle, radius: 1.0_lambda}
  freq_GHz: 10.0
  k: 209.4  # 2*pi*f/c
E:
  forward: "(nabla^2 + k^2) u_s = 0, Sommerfeld BC"
  incident: plane_wave
I:
  scenario: S1_ideal
  mesh: lambda/10
  truncation: PML_10_layers
O: [RCS_error_dB, relative_L2_far_field]
epsilon:
  RCS_error_max_dB: 0.5
  rel_L2_max: 0.01
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact geometry | None | RCS err ≤ 0.5 dB |
| S2 Mismatch | Perturbed radius ±5% | Δr | RCS err ≤ 1.5 dB |
| S3 Oracle | True geometry given | Known Δr | RCS err ≤ 0.8 dB |
| S4 Blind Cal | Estimate shape from scattered field | Self-cal | recovery ≥ 85% |

Layer 2 reward: 150 × φ(t) PWM per spec

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: helmholtz_scatter_2D
  cases: 10  # circle, ellipse, square, multi-body
  analytical_ref: Mie_series (circle), series expansion
baselines:
  - solver: FEM_PML_p2
    RCS_err_dB: 0.3
    time_s: 45
  - solver: BEM_linear
    RCS_err_dB: 0.4
    time_s: 30
quality_scoring:
  metric: RCS_error_dB
  thresholds:
    - {max: 0.1, Q: 1.00}
    - {max: 0.3, Q: 0.90}
    - {max: 0.5, Q: 0.80}
    - {max: 1.5, Q: 0.75}
```

Layer 3 reward: 100 × φ(t) PWM

---

## Layer 4 — Solution

| Solver | RCS err (dB) | Time | Q | Reward |
|--------|-------------|------|---|--------|
| FEM_PML_p2 | 0.3 | 45s | 0.90 | 270 PWM |
| BEM_linear | 0.4 | 30s | 0.80 | 240 PWM |
| hp-BEM | 0.08 | 90s | 1.00 | 300 PWM |

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q PWM
```

### Certificate

```json
{
  "principle": 233,
  "r": {"residual_norm": 0.003, "error_bound": 0.01, "ratio": 0.30},
  "c": {"resolutions": [5,10,20], "fitted_rate": 2.05, "theoretical_rate": 2.0},
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
| L4 Solution | — | 240–300 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep helmholtz_scatter
pwm-node mine helmholtz/scatter_s1_ideal.yaml
```
