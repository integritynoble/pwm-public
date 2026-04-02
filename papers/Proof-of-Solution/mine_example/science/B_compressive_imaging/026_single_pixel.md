# Principle #26 — Single-Pixel Camera (SPC)

**Domain:** Compressive Imaging | **Carrier:** Photon | **Difficulty:** Standard (δ=3)
**DAG:** L.diag.binary → ∫.spatial | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.diag→∫     SPC         SPC-Scene-10       CS-Recon
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SINGLE-PIXEL CAMERA   P = (E, G, W, C)   Principle #26         │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y_i = <φ_i, f> + n_i,   i = 1..M                      │
│        │ φ_i = DMD pattern (structured illumination/modulation)  │
│        │ f ∈ R^N (vectorized scene), M << N measurements        │
│        │ Inverse: recover N-pixel image from M scalar products   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.diag.binary] --> [∫.spatial]                        │
│        │   DMD pattern         bucket sum (single photodiode)   │
│        │   φ_i(x,y)∈{0,1}     y_i = Σ_xy φ_i · f              │
│        │ V={L.diag.binary, ∫.spatial}  A={L.diag->∫}           │
│        │ |V|=2, |A|=1, L_DAG=2.0                               │
│        │ Note: L.diag.binary -> ∫.spatial = dot product <φ,f>  │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (RIP for Gaussian/Bernoulli matrices)   │
│        │ Uniqueness: YES under sparsity (s-sparse, M≥Cs·log N) │
│        │ Stability: δ_2s < 0.4 for random patterns, M/N ≥ 0.1  │
│        │ Mismatch: DMD pattern fidelity, photodiode linearity    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR, SSIM                                          │
│        │ q = 1.0 (ISTA/FISTA O(1/k) to O(1/k²))              │
│        │ T = {residual_norm, fitted_rate, compression_ratio}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | DMD patterns M×N consistent; single-detector readout matched | PASS |
| S2 | M/N ≥ 0.1 with random patterns: RIP holds; δ_2s < 0.4 | PASS |
| S3 | FISTA converges with O(1/k²) rate for L1-regularized problem | PASS |
| S4 | PSNR ≥ 25 dB at 10% compression ratio | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# spc/scene_s1_ideal.yaml
principle_ref: sha256:<p026_hash>
omega:
  image_size: [64, 64]
  N: 4096
  M: 1024
  compression_ratio: 0.25
  pattern_type: bernoulli_random
  detector: single_photodiode
E:
  forward: "y_i = <φ_i, f> + n"
I:
  dataset: SPC_Scene_10
  images: 10
  noise: {type: gaussian, sigma: 0.01}
  scenario: ideal
O: [PSNR, SSIM]
epsilon:
  PSNR_min: 25.0
  SSIM_min: 0.75
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | M=1024, N=4096: 25% compression ratio, patterns verified | PASS |
| S2 | Bernoulli random at M/N=0.25: RIP satisfied | PASS |
| S3 | FISTA converges within 500 iterations | PASS |
| S4 | PSNR ≥ 25 dB feasible at 25% measurements | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# spc/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec026_hash>
dataset:
  name: SPC_Scene_10
  images: 10
  size: [64, 64]
  measurements: 1024
baselines:
  - solver: FISTA-L1
    params: {lambda: 0.01, max_iter: 500, basis: DCT}
    results: {PSNR: 26.8, SSIM: 0.782}
  - solver: D-AMP
    params: {denoiser: BM3D, max_iter: 30}
    results: {PSNR: 29.5, SSIM: 0.852}
  - solver: SPC-Net
    params: {arch: ReconNet, pretrained: true}
    results: {PSNR: 31.2, SSIM: 0.898}
quality_scoring:
  - {min: 31.0, Q: 1.00}
  - {min: 28.0, Q: 0.90}
  - {min: 25.0, Q: 0.80}
  - {min: 22.0, Q: 0.75}
```

**Baseline:** FISTA-L1 — PSNR 26.8 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| FISTA-L1 | 26.8 | 0.782 | 5 s | 0.82 |
| D-AMP | 29.5 | 0.852 | 3 s | 0.92 |
| SPC-Net | 31.2 | 0.898 | 0.05 s | 1.00 |
| TVAL3 | 28.1 | 0.821 | 2 s | 0.88 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q
Best (SPC-Net):  300 × 1.00 = 300 PWM
Floor:           300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p026_hash>",
  "h_s": "sha256:<spec026_hash>",
  "h_b": "sha256:<bench026_hash>",
  "r": {"residual_norm": 0.009, "error_bound": 0.025, "ratio": 0.36},
  "c": {"fitted_rate": 0.92, "theoretical_rate": 1.0, "K": 3},
  "Q": 0.92,
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
pwm-node benchmarks | grep single_pixel
pwm-node verify spc/scene_s1_ideal.yaml
pwm-node mine spc/scene_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
