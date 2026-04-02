# Principle #159 — US/MRI Fusion

**Domain:** Multimodal Fusion | **Carrier:** Acoustic + RF | **Difficulty:** Advanced (δ=3)
**DAG:** M₁ → R₁, M₂ → R₂, R₁+R₂ → F → D | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          dual-acq     US-MRI      USMRIFuse-8       Register+Fuse
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  US/MRI FUSION   P = (E, G, W, C)   Principle #159              │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ f_fused(r) = W_US(r)·f_US(r) + W_MR(r)·f_MR(r)       │
│        │ US: y(t) = Σ σ(r)·h(t−2|r|/c) (pulse-echo B-mode)    │
│        │ MR: y_k = ∫ m(r)·e^{-i2πk·r} dr (k-space)            │
│        │ Inverse: deformable registration + real-time overlay    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [M₁]→[R₁] (US beamform), [M₂]→[R₂] (MR recon)       │
│        │  [R₁]+[R₂]→[F]→[D]                                   │
│        │ V={M₁,M₂,R₁,R₂,F,D}   L_DAG=3.5                     │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (shared anatomy, tracked US probe)      │
│        │ Uniqueness: YES with EM/optical tracking + deformable  │
│        │ Stability: κ ≈ 25 (deformation, probe pressure)       │
│        │ Mismatch: tissue deformation, tracking latency, FOV    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = TRE_mm (primary), overlay_accuracy (secondary)     │
│        │ q = 1.5 (deformable registration convergence)        │
│        │ T = {TRE_mm, Dice_target, latency_ms, overlay_err_mm} │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | US FOV within MR volume; tracking coordinates calibrated | PASS |
| S2 | Deformable registration bounded with regularization | PASS |
| S3 | B-spline FFD converges for tissue deformation model | PASS |
| S4 | TRE ≤ 3 mm achievable with EM tracking + deformable reg. | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# us_mri_fusion/usmrifuse_s1_ideal.yaml
principle_ref: sha256:<p159_hash>
omega:
  grid_MR: [256, 256, 128]
  voxel_MR_mm: [1.0, 1.0, 1.5]
  US_probe: convex_C5_2
  US_depth_mm: 150
  tracking: electromagnetic
E:
  forward_US: "y(t) = Σ σ(r)·h(t-2|r|/c)"
  forward_MR: "y_k = FT{m(r)}"
  registration: "deformable B-spline FFD"
I:
  dataset: USMRIFuse_8
  patients: 8
  organ: liver
  noise: {US: speckle_variance: 0.15, MR: rician_sigma: 0.02}
  scenario: ideal
O: [TRE_mm, Dice_target, latency_ms]
epsilon:
  TRE_max_mm: 3.0
  Dice_min: 0.80
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | US 150 mm depth within MR FOV; EM tracking calibrated | PASS |
| S2 | B-spline FFD with regularization: κ ≈ 25 | PASS |
| S3 | Deformable registration converges within 50 ms | PASS |
| S4 | TRE ≤ 3 mm and Dice ≥ 0.80 feasible | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# us_mri_fusion/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec159_hash>
dataset:
  name: USMRIFuse_8
  patients: 8
  modalities: [US, MR_T2w]
baselines:
  - solver: Rigid-Tracker
    params: {tracking: EM, transform: rigid}
    results: {TRE_mm: 5.2, Dice: 0.72}
  - solver: BSpline-FFD
    params: {grid_spacing_mm: 20, metric: NCC}
    results: {TRE_mm: 2.8, Dice: 0.84}
  - solver: DL-DeformFuse
    params: {arch: VoxelMorph, pretrained: true}
    results: {TRE_mm: 1.9, Dice: 0.91}
quality_scoring:
  metric: TRE_mm
  thresholds:
    - {max: 2.0, Q: 1.00}
    - {max: 3.0, Q: 0.90}
    - {max: 4.0, Q: 0.80}
    - {max: 5.0, Q: 0.75}
```

**Baseline:** Rigid-Tracker — TRE 5.2 mm | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | TRE (mm) | Dice | Latency (ms) | Q |
|--------|----------|------|--------------|---|
| Rigid-Tracker | 5.2 | 0.72 | 10 | 0.75 |
| BSpline-FFD | 2.8 | 0.84 | 120 | 0.90 |
| DL-DeformFuse | 1.9 | 0.91 | 35 | 1.00 |
| Demons-Deformable | 3.5 | 0.80 | 200 | 0.82 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q
Best (DL-DeformFuse):  300 × 1.00 = 300 PWM
Floor:                 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p159_hash>",
  "h_s": "sha256:<spec159_hash>",
  "h_b": "sha256:<bench159_hash>",
  "r": {"residual_norm": 1.9, "error_bound": 3.0, "ratio": 0.63},
  "c": {"fitted_rate": 1.45, "theoretical_rate": 1.5, "K": 3},
  "Q": 0.91,
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
pwm-node benchmarks | grep us_mri
pwm-node verify us_mri_fusion/usmrifuse_s1_ideal.yaml
pwm-node mine us_mri_fusion/usmrifuse_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
