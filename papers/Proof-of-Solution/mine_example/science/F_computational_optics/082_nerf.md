# Principle #82 — Neural Radiance Fields (NeRF)

**Domain:** Computational Optics & Neural Rendering | **Carrier:** Photon | **Difficulty:** Research (δ=8)
**DAG:** integral.volume --> N.pointwise.activation --> Pi.ray | **Reward:** 8× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │         integral.volume-->N.pointwise.activation-->Pi.ray    NeRF        NeRF-Synth-8      InstNGP
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  NEURAL RADIANCE FIELDS (NeRF)   P = (E, G, W, C)   #82        │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ C(r) = ∫ T(t)·σ(r(t))·c(r(t),d) dt                   │
│        │ T(t) = exp(−∫σ(r(s))ds); σ = density, c = color        │
│        │ MLP: F_θ(x,y,z,θ,φ) → (σ, r,g,b)                     │
│        │ Inverse: optimize θ to match posed multi-view images    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [integral.volume] --> [N.pointwise.activation] --> [Pi.ray]│
│        │  VolRender  Activation  RayMarch                        │
│        │ V={integral.volume, N.pointwise.activation, Pi.ray}  A={integral.volume-->N.pointwise.activation, N.pointwise.activation-->Pi.ray}   L_DAG=6.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (volume rendering integral well-defined) │
│        │ Uniqueness: conditional (shape-radiance ambiguity)      │
│        │ Stability: κ ≈ 30 (dense views), κ ≈ 200 (few-shot)    │
│        │ Mismatch: pose error, transient objects, lighting change │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), SSIM, LPIPS (secondary)            │
│        │ q = 1.5 (gradient descent on photometric loss)         │
│        │ T = {residual_norm, novel_view_PSNR, K_resolutions}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Camera poses calibrated; ray sampling resolution matches target | PASS |
| S2 | Sufficient views → volume rendering integral converges uniquely | PASS |
| S3 | Adam optimizer on photometric MSE converges within 200k steps | PASS |
| S4 | PSNR ≥ 28 dB on novel views from 100+ training views | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# nerf/synth_s1_ideal.yaml
principle_ref: sha256:<p082_hash>
omega:
  image_res: [800, 800]
  train_views: 100
  test_views: 200
  near: 2.0
  far: 6.0
  n_samples: 128
E:
  forward: "C(r) = ∫ T(t)·σ·c dt  (volume rendering)"
  model: "MLP with positional encoding"
I:
  dataset: NeRF_Synth_8
  scenes: 8
  noise: {type: clean}
  scenario: ideal
O: [PSNR, SSIM, LPIPS]
epsilon:
  PSNR_min: 28.0
  SSIM_min: 0.90
  LPIPS_max: 0.08
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 100 training views at 800×800; 128 samples/ray | PASS |
| S2 | 100 views → sufficient for κ ≈ 30 | PASS |
| S3 | Adam optimizer converges within 200k iterations | PASS |
| S4 | PSNR ≥ 28 dB feasible on synthetic scenes | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# nerf/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec082_hash>
principle_ref: sha256:<p082_hash>
dataset:
  name: NeRF_Synth_8
  scenes: 8
  image_size: [800, 800]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: NeRF-vanilla
    params: {n_iter: 200000, lr: 5e-4}
    results: {PSNR: 31.0, SSIM: 0.947, LPIPS: 0.050}
  - solver: Instant-NGP
    params: {hash_levels: 16}
    results: {PSNR: 33.2, SSIM: 0.960, LPIPS: 0.035}
  - solver: Mip-NeRF-360
    params: {proposal_nets: 2}
    results: {PSNR: 33.8, SSIM: 0.962, LPIPS: 0.030}
quality_scoring:
  - {min: 34.0, Q: 1.00}
  - {min: 32.0, Q: 0.90}
  - {min: 30.0, Q: 0.80}
  - {min: 28.0, Q: 0.75}
```

**Baseline solver:** NeRF-vanilla — PSNR 31.0 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PSNR (dB) | SSIM | LPIPS | Runtime | Q |
|--------|-----------|------|-------|---------|---|
| NeRF-vanilla | 31.0 | 0.947 | 0.050 | 12 h | 0.82 |
| Instant-NGP | 33.2 | 0.960 | 0.035 | 5 min | 0.95 |
| Mip-NeRF-360 | 33.8 | 0.962 | 0.030 | 8 h | 0.97 |
| Zip-NeRF | 34.5 | 0.968 | 0.025 | 6 h | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 8 × 1.0 × Q
Best case (Zip-NeRF):  800 × 1.00 = 800 PWM
Floor:                 800 × 0.75 = 600 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p082_hash>",
  "h_s": "sha256:<spec082_hash>",
  "h_b": "sha256:<bench082_hash>",
  "r": {"residual_norm": 0.005, "error_bound": 0.015, "ratio": 0.33},
  "c": {"fitted_rate": 1.48, "theoretical_rate": 1.5, "K": 4},
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
pwm-node benchmarks | grep nerf
pwm-node verify nerf/synth_s1_ideal.yaml
pwm-node mine nerf/synth_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
