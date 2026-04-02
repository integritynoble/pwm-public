# Principle #141 — Laser-Induced Breakdown Spectroscopy (LIBS) Imaging

**Domain:** Spectroscopy | **Carrier:** Photon (plasma emission) | **Difficulty:** Advanced (δ=3)
**DAG:** G.pulse.laser --> K.scatter.inelastic --> S.spectral | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.pulse.laser-->K.scatter.inelastic-->S.spectral    LIBS        LIBSRock-15        Calib
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LIBS IMAGING   P = (E, G, W, C)   Principle #141              │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I(λ, r) = Σ_Z C_Z(r) · A_ki · g_k · exp(−E_k/kT) / U│
│        │ Plasma emission at characteristic wavelengths per Z    │
│        │ Boltzmann distribution governs line intensities         │
│        │ Inverse: quantify C_Z(r) from emission spectra          │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse.laser] --> [K.scatter.inelastic] --> [S.spectral]│
│        │  AblationLaser  PlasmaEmit  SpectralDisperse           │
│        │ V={G.pulse.laser, K.scatter.inelastic, S.spectral}  A={G.pulse.laser-->K.scatter.inelastic, K.scatter.inelastic-->S.spectral}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (plasma forms above ablation threshold) │
│        │ Uniqueness: YES (atomic lines per element Z unique)    │
│        │ Stability: κ ≈ 8 (homogeneous), κ ≈ 40 (matrix effect)│
│        │ Mismatch: matrix effects, self-absorption, shot noise  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = concentration RMSE (primary), LOD ppm (secondary)  │
│        │ q = 2.0 (univariate calibration linear)                │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Laser fluence, gate delay, and spectrometer range cover target emission lines | PASS |
| S2 | Calibration curves linear (R² ≥ 0.98) for major/minor elements | PASS |
| S3 | Univariate/multivariate calibration converges for matrix-matched standards | PASS |
| S4 | Concentration RMSE ≤ 10% for major elements (> 1 wt%) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# libs_imaging/libsrock_s1.yaml
principle_ref: sha256:<p141_hash>
omega:
  grid: [100, 100]
  pixel_um: 50
  laser_energy_mJ: 5
  gate_delay_us: 1.0
  spectral_range_nm: [200, 800]
  spectral_channels: 2048
E:
  forward: "I(lambda) = sum_Z C_Z * A_ki * g_k * exp(-E_k/kT) / U"
  calibration: "multivariate_PLS"
I:
  dataset: LIBSRock_15
  maps: 15
  noise: {type: poisson, peak: 10000}
  scenario: ideal
O: [concentration_RMSE_pct, LOD_ppm]
epsilon:
  concentration_RMSE_max: 12.0
  LOD_max: 100.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200–800 nm covers emission lines for Si, Al, Fe, Ca, Na, K | PASS |
| S2 | κ ≈ 8 for PLS with matrix-matched calibration | PASS |
| S3 | PLS converges for ≤ 10 latent variables | PASS |
| S4 | RMSE ≤ 12% for major elements at 10000 peak counts | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# libs_imaging/benchmark_s1.yaml
spec_ref: sha256:<spec141_hash>
principle_ref: sha256:<p141_hash>
dataset:
  name: LIBSRock_15
  maps: 15
  shots_per_map: 10000
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Univariate-Cal
    params: {line: "Fe_404.58nm"}
    results: {concentration_RMSE_pct: 15.0, LOD_ppm: 150}
  - solver: PLS-LIBS
    params: {n_components: 8}
    results: {concentration_RMSE_pct: 8.0, LOD_ppm: 60}
  - solver: CF-LIBS
    params: {T_plasma: auto}
    results: {concentration_RMSE_pct: 10.0, LOD_ppm: 80}
quality_scoring:
  - {max_RMSE: 8.0, Q: 1.00}
  - {max_RMSE: 10.0, Q: 0.90}
  - {max_RMSE: 12.0, Q: 0.80}
  - {max_RMSE: 16.0, Q: 0.75}
```

**Baseline solver:** PLS-LIBS — RMSE 8.0%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Conc. RMSE (%) | LOD (ppm) | Runtime | Q |
|--------|----------------|-----------|---------|---|
| Univariate-Cal | 15.0 | 150 | 1 s | 0.75 |
| CF-LIBS | 10.0 | 80 | 30 s | 0.85 |
| PLS-LIBS | 8.0 | 60 | 5 s | 1.00 |
| DL-LIBS (CNN-Quant) | 6.5 | 40 | 2 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (PLS/DL):    300 × 1.00 = 300 PWM
Floor:                 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p141_hash>",
  "h_s": "sha256:<spec141_hash>",
  "h_b": "sha256:<bench141_hash>",
  "r": {"residual_norm": 0.065, "error_bound": 0.12, "ratio": 0.54},
  "c": {"fitted_rate": 1.92, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep libs_imaging
pwm-node verify libs_imaging/libsrock_s1.yaml
pwm-node mine libs_imaging/libsrock_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
