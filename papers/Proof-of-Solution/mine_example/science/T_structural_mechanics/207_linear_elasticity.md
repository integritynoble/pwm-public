# Principle #207 — Linear Elasticity (Navier-Cauchy)

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Textbook (δ=1)
**DAG:** [L.stiffness] --> [B.dirichlet] |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.stiffness→B.dirichlet      Navier-C    cantilever-2D     FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LINEAR ELASTICITY (NAVIER-CAUCHY)  P = (E,G,W,C)  Principle #207│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ −∇·σ = f,  σ = C:ε,  ε = ½(∇u + ∇uᵀ)                │
│        │ u = displacement, σ = stress tensor, ε = strain tensor │
│        │ C = fourth-order elasticity tensor (λ, μ Lamé params)  │
│        │ Forward: given BC/loads/material → solve for u over Ω  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.stiffness] --> [B.dirichlet]                      │
│        │ stiffness-assemble-solve  displacement-BC              │
│        │ V={L.stiffness,B.dirichlet}  L_DAG=1.0               │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Lax-Milgram on H¹; elliptic PDE)      │
│        │ Uniqueness: YES (coercivity of bilinear form)          │
│        │ Stability: κ depends on Poisson ratio; κ ~ 1/(1−2ν)   │
│        │ Mismatch: material property error, BC perturbation     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖u−u_ref‖/‖u_ref‖ (primary)    │
│        │ q = 2.0 (FEM-Q2), 1.0 (FEM-Q1)                       │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Displacement/stress dimensions consistent; symmetry of σ well-formed | PASS |
| S2 | Lax-Milgram guarantees unique weak solution; Korn's inequality holds | PASS |
| S3 | FEM (Q1/Q2) converges for well-posed linear elastic problems | PASS |
| S4 | Relative L2 error bounded by mesh-dependent a priori estimates | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# linear_elasticity/cantilever_s1_ideal.yaml
principle_ref: sha256:<p207_hash>
omega:
  grid: [128, 64]
  domain: rectangular_beam
  length: 1.0
  height: 0.1
E:
  forward: "-div(sigma) = f,  sigma = C:eps(u)"
  youngs_modulus: 210.0e9   # steel, Pa
  poisson_ratio: 0.3
B:
  left_wall: {u: [0.0, 0.0]}   # clamped
  right_end: {traction: [0.0, -1000.0]}  # tip load
I:
  scenario: cantilever_beam
  material: steel
  mesh_sizes: [16, 32, 64, 128]
O: [L2_displacement_error, max_stress_error, energy_norm_error]
epsilon:
  L2_error_max: 1.0e-4
  energy_error_max: 1.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Mesh adequate for beam aspect ratio; element quality verified | PASS |
| S2 | Linear problem with unique solution; well within elastic regime | PASS |
| S3 | FEM-Q2 converges at O(h²) for displacement | PASS |
| S4 | L2 error < 10⁻⁴ achievable at h=1/128 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# linear_elasticity/benchmark_cantilever.yaml
spec_ref: sha256:<spec207_hash>
principle_ref: sha256:<p207_hash>
dataset:
  name: cantilever_beam_analytical
  reference: "Timoshenko & Goodier — analytical beam solutions"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-Q1
    params: {h: 1/64, order: 1}
    results: {L2_error: 8.5e-3, max_stress_error: 2.1e-2}
  - solver: FEM-Q2
    params: {h: 1/64, order: 2}
    results: {L2_error: 1.2e-4, max_stress_error: 5.3e-4}
  - solver: FEM-Q2 (h=1/128)
    params: {h: 1/128, order: 2}
    results: {L2_error: 3.0e-5, max_stress_error: 1.3e-4}
quality_scoring:
  - {min_L2: 1.0e-5, Q: 1.00}
  - {min_L2: 1.0e-4, Q: 0.90}
  - {min_L2: 1.0e-3, Q: 0.80}
  - {min_L2: 5.0e-3, Q: 0.75}
```

**Baseline solver:** FEM-Q2 — L2 error 1.2×10⁻⁴
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Max Error | Runtime | Q |
|--------|----------|-----------|---------|---|
| FEM-Q1 | 8.5e-3 | 2.1e-2 | 2 s | 0.75 |
| FEM-Q2 | 1.2e-4 | 5.3e-4 | 8 s | 0.90 |
| FEM-Q2 (h=1/128) | 3.0e-5 | 1.3e-4 | 30 s | 1.00 |
| hp-FEM | 5.0e-6 | 2.0e-5 | 15 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (hp-FEM):   100 × 1.00 = 100 PWM
Floor:                100 × 0.75 =  75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p207_hash>",
  "h_s": "sha256:<spec207_hash>",
  "h_b": "sha256:<bench207_hash>",
  "r": {"residual_norm": 5.0e-6, "error_bound": 1.0e-4, "ratio": 0.05},
  "c": {"fitted_rate": 2.01, "theoretical_rate": 2.0, "K": 4},
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
pwm-node benchmarks | grep linear_elasticity
pwm-node verify linear_elasticity/cantilever_s1_ideal.yaml
pwm-node mine linear_elasticity/cantilever_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
