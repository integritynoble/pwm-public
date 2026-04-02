# Principle #220 — Linear Elastic Fracture Mechanics (LEFM)

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [L.stiffness] --> [N.sif] --> [B.crack] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.stiffness→N.sif→B.crack LEFM        edge-crack-plate   FEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LINEAR ELASTIC FRACTURE MECH.     P = (E,G,W,C)  Principle #220│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ σ_ij ~ K_I / √(2πr) f_ij(θ)  (near-tip asymptotic)   │
│        │ G = K_I² / E'  (energy release rate, plane strain)     │
│        │ Fracture criterion: K_I ≥ K_Ic (fracture toughness)   │
│        │ Forward: given crack/BC/loads → K_I, G               │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.stiffness] --> [N.sif] --> [B.crack]             │
│        │ stiffness-solve  SIF-extract  crack-tip-BC             │
│        │ V={L.stiffness,N.sif,B.crack}  L_DAG=3.0              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear elasticity with crack; H¹ minus │
│        │   tip singularity)                                      │
│        │ Uniqueness: YES (linear problem for given crack geom)  │
│        │ Stability: SIF sensitive to crack length; ∂K/∂a > 0   │
│        │ Mismatch: crack geometry error, material K_Ic error    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative SIF error |K−K_ref|/K_ref (primary)      │
│        │ q = 1.0 (standard FEM), 2.0 (quarter-point elements) │
│        │ T = {SIF_error, J_integral, K_resolutions}             │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Stress intensity factor dimensions [Pa√m] consistent | PASS |
| S2 | Williams eigenfunction expansion provides exact near-tip field | PASS |
| S3 | J-integral / interaction integral extracts K_I accurately | PASS |
| S4 | SIF error bounded by mesh refinement and contour independence | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# lefm/edge_crack_plate_s1_ideal.yaml
principle_ref: sha256:<p220_hash>
omega:
  grid: [64, 64]
  domain: rectangular_plate
  width: 1.0
  height: 2.0
  crack_length: 0.5
E:
  forward: "Linear elasticity + SIF extraction"
  youngs_modulus: 210.0e9
  poisson: 0.3
  plane: strain
B:
  top: {traction: [0, 100.0e6]}
  bottom: {traction: [0, -100.0e6]}
  crack_faces: {traction: [0, 0]}
I:
  scenario: mode_I_edge_crack
  a_over_W: [0.2, 0.3, 0.5]
  mesh_sizes: [32x32, 64x64, 128x128]
O: [K_I_error, J_integral_error, crack_opening_displacement]
epsilon:
  K_I_error_max: 1.0e-2
  J_error_max: 2.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Mesh refined near crack tip; quarter-point elements used | PASS |
| S2 | Tada handbook solutions provide exact K_I reference | PASS |
| S3 | J-integral path-independent; converges with refinement | PASS |
| S4 | K_I error < 1% at 128×128 mesh | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# lefm/benchmark_edge_crack.yaml
spec_ref: sha256:<spec220_hash>
principle_ref: sha256:<p220_hash>
dataset:
  name: edge_crack_SIF
  reference: "Tada, Paris & Irwin — Stress Analysis of Cracks Handbook"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-Q8 + J-integral
    params: {h: 1/32, quarter_point: true}
    results: {K_I_error: 2.5e-2, J_error: 3.0e-2}
  - solver: FEM-Q8 + J-integral (fine)
    params: {h: 1/64, quarter_point: true}
    results: {K_I_error: 6.0e-3, J_error: 8.0e-3}
  - solver: FEM-Q8 + interaction integral
    params: {h: 1/64, quarter_point: true}
    results: {K_I_error: 3.5e-3, J_error: 5.0e-3}
quality_scoring:
  - {min_K_err: 2.0e-3, Q: 1.00}
  - {min_K_err: 1.0e-2, Q: 0.90}
  - {min_K_err: 3.0e-2, Q: 0.80}
  - {min_K_err: 5.0e-2, Q: 0.75}
```

**Baseline solver:** FEM-Q8 + interaction integral — K_I error 3.5×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | K_I Error | J Error | Runtime | Q |
|--------|-----------|---------|---------|---|
| FEM-Q8 + J (h=1/32) | 2.5e-2 | 3.0e-2 | 10 s | 0.80 |
| FEM-Q8 + J (h=1/64) | 6.0e-3 | 8.0e-3 | 40 s | 0.90 |
| FEM-Q8 + interaction | 3.5e-3 | 5.0e-3 | 45 s | 0.90 |
| XFEM + interaction | 1.5e-3 | 2.0e-3 | 30 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (XFEM):  300 × 1.00 = 300 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p220_hash>",
  "h_s": "sha256:<spec220_hash>",
  "h_b": "sha256:<bench220_hash>",
  "r": {"residual_norm": 1.5e-3, "error_bound": 1.0e-2, "ratio": 0.15},
  "c": {"fitted_rate": 1.05, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep lefm
pwm-node verify lefm/edge_crack_plate_s1_ideal.yaml
pwm-node mine lefm/edge_crack_plate_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
