# Principle #216 — J2 Plasticity (von Mises)

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [N.pointwise] --> [L.tangent] --> [∂.time] --> [B.dirichlet] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pointwise→L.tangent→∂.time→B.dirichlet   J2-plast    notched-bar-tens   FEM-NR
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  J2 PLASTICITY (VON MISES)         P = (E,G,W,C)  Principle #216│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∇·σ = f,  ε = εᵉ + εᵖ                                │
│        │ Yield: f(σ) = σ_vm − σ_y(ε̄ᵖ) ≤ 0                    │
│        │ Flow: ε̇ᵖ = γ̇ ∂f/∂σ (associated flow rule)            │
│        │ Forward: given BC/loads/material → (u, σ, εᵖ)         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pointwise] --> [L.tangent] --> [∂.time] --> [B.dirichlet]│
│        │ yield-check  tangent-solve  load-increment  displacement-BC │
│        │ V={N.pointwise,L.tangent,∂.time,B.dirichlet}  L_DAG=3.0    │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (variational inequality; convex yield)  │
│        │ Uniqueness: YES (for monotone loading; convex Ψ)       │
│        │ Stability: path-dependent; load increment sensitivity  │
│        │ Mismatch: yield stress error, hardening parameter      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖u−u_ref‖/‖u_ref‖ (primary)    │
│        │ q = 1.5 (reduced by plastic strain localisation)      │
│        │ T = {residual_norm, plastic_zone_area, K_resolutions}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Stress/strain decomposition consistent; yield surface convex | PASS |
| S2 | Convex yield surface guarantees unique return-map solution | PASS |
| S3 | Radial return algorithm with Newton-Raphson converges | PASS |
| S4 | L2 error bounded; plastic zone captured with mesh refinement | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# j2_plasticity/notched_bar_s1_ideal.yaml
principle_ref: sha256:<p216_hash>
omega:
  grid: [64, 32]
  domain: notched_bar_2D
  length: 1.0
  width: 0.2
  notch_radius: 0.02
E:
  forward: "div(sigma) = f,  radial return for J2"
  youngs_modulus: 210.0e9
  poisson: 0.3
  yield_stress: 250.0e6
  hardening: {type: linear, H: 1.0e9}
B:
  left: {u_x: 0}
  right: {traction: [500e6, 0]}   # above yield
I:
  scenario: notched_tensile
  load_steps: 20
  mesh_sizes: [16x8, 32x16, 64x32]
O: [L2_displacement_error, plastic_zone_error, load_displacement_curve]
epsilon:
  L2_error_max: 5.0e-3
  plastic_zone_accuracy: 0.95
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Mesh refined near notch; 20 load steps for path accuracy | PASS |
| S2 | Well-posed for monotonic loading with linear hardening | PASS |
| S3 | Radial return + global Newton converges in ≤ 10 iterations/step | PASS |
| S4 | L2 error < 5×10⁻³ at 64×32 mesh | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# j2_plasticity/benchmark_notched_bar.yaml
spec_ref: sha256:<spec216_hash>
principle_ref: sha256:<p216_hash>
dataset:
  name: notched_bar_tensile
  reference: "de Souza Neto et al. — computational plasticity benchmarks"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-Q4 (32×16)
    params: {h: 1/32, load_steps: 20}
    results: {L2_error: 8.5e-3, plastic_zone_acc: 0.91}
  - solver: FEM-Q8 (32×16)
    params: {h: 1/32, load_steps: 20}
    results: {L2_error: 2.1e-3, plastic_zone_acc: 0.96}
  - solver: FEM-Q8 (64×32)
    params: {h: 1/64, load_steps: 20}
    results: {L2_error: 5.5e-4, plastic_zone_acc: 0.98}
quality_scoring:
  - {min_L2: 5.0e-4, Q: 1.00}
  - {min_L2: 2.0e-3, Q: 0.90}
  - {min_L2: 5.0e-3, Q: 0.80}
  - {min_L2: 1.0e-2, Q: 0.75}
```

**Baseline solver:** FEM-Q8 (32×16) — L2 error 2.1×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Plastic Zone | Runtime | Q |
|--------|----------|--------------|---------|---|
| FEM-Q4 (32×16) | 8.5e-3 | 91% | 15 s | 0.75 |
| FEM-Q8 (32×16) | 2.1e-3 | 96% | 45 s | 0.90 |
| FEM-Q8 (64×32) | 5.5e-4 | 98% | 180 s | 1.00 |
| FEM-Q8 + adaptive | 3.0e-4 | 99% | 120 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (adaptive): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p216_hash>",
  "h_s": "sha256:<spec216_hash>",
  "h_b": "sha256:<bench216_hash>",
  "r": {"residual_norm": 3.0e-4, "error_bound": 5.0e-3, "ratio": 0.06},
  "c": {"fitted_rate": 1.52, "theoretical_rate": 1.5, "K": 3},
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
pwm-node benchmarks | grep j2_plasticity
pwm-node verify j2_plasticity/notched_bar_s1_ideal.yaml
pwm-node mine j2_plasticity/notched_bar_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
