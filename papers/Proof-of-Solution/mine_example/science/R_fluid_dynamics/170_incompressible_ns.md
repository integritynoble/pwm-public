# Principle #170 — Incompressible Navier-Stokes

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.bilinear.advection] --> [L.poisson] --> [B.wall] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.bilinear.advection→L.poisson→B.wall      NS-incomp   lid-driven-2D     FEM/FVM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  INCOMPRESSIBLE NAVIER-STOKES   P = (E,G,W,C)   Principle #170 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂u/∂t + (u·∇)u = −∇p/ρ + ν∇²u + f                    │
│        │ ∇·u = 0  (continuity / incompressibility)              │
│        │ u = velocity, p = pressure, ν = kinematic viscosity    │
│        │ Forward: given IC/BC/ν/f → solve for (u,p) over Ω×[0,T]│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.bilinear.advection] --> [L.poisson] --> [B.wall]│
│        │ time-step  advection  pressure-solve  wall-BC                   │
│        │ V={∂.time,N.bilinear.advection,L.poisson,B.wall}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Leray-Hopf weak solutions in 2D/3D)   │
│        │ Uniqueness: YES in 2D; OPEN in 3D (millennium problem) │
│        │ Stability: κ depends on Re; κ ~ Re for laminar flows   │
│        │ Mismatch: viscosity error, inlet BC perturbation       │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖u−u_ref‖/‖u_ref‖ (primary)    │
│        │ q = 2.0 (FEM-P2/P1), 1.0 (FVM-upwind)               │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Velocity/pressure dimensions consistent; divergence-free constraint well-formed | PASS |
| S2 | Leray-Hopf theory guarantees weak solutions; inf-sup stable discretizations exist | PASS |
| S3 | FEM (Taylor-Hood), FVM (SIMPLE), projection methods converge for Re < 10⁴ | PASS |
| S4 | Relative L2 error bounded by mesh-dependent a priori estimates | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# ns_incomp/lid_driven_s1_ideal.yaml
principle_ref: sha256:<p170_hash>
omega:
  grid: [128, 128]
  domain: unit_square
  time: [0, 10.0]
  dt: 0.01
E:
  forward: "∂u/∂t + (u·∇)u = −∇p + ν∇²u,  ∇·u = 0"
  viscosity: 0.01   # Re = 100
B:
  top_wall: {u: [1.0, 0.0]}   # lid velocity
  other_walls: {u: [0.0, 0.0]}  # no-slip
I:
  scenario: lid_driven_cavity
  Re: 100
  mesh_sizes: [32, 64, 128]
O: [L2_velocity_error, max_error, pressure_L2]
epsilon:
  L2_error_max: 1.0e-3
  divergence_max: 1.0e-10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid 128² adequate for Re=100; dt satisfies CFL | PASS |
| S2 | Re=100 well within laminar regime; unique steady state exists | PASS |
| S3 | Taylor-Hood FEM converges at O(h²) for velocity | PASS |
| S4 | L2 error < 10⁻³ achievable at h=1/128 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# ns_incomp/benchmark_lid_driven.yaml
spec_ref: sha256:<spec170_hash>
principle_ref: sha256:<p170_hash>
dataset:
  name: Ghia_lid_driven_Re100
  reference: "Ghia et al. (1982) centerline velocity profiles"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-P2P1 (Taylor-Hood)
    params: {h: 1/64, dt: 0.01, method: Chorin_projection}
    results: {L2_error: 2.1e-3, max_error: 5.3e-3}
  - solver: FVM-SIMPLE
    params: {h: 1/64, relaxation: 0.7}
    results: {L2_error: 3.8e-3, max_error: 9.1e-3}
  - solver: Spectral (Chebyshev-tau)
    params: {N: 64}
    results: {L2_error: 4.2e-5, max_error: 1.1e-4}
quality_scoring:
  - {min_L2: 1.0e-5, Q: 1.00}
  - {min_L2: 1.0e-4, Q: 0.90}
  - {min_L2: 1.0e-3, Q: 0.80}
  - {min_L2: 5.0e-3, Q: 0.75}
```

**Baseline solver:** FEM-P2P1 — L2 error 2.1×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Max Error | Runtime | Q |
|--------|----------|-----------|---------|---|
| FVM-SIMPLE | 3.8e-3 | 9.1e-3 | 12 s | 0.80 |
| FEM-P2P1 | 2.1e-3 | 5.3e-3 | 18 s | 0.80 |
| FEM-P2P1 (h=1/128) | 5.2e-4 | 1.3e-3 | 90 s | 0.90 |
| Spectral (N=64) | 4.2e-5 | 1.1e-4 | 5 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (spectral): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p170_hash>",
  "h_s": "sha256:<spec170_hash>",
  "h_b": "sha256:<bench170_hash>",
  "r": {"residual_norm": 4.2e-5, "error_bound": 1.0e-3, "ratio": 0.042},
  "c": {"fitted_rate": 1.98, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep ns_incomp
pwm-node verify ns_incomp/lid_driven_s1_ideal.yaml
pwm-node mine ns_incomp/lid_driven_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
