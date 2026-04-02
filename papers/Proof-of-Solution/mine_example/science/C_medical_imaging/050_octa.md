# Principle #50 — OCT Angiography (OCTA)

**Domain:** Medical Imaging | **Carrier:** Photon | **Difficulty:** Standard (δ=3)
**DAG:** [G.broadband] --> [K.green.coherent] --> [∫.spectral] --> [∫.temporal]

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.broadband --> K.green.coherent --> ∫.spectral --> ∫.temporal    OCTA-vasc    RetinaOCTA-20     SSADA
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  OCT ANGIOGRAPHY (OCTA)   P = (E, G, W, C)   Principle #50     │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ D(r) = var{ A_n(r) } or |A_n − A_{n-1}| over repeats  │
│        │ A_n(r) = |FT⁻¹{S_n(k)}|  (OCT amplitude at repeat n) │
│        │ Inverse: detect vascular motion contrast from temporal │
│        │ decorrelation of sequential OCT B-scans                │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.broadband] ──→ [K.green.coherent] ──→ [∫.spectral] ──→ [∫.temporal]│
│        │  Propagate Interfere Fourier  Accumulate Detect        │
│        │ V={G.broadband,K.green.coherent,∫.spectral,∫.temporal}  A={G.broadband→K.green.coherent, K.green.coherent→∫.spectral, ∫.spectral→∫.temporal}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (blood flow causes measurable decor.)   │
│        │ Uniqueness: CONDITIONAL (binary flow/no-flow map)      │
│        │ Stability: κ ≈ 10 (high SNR), κ ≈ 35 (low SNR)        │
│        │ Mismatch: Δ_bulk_motion, Δ_SNR (projection artifacts) │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = vessel Dice (primary), FAZ area error % (second.)  │
│        │ q = 1.0 (decorrelation estimator convergence)         │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Interscan time and number of repeats resolve capillary flow | PASS |
| S2 | Decorrelation signal above noise floor for capillary velocities | PASS |
| S3 | SSADA / OMAG decorrelation estimator converges | PASS |
| S4 | Vessel Dice ≥ 0.75 achievable for retinal OCTA at SNR > 30 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# octa/retina_s1_ideal.yaml
principle_ref: sha256:<p050_hash>
omega:
  axial_pixels: 1024
  lateral_pixels: 304
  n_repeats: 4
  interscan_ms: 3.5
  wavelength_nm: 840
E:
  forward: "D(r) = var{A_n(r)} over n repeats"
  contrast: "split-spectrum amplitude decorrelation"
I:
  dataset: RetinaOCTA_20
  volumes: 20
  noise: {type: speckle, SNR_dB: 32}
  scenario: ideal
O: [vessel_Dice, FAZ_area_error_pct]
epsilon:
  Dice_min: 0.75
  FAZ_error_max_pct: 10.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 4 repeats at 3.5 ms interscan detects flow > 0.3 mm/s | PASS |
| S2 | κ ≈ 10 within well-posed regime for 4-repeat decorrelation | PASS |
| S3 | SSADA converges for speckle noise model | PASS |
| S4 | Dice ≥ 0.75 feasible at SNR=32 dB | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# octa/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec050_hash>
principle_ref: sha256:<p050_hash>
dataset:
  name: RetinaOCTA_20
  volumes: 20
  size: [1024, 304, 304]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: SSADA
    params: {n_splits: 4}
    results: {Dice: 0.76, FAZ_error_pct: 8.5}
  - solver: OMAG
    params: {threshold: 0.1}
    results: {Dice: 0.79, FAZ_error_pct: 7.0}
  - solver: DeepOCTA
    params: {pretrained: true}
    results: {Dice: 0.88, FAZ_error_pct: 3.5}
quality_scoring:
  - {min_Dice: 0.90, Q: 1.00}
  - {min_Dice: 0.85, Q: 0.90}
  - {min_Dice: 0.78, Q: 0.80}
  - {min_Dice: 0.75, Q: 0.75}
```

**Baseline solver:** SSADA — Dice 0.76
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Dice | FAZ Error (%) | Runtime | Q |
|--------|------|---------------|---------|---|
| SSADA | 0.76 | 8.5 | 1 s | 0.75 |
| OMAG | 0.79 | 7.0 | 1.5 s | 0.80 |
| DeepOCTA (learned) | 0.88 | 3.5 | 0.5 s | 0.94 |
| VesselFormer | 0.92 | 2.0 | 1 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (VesselFormer):  300 × 1.00 = 300 PWM
Floor:                     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p050_hash>",
  "h_s": "sha256:<spec050_hash>",
  "h_b": "sha256:<bench050_hash>",
  "r": {"residual_norm": 0.025, "error_bound": 0.05, "ratio": 0.50},
  "c": {"fitted_rate": 0.95, "theoretical_rate": 1.0, "K": 3},
  "Q": 0.94,
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
pwm-node benchmarks | grep octa
pwm-node verify octa/retina_s1_ideal.yaml
pwm-node mine octa/retina_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
