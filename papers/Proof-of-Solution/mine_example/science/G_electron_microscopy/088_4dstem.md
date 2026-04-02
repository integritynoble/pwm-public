# Principle #88 — 4D-STEM

**Domain:** Electron Microscopy | **Carrier:** Electron | **Difficulty:** Hard (δ=5)
**DAG:** G.beam --> K.scatter.electron --> S.raster --> F.dft | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.beam-->K.scatter.electron-->S.raster-->F.dft    4DSTEM      4DSTEM-Crystal     Ptychography
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  4D-STEM   P = (E, G, W, C)   Principle #88                    │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I(r_p, k) = |FT{Probe(r−r_p)·T(r)}|² + n             │
│        │ 4D dataset: 2D scan (r_p) × 2D diffraction (k)        │
│        │ T(r) = transmission function of specimen               │
│        │ Inverse: recover T(r) (phase + amplitude) from 4D data │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.beam] --> [K.scatter.electron] --> [S.raster] --> [F.dft]│
│        │  E-Beam  Scatter  RasterScan  DiffractFFT               │
│        │ V={G.beam, K.scatter.electron, S.raster, F.dft}  A={G.beam-->K.scatter.electron, K.scatter.electron-->S.raster, S.raster-->F.dft}   L_DAG=4.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (ptychographic phase retrieval)         │
│        │ Uniqueness: YES with sufficient overlap (>60%)          │
│        │ Stability: κ ≈ 15 (dense scan), κ ≈ 80 (sparse scan)  │
│        │ Mismatch: scan position error, partial coherence        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), phase RMSE (secondary)             │
│        │ q = 1.5 (ePIE convergence)                            │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | 4D array dimensions consistent; scan step < probe FWHM (overlap) | PASS |
| S2 | Overlap > 60% guarantees unique phase retrieval | PASS |
| S3 | ePIE / rPIE converge monotonically for sufficient overlap | PASS |
| S4 | Phase RMSE < 0.1 rad achievable at standard dose | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# 4dstem/crystal_s1_ideal.yaml
principle_ref: sha256:<p088_hash>
omega:
  scan_grid: [64, 64]
  diffraction_grid: [128, 128]
  scan_step_nm: 0.5
  probe_FWHM_nm: 1.0
  overlap_pct: 75
E:
  forward: "I(r_p,k) = |FT{Probe(r-r_p)·T(r)}|² + n"
I:
  dataset: 4DSTEM_Crystal
  samples: 20
  noise: {type: poisson, dose_e_per_A2: 100}
  scenario: ideal
O: [PSNR, phase_RMSE_rad]
epsilon:
  PSNR_min: 24.0
  phase_RMSE_max: 0.15
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 64×64 scan at 0.5 nm step with 1 nm probe gives 75% overlap | PASS |
| S2 | Overlap 75% → unique phase retrieval; κ ≈ 15 | PASS |
| S3 | ePIE converges for 75% overlap at 100 e⁻/Å² | PASS |
| S4 | PSNR ≥ 24 dB and phase RMSE < 0.15 rad feasible | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# 4dstem/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec088_hash>
principle_ref: sha256:<p088_hash>
dataset:
  name: 4DSTEM_Crystal
  samples: 20
  scan_size: [64, 64]
  diff_size: [128, 128]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: ePIE
    params: {n_iter: 200, step_size: 0.5}
    results: {PSNR: 25.3, phase_RMSE: 0.12}
  - solver: rPIE
    params: {n_iter: 200, alpha: 1.0}
    results: {PSNR: 26.8, phase_RMSE: 0.09}
  - solver: PtychoNN
    params: {pretrained: true}
    results: {PSNR: 29.1, phase_RMSE: 0.06}
quality_scoring:
  - {min: 30.0, Q: 1.00}
  - {min: 27.0, Q: 0.90}
  - {min: 25.0, Q: 0.80}
  - {min: 23.0, Q: 0.75}
```

**Baseline solver:** ePIE — PSNR 25.3 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PSNR (dB) | Phase RMSE | Runtime | Q |
|--------|-----------|------------|---------|---|
| ePIE | 25.3 | 0.12 rad | 60 s | 0.80 |
| rPIE | 26.8 | 0.09 rad | 55 s | 0.88 |
| PtychoNN | 29.1 | 0.06 rad | 5 s | 0.95 |
| AutoPtycho | 30.5 | 0.04 rad | 15 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (AutoPtycho): 500 × 1.00 = 500 PWM
Floor:                  500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p088_hash>",
  "h_s": "sha256:<spec088_hash>",
  "h_b": "sha256:<bench088_hash>",
  "r": {"residual_norm": 0.013, "error_bound": 0.03, "ratio": 0.43},
  "c": {"fitted_rate": 1.48, "theoretical_rate": 1.5, "K": 3},
  "Q": 0.95,
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
pwm-node benchmarks | grep 4dstem
pwm-node verify 4dstem/crystal_s1_ideal.yaml
pwm-node mine 4dstem/crystal_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
