# Principle #377 — Galaxy SED Fitting: Four-Layer Walkthrough

**Principle #377: Galaxy SED Fitting**
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
F_λ = ∫₀ᵗ SFR(t-τ) SSP(λ,τ,Z) A(λ) dτ     (composite SED)
SSP(λ,τ,Z): simple stellar population spectrum (age τ, metallicity Z)
A(λ) = 10^{-0.4 k(λ) E(B-V)}               (dust attenuation)
m_band = -2.5 log₁₀[∫ F_λ R_band(λ) dλ / ∫ R_band(λ) dλ] + zp
```

### DAG Decomposition G = (V, A)

```
[L.sparse] -> [∫.volume] -> [O.l2]

V = {L.sparse, ∫.volume, O.l2}
A = {L.sparse->∫.volume, ∫.volume->O.l2}
L_DAG = 2.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- convolution of SFH with SSP library yields unique SED |
| Uniqueness | CONDITIONAL -- age-dust-metallicity degeneracy; resolved with sufficient bands |
| Stability | CONDITIONAL -- prior-dependent for photometric data; stable for spectroscopy |

Mismatch parameters: SFH parametrization, dust law, IMF, metallicity, redshift

### Error-Bounding Method

```
e  = log stellar mass error (primary), chi-squared per band (secondary)
q = 0.5 (MCMC posterior convergence)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Flux [erg/s/cm²/Hz], magnitude [AB mag], wavelength [nm] consistent | PASS |
| S2 | SED model bounded for physical SFH + dust; chi-squared computable | PASS |
| S3 | MCMC/nested sampling converges for > 5 photometric bands | PASS |
| S4 | Stellar mass recoverable to 0.2 dex for multi-band photometry | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_377_hash>

omega:
  description: "Galaxy SED fitting, 10-band ugrizJHK+IRAC, z=0.5-2.0"
  n_bands: 10
  redshift_range: [0.5, 2.0]
  outputs: [stellar_mass, SFR, dust, age, metallicity]

E:
  forward: "F_λ = ∫ SFR(t-τ) SSP(λ,τ,Z) A(λ) dτ"
  dag: "[L.sparse] -> [∫.volume] -> [O.l2]"

B:
  constraints: "M* > 0; SFR ≥ 0; 0 ≤ E(B-V) ≤ 1; physical age < t(z)"

I:
  scenario: ideal
  mock_parameters: {logM: 10.5, SFR: 10.0, EBV: 0.2, Z: 0.02, z: 1.0}
  mismatch: null

O: [logM_error, chi2_per_band]

epsilon:
  logM_err_max: 0.20
  convergence_order: 0.5

difficulty:
  L_DAG: 3.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known SSP library + true z | None | logM_err < 0.2 dex |
| S2 Mismatch | Wrong dust law or IMF | Applied | relaxed 1.5x |
| S3 Oracle | True SFH known | Known | logM_err < 0.2 dex |
| S4 Blind Cal | Fit all parameters from photometry | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_377_hash>
principle_ref: sha256:<principle_377_hash>

dataset:
  description: "Mock galaxy photometry with known physical parameters"
  n_galaxies: 1000
  data_hash: sha256:<dataset_377_hash>

baselines:
  - solver: CIGALE             logM_error: 0.10    q: 0.95
  - solver: BAGPIPES           logM_error: 0.12    q: 0.92
  - solver: LePhare            logM_error: 0.18    q: 0.82

quality_scoring:
  metric: logM_error
  thresholds:
    - {max: 0.08, Q: 1.00}
    - {max: 0.12, Q: 0.90}
    - {max: 0.20, Q: 0.80}
    - {max: 0.30, Q: 0.75}
```

### Baselines

| Solver | logM_error | Q | Approx Reward |
|--------|-----------|---|---------------|
| CIGALE | 0.10 | 0.95 | ~285 PWM |
| BAGPIPES | 0.12 | 0.92 | ~276 PWM |
| LePhare | 0.18 | 0.82 | ~246 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Band counts and redshift range match spec | PASS |
| S2 | Problem well-posed: mock galaxies have known truth | PASS |
| S3 | CIGALE MCMC converges; mass estimates stable with chain length | PASS |
| S4 | Baseline meets threshold (logM_err < 0.2); feasibility confirmed | PASS |

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
| CIGALE | 0.10 dex | ~5 min | 0.95 | ~285 PWM |
| BAGPIPES | 0.12 dex | ~8 min | 0.92 | ~276 PWM |
| LePhare | 0.18 dex | ~1 min | 0.82 | ~246 PWM |

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
  "principle": "#377 Galaxy SED Fitting",
  "h_p": "sha256:<principle_377_hash>",
  "h_s": "sha256:<spec_377_hash>",
  "h_b": "sha256:<bench_377_hash>",
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
pwm-node benchmarks | grep galaxy_sed
pwm-node verify AC_astrophysics/galaxy_sed_s1_ideal.yaml
pwm-node mine AC_astrophysics/galaxy_sed_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
