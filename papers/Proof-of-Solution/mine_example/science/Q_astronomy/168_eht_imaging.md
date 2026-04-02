# Principle #168 — Event Horizon Telescope (EHT) Imaging

**Domain:** Astronomy | **Carrier:** Photon (mm-wave) | **Difficulty:** Frontier (δ=5)
**DAG:** S.sparse --> F.nufft --> integral.baseline | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.sparse-->F.nufft-->integral.baseline    EHT         EHTSynth-6        VLBI-Recon
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  EHT IMAGING   P = (E, G, W, C)   Principle #168                │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ V(u,v) = ∫∫ I(l,m) · e^{-i2π(ul+vm)} dl dm            │
│        │ Sparse (u,v) coverage from Earth-baseline VLBI array    │
│        │ Closure quantities: phases φ_123, amplitudes A_1234     │
│        │ Inverse: reconstruct I(l,m) from sparse visibilities    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.sparse] --> [F.nufft] --> [integral.baseline]         │
│        │  SparseArray  NUFFT  BaselineSynth                     │
│        │ V={S.sparse, F.nufft, integral.baseline}  A={S.sparse-->F.nufft, F.nufft-->integral.baseline}   L_DAG=5.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (closure quantities are calibration-     │
│        │   independent observables)                              │
│        │ Uniqueness: NO (severely under-determined; regularized) │
│        │ Stability: κ ≈ 100+ (sparse uv), κ ≈ 30 (with prior)  │
│        │ Mismatch: atmospheric phase, antenna gains, interstellar│
│        │   scattering, variable source structure                 │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = NXCORR (primary), χ²_closure (secondary)           │
│        │ q = 1.0 (RML convergence with strong regularization)  │
│        │ T = {NXCORR, chi2_closure, ring_diameter_uas, width}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | (u,v) coverage from 8 stations; max baseline ~10 Gλ at 230 GHz | PASS |
| S2 | Closure quantities eliminate station-based errors; regularization bounds κ | PASS |
| S3 | RML with entropy/TSV regularizer converges | PASS |
| S4 | NXCORR ≥ 0.90 on synthetic ring images achievable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# eht_imaging/ehtsynth_s1_ideal.yaml
principle_ref: sha256:<p168_hash>
omega:
  grid: [128, 128]
  pixel_uas: 2.0
  frequency_GHz: 230
  n_stations: 8
  bandwidth_GHz: 2.0
  integration_s: 10
  scan_duration_hr: 12
E:
  forward: "V(u,v) = FT{I(l,m)} sampled at sparse baselines"
  observables: "closure phases, closure amplitudes, visibilities"
I:
  dataset: EHTSynth_6
  sources: 6
  noise: {type: gaussian, thermal_Jy: 0.01}
  scenario: ideal
O: [NXCORR, chi2_closure_phase]
epsilon:
  NXCORR_min: 0.90
  chi2_CP_max: 1.5
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 8 stations → 28 baselines; 12 hr track: adequate (u,v) fill | PASS |
| S2 | Closure phases remove station gains; κ ≈ 30 with RML | PASS |
| S3 | RML with MEM + TSV converges within 500 iterations | PASS |
| S4 | NXCORR ≥ 0.90 feasible on synthetic data | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# eht_imaging/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec168_hash>
dataset:
  name: EHTSynth_6
  sources: 6
  uv_coverage: 8_stations_12hr
baselines:
  - solver: CLEAN
    params: {gain: 0.1, iterations: 5000, beam: circular}
    results: {NXCORR: 0.82, chi2_CP: 2.1}
  - solver: eht-imaging-RML
    params: {regularizer: [MEM, TSV], alpha: [1.0, 0.5]}
    results: {NXCORR: 0.93, chi2_CP: 1.2}
  - solver: PRIMO-DL
    params: {arch: PCA_dictionary, pretrained: true}
    results: {NXCORR: 0.96, chi2_CP: 1.05}
quality_scoring:
  metric: NXCORR
  thresholds:
    - {min: 0.95, Q: 1.00}
    - {min: 0.92, Q: 0.90}
    - {min: 0.88, Q: 0.80}
    - {min: 0.82, Q: 0.75}
```

**Baseline:** CLEAN — NXCORR 0.82 | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | NXCORR | χ²_CP | Runtime | Q |
|--------|--------|-------|---------|---|
| CLEAN | 0.82 | 2.10 | 30 s | 0.75 |
| eht-imaging-RML | 0.93 | 1.20 | 300 s | 0.90 |
| PRIMO-DL | 0.96 | 1.05 | 20 s | 1.00 |
| SMILI | 0.91 | 1.30 | 250 s | 0.88 |

### Reward Calculation

```
R = 100 × 1.0 × 5 × 1.0 × Q = 500 × Q
Best (PRIMO-DL):  500 × 1.00 = 500 PWM
Floor:            500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p168_hash>",
  "h_s": "sha256:<spec168_hash>",
  "h_b": "sha256:<bench168_hash>",
  "r": {"residual_norm": 0.04, "error_bound": 0.10, "ratio": 0.40},
  "c": {"fitted_rate": 0.95, "theoretical_rate": 1.0, "K": 3},
  "Q": 0.96,
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
pwm-node benchmarks | grep eht
pwm-node verify eht_imaging/ehtsynth_s1_ideal.yaml
pwm-node mine eht_imaging/ehtsynth_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
