# Principle #142 — Brillouin Microscopy

**Domain:** Spectroscopy | **Carrier:** Photon (inelastic) | **Difficulty:** Research (δ=5)
**DAG:** G.pulse.laser --> K.scatter.inelastic --> F.dft | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.pulse.laser-->K.scatter.inelastic-->F.dft    Brillouin   BrilCell-12        FitVIPP
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  BRILLOUIN MICROSCOPY   P = (E, G, W, C)   Principle #142      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ν_B = 2n V_s sin(θ/2) / λ                             │
│        │ ν_B = Brillouin shift; V_s = sound velocity; n = RI    │
│        │ Linewidth Γ_B ∝ viscosity; shift → longitudinal modulus│
│        │ Inverse: map M'(r) = ρV_s² from Brillouin shift/width │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse.laser] --> [K.scatter.inelastic] --> [F.dft]    │
│        │  LaserExcite  BrillouinScatter  FreqAnalysis           │
│        │ V={G.pulse.laser, K.scatter.inelastic, F.dft}  A={G.pulse.laser-->K.scatter.inelastic, K.scatter.inelastic-->F.dft}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Brillouin scattering universal in mat.)│
│        │ Uniqueness: YES (shift + linewidth → modulus + viscosity│
│        │ Stability: κ ≈ 8 (VIPA spectrometer), κ ≈ 40 (FP)     │
│        │ Mismatch: elastic scattering leakage, temperature drift│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = shift accuracy MHz (primary), modulus RMSE (sec.)  │
│        │ q = 2.0 (Lorentzian fit converges quadratically)       │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | VIPA free spectral range, finesse, and pixel calibration yield ≤ 10 MHz accuracy | PASS |
| S2 | Lorentzian fit resolves shift and linewidth uniquely for SNR > 10 | PASS |
| S3 | Levenberg-Marquardt fitting converges within 20 iterations | PASS |
| S4 | Brillouin shift accuracy ≤ 20 MHz achievable at 100 ms integration | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# brillouin/brilcell_s1.yaml
principle_ref: sha256:<p142_hash>
omega:
  grid: [128, 128]
  pixel_um: 0.5
  laser_nm: 532
  spectrometer: VIPA
  FSR_GHz: 30
  finesse: 60
E:
  forward: "nu_B = 2*n*V_s*sin(theta/2)/lambda"
  fitting: "Lorentzian_LM"
I:
  dataset: BrilCell_12
  spectra: 16384
  noise: {type: poisson, peak: 1000}
  scenario: ideal
O: [shift_accuracy_MHz, modulus_RMSE_GPa]
epsilon:
  shift_accuracy_max: 30.0
  modulus_RMSE_max: 0.3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 30 GHz FSR with finesse 60 gives 500 MHz spectral resolution | PASS |
| S2 | κ ≈ 8 for Lorentzian fitting at 1000 peak counts | PASS |
| S3 | LM fitting converges within 15 iterations per spectrum | PASS |
| S4 | Shift accuracy ≤ 30 MHz feasible at 1000 counts | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# brillouin/benchmark_s1.yaml
spec_ref: sha256:<spec142_hash>
principle_ref: sha256:<p142_hash>
dataset:
  name: BrilCell_12
  maps: 12
  spectra_per: 16384
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Peak-Find
    params: {method: centroid}
    results: {shift_accuracy_MHz: 50, modulus_RMSE_GPa: 0.5}
  - solver: Lorentzian-LM
    params: {init: peak_based}
    results: {shift_accuracy_MHz: 20, modulus_RMSE_GPa: 0.2}
  - solver: Bayesian-Fit
    params: {model: lorentzian, prior: informative}
    results: {shift_accuracy_MHz: 12, modulus_RMSE_GPa: 0.12}
quality_scoring:
  - {max_shift: 15, Q: 1.00}
  - {max_shift: 25, Q: 0.90}
  - {max_shift: 35, Q: 0.80}
  - {max_shift: 50, Q: 0.75}
```

**Baseline solver:** Lorentzian-LM — shift accuracy 20 MHz
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Shift acc (MHz) | Modulus RMSE (GPa) | Runtime | Q |
|--------|-----------------|---------------------|---------|---|
| Peak-Find | 50 | 0.5 | 0.1 s | 0.75 |
| Lorentzian-LM | 20 | 0.2 | 5 s | 0.88 |
| Bayesian-Fit | 12 | 0.12 | 30 s | 1.00 |
| DL-Brillouin | 15 | 0.15 | 0.5 s | 0.98 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (Bayesian):  500 × 1.00 = 500 PWM
Floor:                 500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p142_hash>",
  "h_s": "sha256:<spec142_hash>",
  "h_b": "sha256:<bench142_hash>",
  "r": {"residual_norm": 0.012, "error_bound": 0.03, "ratio": 0.40},
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
| L4 Solution | — | 375–500 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep brillouin
pwm-node verify brillouin/brilcell_s1.yaml
pwm-node mine brillouin/brilcell_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
