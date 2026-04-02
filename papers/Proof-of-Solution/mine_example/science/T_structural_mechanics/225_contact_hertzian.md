# Principle #225 — Contact Mechanics (Hertzian)

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [L.stiffness] --> [N.pointwise.contact] --> [B.contact] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.stiffness→N.pointwise.contact→B.contact   Hertz       sphere-on-flat     FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CONTACT MECHANICS (HERTZIAN)      P = (E,G,W,C)  Principle #225│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ p(r) = p₀ √(1 − r²/a²)  (Hertzian pressure)          │
│        │ a = (3FR/4E*)^(1/3),  δ = a²/R                        │
│        │ E* = effective modulus, R = relative radius             │
│        │ Forward: given F/R/E* → solve for (p, a, δ)           │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.stiffness] --> [N.pointwise.contact] --> [B.contact]│
│        │ stiffness-solve  Hertz-contact-eval  contact-BC        │
│        │ V={L.stiffness,N.pointwise.contact,B.contact}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Signorini variational inequality)      │
│        │ Uniqueness: YES (monotone operator for frictionless)   │
│        │ Stability: κ depends on contact stiffness / penalty    │
│        │ Mismatch: surface roughness, penalty parameter choice  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative error in contact radius |a−a_ref|/a_ref  │
│        │ q = 2.0 (FEM-Q2); pressure convergence limited at edge│
│        │ T = {contact_area_error, pressure_error, K_resolutions}│
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Hertzian pressure profile dimensions consistent; elliptic distribution | PASS |
| S2 | Hertz theory provides exact solution for elastic sphere-on-flat | PASS |
| S3 | Penalty/Lagrange-multiplier contact FEM converges | PASS |
| S4 | Contact radius and pressure error bounded by mesh refinement | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# contact/sphere_on_flat_s1_ideal.yaml
principle_ref: sha256:<p225_hash>
omega:
  grid: [64, 64, 32]
  domain: half_space_3D
  sphere_radius: 0.01   # m
E:
  forward: "Elastic contact with Hertzian analytical solution"
  E_star: 115.4e9   # effective modulus
  poisson: 0.3
B:
  normal_load: {F: 100.0}   # N
  far_field: {u: [0,0,0]}
I:
  scenario: Hertzian_sphere_on_flat
  load_levels: [10, 50, 100, 500]   # N
  mesh_sizes: [16³, 32³, 64³]
O: [contact_radius_error, max_pressure_error, indentation_depth_error]
epsilon:
  radius_error_max: 1.0e-2
  pressure_error_max: 2.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Mesh refined in contact zone; penalty parameter calibrated | PASS |
| S2 | Hertz closed-form gives exact a, p₀, δ for sphere-on-flat | PASS |
| S3 | Augmented Lagrangian contact converges without penetration | PASS |
| S4 | Contact radius error < 1% at 64³ mesh | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# contact/benchmark_hertz.yaml
spec_ref: sha256:<spec225_hash>
principle_ref: sha256:<p225_hash>
dataset:
  name: Hertzian_contact
  reference: "Hertz (1881) — exact contact mechanics solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-penalty (32³)
    params: {h: 1/32, penalty: 1e12}
    results: {radius_error: 3.5e-2, pressure_error: 5.0e-2}
  - solver: FEM-augmented-Lagrange (32³)
    params: {h: 1/32, aug_iter: 5}
    results: {radius_error: 1.2e-2, pressure_error: 2.5e-2}
  - solver: FEM-augmented-Lagrange (64³)
    params: {h: 1/64, aug_iter: 5}
    results: {radius_error: 3.0e-3, pressure_error: 8.0e-3}
quality_scoring:
  - {min_err: 3.0e-3, Q: 1.00}
  - {min_err: 1.0e-2, Q: 0.90}
  - {min_err: 3.0e-2, Q: 0.80}
  - {min_err: 5.0e-2, Q: 0.75}
```

**Baseline solver:** FEM-augmented-Lagrange (32³) — radius error 1.2×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Radius Err | Press. Err | Runtime | Q |
|--------|------------|------------|---------|---|
| FEM-penalty (32³) | 3.5e-2 | 5.0e-2 | 30 s | 0.75 |
| FEM-aug-Lag (32³) | 1.2e-2 | 2.5e-2 | 60 s | 0.90 |
| FEM-aug-Lag (64³) | 3.0e-3 | 8.0e-3 | 300 s | 1.00 |
| BEM-Hertz (analytical) | 0.0 | 0.0 | 0.1 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (BEM):  300 × 1.00 = 300 PWM
Floor:            300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p225_hash>",
  "h_s": "sha256:<spec225_hash>",
  "h_b": "sha256:<bench225_hash>",
  "r": {"residual_norm": 3.0e-3, "error_bound": 1.0e-2, "ratio": 0.30},
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
pwm-node benchmarks | grep contact_hertz
pwm-node verify contact/sphere_on_flat_s1_ideal.yaml
pwm-node mine contact/sphere_on_flat_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
