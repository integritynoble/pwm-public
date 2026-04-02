# Principle #118 — X-ray Fluorescence (XRF) Imaging

**Domain:** Industrial Inspection & NDE | **Carrier:** X-ray Photon | **Difficulty:** Practitioner (δ=3)
**DAG:** G.beam --> K.scatter.inelastic --> S.spectral | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.beam-->K.scatter.inelastic-->S.spectral    XRF-img     AlloyMap-30        Deconv
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  X-RAY FLUORESCENCE (XRF) IMAGING  P = (E, G, W, C)  #118      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I_k(x,y) = η_k ∫ σ_k(E) Φ(E) C_k(x,y,z) dz dE      │
│        │ σ_k = photoelectric cross-section for element k        │
│        │ Fluorescence yield η_k; concentration C_k              │
│        │ Inverse: quantify elemental maps C_k(x,y) from spectra│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.beam] --> [K.scatter.inelastic] --> [S.spectral]      │
│        │  XrayBeam  Fluorescence  EnergyDisperse                │
│        │ V={G.beam, K.scatter.inelastic, S.spectral}  A={G.beam-->K.scatter.inelastic, K.scatter.inelastic-->S.spectral}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (characteristic lines always emitted)   │
│        │ Uniqueness: YES (unique Kα/Kβ lines per element)       │
│        │ Stability: κ ≈ 8 (major elem.), κ ≈ 50 (trace elem.) │
│        │ Mismatch: matrix effects, self-absorption, overlap     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = concentration RMSE wt% (primary), LOD ppm (sec.)  │
│        │ q = 1.0 (fundamental parameter method convergence)    │
│        │ T = {concentration_RMSE, LOD_ppm, spectral_residual}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Primary beam energy exceeds absorption edges of target elements | PASS |
| S2 | Peak-to-background ratio sufficient for quantification above LOD | PASS |
| S3 | Fundamental parameter iteration converges for matrix correction | PASS |
| S4 | RMSE ≤ 0.5 wt% for major elements (> 1 wt%) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# xrf_imaging/alloymap_s1.yaml
principle_ref: sha256:<p118_hash>
omega:
  beam_energy_keV: 40
  spot_size_um: 50
  dwell_time_ms: 100
  detector: SDD
  energy_resolution_eV: 130
E:
  forward: "I_k = eta_k * sigma_k * Phi * C_k * rho * d"
  model: "fundamental parameters with matrix correction"
I:
  dataset: AlloyMap_30
  samples: 30
  elements: [Fe, Ni, Cr, Mo, Ti]
  noise: {type: poisson, counts_per_pixel: 5000}
O: [concentration_RMSE, LOD_ppm]
epsilon:
  RMSE_max: 0.5
  LOD_max: 100
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 40 keV exceeds Fe K-edge (7.1 keV), Ni K-edge (8.3 keV) | PASS |
| S2 | κ ≈ 8 for Fe, Ni, Cr at 5000 counts/pixel | PASS |
| S3 | FP iteration converges in ≤ 10 cycles for alloy matrix | PASS |
| S4 | RMSE ≤ 0.5 wt% feasible for major elements at given count rate | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# xrf_imaging/benchmark_s1.yaml
spec_ref: sha256:<spec118_hash>
principle_ref: sha256:<p118_hash>
dataset:
  name: AlloyMap_30
  samples: 30
  spectrum_channels: 2048
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: ROI-Integration
    params: {background: linear}
    results: {RMSE: 0.85, LOD: 200}
  - solver: Fundamental-Parameters
    params: {iterations: 10}
    results: {RMSE: 0.42, LOD: 80}
  - solver: PyMCA-Batch
    params: {fit: gaussian}
    results: {RMSE: 0.35, LOD: 60}
quality_scoring:
  - {max_RMSE: 0.35, Q: 1.00}
  - {max_RMSE: 0.50, Q: 0.90}
  - {max_RMSE: 0.70, Q: 0.80}
  - {max_RMSE: 1.00, Q: 0.75}
```

**Baseline solver:** ROI-Integration — RMSE 0.85 wt%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | RMSE (wt%) | LOD (ppm) | Runtime | Q |
|--------|-----------|-----------|---------|---|
| ROI-Integration | 0.85 | 200 | 0.1 s | 0.75 |
| Fundamental-Parameters | 0.42 | 80 | 5 s | 0.92 |
| PyMCA-Batch | 0.35 | 60 | 10 s | 1.00 |
| DL-XRF | 0.38 | 70 | 0.5 s | 0.95 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (PyMCA):  300 × 1.00 = 300 PWM
Floor:              300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p118_hash>",
  "h_s": "sha256:<spec118_hash>",
  "h_b": "sha256:<bench118_hash>",
  "r": {"residual_norm": 0.35, "error_bound": 0.50, "ratio": 0.70},
  "c": {"fitted_rate": 0.95, "theoretical_rate": 1.0, "K": 5},
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
pwm-node benchmarks | grep xrf_imaging
pwm-node verify xrf_imaging/alloymap_s1.yaml
pwm-node mine xrf_imaging/alloymap_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
