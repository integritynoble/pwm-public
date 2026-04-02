# Principle #172 — Euler Equations (Inviscid Flow)

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.flux] --> [L.riemann] --> [B.reflective] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.flux→L.riemann→B.reflective        Euler       blast-wave-2D     FVM/DG
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  EULER EQUATIONS (INVISCID)   P = (E,G,W,C)   Principle #172    │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂U/∂t + ∇·F(U) = 0                                    │
│        │ U = (ρ, ρu, ρE)ᵀ   conservative variables             │
│        │ F = (ρu, ρu⊗u+pI, (ρE+p)u)ᵀ  flux tensor            │
│        │ EOS: p = (γ−1)(ρE − ½ρ|u|²)                          │
│        │ Forward: hyperbolic conservation law on Ω×[0,T]       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.flux] --> [L.riemann] --> [B.reflective]│
│        │ time-adv  flux-eval  Riemann-solve  reflective-BC       │
│        │ V={∂.time,N.flux,L.riemann,B.reflective}  L_DAG=3.0  │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (entropy weak solutions)                │
│        │ Uniqueness: YES with entropy condition (Lax, Oleinik)  │
│        │ Stability: TVD property under CFL condition            │
│        │ Mismatch: γ error, initial data perturbation           │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L1 error (natural for conservation laws)  │
│        │ q = 1.0 (near discontinuities), 2+ (smooth regions)  │
│        │ T = {L1_error, shock_speed_error, K_resolutions}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Conservative variables form hyperbolic system; EOS consistent | PASS |
| S2 | Entropy condition selects unique weak solution; Rankine-Hugoniot holds | PASS |
| S3 | Godunov, HLLC, Roe solvers converge; CFL-stable time stepping | PASS |
| S4 | L1 error bounded; convergence O(h) at shocks, O(h^k) smooth | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# euler/sedov_blast_s1.yaml
principle_ref: sha256:<p172_hash>
omega:
  grid: [200, 200]
  domain: [[0,1],[0,1]]
  time: [0, 0.5]
E:
  forward: "∂U/∂t + ∇·F(U) = 0, ideal gas γ=1.4"
  gamma: 1.4
B:
  type: reflective_all_walls
I:
  scenario: sedov_blast_2D
  IC: {point_energy: 1.0, ambient_rho: 1.0, ambient_p: 1e-5}
  mesh_sizes: [50, 100, 200]
O: [L1_density_error, shock_radius_error, symmetry_error]
epsilon:
  L1_error_max: 5.0e-2
  shock_radius_error_max: 0.02
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 2D grid; Sedov IC well-formed; point energy finite | PASS |
| S2 | Self-similar exact solution exists (Sedov-Taylor) | PASS |
| S3 | HLLC/Roe FVM converges; symmetry preserved on Cartesian grid | PASS |
| S4 | L1 error < 5×10⁻² achievable at 200² | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# euler/benchmark_sedov.yaml
spec_ref: sha256:<spec172_hash>
principle_ref: sha256:<p172_hash>
dataset:
  name: Sedov_exact_similarity
  reference: "Sedov (1959) self-similar solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FVM-HLLC (1st order)
    params: {N: 100x100}
    results: {L1_error: 7.2e-2, shock_radius_err: 0.015}
  - solver: FVM-MUSCL-HLLC
    params: {N: 100x100, limiter: vanLeer}
    results: {L1_error: 3.5e-2, shock_radius_err: 0.008}
  - solver: PPM (Piecewise Parabolic)
    params: {N: 100x100}
    results: {L1_error: 2.1e-2, shock_radius_err: 0.005}
quality_scoring:
  - {min_L1: 1.0e-2, Q: 1.00}
  - {min_L1: 3.0e-2, Q: 0.90}
  - {min_L1: 5.0e-2, Q: 0.80}
  - {min_L1: 8.0e-2, Q: 0.75}
```

**Baseline solver:** FVM-MUSCL-HLLC — L1 error 3.5×10⁻²
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L1 Error | Shock Radius Err | Runtime | Q |
|--------|----------|-------------------|---------|---|
| FVM-HLLC (1st) | 7.2e-2 | 0.015 | 5 s | 0.75 |
| FVM-MUSCL-HLLC | 3.5e-2 | 0.008 | 12 s | 0.90 |
| PPM | 2.1e-2 | 0.005 | 15 s | 0.90 |
| WENO-5 + HLLC | 8.5e-3 | 0.002 | 30 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case (WENO-5): 300 × 1.00 = 300 PWM
Floor:              300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p172_hash>",
  "h_s": "sha256:<spec172_hash>",
  "h_b": "sha256:<bench172_hash>",
  "r": {"residual_norm": 8.5e-3, "error_bound": 5.0e-2, "ratio": 0.17},
  "c": {"fitted_rate": 0.95, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep euler
pwm-node verify euler/sedov_blast_s1.yaml
pwm-node mine euler/sedov_blast_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
