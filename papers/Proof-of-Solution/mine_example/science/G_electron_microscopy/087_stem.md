# Principle #87 — Scanning TEM (STEM)

**Domain:** Electron Microscopy | **Carrier:** Electron | **Difficulty:** Standard (δ=3)
**DAG:** G.beam --> K.scatter.electron --> S.raster | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.beam-->K.scatter.electron-->S.raster    STEM-ADF   STEM-Materials     Denoise/SR
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  STEM   P = (E, G, W, C)   Principle #87                       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = ∫_{β_1}^{β_2} |Probe(r) ⊛ V(r)|² dΩ + n(r)  │
│        │ ADF-STEM: annular detector integrates scattered e⁻     │
│        │ Z-contrast: intensity ∝ Z^1.7 (atomic number)         │
│        │ Inverse: recover atomic-column positions from scan      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.beam] --> [K.scatter.electron] --> [S.raster]         │
│        │  E-Beam  Scatter  RasterScan                            │
│        │ V={G.beam, K.scatter.electron, S.raster}  A={G.beam-->K.scatter.electron, K.scatter.electron-->S.raster}   L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Z-contrast monotonic with composition) │
│        │ Uniqueness: YES for single-element columns              │
│        │ Stability: κ ≈ 10 (high-dose), κ ≈ 100 (low-dose)     │
│        │ Mismatch: probe aberrations, scan distortion, drift     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), atom-position RMSE (secondary)     │
│        │ q = 2.0 (deconvolution convergence)                   │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Probe size consistent with convergence angle; detector angles valid | PASS |
| S2 | Z-contrast monotonic → bounded inverse for composition mapping | PASS |
| S3 | Deconvolution converges for incoherent imaging model | PASS |
| S4 | PSNR ≥ 28 dB at standard STEM dose (10⁶ e⁻/probe position) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# stem/materials_s1_ideal.yaml
principle_ref: sha256:<p087_hash>
omega:
  grid: [256, 256]
  pixel_pm: 20
  voltage_kV: 200
  convergence_mrad: 21.4
E:
  forward: "y = ADF(Probe ⊛ V) + n"
  detector: "ADF, inner=60 mrad, outer=200 mrad"
I:
  dataset: STEM_Materials
  images: 40
  noise: {type: poisson, dose_e_per_pos: 1e6}
  scenario: ideal
O: [PSNR, SSIM, atom_RMSE_pm]
epsilon:
  PSNR_min: 28.0
  SSIM_min: 0.82
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 20 pm pixel at 200 kV resolves sub-Angstrom features | PASS |
| S2 | κ ≈ 10 at 10⁶ e⁻/position; well-posed | PASS |
| S3 | Richardson-Lucy converges for incoherent STEM model | PASS |
| S4 | PSNR ≥ 28 dB feasible at stated dose | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# stem/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec087_hash>
principle_ref: sha256:<p087_hash>
dataset:
  name: STEM_Materials
  images: 40
  size: [256, 256]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Wiener-ADF
    params: {SNR: 50}
    results: {PSNR: 29.2, SSIM: 0.851}
  - solver: Richardson-Lucy
    params: {n_iter: 100}
    results: {PSNR: 30.8, SSIM: 0.878}
  - solver: AtomNet
    params: {pretrained: STEM}
    results: {PSNR: 33.5, SSIM: 0.932}
quality_scoring:
  - {min: 34.0, Q: 1.00}
  - {min: 31.0, Q: 0.90}
  - {min: 29.0, Q: 0.80}
  - {min: 27.0, Q: 0.75}
```

**Baseline solver:** Wiener-ADF — PSNR 29.2 dB
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| Wiener-ADF | 29.2 | 0.851 | 0.2 s | 0.80 |
| Richardson-Lucy | 30.8 | 0.878 | 3 s | 0.88 |
| AtomNet | 33.5 | 0.932 | 1 s | 0.97 |
| STEM-Transformer | 34.2 | 0.945 | 2 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (STEM-TF):  300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p087_hash>",
  "h_s": "sha256:<spec087_hash>",
  "h_b": "sha256:<bench087_hash>",
  "r": {"residual_norm": 0.007, "error_bound": 0.02, "ratio": 0.35},
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

---

## Quick-Start

```bash
pwm-node benchmarks | grep stem
pwm-node verify stem/materials_s1_ideal.yaml
pwm-node mine stem/materials_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
