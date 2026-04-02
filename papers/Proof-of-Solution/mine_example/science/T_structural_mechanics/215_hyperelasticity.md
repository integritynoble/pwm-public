# Principle #215 — Nonlinear Elasticity (Hyperelasticity)

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [N.strain_energy] --> [L.tangent] --> [B.dirichlet] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.strain_energy→L.tangent→B.dirichlet   hyperelast  rubber-block-3D    FEM-NR
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  NONLINEAR ELASTICITY (HYPERELAST) P = (E,G,W,C)  Principle #215│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∇·P = f,  P = ∂Ψ/∂F,  F = I + ∇u                    │
│        │ P = first Piola-Kirchhoff stress, F = deformation grad │
│        │ Ψ = strain-energy density (Neo-Hookean, Mooney-Rivlin) │
│        │ Forward: given BC/Ψ/loads → solve for u (large def.)  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.strain_energy] --> [L.tangent] --> [B.dirichlet] │
│        │ strain-energy-eval  tangent-stiffness-solve  displacement-BC│
│        │ V={N.strain_energy,L.tangent,B.dirichlet}  L_DAG=3.0        │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Ball's polyconvexity for Ψ)           │
│        │ Uniqueness: CONDITIONAL (depends on load level/Ψ)     │
│        │ Stability: Newton-Raphson convergence depends on step  │
│        │ Mismatch: material parameter error, load path          │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖u−u_ref‖/‖u_ref‖ (primary)    │
│        │ q = 2.0 (quadratic elements), Newton iterations < 20 │
│        │ T = {residual_norm, Newton_iters, K_resolutions}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Deformation gradient and stress measures consistent; Ψ polyconvex | PASS |
| S2 | Ball's existence theory applies for Neo-Hookean/Mooney-Rivlin | PASS |
| S3 | Newton-Raphson with load stepping converges for moderate strains | PASS |
| S4 | Relative L2 error bounded via nonlinear a priori estimates | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# hyperelasticity/rubber_block_s1_ideal.yaml
principle_ref: sha256:<p215_hash>
omega:
  grid: [32, 32, 32]
  domain: unit_cube
E:
  forward: "div(P) = f,  P = dPsi/dF"
  model: Neo-Hookean
  mu: 0.4225e6   # shear modulus Pa
  kappa: 1.0e8   # bulk modulus Pa (nearly incompressible)
B:
  bottom: {u: [0,0,0]}   # fixed
  top: {u: [0,0,-0.3]}   # 30% compression
I:
  scenario: uniaxial_compression
  strain_levels: [0.1, 0.2, 0.3]
  mesh_sizes: [8, 16, 32]
O: [L2_displacement_error, max_stress_error, volume_change]
epsilon:
  L2_error_max: 1.0e-3
  volume_change_max: 1.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 32³ mesh adequate; nearly-incompressible formulation used | PASS |
| S2 | Neo-Hookean model polyconvex; solution exists for 30% strain | PASS |
| S3 | Newton-Raphson with load steps converges in < 15 iterations | PASS |
| S4 | L2 error < 10⁻³ at 32³ mesh | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# hyperelasticity/benchmark_rubber_block.yaml
spec_ref: sha256:<spec215_hash>
principle_ref: sha256:<p215_hash>
dataset:
  name: rubber_block_compression
  reference: "Ogden (1997) — analytical uniaxial Neo-Hookean solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-Q1-mixed
    params: {h: 1/16, load_steps: 10}
    results: {L2_error: 5.2e-3, Newton_iters_avg: 6}
  - solver: FEM-Q2-mixed
    params: {h: 1/16, load_steps: 10}
    results: {L2_error: 8.0e-4, Newton_iters_avg: 5}
  - solver: FEM-Q2-mixed (h=1/32)
    params: {h: 1/32, load_steps: 10}
    results: {L2_error: 2.0e-4, Newton_iters_avg: 5}
quality_scoring:
  - {min_L2: 1.0e-4, Q: 1.00}
  - {min_L2: 1.0e-3, Q: 0.90}
  - {min_L2: 5.0e-3, Q: 0.80}
  - {min_L2: 1.0e-2, Q: 0.75}
```

**Baseline solver:** FEM-Q2-mixed — L2 error 8.0×10⁻⁴
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Max Error | Runtime | Q |
|--------|----------|-----------|---------|---|
| FEM-Q1-mixed | 5.2e-3 | 1.2e-2 | 30 s | 0.80 |
| FEM-Q2-mixed (h=1/16) | 8.0e-4 | 2.0e-3 | 90 s | 0.90 |
| FEM-Q2-mixed (h=1/32) | 2.0e-4 | 5.0e-4 | 600 s | 1.00 |
| FEM-Q2-mixed + arc-length | 1.5e-4 | 4.0e-4 | 500 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (fine mesh): 300 × 1.00 = 300 PWM
Floor:                 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p215_hash>",
  "h_s": "sha256:<spec215_hash>",
  "h_b": "sha256:<bench215_hash>",
  "r": {"residual_norm": 2.0e-4, "error_bound": 1.0e-3, "ratio": 0.20},
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
pwm-node benchmarks | grep hyperelasticity
pwm-node verify hyperelasticity/rubber_block_s1_ideal.yaml
pwm-node mine hyperelasticity/rubber_block_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
