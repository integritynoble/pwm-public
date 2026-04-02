# Principle #479 — Liquid Crystal Modeling (Landau-de Gennes)

**Domain:** Polymer Physics / Soft Matter | **Carrier:** N/A (PDE-based) | **Difficulty:** Advanced (δ=4)
**DAG:** [N.pointwise] --> [∂.space] --> [L.dense] --> [B.surface] | **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pw-->∂.x-->L.dense-->B.surf  LC-LdG  defect-bench  FEM/FD
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LIQUID CRYSTAL (LANDAU-DE GENNES)  P=(E,G,W,C) Princ. #479    │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ F[Q] = ∫(f_bulk + f_elastic) dV + ∫ f_surface dS      │
│        │ f_bulk = a tr(Q²) − b tr(Q³) + c [tr(Q²)]²            │
│        │ f_elastic = L₁|∇Q|² (one-constant approx)             │
│        │ Q_ij = S(n_i n_j − δ_ij/3) + P(m_i m_j − δ_ij/3)    │
│        │ Forward: given (a,b,c,L₁,BC) → Q(r) equilibrium      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pw] ──→ [∂.x] ──→ [L.dense] ──→ [B.surf]            │
│        │  free-energy  gradient  elasticity  anchoring          │
│        │ V={N.pw,∂.x,L.dense,B.surf}  A={N.pw→∂.x,∂.x→L.dense,L.dense→B.surf}  L_DAG=3.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (minimizer of F[Q] in H¹)              │
│        │ Uniqueness: NO (multiple minima; defect topologies)    │
│        │ Stability: gradient flow L₂ → free energy decrease    │
│        │ Mismatch: one-constant approx; flexoelectric neglected │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |F−F_ref|/|F_ref| (free energy error)             │
│        │ q = 2.0 (FEM P2 elements)                            │
│        │ T = {free_energy_error, defect_position, S_profile}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Q symmetric traceless (5 DOF); free energy bounded below | PASS |
| S2 | Coercivity of F ensures minimizer existence in H¹ | PASS |
| S3 | Gradient flow + Newton-Raphson converges for defect problems | PASS |
| S4 | Free energy error bounded by O(h²) for P2 FEM | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# lc_ldg/saturn_ring_s1.yaml
principle_ref: sha256:<p479_hash>
omega:
  grid: [128, 128, 128]
  domain: sphere_in_nematic
  nematic_coherence: 10e-9   # m
E:
  forward: "Landau-de Gennes free energy minimization"
  a: -0.172e6     # Pa (thermotropic)
  b: -2.12e6
  c: 1.73e6
  L1: 4.0e-12     # N
B:
  particle: {radius: 1e-6, anchoring: homeotropic_strong}
  far_field: {type: uniform_director, n: [0,0,1]}
I:
  scenario: Saturn_ring_vs_hedgehog_defect
  particle_radii: [0.5e-6, 1e-6, 2e-6, 5e-6]
O: [free_energy, defect_type, defect_position]
epsilon:
  free_energy_tol: 1.0e-6
  Q_residual_max: 1.0e-8
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid 128³ resolves coherence length ξ ~ 10 nm | PASS |
| S2 | Homeotropic anchoring + far-field ensures well-posed BVP | PASS |
| S3 | Gradient descent + adaptive mesh converges | PASS |
| S4 | Free energy to 10⁻⁶ distinguishes Saturn ring from hedgehog | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# lc_ldg/benchmark_saturn.yaml
spec_ref: sha256:<spec479_hash>
principle_ref: sha256:<p479_hash>
dataset:
  name: Saturn_ring_defect_benchmark
  reference: "Ravnik & Zumer (2009) LdG defect modeling"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FD gradient flow
    params: {grid: 64^3, dt_relax: 0.1}
    results: {free_energy_error: 5.2e-4, defect_pos_error: 0.08}
  - solver: FEM P2 (adaptive)
    params: {elements: 50000, Newton: true}
    results: {free_energy_error: 8.5e-5, defect_pos_error: 0.02}
  - solver: FEM P2 (fine)
    params: {elements: 200000, Newton: true}
    results: {free_energy_error: 1.2e-5, defect_pos_error: 0.005}
quality_scoring:
  - {min_err: 1.0e-5, Q: 1.00}
  - {min_err: 1.0e-4, Q: 0.90}
  - {min_err: 1.0e-3, Q: 0.80}
  - {min_err: 1.0e-2, Q: 0.75}
```

**Baseline solver:** FEM P2 (adaptive) — free energy error 8.5×10⁻⁵
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | F Error | Defect Pos Error | Runtime | Q |
|--------|---------|-----------------|---------|---|
| FD gradient flow | 5.2e-4 | 0.08 | 300 s | 0.80 |
| FEM P2 (50k elem) | 8.5e-5 | 0.02 | 180 s | 0.90 |
| FEM P2 (200k elem) | 1.2e-5 | 0.005 | 900 s | 1.00 |
| GPU FD (256³) | 2.8e-5 | 0.01 | 60 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (fine FEM): 400 × 1.00 = 400 PWM
Floor:                400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p479_hash>",
  "h_s": "sha256:<spec479_hash>",
  "h_b": "sha256:<bench479_hash>",
  "r": {"free_energy_error": 1.2e-5, "error_bound": 1.0e-3, "ratio": 0.012},
  "c": {"defect_pos_error": 0.005, "elements": 200000, "K": 3},
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
pwm-node benchmarks | grep lc_ldg
pwm-node verify lc_ldg/saturn_ring_s1.yaml
pwm-node mine lc_ldg/saturn_ring_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
