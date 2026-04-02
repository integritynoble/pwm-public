# Principle #171 — Compressible Navier-Stokes

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.flux] --> [L.riemann] --> [B.farfield] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.flux→L.riemann→B.farfield      NS-comp     shock-tube-1D     FVM/DG
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  COMPRESSIBLE NAVIER-STOKES   P = (E,G,W,C)   Principle #171    │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂ρ/∂t + ∇·(ρu) = 0                                    │
│        │ ∂(ρu)/∂t + ∇·(ρu⊗u + pI) = ∇·τ + f                  │
│        │ ∂(ρE)/∂t + ∇·((ρE+p)u) = ∇·(τ·u − q) + f·u          │
│        │ EOS: p = (γ−1)ρe,  τ = μ(∇u+∇uᵀ−⅔(∇·u)I)           │
│        │ Forward: given IC/BC/μ/γ → solve (ρ,u,p,E) on Ω×[0,T]│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.flux] --> [L.riemann] --> [B.farfield]│
│        │ time-adv  flux-eval  Riemann-solve  farfield-BC        │
│        │ V={∂.time,N.flux,L.riemann,B.farfield}  L_DAG=3.0    │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (smooth solutions for short time)       │
│        │ Uniqueness: YES (smooth regime); entropy solutions     │
│        │   required for shocks                                   │
│        │ Stability: κ depends on Mach; shock-capturing needed   │
│        │ Mismatch: γ error, viscosity error, inlet conditions   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error in density/velocity/pressure     │
│        │ q = 2.0 (DG-P2), 1.0 (FVM-Roe, smooth regions)      │
│        │ T = {residual_norm, shock_location_error, K_resolutions}│
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Conservation variables (ρ,ρu,ρE) consistent; EOS closes system | PASS |
| S2 | Smooth solutions exist locally; entropy conditions select unique weak solution | PASS |
| S3 | Godunov-type FVM, DG methods converge; Roe/HLLC fluxes well-tested | PASS |
| S4 | L2 error bounded in smooth regions; shock location error O(h) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# ns_comp/sod_shock_tube_s1.yaml
principle_ref: sha256:<p171_hash>
omega:
  grid: [1000]
  domain: [0, 1]
  time: [0, 0.2]
E:
  forward: "compressible Euler + viscous terms"
  gamma: 1.4
  mu: 0.0   # inviscid limit for Sod problem
B:
  left: {rho: 1.0, u: 0.0, p: 1.0}
  right: {rho: 0.125, u: 0.0, p: 0.1}
  type: transmissive
I:
  scenario: sod_shock_tube
  mesh_sizes: [100, 500, 1000]
O: [L2_density_error, shock_position_error, max_error]
epsilon:
  L2_error_max: 5.0e-3
  shock_pos_error_max: 0.01
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1D grid adequate; Riemann initial data well-formed | PASS |
| S2 | Exact Riemann solution exists; entropy condition satisfied | PASS |
| S3 | Godunov/Roe FVM converges at O(h) near shocks | PASS |
| S4 | L2 error < 5×10⁻³ achievable at N=1000 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# ns_comp/benchmark_sod.yaml
spec_ref: sha256:<spec171_hash>
principle_ref: sha256:<p171_hash>
dataset:
  name: Sod_exact_solution
  reference: "Toro (2009) exact Riemann solver"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FVM-Roe (1st order)
    params: {N: 500}
    results: {L2_error: 8.2e-3, shock_pos_err: 0.005}
  - solver: FVM-MUSCL (2nd order)
    params: {N: 500, limiter: minmod}
    results: {L2_error: 3.1e-3, shock_pos_err: 0.002}
  - solver: DG-P2
    params: {N_elem: 200, limiter: TVB}
    results: {L2_error: 1.5e-3, shock_pos_err: 0.001}
quality_scoring:
  - {min_L2: 5.0e-4, Q: 1.00}
  - {min_L2: 2.0e-3, Q: 0.90}
  - {min_L2: 5.0e-3, Q: 0.80}
  - {min_L2: 1.0e-2, Q: 0.75}
```

**Baseline solver:** FVM-MUSCL — L2 error 3.1×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Shock Pos Error | Runtime | Q |
|--------|----------|-----------------|---------|---|
| FVM-Roe (1st) | 8.2e-3 | 0.005 | 0.5 s | 0.75 |
| FVM-MUSCL | 3.1e-3 | 0.002 | 1.2 s | 0.90 |
| DG-P2 | 1.5e-3 | 0.001 | 3.0 s | 0.90 |
| WENO-5 | 4.8e-4 | 0.0005 | 2.5 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (WENO-5): 300 × 1.00 = 300 PWM
Floor:              300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p171_hash>",
  "h_s": "sha256:<spec171_hash>",
  "h_b": "sha256:<bench171_hash>",
  "r": {"residual_norm": 4.8e-4, "error_bound": 5.0e-3, "ratio": 0.096},
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
pwm-node benchmarks | grep ns_comp
pwm-node verify ns_comp/sod_shock_tube_s1.yaml
pwm-node mine ns_comp/sod_shock_tube_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
