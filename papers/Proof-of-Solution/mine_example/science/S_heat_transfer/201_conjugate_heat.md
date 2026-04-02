# Principle #201 — Conjugate Heat Transfer

**Domain:** Heat Transfer | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [∂.space.laplacian] --> [B.interface] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→∂.space.laplacian→B.interface   CHT         heated-fin-2D     FVM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CONJUGATE HEAT TRANSFER   P = (E,G,W,C)   Principle #201       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Fluid: ρcₚ(∂T/∂t + u·∇T) = k_f∇²T                   │
│        │ Solid: ρₛcₛ ∂Tₛ/∂t = kₛ∇²Tₛ + Q                     │
│        │ Interface: T_f = T_s,  k_f∂T_f/∂n = kₛ∂Tₛ/∂n        │
│        │ Forward: fluid flow + solid → coupled T(x,t)          │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [∂.space.laplacian] --> [B.interface]    │
│        │ time  thermal-diffusion  solid-fluid-interface-BC     │
│        │ V={∂.time,∂.space.laplacian,B.interface}  L_DAG=1.0   │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (coupled parabolic system)              │
│        │ Uniqueness: YES (interface continuity well-posed)     │
│        │ Stability: k_s/k_f ratio affects convergence rate     │
│        │ Mismatch: contact resistance, k_s uncertainty         │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = T_solid L2 error, interface heat flux error        │
│        │ q = 2.0 (FVM/FEM)                                     │
│        │ T = {T_error, flux_continuity_error, Nu_error}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Fluid-solid coupling via continuity + flux balance at interface | PASS |
| S2 | Coupled system well-posed; interface conditions matched | PASS |
| S3 | Partitioned or monolithic solver converges | PASS |
| S4 | Interface temperature error bounded by mesh size | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# cht/heated_fin_s1.yaml
principle_ref: sha256:<p201_hash>
omega:
  grid: [200, 100]
  domain: {fluid: [0.2, 0.05], solid: fin_geometry}
  time: steady_state
E:
  forward: "coupled fluid energy + solid conduction"
  k_fluid: 0.026
  k_solid: 200
B:
  inlet: {u: 2.0, T: 300}
  fin_base: {T: 400}
  outlet: {zero_gradient: true}
I:
  scenario: heated_fin_crossflow
  Re: 500
  k_ratio: 7700
  mesh_sizes: [100x50, 200x100]
O: [T_solid_L2_error, interface_flux_error, fin_efficiency_error]
epsilon:
  T_error_max: 2.0e-2
  fin_eff_error_max: 3.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Fluid-solid mesh conforming at interface | PASS |
| S2 | k ratio 7700 manageable; Biot number finite | PASS |
| S3 | Partitioned CHT converges in < 50 coupling iterations | PASS |
| S4 | T error < 2% vs converged monolithic reference | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# cht/benchmark_fin.yaml
spec_ref: sha256:<spec201_hash>
principle_ref: sha256:<p201_hash>
dataset:
  name: CHT_fin_reference
  reference: "Conjugate heat transfer benchmark (Dorfman 2009)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: OpenFOAM-chtMultiRegionFoam
    params: {mesh: 200x100}
    results: {T_error: 1.8e-2, fin_eff_err: 2.5%}
  - solver: ANSYS-Fluent (coupled)
    params: {mesh: 200x100}
    results: {T_error: 1.5e-2, fin_eff_err: 2.1%}
  - solver: Monolithic FEM
    params: {mesh: 100x50}
    results: {T_error: 1.2e-2, fin_eff_err: 1.5%}
quality_scoring:
  - {min_T_err: 5.0e-3, Q: 1.00}
  - {min_T_err: 1.5e-2, Q: 0.90}
  - {min_T_err: 3.0e-2, Q: 0.80}
  - {min_T_err: 5.0e-2, Q: 0.75}
```

**Baseline solver:** Monolithic FEM — T error 1.2×10⁻²
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | T Error | Fin Eff Err | Runtime | Q |
|--------|---------|------------|---------|---|
| OpenFOAM CHT | 1.8e-2 | 2.5% | 60 s | 0.80 |
| Fluent (coupled) | 1.5e-2 | 2.1% | 45 s | 0.90 |
| Monolithic FEM | 1.2e-2 | 1.5% | 30 s | 0.90 |
| Monolithic (fine) | 4.5e-3 | 0.5% | 120 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case: 300 × 1.00 = 300 PWM
Floor:     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p201_hash>",
  "h_s": "sha256:<spec201_hash>",
  "h_b": "sha256:<bench201_hash>",
  "r": {"residual_norm": 4.5e-3, "error_bound": 2.0e-2, "ratio": 0.225},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 2},
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
pwm-node benchmarks | grep cht
pwm-node verify cht/heated_fin_s1.yaml
pwm-node mine cht/heated_fin_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
