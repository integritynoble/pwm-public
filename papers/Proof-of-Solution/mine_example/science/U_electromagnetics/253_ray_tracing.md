# EM Ray Tracing — Four-Layer Walkthrough

**Principle #253 · Electromagnetic Ray Tracing (Propagation)**
Domain: Electromagnetics & Optics | Carrier: EM-field | Difficulty: standard (δ=3) | DAG: [∂.space] --> [N.pointwise.snell] --> [B.surface] --> [∫.spatial]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ GO+GTD/UTD,      │→│ Indoor/outdoor   │→│ Full-wave ref,   │→│ SBR / image /    │
│ reflection/dif-  │ │ propagation env, │ │ measured path    │ │ ray-launching     │
│ fraction, path   │ │ S1-S4 scenarios  │ │ loss baselines   │ │ solver           │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

Ray amplitude: E(s) = E(0)√(ρ₁ρ₂/((ρ₁+s)(ρ₂+s))) · exp(−jks)
Reflection: E_r = R·E_i (Fresnel), Diffraction: E_d = D·E_i (UTD coefficients)
Path loss: PL = 20log₁₀(4πd/λ) + Σ reflections + Σ diffractions

### DAG

```
[∂.space] --> [N.pointwise.snell] --> [B.surface] --> [∫.spatial]
ray-march  Snell/Fresnel  surface-intersect  power-integral
```
V={∂.space,N.pointwise.snell,B.surface,∫.spatial}  L_DAG=3.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Rays always exist for smooth geometry |
| Uniqueness | YES | For given ray path, unique field |
| Stability | CONDITIONAL | Caustics, shadow boundaries need UTD |

Mismatch: geometry simplification, material properties, diffraction order

### Error Method

e = path loss error (dB), delay spread error; q = 1.0 (asymptotic)

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #253"
omega:
  environment: indoor_office
  dimensions_m: [20, 15, 3]
  freq_GHz: 28.0
  materials: {walls: concrete, floor: tile, ceiling: plaster}
E:
  forward: "GO+UTD ray tracing with reflections and diffractions"
  max_reflections: 3
  max_diffractions: 1
I:
  scenario: S1_ideal
O: [path_loss_error_dB, delay_spread_error_ns, angular_spread_error_deg]
epsilon:
  path_loss_error_max_dB: 3.0
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact geometry + materials | None | PL err ≤ 3 dB |
| S2 Mismatch | Simplified geometry | Missing furniture | PL err ≤ 8 dB |
| S3 Oracle | Full geometry given | Known objects | PL err ≤ 4 dB |
| S4 Blind Cal | Estimate materials from data | Self-cal | recovery ≥ 80% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: em_ray_tracing
  cases: 8  # indoor, outdoor, urban canyon, tunnel
  ref: full_wave_FDTD, measurements
baselines:
  - solver: SBR_3bounce
    PL_err_dB: 2.5
  - solver: image_method
    PL_err_dB: 3.0
quality_scoring:
  metric: path_loss_error_dB
  thresholds:
    - {max: 1.0, Q: 1.00}
    - {max: 2.0, Q: 0.90}
    - {max: 3.0, Q: 0.80}
    - {max: 6.0, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | PL err | Time | Q | Reward |
|--------|--------|------|---|--------|
| SBR_3bounce | 2.5 dB | 30s | 0.80 | 240 PWM |
| image_method | 3.0 dB | 10s | 0.80 | 240 PWM |
| ray_launching_GPU | 1.5 dB | 15s | 0.90 | 270 PWM |

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q PWM
```

### Certificate

```json
{
  "principle": 253,
  "r": {"residual_norm": 1.5, "error_bound": 3.0, "ratio": 0.50},
  "c": {"resolutions": [1000,5000,20000], "fitted_rate": 1.0, "theoretical_rate": 1.0},
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
pwm-node benchmarks | grep ray_tracing
pwm-node mine ray_tracing/indoor_s1_ideal.yaml
```
