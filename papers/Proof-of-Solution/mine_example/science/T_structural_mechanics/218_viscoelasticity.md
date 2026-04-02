# Principle #218 — Viscoelasticity (Maxwell/Kelvin-Voigt)

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [∂.time] --> [N.pointwise.hereditary] --> [L.stiffness] --> [B.dirichlet] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.pointwise.hereditary→L.stiffness→B.dirichlet      viscoelast  creep-relaxation   FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  VISCOELASTICITY (MAXWELL/K-V)     P = (E,G,W,C)  Principle #218│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ σ(t) = ∫₀ᵗ G(t−s) ε̇(s) ds  (hereditary integral)     │
│        │ G(t) = relaxation modulus (Prony series)               │
│        │ Maxwell: σ + (η/E)σ̇ = η ε̇                            │
│        │ Forward: given BC/G(t)/loads → solve for (u,σ)(x,t)   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] --> [N.pointwise.hereditary] --> [L.stiffness] --> [B.dirichlet]│
│        │ time  hereditary-integral  stiffness-solve  displacement-BC              │
│        │ V={∂.time,N.pointwise.hereditary,L.stiffness,B.dirichlet}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (positive relaxation modulus; Volterra) │
│        │ Uniqueness: YES (linear hereditary integral)           │
│        │ Stability: long-time decay governed by relaxation times│
│        │ Mismatch: Prony series truncation, temperature shift   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖u−u_ref‖/‖u_ref‖ (primary)    │
│        │ q = 2.0 (FEM-Q2) with time-stepping O(Δt)            │
│        │ T = {residual_norm, creep_compliance_err, K_resolutions}│
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Hereditary integral well-formed; Prony series positive-definite | PASS |
| S2 | Linear Volterra equation has unique solution for positive G(t) | PASS |
| S3 | Recursive algorithm avoids full history storage; FEM converges | PASS |
| S4 | L2 error bounded by space-time discretisation estimates | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# viscoelasticity/creep_relaxation_s1_ideal.yaml
principle_ref: sha256:<p218_hash>
omega:
  grid: [64, 32]
  domain: rectangular_bar
  time: [0, 100.0]
  dt: 0.1
E:
  forward: "sigma = integral G(t-s) deps/ds ds"
  prony_series:
    - {G_i: 0.5e9, tau_i: 1.0}
    - {G_i: 0.3e9, tau_i: 10.0}
    - {G_i: 0.2e9, tau_i: 100.0}
  G_inf: 0.1e9
B:
  left: {u: [0,0]}
  right: {traction: [1.0e6, 0]}   # constant stress → creep
I:
  scenario: uniaxial_creep
  mesh_sizes: [16x8, 32x16, 64x32]
O: [L2_displacement_error, creep_compliance_error, relaxation_error]
epsilon:
  L2_error_max: 1.0e-3
  creep_error_max: 5.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Prony series covers relevant time scales; dt adequate | PASS |
| S2 | Linear viscoelastic problem; exact Prony-series solution exists | PASS |
| S3 | Recursive hereditary integral algorithm converges | PASS |
| S4 | L2 error < 10⁻³ at 64×32 mesh with dt=0.1 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# viscoelasticity/benchmark_creep.yaml
spec_ref: sha256:<spec218_hash>
principle_ref: sha256:<p218_hash>
dataset:
  name: prony_creep_analytical
  reference: "Analytical Prony-series creep compliance J(t)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-Q4 + recursive
    params: {h: 1/32, dt: 0.1}
    results: {L2_error: 3.5e-3, creep_error: 8.0e-3}
  - solver: FEM-Q8 + recursive
    params: {h: 1/32, dt: 0.1}
    results: {L2_error: 8.0e-4, creep_error: 2.0e-3}
  - solver: FEM-Q8 + recursive (fine dt)
    params: {h: 1/32, dt: 0.01}
    results: {L2_error: 2.5e-4, creep_error: 6.0e-4}
quality_scoring:
  - {min_L2: 2.0e-4, Q: 1.00}
  - {min_L2: 1.0e-3, Q: 0.90}
  - {min_L2: 5.0e-3, Q: 0.80}
  - {min_L2: 1.0e-2, Q: 0.75}
```

**Baseline solver:** FEM-Q8 + recursive — L2 error 8.0×10⁻⁴
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Creep Err | Runtime | Q |
|--------|----------|-----------|---------|---|
| FEM-Q4 + recursive | 3.5e-3 | 8.0e-3 | 20 s | 0.80 |
| FEM-Q8 + recursive | 8.0e-4 | 2.0e-3 | 60 s | 0.90 |
| FEM-Q8 (fine dt) | 2.5e-4 | 6.0e-4 | 300 s | 1.00 |
| Spectral + Prony | 5.0e-5 | 1.0e-4 | 45 s | 1.00 |

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
  "h_p": "sha256:<p218_hash>",
  "h_s": "sha256:<spec218_hash>",
  "h_b": "sha256:<bench218_hash>",
  "r": {"residual_norm": 5.0e-5, "error_bound": 1.0e-3, "ratio": 0.05},
  "c": {"fitted_rate": 2.01, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep viscoelasticity
pwm-node verify viscoelasticity/creep_relaxation_s1_ideal.yaml
pwm-node mine viscoelasticity/creep_relaxation_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
