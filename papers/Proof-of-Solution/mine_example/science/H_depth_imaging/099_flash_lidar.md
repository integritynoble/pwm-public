# Principle #99 — Flash LiDAR (Single-Photon Avalanche Diode Array)

**Domain:** Depth Imaging | **Carrier:** Photon (NIR) | **Difficulty:** Hard (δ=5)
**DAG:** G.pulse.laser --> K.green --> integral.temporal | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │        G.pulse.laser-->K.green-->integral.temporal    FlashLiDAR SPAD-Outdoor        Photon-est
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  FLASH LIDAR   P = (E, G, W, C)   Principle #99                │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r,t) ~ Poisson(s(r)·h(t−2d(r)/c) + b(r))           │
│        │ SPAD array: each pixel timestamps single photons       │
│        │ Extreme low-flux: 0.1–5 signal photons per pixel       │
│        │ Inverse: depth d(r) from photon-starved histograms     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse.laser] --> [K.green] --> [integral.temporal]    │
│        │ LaserPulse  Propagate  PhotonAccum                      │
│        │ V={G.pulse.laser, K.green, integral.temporal}  A={G.pulse.laser-->K.green, K.green-->integral.temporal}   L_DAG=4.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (photon timestamps encode depth)        │
│        │ Uniqueness: YES with sufficient photon count (>1)       │
│        │ Stability: κ ≈ 10 (>5 photons), κ ≈ 200 (<1 photon)   │
│        │ Mismatch: background photons, pile-up, detector jitter  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = depth MAE (primary), detection rate (secondary)    │
│        │ q = 1.5 (ML estimation convergence)                   │
│        │ T = {depth_MAE, detection_rate, K_resolutions}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | SPAD time-bin resolution consistent with depth precision target | PASS |
| S2 | ML depth estimation regularizable even at <1 signal photon | PASS |
| S3 | EM / matched-filter estimation converges for Poisson model | PASS |
| S4 | Depth MAE < 10 cm achievable at SBR > 1 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# flash_lidar/outdoor_s1_ideal.yaml
principle_ref: sha256:<p099_hash>
omega:
  grid: [256, 256]
  time_bins: 1024
  bin_width_ps: 50
  max_range_m: 50
E:
  forward: "y ~ Poisson(s·h(t−2d/c) + b)"
  signal_photons_mean: 2.0
  background_photons_mean: 5.0
I:
  dataset: SPAD_Outdoor
  scenes: 30
  noise: {type: poisson, SBR: 0.4}
  scenario: ideal
O: [depth_MAE_cm, detection_rate_pct]
epsilon:
  depth_MAE_max_cm: 10.0
  detection_rate_min_pct: 90.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1024 bins at 50 ps → 7.5 m range per cycle; 50 m with coding | PASS |
| S2 | SBR=0.4 → challenging but regularizable with spatial priors | PASS |
| S3 | Matched-filter + spatial smoothing converges | PASS |
| S4 | MAE < 10 cm and detection > 90% feasible at SBR=0.4 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# flash_lidar/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec099_hash>
principle_ref: sha256:<p099_hash>
dataset:
  name: SPAD_Outdoor
  scenes: 30
  size: [256, 256, 1024]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Matched-Filter
    params: {template: gaussian}
    results: {depth_MAE_cm: 8.5, detection_pct: 91.2}
  - solver: Cross-Correlation
    params: {regularize: TV}
    results: {depth_MAE_cm: 5.2, detection_pct: 94.5}
  - solver: SPADNet
    params: {pretrained: true}
    results: {depth_MAE_cm: 2.1, detection_pct: 98.3}
quality_scoring:
  - {max_MAE_cm: 2.0, Q: 1.00}
  - {max_MAE_cm: 5.0, Q: 0.90}
  - {max_MAE_cm: 8.0, Q: 0.80}
  - {max_MAE_cm: 12.0, Q: 0.75}
```

**Baseline solver:** Matched-Filter — MAE 8.5 cm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | MAE (cm) | Detection (%) | Runtime | Q |
|--------|----------|---------------|---------|---|
| Matched-Filter | 8.5 | 91.2 | 0.1 s | 0.80 |
| Cross-Correlation | 5.2 | 94.5 | 0.5 s | 0.90 |
| SPADNet | 2.1 | 98.3 | 0.3 s | 0.97 |
| PhotonFormer | 1.8 | 98.8 | 0.5 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (PhotonFormer): 500 × 1.00 = 500 PWM
Floor:                    500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p099_hash>",
  "h_s": "sha256:<spec099_hash>",
  "h_b": "sha256:<bench099_hash>",
  "r": {"depth_MAE_cm": 2.1, "detection_pct": 98.3},
  "c": {"fitted_rate": 1.45, "theoretical_rate": 1.5, "K": 3},
  "Q": 0.97,
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
pwm-node benchmarks | grep flash_lidar
pwm-node verify flash_lidar/outdoor_s1_ideal.yaml
pwm-node mine flash_lidar/outdoor_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
