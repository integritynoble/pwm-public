# Principle #372 — Supernova Light Curve Fitting: Four-Layer Walkthrough

**Principle #372: Supernova Light Curve Fitting**
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
L(t) = M_Ni [ε_Ni e^{-t/τ_Ni} + ε_Co (e^{-t/τ_Co} - e^{-t/τ_Ni})]  (Arnett rule)
T_eff(t) = [L(t)/(4πR(t)²σ)]^{1/4}   (photospheric temperature)
R(t) = R_0 + v_exp t                   (homologous expansion)
m_band(t) = -2.5 log₁₀[L_band(t)] + const  (observed magnitude)
```

### DAG Decomposition G = (V, A)

```
[∂.time] -> [N.reaction] -> [∫.volume]

V = {∂.time, N.reaction, ∫.volume}
A = {∂.time->N.reaction, N.reaction->∫.volume}
L_DAG = 2.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- radioactive decay provides bounded energy source |
| Uniqueness | YES -- given M_Ni, E_kin, M_ej, light curve is unique |
| Stability | YES -- smooth dependence on physical parameters |

Mismatch parameters: nickel mass M_Ni, ejecta mass M_ej, explosion energy E_kin, opacity κ

### Error-Bounding Method

```
e  = magnitude residual |Δm| (primary), parameter recovery error (secondary)
q = 1.0 (chi-squared fitting convergence)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Luminosity [erg/s], time [days], magnitude [mag] units consistent | PASS |
| S2 | Arnett model bounded for physical M_Ni; smooth light curves | PASS |
| S3 | MCMC/Levenberg-Marquardt converges for multi-band fitting | PASS |
| S4 | Magnitude residual < 0.1 mag achievable for well-sampled SNe | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_372_hash>

omega:
  description: "Type II-P supernova, multi-band BVRI, 200-day coverage"
  bands: [B, V, R, I]
  time_range_days: [0, 200]
  outputs: [M_Ni, M_ej, E_kin, fitted_light_curve]

E:
  forward: "L(t) = M_Ni [ε_Ni exp(-t/τ_Ni) + ε_Co (...)]"
  dag: "[∂.time] -> [N.reaction] -> [∫.volume]"

B:
  constraints: "M_Ni > 0; E_kin > 0; M_ej > 0; opacity bounded"

I:
  scenario: ideal
  parameters: {M_Ni: 0.07, M_ej: 12.0, E_kin: 1.2e51}
  mismatch: null

O: [mag_residual, param_error]

epsilon:
  mag_err_max: 0.10
  convergence_order: 1.0

difficulty:
  L_DAG: 3.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known SN model + clean photometry | None | mag_err < 0.1 |
| S2 Mismatch | Wrong opacity or distance | Applied | relaxed 1.5x |
| S3 Oracle | True parameters known | Known | mag_err < 0.1 |
| S4 Blind Cal | Fit SN parameters from light curve | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_372_hash>
principle_ref: sha256:<principle_372_hash>

dataset:
  description: "Simulated and observed SN light curves across types"
  n_supernovae: 30
  data_hash: sha256:<dataset_372_hash>

baselines:
  - solver: SNEC-hydro          mag_residual: 0.05    q: 0.95
  - solver: Arnett-analytic     mag_residual: 0.08    q: 0.88
  - solver: Template-match      mag_residual: 0.12    q: 0.78

quality_scoring:
  metric: mag_residual
  thresholds:
    - {max: 0.03, Q: 1.00}
    - {max: 0.06, Q: 0.90}
    - {max: 0.10, Q: 0.80}
    - {max: 0.15, Q: 0.75}
```

### Baselines

| Solver | mag_residual | Q | Approx Reward |
|--------|-------------|---|---------------|
| SNEC-hydro | 0.05 | 0.95 | ~285 PWM |
| Arnett-analytic | 0.08 | 0.88 | ~264 PWM |
| Template-match | 0.12 | 0.78 | ~234 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Photometric bands and time coverage match spec | PASS |
| S2 | Problem well-posed: Arnett model has analytic solution | PASS |
| S3 | SNEC converges; residuals decrease with model refinement | PASS |
| S4 | Baseline meets threshold (mag_err < 0.1); feasibility confirmed | PASS |

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
| SNEC-hydro | 0.05 | ~20 min | 0.95 | ~285 PWM |
| Arnett-analytic | 0.08 | ~1 min | 0.88 | ~264 PWM |
| Template-match | 0.12 | ~10 s | 0.78 | ~234 PWM |

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
  "principle": "#372 Supernova Light Curve Fitting",
  "h_p": "sha256:<principle_372_hash>",
  "h_s": "sha256:<spec_372_hash>",
  "h_b": "sha256:<bench_372_hash>",
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
pwm-node benchmarks | grep supernova_light_curve
pwm-node verify AC_astrophysics/supernova_light_curve_s1_ideal.yaml
pwm-node mine AC_astrophysics/supernova_light_curve_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
