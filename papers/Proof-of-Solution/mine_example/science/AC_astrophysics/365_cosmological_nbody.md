# Principle #365 — Cosmological N-Body (Cold Dark Matter): Four-Layer Walkthrough

**Principle #365: Cosmological N-Body (Cold Dark Matter)**
Domain: Astrophysics & Cosmology | Carrier: gravitational | Difficulty: hard (delta=5) | Reward: 5x base

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
d²r_i/dt² = -∇Φ(r_i)     (particle equation of motion)
∇²Φ = 4πGa⁻¹[ρ(x) - ρ̄]  (Poisson equation in comoving coords)
a(t): Friedmann expansion factor
```

### DAG Decomposition G = (V, A)

```
[N.bilinear.pair] -> [∂.time.symplectic] -> [∫.volume]

V = {N.bilinear.pair, ∂.time.symplectic, ∫.volume}
A = {N.bilinear.pair->∂.time.symplectic, ∂.time.symplectic->∫.volume}
L_DAG = 2.0   Tier: hard (delta = 5)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- Vlasov-Poisson in expanding background has classical solutions |
| Uniqueness | YES -- unique for given cosmological parameters and initial power spectrum |
| Stability | CONDITIONAL -- force resolution and mass resolution must exceed Jeans scale |

Mismatch parameters: Omega_m, Omega_Lambda, sigma_8, force softening, box size L

### Error-Bounding Method

```
e  = power spectrum P(k) relative error (primary), halo mass function error (secondary)
q = 2.0 (PM) or 1.3 (adaptive refinement)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Comoving coordinates consistent with Friedmann expansion; density units match | PASS |
| S2 | Poisson equation well-posed on periodic domain; PM grid resolves Jeans scale | PASS |
| S3 | TreePM / P3M converges with resolution; validated against Zel'dovich solution | PASS |
| S4 | P(k) recoverable to 1% for k < k_Nyquist/2 | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_365_hash>

omega:
  description: "Lambda-CDM box, L=256 Mpc/h, N=256³, z_init=99 -> z=0"
  grid: [256, 256, 256]
  box_size_Mpc_h: 256
  outputs: [power_spectrum, halo_catalog]

E:
  forward: "d²r/dt² = -∇Φ; ∇²Φ = 4πGa⁻¹(ρ-ρ̄)"
  dag: "[N.bilinear.pair] -> [∂.time.symplectic] -> [∫.volume]"

B:
  constraints: "periodic boundary; total momentum conserved; mass conserved"

I:
  scenario: ideal
  cosmology: {Omega_m: 0.3, Omega_L: 0.7, h: 0.7, sigma_8: 0.8}
  initial_conditions: Zel'dovich approximation at z=99
  mismatch: null

O: [Pk_relative_error, halo_mass_function_error]

epsilon:
  Pk_err_max: 0.01
  convergence_order: 2.0

difficulty:
  L_DAG: 4.0
  tier: hard
  delta: 5
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known cosmology + exact IC | None | Pk_err < 1% |
| S2 Mismatch | Wrong Omega_m or sigma_8 | Applied | relaxed 1.5x |
| S3 Oracle | True cosmology known | Known | Pk_err < 1% |
| S4 Blind Cal | Estimate cosmology from clustering | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_365_hash>
principle_ref: sha256:<principle_365_hash>

dataset:
  description: "Lambda-CDM cosmological N-body at multiple resolutions"
  N_particles: [64^3, 128^3, 256^3]
  data_hash: sha256:<dataset_365_hash>

baselines:
  - solver: Gadget-4 TreePM     Pk_error: 0.005    q: 0.95
  - solver: PM-only              Pk_error: 0.03     q: 0.80
  - solver: COLA                 Pk_error: 0.015    q: 0.88

quality_scoring:
  metric: Pk_relative_error
  thresholds:
    - {max: 0.003, Q: 1.00}
    - {max: 0.008, Q: 0.90}
    - {max: 0.015, Q: 0.80}
    - {max: 0.030, Q: 0.75}
```

### Baselines

| Solver | Pk_error | Q | Approx Reward |
|--------|---------|---|---------------|
| Gadget-4 TreePM | 0.005 | 0.95 | ~475 PWM |
| COLA | 0.015 | 0.88 | ~440 PWM |
| PM-only | 0.030 | 0.80 | ~400 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Particle count and box size match spec; IC power spectrum consistent | PASS |
| S2 | Problem well-posed: Zel'dovich solution validates early-time evolution | PASS |
| S3 | TreePM converges; P(k) stable with increasing resolution | PASS |
| S4 | Baseline meets threshold (Pk_err < 1%); feasibility confirmed | PASS |

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
| Gadget-4 TreePM | 0.005 | ~30 min | 0.95 | ~475 PWM |
| COLA | 0.015 | ~5 min | 0.88 | ~440 PWM |
| PM-only | 0.030 | ~2 min | 0.80 | ~400 PWM |

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
  "principle": "#365 Cosmological N-Body (Cold Dark Matter)",
  "h_p": "sha256:<principle_365_hash>",
  "h_s": "sha256:<spec_365_hash>",
  "h_b": "sha256:<bench_365_hash>",
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
pwm-node benchmarks | grep cosmological_nbody
pwm-node verify AC_astrophysics/cosmological_nbody_s1_ideal.yaml
pwm-node mine AC_astrophysics/cosmological_nbody_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
