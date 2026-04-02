# Principle #477 — Viscoelastic Fluid Models (Oldroyd-B)

**Domain:** Polymer Physics | **Carrier:** N/A (PDE-based) | **Difficulty:** Advanced (δ=4)
**DAG:** [∂.time] --> [N.bilinear] --> [∂.space] --> [B.wall] | **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.t-->N.bilin-->∂.x-->B.wall  OldroydB  4:1-contraction  FEM/log-conf
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  VISCOELASTIC FLUID (OLDROYD-B)  P = (E,G,W,C) Principle #477  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ρ(∂u/∂t + u·∇u) = −∇p + ∇·τ_s + ∇·τ_p + f           │
│        │ ∇·u = 0   (incompressibility)                          │
│        │ τ_p + λ₁ τ̊_p = η_p(∇u + ∇uᵀ) (upper-convected deriv)│
│        │ τ̊_p = ∂τ_p/∂t + u·∇τ_p − (∇u)τ_p − τ_p(∇u)ᵀ       │
│        │ Forward: given (λ₁,η_s,η_p,BC) → (u,p,τ_p)          │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.t] ──→ [N.bilin] ──→ [∂.x] ──→ [B.wall]             │
│        │  time-step  advection  FEM-disc  wall-BC               │
│        │ V={∂.t,N.bilin,∂.x,B.wall}  A={∂.t→N.bilin,N.bilin→∂.x,∂.x→B.wall}  L_DAG=3.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (local in time; global for small Wi)    │
│        │ Uniqueness: YES for small Weissenberg number           │
│        │ Stability: HWNP at high Wi; log-conformation helps    │
│        │ Mismatch: Oldroyd-B predicts infinite extension        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖u−u_ref‖/‖u_ref‖ (velocity L2 error)           │
│        │ q = 2.0 (FEM with SUPG/log-conf)                     │
│        │ T = {velocity_L2, stress_L2, pressure_drop}            │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Stress tensor symmetric; constitutive eq frame-invariant | PASS |
| S2 | Well-posed for Wi < O(1); log-conformation extends range | PASS |
| S3 | Log-conformation FEM converges up to Wi ~ 5 in contraction | PASS |
| S4 | Velocity L2 error bounded by mesh-dependent estimates | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# oldroyd_b/contraction_s1.yaml
principle_ref: sha256:<p477_hash>
omega:
  grid: [200, 50]
  domain: 4to1_planar_contraction
  time: [0, 50.0]    # relaxation times
  dt: 0.01
E:
  forward: "Oldroyd-B + Stokes momentum + log-conformation"
  lambda_1: 1.0      # relaxation time
  eta_s: 0.59        # solvent viscosity
  eta_p: 0.41        # polymer viscosity
  beta: 0.59         # viscosity ratio
B:
  inlet: {type: parabolic, U_mean: 1.0}
  outlet: {type: traction_free}
  walls: no_slip
I:
  scenario: 4to1_contraction_Oldroyd_B
  Wi_values: [0.5, 1.0, 2.0, 3.0, 5.0]
O: [velocity_L2, stress_L2, corner_vortex_size]
epsilon:
  velocity_L2_max: 1.0e-2
  stress_L2_max: 5.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Mesh 200×50 resolves corner singularity; dt=0.01 stable | PASS |
| S2 | β=0.59 standard benchmark; Wi ≤ 5 with log-conf | PASS |
| S3 | Log-conformation FEM converges for all listed Wi | PASS |
| S4 | Velocity L2 < 1% on refined mesh | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# oldroyd_b/benchmark_contraction.yaml
spec_ref: sha256:<spec477_hash>
principle_ref: sha256:<p477_hash>
dataset:
  name: Contraction_flow_Oldroyd_B
  reference: "Alves et al. (2003) 4:1 contraction benchmark"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: SUPG-FEM
    params: {mesh: 200x50, Wi: 1.0}
    results: {velocity_L2: 2.5e-2, stress_L2: 8.1e-2}
  - solver: Log-conformation FEM
    params: {mesh: 200x50, Wi: 1.0}
    results: {velocity_L2: 8.5e-3, stress_L2: 3.2e-2}
  - solver: Log-conformation FEM (fine)
    params: {mesh: 400x100, Wi: 1.0}
    results: {velocity_L2: 2.1e-3, stress_L2: 9.5e-3}
quality_scoring:
  - {min_L2: 1.0e-3, Q: 1.00}
  - {min_L2: 5.0e-3, Q: 0.90}
  - {min_L2: 1.0e-2, Q: 0.80}
  - {min_L2: 5.0e-2, Q: 0.75}
```

**Baseline solver:** Log-conformation FEM — velocity L2 8.5×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Vel L2 | Stress L2 | Runtime | Q |
|--------|--------|-----------|---------|---|
| SUPG-FEM | 2.5e-2 | 8.1e-2 | 60 s | 0.75 |
| Log-conf (200×50) | 8.5e-3 | 3.2e-2 | 120 s | 0.80 |
| Log-conf (400×100) | 2.1e-3 | 9.5e-3 | 600 s | 0.90 |
| Log-conf (800×200) | 5.5e-4 | 2.8e-3 | 3600 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (fine): 400 × 1.00 = 400 PWM
Floor:            400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p477_hash>",
  "h_s": "sha256:<spec477_hash>",
  "h_b": "sha256:<bench477_hash>",
  "r": {"velocity_L2": 5.5e-4, "error_bound": 1.0e-2, "ratio": 0.055},
  "c": {"fitted_rate": 1.96, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 300–400 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep oldroyd_b
pwm-node verify oldroyd_b/contraction_s1.yaml
pwm-node mine oldroyd_b/contraction_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
