# Principle #136 — Cathodoluminescence (CL) Imaging

**Domain:** Scientific Instrumentation | **Carrier:** Electron → Photon | **Difficulty:** Advanced (δ=3)
**DAG:** G.beam --> K.scatter.inelastic --> S.spectral | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.beam-->K.scatter.inelastic-->S.spectral    CL          CLMineral-15       Spectral
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CATHODOLUMINESCENCE IMAGING   P = (E, G, W, C)   #136         │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I_CL(λ, r) = η(λ) · G(E₀, r) · n_e(r)               │
│        │ η = luminescence efficiency; G = generation volume     │
│        │ E₀ = beam energy; spectral peaks encode defects/comp.  │
│        │ Inverse: map composition/defects from hyperspectral CL │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.beam] --> [K.scatter.inelastic] --> [S.spectral]      │
│        │  E-Beam  Luminescence  SpectralDetect                  │
│        │ V={G.beam, K.scatter.inelastic, S.spectral}  A={G.beam-->K.scatter.inelastic, K.scatter.inelastic-->S.spectral}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (CL emission from band-gap / defect)   │
│        │ Uniqueness: YES (spectral peaks characteristic of comp)│
│        │ Stability: κ ≈ 5 (bright emitters), κ ≈ 30 (weak CL)  │
│        │ Mismatch: beam damage, surface contamination, quench.  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = spectral RMSE (primary), spatial resolution (sec.) │
│        │ q = 2.0 (linear spectral unmixing)                     │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Beam energy, current, and spectrometer range yield detectable CL signal | PASS |
| S2 | Spectral peaks separated by ≥ 10 nm enable unique phase identification | PASS |
| S3 | Linear spectral unmixing converges in single pass (NNLS) | PASS |
| S4 | Spectral RMSE ≤ 5% achievable for minerals with strong CL emission | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# cathodoluminescence/clmineral_s1.yaml
principle_ref: sha256:<p136_hash>
omega:
  grid: [512, 512]
  pixel_nm: 50
  beam_keV: 10
  beam_current_nA: 1.0
  spectral_range_nm: [200, 900]
  spectral_channels: 512
E:
  forward: "I_CL(lambda, r) = eta(lambda) * G(E0, r) * n_e(r)"
  unmixing: "NNLS_spectral"
I:
  dataset: CLMineral_15
  images: 15
  noise: {type: poisson, peak: 2000}
  scenario: ideal
O: [spectral_RMSE_pct, phase_accuracy_pct]
epsilon:
  spectral_RMSE_max: 8.0
  phase_accuracy_min: 90.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 10 keV beam at 1 nA over 200–900 nm range covers visible CL bands | PASS |
| S2 | κ ≈ 5 for bright mineral CL with 512 spectral channels | PASS |
| S3 | NNLS spectral unmixing converges in one pass | PASS |
| S4 | Spectral RMSE ≤ 8% and phase accuracy ≥ 90% feasible | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# cathodoluminescence/benchmark_s1.yaml
spec_ref: sha256:<spec136_hash>
principle_ref: sha256:<p136_hash>
dataset:
  name: CLMineral_15
  images: 15
  size: [512, 512]
  spectral_channels: 512
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Peak-Fitting
    params: {model: gaussian, n_peaks: 5}
    results: {spectral_RMSE_pct: 8.5, phase_accuracy_pct: 88}
  - solver: NNLS-Unmixing
    params: {endmembers: 4}
    results: {spectral_RMSE_pct: 5.2, phase_accuracy_pct: 93}
  - solver: NMF-Spectral
    params: {components: 4, n_iter: 200}
    results: {spectral_RMSE_pct: 4.0, phase_accuracy_pct: 96}
quality_scoring:
  - {max_RMSE: 4.0, Q: 1.00}
  - {max_RMSE: 6.0, Q: 0.90}
  - {max_RMSE: 8.0, Q: 0.80}
  - {max_RMSE: 12.0, Q: 0.75}
```

**Baseline solver:** NNLS-Unmixing — spectral RMSE 5.2%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Spectral RMSE (%) | Phase acc. (%) | Runtime | Q |
|--------|---------------------|----------------|---------|---|
| Peak-Fitting | 8.5 | 88 | 5 s | 0.78 |
| NNLS-Unmixing | 5.2 | 93 | 2 s | 0.90 |
| NMF-Spectral | 4.0 | 96 | 30 s | 1.00 |
| DL-CL (HyperNet) | 3.8 | 97 | 1 s | 1.00 |

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
  "h_p": "sha256:<p136_hash>",
  "h_s": "sha256:<spec136_hash>",
  "h_b": "sha256:<bench136_hash>",
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
pwm-node benchmarks | grep cathodoluminescence
pwm-node verify cathodoluminescence/clmineral_s1.yaml
pwm-node mine cathodoluminescence/clmineral_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
