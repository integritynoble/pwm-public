# Principle #27 — Coded Aperture Compressive Temporal Imaging (CACTI)

**Domain:** Compressive Imaging | **Carrier:** Photon | **Difficulty:** Frontier (δ=5)
**DAG:** L.diag.binary → L.shear.temporal → ∫.temporal | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.diag→L.shear→∫  CACTI   CACTI-Video-6      CS-Video-Recon
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CACTI   P = (E, G, W, C)   Principle #27                       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(x,y) = Σ_t C_t(x,y) · f(x,y,t) + n                 │
│        │ C_t = time-varying coded mask (binary, per sub-frame)   │
│        │ B video frames compressed into 1 detector exposure      │
│        │ Inverse: recover B high-speed frames from single shot   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ DAG DECOMPOSITION  G = (V, A)                          │
│        │                                                         │
│        │ Hierarchical primitive notation: root.sub.subsub         │
│        │ (See primitives.md for full 149-leaf hierarchy)         │
│        │                                                         │
│        │ CACTI forward DAG:                                      │
│        │                                                         │
│        │   [L.diag.binary] --> [L.shear.temporal] --> [∫.temporal]│
│        │        │                    │                    │       │
│        │   coded mask C_t        rolling shift        sum over t │
│        │   C_t(x,y)∈{0,1}       mask varies per      single     │
│        │   per sub-frame         sub-frame t          exposure   │
│        │                                                         │
│        │ V = {L.diag.binary, L.shear.temporal, ∫.temporal}      │
│        │ A = {L.diag.binary -> L.shear.temporal,                │
│        │      L.shear.temporal -> ∫.temporal}                    │
│        │ |V| = 3, |A| = 2, P = 3, C = 0                        │
│        │                                                         │
│        │ Node semantics:                                         │
│        │   L.diag.binary:                                        │
│        │     root L = linear operator                            │
│        │     sub  diag = diagonal (element-wise multiply)       │
│        │     subsub binary = values ∈ {0,1} (coded mask)        │
│        │     f(x,y,t) -> C_t(x,y) · f(x,y,t)                  │
│        │                                                         │
│        │   L.shear.temporal:                                     │
│        │     root L = linear operator                            │
│        │     sub  shear = dimension-dependent translation       │
│        │     subsub temporal = shift indexed by time t           │
│        │     mask pattern rolls across B sub-frames             │
│        │                                                         │
│        │   ∫.temporal:                                           │
│        │     root ∫ = integrate / accumulate                     │
│        │     sub  temporal = sum over time dimension             │
│        │     y(x,y) = Σ_t C_t(x,y) · f(x,y,t)                 │
│        │                                                         │
│        │ Cross-domain: shares L.diag.binary with CASSI (#25),   │
│        │   SPC (#26), CUP (#151) — "compressive snapshot" family│
│        │ CASSI shears spectrally; CACTI shears temporally       │
│        │                                                         │
│        │ L_DAG = 4.0  (computed from |V|, path length, coupling)│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (temporal codes provide diversity)      │
│        │ Uniqueness: YES under video sparsity + temporal corr.  │
│        │ Stability: κ ~ B (compression ratio = #frames)        │
│        │ Mismatch: mask synchronization, motion blur within sub │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR, SSIM (per-frame average)                     │
│        │ q = 1.0 (ADMM/PnP convergence for video CS)         │
│        │ T = {residual_norm, fitted_rate, temporal_consistency}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | B temporal masks per exposure; mask modulation rate consistent | PASS |
| S2 | Binary masks with ~50% transmittance: RIP-like condition holds | PASS |
| S3 | GAP-TV / PnP-ADMM converges for temporal CS model | PASS |
| S4 | PSNR ≥ 27 dB per frame for B=8 compression | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# cacti/video_s1_ideal.yaml
principle_ref: sha256:<p027_hash>
omega:
  spatial_grid: [256, 256]
  temporal_frames: 8
  mask_type: shifting_binary
  mask_transmittance: 0.5
  detector_fps: 30
  effective_fps: 240
E:
  forward: "y(x,y) = Σ_t C_t(x,y) · f(x,y,t) + n"
I:
  dataset: CACTI_Video_6
  sequences: 6
  noise: {type: gaussian, sigma: 0.03}
  scenario: ideal
O: [PSNR, SSIM]
epsilon:
  PSNR_min: 27.0
  SSIM_min: 0.78
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 8 masks per exposure at 256x256: geometry consistent | PASS |
| S2 | 8x temporal compression: manageable with temporal priors | PASS |
| S3 | PnP-ADMM converges within 100 iterations | PASS |
| S4 | PSNR ≥ 27 dB per frame at 8x compression | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# cacti/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec027_hash>
dataset:
  name: CACTI_Video_6
  sequences: 6
  size: [256, 256, 8]
baselines:
  - solver: GAP-TV
    params: {lambda_TV: 0.01, max_iter: 100}
    results: {PSNR: 27.8, SSIM: 0.798}
  - solver: PnP-FFDNet
    params: {denoiser: FFDNet, max_iter: 50}
    results: {PSNR: 30.5, SSIM: 0.878}
  - solver: EfficientSCI
    params: {arch: RevSCI, pretrained: true}
    results: {PSNR: 33.1, SSIM: 0.932}
quality_scoring:
  - {min: 33.0, Q: 1.00}
  - {min: 30.0, Q: 0.90}
  - {min: 27.0, Q: 0.80}
  - {min: 24.0, Q: 0.75}
```

**Baseline:** GAP-TV — PSNR 27.8 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| GAP-TV | 27.8 | 0.798 | 15 s | 0.80 |
| PnP-FFDNet | 30.5 | 0.878 | 8 s | 0.90 |
| EfficientSCI | 33.1 | 0.932 | 0.3 s | 1.00 |
| BIRNAT | 31.8 | 0.905 | 0.5 s | 0.94 |

### Reward Calculation

```
R = 100 × 1.0 × 5 × 1.0 × Q = 500 × Q
Best (EfficientSCI):  500 × 1.00 = 500 PWM
Floor:                500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p027_hash>",
  "h_s": "sha256:<spec027_hash>",
  "h_b": "sha256:<bench027_hash>",
  "r": {"residual_norm": 0.018, "error_bound": 0.04, "ratio": 0.45},
  "c": {"fitted_rate": 0.94, "theoretical_rate": 1.0, "K": 3},
  "Q": 0.94,
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
| L4 Solution | — | 375–500 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep cacti
pwm-node verify cacti/video_s1_ideal.yaml
pwm-node mine cacti/video_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
