# Principle #105 — Weather Radar

**Domain:** Remote Sensing | **Carrier:** Microwave | **Difficulty:** Standard (δ=3)
**DAG:** G.pulse --> K.green --> F.dft --> integral.temporal | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │        G.pulse-->K.green-->F.dft-->integral.temporal    WxRadar    NEXRAD-Precip       QPE
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  WEATHER RADAR   P = (E, G, W, C)   Principle #105             │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Z_e(r,θ,φ) = C·∫ σ_back(D)·N(D) dD                   │
│        │ Z_e = reflectivity factor (dBZ); N(D) = drop-size dist│
│        │ Z-R relation: Z = a·R^b for precipitation rate R      │
│        │ Inverse: recover rainfall rate R from reflectivity Z   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse] --> [K.green] --> [F.dft] --> [integral.temporal]│
│        │ MicrowavePulse  Propagate  DopplerFFT  Accumulate       │
│        │ V={G.pulse, K.green, F.dft, integral.temporal}  A={G.pulse-->K.green, K.green-->F.dft, F.dft-->integral.temporal}   L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Z-R is empirically calibrated)         │
│        │ Uniqueness: CONDITIONAL (Z-R coefficients vary)        │
│        │ Stability: κ ≈ 12 (stratiform), κ ≈ 50 (convective)   │
│        │ Mismatch: beam broadening, attenuation, clutter         │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = rainfall RMSE (primary), bias (secondary)          │
│        │ q = 2.0 (variational QPE convergence)                 │
│        │ T = {RMSE_mm_hr, bias, K_resolutions}                  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Range bins and elevation angles consistent with scan strategy | PASS |
| S2 | Z-R relation bounded for given precipitation type | PASS |
| S3 | Variational QPE converges with gauge calibration | PASS |
| S4 | RMSE < 3 mm/hr achievable for stratiform rain | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# weather_radar/nexrad_s1_ideal.yaml
principle_ref: sha256:<p105_hash>
omega:
  grid_polar: [920, 360]
  range_km: 230
  elevation_scans: 14
E:
  forward: "Z = a·R^b + clutter + attenuation"
  ZR_relation: {a: 300, b: 1.4}
I:
  dataset: NEXRAD_Precip
  events: 50
  noise: {type: gaussian, SNR_dB: 20}
  scenario: ideal
O: [RMSE_mm_hr, correlation, bias]
epsilon:
  RMSE_max_mm_hr: 3.0
  correlation_min: 0.85
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 920 range gates at 250 m spacing; 14 elevations | PASS |
| S2 | Z-R bounded for Marshall-Palmer DSD; κ ≈ 12 | PASS |
| S3 | QPE algorithm converges with gauge calibration data | PASS |
| S4 | RMSE < 3 mm/hr feasible for stated parameters | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# weather_radar/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec105_hash>
principle_ref: sha256:<p105_hash>
dataset:
  name: NEXRAD_Precip
  events: 50
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Standard-ZR
    results: {RMSE_mm_hr: 2.8, correlation: 0.87}
  - solver: Dual-Pol-QPE
    results: {RMSE_mm_hr: 1.8, correlation: 0.93}
  - solver: RadarNet
    results: {RMSE_mm_hr: 1.2, correlation: 0.96}
quality_scoring:
  - {max_RMSE: 1.0, Q: 1.00}
  - {max_RMSE: 1.8, Q: 0.90}
  - {max_RMSE: 2.8, Q: 0.80}
  - {max_RMSE: 4.0, Q: 0.75}
```

**Baseline:** Standard-ZR — RMSE 2.8 mm/hr | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | RMSE (mm/hr) | Corr | Q |
|--------|--------------|------|---|
| Standard-ZR | 2.8 | 0.87 | 0.80 |
| Dual-Pol-QPE | 1.8 | 0.93 | 0.90 |
| RadarNet | 1.2 | 0.96 | 0.95 |
| PrecipFormer | 0.9 | 0.97 | 1.00 |

### Reward: `R = 100 × 3 × q` → Best: 300 PWM | Floor: 225 PWM

```json
{
  "h_p": "sha256:<p105_hash>", "Q": 0.95,
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
pwm-node benchmarks | grep weather_radar
pwm-node mine weather_radar/nexrad_s1_ideal.yaml
```
