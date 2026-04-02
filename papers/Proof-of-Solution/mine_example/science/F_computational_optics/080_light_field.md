# Principle #80 — Light Field Imaging

**Domain:** Computational Optics & Neural Rendering | **Carrier:** Photon | **Difficulty:** Hard (δ=5)
**DAG:** Pi.ray --> S.angular --> integral.spatial | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │         Pi.ray-->S.angular-->integral.spatial    LightField  LF-Stanford-30    ShearWarp
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LIGHT FIELD IMAGING   P = (E, G, W, C)   Principle #80         │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ L(u,v,s,t) = ∫ ρ(x)·δ(ray(u,v,s,t,x)) dx            │
│        │ 4D light field parameterized on two parallel planes     │
│        │ (u,v) = lens plane; (s,t) = sensor plane               │
│        │ Inverse: refocus at arbitrary depth from 4D L           │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [Pi.ray] --> [S.angular] --> [integral.spatial]          │
│        │  RayProject  AngularSample  Refocus                     │
│        │ V={Pi.ray, S.angular, integral.spatial}  A={Pi.ray-->S.angular, S.angular-->integral.spatial}   L_DAG=4.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (4D capture encodes angular+spatial)     │
│        │ Uniqueness: YES within angular sampling bounds           │
│        │ Stability: κ ≈ 8 (dense angular), κ ≈ 60 (sparse)      │
│        │ Mismatch: microlens calibration, vignetting              │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), SSIM (secondary)                    │
│        │ q = 2.0 (shift-and-add refocusing convergence)         │
│        │ T = {residual_norm, depth_accuracy, K_resolutions}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Angular sampling satisfies anti-aliasing; spatial resolution matches sensor | PASS |
| S2 | Dense angular views → unique depth and refocus within disparity range | PASS |
| S3 | Shift-and-add converges; Fourier-slice extraction stable | PASS |
| S4 | PSNR ≥ 30 dB for refocused images from 9×9 angular grid | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# light_field/lf_stanford_s1_ideal.yaml
principle_ref: sha256:<p080_hash>
omega:
  spatial_res: [512, 512]
  angular_res: [9, 9]
  pixel_um: 1.4
  baseline_mm: 5.0
E:
  forward: "L(u,v,s,t) = scene radiance along ray"
  model: "Two-plane parameterization with microlens array"
I:
  dataset: LF_Stanford_30
  scenes: 30
  noise: {type: gaussian, sigma: 0.005}
  scenario: ideal
O: [PSNR, SSIM]
epsilon:
  PSNR_min: 30.0
  SSIM_min: 0.88
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 9×9 angular views at 512×512 spatial; baseline 5 mm | PASS |
| S2 | κ ≈ 8 for 81-view dense capture | PASS |
| S3 | Shift-and-add converges at all disparity levels | PASS |
| S4 | PSNR ≥ 30 dB feasible for σ=0.005 noise | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# light_field/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec080_hash>
principle_ref: sha256:<p080_hash>
dataset:
  name: LF_Stanford_30
  scenes: 30
  spatial_size: [512, 512]
  angular_size: [9, 9]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Shift-and-Add
    params: {disparity_range: [-4, 4]}
    results: {PSNR: 31.5, SSIM: 0.90}
  - solver: Fourier-Disparity-Layer
    params: {layers: 16}
    results: {PSNR: 34.2, SSIM: 0.93}
  - solver: LFAttNet
    params: {pretrained: true}
    results: {PSNR: 38.5, SSIM: 0.97}
quality_scoring:
  - {min: 38.0, Q: 1.00}
  - {min: 35.0, Q: 0.90}
  - {min: 32.0, Q: 0.80}
  - {min: 30.0, Q: 0.75}
```

**Baseline solver:** Shift-and-Add — PSNR 31.5 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| Shift-and-Add | 31.5 | 0.90 | 0.2 s | 0.78 |
| Fourier-Disparity-Layer | 34.2 | 0.93 | 1.0 s | 0.88 |
| LFAttNet | 38.5 | 0.97 | 2.0 s | 0.98 |
| LFSSR | 36.0 | 0.95 | 1.5 s | 0.93 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (LFAttNet):  500 × 0.98 = 490 PWM
Floor:                 500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p080_hash>",
  "h_s": "sha256:<spec080_hash>",
  "h_b": "sha256:<bench080_hash>",
  "r": {"residual_norm": 0.007, "error_bound": 0.02, "ratio": 0.35},
  "c": {"fitted_rate": 1.96, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 375–490 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep light_field
pwm-node verify light_field/lf_stanford_s1_ideal.yaml
pwm-node mine light_field/lf_stanford_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
