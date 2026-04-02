# Principle #208 — Euler-Bernoulli Beam

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Textbook (δ=1)
**DAG:** [∂.space.biharmonic] --> [B.dirichlet] |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.space.biharmonic→B.dirichlet          EB-beam     simply-supported  FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  EULER-BERNOULLI BEAM   P = (E,G,W,C)   Principle #208          │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ EI d⁴w/dx⁴ = q(x)   (static beam equation)          │
│        │ w = transverse deflection, q = distributed load        │
│        │ EI = flexural rigidity (E Young's, I moment of inertia)│
│        │ No shear deformation (thin beam assumption)            │
│        │ Forward: BC/EI/q → solve w(x) on [0,L]               │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.space.biharmonic] --> [B.dirichlet]                 │
│        │ biharmonic-operator  clamped/simply-supported-BC       │
│        │ V={∂.space.biharmonic,B.dirichlet}  L_DAG=1.0         │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (4th-order elliptic, well-posed)        │
│        │ Uniqueness: YES with 4 boundary conditions             │
│        │ Stability: κ ~ 1 for standard support conditions      │
│        │ Mismatch: EI variation, load uncertainty               │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = deflection L2 error, max deflection error          │
│        │ q = 4.0 (Hermite cubic FEM), 2.0 (C⁰ penalty)       │
│        │ T = {deflection_error, moment_error, K_mesh}          │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | 4th-order ODE; EI > 0; boundary conditions (4 total) specified | PASS |
| S2 | Unique solution for standard BCs (simply-supported, clamped, etc.) | PASS |
| S3 | Hermite cubic FEM converges at O(h⁴) | PASS |
| S4 | Exact solutions exist for uniform load, point load, etc. | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# eb_beam/simply_supported_s1.yaml
principle_ref: sha256:<p208_hash>
omega:
  grid: [100]
  domain: [0, 1]   # unit beam
E:
  forward: "EI w'''' = q"
  EI: 1.0
  q: 1.0   # uniform distributed load
B:
  left: {w: 0, M: 0}   # simply supported
  right: {w: 0, M: 0}
I:
  scenario: uniform_load_SS_beam
  mesh_sizes: [10, 25, 50, 100]
O: [deflection_L2_error, max_deflection_error, moment_error]
epsilon:
  L2_error_max: 1.0e-6
  max_deflection_error_max: 1.0e-5
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | SS beam; uniform load; EI constant | PASS |
| S2 | Exact: w = q/(24EI)(x⁴−2Lx³+L³x) | PASS |
| S3 | Hermite FEM converges at O(h⁴) | PASS |
| S4 | L2 error < 10⁻⁶ at N=100 elements | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# eb_beam/benchmark_ss.yaml
spec_ref: sha256:<spec208_hash>
principle_ref: sha256:<p208_hash>
dataset:
  name: EB_beam_exact
  reference: "Analytical w = q(x⁴−2Lx³+L³x)/(24EI)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Hermite cubic FEM
    params: {N: 10}
    results: {L2_error: 0.0, max_defl_err: 0.0}  # exact for cubic
  - solver: C0-penalty FEM (P2)
    params: {N: 25}
    results: {L2_error: 8.5e-5, max_defl_err: 1.2e-4}
  - solver: FDM (2nd order)
    params: {N: 100}
    results: {L2_error: 3.2e-5, max_defl_err: 5.5e-5}
quality_scoring:
  - {min_L2: 1.0e-8, Q: 1.00}
  - {min_L2: 1.0e-6, Q: 0.90}
  - {min_L2: 1.0e-4, Q: 0.80}
  - {min_L2: 1.0e-2, Q: 0.75}
```

**Baseline solver:** Hermite cubic FEM — exact (machine precision)
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Max Defl Err | Runtime | Q |
|--------|----------|-------------|---------|---|
| FDM (2nd) | 3.2e-5 | 5.5e-5 | 0.001 s | 0.90 |
| C0-penalty (P2) | 8.5e-5 | 1.2e-4 | 0.005 s | 0.80 |
| Hermite cubic | ~1e-15 | ~1e-15 | 0.001 s | 1.00 |
| IGA (p=4) | ~1e-12 | ~1e-12 | 0.002 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 1 × 1.0 × Q
Best case (Hermite): 100 × 1.00 = 100 PWM
Floor:               100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p208_hash>",
  "h_s": "sha256:<spec208_hash>",
  "h_b": "sha256:<bench208_hash>",
  "r": {"residual_norm": 1e-15, "error_bound": 1e-6, "ratio": 1e-9},
  "c": {"fitted_rate": 4.0, "theoretical_rate": 4.0, "K": 3},
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
pwm-node benchmarks | grep eb_beam
pwm-node verify eb_beam/simply_supported_s1.yaml
pwm-node mine eb_beam/simply_supported_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
