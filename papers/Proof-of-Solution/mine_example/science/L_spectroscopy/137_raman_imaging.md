# Principle #137 — Raman Imaging / Microscopy

**Domain:** Spectroscopy | **Carrier:** Photon (inelastic) | **Difficulty:** Advanced (δ=3)
**DAG:** G.pulse.laser --> K.scatter.inelastic --> S.spectral | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.pulse.laser-->K.scatter.inelastic-->S.spectral    Raman       RamanCell-15       Unmix
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  RAMAN IMAGING / MICROSCOPY   P = (E, G, W, C)   #137          │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I(ν̃, r) = Σ_k c_k(r) · σ_k(ν̃) · I₀ · η             │
│        │ ν̃ = Raman shift (cm⁻¹); σ_k = cross-section of mode k│
│        │ c_k = concentration; I₀ = laser intensity; η = collect.│
│        │ Inverse: unmix c_k(r) from hyperspectral Raman cube    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse.laser] --> [K.scatter.inelastic] --> [S.spectral]│
│        │  LaserExcite  RamanScatter  SpectralDisperse           │
│        │ V={G.pulse.laser, K.scatter.inelastic, S.spectral}  A={G.pulse.laser-->K.scatter.inelastic, K.scatter.inelastic-->S.spectral}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Raman-active modes always present)     │
│        │ Uniqueness: YES (fingerprint spectra per molecule)     │
│        │ Stability: κ ≈ 5 (pure compounds), κ ≈ 30 (mixtures)  │
│        │ Mismatch: fluorescence background, cosmic rays, laser  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = spectral RMSE (primary), classification acc (sec.) │
│        │ q = 2.0 (NNLS/MCR linear unmixing convergence)        │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Laser wavelength, grating resolution, and spectral range cover target Raman modes | PASS |
| S2 | Fingerprint bands separated by ≥ 5 cm⁻¹ enable unique component identification | PASS |
| S3 | MCR-ALS converges monotonically with non-negativity constraints | PASS |
| S4 | Spectral RMSE ≤ 5% achievable for pure-component reference spectra | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# raman_imaging/ramancell_s1.yaml
principle_ref: sha256:<p137_hash>
omega:
  grid: [128, 128]
  pixel_um: 0.5
  laser_nm: 532
  spectral_range_cm: [200, 3200]
  spectral_channels: 1024
  integration_s: 0.5
E:
  forward: "I(nu, r) = sum_k c_k(r) * sigma_k(nu) * I0 * eta"
  unmixing: "MCR-ALS"
I:
  dataset: RamanCell_15
  images: 15
  noise: {type: poisson, peak: 3000}
  scenario: ideal
O: [spectral_RMSE_pct, classification_acc_pct]
epsilon:
  spectral_RMSE_max: 8.0
  classification_acc_min: 90.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 532 nm laser over 200–3200 cm⁻¹ with 1024 channels covers fingerprint + CH region | PASS |
| S2 | κ ≈ 5 for pure compounds at 3000 peak counts | PASS |
| S3 | MCR-ALS converges within 100 iterations with non-negativity | PASS |
| S4 | RMSE ≤ 8% and classification ≥ 90% feasible | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# raman_imaging/benchmark_s1.yaml
spec_ref: sha256:<spec137_hash>
principle_ref: sha256:<p137_hash>
dataset:
  name: RamanCell_15
  images: 15
  size: [128, 128]
  spectral_channels: 1024
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Peak-Ratio
    params: {peaks: [1003, 1450, 2930]}
    results: {spectral_RMSE_pct: 12.0, classification_acc_pct: 82}
  - solver: MCR-ALS
    params: {components: 4, n_iter: 100}
    results: {spectral_RMSE_pct: 5.5, classification_acc_pct: 93}
  - solver: NMF-Raman
    params: {components: 4, n_iter: 200}
    results: {spectral_RMSE_pct: 4.2, classification_acc_pct: 96}
quality_scoring:
  - {max_RMSE: 4.5, Q: 1.00}
  - {max_RMSE: 6.0, Q: 0.90}
  - {max_RMSE: 8.0, Q: 0.80}
  - {max_RMSE: 12.0, Q: 0.75}
```

**Baseline solver:** MCR-ALS — spectral RMSE 5.5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Spectral RMSE (%) | Class. acc (%) | Runtime | Q |
|--------|---------------------|----------------|---------|---|
| Peak-Ratio | 12.0 | 82 | 1 s | 0.75 |
| MCR-ALS | 5.5 | 93 | 30 s | 0.90 |
| NMF-Raman | 4.2 | 96 | 1 min | 1.00 |
| DL-Raman (1D-CNN) | 3.8 | 97 | 2 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (NMF/DL):    300 × 1.00 = 300 PWM
Floor:                 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p137_hash>",
  "h_s": "sha256:<spec137_hash>",
  "h_b": "sha256:<bench137_hash>",
  "r": {"residual_norm": 0.038, "error_bound": 0.08, "ratio": 0.48},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep raman_imaging
pwm-node verify raman_imaging/ramancell_s1.yaml
pwm-node mine raman_imaging/ramancell_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
