# Principle #226 — Frictional Contact (Signorini + Coulomb)

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [L.stiffness] --> [N.pointwise] --> [B.contact] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.stiffness→N.pointwise→B.contact   fric-cont   block-on-plane     FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  FRICTIONAL CONTACT (SIGNORINI+C)  P = (E,G,W,C)  Principle #226│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Normal: g_N ≥ 0, p_N ≥ 0, g_N · p_N = 0 (Signorini) │
│        │ Tangential: |t_T| ≤ μ p_N (Coulomb friction)          │
│        │ Slip: |t_T| = μ p_N ⟹ ẋ_T = λ t_T/|t_T|             │
│        │ Forward: given bodies/μ/loads → contact state, u       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.stiffness] --> [N.pointwise] --> [B.contact]     │
│        │ stiffness-solve  friction-eval  contact-BC             │
│        │ V={L.stiffness,N.pointwise,B.contact}  L_DAG=3.0      │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (variational inequality; Fichera)       │
│        │ Uniqueness: CONDITIONAL (μ < μ_crit for uniqueness)   │
│        │ Stability: active-set changes cause non-smooth behavior│
│        │ Mismatch: friction coefficient μ, surface geometry     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative error in contact force and slip (primary) │
│        │ q = 1.5 (limited by contact non-smoothness)           │
│        │ T = {contact_force_error, slip_distance, K_resolutions}│
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | KKT complementarity conditions well-formed; μ ≥ 0 | PASS |
| S2 | Existence via Fichera's theorem; uniqueness for small μ | PASS |
| S3 | Semi-smooth Newton or augmented Lagrangian converges | PASS |
| S4 | Contact force error bounded; active set identified correctly | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# frictional_contact/block_on_plane_s1_ideal.yaml
principle_ref: sha256:<p226_hash>
omega:
  grid: [64, 32]
  domain: block_on_rigid_plane
  block_size: [0.1, 0.05]
E:
  forward: "Signorini + Coulomb variational inequality"
  youngs_modulus: 210.0e9
  poisson: 0.3
  friction_coeff: 0.3
B:
  top: {traction: [20.0e6, -50.0e6]}   # shear + normal
  bottom: rigid_plane
I:
  scenario: sliding_block
  mu_values: [0.1, 0.3, 0.5]
  mesh_sizes: [16x8, 32x16, 64x32]
O: [contact_force_error, slip_distance_error, contact_area_error]
epsilon:
  force_error_max: 2.0e-2
  slip_error_max: 5.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Mesh adequate in contact zone; penalty/mortar formulation used | PASS |
| S2 | Block-on-plane has analytical stick-slip solution for simple cases | PASS |
| S3 | Semi-smooth Newton converges for moderate μ | PASS |
| S4 | Contact force error < 2% at 64×32 mesh | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# frictional_contact/benchmark_block.yaml
spec_ref: sha256:<spec226_hash>
principle_ref: sha256:<p226_hash>
dataset:
  name: block_sliding_contact
  reference: "Wriggers (2006) — Computational Contact Mechanics benchmarks"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-penalty (32×16)
    params: {penalty: 1e11, mu: 0.3}
    results: {force_error: 5.0e-2, slip_error: 8.0e-2}
  - solver: FEM-mortar (32×16)
    params: {mortar: true, mu: 0.3}
    results: {force_error: 1.5e-2, slip_error: 3.0e-2}
  - solver: FEM-mortar (64×32)
    params: {mortar: true, mu: 0.3}
    results: {force_error: 4.0e-3, slip_error: 1.0e-2}
quality_scoring:
  - {min_err: 5.0e-3, Q: 1.00}
  - {min_err: 2.0e-2, Q: 0.90}
  - {min_err: 5.0e-2, Q: 0.80}
  - {min_err: 1.0e-1, Q: 0.75}
```

**Baseline solver:** FEM-mortar (32×16) — force error 1.5×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Force Err | Slip Err | Runtime | Q |
|--------|-----------|----------|---------|---|
| FEM-penalty (32×16) | 5.0e-2 | 8.0e-2 | 15 s | 0.80 |
| FEM-mortar (32×16) | 1.5e-2 | 3.0e-2 | 40 s | 0.90 |
| FEM-mortar (64×32) | 4.0e-3 | 1.0e-2 | 150 s | 1.00 |
| Semi-smooth Newton (64×32) | 3.0e-3 | 8.0e-3 | 120 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (SSN):  300 × 1.00 = 300 PWM
Floor:            300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p226_hash>",
  "h_s": "sha256:<spec226_hash>",
  "h_b": "sha256:<bench226_hash>",
  "r": {"residual_norm": 3.0e-3, "error_bound": 2.0e-2, "ratio": 0.15},
  "c": {"fitted_rate": 1.48, "theoretical_rate": 1.5, "K": 3},
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
pwm-node benchmarks | grep frictional_contact
pwm-node verify frictional_contact/block_on_plane_s1_ideal.yaml
pwm-node mine frictional_contact/block_on_plane_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
