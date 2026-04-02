# Principle #381 — Type Ia Supernova Distance: Four-Layer Walkthrough

**Principle #381: Type Ia Supernova Distance**
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
μ = m_B - M_B + α x₁ - β c         (Tripp standardization)
μ(z) = 5 log₁₀[d_L(z)/10 pc]       (distance modulus)
d_L(z) = (1+z) ∫₀ᶻ c dz'/H(z')    (luminosity distance)
H(z) = H₀ √[Ω_m(1+z)³ + Ω_Λ]      (Friedmann equation, flat ΛCDM)
```

### DAG Decomposition G = (V, A)

```
[L.sparse] -> [∫.temporal] -> [O.l2]

V = {L.sparse, ∫.temporal, O.l2}
A = {L.sparse->∫.temporal, ∫.temporal->O.l2}
L_DAG = 2.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- stretch-color-luminosity relation is empirically calibrated |
| Uniqueness | YES -- (α, β, M_B) uniquely map observables to standardized magnitudes |
| Stability | YES -- smooth dependence on cosmological parameters |

Mismatch parameters: dust law R_V, host mass step, peculiar velocities, survey calibration

### Error-Bounding Method

```
e  = distance modulus residual σ_μ (primary), Hubble residual scatter (secondary)
q = 0.5 (sqrt(N) statistical improvement)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Magnitude [mag], redshift dimensionless, distance [Mpc] consistent | PASS |
| S2 | Tripp relation well-posed; linear in (x₁, c) | PASS |
| S3 | MCMC/chi-squared minimization converges for Pantheon-like samples | PASS |
| S4 | σ_μ ~ 0.15 mag per SN achievable after standardization | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_381_hash>

omega:
  description: "Type Ia SN Hubble diagram, z=0.01-1.5, N=1000"
  n_SNe: 1000
  redshift_range: [0.01, 1.5]
  outputs: [Omega_m, w, H_0, Hubble_diagram]

E:
  forward: "μ = m_B - M_B + α x₁ - β c; μ(z) = 5log₁₀(d_L/10pc)"
  dag: "[L.sparse] -> [∫.temporal] -> [O.l2]"

B:
  constraints: "α > 0; β > 0; 0 < Omega_m < 1; physical distances"

I:
  scenario: ideal
  cosmology: {Omega_m: 0.3, w: -1.0, H_0: 70.0}
  mismatch: null

O: [Omega_m_error, w_error]

epsilon:
  Omega_m_err_max: 0.03
  convergence_order: 0.5

difficulty:
  L_DAG: 2.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known standardization + no systematics | None | Omega_m_err < 3% |
| S2 Mismatch | Wrong dust law or calibration | Applied | relaxed 1.5x |
| S3 Oracle | True cosmology known | Known | Omega_m_err < 3% |
| S4 Blind Cal | Fit cosmology from SN data | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_381_hash>
principle_ref: sha256:<principle_381_hash>

dataset:
  description: "Simulated SN Ia Hubble diagram with known cosmology"
  n_SNe: 1000
  data_hash: sha256:<dataset_381_hash>

baselines:
  - solver: SALT3+BEAMS        Omega_m_error: 0.015    q: 0.95
  - solver: SALT2+chi2         Omega_m_error: 0.020    q: 0.90
  - solver: Simple-Hubble      Omega_m_error: 0.040    q: 0.78

quality_scoring:
  metric: Omega_m_error
  thresholds:
    - {max: 0.010, Q: 1.00}
    - {max: 0.020, Q: 0.90}
    - {max: 0.030, Q: 0.80}
    - {max: 0.050, Q: 0.75}
```

### Baselines

| Solver | Omega_m_error | Q | Approx Reward |
|--------|-------------|---|---------------|
| SALT3+BEAMS | 0.015 | 0.95 | ~285 PWM |
| SALT2+chi2 | 0.020 | 0.90 | ~270 PWM |
| Simple-Hubble | 0.040 | 0.78 | ~234 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | SN count and redshift range match spec | PASS |
| S2 | Problem well-posed: simulated data has known input cosmology | PASS |
| S3 | SALT3 converges; posterior well-sampled | PASS |
| S4 | Baseline meets threshold (Omega_m_err < 3%); feasibility confirmed | PASS |

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
| SALT3+BEAMS | 0.015 | ~5 min | 0.95 | ~285 PWM |
| SALT2+chi2 | 0.020 | ~2 min | 0.90 | ~270 PWM |
| Simple-Hubble | 0.040 | ~30 s | 0.78 | ~234 PWM |

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
  "principle": "#381 Type Ia Supernova Distance",
  "h_p": "sha256:<principle_381_hash>",
  "h_s": "sha256:<spec_381_hash>",
  "h_b": "sha256:<bench_381_hash>",
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
pwm-node benchmarks | grep type_ia_distance
pwm-node verify AC_astrophysics/type_ia_distance_s1_ideal.yaml
pwm-node mine AC_astrophysics/type_ia_distance_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
