# Principle #83 — 3D Gaussian Splatting (3DGS)

**Domain:** Computational Optics & Neural Rendering | **Carrier:** Photon | **Difficulty:** Research (δ=8)
**DAG:** K.psf.gaussian --> integral.volume --> Pi.perspective | **Reward:** 8× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │         K.psf.gaussian-->integral.volume-->Pi.perspective    3DGS        MipNeRF360-9      3DGS-Adam
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  3D GAUSSIAN SPLATTING   P = (E, G, W, C)   Principle #83       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ C(p) = Σ_i c_i · α_i · G(p; μ_i, Σ_i) · Π_{j<i}(1−α_j)│
│        │ G = 3D Gaussian projected to 2D via EWA splatting       │
│        │ {μ_i, Σ_i, c_i, α_i} = learnable per-Gaussian params   │
│        │ Inverse: optimize Gaussians to match multi-view images  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.psf.gaussian] --> [integral.volume] --> [Pi.perspective]│
│        │  GaussSplat  AlphaComposite  PerspProject               │
│        │ V={K.psf.gaussian, integral.volume, Pi.perspective}  A={K.psf.gaussian-->integral.volume, integral.volume-->Pi.perspective}   L_DAG=6.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (differentiable alpha-compositing)       │
│        │ Uniqueness: conditional (Gaussian count unbounded)       │
│        │ Stability: κ ≈ 20 (dense init), κ ≈ 150 (random init)  │
│        │ Mismatch: SfM init errors, exposure inconsistency        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), SSIM, LPIPS (secondary)            │
│        │ q = 1.5 (Adam on L1+SSIM loss convergence)            │
│        │ T = {residual_norm, novel_view_PSNR, K_resolutions}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | SfM point cloud initializes Gaussians; camera poses calibrated | PASS |
| S2 | Densification + pruning → stable Gaussian count; unique rendering | PASS |
| S3 | Adam optimizer on L1+D-SSIM converges within 30k steps | PASS |
| S4 | PSNR ≥ 30 dB on novel views; real-time rendering at 100+ FPS | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# 3dgs/mipnerf360_s1_ideal.yaml
principle_ref: sha256:<p083_hash>
omega:
  image_res: [1600, 900]
  train_views: 200
  test_views: 50
  init: SfM_points
  max_gaussians: 3000000
E:
  forward: "C(p) = Σ α_i·G_i·Π(1−α_j)  (alpha compositing)"
  model: "Anisotropic 3D Gaussians with SH color"
I:
  dataset: MipNeRF360_9
  scenes: 9
  noise: {type: real_capture}
  scenario: ideal
O: [PSNR, SSIM, LPIPS]
epsilon:
  PSNR_min: 27.0
  SSIM_min: 0.85
  LPIPS_max: 0.15
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200 train views at 1600×900; SfM initialization | PASS |
| S2 | Adaptive densification/pruning → κ ≈ 20 | PASS |
| S3 | Adam converges in 30k steps with densify schedule | PASS |
| S4 | PSNR ≥ 27 dB feasible on outdoor 360° scenes | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# 3dgs/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec083_hash>
principle_ref: sha256:<p083_hash>
dataset:
  name: MipNeRF360_9
  scenes: 9
  image_size: [1600, 900]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: 3DGS-Original
    params: {iterations: 30000, densify_until: 15000}
    results: {PSNR: 27.5, SSIM: 0.870, LPIPS: 0.130}
  - solver: Mip-Splatting
    params: {iterations: 30000, 3D_filter: true}
    results: {PSNR: 28.2, SSIM: 0.880, LPIPS: 0.115}
  - solver: Scaffold-GS
    params: {iterations: 30000, anchor_growing: true}
    results: {PSNR: 28.8, SSIM: 0.895, LPIPS: 0.100}
quality_scoring:
  - {min: 29.0, Q: 1.00}
  - {min: 28.0, Q: 0.90}
  - {min: 27.0, Q: 0.80}
  - {min: 25.5, Q: 0.75}
```

**Baseline solver:** 3DGS-Original — PSNR 27.5 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PSNR (dB) | SSIM | LPIPS | FPS | Q |
|--------|-----------|------|-------|-----|---|
| 3DGS-Original | 27.5 | 0.870 | 0.130 | 134 | 0.82 |
| Mip-Splatting | 28.2 | 0.880 | 0.115 | 120 | 0.90 |
| Scaffold-GS | 28.8 | 0.895 | 0.100 | 105 | 0.95 |
| GaussianPro | 29.3 | 0.905 | 0.088 | 98 | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 8 × 1.0 × Q
Best case (GaussianPro): 800 × 1.00 = 800 PWM
Floor:                   800 × 0.75 = 600 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p083_hash>",
  "h_s": "sha256:<spec083_hash>",
  "h_b": "sha256:<bench083_hash>",
  "r": {"residual_norm": 0.006, "error_bound": 0.018, "ratio": 0.33},
  "c": {"fitted_rate": 1.45, "theoretical_rate": 1.5, "K": 4},
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
| L4 Solution | — | 600–800 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep 3dgs
pwm-node verify 3dgs/mipnerf360_s1_ideal.yaml
pwm-node mine 3dgs/mipnerf360_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
