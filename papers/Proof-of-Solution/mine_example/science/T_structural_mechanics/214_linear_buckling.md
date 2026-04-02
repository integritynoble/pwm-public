# Principle #214 — Linear Buckling (Euler)

**Domain:** Structural Mechanics | **Carrier:** N/A (eigenvalue problem) | **Difficulty:** Textbook (δ=1)
**DAG:** [E.stability] --> [L.stiffness] |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E.stability→L.stiffness      buckling    column-Euler       FEM+eig
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LINEAR BUCKLING (EULER)           P = (E,G,W,C)  Principle #214│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ (K + λ K_G) φ = 0  (buckling eigenvalue problem)      │
│        │ K = elastic stiffness, K_G = geometric stiffness       │
│        │ λ = load multiplier (critical), φ = buckling mode      │
│        │ Forward: given K, K_G → solve for (λ_cr, φ)           │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [E.stability] --> [L.stiffness]                      │
│        │ buckling-eigenvalue  stiffness+geometric-assemble      │
│        │ V={E.stability,L.stiffness}  L_DAG=1.0               │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (symmetric generalized eigenvalue prob) │
│        │ Uniqueness: YES (eigenvalues real; smallest λ_cr unique)│
│        │ Stability: imperfection sensitivity near bifurcation   │
│        │ Mismatch: geometric imperfections, BC idealisation     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative error |λ_cr−λ_ref|/λ_ref (primary)       │
│        │ q = 2p (eigenvalue superconvergence)                  │
│        │ T = {critical_load_error, mode_shape, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | K, K_G symmetric; eigenvalue problem well-formed | PASS |
| S2 | Euler column formula P_cr = π²EI/L² provides exact reference | PASS |
| S3 | FEM converges for simply-supported column; analytical check | PASS |
| S4 | Critical load error bounded by mesh-dependent estimates | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# linear_buckling/euler_column_s1_ideal.yaml
principle_ref: sha256:<p214_hash>
omega:
  grid: [64]
  domain: column_1D
  length: 1.0
  cross_section: {b: 0.01, h: 0.01}
E:
  forward: "(K + lambda * K_G) * phi = 0"
  youngs_modulus: 210.0e9
  I: 8.33e-10   # bh³/12
B:
  both_ends: {pinned: true}   # simply supported
I:
  scenario: Euler_column
  mesh_sizes: [8, 16, 32, 64]
O: [critical_load_error, buckling_mode_L2_error]
epsilon:
  lambda_error_max: 1.0e-4
  mode_error_max: 1.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1D column mesh adequate; element length appropriate | PASS |
| S2 | Euler formula gives exact P_cr = π²EI/L²; unique first mode | PASS |
| S3 | Beam FEM with geometric stiffness converges rapidly | PASS |
| S4 | λ_cr error < 10⁻⁴ at N=64 elements | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# linear_buckling/benchmark_euler_column.yaml
spec_ref: sha256:<spec214_hash>
principle_ref: sha256:<p214_hash>
dataset:
  name: Euler_column_analytical
  reference: "P_cr = π²EI/L² (Euler 1744)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-Hermite (N=8)
    params: {N: 8}
    results: {lambda_error: 3.8e-3}
  - solver: FEM-Hermite (N=16)
    params: {N: 16}
    results: {lambda_error: 2.4e-4}
  - solver: FEM-Hermite (N=32)
    params: {N: 32}
    results: {lambda_error: 1.5e-5}
quality_scoring:
  - {min_err: 1.0e-5, Q: 1.00}
  - {min_err: 1.0e-4, Q: 0.95}
  - {min_err: 1.0e-3, Q: 0.90}
  - {min_err: 1.0e-2, Q: 0.80}
```

**Baseline solver:** FEM-Hermite (N=16) — λ_cr error 2.4×10⁻⁴
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | λ_cr Error | Mode Error | Runtime | Q |
|--------|------------|------------|---------|---|
| FEM-Hermite (N=8) | 3.8e-3 | 5.0e-3 | 0.01 s | 0.90 |
| FEM-Hermite (N=16) | 2.4e-4 | 3.0e-4 | 0.02 s | 0.95 |
| FEM-Hermite (N=32) | 1.5e-5 | 2.0e-5 | 0.03 s | 1.00 |
| Exact (analytical) | 0.0 | 0.0 | 0.001 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (exact):  100 × 1.00 = 100 PWM
Floor:              100 × 0.80 =  80 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p214_hash>",
  "h_s": "sha256:<spec214_hash>",
  "h_b": "sha256:<bench214_hash>",
  "r": {"residual_norm": 1.5e-5, "error_bound": 1.0e-4, "ratio": 0.15},
  "c": {"fitted_rate": 4.01, "theoretical_rate": 4.0, "K": 3},
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
| L4 Solution | — | 80–100 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep linear_buckling
pwm-node verify linear_buckling/euler_column_s1_ideal.yaml
pwm-node mine linear_buckling/euler_column_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
