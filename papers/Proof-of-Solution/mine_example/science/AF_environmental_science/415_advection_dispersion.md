# Principle #415 — Advection-Dispersion (Pollutant Transport)

**Domain:** Environmental Science | **Carrier:** solute concentration | **Difficulty:** Standard (δ=3)
**DAG:** ∂.time → N.bilinear.advection → ∂.space.laplacian |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→∂.space.laplacian      ADE          river-plume       FVM/FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ADVECTION-DISPERSION EQUATION  P = (E,G,W,C)   Principle #415 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂C/∂t + u·∇C = ∇·(D∇C) − λC + S(x,t)               │
│        │ C = concentration, u = velocity field                   │
│        │ D = dispersion tensor, λ = decay rate                  │
│        │ Forward: given u, D, λ, S, IC/BC → C(x,t)            │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [N.bilinear.advection] ──→ [∂.space.laplacian] │
│        │ derivative  nonlinear  derivative                      │
│        │ V={∂.time, N.bilinear.advection, ∂.space.laplacian}  A={∂.time→N.bilinear.advection, N.bilinear.advection→∂.space.laplacian}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear parabolic PDE)                  │
│        │ Uniqueness: YES (unique for given IC/BC)               │
│        │ Stability: Peclet number Pe = uL/D governs stability   │
│        │ Mismatch: D estimation, velocity field uncertainty     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖C−C_ref‖/‖C_ref‖              │
│        │ q = 1.0 (upwind FVM), 2.0 (MUSCL), 2.0 (FEM)       │
│        │ T = {C_error, mass_conservation, peak_error}           │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Concentration, velocity, dispersion dimensions consistent | PASS |
| S2 | Linear parabolic PDE — well-posed by standard theory | PASS |
| S3 | FVM-upwind stable for all Pe; MUSCL reduces numerical diffusion | PASS |
| S4 | L2 error computable against analytic or high-resolution reference | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# advection_dispersion/river_plume_s1_ideal.yaml
principle_ref: sha256:<p415_hash>
omega:
  grid: [500]
  domain: river_reach_1D
  length: 10000   # m
  time: [0, 3600.0]   # s (1 hour)
  dt: 1.0
E:
  forward: "∂C/∂t + u ∂C/∂x = D ∂²C/∂x² − λC"
  u: 1.0   # m/s
  D: 10.0   # m²/s
  lambda: 0.0   # no decay
B:
  upstream: {C: 0.0}
  downstream: {dCdx: 0.0}
  initial: {pulse: {mass: 1000, x0: 1000}}
I:
  scenario: instantaneous_pulse_release
  Pe: 100
  mesh_sizes: [100, 250, 500]
O: [C_L2_error, peak_error, mass_conservation]
epsilon:
  C_error_max: 1.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 500 cells over 10 km; dt=1 s satisfies CFL for u=1 m/s | PASS |
| S2 | 1D ADE with pulse IC — analytic solution exists | PASS |
| S3 | FVM-MUSCL converges at O(h²) for smooth solutions | PASS |
| S4 | C error < 10⁻³ achievable at 500 cells | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# advection_dispersion/benchmark_river.yaml
spec_ref: sha256:<spec415_hash>
principle_ref: sha256:<p415_hash>
dataset:
  name: ADE_pulse_analytic
  reference: "Analytic 1D ADE pulse solution (Ogata-Banks)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FVM-upwind
    params: {N: 250, dt: 1.0}
    results: {C_error: 8.5e-3, mass_err: 1.0e-12}
  - solver: FVM-MUSCL
    params: {N: 250, dt: 1.0}
    results: {C_error: 1.2e-3, mass_err: 1.0e-12}
  - solver: DG-P1
    params: {N: 250, dt: 0.5}
    results: {C_error: 3.5e-4, mass_err: 1.0e-13}
quality_scoring:
  - {min_C_err: 1.0e-4, Q: 1.00}
  - {min_C_err: 1.0e-3, Q: 0.90}
  - {min_C_err: 5.0e-3, Q: 0.80}
  - {min_C_err: 1.0e-2, Q: 0.75}
```

**Baseline solver:** FVM-MUSCL — C error 1.2×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | C L2 Error | Mass Error | Runtime | Q |
|--------|-----------|-----------|---------|---|
| FVM-upwind | 8.5e-3 | 1.0e-12 | 0.5 s | 0.80 |
| FVM-MUSCL | 1.2e-3 | 1.0e-12 | 1 s | 0.90 |
| DG-P1 | 3.5e-4 | 1.0e-13 | 2 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (DG-P1): 300 × 1.00 = 300 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p415_hash>",
  "h_s": "sha256:<spec415_hash>",
  "h_b": "sha256:<bench415_hash>",
  "r": {"C_error": 3.5e-4, "mass_err": 1.0e-13, "ratio": 0.35},
  "c": {"fitted_rate": 2.05, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep advection_dispersion
pwm-node verify AF_environmental_science/advection_dispersion_s1_ideal.yaml
pwm-node mine AF_environmental_science/advection_dispersion_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
