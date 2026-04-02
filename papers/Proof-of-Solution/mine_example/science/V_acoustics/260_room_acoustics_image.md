# Room Acoustics Image Source — Four-Layer Walkthrough

**Principle #260 · Room Acoustics — Image Source Method**
Domain: Acoustics & Vibration | Carrier: pressure wave | Difficulty: standard (δ=3) | DAG: G.point → K.green → ∫.path

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Mirror images,   │→│ Shoebox room,    │→│ Analytical early │→│ Image source /   │
│ specular reflec- │ │ early reflections│ │ reflections, RIR │ │ hybrid solver    │
│ tions, RIR       │ │ S1-S4 scenarios  │ │ baselines        │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

p(r,t) = Σᵢ (Aᵢ/rᵢ) δ(t − rᵢ/c), image sources at reflected positions
For shoebox: image at r_img = (±x_s + 2nL_x, ±y_s + 2mL_y, ±z_s + 2ℓL_z)
Amplitude: Aᵢ = ∏ (1−α_wall)^{n_reflections}

### DAG

```
[G.point] --> [K.green] --> [∫.path]
```
V={G.point, K.green, ∫.path}  A={G.point→K.green, K.green→∫.path}  L_DAG=2.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Finite image sources up to any reflection order |
| Uniqueness | YES | Deterministic for given geometry |
| Stability | YES | Converges as image order increases |

Mismatch: wall absorption error, non-planar walls, diffraction neglected

### Error Method

e = RIR correlation, EDT error, early reflection level error (dB)
q = exponential convergence with reflection order

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #260"
omega:
  room: shoebox
  dims_m: [8, 6, 3]
  reflection_order: 20
  absorption: {walls: 0.04, floor: 0.06, ceiling: 0.05}
E:
  forward: "p = sum(A_i/r_i * delta(t - r_i/c)) over image sources"
I:
  scenario: S1_ideal
O: [RIR_correlation, EDT_error_pct, early_level_error_dB]
epsilon:
  RIR_correlation_min: 0.95
  EDT_error_max_pct: 5.0
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact shoebox | None | RIR corr ≥ 0.95 |
| S2 Mismatch | α ± 0.03 | Δα | RIR corr ≥ 0.80 |
| S3 Oracle | True α given | Known Δα | RIR corr ≥ 0.90 |
| S4 Blind Cal | Estimate α from RIR | Self-cal | recovery ≥ 85% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: room_image_source
  cases: 6  # various shoebox rooms
  ref: analytical_image_source_exact
baselines:
  - solver: ISM_order20
    RIR_corr: 0.98
  - solver: hybrid_ISM_ray
    RIR_corr: 0.96
quality_scoring:
  metric: RIR_correlation
  thresholds:
    - {min: 0.99, Q: 1.00}
    - {min: 0.97, Q: 0.90}
    - {min: 0.95, Q: 0.80}
    - {min: 0.85, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | RIR corr | Time | Q | Reward |
|--------|---------|------|---|--------|
| ISM_order20 | 0.98 | 2s | 0.90 | 270 PWM |
| hybrid_ISM_ray | 0.96 | 5s | 0.80 | 240 PWM |
| ISM_order50 | 0.995 | 30s | 1.00 | 300 PWM |

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q PWM
```

### Certificate

```json
{
  "principle": 260,
  "r": {"residual_norm": 0.005, "error_bound": 0.05, "ratio": 0.10},
  "c": {"resolutions": [5,10,20], "fitted_rate": "exponential"},
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
| L4 Solution | — | 240–300 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep room_image
pwm-node mine room_acoustics/shoebox_ism_s1_ideal.yaml
```
