# Principle #95 — Time-of-Flight Depth Imaging

**Domain:** Depth Imaging | **Carrier:** Photon (NIR) | **Difficulty:** Standard (δ=3)
**DAG:** G.pulse --> K.green --> integral.temporal --> N.phase | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.pulse-->K.green-->integral.temporal-->N.phase    ToF-depth  ToF-Indoor         DepthSR
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  TOF DEPTH   P = (E, G, W, C)   Principle #95                  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = A(r)·h(t − 2d(r)/c) ⊛ g(t) + n(r)            │
│        │ h = modulated illumination; g = correlation waveform   │
│        │ d(r) = depth at pixel r; A = amplitude/albedo          │
│        │ Inverse: recover depth d(r) from phase measurements    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse] --> [K.green] --> [integral.temporal] --> [N.phase]│
│        │ ModIllum  Propagate  Correlate  PhaseEst                │
│        │ V={G.pulse, K.green, integral.temporal, N.phase}  A={G.pulse-->K.green, K.green-->integral.temporal, integral.temporal-->N.phase}   L_DAG=2.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (phase → depth is bijective in range)   │
│        │ Uniqueness: YES within unambiguous range c/(2f_mod)     │
│        │ Stability: κ ≈ 8 (high SNR), κ ≈ 50 (low albedo)      │
│        │ Mismatch: multipath interference, motion blur            │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = depth MAE (primary), RMSE (secondary)              │
│        │ q = 2.0 (least-squares phase estimation)              │
│        │ T = {depth_MAE, residual_norm, K_resolutions}          │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Modulation frequency consistent with max range; pixel count valid | PASS |
| S2 | Phase-to-depth bijective in unambiguous range → bounded inverse | PASS |
| S3 | 4-tap phase unwrapping converges for single-frequency | PASS |
| S4 | Depth MAE < 5 mm achievable at SNR > 30 dB | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# tof_depth/indoor_s1_ideal.yaml
principle_ref: sha256:<p095_hash>
omega:
  grid: [240, 320]
  max_range_m: 5.0
  modulation_MHz: 30
E:
  forward: "y = A·h(t − 2d/c) ⊛ g + n"
  correlation_taps: 4
I:
  dataset: ToF_Indoor
  scenes: 40
  noise: {type: shot_noise, integration_ms: 10}
  scenario: ideal
O: [depth_MAE_mm, depth_RMSE_mm]
epsilon:
  depth_MAE_max_mm: 5.0
  depth_RMSE_max_mm: 8.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | f_mod=30 MHz → unambiguous range 5 m matches max_range | PASS |
| S2 | κ ≈ 8 at 10 ms integration; well-posed | PASS |
| S3 | 4-tap arctangent estimator converges | PASS |
| S4 | MAE < 5 mm feasible at stated integration time | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# tof_depth/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec095_hash>
principle_ref: sha256:<p095_hash>
dataset:
  name: ToF_Indoor
  scenes: 40
  size: [240, 320]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: 4-Tap-Phase
    params: {unwrap: basic}
    results: {depth_MAE_mm: 4.2, depth_RMSE_mm: 6.8}
  - solver: Multipath-Correct
    params: {n_freq: 2}
    results: {depth_MAE_mm: 2.8, depth_RMSE_mm: 4.5}
  - solver: DeepToF
    params: {pretrained: indoor}
    results: {depth_MAE_mm: 1.5, depth_RMSE_mm: 2.8}
quality_scoring:
  - {max_MAE: 1.5, Q: 1.00}
  - {max_MAE: 3.0, Q: 0.90}
  - {max_MAE: 5.0, Q: 0.80}
  - {max_MAE: 8.0, Q: 0.75}
```

**Baseline solver:** 4-Tap-Phase — MAE 4.2 mm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | MAE (mm) | RMSE (mm) | Runtime | Q |
|--------|----------|-----------|---------|---|
| 4-Tap-Phase | 4.2 | 6.8 | 0.01 s | 0.80 |
| Multipath-Correct | 2.8 | 4.5 | 0.1 s | 0.90 |
| DeepToF | 1.5 | 2.8 | 0.05 s | 1.00 |
| ToF-Transformer | 1.2 | 2.2 | 0.08 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (ToF-TF):  300 × 1.00 = 300 PWM
Floor:               300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p095_hash>",
  "h_s": "sha256:<spec095_hash>",
  "h_b": "sha256:<bench095_hash>",
  "r": {"depth_MAE_mm": 1.5, "depth_RMSE_mm": 2.8},
  "c": {"fitted_rate": 1.98, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep tof_depth
pwm-node verify tof_depth/indoor_s1_ideal.yaml
pwm-node mine tof_depth/indoor_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
