# Principle #380 — Exoplanet Transit Light Curve: Four-Layer Walkthrough

**Principle #380: Exoplanet Transit Light Curve**
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
F(t)/F₀ = 1 - δ(p(t))                        (transit flux)
δ = (R_p/R_s)²  (transit depth, uniform disk)
p(t) = |r(t)|/R_s  (projected separation in stellar radii)
r(t) from Keplerian orbit: a, e, i, ω, T₀, P
I(μ) = 1 - Σ u_k(1-μ^{k/2})               (limb darkening)
```

### DAG Decomposition G = (V, A)

```
[K.green] -> [∫.path] -> [O.l2]

V = {K.green, ∫.path, O.l2}
A = {K.green->∫.path, ∫.path->O.l2}
L_DAG = 2.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- Keplerian orbit + occultation geometry yields unique light curve |
| Uniqueness | YES -- (R_p/R_s, a/R_s, i, u) uniquely determine transit shape |
| Stability | YES -- smooth dependence on orbital and limb-darkening parameters |

Mismatch parameters: limb-darkening coefficients, eccentricity, stellar variability, TTVs

### Error-Bounding Method

```
e  = R_p/R_s relative error (primary), flux residual RMS (secondary)
q = 0.5 (sqrt(N) photometric improvement)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Flux [normalized], time [days], radii [stellar radii] consistent | PASS |
| S2 | Transit model analytic (Mandel & Agol); bounded for physical params | PASS |
| S3 | MCMC/Levenberg-Marquardt converges for well-sampled transits | PASS |
| S4 | R_p/R_s recoverable to 1% for SNR > 100 per cadence | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_380_hash>

omega:
  description: "Hot Jupiter transit, Kepler-like cadence, 30 transits stacked"
  cadence_min: 1.0
  n_transits: 30
  outputs: [Rp_Rs, a_Rs, inclination, limb_dark_coeffs]

E:
  forward: "F(t)/F₀ = 1 - δ(p(t)); Mandel-Agol model"
  dag: "[K.green] -> [∫.path] -> [O.l2]"

B:
  constraints: "0 < R_p/R_s < 0.3; 0 < i < 90°; u₁+u₂ < 1"

I:
  scenario: ideal
  parameters: {Rp_Rs: 0.1, a_Rs: 8.0, inc_deg: 87, P_days: 3.5}
  mismatch: null

O: [Rp_Rs_error, flux_residual_rms]

epsilon:
  Rp_Rs_err_max: 0.01
  convergence_order: 0.5

difficulty:
  L_DAG: 3.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known orbit + clean photometry | None | Rp_Rs_err < 1% |
| S2 Mismatch | Wrong limb darkening or stellar variability | Applied | relaxed 1.5x |
| S3 Oracle | True parameters known | Known | Rp_Rs_err < 1% |
| S4 Blind Cal | Fit all transit parameters | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_380_hash>
principle_ref: sha256:<principle_380_hash>

dataset:
  description: "Simulated transit light curves for planets of varying sizes"
  n_planets: 50
  data_hash: sha256:<dataset_380_hash>

baselines:
  - solver: batman+emcee       Rp_Rs_error: 0.003    q: 0.95
  - solver: JKTEBOP            Rp_Rs_error: 0.005    q: 0.90
  - solver: Box-fit            Rp_Rs_error: 0.015    q: 0.78

quality_scoring:
  metric: Rp_Rs_error
  thresholds:
    - {max: 0.002, Q: 1.00}
    - {max: 0.005, Q: 0.90}
    - {max: 0.010, Q: 0.80}
    - {max: 0.015, Q: 0.75}
```

### Baselines

| Solver | Rp_Rs_error | Q | Approx Reward |
|--------|------------|---|---------------|
| batman+emcee | 0.003 | 0.95 | ~285 PWM |
| JKTEBOP | 0.005 | 0.90 | ~270 PWM |
| Box-fit | 0.015 | 0.78 | ~234 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Planet sizes and cadences match spec | PASS |
| S2 | Problem well-posed: simulated transits have known ground truth | PASS |
| S3 | batman+emcee converges; posteriors well-sampled | PASS |
| S4 | Baseline meets threshold (Rp_Rs_err < 1%); feasibility confirmed | PASS |

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
| batman+emcee | 0.003 | ~5 min | 0.95 | ~285 PWM |
| JKTEBOP | 0.005 | ~2 min | 0.90 | ~270 PWM |
| Box-fit | 0.015 | ~5 s | 0.78 | ~234 PWM |

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
  "principle": "#380 Exoplanet Transit Light Curve",
  "h_p": "sha256:<principle_380_hash>",
  "h_s": "sha256:<spec_380_hash>",
  "h_b": "sha256:<bench_380_hash>",
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
pwm-node benchmarks | grep exoplanet_transit
pwm-node verify AC_astrophysics/exoplanet_transit_s1_ideal.yaml
pwm-node mine AC_astrophysics/exoplanet_transit_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
