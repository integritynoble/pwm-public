# Principle #11 — PALM/STORM Localization Microscopy

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Frontier (δ=5)
**DAG:** S.stochastic --> K.psf.airy --> N.pointwise.abs2 | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.stochastic-->K.psf.airy-->N.pointwise.abs2  SMLM  SMLM-Tubulins-10  Localize
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PALM/STORM   P = (E, G, W, C)   Principle #11                │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = Σ_j N_j · PSF(r - r_j) + b(r) + n(r)         │
│        │ Each emitter j has position r_j and photon count N_j  │
│        │ Inverse: localize r_j to ~20 nm from stochastic on/off│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.stochastic]──→[K.psf.airy]──→[N.pointwise.abs2]     │
│        │  Sample(on/off)  PSF-blur(Airy)  Intensity(|·|²)       │
│        │ V={S,K,N}  A={S-->K, K-->N}   L_DAG=4.0              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (isolated PSFs are localizable)        │
│        │ Uniqueness: YES at low emitter density (<1/μm²)       │
│        │ Stability: κ ≈ 20 (sparse); κ ≈ 300 (high density)  │
│        │ Mismatch: emitter density, drift, aberrations         │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSE_xy (nm), Jaccard index, FRC resolution       │
│        │ q = 2.0 (MLE for Gaussian PSF model)                │
│        │ T = {RMSE_loc, Jaccard, FRC_nm, detection_rate}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Frame count × density × FoV consistent with Nyquist-localization | PASS |
| S2 | At emitter density < 1/μm², CRLB gives σ_loc < 20 nm | PASS |
| S3 | ThunderSTORM/FALCON converge for isolated + overlapping PSFs | PASS |
| S4 | RMSE ≤ 20 nm, Jaccard ≥ 0.7 achievable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# smlm/tubulins_s1_ideal.yaml
principle_ref: sha256:<p011_hash>
omega:
  grid: [256, 256]
  pixel_nm: 100
  frames: 20000
  emitter_density_per_um2: 0.5
  photons_per_emitter: 2000
E:
  forward: "y_t = Σ_j N_j · PSF(r-r_j,t) + bg + n"
I:
  dataset: SMLM_Tubulins_10
  sequences: 10
  noise: {type: poisson_gaussian, bg: 20, sigma_read: 1.5}
  scenario: ideal
O: [RMSE_xy_nm, Jaccard, FRC_nm]
epsilon:
  RMSE_max_nm: 20.0
  Jaccard_min: 0.70
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 20k frames at 0.5/μm²: sufficient localizations for reconstruction | PASS |
| S2 | 2000 photons/emitter: CRLB ~10 nm, well below threshold | PASS |
| S3 | ThunderSTORM converges per-frame | PASS |
| S4 | RMSE ≤ 20 nm, Jaccard ≥ 0.70 | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# smlm/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec011_hash>
dataset:
  name: SMLM_Tubulins_10
  sequences: 10
  frames_per_seq: 20000
baselines:
  - solver: ThunderSTORM
    params: {method: MLE, threshold: 1.5}
    results: {RMSE_xy: 18.2, Jaccard: 0.74}
  - solver: FALCON
    params: {sparsity: L1, lambda: 0.01}
    results: {RMSE_xy: 15.1, Jaccard: 0.81}
  - solver: DECODE
    params: {arch: UNet, pretrained: true}
    results: {RMSE_xy: 10.3, Jaccard: 0.89}
quality_scoring:
  metric: RMSE_xy_nm
  thresholds:
    - {max: 10.0, Q: 1.00}
    - {max: 15.0, Q: 0.90}
    - {max: 20.0, Q: 0.80}
    - {max: 25.0, Q: 0.75}
```

**Baseline:** ThunderSTORM — RMSE 18.2 nm | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | RMSE (nm) | Jaccard | Runtime | Q |
|--------|-----------|---------|---------|---|
| ThunderSTORM | 18.2 | 0.74 | 60 s | 0.80 |
| FALCON | 15.1 | 0.81 | 120 s | 0.90 |
| DECODE | 10.3 | 0.89 | 20 s | 0.98 |
| DeepSTORM3D | 12.5 | 0.85 | 15 s | 0.92 |

### Reward Calculation

```
R = 100 × 1.0 × 5 × 1.0 × Q = 500 × Q
Best (DECODE):  500 × 0.98 = 490 PWM
Floor:          500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p011_hash>",
  "r": {"residual_norm": 10.3, "error_bound": 20.0, "ratio": 0.52},
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
| L4 Solution | — | 375–490 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep smlm
pwm-node verify smlm/tubulins_s1_ideal.yaml
pwm-node mine smlm/tubulins_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
