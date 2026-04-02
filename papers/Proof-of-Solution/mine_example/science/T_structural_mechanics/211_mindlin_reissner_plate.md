# Principle #211 — Mindlin-Reissner Plate Theory

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Textbook (δ=1)
**DAG:** [L.stiffness] --> [B.dirichlet] |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.stiffness→B.dirichlet      MR-plate    thick-plate-2D     FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MINDLIN-REISSNER PLATE THEORY     P = (E,G,W,C)  Principle #211│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ D∇²∇²w component + shear: κGh(∇²w − ∇·θ) + q = 0    │
│        │ D(∇²θ + …) − κGh(∇w − θ) = 0                         │
│        │ w = deflection, θ = (θ_x, θ_y) independent rotations  │
│        │ Forward: given BC/D/κGh/q → solve for (w, θ)          │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.stiffness] --> [B.dirichlet]                      │
│        │ shear-deformable-stiffness  plate-BC                   │
│        │ V={L.stiffness,B.dirichlet}  L_DAG=1.0               │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (mixed variational formulation)         │
│        │ Uniqueness: YES (coercive bilinear form)               │
│        │ Stability: shear locking risk for thin plates          │
│        │ Mismatch: thickness error, shear correction factor     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖w−w_ref‖/‖w_ref‖ (primary)    │
│        │ q = 2.0 (MITC4), 1.0 (selective reduced integration) │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Coupled system consistent; independent rotations well-defined | PASS |
| S2 | Well-posed for clamped/simply-supported; inf-sup stable elements exist | PASS |
| S3 | MITC elements converge without shear locking for all thicknesses | PASS |
| S4 | Relative L2 error bounded by mesh-dependent a priori estimates | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# mindlin_reissner/thick_plate_s1_ideal.yaml
principle_ref: sha256:<p211_hash>
omega:
  grid: [32, 32]
  domain: unit_square
  thickness: 0.1   # moderately thick
E:
  forward: "Mindlin-Reissner coupled (w, theta_x, theta_y)"
  D: 1.0e3
  kappa_Gh: 5.0e4
B:
  all_edges: {w: 0, theta_n: 0}   # clamped
I:
  scenario: clamped_uniform_load
  thickness_ratios: [0.01, 0.05, 0.1, 0.2]
  mesh_sizes: [8, 16, 32]
O: [L2_deflection_error, L2_rotation_error, shear_force_error]
epsilon:
  L2_error_max: 1.0e-3
  rotation_error_max: 5.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Mesh adequate for thickness ratio; MITC element selected | PASS |
| S2 | Clamped plate has unique solution; reference from 3D elasticity | PASS |
| S3 | MITC4 converges locking-free across all thickness ratios | PASS |
| S4 | L2 error < 10⁻³ achievable at 32×32 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# mindlin_reissner/benchmark_thick_plate.yaml
spec_ref: sha256:<spec211_hash>
principle_ref: sha256:<p211_hash>
dataset:
  name: MR_plate_3D_reference
  reference: "3D elasticity FEM solution (fine mesh) as reference"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-Q4-full-integration
    params: {h: 1/16}
    results: {L2_error: 1.5e-1, note: "shear-locked for thin"}
  - solver: FEM-MITC4
    params: {h: 1/16}
    results: {L2_error: 2.8e-3, rotation_error: 5.5e-3}
  - solver: FEM-MITC9
    params: {h: 1/16}
    results: {L2_error: 3.5e-4, rotation_error: 8.0e-4}
quality_scoring:
  - {min_L2: 1.0e-4, Q: 1.00}
  - {min_L2: 1.0e-3, Q: 0.90}
  - {min_L2: 5.0e-3, Q: 0.80}
  - {min_L2: 1.0e-2, Q: 0.75}
```

**Baseline solver:** MITC4 — L2 error 2.8×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Max Error | Runtime | Q |
|--------|----------|-----------|---------|---|
| FEM-Q4-full | 1.5e-1 | 3.0e-1 | 2 s | — (locked) |
| FEM-MITC4 | 2.8e-3 | 7.0e-3 | 3 s | 0.80 |
| FEM-MITC9 | 3.5e-4 | 9.0e-4 | 8 s | 0.90 |
| FEM-MITC9 (h=1/32) | 8.5e-5 | 2.2e-4 | 30 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (MITC9 fine): 100 × 1.00 = 100 PWM
Floor:                  100 × 0.75 =  75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p211_hash>",
  "h_s": "sha256:<spec211_hash>",
  "h_b": "sha256:<bench211_hash>",
  "r": {"residual_norm": 8.5e-5, "error_bound": 1.0e-3, "ratio": 0.085},
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
| L4 Solution | — | 75–100 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep mindlin_reissner
pwm-node verify mindlin_reissner/thick_plate_s1_ideal.yaml
pwm-node mine mindlin_reissner/thick_plate_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
