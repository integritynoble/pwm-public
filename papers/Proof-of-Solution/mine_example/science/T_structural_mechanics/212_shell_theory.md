# Principle #212 — Shell Theory (Koiter/Naghdi)

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [L.stiffness] --> [B.dirichlet] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.stiffness→B.dirichlet      shell-KN    Scordelis-Lo-roof  FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SHELL THEORY (KOITER/NAGHDI)      P = (E,G,W,C)  Principle #212│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Membrane: Eh/(1−ν²) [εαβ + ν εγγ δαβ] = Nαβ          │
│        │ Bending:  D κ_αβ + transverse shear (Naghdi)           │
│        │ Coupled membrane-bending on curved surface S            │
│        │ Forward: given geometry/BC/loads → solve for (u,θ)     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.stiffness] --> [B.dirichlet]                      │
│        │ shell-stiffness-assemble  clamped-BC                   │
│        │ V={L.stiffness,B.dirichlet}  L_DAG=1.0               │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Koiter energy functional; H¹×H¹)      │
│        │ Uniqueness: YES (adequate BCs on inextensional modes)  │
│        │ Stability: κ depends on R/h ratio; locking risk        │
│        │ Mismatch: curvature approx., thickness variation       │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖u−u_ref‖/‖u_ref‖ (primary)    │
│        │ q = 2.0 (MITC shell), curved geometry adds complexity │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Membrane/bending coupling consistent; surface parametrisation valid | PASS |
| S2 | Koiter/Naghdi theory well-posed for adequate boundary conditions | PASS |
| S3 | MITC shell elements converge without membrane/shear locking | PASS |
| S4 | Relative L2 error bounded by shell a priori estimates | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# shell/scordelis_lo_s1_ideal.yaml
principle_ref: sha256:<p212_hash>
omega:
  geometry: cylindrical_roof
  radius: 25.0
  length: 50.0
  angle: 80_deg
  thickness: 0.25
E:
  forward: "Koiter-Naghdi shell equations"
  E_modulus: 4.32e8
  poisson: 0.0
B:
  diaphragm_ends: {u_x: 0, u_z: 0}
  curved_edges: free
I:
  scenario: Scordelis_Lo_roof
  load: gravity_90_per_area
  mesh_sizes: [8x8, 16x16, 32x32]
O: [vertical_displacement_at_midpoint, L2_error, energy_norm_error]
epsilon:
  displacement_error_max: 1.0e-2
  energy_error_max: 5.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Cylindrical geometry properly parametrised; mesh distortion minimal | PASS |
| S2 | Scordelis-Lo is a standard shell benchmark with known reference | PASS |
| S3 | MITC4 shell elements converge for this benchmark | PASS |
| S4 | Displacement error < 1% at 32×32 mesh | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# shell/benchmark_scordelis_lo.yaml
spec_ref: sha256:<spec212_hash>
principle_ref: sha256:<p212_hash>
dataset:
  name: Scordelis_Lo_roof
  reference: "MacNeal & Harder (1985) standard shell benchmarks"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-MITC4
    params: {mesh: 16x16}
    results: {midpoint_disp: 0.3006, L2_error: 8.2e-3}
  - solver: FEM-MITC9
    params: {mesh: 8x8}
    results: {midpoint_disp: 0.3013, L2_error: 3.5e-3}
  - solver: FEM-MITC4 (32x32)
    params: {mesh: 32x32}
    results: {midpoint_disp: 0.3023, L2_error: 1.1e-3}
quality_scoring:
  - {min_L2: 5.0e-4, Q: 1.00}
  - {min_L2: 2.0e-3, Q: 0.90}
  - {min_L2: 1.0e-2, Q: 0.80}
  - {min_L2: 5.0e-2, Q: 0.75}
```

**Baseline solver:** FEM-MITC4 (16×16) — L2 error 8.2×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Midpoint w | Runtime | Q |
|--------|----------|------------|---------|---|
| FEM-MITC4 (16×16) | 8.2e-3 | 0.3006 | 5 s | 0.80 |
| FEM-MITC9 (8×8) | 3.5e-3 | 0.3013 | 8 s | 0.90 |
| FEM-MITC4 (32×32) | 1.1e-3 | 0.3023 | 20 s | 0.90 |
| IGA-NURBS (p=4) | 3.0e-4 | 0.3024 | 15 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (IGA):  300 × 1.00 = 300 PWM
Floor:            300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p212_hash>",
  "h_s": "sha256:<spec212_hash>",
  "h_b": "sha256:<bench212_hash>",
  "r": {"residual_norm": 3.0e-4, "error_bound": 1.0e-2, "ratio": 0.03},
  "c": {"fitted_rate": 2.10, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep shell_koiter
pwm-node verify shell/scordelis_lo_s1_ideal.yaml
pwm-node mine shell/scordelis_lo_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
