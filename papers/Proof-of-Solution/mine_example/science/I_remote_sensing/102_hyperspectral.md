# Principle #102 — Hyperspectral Remote Sensing

**Domain:** Remote Sensing | **Carrier:** Photon (VNIR/SWIR) | **Difficulty:** Standard (δ=3)
**DAG:** L.diag.spectral --> S.spectral --> integral.spatial | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.diag.spectral-->S.spectral-->integral.spatial    HSI-RS     IndianPines         Unmix/SR
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  HYPERSPECTRAL RS   P = (E, G, W, C)   Principle #102          │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r,λ) = ∫ ρ(r,λ)·L_sun(λ)·τ_atm(λ) dΩ + n(r,λ)   │
│        │ ρ = surface reflectance; τ_atm = atmospheric transm.  │
│        │ N_λ = 100–400 contiguous spectral bands                │
│        │ Inverse: atmospheric correction + spectral unmixing    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.diag.spectral] --> [S.spectral] --> [integral.spatial]│
│        │ SpectralFilter  SpectralSample  Integrate               │
│        │ V={L.diag.spectral, S.spectral, integral.spatial}  A={L.diag.spectral-->S.spectral, S.spectral-->integral.spatial}   L_DAG=2.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (spectral unmixing is well-posed)       │
│        │ Uniqueness: YES with endmember constraints (VCA/NMF)   │
│        │ Stability: κ ≈ 10 (distinct endmembers), κ ≈ 80 (sim.)│
│        │ Mismatch: atmospheric model error, adjacency effects    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = abundance RMSE (primary), SAM (secondary)          │
│        │ q = 2.0 (NMF/FCLS convergence)                       │
│        │ T = {abundance_RMSE, SAM_deg, K_resolutions}           │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Spectral bands cover diagnostic absorption features | PASS |
| S2 | Endmember spectra sufficiently distinct; κ < 80 | PASS |
| S3 | NMF / FCLS converge for non-negative abundance constraints | PASS |
| S4 | Abundance RMSE < 0.10 achievable for distinct materials | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# hyperspectral/indianpines_s1_ideal.yaml
principle_ref: sha256:<p102_hash>
omega:
  grid: [145, 145]
  spectral_bands: 200
  wavelength_range_nm: [400, 2500]
E:
  forward: "y = ρ·L_sun·τ_atm + n"
  unmixing: "y = E·a + n, a ≥ 0, Σa = 1"
I:
  dataset: IndianPines
  scenes: 1
  noise: {type: gaussian, SNR_dB: 30}
  scenario: ideal
O: [abundance_RMSE, OA_pct, SAM_deg]
epsilon:
  abundance_RMSE_max: 0.10
  OA_min_pct: 85.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200 bands over 400–2500 nm; 145×145 spatial grid | PASS |
| S2 | Endmembers in IndianPines distinct; κ ≈ 15 | PASS |
| S3 | FCLS converges for sum-to-one, non-negative constraints | PASS |
| S4 | RMSE < 0.10 feasible at SNR 30 dB | PASS |

**Layer 2 reward:** 105 PWM + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# hyperspectral/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec102_hash>
principle_ref: sha256:<p102_hash>
dataset:
  name: IndianPines
  size: [145, 145, 200]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FCLS
    params: {endmembers: VCA}
    results: {abundance_RMSE: 0.085, OA_pct: 87.2}
  - solver: SUnSAL
    params: {lambda_sparse: 0.01}
    results: {abundance_RMSE: 0.062, OA_pct: 91.5}
  - solver: DeepHSI
    params: {pretrained: true}
    results: {abundance_RMSE: 0.035, OA_pct: 96.8}
quality_scoring:
  - {max_RMSE: 0.03, Q: 1.00}
  - {max_RMSE: 0.06, Q: 0.90}
  - {max_RMSE: 0.09, Q: 0.80}
  - {max_RMSE: 0.12, Q: 0.75}
```

**Baseline:** FCLS — RMSE 0.085 | **Layer 3 reward:** 60 PWM + upstream

---

## Layer 4 — Benchmark → Solution

| Solver | RMSE | OA (%) | Runtime | Q |
|--------|------|--------|---------|---|
| FCLS | 0.085 | 87.2 | 2 s | 0.80 |
| SUnSAL | 0.062 | 91.5 | 10 s | 0.90 |
| DeepHSI | 0.035 | 96.8 | 3 s | 0.97 |
| SpectralFormer | 0.028 | 97.5 | 5 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best: 300 × 1.00 = 300 PWM | Floor: 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p102_hash>",
  "h_s": "sha256:<spec102_hash>",
  "h_b": "sha256:<bench102_hash>",
  "r": {"abundance_RMSE": 0.035, "OA_pct": 96.8},
  "c": {"fitted_rate": 1.96, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.97,
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

## Quick-Start

```bash
pwm-node benchmarks | grep hyperspectral
pwm-node verify hyperspectral/indianpines_s1_ideal.yaml
pwm-node mine hyperspectral/indianpines_s1_ideal.yaml
```
