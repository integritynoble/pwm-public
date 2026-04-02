# Principle #124 — Vibration-Based Damage Detection

**Domain:** Industrial Inspection & NDE | **Carrier:** Mechanical Vibration | **Difficulty:** Practitioner (δ=3)
**DAG:** G.cw --> F.dft --> S.spectral | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.cw-->F.dft-->S.spectral    VDD         BridgeModal-30     Identify
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  VIBRATION-BASED DAMAGE DETECTION  P = (E, G, W, C)  #124      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ [M]{ü} + [C]{u̇} + [K]{u} = {f(t)}                   │
│        │ Damage → ΔK → Δω_n, Δφ_n, Δζ_n                      │
│        │ FRF: H(ω) = Σ_n φ_n φ_nᵀ / (ω_n² − ω² + 2iζ_nω_nω)│
│        │ Inverse: detect/locate damage from modal parameter Δ  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.cw] --> [F.dft] --> [S.spectral]                      │
│        │  ModalExcite  ModalFFT  FreqIdent                      │
│        │ V={G.cw, F.dft, S.spectral}  A={G.cw-->F.dft, F.dft-->S.spectral}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (modal parameters always extractable)   │
│        │ Uniqueness: LIMITED (symmetric damage ambiguity)        │
│        │ Stability: κ ≈ 30 (large damage), κ ≈ 200 (small)    │
│        │ Mismatch: temperature effects, boundary condition var. │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = damage detection accuracy (primary), localization  │
│        │ q = 1.0 (modal identification convergence)            │
│        │ T = {detection_accuracy, location_error, severity_est} │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Sensor count and placement resolve target mode shapes | PASS |
| S2 | Frequency shifts exceed measurement uncertainty for target damage | PASS |
| S3 | Modal identification (SSI/ERA) converges for measured data | PASS |
| S4 | Detection accuracy ≥ 90% for stiffness loss ≥ 10% in one element | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# vibration_damage/bridgemodal_s1.yaml
principle_ref: sha256:<p124_hash>
omega:
  sensors: 16
  sampling_Hz: 1000
  modes_extracted: 10
  structure: steel_bridge_girder
  length_m: 20
E:
  forward: "[M]u'' + [C]u' + [K]u = f"
  damage_indicator: "MAC, COMAC, flexibility_change"
I:
  dataset: BridgeModal_30
  samples: 30
  damage_scenarios: [bolt_loosening, crack, corrosion_section_loss]
  noise: {type: gaussian, SNR_dB: 25}
O: [detection_accuracy, location_accuracy]
epsilon:
  detection_accuracy_min: 0.90
  location_accuracy_min: 0.80
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 16 sensors at 1 kHz resolve first 10 modes of 20 m girder | PASS |
| S2 | κ ≈ 30 for 10% stiffness reduction at SNR=25 dB | PASS |
| S3 | SSI-COV converges for 10 modes at specified noise level | PASS |
| S4 | Detection accuracy ≥ 0.90 for target damage scenarios | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# vibration_damage/benchmark_s1.yaml
spec_ref: sha256:<spec124_hash>
principle_ref: sha256:<p124_hash>
dataset:
  name: BridgeModal_30
  samples: 30
  channels: 16
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Frequency-Shift
    params: {modes: 5}
    results: {detection: 0.78, location: 0.60}
  - solver: Flexibility-Matrix
    params: {modes: 10}
    results: {detection: 0.88, location: 0.78}
  - solver: Bayesian-Model-Update
    params: {mcmc_samples: 10000}
    results: {detection: 0.95, location: 0.90}
quality_scoring:
  - {min_detection: 0.95, Q: 1.00}
  - {min_detection: 0.90, Q: 0.90}
  - {min_detection: 0.85, Q: 0.80}
  - {min_detection: 0.80, Q: 0.75}
```

**Baseline solver:** Frequency-Shift — detection 0.78
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Detection Acc. | Location Acc. | Runtime | Q |
|--------|----------------|---------------|---------|---|
| Frequency-Shift | 0.78 | 0.60 | 0.1 s | 0.75 |
| Flexibility-Matrix | 0.88 | 0.78 | 1 s | 0.85 |
| Bayesian-Model-Update | 0.95 | 0.90 | 300 s | 1.00 |
| Autoencoder-SHM | 0.93 | 0.85 | 0.5 s | 0.95 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (Bayesian):  300 × 1.00 = 300 PWM
Floor:                 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p124_hash>",
  "h_s": "sha256:<spec124_hash>",
  "h_b": "sha256:<bench124_hash>",
  "r": {"residual_norm": 0.05, "error_bound": 0.10, "ratio": 0.50},
  "c": {"fitted_rate": 0.95, "theoretical_rate": 1.0, "K": 10},
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
pwm-node benchmarks | grep vibration_damage
pwm-node verify vibration_damage/bridgemodal_s1.yaml
pwm-node mine vibration_damage/bridgemodal_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
