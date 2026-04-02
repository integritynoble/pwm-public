# Principle #350 — Plasma Sheath: Four-Layer Walkthrough

**Principle #350: Plasma Sheath Structure**
Domain: Plasma Physics | Carrier: electromagnetic | Difficulty: standard (delta=3) | Reward: 3x base

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
d^2(phi)/dx^2 = (e/eps0)(n_e - n_i)              (Poisson)
n_e = n0 * exp(e*phi / (k_B*T_e))                (Boltzmann electrons)
n_i: (1/2)*m_i*v_i^2 + e*phi = (1/2)*m_i*v_0^2   (ion energy conservation)
n_i*v_i = n0*v_0                                   (ion flux conservation)
Bohm criterion: v_0 >= c_s = sqrt(k_B*T_e / m_i)
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
| Existence | YES -- Bohm criterion ensures monotonic potential profile |
| Uniqueness | YES -- given wall potential and Bohm entrance velocity |
| Stability | CONDITIONAL -- Bohm criterion must be satisfied at sheath edge |

Mismatch parameters: electron temperature T_e, ion mass m_i, wall potential phi_w

### Error-Bounding Method

```
e  = sheath thickness error vs Child-Langmuir law
q = 2.0 (second-order for ODE solver)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Poisson + ion continuity dimensions consistent | PASS |
| S2 | Bohm criterion ensures well-posed sheath structure | PASS |
| S3 | Shooting method and PIC both converge | PASS |
| S4 | Sheath thickness computable against Child-Langmuir theory | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_350_hash>

omega:
  description: "Collisionless sheath, 1D, floating wall, T_e=2eV, T_i=0.1eV"
  grid: [1024]
  outputs: [phi(x), n_i(x), n_e(x), v_i(x)]

E:
  forward: "Poisson + Boltzmann electrons + ion continuity"
  dag: "[∂.space] -> [N.pointwise] -> [B.surface]"

I:
  scenario: ideal
  T_e: 2.0   # eV
  T_i: 0.1   # eV
  m_i: 1.0   # proton mass units
  mismatch: null

O: [sheath_thickness_error]

epsilon:
  thickness_err_max: 0.05

difficulty:
  L_DAG: 3.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact T_e, m_i | None | thickness_err < 5% |
| S2 Mismatch | Wrong T_e | Applied | relaxed 1.5x |
| S3 Oracle | True T_e known | Known | thickness_err < 5% |
| S4 Blind Cal | Estimate T_e from I-V characteristic | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_350_hash>
principle_ref: sha256:<principle_350_hash>

dataset:
  description: "Collisionless sheath profiles at multiple T_e values"
  data_hash: sha256:<dataset_350_hash>

baselines:
  - solver: Shooting           sheath_thickness_error: 0.02    q: 0.95
  - solver: PIC-sheath         sheath_thickness_error: 0.035   q: 0.88
  - solver: Fluid              sheath_thickness_error: 0.045   q: 0.80

quality_scoring:
  metric: sheath_thickness_error
  thresholds:
    - {max: 0.01, Q: 1.00}
    - {max: 0.02, Q: 0.90}
    - {max: 0.04, Q: 0.80}
    - {max: 0.05, Q: 0.75}
```

### Baselines

| Solver | sheath_thickness_error | Q | Approx Reward |
|--------|----------------------|---|---------------|
| Shooting | 0.02 | 0.95 | ~285 PWM |
| PIC-sheath | 0.035 | 0.88 | ~264 PWM |
| Fluid | 0.045 | 0.80 | ~240 PWM |

### Layer 3 Reward

```
Benchmark seed reward = 100 x phi(t) x 0.60 = 60 PWM
```

---

## Layer 4: Benchmark -> Solution (PoSol Mining)

### Reward Calculation

```
R = 100 x 1.0 x 3 x 1.0 x q = 300 x q PWM
Best case:  300 x 0.95 = 285 PWM
Worst case: 300 x 0.75 = 225 PWM
```

### S4 Certificate

```json
{
  "principle": "#350 Plasma Sheath",
  "h_p": "sha256:<principle_350_hash>",
  "h_s": "sha256:<spec_350_hash>",
  "h_b": "sha256:<bench_350_hash>",
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"},
  "Q": 0.95,
  "difficulty": {"tier":"standard","delta":3}
}
```

---

## Reward Summary

```
L1 Principle:  200 PWM seed + upstream royalties
L2 spec.md:    105 PWM seed (x4 scenarios = 420 PWM)
L3 Benchmark:   60 PWM seed (x4 benchmarks = 240 PWM)
L4 Solution:   225-285 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep plasma_sheath
pwm-node verify AA_plasma_physics/plasma_sheath_s1_ideal.yaml
pwm-node mine AA_plasma_physics/plasma_sheath_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
