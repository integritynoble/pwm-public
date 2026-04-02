# Principle #371 — Stellar Atmosphere (Radiative Transfer): Four-Layer Walkthrough

**Principle #371: Stellar Atmosphere (Radiative Transfer)**
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
μ dI_ν/dτ_ν = I_ν - S_ν          (plane-parallel radiative transfer)
S_ν = (1-ε)J_ν + εB_ν(T)        (source function, scattering + thermal)
κ_ν = Σ_i n_i σ_i(ν)            (opacity from atomic/molecular data)
F_ν = ∫ I_ν μ dΩ                 (emergent flux / spectrum)
```

### DAG Decomposition G = (V, A)

```
[∂.space] -> [N.pointwise] -> [B.surface]

V = {∂.space, N.pointwise, B.surface}
A = {∂.space->N.pointwise, N.pointwise->B.surface}
L_DAG = 2.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- formal solution of RT equation exists for bounded opacity |
| Uniqueness | YES -- given T(τ) and opacity, emergent spectrum is unique |
| Stability | YES -- smooth dependence on T_eff, log g, [Fe/H] |

Mismatch parameters: effective temperature T_eff, surface gravity log g, metallicity [Fe/H], microturbulence

### Error-Bounding Method

```
e  = flux residual Σ|F_obs - F_model|/F_obs (primary), chi-squared (secondary)
q = 2.0 (ALI convergence rate)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Optical depth τ dimensionless; flux [erg/s/cm²/Hz] consistent | PASS |
| S2 | RT equation with bounded κ yields unique emergent spectrum | PASS |
| S3 | ALI (accelerated lambda iteration) converges for NLTE atmospheres | PASS |
| S4 | Synthetic spectra match observed solar spectrum to < 2% in continuum | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_371_hash>

omega:
  description: "Solar atmosphere, T_eff=5778K, log_g=4.44, [Fe/H]=0.0"
  wavelength_range_nm: [300, 1000]
  n_depth_points: 72
  outputs: [emergent_spectrum, T_tau_profile]

E:
  forward: "μ dI/dτ = I - S"
  dag: "[∂.space] -> [N.pointwise] -> [B.surface]"

B:
  constraints: "radiative equilibrium; hydrostatic equilibrium; LTE or NLTE"

I:
  scenario: ideal
  parameters: {T_eff: 5778, log_g: 4.44, Fe_H: 0.0}
  mismatch: null

O: [flux_residual, chi2]

epsilon:
  flux_err_max: 0.02
  convergence_order: 2.0

difficulty:
  L_DAG: 2.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known T_eff, log g, [Fe/H] | None | flux_err < 2% |
| S2 Mismatch | Wrong T_eff or metallicity | Applied | relaxed 1.5x |
| S3 Oracle | True atmosphere known | Known | flux_err < 2% |
| S4 Blind Cal | Fit stellar parameters from spectrum | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_371_hash>
principle_ref: sha256:<principle_371_hash>

dataset:
  description: "Synthetic and observed stellar spectra for FGKM stars"
  spectral_types: [F5, G2, K2, M0]
  data_hash: sha256:<dataset_371_hash>

baselines:
  - solver: ATLAS9/SYNTHE       flux_residual: 0.01    q: 0.95
  - solver: MARCS/Turbospectrum flux_residual: 0.015   q: 0.90
  - solver: PHOENIX             flux_residual: 0.02    q: 0.85

quality_scoring:
  metric: flux_residual
  thresholds:
    - {max: 0.005, Q: 1.00}
    - {max: 0.010, Q: 0.90}
    - {max: 0.020, Q: 0.80}
    - {max: 0.030, Q: 0.75}
```

### Baselines

| Solver | flux_residual | Q | Approx Reward |
|--------|-------------|---|---------------|
| ATLAS9/SYNTHE | 0.01 | 0.95 | ~285 PWM |
| MARCS/Turbospectrum | 0.015 | 0.90 | ~270 PWM |
| PHOENIX | 0.02 | 0.85 | ~255 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Wavelength ranges and spectral types match spec | PASS |
| S2 | Problem well-posed: solar spectrum provides ground truth | PASS |
| S3 | ATLAS9 converges; flux residual decreases with depth refinement | PASS |
| S4 | Baseline meets threshold (flux_err < 2%); feasibility confirmed | PASS |

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
| ATLAS9/SYNTHE | 0.01 | ~5 min | 0.95 | ~285 PWM |
| MARCS/Turbospectrum | 0.015 | ~8 min | 0.90 | ~270 PWM |
| PHOENIX | 0.02 | ~15 min | 0.85 | ~255 PWM |

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
  "principle": "#371 Stellar Atmosphere (Radiative Transfer)",
  "h_p": "sha256:<principle_371_hash>",
  "h_s": "sha256:<spec_371_hash>",
  "h_b": "sha256:<bench_371_hash>",
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
pwm-node benchmarks | grep stellar_atmosphere
pwm-node verify AC_astrophysics/stellar_atmosphere_s1_ideal.yaml
pwm-node mine AC_astrophysics/stellar_atmosphere_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
