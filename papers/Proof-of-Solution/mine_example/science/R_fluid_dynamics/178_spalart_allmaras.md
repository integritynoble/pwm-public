# Principle #178 — Spalart-Allmaras Model

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.bilinear.advection] --> [L.poisson] --> [N.pointwise.turbmodel] --> [B.wall] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→L.poisson→N.pointwise.turbmodel→B.wall   SA-turb     NACA0012-aero     FVM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SPALART-ALLMARAS   P = (E,G,W,C)   Principle #178              │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂ν̃/∂t + u·∇ν̃ = cb₁S̃ν̃ − cw₁fw(ν̃/d)²                │
│        │              + (1/σ)∇·[(ν+ν̃)∇ν̃] + cb₂(∇ν̃)²          │
│        │ νₜ = ν̃fv₁;  one-equation eddy viscosity model        │
│        │ Forward: RANS + SA → mean flow (ū,p̄) on Ω            │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.bilinear.advection] --> [L.poisson] --> [N.pointwise.turbmodel] --> [B.wall]│
│        │ time  momentum  pressure  SA-model  wall-BC                                                 │
│        │ V={∂.time,N.bilinear.advection,L.poisson,N.pointwise.turbmodel,B.wall}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (one-equation model; robust convergence)│
│        │ Uniqueness: YES for attached and mildly separated flows│
│        │ Stability: robust; designed for aerospace applications │
│        │ Mismatch: wall distance d error, trip term setting     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = Cl/Cd error vs experiment, L2 velocity error       │
│        │ q = 2.0 (2nd-order FVM)                               │
│        │ T = {lift_error, drag_error, Cp_distribution_error}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | SA transport equation dimensionally consistent; fv1, fw functions well-defined | PASS |
| S2 | Single-equation closure; robust for attached external aero flows | PASS |
| S3 | SIMPLE/density-based solver converges; CFL ramping standard | PASS |
| S4 | Cl error < 2%, Cd error < 10% for subsonic airfoils | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# spalart_allmaras/naca0012_s1.yaml
principle_ref: sha256:<p178_hash>
omega:
  grid: [256, 128]
  domain: C-mesh_around_NACA0012
  chord: 1.0
  far_field: 50_chords
E:
  forward: "RANS + Spalart-Allmaras"
B:
  airfoil: {no_slip: true, y_plus: 1}
  far_field: {freestream: {M: 0.15, alpha: 4_deg}}
I:
  scenario: NACA0012_subsonic
  Re: 6.0e6
  alpha_deg: [0, 4, 8, 12]
O: [Cl_error, Cd_error, Cp_distribution_L2]
epsilon:
  Cl_error_max: 2.0e-2
  Cd_error_max: 1.0e-1
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | C-mesh adequate; far-field 50c sufficient; y⁺<1 | PASS |
| S2 | Re=6M subsonic well within SA validity | PASS |
| S3 | SA + SIMPLE converges for α ≤ 12° | PASS |
| S4 | Cl error < 2% achievable vs Abbott-Doenhoff data | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# spalart_allmaras/benchmark_naca0012.yaml
spec_ref: sha256:<spec178_hash>
principle_ref: sha256:<p178_hash>
dataset:
  name: NACA0012_experimental
  reference: "Abbott & von Doenhoff (1959), NASA TMR"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: SU2 (SA)
    params: {mesh: 256x128, CFL: 10}
    results: {Cl_error: 1.5%, Cd_error: 8.2%}
  - solver: OpenFOAM (SA)
    params: {mesh: 256x128}
    results: {Cl_error: 1.8%, Cd_error: 9.1%}
  - solver: FUN3D (SA)
    params: {mesh: 256x128}
    results: {Cl_error: 1.2%, Cd_error: 7.5%}
quality_scoring:
  - {min_Cl_err: 0.5%, Q: 1.00}
  - {min_Cl_err: 1.5%, Q: 0.90}
  - {min_Cl_err: 2.5%, Q: 0.80}
  - {min_Cl_err: 4.0%, Q: 0.75}
```

**Baseline solver:** SU2 SA — Cl error 1.5%
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Cl Error | Cd Error | Runtime | Q |
|--------|----------|----------|---------|---|
| OpenFOAM (SA, coarse) | 2.5% | 12% | 60 s | 0.80 |
| SU2 (SA) | 1.5% | 8.2% | 90 s | 0.90 |
| FUN3D (SA) | 1.2% | 7.5% | 120 s | 0.90 |
| SU2 (SA, grid-adapted) | 0.4% | 4.1% | 300 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case (adapted): 300 × 1.00 = 300 PWM
Floor:               300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p178_hash>",
  "h_s": "sha256:<spec178_hash>",
  "h_b": "sha256:<bench178_hash>",
  "r": {"residual_norm": 4.0e-3, "error_bound": 2.0e-2, "ratio": 0.20},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
  "Q": 1.00,
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"}
}
```

---

## Reward Summary

| Layer | Seed Reward | Ongoing Royalties |
|-------|-------------|-------------------|
| L1 Principle | 200 PWM | 5% of L4 mints |
| L2 spec.md | 105 PWM | 10% of L4 mints |
| L3 Benchmark | 60 PWM | 15% of L4 mints |
| L4 Solution | — | 225–300 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep spalart
pwm-node verify spalart_allmaras/naca0012_s1.yaml
pwm-node mine spalart_allmaras/naca0012_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
