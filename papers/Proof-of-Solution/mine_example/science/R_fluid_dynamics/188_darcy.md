# Principle #188 — Darcy Flow (Porous Media)

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Textbook (δ=1)
**DAG:** [∂.space.gradient] --> [L.sparse] --> [B.well] |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.space.gradient→L.sparse→B.well          Darcy       2D-heterogeneous  FEM/FVM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  DARCY FLOW   P = (E,G,W,C)   Principle #188                    │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ u = −(K/μ)∇p   (Darcy's law)                          │
│        │ ∇·u = q         (mass conservation)                    │
│        │ → −∇·(K/μ ∇p) = q   (pressure equation, elliptic)    │
│        │ K = permeability tensor, μ = viscosity                 │
│        │ Forward: given K(x), BC, q → solve for p on Ω         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.space.gradient] --> [L.sparse] --> [B.well]         │
│        │ pressure-gradient  elliptic-solve  well-BC              │
│        │ V={∂.space.gradient,L.sparse,B.well}  L_DAG=1.0       │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Lax-Milgram, K uniformly positive)    │
│        │ Uniqueness: YES (elliptic, coercive bilinear form)    │
│        │ Stability: κ depends on K contrast ratio               │
│        │ Mismatch: permeability K(x) uncertainty, anisotropy   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error in pressure, flux error          │
│        │ q = 2.0 (FEM-P1), 1.0 (FVM cell-centered)           │
│        │ T = {pressure_error, flux_error, K_resolutions}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Elliptic PDE well-formed; K SPD on Ω | PASS |
| S2 | Lax-Milgram guarantees unique solution in H¹ | PASS |
| S3 | FEM/FVM/MFEM converge; multigrid solvers efficient | PASS |
| S4 | A priori error ‖p−pₕ‖ ≤ Ch^(k+1)‖p‖_{k+1} | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# darcy/heterogeneous_2d_s1.yaml
principle_ref: sha256:<p188_hash>
omega:
  grid: [128, 128]
  domain: unit_square
E:
  forward: "−∇·(K∇p) = q"
  K: log_normal_field   # K_max/K_min ~ 10⁴
B:
  left: {p: 1.0}
  right: {p: 0.0}
  top_bottom: {flux: 0}
I:
  scenario: heterogeneous_darcy
  K_contrast: 1e4
  realizations: 10
  mesh_sizes: [32, 64, 128]
O: [L2_pressure_error, flux_error, effective_K_error]
epsilon:
  L2_error_max: 1.0e-3
  flux_error_max: 5.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid resolves K heterogeneity; contrast 10⁴ manageable | PASS |
| S2 | K > 0 everywhere; elliptic well-posedness maintained | PASS |
| S3 | MFEM preserves local flux conservation; multigrid converges | PASS |
| S4 | L2 error < 10⁻³ at h=1/128 for log-normal K | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# darcy/benchmark_heterogeneous.yaml
spec_ref: sha256:<spec188_hash>
principle_ref: sha256:<p188_hash>
dataset:
  name: SPE10_layer_Darcy
  reference: "SPE10 comparative solution project"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-P1
    params: {h: 1/64}
    results: {L2_error: 3.5e-3, flux_error: 8.2e-3}
  - solver: MFEM (RT0)
    params: {h: 1/64}
    results: {L2_error: 2.8e-3, flux_error: 1.5e-3}
  - solver: FVM (TPFA)
    params: {h: 1/64}
    results: {L2_error: 5.1e-3, flux_error: 4.2e-3}
quality_scoring:
  - {min_L2: 5.0e-4, Q: 1.00}
  - {min_L2: 2.0e-3, Q: 0.90}
  - {min_L2: 5.0e-3, Q: 0.80}
  - {min_L2: 1.0e-2, Q: 0.75}
```

**Baseline solver:** MFEM-RT0 — L2 error 2.8×10⁻³
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Flux Error | Runtime | Q |
|--------|----------|------------|---------|---|
| FVM-TPFA | 5.1e-3 | 4.2e-3 | 1 s | 0.80 |
| FEM-P1 | 3.5e-3 | 8.2e-3 | 2 s | 0.80 |
| MFEM-RT0 | 2.8e-3 | 1.5e-3 | 3 s | 0.90 |
| MFEM-RT0 (h=1/128) | 7.1e-4 | 3.8e-4 | 15 s | 0.90 |

### Reward Calculation

```
R = 100 × 1.0 × 1 × 1.0 × Q
Best case: 100 × 0.90 = 90 PWM
Floor:     100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p188_hash>",
  "h_s": "sha256:<spec188_hash>",
  "h_b": "sha256:<bench188_hash>",
  "r": {"residual_norm": 7.1e-4, "error_bound": 1.0e-3, "ratio": 0.71},
  "c": {"fitted_rate": 1.98, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.90,
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
| L4 Solution | — | 75–90 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep darcy
pwm-node verify darcy/heterogeneous_2d_s1.yaml
pwm-node mine darcy/heterogeneous_2d_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
