# Principle #369 — Weak Gravitational Lensing (Shear): Four-Layer Walkthrough

**Principle #369: Weak Gravitational Lensing (Shear)**
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
γ(θ) = (1/π) ∫ D(θ-θ') κ(θ') d²θ'   (shear-convergence relation)
κ(θ) = Σ(θ)/Σ_cr                       (convergence from projected mass)
⟨ε⟩ ≈ γ  (galaxy ellipticity → shear in weak limit)
P_κ(l) = (9H₀⁴Ω_m²/4c⁴) ∫ W²(χ)/a² P_δ(l/χ, χ) dχ  (convergence power spectrum)
```

### DAG Decomposition G = (V, A)

```
[K.green] -> [∫.volume] -> [O.l2]

V = {K.green, ∫.volume, O.l2}
A = {K.green->∫.volume, ∫.volume->O.l2}
L_DAG = 2.0   Tier: hard (delta = 5)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- convergence field exists for any matter distribution |
| Uniqueness | YES -- Kaiser-Squires inversion unique up to mass-sheet degeneracy |
| Stability | CONDITIONAL -- shape noise dominates; requires large galaxy samples |

Mismatch parameters: intrinsic alignment, photo-z bias, PSF model error, shear calibration

### Error-Bounding Method

```
e  = convergence power spectrum P_κ(l) relative error (primary), mass map correlation (secondary)
q = 0.5 (shape noise limited, sqrt(N) scaling)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Shear γ dimensionless; convergence κ dimensionless; power spectrum units consistent | PASS |
| S2 | Kaiser-Squires inversion well-posed with boundary conditions | PASS |
| S3 | Mass map reconstruction converges with increasing galaxy density | PASS |
| S4 | P_κ(l) recoverable to 5% for n_gal > 10 arcmin⁻² | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_369_hash>

omega:
  description: "Weak lensing mass map, 10x10 deg² field, n_gal=20/arcmin²"
  grid: [512, 512]
  field_deg: 10
  outputs: [kappa_map, Pk_kappa]

E:
  forward: "γ(θ) = (1/π) ∫ D(θ-θ')κ(θ') d²θ'"
  dag: "[K.green] -> [∫.volume] -> [O.l2]"

B:
  constraints: "κ curl-free (B-mode = 0); mass-sheet degeneracy broken"

I:
  scenario: ideal
  galaxy_density: 20
  shape_noise: 0.3
  mismatch: null

O: [Pk_kappa_error, mass_map_correlation]

epsilon:
  Pk_err_max: 0.05
  correlation_min: 0.85

difficulty:
  L_DAG: 3.0
  tier: hard
  delta: 5
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known shear + no systematics | None | Pk_err < 5% |
| S2 Mismatch | PSF model error or photo-z bias | Applied | relaxed 1.5x |
| S3 Oracle | True κ known | Known | Pk_err < 5% |
| S4 Blind Cal | Self-calibrate shear from data | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_369_hash>
principle_ref: sha256:<principle_369_hash>

dataset:
  description: "Simulated weak lensing shear catalogs at multiple densities"
  galaxy_densities: [5, 10, 20, 40]
  data_hash: sha256:<dataset_369_hash>

baselines:
  - solver: Kaiser-Squires       Pk_error: 0.04    q: 0.92
  - solver: Wiener-filter        Pk_error: 0.03    q: 0.95
  - solver: DeepMass-CNN         Pk_error: 0.025   q: 0.96

quality_scoring:
  metric: Pk_kappa_error
  thresholds:
    - {max: 0.02, Q: 1.00}
    - {max: 0.03, Q: 0.90}
    - {max: 0.05, Q: 0.80}
    - {max: 0.08, Q: 0.75}
```

### Baselines

| Solver | Pk_error | Q | Approx Reward |
|--------|---------|---|---------------|
| DeepMass-CNN | 0.025 | 0.96 | ~480 PWM |
| Wiener-filter | 0.03 | 0.95 | ~475 PWM |
| Kaiser-Squires | 0.04 | 0.92 | ~460 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Galaxy densities match spec; shear catalog format consistent | PASS |
| S2 | Problem well-posed: KS inversion bounded with smoothing | PASS |
| S3 | Wiener filter converges; residual decreases with galaxy density | PASS |
| S4 | Baseline meets threshold (Pk_err < 5%); feasibility confirmed | PASS |

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
| DeepMass-CNN | 0.025 | ~30 s | 0.96 | ~480 PWM |
| Wiener-filter | 0.03 | ~1 min | 0.95 | ~475 PWM |
| Kaiser-Squires | 0.04 | ~10 s | 0.92 | ~460 PWM |

### Reward Calculation

```
R = R_base x phi(t) x delta x nu_c x q
  = 100 x 1.0 x 5 x 1.0 x q
  = 500 x q  PWM

Best case:  500 x 0.96 = 480 PWM
Worst case: 500 x 0.75 = 375 PWM
```

### S4 Certificate

```json
{
  "principle": "#369 Weak Gravitational Lensing (Shear)",
  "h_p": "sha256:<principle_369_hash>",
  "h_s": "sha256:<spec_369_hash>",
  "h_b": "sha256:<bench_369_hash>",
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"},
  "Q": 0.96,
  "difficulty": {"tier":"hard","delta":5}
}
```

---

## Reward Summary

```
L1 Principle:  200 PWM seed + upstream royalties from L2/L3/L4
L2 spec.md:    105 PWM seed (x4 scenarios = 420 PWM) + upstream from L3/L4
L3 Benchmark:   60 PWM seed (x4 benchmarks = 240 PWM) + upstream from L4
L4 Solution:   375-480 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep weak_lensing
pwm-node verify AC_astrophysics/weak_lensing_s1_ideal.yaml
pwm-node mine AC_astrophysics/weak_lensing_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
