# Principle #153 — Ghost Imaging

**Domain:** Quantum Imaging | **Carrier:** Photon (entangled pair) | **Difficulty:** Advanced (δ=3)
**DAG:** S.correlated --> integral.coincidence | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.correlated-->integral.coincidence    Ghost-Img   GhostSim-12       Correlate
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  GHOST IMAGING   P = (E, G, W, C)   Principle #153              │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ G(r) = ⟨I_ref(r) · I_bucket⟩ − ⟨I_ref(r)⟩⟨I_bucket⟩  │
│        │ SPDC source → signal (bucket) + idler (spatially res.) │
│        │ Inverse: recover object T(r) from correlation of       │
│        │ bucket detector with spatially-resolved reference beam  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.correlated] --> [integral.coincidence]                │
│        │  EntangledPairs  CoincidenceCount                      │
│        │ V={S.correlated, integral.coincidence}  A={S.correlated-->integral.coincidence}   L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (non-zero spatial correlations)         │
│        │ Uniqueness: YES with sufficient measurement diversity   │
│        │ Stability: κ ≈ 40 (photon-starved), κ ≈ 12 (bright)   │
│        │ Mismatch: background counts, partial coherence          │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), SSIM (secondary)                  │
│        │ q = 1.0 (correlation convergence ~ 1/√N)             │
│        │ T = {residual_norm, SNR_corr, N_measurements}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Correlation dimensions match object grid; speckle grain ≤ pixel | PASS |
| S2 | Sufficient measurements N → bounded pseudo-inverse of pattern matrix | PASS |
| S3 | Correlation estimate converges as O(1/√N) with measurement count | PASS |
| S4 | PSNR ≥ 22 dB achievable for N ≥ 10 000 patterns | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# ghost_imaging/ghostsim_s1_ideal.yaml
principle_ref: sha256:<p153_hash>
omega:
  grid: [128, 128]
  pixel_um: 50
  wavelength_nm: 810
  source: SPDC
  N_patterns: 20000
E:
  forward: "G(r) = <I_ref(r) · I_bucket> - <I_ref><I_bucket>"
  correlation: "second-order intensity correlation"
I:
  dataset: GhostSim_12
  objects: 12
  noise: {type: poisson, dark_counts: 50}
  scenario: ideal
O: [PSNR, SSIM]
epsilon:
  PSNR_min: 22.0
  SSIM_min: 0.70
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 128×128 grid at 50 µm with 20k patterns exceeds Nyquist sampling | PASS |
| S2 | κ ≈ 12 for 20k patterns with SPDC source | PASS |
| S3 | Correlation converges at O(1/√N) for N=20000 | PASS |
| S4 | PSNR ≥ 22 dB feasible with 20k measurements | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# ghost_imaging/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec153_hash>
dataset:
  name: GhostSim_12
  objects: 12
  N_patterns: 20000
baselines:
  - solver: Classical-Correlation
    params: {method: subtract_mean}
    results: {PSNR: 22.5, SSIM: 0.72}
  - solver: Compressed-Sensing
    params: {basis: DCT, lambda: 0.01}
    results: {PSNR: 27.3, SSIM: 0.85}
  - solver: DGI-Net
    params: {arch: UNet, pretrained: true}
    results: {PSNR: 30.1, SSIM: 0.91}
quality_scoring:
  - {min: 30.0, Q: 1.00}
  - {min: 27.0, Q: 0.90}
  - {min: 24.0, Q: 0.80}
  - {min: 22.0, Q: 0.75}
```

**Baseline:** Classical-Correlation — PSNR 22.5 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| Classical-Correlation | 22.5 | 0.72 | 0.5 s | 0.75 |
| Compressed-Sensing | 27.3 | 0.85 | 8 s | 0.90 |
| DGI-Net | 30.1 | 0.91 | 1.2 s | 1.00 |
| Normalized-GI | 25.0 | 0.79 | 0.6 s | 0.82 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q
Best (DGI-Net):  300 × 1.00 = 300 PWM
Floor:           300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p153_hash>",
  "h_s": "sha256:<spec153_hash>",
  "h_b": "sha256:<bench153_hash>",
  "r": {"residual_norm": 0.015, "error_bound": 0.04, "ratio": 0.38},
  "c": {"fitted_rate": 0.98, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep ghost_imaging
pwm-node verify ghost_imaging/ghostsim_s1_ideal.yaml
pwm-node mine ghost_imaging/ghostsim_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
