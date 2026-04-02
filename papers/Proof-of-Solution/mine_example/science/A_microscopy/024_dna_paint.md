# Principle #24 — DNA-PAINT Super-Resolution

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Frontier (δ=5)
**DAG:** S.stochastic --> K.psf.airy --> N.pointwise.abs2 | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.stochastic-->K.psf.airy-->N.pointwise.abs2  DNA-PAINT  PAINT-Origami-8  Localize+Render
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  DNA-PAINT   P = (E, G, W, C)   Principle #24                   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y_t(r) = Σ_j N_j(t) · PSF(r - r_j) + b + n            │
│        │ Binding: k_on[I], k_off → transient fluorescence bursts │
│        │ Localization: fit PSF centroid per binding event         │
│        │ Inverse: accumulate localizations → super-res image     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.stochastic]──→[K.psf.airy]──→[N.pointwise.abs2]     │
│        │  Sample(bind/unbind)  PSF-blur(Airy)  Intensity(|·|²)  │
│        │ V={S,K,N}  A={S-->K, K-->N}   L_DAG=4.0              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (transient binding yields sparse events)│
│        │ Uniqueness: YES at controlled imager concentration      │
│        │ Stability: κ ≈ 15 (programmable binding kinetics)     │
│        │ Mismatch: imager concentration, non-specific binding    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSE_xy (nm), Jaccard, NeNA resolution              │
│        │ q = 2.0 (MLE localization per binding event)          │
│        │ T = {RMSE_loc, Jaccard, NeNA_nm, binding_rate}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | k_on, k_off consistent with imager concentration and docking density | PASS |
| S2 | Sparse binding events → isolated PSFs; κ ≈ 15 | PASS |
| S3 | MLE localization converges per binding event | PASS |
| S4 | RMSE ≤ 5 nm, NeNA ≤ 8 nm achievable with DNA-PAINT kinetics | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# dna_paint/origami_s1_ideal.yaml
principle_ref: sha256:<p024_hash>
omega:
  grid: [256, 256]
  pixel_nm: 130
  frames: 30000
  imager_conc_nM: 5.0
  k_on_per_nM_per_s: 0.1
  k_off_per_s: 0.5
  photons_per_event: 5000
E:
  forward: "y_t = Σ_j N_j(t) · PSF(r-r_j) + bg + n"
I:
  dataset: PAINT_Origami_8
  sequences: 8
  noise: {type: poisson_gaussian, bg: 15, sigma_read: 1.2}
  scenario: ideal
O: [RMSE_xy_nm, Jaccard, NeNA_nm]
epsilon:
  RMSE_max_nm: 5.0
  Jaccard_min: 0.80
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 30k frames at 5 nM imager: ~3 events/site/min → sufficient | PASS |
| S2 | 5000 photons/event: CRLB ~3 nm, well below threshold | PASS |
| S3 | MLE converges per event with 5000 photons | PASS |
| S4 | RMSE ≤ 5 nm and Jaccard ≥ 0.80 feasible | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# dna_paint/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec024_hash>
dataset:
  name: PAINT_Origami_8
  sequences: 8
  frames_per_seq: 30000
baselines:
  - solver: Picasso
    params: {method: MLE, threshold: 2.0}
    results: {RMSE_xy: 4.2, Jaccard: 0.84}
  - solver: ThunderSTORM
    params: {method: MLE, wavelet: B-spline}
    results: {RMSE_xy: 4.8, Jaccard: 0.81}
  - solver: DECODE-PAINT
    params: {arch: UNet, pretrained: true}
    results: {RMSE_xy: 2.8, Jaccard: 0.92}
quality_scoring:
  metric: RMSE_xy_nm
  thresholds:
    - {max: 3.0, Q: 1.00}
    - {max: 4.0, Q: 0.90}
    - {max: 5.0, Q: 0.80}
    - {max: 7.0, Q: 0.75}
```

**Baseline:** Picasso — RMSE 4.2 nm | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | RMSE (nm) | Jaccard | Runtime | Q |
|--------|-----------|---------|---------|---|
| ThunderSTORM | 4.8 | 0.81 | 90 s | 0.80 |
| Picasso | 4.2 | 0.84 | 60 s | 0.88 |
| DECODE-PAINT | 2.8 | 0.92 | 15 s | 1.00 |
| DeepSTORM | 3.5 | 0.89 | 20 s | 0.92 |

### Reward Calculation

```
R = 100 × 1.0 × 5 × 1.0 × Q = 500 × Q
Best (DECODE-PAINT):  500 × 1.00 = 500 PWM
Floor:                500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p024_hash>",
  "h_s": "sha256:<spec024_hash>",
  "h_b": "sha256:<bench024_hash>",
  "r": {"residual_norm": 3.5, "error_bound": 5.0, "ratio": 0.70},
  "c": {"fitted_rate": 1.94, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 375–500 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep dna_paint
pwm-node verify dna_paint/origami_s1_ideal.yaml
pwm-node mine dna_paint/origami_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
