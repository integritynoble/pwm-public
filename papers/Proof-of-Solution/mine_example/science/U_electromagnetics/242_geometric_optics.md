# Geometric Optics Ray Tracing — Four-Layer Walkthrough

**Principle #242 · Geometric Optics / Eikonal Equation**
Domain: Electromagnetics & Optics | Carrier: photon | Difficulty: basic (δ=2) | DAG: [∂.space] --> [N.pointwise.snell] --> [B.surface]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Eikonal eqn,     │→│ Lens system or   │→│ Analytical Seidel│→│ Ray-trace engine │
│ Snell's law,     │ │ GRIN medium,     │ │ aberrations,     │ │ / eikonal solver │
│ Fermat principle  │ │ S1-S4 scenarios │ │ baselines        │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

|∇S|² = n²(r)  (Eikonal equation)
Ray equation: d/ds[n(r) dr/ds] = ∇n
Snell's law: n₁ sin θ₁ = n₂ sin θ₂

### DAG

```
[∂.space] --> [N.pointwise.snell] --> [B.surface]
ray-propagation  Snell-refraction  surface-intersection
```

V={∂.space,N.pointwise.snell,B.surface}  L_DAG=1.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | ODE system has solution for smooth n(r) |
| Uniqueness | YES | Rays determined by initial position and direction |
| Stability | YES | Continuous dependence on initial conditions (away from caustics) |

Mismatch: surface curvature error, refractive index error, alignment

### Error Method

e = spot diagram RMS, wavefront error (waves), Seidel coefficients
q = 4.0 (Runge-Kutta ray tracer)

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #242"
omega:
  system: doublet_lens
  surfaces: 4
  wavelength_nm: [486, 588, 656]
E:
  forward: "|grad(S)|^2 = n^2(r), Snell at interfaces"
I:
  scenario: S1_ideal
  rays: 10000
  field_angles_deg: [0, 5, 10, 15]
O: [spot_RMS_um, wavefront_PV_waves, distortion_pct]
epsilon:
  spot_RMS_max_um: 5.0
  wavefront_PV_max: 0.25
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact surfaces | None | spot RMS ≤ 5 μm |
| S2 Mismatch | Radius ± 0.1% | ΔR | spot RMS ≤ 15 μm |
| S3 Oracle | True radii given | Known ΔR | spot RMS ≤ 7 μm |
| S4 Blind Cal | Estimate R from spot | Self-cal | recovery ≥ 85% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: geometric_optics_lenses
  cases: 8  # singlet, doublet, triplet, GRIN
  analytical_ref: Seidel_coefficients, paraxial_image
baselines:
  - solver: sequential_ray_trace
    spot_RMS_um: 3.0
    time_s: 1.0
  - solver: eikonal_FD
    spot_RMS_um: 4.5
    time_s: 5.0
quality_scoring:
  metric: spot_RMS_um
  thresholds:
    - {max: 1.0, Q: 1.00}
    - {max: 3.0, Q: 0.90}
    - {max: 5.0, Q: 0.80}
    - {max: 15.0, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | Spot RMS | Time | Q | Reward |
|--------|---------|------|---|--------|
| sequential_ray_trace | 3.0 μm | 1s | 0.90 | 180 PWM |
| eikonal_FD | 4.5 μm | 5s | 0.80 | 160 PWM |
| differential_ray | 0.8 μm | 2s | 1.00 | 200 PWM |

```
R = 100 × 1.0 × 2 × 1.0 × Q = 200 × Q PWM
```

### Certificate

```json
{
  "principle": 242,
  "r": {"residual_norm": 0.8, "error_bound": 5.0, "ratio": 0.16},
  "c": {"resolutions": [1000,5000,20000], "fitted_rate": 4.0, "theoretical_rate": 4.0},
  "Q": 1.00,
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
| L4 Solution | — | 160–200 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep geometric_optics
pwm-node mine geometric_optics/doublet_s1_ideal.yaml
```
