# Principle #366 — CMB Power Spectrum: Four-Layer Walkthrough

**Principle #366: CMB Power Spectrum**
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
C_l = (4π/(2l+1)) ∫ dk/k  P_R(k) |Δ_l(k)|²
Δ_l(k): transfer function from Boltzmann-Einstein hierarchy
∂f/∂t + (p/E)·∇f = C[f]  (photon Boltzmann equation)
```

### DAG Decomposition G = (V, A)

```
[∂.time] -> [N.boltzmann] -> [∫.multipole]

V = {∂.time, N.boltzmann, ∫.multipole}
A = {∂.time->N.boltzmann, N.boltzmann->∫.multipole}
L_DAG = 2.0   Tier: hard (delta = 5)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- linear perturbation theory yields unique transfer functions |
| Uniqueness | YES -- C_l uniquely determined by cosmological parameters |
| Stability | YES -- smooth dependence on {Omega_b, Omega_c, h, n_s, tau} |

Mismatch parameters: Omega_b h², Omega_c h², n_s, tau (reionization optical depth)

### Error-Bounding Method

```
e  = relative C_l error (primary), chi-squared fit to Planck data (secondary)
q = spectral accuracy (exponential convergence in l-truncation)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Multipole l dimensions consistent; angular power spectrum units [μK²] correct | PASS |
| S2 | Linear perturbation equations well-posed; transfer functions bounded | PASS |
| S3 | CAMB/CLASS converge to sub-percent accuracy at l < 3000 | PASS |
| S4 | C_l residuals vs Planck < 1% achievable | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_366_hash>

omega:
  description: "CMB TT power spectrum, l_max=2500, Planck 2018 cosmology"
  l_max: 2500
  outputs: [C_l_TT, C_l_EE, C_l_TE]

E:
  forward: "C_l = (4π/(2l+1)) ∫ P_R(k)|Δ_l(k)|² dk/k"
  dag: "[∂.time] -> [N.boltzmann] -> [∫.multipole]"

B:
  constraints: "sum rule on C_l; positive definite; gauge invariance"

I:
  scenario: ideal
  cosmology: {Omega_b_h2: 0.0224, Omega_c_h2: 0.120, h: 0.674, n_s: 0.965, tau: 0.054}
  mismatch: null

O: [Cl_relative_error, chi2_planck]

epsilon:
  Cl_err_max: 0.005
  convergence_order: spectral

difficulty:
  L_DAG: 3.0
  tier: hard
  delta: 5
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known cosmology | None | Cl_err < 0.5% |
| S2 Mismatch | Wrong Omega_b or n_s | Applied | relaxed 1.5x |
| S3 Oracle | True params known | Known | Cl_err < 0.5% |
| S4 Blind Cal | Fit cosmology from C_l data | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_366_hash>
principle_ref: sha256:<principle_366_hash>

dataset:
  description: "CMB power spectra at multiple l_max truncations"
  l_max_values: [500, 1000, 2000, 2500]
  data_hash: sha256:<dataset_366_hash>

baselines:
  - solver: CLASS              Cl_error: 0.001    q: 0.95
  - solver: CAMB               Cl_error: 0.002    q: 0.92
  - solver: Simplified-Boltzmann  Cl_error: 0.02  q: 0.78

quality_scoring:
  metric: Cl_relative_error
  thresholds:
    - {max: 0.001, Q: 1.00}
    - {max: 0.003, Q: 0.90}
    - {max: 0.005, Q: 0.80}
    - {max: 0.010, Q: 0.75}
```

### Baselines

| Solver | Cl_error | Q | Approx Reward |
|--------|---------|---|---------------|
| CLASS | 0.001 | 0.95 | ~475 PWM |
| CAMB | 0.002 | 0.92 | ~460 PWM |
| Simplified-Boltzmann | 0.02 | 0.78 | ~390 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | l_max values match spec; cosmological parameters consistent | PASS |
| S2 | Problem well-posed: linear theory guarantees unique C_l | PASS |
| S3 | CLASS converges; C_l stable with increasing l-truncation | PASS |
| S4 | Baseline meets threshold (Cl_err < 0.5%); feasibility confirmed | PASS |

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
| CLASS | 0.001 | ~30 s | 0.95 | ~475 PWM |
| CAMB | 0.002 | ~45 s | 0.92 | ~460 PWM |
| Simplified-Boltzmann | 0.02 | ~5 s | 0.78 | ~390 PWM |

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
  "principle": "#366 CMB Power Spectrum",
  "h_p": "sha256:<principle_366_hash>",
  "h_s": "sha256:<spec_366_hash>",
  "h_b": "sha256:<bench_366_hash>",
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
pwm-node benchmarks | grep cmb_power_spectrum
pwm-node verify AC_astrophysics/cmb_power_spectrum_s1_ideal.yaml
pwm-node mine AC_astrophysics/cmb_power_spectrum_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
