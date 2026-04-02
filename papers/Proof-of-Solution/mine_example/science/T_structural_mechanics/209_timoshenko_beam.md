# Principle #209 — Timoshenko Beam Theory

**Domain:** Structural Mechanics | **Carrier:** N/A (ODE-based) | **Difficulty:** Textbook (δ=1)
**DAG:** [L.stiffness] --> [B.dirichlet] |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.stiffness→B.dirichlet      Timo-beam   thick-cantilever   FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  TIMOSHENKO BEAM THEORY            P = (E,G,W,C)  Principle #209│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ GA_s(d²w/dx² − dψ/dx) + q = 0                         │
│        │ EI d²ψ/dx² + GA_s(dw/dx − ψ) = 0                      │
│        │ w = deflection, ψ = rotation, A_s = shear area         │
│        │ Forward: given BC/EI/GA_s/q → solve for (w, ψ)        │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.stiffness] --> [B.dirichlet]                      │
│        │ Timoshenko-stiffness-solve  beam-BC                    │
│        │ V={L.stiffness,B.dirichlet}  L_DAG=1.0               │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (coupled second-order system; H¹)       │
│        │ Uniqueness: YES (coercive bilinear form)               │
│        │ Stability: κ depends on slenderness; shear locking risk│
│        │ Mismatch: shear correction factor, material error      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖w−w_ref‖/‖w_ref‖ (primary)    │
│        │ q = 2.0 (linear elements), locking-free with reduced  │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Coupled ODE system consistent; shear area well-defined | PASS |
| S2 | Unique solution for standard BCs; shear locking avoided with reduced integration | PASS |
| S3 | Mixed FEM or reduced-integration elements converge without locking | PASS |
| S4 | Relative L2 error bounded by a priori estimates | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# timoshenko/thick_cantilever_s1_ideal.yaml
principle_ref: sha256:<p209_hash>
omega:
  grid: [64]
  domain: beam_1D
  span: 1.0
  depth: 0.2   # thick beam L/d = 5
E:
  forward: "Timoshenko coupled system (w, psi)"
  EI: 1.0e6
  GA_s: 5.0e6   # shear rigidity
B:
  x0: {w: 0, psi: 0}   # clamped
  xL: {V: -1000}        # tip shear load
I:
  scenario: thick_cantilever
  L_over_d: [5, 10, 20, 100]
  mesh_sizes: [8, 16, 32, 64]
O: [L2_deflection_error, L2_rotation_error, tip_deflection_error]
epsilon:
  L2_error_max: 1.0e-4
  tip_error_max: 1.0e-5
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Mesh and shear correction factor consistent | PASS |
| S2 | Well-posed thick-beam problem; analytical solution exists | PASS |
| S3 | Reduced-integration linear elements converge without locking | PASS |
| S4 | L2 error < 10⁻⁴ achievable at N=64 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# timoshenko/benchmark_thick_cantilever.yaml
spec_ref: sha256:<spec209_hash>
principle_ref: sha256:<p209_hash>
dataset:
  name: Timoshenko_beam_analytical
  reference: "Timoshenko — exact thick-beam deflection formulas"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-linear-full-integration
    params: {N: 32}
    results: {L2_error: 2.3e-1, note: "shear locking"}
  - solver: FEM-linear-reduced-integration
    params: {N: 32}
    results: {L2_error: 4.5e-4, tip_error: 1.2e-4}
  - solver: FEM-quadratic
    params: {N: 16}
    results: {L2_error: 8.0e-5, tip_error: 2.0e-5}
quality_scoring:
  - {min_L2: 1.0e-5, Q: 1.00}
  - {min_L2: 1.0e-4, Q: 0.90}
  - {min_L2: 1.0e-3, Q: 0.80}
  - {min_L2: 5.0e-3, Q: 0.75}
```

**Baseline solver:** FEM-quadratic — L2 error 8.0×10⁻⁵
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Max Error | Runtime | Q |
|--------|----------|-----------|---------|---|
| FEM-linear-full | 2.3e-1 | 4.0e-1 | 0.1 s | — (locked) |
| FEM-linear-reduced | 4.5e-4 | 1.2e-3 | 0.1 s | 0.80 |
| FEM-quadratic | 8.0e-5 | 2.0e-4 | 0.2 s | 0.90 |
| Exact (closed-form) | 0.0 | 0.0 | 0.01 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (exact):  100 × 1.00 = 100 PWM
Floor:              100 × 0.75 =  75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p209_hash>",
  "h_s": "sha256:<spec209_hash>",
  "h_b": "sha256:<bench209_hash>",
  "r": {"residual_norm": 8.0e-5, "error_bound": 1.0e-4, "ratio": 0.80},
  "c": {"fitted_rate": 2.02, "theoretical_rate": 2.0, "K": 4},
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
pwm-node benchmarks | grep timoshenko
pwm-node verify timoshenko/thick_cantilever_s1_ideal.yaml
pwm-node mine timoshenko/thick_cantilever_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
