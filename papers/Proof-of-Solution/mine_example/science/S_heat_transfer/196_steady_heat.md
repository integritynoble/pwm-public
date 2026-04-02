# Principle #196 — Steady-State Heat Conduction

**Domain:** Heat Transfer | **Carrier:** N/A (PDE-based) | **Difficulty:** Textbook (δ=1)
**DAG:** [∂.space.laplacian] --> [B.dirichlet] |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.space.laplacian→B.dirichlet          SteadyHeat  2D-composite      FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  STEADY-STATE HEAT CONDUCTION   P = (E,G,W,C)   Principle #196  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ −∇·(k∇T) = Q   (elliptic, Poisson-type)              │
│        │ k = k(x) spatially varying conductivity                │
│        │ Forward: given k(x),BC,Q → solve for T(x) on Ω       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.space.laplacian] --> [B.dirichlet]                  │
│        │ Laplacian-solve  temperature-BC                         │
│        │ V={∂.space.laplacian,B.dirichlet}  L_DAG=1.0          │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Lax-Milgram, k > 0)                   │
│        │ Uniqueness: YES (coercive, symmetric bilinear form)   │
│        │ Stability: κ depends on k_max/k_min contrast          │
│        │ Mismatch: k(x) uncertainty, interface conductance     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error in temperature                    │
│        │ q = 2.0 (FEM-P1), 4.0 (FEM-P2)                      │
│        │ T = {L2_error, heat_flux_error, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Elliptic PDE; k > 0; BC (Dirichlet/Neumann/Robin) consistent | PASS |
| S2 | Lax-Milgram guarantees unique solution in H¹ | PASS |
| S3 | FEM/FVM with direct or iterative solvers converge | PASS |
| S4 | A priori estimate ‖T−Tₕ‖ ≤ Ch^(k+1) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# steady_heat/composite_2d_s1.yaml
principle_ref: sha256:<p196_hash>
omega:
  grid: [128, 128]
  domain: unit_square
E:
  forward: "−∇·(k∇T) = 0"
  k: {region1: 1.0, region2: 100.0}   # k contrast 100:1
B:
  left: {T: 100.0}
  right: {T: 0.0}
  top_bottom: {flux: 0}
I:
  scenario: composite_wall_2D
  k_contrast: 100
  mesh_sizes: [32, 64, 128]
O: [L2_temperature_error, heat_flux_error, interface_accuracy]
epsilon:
  L2_error_max: 1.0e-4
  flux_error_max: 1.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 2D grid; k piecewise constant; interface well-defined | PASS |
| S2 | k > 0 everywhere; unique solution exists | PASS |
| S3 | FEM with interface-fitted mesh converges optimally | PASS |
| S4 | L2 error < 10⁻⁴ at h=1/128 | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# steady_heat/benchmark_composite.yaml
spec_ref: sha256:<spec196_hash>
principle_ref: sha256:<p196_hash>
dataset:
  name: Composite_wall_analytic
  reference: "Analytical 1D composite + 2D numerical reference"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-P1
    params: {h: 1/64}
    results: {L2_error: 3.2e-3, flux_error: 5.1e-3}
  - solver: FEM-P1 (interface-fitted)
    params: {h: 1/64}
    results: {L2_error: 8.5e-4, flux_error: 1.2e-3}
  - solver: FEM-P2
    params: {h: 1/64}
    results: {L2_error: 1.2e-5, flux_error: 3.5e-5}
quality_scoring:
  - {min_L2: 1.0e-5, Q: 1.00}
  - {min_L2: 1.0e-4, Q: 0.90}
  - {min_L2: 1.0e-3, Q: 0.80}
  - {min_L2: 5.0e-3, Q: 0.75}
```

**Baseline solver:** FEM-P1 interface-fitted — L2 error 8.5×10⁻⁴
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Flux Error | Runtime | Q |
|--------|----------|------------|---------|---|
| FEM-P1 | 3.2e-3 | 5.1e-3 | 0.5 s | 0.80 |
| FEM-P1 (fitted) | 8.5e-4 | 1.2e-3 | 0.8 s | 0.90 |
| FEM-P2 | 1.2e-5 | 3.5e-5 | 1.5 s | 0.90 |
| FEM-P2 (h=1/128) | 7.5e-7 | 2.1e-6 | 5 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 1 × 1.0 × Q
Best case: 100 × 1.00 = 100 PWM
Floor:     100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p196_hash>",
  "h_s": "sha256:<spec196_hash>",
  "h_b": "sha256:<bench196_hash>",
  "r": {"residual_norm": 7.5e-7, "error_bound": 1.0e-4, "ratio": 7.5e-3},
  "c": {"fitted_rate": 3.0, "theoretical_rate": 3.0, "K": 3},
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
pwm-node benchmarks | grep steady_heat
pwm-node verify steady_heat/composite_2d_s1.yaml
pwm-node mine steady_heat/composite_2d_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
