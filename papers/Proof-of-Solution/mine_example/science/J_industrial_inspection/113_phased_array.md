# Principle #113 — Phased-Array Ultrasonic Testing (PAUT)

**Domain:** Industrial Inspection | **Carrier:** Acoustic | **Difficulty:** Standard (δ=3)
**DAG:** G.pulse.acoustic --> K.green.acoustic --> integral.fullmatrix | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │        G.pulse.acoustic-->K.green.acoustic-->integral.fullmatrix    PAUT       UT-Weld             TFM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PAUT   P = (E, G, W, C)   Principle #113                      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(t,tx,rx) = Σ_k r_k·g(t−(d_tx_k+d_rx_k)/v) + n     │
│        │ Full matrix capture: all Tx-Rx pairs recorded          │
│        │ TFM: total focusing method for synthetic focusing      │
│        │ Inverse: image reflectivity from FMC data             │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse.acoustic] --> [K.green.acoustic] --> [integral.fullmatrix]│
│        │ ArrayPulse  AcousticProp  FMCSynth                      │
│        │ V={G.pulse.acoustic, K.green.acoustic, integral.fullmatrix}  A={G.pulse.acoustic-->K.green.acoustic, K.green.acoustic-->integral.fullmatrix}   L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (TFM delay-and-sum is well-defined)    │
│        │ Uniqueness: YES within diffraction limit                │
│        │ Stability: κ ≈ 8 (well-coupled), κ ≈ 40 (rough surf.) │
│        │ Mismatch: velocity error, couplant variation            │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = SNR (primary), detection probability (secondary)   │
│        │ q = 2.0 (TFM convergence with element count)         │
│        │ T = {SNR_dB, PoD, K_resolutions}                       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Array element count and pitch consistent with beam steering | PASS |
| S2 | TFM well-conditioned for stated material velocity | PASS |
| S3 | TFM delay-and-sum converges with increasing elements | PASS |
| S4 | SNR > 20 dB achievable for 2 mm defect at 50 mm depth | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# paut/weld_s1_ideal.yaml
principle_ref: sha256:<p113_hash>
omega:
  elements: 64
  pitch_mm: 0.6
  frequency_MHz: 5
  velocity_m_s: 5900
E:
  forward: "y(t,tx,rx) = Σ r_k·g(t−ToF) + n"
  method: FMC_TFM
I:
  dataset: UT_Weld
  scans: 50
  noise: {type: gaussian, SNR_dB: 25}
  scenario: ideal
O: [SNR_dB, PoD_pct, sizing_error_mm]
epsilon:
  SNR_min_dB: 20.0
  PoD_min_pct: 90.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 64 elements at 0.6 mm pitch; 5 MHz in steel | PASS |
| S2 | TFM with 64 elements → κ ≈ 8 | PASS |
| S3 | TFM converges for FMC data | PASS |
| S4 | SNR > 20 dB and PoD > 90% feasible | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# paut/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec113_hash>
principle_ref: sha256:<p113_hash>
dataset:
  name: UT_Weld
  scans: 50
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: TFM
    results: {SNR_dB: 22.5, PoD_pct: 93.2, sizing_err_mm: 0.8}
  - solver: Adaptive-TFM
    results: {SNR_dB: 26.1, PoD_pct: 96.5, sizing_err_mm: 0.5}
  - solver: DL-TFM
    results: {SNR_dB: 30.2, PoD_pct: 98.8, sizing_err_mm: 0.3}
quality_scoring:
  - {min_SNR: 30.0, Q: 1.00}
  - {min_SNR: 26.0, Q: 0.90}
  - {min_SNR: 22.0, Q: 0.80}
  - {min_SNR: 18.0, Q: 0.75}
```

**Baseline:** TFM — SNR 22.5 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | SNR (dB) | PoD (%) | Q |
|--------|----------|---------|---|
| TFM | 22.5 | 93.2 | 0.80 |
| Adaptive-TFM | 26.1 | 96.5 | 0.90 |
| DL-TFM | 30.2 | 98.8 | 1.00 |

### Reward: `R = 100 × 3 × q` → Best: 300 PWM | Floor: 225 PWM

```json
{
  "h_p": "sha256:<p113_hash>", "Q": 0.90,
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

## Quick-Start

```bash
pwm-node benchmarks | grep paut
pwm-node mine paut/weld_s1_ideal.yaml
```
