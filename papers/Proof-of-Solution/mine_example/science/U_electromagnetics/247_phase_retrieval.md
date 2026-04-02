# Phase Retrieval — Four-Layer Walkthrough

**Principle #247 · Phase Retrieval**
Domain: Electromagnetics & Optics | Carrier: photon | Difficulty: hard (δ=5) | DAG: [F.dft] --> [N.pointwise.constraint] --> [O.iterative]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Intensity-only   │→│ CDI / ptychogra- │→│ Simulated inten- │→│ GS / HIO / ePIE /│
│ measurements,    │ │ phy config,      │ │ sity patterns,   │ │ WF gradient      │
│ Fourier amplitude│ │ S1-S4 scenarios  │ │ known objects    │ │ solver           │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

Find x such that |Fx| = b (measured amplitudes)
F = Fourier or Fresnel propagation operator
Non-convex: phase lost in intensity measurement I = |U|²

### DAG

```
[F.dft] --> [N.pointwise.constraint] --> [O.iterative]
Fourier-transform  magnitude-constraint  iterative-projection
```
V={F.dft,N.pointwise.constraint,O.iterative}  L_DAG=3.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Feasible when oversampling ratio > 2 |
| Uniqueness | CONDITIONAL | Up to global phase; needs support constraint or diversity |
| Stability | CONDITIONAL | Non-convex; multiple local minima possible |

Mismatch: detector noise, partial coherence, probe uncertainty

### Error Method

e = relative object error (up to global phase), phase RMSE
q = 1.0 (GS), q = 2.0 (gradient methods)

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #247"
omega:
  object: complex_2D
  grid: [256, 256]
  oversampling: 2.0
E:
  forward: "|F{x}|^2 = b^2, recover x from b"
  diversity: single_shot  # or multi-distance
I:
  scenario: S1_ideal
  noise: {type: poisson, photons: 1e6}
O: [object_error, phase_RMSE_rad, SSIM]
epsilon:
  object_error_max: 0.05
  phase_RMSE_max_rad: 0.2
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known support + oversample | None | obj err ≤ 0.05 |
| S2 Mismatch | Unknown support | Missing constraint | obj err ≤ 0.15 |
| S3 Oracle | True support given | Known boundary | obj err ≤ 0.08 |
| S4 Blind Cal | Estimate support from data | Shrink-wrap | recovery ≥ 80% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: phase_retrieval_2D
  cases: 10
  ref: simulated_coherent_diffraction
baselines:
  - solver: HIO
    obj_err: 0.04
    iterations: 500
  - solver: ER
    obj_err: 0.08
    iterations: 1000
  - solver: WF_gradient
    obj_err: 0.02
    iterations: 200
quality_scoring:
  metric: object_error
  thresholds:
    - {max: 0.01, Q: 1.00}
    - {max: 0.03, Q: 0.90}
    - {max: 0.05, Q: 0.80}
    - {max: 0.15, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | Obj err | Iters | Q | Reward |
|--------|---------|-------|---|--------|
| HIO | 0.04 | 500 | 0.80 | 400 PWM |
| WF_gradient | 0.02 | 200 | 0.90 | 450 PWM |
| ePIE | 0.008 | 300 | 1.00 | 500 PWM |

```
R = 100 × 1.0 × 5 × 1.0 × Q = 500 × Q PWM
```

### Certificate

```json
{
  "principle": 247,
  "r": {"residual_norm": 0.008, "error_bound": 0.05, "ratio": 0.16},
  "c": {"resolutions": [64,128,256], "fitted_rate": 2.0, "theoretical_rate": 2.0},
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
| L4 Solution | — | 400–500 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep phase_retrieval
pwm-node mine phase_retrieval/cdi_s1_ideal.yaml
```
