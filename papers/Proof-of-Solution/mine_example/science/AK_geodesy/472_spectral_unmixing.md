# Principle #472 — Spectral Unmixing (Hyperspectral)

**Domain:** Geodesy / Remote Sensing | **Carrier:** N/A (linear algebra) | **Difficulty:** Standard (δ=3)
**DAG:** [L.mix.spectral] --> [O.l1] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.mix.spec-->O.l1  SpectUnmix  AVIRIS-bench  NNLS/sparse
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SPECTRAL UNMIXING (HYPERSPECTRAL)  P=(E,G,W,C) Principle #472  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y = Ma + n   (linear mixing model)                     │
│        │ y ∈ ℝᴸ (pixel spectrum, L bands)                       │
│        │ M ∈ ℝᴸˣᵖ (endmember matrix, p endmembers)             │
│        │ a ∈ ℝᵖ (abundance vector), Σaᵢ=1, aᵢ≥0 (ASC+ANC)    │
│        │ Forward: given M,a → y;  Inverse: given y,M → a       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.mix.spec] ──→ [O.l1]                                │
│        │  spectral-unmix  sparse-solve                          │
│        │ V={L.mix.spec,O.l1}  A={L.mix.spec→O.l1}  L_DAG=1.0              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (NNLS always has solution)              │
│        │ Uniqueness: YES when M full column rank, p ≤ L         │
│        │ Stability: condition number of M determines sensitivity│
│        │ Mismatch: nonlinear mixing, endmember variability      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSE(a_est − a_true)  (abundance error)            │
│        │ q = N/A (constrained optimization)                    │
│        │ T = {abundance_RMSE, reconstruction_error, SAD}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Mixing model dimensionally consistent; ANC+ASC constraints valid | PASS |
| S2 | Full column rank M ensures unique abundance solution | PASS |
| S3 | FCLS / SUNSAL converge for well-conditioned M | PASS |
| S4 | Abundance RMSE bounded by SNR and cond(M) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# spect_unmix/aviris_s1.yaml
principle_ref: sha256:<p472_hash>
omega:
  pixels: 10000
  bands: 224
  domain: AVIRIS_Cuprite
E:
  forward: "y = Ma + n;  FCLS inversion"
  endmembers: 5
  constraints: [ANC, ASC]
B:
  SNR: 50_dB
  library: USGS_spectral_library
I:
  scenario: mineral_mapping_Cuprite
  methods: [FCLS, SUNSAL, sparse_unmixing]
O: [abundance_RMSE, reconstruction_RMSE, spectral_angle]
epsilon:
  abundance_RMSE_max: 0.10
  reconstruction_RMSE_max: 0.05
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 224 bands, 5 endmembers; L >> p ensures overdetermined | PASS |
| S2 | USGS library endmembers well-separated (SAD > 10°) | PASS |
| S3 | FCLS converges within 100 ADMM iterations | PASS |
| S4 | Abundance RMSE < 10% at SNR 50 dB | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# spect_unmix/benchmark_cuprite.yaml
spec_ref: sha256:<spec472_hash>
principle_ref: sha256:<p472_hash>
dataset:
  name: AVIRIS_Cuprite_1995
  reference: "Swayze et al. (1998) Cuprite mineral mapping"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FCLS (fully constrained)
    params: {constraints: ANC+ASC}
    results: {abundance_RMSE: 0.085, reconstruction_RMSE: 0.032}
  - solver: SUNSAL (ADMM)
    params: {lambda: 0.01, constraints: ANC+ASC}
    results: {abundance_RMSE: 0.072, reconstruction_RMSE: 0.028}
  - solver: Sparse unmixing (SUnSAL)
    params: {library: full_USGS, lambda: 0.001}
    results: {abundance_RMSE: 0.065, reconstruction_RMSE: 0.025}
quality_scoring:
  - {min_RMSE: 0.03, Q: 1.00}
  - {min_RMSE: 0.07, Q: 0.90}
  - {min_RMSE: 0.10, Q: 0.80}
  - {min_RMSE: 0.15, Q: 0.75}
```

**Baseline solver:** SUNSAL — abundance RMSE 7.2%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Abund RMSE | Recon RMSE | Runtime | Q |
|--------|-----------|-----------|---------|---|
| FCLS | 0.085 | 0.032 | 2 s | 0.80 |
| SUNSAL | 0.072 | 0.028 | 5 s | 0.90 |
| Sparse (SUnSAL) | 0.065 | 0.025 | 15 s | 0.90 |
| Nonlinear (kernel) | 0.038 | 0.015 | 60 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (nonlinear): 300 × 1.00 = 300 PWM
Floor:                 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p472_hash>",
  "h_s": "sha256:<spec472_hash>",
  "h_b": "sha256:<bench472_hash>",
  "r": {"abundance_RMSE": 0.038, "error_bound": 0.10, "ratio": 0.380},
  "c": {"SAD_mean": 3.2, "pixels": 10000, "K": 3},
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
| L4 Solution | — | 225–300 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep spect_unmix
pwm-node verify spect_unmix/aviris_s1.yaml
pwm-node mine spect_unmix/aviris_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
