# Principle #499 — Shape Optimization

**Domain:** Optimization | **Carrier:** N/A (PDE-constrained) | **Difficulty:** Advanced (δ=4)
**DAG:** [L.stiffness] --> [O.adjoint] --> [B.surface] | **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.stiff-->O.adj-->B.surf  ShapeOpt  airfoil/nozzle  adjoint-grad
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SHAPE OPTIMIZATION           P = (E,G,W,C)   Principle #499   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ min_Ω J(Ω) = ∫_Ω j(u,∇u) dx  s.t. PDE(u)=0 in Ω    │
│        │ Shape derivative: dJ/dΩ[V] = ∫_∂Ω g(u,p) V·n ds      │
│        │ p = adjoint state from adjoint PDE                     │
│        │ Deformation: X_new = X + αV   (boundary perturbation)  │
│        │ Forward: given initial shape → optimal boundary Γ*     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.stiff] ──→ [O.adj] ──→ [B.surf]                     │
│        │  FEM-matrix  adjoint-grad  shape-deform                │
│        │ V={L.stiff,O.adj,B.surf}  A={L.stiff→O.adj,O.adj→B.surf}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (shape derivative well-defined in Ck)   │
│        │ Uniqueness: NO (multiple local minima)                 │
│        │ Stability: regularization / Hadamard structure needed  │
│        │ Mismatch: mesh quality degradation, re-meshing errors  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |J − J_ref|/J_ref  (objective improvement)        │
│        │ q = N/A (gradient-based iteration)                    │
│        │ T = {objective_reduction, constraint_satisfaction, mesh}│
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Objective J well-defined; shape derivative exists (Hadamard) | PASS |
| S2 | Adjoint PDE well-posed (same operator as primal) | PASS |
| S3 | Steepest descent / L-BFGS-B converges within 50 iterations | PASS |
| S4 | Objective reduction > 20% from initial shape | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# shape_opt/airfoil_drag_s1.yaml
principle_ref: sha256:<p499_hash>
omega:
  mesh_elements: 50000
  domain: 2D_airfoil_RANS
  Re: 6.0e6
E:
  forward: "RANS flow + adjoint → shape gradient → deformation"
  objective: drag_coefficient
  constraint: lift_coefficient >= 0.5
  turbulence: SA_model
B:
  far_field: {Mach: 0.5, AoA: 2.0}
  airfoil: NACA0012_initial
  design_variables: 20_Hicks_Henne_bumps
I:
  scenario: 2D_airfoil_drag_minimization
  methods: [adjoint_steepest, adjoint_BFGS, free_form]
O: [Cd_reduction, Cl_maintained, shape_smoothness]
epsilon:
  Cd_reduction_min: 0.20    # 20% drag reduction
  Cl_constraint: 0.50
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 50k elements resolve BL; 20 design variables adequate | PASS |
| S2 | RANS + SA well-posed for transonic flow | PASS |
| S3 | Adjoint gradient converges; L-BFGS within 30 iterations | PASS |
| S4 | > 20% drag reduction from NACA0012 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# shape_opt/benchmark_airfoil.yaml
spec_ref: sha256:<spec499_hash>
principle_ref: sha256:<p499_hash>
dataset:
  name: NACA0012_shape_optimization
  reference: "Jameson (1988) aerodynamic shape optimization"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Finite-difference gradient
    params: {design_vars: 20, perturbation: 1e-4}
    results: {Cd_reduction: 0.18, iterations: 50}
  - solver: Adjoint gradient (steepest)
    params: {design_vars: 20}
    results: {Cd_reduction: 0.25, iterations: 40}
  - solver: Adjoint + L-BFGS
    params: {design_vars: 20, memory: 10}
    results: {Cd_reduction: 0.32, iterations: 25}
quality_scoring:
  - {min_reduction: 0.35, Q: 1.00}
  - {min_reduction: 0.25, Q: 0.90}
  - {min_reduction: 0.20, Q: 0.80}
  - {min_reduction: 0.10, Q: 0.75}
```

**Baseline solver:** Adjoint steepest descent — 25% drag reduction
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Cd Reduction | Cl Met | Iterations | Q |
|--------|-------------|--------|-----------|---|
| FD gradient | 0.18 | yes | 50 | 0.80 |
| Adjoint steepest | 0.25 | yes | 40 | 0.80 |
| Adjoint L-BFGS | 0.32 | yes | 25 | 0.90 |
| FFD + adjoint | 0.38 | yes | 20 | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (FFD): 400 × 1.00 = 400 PWM
Floor:           400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p499_hash>",
  "h_s": "sha256:<spec499_hash>",
  "h_b": "sha256:<bench499_hash>",
  "r": {"Cd_reduction": 0.38, "error_bound": 0.20, "ratio": 1.900},
  "c": {"Cl_maintained": true, "iterations": 20, "K": 3},
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
| L4 Solution | — | 300–400 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep shape_opt
pwm-node verify shape_opt/airfoil_drag_s1.yaml
pwm-node mine shape_opt/airfoil_drag_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
