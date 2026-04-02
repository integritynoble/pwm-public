# Principle #140 — FTIR Spectroscopic Imaging

**Domain:** Spectroscopy | **Carrier:** Infrared Photon | **Difficulty:** Advanced (δ=3)
**DAG:** G.broadband --> L.diag.spectral --> F.dft | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.broadband-->L.diag.spectral-->F.dft    FTIR        FTIRTissue-15      Unmix
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  FTIR SPECTROSCOPIC IMAGING   P = (E, G, W, C)   #140          │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ A(ν̃, r) = −log₁₀[I(ν̃,r)/I₀(ν̃)] = Σ_k ε_k(ν̃)c_k(r)d│
│        │ Beer-Lambert: absorbance linear in concentration       │
│        │ Interferogram → spectrum via FFT (Fourier transform)   │
│        │ Inverse: unmix c_k(r) from hyperspectral absorbance    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.broadband] --> [L.diag.spectral] --> [F.dft]          │
│        │  BroadbandSource  Interferogram  FourierTransform      │
│        │ V={G.broadband, L.diag.spectral, F.dft}  A={G.broadband-->L.diag.spectral, L.diag.spectral-->F.dft}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (IR-active modes always present)        │
│        │ Uniqueness: YES (fingerprint region 900–1800 cm⁻¹)    │
│        │ Stability: κ ≈ 5 (thin section), κ ≈ 30 (thick/scatter│
│        │ Mismatch: Mie scattering, water vapor, baseline drift  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = spectral RMSE (primary), classification acc (sec.) │
│        │ q = 2.0 (linear Beer-Lambert unmixing exact)           │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Spectral range, resolution, and pixel size cover fingerprint IR bands | PASS |
| S2 | Beer-Lambert linearity holds for thin sections (d < 10 µm); unique unmixing | PASS |
| S3 | NNLS / MCR-ALS converges monotonically for non-negative concentrations | PASS |
| S4 | Classification accuracy ≥ 90% for 5-class tissue histology | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# ftir_imaging/ftirtissue_s1.yaml
principle_ref: sha256:<p140_hash>
omega:
  grid: [128, 128]
  pixel_um: 5.5
  spectral_range_cm: [900, 4000]
  spectral_resolution_cm: 4
  spectral_points: 775
E:
  forward: "A(nu, r) = sum_k eps_k(nu) * c_k(r) * d"
  unmixing: "MCR-ALS"
I:
  dataset: FTIRTissue_15
  images: 15
  noise: {type: gaussian, sigma_abs: 0.005}
  scenario: ideal
O: [spectral_RMSE_pct, classification_acc_pct]
epsilon:
  spectral_RMSE_max: 8.0
  classification_acc_min: 88.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 900–4000 cm⁻¹ at 4 cm⁻¹ resolution covers fingerprint + amide bands | PASS |
| S2 | κ ≈ 5 for thin tissue sections at σ_abs = 0.005 | PASS |
| S3 | MCR-ALS converges within 100 iterations with non-negativity | PASS |
| S4 | Classification ≥ 88% feasible for 5-class histopathology | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# ftir_imaging/benchmark_s1.yaml
spec_ref: sha256:<spec140_hash>
principle_ref: sha256:<p140_hash>
dataset:
  name: FTIRTissue_15
  images: 15
  size: [128, 128]
  spectral_points: 775
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Peak-Height
    params: {bands: [1650, 1550, 1080]}
    results: {spectral_RMSE_pct: 14.0, classification_acc_pct: 78}
  - solver: MCR-ALS
    params: {components: 5, n_iter: 100}
    results: {spectral_RMSE_pct: 5.8, classification_acc_pct: 91}
  - solver: RF-FTIR
    params: {features: PCA_20, trees: 500}
    results: {spectral_RMSE_pct: 4.5, classification_acc_pct: 95}
quality_scoring:
  - {max_RMSE: 5.0, Q: 1.00}
  - {max_RMSE: 7.0, Q: 0.90}
  - {max_RMSE: 9.0, Q: 0.80}
  - {max_RMSE: 14.0, Q: 0.75}
```

**Baseline solver:** MCR-ALS — spectral RMSE 5.8%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Spectral RMSE (%) | Class. acc (%) | Runtime | Q |
|--------|---------------------|----------------|---------|---|
| Peak-Height | 14.0 | 78 | 0.5 s | 0.75 |
| MCR-ALS | 5.8 | 91 | 30 s | 0.88 |
| RF-FTIR | 4.5 | 95 | 5 s | 1.00 |
| DL-FTIR (1D-ResNet) | 3.8 | 97 | 1 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (RF/DL):     300 × 1.00 = 300 PWM
Floor:                 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p140_hash>",
  "h_s": "sha256:<spec140_hash>",
  "h_b": "sha256:<bench140_hash>",
  "r": {"residual_norm": 0.038, "error_bound": 0.08, "ratio": 0.48},
  "c": {"fitted_rate": 1.96, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep ftir_imaging
pwm-node verify ftir_imaging/ftirtissue_s1.yaml
pwm-node mine ftir_imaging/ftirtissue_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
