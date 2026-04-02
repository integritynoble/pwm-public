# Principle #222 — XFEM (Extended Finite Element for Cracks)

**Domain:** Structural Mechanics | **Carrier:** N/A (PDE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [L.sparse.fem] --> [N.sif] --> [B.crack] |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.sparse.fem→N.sif→B.crack XFEM        propagating-crack  XFEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  XFEM (EXTENDED FEM FOR CRACKS)    P = (E,G,W,C)  Principle #222│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ u^h = Σ N_i u_i + Σ N_j H(x) a_j + Σ N_k Σα Fα(r,θ) bkα│
│        │ H(x) = Heaviside enrichment (crack body)               │
│        │ Fα = crack-tip enrichment (√r sin/cos functions)       │
│        │ Forward: given crack/BC → u, σ, K_I, K_II without remesh│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.sparse.fem] --> [N.sif] --> [B.crack]            │
│        │ enriched-FEM-solve  SIF-extract  crack-BC              │
│        │ V={L.sparse.fem,N.sif,B.crack}  L_DAG=3.0             │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (partition of unity + enrichment)       │
│        │ Uniqueness: YES (linear enriched system for given crack)│
│        │ Stability: blending elements need care; conditioning   │
│        │ Mismatch: level-set crack geometry, enrichment radius  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative SIF error |K−K_ref|/K_ref (primary)      │
│        │ q = 2.0 (with tip enrichment), 0.5 (without tip)     │
│        │ T = {SIF_error, crack_path_error, K_resolutions}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Enrichment functions span crack-tip asymptotic field | PASS |
| S2 | Partition of unity ensures approximation completeness | PASS |
| S3 | XFEM converges at optimal rate with tip enrichment | PASS |
| S4 | SIF error bounded by enrichment radius and mesh size | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# xfem/propagating_crack_s1_ideal.yaml
principle_ref: sha256:<p222_hash>
omega:
  grid: [64, 64]
  domain: square_plate
  size: 1.0
E:
  forward: "XFEM enriched FEM + level-set crack representation"
  youngs_modulus: 210.0e9
  poisson: 0.3
  enrichment: {tip: branch_functions, body: Heaviside}
B:
  top: {traction: [0, 50.0e6]}
  bottom: {u: [0, 0]}
I:
  scenario: mixed_mode_crack_propagation
  initial_crack: {start: [0, 0.5], length: 0.3, angle: 0}
  mesh_sizes: [32x32, 64x64, 128x128]
O: [K_I_error, K_II_error, crack_path_error]
epsilon:
  SIF_error_max: 2.0e-2
  path_error_max: 5.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Level-set correctly tracks crack; enrichment radius adequate | PASS |
| S2 | Reference SIF from fine-mesh conventional FEM with remeshing | PASS |
| S3 | XFEM converges without remeshing; SIF via interaction integral | PASS |
| S4 | SIF error < 2% at 128×128 mesh | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# xfem/benchmark_propagating_crack.yaml
spec_ref: sha256:<spec222_hash>
principle_ref: sha256:<p222_hash>
dataset:
  name: mixed_mode_crack_prop
  reference: "Moës et al. (1999) XFEM benchmarks"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: XFEM-linear (32×32)
    params: {mesh: 32x32, tip_enrichment: true}
    results: {K_I_error: 5.2e-2, K_II_error: 7.0e-2}
  - solver: XFEM-linear (64×64)
    params: {mesh: 64x64, tip_enrichment: true}
    results: {K_I_error: 1.5e-2, K_II_error: 2.0e-2}
  - solver: XFEM-quadratic (64×64)
    params: {mesh: 64x64, tip_enrichment: true}
    results: {K_I_error: 5.0e-3, K_II_error: 8.0e-3}
quality_scoring:
  - {min_err: 5.0e-3, Q: 1.00}
  - {min_err: 2.0e-2, Q: 0.90}
  - {min_err: 5.0e-2, Q: 0.80}
  - {min_err: 1.0e-1, Q: 0.75}
```

**Baseline solver:** XFEM-linear (64×64) — K_I error 1.5×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | K_I Error | K_II Error | Runtime | Q |
|--------|-----------|------------|---------|---|
| XFEM-lin (32×32) | 5.2e-2 | 7.0e-2 | 5 s | 0.80 |
| XFEM-lin (64×64) | 1.5e-2 | 2.0e-2 | 20 s | 0.90 |
| XFEM-quad (64×64) | 5.0e-3 | 8.0e-3 | 35 s | 1.00 |
| XFEM-quad (128×128) | 1.2e-3 | 2.0e-3 | 140 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (quad fine): 300 × 1.00 = 300 PWM
Floor:                 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p222_hash>",
  "h_s": "sha256:<spec222_hash>",
  "h_b": "sha256:<bench222_hash>",
  "r": {"residual_norm": 1.2e-3, "error_bound": 2.0e-2, "ratio": 0.06},
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
| L4 Solution | — | 225–300 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep xfem
pwm-node verify xfem/propagating_crack_s1_ideal.yaml
pwm-node mine xfem/propagating_crack_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
