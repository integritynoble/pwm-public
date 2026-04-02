# Principle #370 — Stellar Structure and Evolution: Four-Layer Walkthrough

**Principle #370: Stellar Structure and Evolution**
Domain: Astrophysics & Cosmology | Carrier: gravitational/radiative | Difficulty: standard (delta=3) | Reward: 3x base

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
dP/dr = -Gm(r)ρ/r²           (hydrostatic equilibrium)
dm/dr = 4πr²ρ                 (mass continuity)
dL/dr = 4πr²ρε               (energy generation)
dT/dr = -3κρL/(16πacr²T³)    (radiative transport)
dX_i/dt = nuclear reaction rates  (composition evolution)
```

### DAG Decomposition G = (V, A)

```
[∂.space] -> [N.pointwise] -> [B.surface] -> [∫.volume]

V = {∂.space, N.pointwise, B.surface, ∫.volume}
A = {∂.space->N.pointwise, N.pointwise->B.surface, B.surface->∫.volume}
L_DAG = 3.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- hydrostatic equilibrium with EOS yields unique radial profiles |
| Uniqueness | YES -- Vogt-Russell theorem: mass + composition determine structure |
| Stability | YES -- thermal and dynamical stability for main-sequence stars |

Mismatch parameters: opacity tables κ(ρ,T), reaction rates, mixing length α, mass loss rate

### Error-Bounding Method

```
e  = luminosity relative error (primary), radius relative error (secondary)
q = 2.0 (second-order shooting method)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Pressure [Pa], mass [kg], luminosity [W] units consistent across equations | PASS |
| S2 | Hydrostatic equilibrium well-posed with boundary conditions (center + surface) | PASS |
| S3 | Henyey method converges for main-sequence models | PASS |
| S4 | L and R match observed HR diagram to 5% for solar-type stars | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_370_hash>

omega:
  description: "Solar-mass star, ZAMS to RGB, 1000 radial zones"
  mass_solar: 1.0
  metallicity: 0.02
  outputs: [L_profile, R_profile, T_c, rho_c]

E:
  forward: "dP/dr = -Gmρ/r²; dL/dr = 4πr²ρε"
  dag: "[∂.space] -> [N.pointwise] -> [B.surface] -> [∫.volume]"

B:
  constraints: "P(R)=0; m(0)=0; L(0)=0; T smooth"

I:
  scenario: ideal
  initial_conditions: ZAMS, solar composition
  mismatch: null

O: [L_error, R_error]

epsilon:
  L_err_max: 0.05
  R_err_max: 0.03

difficulty:
  L_DAG: 3.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known opacity + reaction rates | None | L_err < 5% |
| S2 Mismatch | Wrong mixing length or opacity | Applied | relaxed 1.5x |
| S3 Oracle | True parameters known | Known | L_err < 5% |
| S4 Blind Cal | Calibrate α_MLT from observables | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_370_hash>
principle_ref: sha256:<principle_370_hash>

dataset:
  description: "Stellar evolution tracks for 0.8-2.0 solar masses"
  masses_solar: [0.8, 1.0, 1.5, 2.0]
  data_hash: sha256:<dataset_370_hash>

baselines:
  - solver: MESA               L_error: 0.02    q: 0.95
  - solver: Geneva-code        L_error: 0.03    q: 0.90
  - solver: Simple-polytrope   L_error: 0.10    q: 0.78

quality_scoring:
  metric: L_error
  thresholds:
    - {max: 0.01, Q: 1.00}
    - {max: 0.03, Q: 0.90}
    - {max: 0.05, Q: 0.80}
    - {max: 0.08, Q: 0.75}
```

### Baselines

| Solver | L_error | Q | Approx Reward |
|--------|--------|---|---------------|
| MESA | 0.02 | 0.95 | ~285 PWM |
| Geneva-code | 0.03 | 0.90 | ~270 PWM |
| Simple-polytrope | 0.10 | 0.78 | ~234 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Mass range matches spec; composition tables consistent | PASS |
| S2 | Problem well-posed: Henyey method converges for all masses | PASS |
| S3 | MESA converges; L tracks stable with zone refinement | PASS |
| S4 | Baseline meets threshold (L_err < 5%); feasibility confirmed | PASS |

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
| MESA | 0.02 | ~10 min | 0.95 | ~285 PWM |
| Geneva-code | 0.03 | ~15 min | 0.90 | ~270 PWM |
| Simple-polytrope | 0.10 | ~1 min | 0.78 | ~234 PWM |

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
  "principle": "#370 Stellar Structure and Evolution",
  "h_p": "sha256:<principle_370_hash>",
  "h_s": "sha256:<spec_370_hash>",
  "h_b": "sha256:<bench_370_hash>",
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
pwm-node benchmarks | grep stellar_structure
pwm-node verify AC_astrophysics/stellar_structure_s1_ideal.yaml
pwm-node mine AC_astrophysics/stellar_structure_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
