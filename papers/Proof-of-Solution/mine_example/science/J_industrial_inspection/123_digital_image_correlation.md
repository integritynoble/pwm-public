# Principle #123 — Digital Image Correlation (DIC)

**Domain:** Industrial Inspection & NDE | **Carrier:** Visible Photon | **Difficulty:** Textbook (δ=1)
**DAG:** L.warp --> N.bilinear --> integral.spatial | **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.warp-->N.bilinear-->integral.spatial    DIC         TensileStrain-50   Correlate
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  DIGITAL IMAGE CORRELATION (DIC)  P = (E, G, W, C)  #123       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ g(x') = f(x' − u(x')); minimize Σ[g(x+u) − f(x)]²  │
│        │ u = displacement field; ε = ∂u/∂x (strain)            │
│        │ Speckle pattern provides unique local texture          │
│        │ Inverse: recover u(x,y) by subpixel cross-correlation │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.warp] --> [N.bilinear] --> [integral.spatial]         │
│        │  Deformation  Interpolate  Correlate                   │
│        │ V={L.warp, N.bilinear, integral.spatial}  A={L.warp-->N.bilinear, N.bilinear-->integral.spatial}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (speckle provides trackable features)   │
│        │ Uniqueness: YES (adequate speckle density assumed)      │
│        │ Stability: κ ≈ 3 (good speckle), κ ≈ 20 (poor)       │
│        │ Mismatch: out-of-plane motion, lighting change         │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = displacement RMSE px (primary), strain RMSE (sec.) │
│        │ q = 2.0 (Newton-Raphson subpixel convergence)         │
│        │ T = {displacement_RMSE, strain_RMSE, spatial_res}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Speckle size ≈ 3–5 px; subset size captures sufficient texture | PASS |
| S2 | Cross-correlation peak unique; subpixel interpolation bounded | PASS |
| S3 | Newton-Raphson converges for smooth displacement fields | PASS |
| S4 | Displacement RMSE ≤ 0.02 px for rigid-body translation test | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# dic/tensilestrain_s1.yaml
principle_ref: sha256:<p123_hash>
omega:
  camera: [4096, 3000]
  pixel_mm: 0.05
  subset_px: 21
  step_px: 5
  speckle_size_px: 4
E:
  forward: "g(x) = f(x - u(x)) + n"
  correlation: "ZNSSD (zero-normalized SSD)"
I:
  dataset: TensileStrain_50
  pairs: 50
  material: [steel, aluminum, composite]
  noise: {type: gaussian, SNR_dB: 45}
O: [displacement_RMSE_px, strain_RMSE]
epsilon:
  disp_RMSE_max: 0.02
  strain_RMSE_max: 100e-6
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Subset 21 px contains ≈ 25 speckles at 4 px speckle size | PASS |
| S2 | ZNSSD robust to lighting changes; unique minimum guaranteed | PASS |
| S3 | Newton-Raphson converges in ≤ 20 iterations per subset | PASS |
| S4 | Displacement RMSE ≤ 0.02 px feasible at SNR=45 dB | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# dic/benchmark_s1.yaml
spec_ref: sha256:<spec123_hash>
principle_ref: sha256:<p123_hash>
dataset:
  name: TensileStrain_50
  pairs: 50
  size: [4096, 3000]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Integer-CC
    params: {search_px: 20}
    results: {disp_RMSE: 0.50, strain_RMSE: 500e-6}
  - solver: ZNSSD-Subpixel
    params: {subset: 21, interp: bicubic}
    results: {disp_RMSE: 0.015, strain_RMSE: 80e-6}
  - solver: Global-DIC (FE)
    params: {mesh_size: 10}
    results: {disp_RMSE: 0.010, strain_RMSE: 50e-6}
quality_scoring:
  - {max_disp_RMSE: 0.010, Q: 1.00}
  - {max_disp_RMSE: 0.020, Q: 0.90}
  - {max_disp_RMSE: 0.050, Q: 0.80}
  - {max_disp_RMSE: 0.100, Q: 0.75}
```

**Baseline solver:** Integer-CC — RMSE 0.50 px
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Disp RMSE (px) | Strain RMSE (με) | Runtime | Q |
|--------|----------------|-------------------|---------|---|
| Integer-CC | 0.500 | 500 | 0.5 s | 0.75 |
| ZNSSD-Subpixel | 0.015 | 80 | 5 s | 0.92 |
| Global-DIC (FE) | 0.010 | 50 | 20 s | 1.00 |
| DL-FlowNet-DIC | 0.012 | 60 | 1 s | 0.95 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (Global-DIC):  100 × 1.00 = 100 PWM
Floor:                   100 × 0.75 =  75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p123_hash>",
  "h_s": "sha256:<spec123_hash>",
  "h_b": "sha256:<bench123_hash>",
  "r": {"residual_norm": 0.010, "error_bound": 0.020, "ratio": 0.50},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep dic
pwm-node verify dic/tensilestrain_s1.yaml
pwm-node mine dic/tensilestrain_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
