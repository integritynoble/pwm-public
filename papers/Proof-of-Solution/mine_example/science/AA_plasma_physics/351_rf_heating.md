# Principle #351 — RF Heating / Wave Propagation: Four-Layer Walkthrough

**Principle #351: RF Wave Heating in Plasmas**
Domain: Plasma Physics | Carrier: electromagnetic | Difficulty: advanced (delta=4) | Reward: 4x base

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
curl(curl E) - (omega^2/c^2) * eps_tensor * E = -i*omega*mu0 * J_ext
eps_tensor: cold plasma dielectric tensor (Stix parameters S, D, P)
S = 1 - sum_s omega_ps^2/(omega^2 - Omega_cs^2)
D = sum_s Omega_cs*omega_ps^2 / (omega*(omega^2 - Omega_cs^2))
P = 1 - sum_s omega_ps^2/omega^2
```

### DAG Decomposition G = (V, A)

```
[∂.time] -> [N.bilinear] -> [∂.space] -> [B.conducting]

V = {∂.time, N.bilinear, ∂.space, B.conducting}
A = {∂.time->N.bilinear, N.bilinear->∂.space, ∂.space->B.conducting}
L_DAG = 3.0   Tier: advanced (delta = 4)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- wave equation with radiation BCs has unique solution |
| Uniqueness | YES -- for given frequency, density profile, and B-field |
| Stability | CONDITIONAL -- cutoff/resonance layers require special treatment |

Mismatch parameters: frequency f, magnetic field B0, density profile n_e(x)

### Error-Bounding Method

```
e  = absorbed power fraction error vs analytic estimates
q = 2.0 (FEM convergence for wave equation)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Dielectric tensor components consistent with cold plasma model | PASS |
| S2 | Wave equation well-posed with radiation boundary conditions | PASS |
| S3 | Full-wave FEM and TORIC-like spectral methods converge | PASS |
| S4 | Absorbed power fraction computable and bounded | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_351_hash>

omega:
  description: "ICRF heating, slab geometry, f=40MHz, B0=3T, n_e=5e19/m^3"
  grid: [512]
  outputs: [E(x), P_abs(x), k(x)]

E:
  forward: "curl(curl E) - (omega^2/c^2)*eps*E = -i*omega*mu0*J_ext"
  dag: "[∂.time] -> [N.bilinear] -> [∂.space] -> [B.conducting]"

I:
  scenario: ideal
  frequency_MHz: 40
  B0_Tesla: 3.0
  n_e: 5.0e19
  mismatch: null

O: [P_abs_error]

epsilon:
  P_abs_err_max: 0.08

difficulty:
  L_DAG: 4.0
  tier: advanced
  delta: 4
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact density profile | None | P_abs_err < 8% |
| S2 Mismatch | Wrong n_e profile | Applied | relaxed 1.5x |
| S3 Oracle | True n_e known | Known | P_abs_err < 8% |
| S4 Blind Cal | Estimate n_e from reflectometry | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_351_hash>
principle_ref: sha256:<principle_351_hash>

dataset:
  description: "ICRF wave propagation and absorption benchmark"
  data_hash: sha256:<dataset_351_hash>

baselines:
  - solver: Full-wave-FEM       P_abs_error: 0.04    q: 0.94
  - solver: TORIC-spectral      P_abs_error: 0.06    q: 0.86
  - solver: WKB-ray             P_abs_error: 0.075   q: 0.78

quality_scoring:
  metric: P_abs_error
  thresholds:
    - {max: 0.02, Q: 1.00}
    - {max: 0.04, Q: 0.90}
    - {max: 0.06, Q: 0.80}
    - {max: 0.08, Q: 0.75}
```

### Baselines

| Solver | P_abs_error | Q | Approx Reward |
|--------|------------|---|---------------|
| Full-wave-FEM | 0.04 | 0.94 | ~376 PWM |
| TORIC-spectral | 0.06 | 0.86 | ~344 PWM |
| WKB-ray | 0.075 | 0.78 | ~312 PWM |

### Layer 3 Reward

```
Benchmark seed reward = 100 x phi(t) x 0.60 = 60 PWM
```

---

## Layer 4: Benchmark -> Solution (PoSol Mining)

### Reward Calculation

```
R = 100 x 1.0 x 4 x 1.0 x q = 400 x q PWM
Best case:  400 x 0.94 = 376 PWM
Worst case: 400 x 0.75 = 300 PWM
```

### S4 Certificate

```json
{
  "principle": "#351 RF Heating",
  "h_p": "sha256:<principle_351_hash>",
  "h_s": "sha256:<spec_351_hash>",
  "h_b": "sha256:<bench_351_hash>",
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"},
  "Q": 0.94,
  "difficulty": {"tier":"advanced","delta":4}
}
```

---

## Reward Summary

```
L1 Principle:  200 PWM seed + upstream royalties
L2 spec.md:    105 PWM seed (x4 scenarios = 420 PWM)
L3 Benchmark:   60 PWM seed (x4 benchmarks = 240 PWM)
L4 Solution:   300-376 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep rf_heating
pwm-node verify AA_plasma_physics/rf_heating_s1_ideal.yaml
pwm-node mine AA_plasma_physics/rf_heating_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
