# Principle #175 — Potential Flow

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Textbook (δ=1)
**DAG:** [L.laplace] --> [B.neumann] |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.laplace→B.neumann          Potential   cylinder-flow      BEM/FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  POTENTIAL FLOW   P = (E,G,W,C)   Principle #175                │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∇²φ = 0  (Laplace equation for velocity potential)    │
│        │ u = ∇φ   (irrotational, inviscid, incompressible)     │
│        │ Bernoulli: p + ½ρ|∇φ|² = const along streamlines     │
│        │ Forward: given far-field + body geometry → solve φ     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.laplace] --> [B.neumann]                            │
│        │ Laplace-solve  no-penetration-BC                        │
│        │ V={L.laplace,B.neumann}  A={L→B}  L_DAG=1.0           │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (maximum principle, harmonic functions) │
│        │ Uniqueness: YES (up to constant; Neumann unique in ∇φ)│
│        │ Stability: κ ~ 1 (Laplace is perfectly conditioned)   │
│        │ Mismatch: body shape perturbation, far-field error     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error in velocity ‖∇φ−∇φ_ref‖        │
│        │ q = 2.0 (FEM-P1), spectral convergence (BEM)        │
│        │ T = {residual_norm, lift_coeff_error, K_resolutions}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Laplace equation on exterior domain; far-field BC consistent | PASS |
| S2 | Maximum principle guarantees unique harmonic solution | PASS |
| S3 | BEM (panel method), FEM, conformal mapping all converge | PASS |
| S4 | Error bounded by panel/element size; analytical benchmarks exist | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# potential/cylinder_s1.yaml
principle_ref: sha256:<p175_hash>
omega:
  grid: [128, 128]
  domain: disk_exterior
  cylinder_radius: 1.0
  far_field_radius: 20.0
E:
  forward: "∇²φ = 0, u = ∇φ"
  U_inf: [1.0, 0.0]
B:
  cylinder: {normal_vel: 0}   # no penetration
  far_field: {phi: U_inf · r}
  circulation: {Gamma: 0}     # no lift
I:
  scenario: cylinder_no_circulation
  mesh_sizes: [32, 64, 128]
O: [L2_velocity_error, pressure_coeff_error, drag_error]
epsilon:
  L2_error_max: 1.0e-4
  Cp_error_max: 1.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Exterior domain well-formed; far-field 20R sufficient | PASS |
| S2 | Analytic solution exists: φ = U(r+R²/r)cosθ | PASS |
| S3 | Panel method converges; FEM on mapped domain converges | PASS |
| S4 | L2 error < 10⁻⁴ achievable at N=128 panels | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# potential/benchmark_cylinder.yaml
spec_ref: sha256:<spec175_hash>
principle_ref: sha256:<p175_hash>
dataset:
  name: Cylinder_analytic
  reference: "Batchelor (1967) exact potential flow"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Panel-method (constant)
    params: {N_panels: 64}
    results: {L2_error: 3.5e-3, Cp_error: 5.2e-3}
  - solver: Panel-method (linear)
    params: {N_panels: 64}
    results: {L2_error: 4.1e-4, Cp_error: 6.8e-4}
  - solver: FEM-P2
    params: {h: 1/64}
    results: {L2_error: 8.5e-5, Cp_error: 1.2e-4}
quality_scoring:
  - {min_L2: 1.0e-5, Q: 1.00}
  - {min_L2: 1.0e-4, Q: 0.90}
  - {min_L2: 1.0e-3, Q: 0.80}
  - {min_L2: 5.0e-3, Q: 0.75}
```

**Baseline solver:** FEM-P2 — L2 error 8.5×10⁻⁵
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Cp Error | Runtime | Q |
|--------|----------|----------|---------|---|
| Panel (constant) | 3.5e-3 | 5.2e-3 | 0.1 s | 0.80 |
| Panel (linear) | 4.1e-4 | 6.8e-4 | 0.2 s | 0.90 |
| FEM-P2 | 8.5e-5 | 1.2e-4 | 2 s | 0.90 |
| Spectral (conformal) | 2.1e-8 | 3.5e-8 | 0.05 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 1 × 1.0 × Q
Best case (spectral): 100 × 1.00 = 100 PWM
Floor:                100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p175_hash>",
  "h_s": "sha256:<spec175_hash>",
  "h_b": "sha256:<bench175_hash>",
  "r": {"residual_norm": 2.1e-8, "error_bound": 1.0e-4, "ratio": 2.1e-4},
  "c": {"fitted_rate": 2.0, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 75–100 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep potential
pwm-node verify potential/cylinder_s1.yaml
pwm-node mine potential/cylinder_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
