# Microwave Imaging — Four-Layer Walkthrough

**Principle #255 · Microwave Tomographic Imaging**
Domain: Electromagnetics & Optics | Carrier: EM-field/microwave | Difficulty: hard (δ=5) | DAG: [K.green.em] --> [L.sparse] --> [O.iterative] --> [B.surface]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Inverse scatter- │→│ Breast / subsur- │→│ Simulated dielec-│→│ Born / DBIM /    │
│ ing, Born approx,│ │ face target,     │ │ tric phantoms,   │ │ CSI / full-wave  │
│ nonlinear inver- │ │ S1-S4 scenarios  │ │ known ε(r)       │ │ inversion solver │
│ sion (DBIM, CSI) │ │                  │ │ baselines        │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

∇²E + k₀²ε_r(r)E = 0 (Helmholtz in inhomogeneous medium)
Data: E_s(r_rx) = ∫ G(r_rx,r')·χ(r')·E(r') dV' (scattering integral)
Contrast: χ(r) = ε_r(r) − ε_bg

### DAG

```
[K.green.em] --> [L.sparse] --> [O.iterative] --> [B.surface]
Green-kernel  forward-model  iterative-inversion  boundary-data
```
V={K.green.em,L.sparse,O.iterative,B.surface}  L_DAG=5.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Scattering data always produced |
| Uniqueness | CONDITIONAL | Requires sufficient view angles and frequencies |
| Stability | CONDITIONAL | Ill-posed nonlinear inverse; regularization needed |

Mismatch: background medium error, antenna coupling, multipath

### Error Method

e = relative ε_r error, contrast RMSE; q = 1.0 (Born), 2.0 (DBIM)

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #255"
omega:
  geometry: circular_array_2D
  n_antennas: 16
  freq_GHz: [2.0, 4.0, 6.0]
  domain_cm: [15, 15]
E:
  forward: "Helmholtz + scattering integral, contrast chi"
  method: DBIM
I:
  scenario: S1_ideal
  background: {eps_r: 9.0}  # tissue-mimicking
O: [contrast_RMSE, eps_error_pct, SSIM]
epsilon:
  contrast_RMSE_max: 0.15
  SSIM_min: 0.75
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known background | None | RMSE ≤ 0.15 |
| S2 Mismatch | Background ε ± 10% | Δε_bg | RMSE ≤ 0.30 |
| S3 Oracle | True background given | Known ε_bg | RMSE ≤ 0.18 |
| S4 Blind Cal | Estimate ε_bg from data | Self-cal | recovery ≥ 75% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: microwave_imaging
  cases: 8  # cylinders, breast phantom, layered
  ref: simulated_FDTD_scattered_fields
baselines:
  - solver: Born_linear
    contrast_RMSE: 0.25
  - solver: DBIM_5iter
    contrast_RMSE: 0.12
  - solver: CSI
    contrast_RMSE: 0.10
quality_scoring:
  metric: contrast_RMSE
  thresholds:
    - {max: 0.05, Q: 1.00}
    - {max: 0.10, Q: 0.90}
    - {max: 0.15, Q: 0.80}
    - {max: 0.30, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | RMSE | Time | Q | Reward |
|--------|------|------|---|--------|
| Born_linear | 0.25 | 5s | 0.75 | 375 PWM |
| DBIM_5iter | 0.12 | 120s | 0.80 | 400 PWM |
| CSI | 0.10 | 300s | 0.90 | 450 PWM |

```
R = 100 × 1.0 × 5 × 1.0 × Q = 500 × Q PWM
```

### Certificate

```json
{
  "principle": 255,
  "r": {"residual_norm": 0.10, "error_bound": 0.15, "ratio": 0.67},
  "c": {"resolutions": [32,64,128], "fitted_rate": 1.5, "theoretical_rate": 2.0},
  "Q": 0.90,
  "gates": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"}
}
```

---

## Reward Summary

| Layer | One-time | Ongoing |
|-------|----------|---------|
| L1 Principle | 200 PWM | 5% of L4 mints |
| L2 spec | 150 PWM × 4 | 10% of L4 mints |
| L3 Benchmark | 100 PWM × 4 | 15% of L4 mints |
| L4 Solution | — | 375–500 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep microwave_imaging
pwm-node mine microwave_imaging/breast_s1_ideal.yaml
```
