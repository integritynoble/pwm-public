# Principle #76 — Panorama Multi-Focus Fusion

**Domain:** Computational Photography | **Carrier:** Photon | **Difficulty:** Moderate (δ=3)
**DAG:** L.diag --> K.psf --> integral.spatial | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │         L.diag-->K.psf-->integral.spatial    MFusion     MultiFocus-30     LapFuse
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PANORAMA MULTI-FOCUS FUSION   P = (E, G, W, C)   Principle #76 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y_k(r) = H_k(r) · x(r) + n_k(r),  k = 1..K           │
│        │ H_k = depth-dependent defocus blur at focus k           │
│        │ x = all-in-focus image; y_k = focal stack frames        │
│        │ Inverse: fuse {y_k} into all-in-focus composite x      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.diag] --> [K.psf] --> [integral.spatial]              │
│        │  FocusWeight  DefocusBlur  Blend                        │
│        │ V={L.diag, K.psf, integral.spatial}  A={L.diag-->K.psf, K.psf-->integral.spatial}   L_DAG=3.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (at least one frame sharp at each depth)│
│        │ Uniqueness: YES if focal stack covers full depth range  │
│        │ Stability: κ ≈ 5 (dense stack), κ ≈ 30 (sparse stack)  │
│        │ Mismatch: registration error, exposure variation        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), SSIM (secondary), Q_focus          │
│        │ q = 2.0 (Laplacian pyramid blending convergence)      │
│        │ T = {residual_norm, sharpness_metric, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Focal steps cover full scene depth; registration within 1 px | PASS |
| S2 | Each depth layer sharp in at least one frame → complete coverage | PASS |
| S3 | Laplacian pyramid blending converges; weight maps normalized | PASS |
| S4 | PSNR ≥ 32 dB achievable for well-aligned K ≥ 5 stack | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# multifocus/panorama_s1_ideal.yaml
principle_ref: sha256:<p076_hash>
omega:
  grid: [1024, 1024]
  pixel_um: 1.5
  focal_planes: 8
  depth_range_mm: [0, 50]
E:
  forward: "y_k = H_k · x + n_k"
  blur: "Depth-dependent Gaussian, σ_k per plane"
I:
  dataset: MultiFocus_30
  stacks: 30
  noise: {type: gaussian, sigma: 0.01}
  scenario: ideal
O: [PSNR, SSIM]
epsilon:
  PSNR_min: 32.0
  SSIM_min: 0.90
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 8 focal planes span 50 mm; pixel pitch 1.5 μm resolves features | PASS |
| S2 | κ ≈ 5 for 8-plane stack with full depth coverage | PASS |
| S3 | Laplacian pyramid converges at 1024×1024 resolution | PASS |
| S4 | PSNR ≥ 32 dB feasible with σ=0.01 noise | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# multifocus/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec076_hash>
principle_ref: sha256:<p076_hash>
dataset:
  name: MultiFocus_30
  stacks: 30
  size: [1024, 1024]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Max-Laplacian
    params: {window: 5}
    results: {PSNR: 31.5, SSIM: 0.89}
  - solver: Laplacian-Pyramid
    params: {levels: 6}
    results: {PSNR: 33.8, SSIM: 0.93}
  - solver: DeepFocus-Net
    params: {pretrained: true}
    results: {PSNR: 37.2, SSIM: 0.96}
quality_scoring:
  - {min: 37.0, Q: 1.00}
  - {min: 34.0, Q: 0.90}
  - {min: 32.0, Q: 0.80}
  - {min: 30.0, Q: 0.75}
```

**Baseline solver:** Laplacian-Pyramid — PSNR 33.8 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| Max-Laplacian | 31.5 | 0.89 | 0.2 s | 0.78 |
| Laplacian-Pyramid | 33.8 | 0.93 | 0.5 s | 0.88 |
| DeepFocus-Net | 37.2 | 0.96 | 1.5 s | 0.98 |
| GuidedFusion | 35.0 | 0.94 | 0.8 s | 0.92 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (DeepFocus-Net): 300 × 0.98 = 294 PWM
Floor:                     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p076_hash>",
  "h_s": "sha256:<spec076_hash>",
  "h_b": "sha256:<bench076_hash>",
  "r": {"residual_norm": 0.006, "error_bound": 0.02, "ratio": 0.30},
  "c": {"fitted_rate": 1.98, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.98,
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
| L4 Solution | — | 225–294 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep multifocus
pwm-node verify multifocus/panorama_s1_ideal.yaml
pwm-node mine multifocus/panorama_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
