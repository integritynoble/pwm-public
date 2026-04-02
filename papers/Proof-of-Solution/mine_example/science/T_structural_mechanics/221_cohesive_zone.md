# Principle #221 — Cohesive Zone Model (CZM)

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [L.stiffness] --> [N.pointwise.traction] --> [B.crack] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.stiffness→N.pointwise.traction→B.crack   CZM         DCB-delamination   FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  COHESIVE ZONE MODEL (CZM)        P = (E,G,W,C)  Principle #221│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ T(δ) = traction-separation law (bilinear, exponential) │
│        │ T_max = cohesive strength, G_c = fracture energy       │
│        │ δ_c = critical separation; damage D = δ_max/δ_c       │
│        │ Forward: given interface/BC/loads → crack path, P-δ    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.stiffness] --> [N.pointwise.traction] --> [B.crack]│
│        │ bulk-solve  traction-separation  cohesive-zone-BC      │
│        │ V={L.stiffness,N.pointwise.traction,B.crack}  L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (variational inequality with softening) │
│        │ Uniqueness: CONDITIONAL (snap-back possible)           │
│        │ Stability: mesh-dependent for strain softening; cohesive│
│        │   length l_cz must be resolved by ≥ 3 elements         │
│        │ Mismatch: T-S law shape, G_c calibration error         │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative error in G_c and peak load (primary)      │
│        │ q = 1.0 (interface elements); mesh in process zone    │
│        │ T = {load_disp_curve, G_c_error, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Traction-separation law thermodynamically consistent; G_c > 0 | PASS |
| S2 | Solution exists for monotonic loading; arc-length for snap-back | PASS |
| S3 | Cohesive elements with adequate process-zone resolution converge | PASS |
| S4 | G_c and peak load error bounded by mesh/process-zone resolution | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# czm/dcb_delamination_s1_ideal.yaml
principle_ref: sha256:<p221_hash>
omega:
  grid: [128, 8]
  domain: DCB_specimen
  length: 0.15
  arm_thickness: 0.003
  initial_crack: 0.05
E:
  forward: "Bilinear traction-separation law"
  T_max: 60.0e6   # Pa
  G_Ic: 280.0     # J/m²
  delta_c: 9.33e-6
B:
  left_end: {opening_displacement: controlled}
I:
  scenario: DCB_mode_I
  mesh_sizes: [32x2, 64x4, 128x8]
O: [peak_load_error, G_c_error, load_displacement_R_curve]
epsilon:
  peak_load_error: 2.0e-2
  G_c_error: 5.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Cohesive zone resolved by ≥ 5 elements at finest mesh | PASS |
| S2 | DCB test is standard CZM validation; LEFM G_c reference exists | PASS |
| S3 | Newton-Raphson with line-search converges for bilinear CZM | PASS |
| S4 | Peak load error < 2% at 128×8 mesh | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# czm/benchmark_dcb.yaml
spec_ref: sha256:<spec221_hash>
principle_ref: sha256:<p221_hash>
dataset:
  name: DCB_delamination
  reference: "ASTM D5528 + analytical beam-on-elastic-foundation"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM + bilinear CZM (64×4)
    params: {mesh: 64x4, arc_length: false}
    results: {peak_load_error: 5.5e-2, G_c_error: 8.0e-2}
  - solver: FEM + bilinear CZM (128×8)
    params: {mesh: 128x8, arc_length: true}
    results: {peak_load_error: 1.8e-2, G_c_error: 3.0e-2}
  - solver: FEM + exponential CZM (128×8)
    params: {mesh: 128x8, arc_length: true}
    results: {peak_load_error: 1.2e-2, G_c_error: 2.0e-2}
quality_scoring:
  - {min_err: 1.0e-2, Q: 1.00}
  - {min_err: 3.0e-2, Q: 0.90}
  - {min_err: 5.0e-2, Q: 0.80}
  - {min_err: 1.0e-1, Q: 0.75}
```

**Baseline solver:** FEM + bilinear CZM (128×8) — peak load error 1.8×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Peak Load Err | G_c Err | Runtime | Q |
|--------|---------------|---------|---------|---|
| Bilinear CZM (64×4) | 5.5e-2 | 8.0e-2 | 10 s | 0.80 |
| Bilinear CZM (128×8) | 1.8e-2 | 3.0e-2 | 40 s | 0.90 |
| Exponential CZM (128×8) | 1.2e-2 | 2.0e-2 | 45 s | 0.90 |
| PPR CZM (128×8) | 8.0e-3 | 1.5e-2 | 50 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (PPR):  300 × 1.00 = 300 PWM
Floor:            300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p221_hash>",
  "h_s": "sha256:<spec221_hash>",
  "h_b": "sha256:<bench221_hash>",
  "r": {"residual_norm": 8.0e-3, "error_bound": 2.0e-2, "ratio": 0.40},
  "c": {"fitted_rate": 1.02, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep cohesive_zone
pwm-node verify czm/dcb_delamination_s1_ideal.yaml
pwm-node mine czm/dcb_delamination_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
