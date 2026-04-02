# Principle #81 — Integral Photography

**Domain:** Computational Optics & Neural Rendering | **Carrier:** Photon | **Difficulty:** Hard (δ=5)
**DAG:** Pi.ray --> S.angular --> integral.spatial | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │         Pi.ray-->S.angular-->integral.spatial    IntPhoto    MLA-Synth-20      ViewSynth
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  INTEGRAL PHOTOGRAPHY   P = (E, G, W, C)   Principle #81        │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I(x,y) = Σ_k L(u_k, v_k, s(x), t(y))                 │
│        │ Microlens array maps angular info to sub-images          │
│        │ Each elemental image encodes a directional sample        │
│        │ Inverse: synthesize novel viewpoints from elemental set  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [Pi.ray] --> [S.angular] --> [integral.spatial]          │
│        │  RayProject  AngularSample  ViewSynth                   │
│        │ V={Pi.ray, S.angular, integral.spatial}  A={Pi.ray-->S.angular, S.angular-->integral.spatial}   L_DAG=4.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (MLA encodes directional radiance)       │
│        │ Uniqueness: YES within angular sampling of MLA pitch     │
│        │ Stability: κ ≈ 10 (fine MLA), κ ≈ 50 (coarse MLA)      │
│        │ Mismatch: MLA misalignment, f-number mismatch            │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), SSIM (secondary)                    │
│        │ q = 2.0 (elemental image inversion convergence)        │
│        │ T = {residual_norm, angular_consistency, K_resolutions}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | MLA pitch and f-number consistent with sensor pixel pitch | PASS |
| S2 | Elemental images provide unique angular samples within NA | PASS |
| S3 | View synthesis via back-projection converges | PASS |
| S4 | PSNR ≥ 28 dB achievable for 50×50 MLA grid | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# integral_photo/mla_synth_s1_ideal.yaml
principle_ref: sha256:<p081_hash>
omega:
  sensor_res: [4096, 4096]
  mla_pitch_um: 125
  mla_grid: [50, 50]
  pixels_per_lenslet: 9
  f_number: 2.8
E:
  forward: "I(x,y) = Σ angular samples via MLA"
  model: "Microlens array directional encoding"
I:
  dataset: MLA_Synth_20
  scenes: 20
  noise: {type: gaussian, sigma: 0.008}
  scenario: ideal
O: [PSNR, SSIM]
epsilon:
  PSNR_min: 28.0
  SSIM_min: 0.84
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 9 px/lenslet at 125 μm pitch; sensor 4096×4096 | PASS |
| S2 | κ ≈ 10 for 50×50 MLA with 9 angular samples | PASS |
| S3 | Back-projection view synthesis converges for 20 scenes | PASS |
| S4 | PSNR ≥ 28 dB feasible at σ=0.008 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# integral_photo/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec081_hash>
principle_ref: sha256:<p081_hash>
dataset:
  name: MLA_Synth_20
  scenes: 20
  sensor_size: [4096, 4096]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Back-Projection
    params: {depth_planes: 16}
    results: {PSNR: 28.8, SSIM: 0.85}
  - solver: PlenopticToolbox
    params: {method: depth_from_focus}
    results: {PSNR: 30.5, SSIM: 0.88}
  - solver: LF-InterNet
    params: {pretrained: true}
    results: {PSNR: 34.2, SSIM: 0.94}
quality_scoring:
  - {min: 34.0, Q: 1.00}
  - {min: 31.0, Q: 0.90}
  - {min: 28.0, Q: 0.80}
  - {min: 26.0, Q: 0.75}
```

**Baseline solver:** Back-Projection — PSNR 28.8 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| Back-Projection | 28.8 | 0.85 | 0.5 s | 0.80 |
| PlenopticToolbox | 30.5 | 0.88 | 2.0 s | 0.87 |
| LF-InterNet | 34.2 | 0.94 | 3.0 s | 0.98 |
| DistgLF | 32.5 | 0.91 | 2.5 s | 0.93 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (LF-InterNet): 500 × 0.98 = 490 PWM
Floor:                   500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p081_hash>",
  "h_s": "sha256:<spec081_hash>",
  "h_b": "sha256:<bench081_hash>",
  "r": {"residual_norm": 0.009, "error_bound": 0.025, "ratio": 0.36},
  "c": {"fitted_rate": 1.94, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep integral_photo
pwm-node verify integral_photo/mla_synth_s1_ideal.yaml
pwm-node mine integral_photo/mla_synth_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
