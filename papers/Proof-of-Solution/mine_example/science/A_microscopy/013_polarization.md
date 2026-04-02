# Principle #13 — Polarization Microscopy

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Standard (δ=3)
**DAG:** L.diag.mueller --> ∫.temporal | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.diag.mueller-->∫.temporal  PolMicro  Birefringence-8  Stokes-Inv
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  POLARIZATION MICRO  P = (E, G, W, C)   Principle #13         │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y_k = M_analyzer(θ_k) · M_sample · S_in + n          │
│        │ S_in = Stokes vector; M = Mueller matrix of sample    │
│        │ k = 1..K polarizer orientations (K ≥ 4)              │
│        │ Inverse: recover retardance δ, orientation φ maps     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.diag.mueller] ──→ [∫.temporal]                      │
│        │  Modulate(Mueller)  Accumulate(intensity per analyzer)  │
│        │ V={L,∫}  A={L-->∫}   L_DAG=2.0                       │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (4+ measurements for 4 Stokes params) │
│        │ Uniqueness: YES (linearly independent analyzer angles)│
│        │ Stability: κ ≈ 10 (4 angles at 0,45,90,135°)        │
│        │ Mismatch: analyzer angle error, extinction ratio      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = retardance RMSE (rad), orientation error (deg)    │
│        │ q = 2.0 (linear least-squares, direct inversion)    │
│        │ T = {residual_norm, retardance_error, orient_error}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | K ≥ 4 analyzer orientations span Stokes space | PASS |
| S2 | Analyzer angles at 45° separation → κ ≈ 10 | PASS |
| S3 | Linear least-squares has closed-form solution | PASS |
| S4 | Retardance RMSE ≤ 0.05 rad achievable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# polarization/birefringence_s1_ideal.yaml
principle_ref: sha256:<p013_hash>
omega:
  grid: [512, 512]
  analyzer_angles_deg: [0, 45, 90, 135]
  wavelength_nm: 546
E:
  forward: "y_k = M_analyzer(θ_k) · M_sample · S_in + n"
I:
  dataset: Birefringence_8
  images: 8
  noise: {type: gaussian, sigma: 0.02}
  scenario: ideal
O: [retardance_RMSE_rad, orientation_error_deg]
epsilon:
  retardance_RMSE_max: 0.05
  orient_error_max: 3.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 4 analyzer angles at 45° intervals: complete Stokes measurement | PASS |
| S2 | κ ≈ 10, SNR ~ 50: well-conditioned inversion | PASS |
| S3 | Direct pseudo-inverse converges in 1 step | PASS |
| S4 | Retardance RMSE ≤ 0.05 rad at σ=0.02 | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# polarization/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec013_hash>
dataset:
  name: Birefringence_8
  images: 8
  size: [512, 512, 4]
baselines:
  - solver: LSQ-Stokes
    params: {method: pseudoinverse}
    results: {retardance_RMSE: 0.042, orient_error: 2.3}
  - solver: ML-Stokes
    params: {method: MLE}
    results: {retardance_RMSE: 0.035, orient_error: 1.9}
  - solver: PolNet
    params: {arch: UNet}
    results: {retardance_RMSE: 0.018, orient_error: 1.1}
quality_scoring:
  metric: retardance_RMSE_rad
  thresholds:
    - {max: 0.015, Q: 1.00}
    - {max: 0.025, Q: 0.90}
    - {max: 0.050, Q: 0.80}
    - {max: 0.080, Q: 0.75}
```

**Baseline:** LSQ-Stokes — RMSE 0.042 rad | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | Retardance RMSE | Orient err | Runtime | Q |
|--------|----------------|------------|---------|---|
| LSQ-Stokes | 0.042 rad | 2.3° | 0.01 s | 0.80 |
| ML-Stokes | 0.035 rad | 1.9° | 0.1 s | 0.86 |
| PolNet | 0.018 rad | 1.1° | 0.2 s | 0.95 |
| TV-Reg-Stokes | 0.028 rad | 1.5° | 0.5 s | 0.90 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q
Best (PolNet):  300 × 0.95 = 285 PWM
Floor:          300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p013_hash>",
  "r": {"residual_norm": 0.018, "error_bound": 0.05, "ratio": 0.36},
  "c": {"fitted_rate": 1.98, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.90,
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
| L4 Solution | — | 225–285 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep polarization
pwm-node verify polarization/birefringence_s1_ideal.yaml
pwm-node mine polarization/birefringence_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
