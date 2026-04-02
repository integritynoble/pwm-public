# Principle #134 — X-ray Fluorescence Tomography

**Domain:** Scientific Instrumentation | **Carrier:** X-ray Photon | **Difficulty:** Research (δ=5)
**DAG:** G.beam --> K.scatter.inelastic --> Pi.radon --> S.spectral | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.beam-->K.scatter.inelastic-->Pi.radon-->S.spectral    XRF-T       XRFPhantom-12      MLEM/FBP
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  X-RAY FLUORESCENCE TOMOGRAPHY   P = (E, G, W, C)   #134       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I_f(s,θ) = ∫ ρ_Z(x,y) · A_in(x,y,θ) · A_out(x,y,θ) dl│
│        │ A_in/out = self-absorption along incident/fluorescent path│
│        │ ρ_Z = elemental concentration; energy-dispersive detect│
│        │ Inverse: reconstruct ρ_Z(x,y) correcting self-absorpt. │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.beam] --> [K.scatter.inelastic] --> [Pi.radon] --> [S.spectral]│
│        │  XrayBeam  Fluorescence  TomoProject  EnergyDisperse   │
│        │ V={G.beam, K.scatter.inelastic, Pi.radon, S.spectral}  A={G.beam-->K.scatter.inelastic, K.scatter.inelastic-->Pi.radon, Pi.radon-->S.spectral}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (fluorescence yield well-defined per Z) │
│        │ Uniqueness: YES (with self-absorption correction)      │
│        │ Stability: κ ≈ 12 (trace elements), κ ≈ 50 (dense mat)│
│        │ Mismatch: self-absorption errors, scatter background   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = concentration RMSE (primary), detection limit (sec)│
│        │ q = 1.5 (MLEM with self-absorption correction)        │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Excitation energy above K-edge of target elements; detector solid angle consistent | PASS |
| S2 | Self-absorption correction yields bounded inverse for ρ < 1 g/cm³ | PASS |
| S3 | MLEM with absorption correction converges within 50 iterations | PASS |
| S4 | Concentration RMSE ≤ 5% achievable for ppm-level trace elements | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# xrf_tomography/xrfphantom_s1.yaml
principle_ref: sha256:<p134_hash>
omega:
  grid: [256, 256]
  pixel_um: 2.0
  excitation_keV: 15.0
  elements: [Fe, Cu, Zn]
  n_projections: 180
  dwell_ms: 100
E:
  forward: "I_f = integral(rho_Z * A_in * A_out) dl"
  correction: "self_absorption_iterative"
I:
  dataset: XRFPhantom_12
  scans: 12
  noise: {type: poisson, counts_per_pixel: 500}
  scenario: ideal
O: [concentration_RMSE_pct, detection_limit_ppm]
epsilon:
  concentration_RMSE_max: 8.0
  detection_limit_max: 10.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 15 keV excitation above Fe/Cu/Zn K-edges; 2 µm pixel matches beam | PASS |
| S2 | κ ≈ 12 with self-absorption correction for biological matrices | PASS |
| S3 | MLEM converges within 30 iterations for 180 projections | PASS |
| S4 | Concentration RMSE ≤ 8% feasible at 500 counts/pixel | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# xrf_tomography/benchmark_s1.yaml
spec_ref: sha256:<spec134_hash>
principle_ref: sha256:<p134_hash>
dataset:
  name: XRFPhantom_12
  scans: 12
  projections: 180
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FBP-NoCorr
    params: {filter: shepp_logan}
    results: {concentration_RMSE_pct: 18.0, detection_limit_ppm: 20}
  - solver: MLEM-AbsCorr
    params: {n_iter: 50}
    results: {concentration_RMSE_pct: 6.5, detection_limit_ppm: 8}
  - solver: Iterative-SelfAbs
    params: {n_iter: 30, correction: full}
    results: {concentration_RMSE_pct: 4.2, detection_limit_ppm: 5}
quality_scoring:
  - {max_RMSE: 5.0, Q: 1.00}
  - {max_RMSE: 7.0, Q: 0.90}
  - {max_RMSE: 10.0, Q: 0.80}
  - {max_RMSE: 15.0, Q: 0.75}
```

**Baseline solver:** MLEM-AbsCorr — RMSE 6.5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Conc. RMSE (%) | Det. limit (ppm) | Runtime | Q |
|--------|----------------|-------------------|---------|---|
| FBP-NoCorr | 18.0 | 20 | 2 s | 0.75 |
| MLEM-AbsCorr | 6.5 | 8 | 3 min | 0.90 |
| Iterative-SelfAbs | 4.2 | 5 | 8 min | 1.00 |
| DL-XRF (AbsNet) | 4.8 | 6 | 15 s | 0.95 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (Iter-SelfAbs):  500 × 1.00 = 500 PWM
Floor:                     500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p134_hash>",
  "h_s": "sha256:<spec134_hash>",
  "h_b": "sha256:<bench134_hash>",
  "r": {"residual_norm": 0.042, "error_bound": 0.08, "ratio": 0.53},
  "c": {"fitted_rate": 1.45, "theoretical_rate": 1.5, "K": 3},
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
| L4 Solution | — | 375–500 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep xrf_tomography
pwm-node verify xrf_tomography/xrfphantom_s1.yaml
pwm-node mine xrf_tomography/xrfphantom_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
