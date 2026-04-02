# Principle #368 — Strong Gravitational Lensing: Four-Layer Walkthrough

**Principle #368: Strong Gravitational Lensing**
Domain: Astrophysics & Cosmology | Carrier: electromagnetic | Difficulty: standard (delta=3) | Reward: 3x base

---

## Four-Layer Pipeline

```
LAYER 1              LAYER 2              LAYER 3              LAYER 4
seeds -> Useful(B)   Principle + S1-S4    spec.md + Principle   spec.md + Benchmark
designs the          designs              + S1-S4 designs &     + Principle + S1-S4
PRINCIPLE            spec.md (PoInf)      verifies BENCHMARK    verifies SOLUTION

[Seed] --> [Principle] --> [spec.md] --> [Benchmark] --> [Solution]
  L1          L1              L2             L3             L4
```

---

## Layer 1: Seeds -> Principle

### Governing Equation

```
β = θ - α(θ)           (lens equation)
α(θ) = (4G/c²) ∫ Σ(θ') (θ-θ')/|θ-θ'|² d²θ'   (deflection angle)
Σ(θ) = ∫ ρ(r) dz       (projected surface mass density)
κ = Σ / Σ_cr            (convergence)
```

### DAG Decomposition G = (V, A)

```
[K.green] -> [N.pointwise] -> [O.l2]

V = {K.green, N.pointwise, O.l2}
A = {K.green->N.pointwise, N.pointwise->O.l2}
L_DAG = 2.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- deflection field exists for any bounded mass distribution |
| Uniqueness | CONDITIONAL -- multiple images arise; reconstruction unique with sufficient constraints |
| Stability | CONDITIONAL -- magnification diverges near caustics; regularization needed |

Mismatch parameters: lens model (SIE vs NFW), ellipticity, external shear, source position

### Error-Bounding Method

```
e  = image position residual [arcsec] (primary), mass profile error (secondary)
q = 1.0 (gradient descent convergence for smooth models)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Angular units [arcsec] consistent; deflection angle dimensionally correct | PASS |
| S2 | Lens equation invertible with regularization away from caustics | PASS |
| S3 | Parametric lens models (SIE, NFW) converge via gradient optimization | PASS |
| S4 | Image position residual < 0.01 arcsec achievable for clean systems | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_368_hash>

omega:
  description: "SIE lens model, quad image system, 5x5 arcsec field"
  grid: [256, 256]
  pixel_arcsec: 0.02
  outputs: [mass_map, image_positions, magnifications]

E:
  forward: "β = θ - α(θ); α from Σ(θ)"
  dag: "[K.green] -> [N.pointwise] -> [O.l2]"

B:
  constraints: "mass > 0; deflection smooth; time delays consistent"

I:
  scenario: ideal
  lens_model: SIE
  parameters: {Einstein_radius: 1.5, ellipticity: 0.3, shear: 0.05}
  mismatch: null

O: [position_residual_arcsec, mass_error]

epsilon:
  pos_err_max: 0.01
  convergence_order: 1.0

difficulty:
  L_DAG: 2.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known SIE model | None | pos_err < 0.01 arcsec |
| S2 Mismatch | Wrong ellipticity or shear | Applied | relaxed 1.5x |
| S3 Oracle | True mass profile known | Known | pos_err < 0.01 arcsec |
| S4 Blind Cal | Infer lens model from images | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_368_hash>
principle_ref: sha256:<principle_368_hash>

dataset:
  description: "Simulated strong lens systems with multiple image configurations"
  n_systems: 50
  data_hash: sha256:<dataset_368_hash>

baselines:
  - solver: Lenstronomy-SIE     position_residual: 0.005    q: 0.95
  - solver: GLEE                position_residual: 0.008    q: 0.90
  - solver: PixeLens            position_residual: 0.015    q: 0.80

quality_scoring:
  metric: position_residual_arcsec
  thresholds:
    - {max: 0.003, Q: 1.00}
    - {max: 0.006, Q: 0.90}
    - {max: 0.010, Q: 0.80}
    - {max: 0.015, Q: 0.75}
```

### Baselines

| Solver | position_residual | Q | Approx Reward |
|--------|------------------|---|---------------|
| Lenstronomy-SIE | 0.005 | 0.95 | ~285 PWM |
| GLEE | 0.008 | 0.90 | ~270 PWM |
| PixeLens | 0.015 | 0.80 | ~240 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Image configurations match spec; pixel scale consistent | PASS |
| S2 | Problem well-posed: SIE has analytic deflection angles | PASS |
| S3 | Lenstronomy converges; residual decreases with optimization | PASS |
| S4 | Baseline meets threshold (pos_err < 0.01); feasibility confirmed | PASS |

### Layer 3 Reward

```
Benchmark seed reward = 100 x phi(t) x 0.60 = 60 PWM (builder)
Upstream: 15% -> L2 designer, 10% -> L1 creator, 15% -> treasury
```

---

## Layer 4: Benchmark -> Solution (PoSol Mining)

### Solver Table

| Solver | Expected Error | Time | Q | Reward |
|--------|---------------|------|---|--------|
| Lenstronomy-SIE | 0.005 | ~1 min | 0.95 | ~285 PWM |
| GLEE | 0.008 | ~2 min | 0.90 | ~270 PWM |
| PixeLens | 0.015 | ~5 min | 0.80 | ~240 PWM |

### Reward Calculation

```
R = R_base x phi(t) x delta x nu_c x q
  = 100 x 1.0 x 3 x 1.0 x q
  = 300 x q  PWM

Best case:  300 x 0.95 = 285 PWM
Worst case: 300 x 0.75 = 225 PWM
```

### S4 Certificate

```json
{
  "principle": "#368 Strong Gravitational Lensing",
  "h_p": "sha256:<principle_368_hash>",
  "h_s": "sha256:<spec_368_hash>",
  "h_b": "sha256:<bench_368_hash>",
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"},
  "Q": 0.95,
  "difficulty": {"tier":"standard","delta":3}
}
```

---

## Reward Summary

```
L1 Principle:  200 PWM seed + upstream royalties from L2/L3/L4
L2 spec.md:    105 PWM seed (x4 scenarios = 420 PWM) + upstream from L3/L4
L3 Benchmark:   60 PWM seed (x4 benchmarks = 240 PWM) + upstream from L4
L4 Solution:   225-285 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep strong_lensing
pwm-node verify AC_astrophysics/strong_lensing_s1_ideal.yaml
pwm-node mine AC_astrophysics/strong_lensing_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
