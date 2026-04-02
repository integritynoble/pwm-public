# Principle #378 — 21cm Cosmology: Four-Layer Walkthrough

**Principle #378: 21cm Cosmology**
Domain: Astrophysics & Cosmology | Carrier: electromagnetic | Difficulty: hard (delta=5) | Reward: 5x base

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
δT_b = 27 x_HI (1+δ) [(T_s - T_CMB)/T_s] [(1+z)/10]^{1/2} [H/(dv_r/dr + H)]  mK
T_s⁻¹ = (T_CMB⁻¹ + x_α T_α⁻¹ + x_c T_K⁻¹) / (1 + x_α + x_c)  (spin temperature)
x_HI: neutral hydrogen fraction (reionization dependent)
```

### DAG Decomposition G = (V, A)

```
[∂.time] -> [N.boltzmann] -> [∫.volume]

V = {∂.time, N.boltzmann, ∫.volume}
A = {∂.time->N.boltzmann, N.boltzmann->∫.volume}
L_DAG = 2.0   Tier: hard (delta = 5)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- brightness temperature determined by (x_HI, T_s, δ) fields |
| Uniqueness | YES -- given astrophysical parameters, signal is unique |
| Stability | CONDITIONAL -- foreground contamination 4-5 orders above signal |

Mismatch parameters: ionizing efficiency ζ, minimum halo mass, X-ray luminosity, Ly-α coupling

### Error-Bounding Method

```
e  = power spectrum P(k) relative error (primary), global signal ΔT_b error (secondary)
q = 1.0 (semi-numerical simulation convergence)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Brightness temperature [mK]; frequency [MHz] ↔ redshift consistent | PASS |
| S2 | 21cm signal bounded for physical T_s and x_HI ranges | PASS |
| S3 | 21cmFAST converges; P(k) stable with box size | PASS |
| S4 | P(k) distinguishable from noise for SKA-level sensitivity | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_378_hash>

omega:
  description: "21cm power spectrum, z=7-12, box=256 Mpc, 200³ grid"
  grid: [200, 200, 200]
  redshift_range: [7, 12]
  outputs: [Pk_21cm, global_signal, x_HI_history]

E:
  forward: "δT_b = 27 x_HI (1+δ)[(T_s-T_CMB)/T_s]..."
  dag: "[∂.time] -> [N.boltzmann] -> [∫.volume]"

B:
  constraints: "0 ≤ x_HI ≤ 1; T_s > 0; causality in light-cone"

I:
  scenario: ideal
  parameters: {zeta: 30, T_vir_min: 1e4, L_X: 1e40}
  mismatch: null

O: [Pk_error, global_signal_error]

epsilon:
  Pk_err_max: 0.10
  convergence_order: 1.0

difficulty:
  L_DAG: 3.0
  tier: hard
  delta: 5
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known astrophysical parameters | None | Pk_err < 10% |
| S2 Mismatch | Wrong ζ or X-ray luminosity | Applied | relaxed 1.5x |
| S3 Oracle | True reionization history known | Known | Pk_err < 10% |
| S4 Blind Cal | Infer parameters from 21cm data | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_378_hash>
principle_ref: sha256:<principle_378_hash>

dataset:
  description: "21cm simulations at multiple astrophysical parameter sets"
  n_models: 20
  data_hash: sha256:<dataset_378_hash>

baselines:
  - solver: 21cmFAST           Pk_error: 0.05    q: 0.95
  - solver: SimFast21          Pk_error: 0.08    q: 0.88
  - solver: Analytical-bubble  Pk_error: 0.15    q: 0.78

quality_scoring:
  metric: Pk_error
  thresholds:
    - {max: 0.03, Q: 1.00}
    - {max: 0.06, Q: 0.90}
    - {max: 0.10, Q: 0.80}
    - {max: 0.15, Q: 0.75}
```

### Baselines

| Solver | Pk_error | Q | Approx Reward |
|--------|---------|---|---------------|
| 21cmFAST | 0.05 | 0.95 | ~475 PWM |
| SimFast21 | 0.08 | 0.88 | ~440 PWM |
| Analytical-bubble | 0.15 | 0.78 | ~390 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Box sizes and redshift ranges match spec | PASS |
| S2 | Problem well-posed: full radiative transfer provides ground truth | PASS |
| S3 | 21cmFAST converges; P(k) stable with grid refinement | PASS |
| S4 | Baseline meets threshold (Pk_err < 10%); feasibility confirmed | PASS |

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
| 21cmFAST | 0.05 | ~15 min | 0.95 | ~475 PWM |
| SimFast21 | 0.08 | ~10 min | 0.88 | ~440 PWM |
| Analytical-bubble | 0.15 | ~1 min | 0.78 | ~390 PWM |

### Reward Calculation

```
R = R_base x phi(t) x delta x nu_c x q
  = 100 x 1.0 x 5 x 1.0 x q
  = 500 x q  PWM

Best case:  500 x 0.95 = 475 PWM
Worst case: 500 x 0.75 = 375 PWM
```

### S4 Certificate

```json
{
  "principle": "#378 21cm Cosmology",
  "h_p": "sha256:<principle_378_hash>",
  "h_s": "sha256:<spec_378_hash>",
  "h_b": "sha256:<bench_378_hash>",
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"},
  "Q": 0.95,
  "difficulty": {"tier":"hard","delta":5}
}
```

---

## Reward Summary

```
L1 Principle:  200 PWM seed + upstream royalties from L2/L3/L4
L2 spec.md:    105 PWM seed (x4 scenarios = 420 PWM) + upstream from L3/L4
L3 Benchmark:   60 PWM seed (x4 benchmarks = 240 PWM) + upstream from L4
L4 Solution:   375-475 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep 21cm_cosmology
pwm-node verify AC_astrophysics/21cm_cosmology_s1_ideal.yaml
pwm-node mine AC_astrophysics/21cm_cosmology_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
