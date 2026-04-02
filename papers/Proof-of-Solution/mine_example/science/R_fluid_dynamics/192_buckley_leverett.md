# Principle #192 — Buckley-Leverett (Two-Phase Immiscible)

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.flux.nonconvex] --> [B.dirichlet] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.flux.nonconvex→B.dirichlet        BL-2phase   waterflood-1D     FVM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  BUCKLEY-LEVERETT   P = (E,G,W,C)   Principle #192              │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ φ ∂S/∂t + ∂f(S)/∂x = 0                               │
│        │ f(S) = k_rw(S)/μ_w / [k_rw(S)/μ_w + k_ro(S)/μ_o]    │
│        │ (fractional flow, S-shaped with inflection point)      │
│        │ Hyperbolic conservation law with non-convex flux       │
│        │ Forward: IC/injection → solve S(x,t) saturation front │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.flux.nonconvex] --> [B.dirichlet]     │
│        │ time  fractional-flow-flux  injection-BC              │
│        │ V={∂.time,N.flux.nonconvex,B.dirichlet}  L_DAG=3.0    │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Oleinik entropy solution)              │
│        │ Uniqueness: YES with Oleinik entropy condition         │
│        │ Stability: CFL on max|f'(S)|; Welge tangent for shock │
│        │ Mismatch: relative perm curves, viscosity ratio       │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = saturation L1 error, front position error          │
│        │ q = 1.0 (near shock), 2.0 (rarefaction fan)         │
│        │ T = {L1_error, breakthrough_time_error, recovery_err} │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Non-convex flux f(S); fractional flow consistent with kr curves | PASS |
| S2 | Oleinik condition selects unique entropy solution; Welge construction | PASS |
| S3 | Godunov FVM converges; Engquist-Osher flux handles non-convexity | PASS |
| S4 | Saturation L1 error bounded; breakthrough time computable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# buckley_leverett/waterflood_1d_s1.yaml
principle_ref: sha256:<p192_hash>
omega:
  grid: [500]
  domain: [0, 1]
  time: [0, 0.5]   # PVI (pore volumes injected)
E:
  forward: "φ ∂S/∂t + ∂f(S)/∂x = 0"
  porosity: 0.2
  kr_model: Corey
  params: {n_w: 2, n_o: 2, S_wr: 0.2, S_or: 0.2}
  mu_w: 1.0e-3
  mu_o: 5.0e-3
B:
  inlet: {S: 1.0}   # water injection
  outlet: {zero_gradient: true}
  IC: {S: 0.2}      # connate water
I:
  scenario: waterflood_1D
  mobility_ratio: 5
  mesh_sizes: [100, 250, 500]
O: [L1_saturation_error, front_position_error, breakthrough_time_error]
epsilon:
  L1_error_max: 5.0e-3
  breakthrough_error_max: 2.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Corey kr valid; S ∈ [S_wr, 1−S_or]; f(S) S-shaped | PASS |
| S2 | Welge tangent gives shock saturation and speed | PASS |
| S3 | Engquist-Osher / Godunov FVM converges | PASS |
| S4 | L1 error < 5×10⁻³ at N=500 | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# buckley_leverett/benchmark_waterflood.yaml
spec_ref: sha256:<spec192_hash>
principle_ref: sha256:<p192_hash>
dataset:
  name: BL_Welge_exact
  reference: "Welge (1952) tangent construction"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FVM-Godunov (1st)
    params: {N: 500}
    results: {L1_error: 8.5e-3, front_err: 0.008}
  - solver: FVM-MUSCL (minmod)
    params: {N: 500}
    results: {L1_error: 3.2e-3, front_err: 0.003}
  - solver: DG-P1
    params: {N_elem: 250}
    results: {L1_error: 2.1e-3, front_err: 0.002}
quality_scoring:
  - {min_L1: 1.0e-3, Q: 1.00}
  - {min_L1: 3.0e-3, Q: 0.90}
  - {min_L1: 6.0e-3, Q: 0.80}
  - {min_L1: 1.0e-2, Q: 0.75}
```

**Baseline solver:** FVM-MUSCL — L1 error 3.2×10⁻³
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L1 Error | Front Error | Runtime | Q |
|--------|----------|------------|---------|---|
| FVM-Godunov | 8.5e-3 | 0.008 | 0.3 s | 0.75 |
| FVM-MUSCL | 3.2e-3 | 0.003 | 0.5 s | 0.90 |
| DG-P1 | 2.1e-3 | 0.002 | 1.0 s | 0.90 |
| WENO-5 | 8.2e-4 | 0.0008 | 1.5 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case (WENO-5): 300 × 1.00 = 300 PWM
Floor:              300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p192_hash>",
  "h_s": "sha256:<spec192_hash>",
  "h_b": "sha256:<bench192_hash>",
  "r": {"residual_norm": 8.2e-4, "error_bound": 5.0e-3, "ratio": 0.164},
  "c": {"fitted_rate": 0.98, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep buckley
pwm-node verify buckley_leverett/waterflood_1d_s1.yaml
pwm-node mine buckley_leverett/waterflood_1d_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
