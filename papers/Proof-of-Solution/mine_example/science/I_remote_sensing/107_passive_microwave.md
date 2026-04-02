# Principle #107 — Passive Microwave Radiometry

**Domain:** Remote Sensing | **Carrier:** Microwave (thermal) | **Difficulty:** Standard (δ=3)
**DAG:** B.planck --> integral.spectral --> S.angular | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          B.planck-->integral.spectral-->S.angular    PassMW     AMSR2-SST           Retrieval
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PASSIVE MICROWAVE   P = (E, G, W, C)   Principle #107         │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ T_B(f,θ) = ε(f,θ)·T_s + (1−ε)·T_sky + T_atm         │
│        │ T_B = brightness temperature; ε = surface emissivity  │
│        │ Multi-frequency: each f probes different surface param │
│        │ Inverse: retrieve SST, soil moisture, wind speed       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [B.planck] --> [integral.spectral] --> [S.angular]       │
│        │  ThermalEmit  RadioInteg  ScanPattern                   │
│        │ V={B.planck, integral.spectral, S.angular}  A={B.planck-->integral.spectral, integral.spectral-->S.angular}   L_DAG=2.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (radiative transfer well-defined)       │
│        │ Uniqueness: YES with multi-frequency observations       │
│        │ Stability: κ ≈ 10 (ocean SST), κ ≈ 40 (land)          │
│        │ Mismatch: atmospheric profile, surface roughness        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = SST RMSE (primary), bias (secondary)               │
│        │ q = 2.0 (regression/optimal estimation convergence)   │
│        │ T = {RMSE_K, bias_K, K_resolutions}                    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Multi-frequency channels cover SST-sensitive bands | PASS |
| S2 | Radiative transfer invertible with multi-freq; κ ≈ 10 | PASS |
| S3 | Optimal estimation converges for multi-channel retrieval | PASS |
| S4 | SST RMSE < 0.5 K achievable with calibrated data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# passive_mw/amsr2_s1_ideal.yaml
principle_ref: sha256:<p107_hash>
omega:
  grid: [720, 1440]
  frequencies_GHz: [6.9, 10.65, 18.7, 23.8, 36.5, 89.0]
  polarizations: [H, V]
E:
  forward: "T_B = ε·T_s + (1−ε)·T_sky + T_atm"
I:
  dataset: AMSR2_SST
  orbits: 100
  noise: {type: gaussian, NEDT_K: 0.3}
  scenario: ideal
O: [SST_RMSE_K, bias_K]
epsilon:
  SST_RMSE_max_K: 0.5
  bias_max_K: 0.1
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 6 frequencies × 2 polarizations = 12 channels | PASS |
| S2 | Multi-channel retrieval well-posed; κ ≈ 10 | PASS |
| S3 | Optimal estimation converges for 12 channels | PASS |
| S4 | RMSE < 0.5 K feasible at NEDT=0.3 K | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# passive_mw/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec107_hash>
principle_ref: sha256:<p107_hash>
dataset:
  name: AMSR2_SST
  orbits: 100
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Linear-Regression
    results: {SST_RMSE_K: 0.45, bias_K: 0.08}
  - solver: Optimal-Estimation
    results: {SST_RMSE_K: 0.35, bias_K: 0.05}
  - solver: MWNet
    results: {SST_RMSE_K: 0.22, bias_K: 0.03}
quality_scoring:
  - {max_RMSE: 0.20, Q: 1.00}
  - {max_RMSE: 0.35, Q: 0.90}
  - {max_RMSE: 0.50, Q: 0.80}
  - {max_RMSE: 0.70, Q: 0.75}
```

**Baseline:** Linear-Regression — RMSE 0.45 K | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | RMSE (K) | Bias (K) | Q |
|--------|----------|----------|---|
| Linear-Regression | 0.45 | 0.08 | 0.80 |
| Optimal-Estimation | 0.35 | 0.05 | 0.90 |
| MWNet | 0.22 | 0.03 | 0.97 |
| SST-Former | 0.18 | 0.02 | 1.00 |

### Reward: `R = 100 × 3 × q` → Best: 300 PWM | Floor: 225 PWM

```json
{
  "h_p": "sha256:<p107_hash>", "Q": 0.97,
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
pwm-node benchmarks | grep passive_mw
pwm-node mine passive_mw/amsr2_s1_ideal.yaml
```
