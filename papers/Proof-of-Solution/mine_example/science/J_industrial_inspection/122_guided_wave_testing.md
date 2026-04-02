# Principle #122 — Guided Wave Testing

**Domain:** Industrial Inspection & NDE | **Carrier:** Acoustic Wave (Lamb/Torsional) | **Difficulty:** Research (δ=5)
**DAG:** G.pulse --> E.transcendental --> K.elastic --> integral.temporal | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.pulse-->E.transcendental-->K.elastic-->integral.temporal    GWT         PipeScreen-25      Locate
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  GUIDED WAVE TESTING   P = (E, G, W, C)   Principle #122        │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ u(x,t) = Σ_m A_m ψ_m(y) exp(i(k_m x − ωt))          │
│        │ Dispersion: ω = ω(k, mode); group velocity c_g(f)     │
│        │ Reflection from wall loss: R_m ∝ ΔZ/Z₀ (impedance)   │
│        │ Inverse: locate & size corrosion from mode reflections │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse] --> [E.transcendental] --> [K.elastic] --> [integral.temporal]│
│        │  Excite  DispersionEq  WaveGuide  TemporalAccum        │
│        │ V={G.pulse, E.transcendental, K.elastic, integral.temporal}  A={G.pulse-->E.transcendental, E.transcendental-->K.elastic, K.elastic-->integral.temporal}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Lamb/SH modes always propagate)        │
│        │ Uniqueness: LIMITED (mode conversion complicates)       │
│        │ Stability: κ ≈ 20 (T(0,1) mode), κ ≈ 100 (multimode)│
│        │ Mismatch: dispersion errors, coating attenuation       │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = location error m (primary), CSA accuracy (sec.)    │
│        │ q = 1.0 (dispersion-compensated focusing)             │
│        │ T = {location_error, CSA_RMSE, false_call_rate}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Excitation frequency selects non-dispersive T(0,1) mode region | PASS |
| S2 | Reflection coefficient detectable for ≥ 5% cross-sectional area loss | PASS |
| S3 | Dispersion compensation converges with known pipe properties | PASS |
| S4 | Location error ≤ ±50 mm over 30 m inspection range | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# guided_wave/pipescreen_s1.yaml
principle_ref: sha256:<p122_hash>
omega:
  pipe_OD_mm: 168
  wall_mm: 7.1
  frequency_kHz: 35
  mode: T(0,1)
  ring_elements: 24
  range_m: 30
E:
  forward: "R_m = DeltaZ/Z0 * mode_shape_overlap"
  dispersion: "Pochhammer-Chree for cylindrical waveguide"
I:
  dataset: PipeScreen_25
  samples: 25
  defect_types: [general_corrosion, circumferential_weld, support_clamp]
  noise: {type: coherent, SNR_dB: 25}
O: [location_error_mm, CSA_accuracy]
epsilon:
  location_error_max: 50
  CSA_accuracy_min: 0.80
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 35 kHz selects non-dispersive T(0,1) region for 168 mm pipe | PASS |
| S2 | κ ≈ 20 for T(0,1) in uncoated steel pipe | PASS |
| S3 | Group velocity dispersion correction converges at 35 kHz | PASS |
| S4 | Location error ≤ 50 mm feasible over 30 m range | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# guided_wave/benchmark_s1.yaml
spec_ref: sha256:<spec122_hash>
principle_ref: sha256:<p122_hash>
dataset:
  name: PipeScreen_25
  samples: 25
  ascan_length: 8192
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Envelope-Threshold
    params: {dB_threshold: -6}
    results: {location_error: 80, CSA_accuracy: 0.72}
  - solver: Dispersion-Compensated
    params: {chirp_z: true}
    results: {location_error: 35, CSA_accuracy: 0.84}
  - solver: Sparse-Defect-Recon
    params: {lambda: 0.1}
    results: {location_error: 20, CSA_accuracy: 0.91}
quality_scoring:
  - {max_loc_error: 20, Q: 1.00}
  - {max_loc_error: 35, Q: 0.90}
  - {max_loc_error: 50, Q: 0.80}
  - {max_loc_error: 80, Q: 0.75}
```

**Baseline solver:** Envelope-Threshold — location error 80 mm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Location Error (mm) | CSA Accuracy | Runtime | Q |
|--------|---------------------|--------------|---------|---|
| Envelope-Threshold | 80 | 0.72 | 0.05 s | 0.75 |
| Dispersion-Compensated | 35 | 0.84 | 1 s | 0.90 |
| Sparse-Defect-Recon | 20 | 0.91 | 10 s | 1.00 |
| DL-GuidedWave | 25 | 0.88 | 0.5 s | 0.95 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (Sparse):  500 × 1.00 = 500 PWM
Floor:               500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p122_hash>",
  "h_s": "sha256:<spec122_hash>",
  "h_b": "sha256:<bench122_hash>",
  "r": {"residual_norm": 20, "error_bound": 50, "ratio": 0.40},
  "c": {"fitted_rate": 0.95, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep guided_wave
pwm-node verify guided_wave/pipescreen_s1.yaml
pwm-node mine guided_wave/pipescreen_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
