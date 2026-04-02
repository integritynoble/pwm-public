# Principle #189 — Richards Equation (Unsaturated Flow)

**Domain:** Fluid Dynamics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.pointwise.vangenuchten] --> [∂.space.laplacian] --> [B.neumann] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.pointwise.vangenuchten→∂.space.laplacian→B.neumann      Richards    infiltration-1D   FEM/FVM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  RICHARDS EQUATION   P = (E,G,W,C)   Principle #189             │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂θ/∂t = ∇·[K(ψ)(∇ψ + ê_z)]                          │
│        │ θ = θ(ψ) via van Genuchten or Brooks-Corey             │
│        │ K = K_s · K_r(ψ) (relative permeability)              │
│        │ ψ = pressure head (matric potential)                   │
│        │ Forward: IC/BC/soil params → solve ψ(x,t) or θ(x,t)  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.pointwise.vangenuchten] --> [∂.space.laplacian] --> [B.neumann]│
│        │ time  nonlin-K(ψ)  diffusion  free-drainage-BC                                 │
│        │ V={∂.time,N.pointwise.vangenuchten,∂.space.laplacian,B.neumann}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (degenerate parabolic; entropy solutions)│
│        │ Uniqueness: YES under Kirchhoff transform              │
│        │ Stability: K(ψ) stiff near saturation; adaptive dt    │
│        │ Mismatch: van Genuchten α,n params, K_s uncertainty   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error in pressure head ψ               │
│        │ q = 2.0 (FEM), 1.0 (FVM cell-centered)              │
│        │ T = {infiltration_front_error, mass_balance, K_mesh}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | θ(ψ) monotone; K(ψ) > 0; mass conservation consistent | PASS |
| S2 | Kirchhoff transform regularizes; unique entropy solution | PASS |
| S3 | Modified Picard / Newton converge with line search | PASS |
| S4 | Error bounded by mesh size; mass balance < 10⁻⁸ achievable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# richards/infiltration_1d_s1.yaml
principle_ref: sha256:<p189_hash>
omega:
  grid: [200]
  domain: [0, 1]   # m depth
  time: [0, 3600]   # 1 hour
E:
  forward: "∂θ/∂t = ∂/∂z[K(ψ)(∂ψ/∂z + 1)]"
  soil: van_Genuchten
  params: {alpha: 3.35, n: 2.0, K_s: 9.22e-5, theta_s: 0.368, theta_r: 0.102}
B:
  top: {psi: -0.75}   # ponded infiltration
  bottom: {free_drainage: true}
I:
  scenario: vertical_infiltration
  soil_type: Haverkamp_sand
  mesh_sizes: [50, 100, 200]
O: [L2_psi_error, wetting_front_position_error, mass_balance]
epsilon:
  L2_error_max: 1.0e-2
  mass_balance_max: 1.0e-6
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1D vertical grid; van Genuchten params physically valid | PASS |
| S2 | Haverkamp solution exists for these parameters | PASS |
| S3 | Modified Picard converges in < 10 iterations per step | PASS |
| S4 | L2 error < 10⁻² at N=200 vs Haverkamp analytical | PASS |

**Layer 2 reward:** 105 PWM

---

## Layer 3 — spec → Benchmark

```yaml
# richards/benchmark_infiltration.yaml
spec_ref: sha256:<spec189_hash>
principle_ref: sha256:<p189_hash>
dataset:
  name: Haverkamp_infiltration_exact
  reference: "Haverkamp et al. (1977) analytical solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-P1 (mod. Picard)
    params: {N: 100, dt_adapt: true}
    results: {L2_error: 5.8e-3, mass_balance: 2.1e-8}
  - solver: FVM (cell-centered)
    params: {N: 100}
    results: {L2_error: 8.2e-3, mass_balance: 1.5e-7}
  - solver: HYDRUS-1D
    params: {N: 100}
    results: {L2_error: 4.5e-3, mass_balance: 5.3e-9}
quality_scoring:
  - {min_L2: 1.0e-3, Q: 1.00}
  - {min_L2: 5.0e-3, Q: 0.90}
  - {min_L2: 1.0e-2, Q: 0.80}
  - {min_L2: 2.0e-2, Q: 0.75}
```

**Baseline solver:** HYDRUS-1D — L2 error 4.5×10⁻³
**Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Mass Balance | Runtime | Q |
|--------|----------|-------------|---------|---|
| FVM (cell-centered) | 8.2e-3 | 1.5e-7 | 2 s | 0.80 |
| FEM-P1 (mod. Picard) | 5.8e-3 | 2.1e-8 | 3 s | 0.80 |
| HYDRUS-1D | 4.5e-3 | 5.3e-9 | 1 s | 0.90 |
| FEM-P2 (Newton, N=200) | 8.5e-4 | 3.2e-10 | 5 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best case (FEM-P2): 300 × 1.00 = 300 PWM
Floor:              300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p189_hash>",
  "h_s": "sha256:<spec189_hash>",
  "h_b": "sha256:<bench189_hash>",
  "r": {"residual_norm": 8.5e-4, "error_bound": 1.0e-2, "ratio": 0.085},
  "c": {"fitted_rate": 2.02, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep richards
pwm-node verify richards/infiltration_1d_s1.yaml
pwm-node mine richards/infiltration_1d_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
