# Principle #90 — Electron Energy-Loss Spectroscopy (EELS)

**Domain:** Electron Microscopy | **Carrier:** Electron | **Difficulty:** Standard (δ=3)
**DAG:** K.scatter.inelastic --> S.spectral | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.scatter.inelastic-->S.spectral    EELS-SI    EELS-CoreLoss      Unmixing
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  EELS   P = (E, G, W, C)   Principle #90                       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r,E) = [Probe(r) ⊛ σ(r,E)] ⊛_E PSF_spec(E) + n    │
│        │ σ(r,E) = inelastic scattering cross-section map        │
│        │ Spectral convolution with spectrometer PSF              │
│        │ Inverse: recover elemental maps from spectrum image     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.scatter.inelastic] --> [S.spectral]                   │
│        │  InelasticScatter  SpectralDisperse                     │
│        │ V={K.scatter.inelastic, S.spectral}  A={K.scatter.inelastic-->S.spectral}   L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (edge energies are element-specific)    │
│        │ Uniqueness: YES for well-separated edges               │
│        │ Stability: κ ≈ 20 (core-loss), κ ≈ 100 (low-loss)     │
│        │ Mismatch: energy drift, gain variation, plural scatter  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = element-map PSNR (primary), SSIM (secondary)       │
│        │ q = 2.0 (NMF/deconvolution convergence)               │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Energy channels match spectrometer dispersion; spatial grid consistent | PASS |
| S2 | Core-loss edges element-specific → bounded inverse for unmixing | PASS |
| S3 | NMF / MCR-ALS converge monotonically for non-negative spectra | PASS |
| S4 | Map PSNR ≥ 26 dB achievable at standard EELS dose | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# eels/coreloss_s1_ideal.yaml
principle_ref: sha256:<p090_hash>
omega:
  scan_grid: [128, 128]
  energy_channels: 2048
  energy_range_eV: [200, 1200]
  dispersion_eV_per_ch: 0.5
E:
  forward: "y(r,E) = Probe ⊛ σ(r,E) ⊛_E PSF_spec + n"
  spectrometer: "Gatan GIF, 0.5 eV/ch"
I:
  dataset: EELS_CoreLoss
  spectrum_images: 25
  noise: {type: poisson, dose_e_per_pos: 1e5}
  scenario: ideal
O: [PSNR_map, SSIM_map]
epsilon:
  PSNR_min: 26.0
  SSIM_min: 0.78
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 2048 channels at 0.5 eV/ch covers 200–1200 eV core-loss range | PASS |
| S2 | κ ≈ 20 for core-loss with well-separated edges | PASS |
| S3 | NMF converges for 128×128 spatial × 2048 spectral | PASS |
| S4 | PSNR ≥ 26 dB feasible at 10⁵ e⁻/position | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# eels/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec090_hash>
principle_ref: sha256:<p090_hash>
dataset:
  name: EELS_CoreLoss
  spectrum_images: 25
  size: [128, 128, 2048]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Power-Law-BG
    params: {window_eV: 50}
    results: {PSNR: 26.8, SSIM: 0.801}
  - solver: NMF
    params: {n_components: 5, n_iter: 500}
    results: {PSNR: 28.5, SSIM: 0.845}
  - solver: DeepEELS
    params: {pretrained: core_loss}
    results: {PSNR: 31.2, SSIM: 0.912}
quality_scoring:
  - {min: 32.0, Q: 1.00}
  - {min: 29.0, Q: 0.90}
  - {min: 27.0, Q: 0.80}
  - {min: 25.0, Q: 0.75}
```

**Baseline solver:** Power-Law-BG — PSNR 26.8 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| Power-Law-BG | 26.8 | 0.801 | 2 s | 0.80 |
| NMF | 28.5 | 0.845 | 30 s | 0.88 |
| DeepEELS | 31.2 | 0.912 | 5 s | 0.95 |
| EELS-Transformer | 32.4 | 0.935 | 8 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (EELS-TF):  300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p090_hash>",
  "h_s": "sha256:<spec090_hash>",
  "h_b": "sha256:<bench090_hash>",
  "r": {"residual_norm": 0.010, "error_bound": 0.025, "ratio": 0.40},
  "c": {"fitted_rate": 1.94, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 225–300 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep eels
pwm-node verify eels/coreloss_s1_ideal.yaml
pwm-node mine eels/coreloss_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
