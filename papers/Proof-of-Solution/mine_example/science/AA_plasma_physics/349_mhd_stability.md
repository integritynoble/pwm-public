# Principle #349 — MHD Stability: Four-Layer Walkthrough

**Principle #349: MHD Energy Principle / Stability Analysis**
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
delta_W = (1/2) int [ |curl(xi x B)|^2/mu0 + gamma*q|div(xi)|^2
          - J_par*(xi_perp x b)*curl(xi_perp)
          - 2*(xi_perqgrad p)*(xi_perqkappa) ] dV

Stability: delta_W > 0 for all admissible displacements xi
Ballooning limit: s - alpha diagram for n -> infinity
```

### DAG Decomposition G = (V, A)

```
[E.hermitian] -> [L.hamiltonian] -> [N.bilinear]

V = {E.hermitian, L.hamiltonian, N.bilinear}
A = {E.hermitian->L.hamiltonian, L.hamiltonian->N.bilinear}
L_DAG = 2.0   Tier: advanced (delta = 4)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- energy functional is bounded below for physical equilibria |
| Uniqueness | YES -- stability boundary well-defined in parameter space |
| Stability | CONDITIONAL -- requires accurate equilibrium as input |

Mismatch parameters: magnetic shear s, normalized pressure gradient alpha, safety factor q

### Error-Bounding Method

```
e  = critical alpha error vs analytic s-alpha boundary
q = 2.0 (spectral convergence for ballooning equation)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Energy functional terms dimensionally consistent | PASS |
| S2 | delta_W is real-valued and bounded below | PASS |
| S3 | Spectral ELITE and shooting method converge | PASS |
| S4 | Critical alpha computable and comparable to analytic boundary | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_349_hash>

omega:
  description: "Ballooning stability, n->inf, s-alpha diagram"
  grid: [128]   # ballooning angle theta
  outputs: [growth_rate, stability_boundary]

E:
  forward: "delta_W energy functional"
  dag: "[E.hermitian] -> [L.hamiltonian] -> [N.bilinear]"

I:
  scenario: ideal
  shear_range: [0.0, 3.0]
  alpha_range: [0.0, 2.0]
  q: 1.5
  mismatch: null

O: [alpha_crit_error]

epsilon:
  alpha_crit_err_max: 0.03

difficulty:
  L_DAG: 4.0
  tier: advanced
  delta: 4
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact equilibrium | None | alpha_crit_err < 3% |
| S2 Mismatch | Wrong shear profile | Applied | relaxed 1.5x |
| S3 Oracle | True shear known | Known | alpha_crit_err < 3% |
| S4 Blind Cal | Estimate shear from equilibrium reconstruction | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_349_hash>
principle_ref: sha256:<principle_349_hash>

dataset:
  description: "s-alpha ballooning diagram benchmark"
  data_hash: sha256:<dataset_349_hash>

baselines:
  - solver: Spectral-ELITE      alpha_crit_error: 0.01    q: 0.96
  - solver: Shooting            alpha_crit_error: 0.02    q: 0.90
  - solver: FEM-variational     alpha_crit_error: 0.028   q: 0.82

quality_scoring:
  metric: alpha_crit_error
  thresholds:
    - {max: 0.005, Q: 1.00}
    - {max: 0.01,  q: 0.90}
    - {max: 0.02,  q: 0.80}
    - {max: 0.03,  q: 0.75}
```

### Baselines

| Solver | alpha_crit_error | Q | Approx Reward |
|--------|-----------------|---|---------------|
| Spectral-ELITE | 0.01 | 0.96 | ~384 PWM |
| Shooting | 0.02 | 0.90 | ~360 PWM |
| FEM-variational | 0.028 | 0.82 | ~328 PWM |

### Layer 3 Reward

```
Benchmark seed reward = 100 x phi(t) x 0.60 = 60 PWM
```

---

## Layer 4: Benchmark -> Solution (PoSol Mining)

### Reward Calculation

```
R = 100 x 1.0 x 4 x 1.0 x q = 400 x q PWM
Best case:  400 x 0.96 = 384 PWM
Worst case: 400 x 0.75 = 300 PWM
```

### S4 Certificate

```json
{
  "principle": "#349 MHD Stability",
  "h_p": "sha256:<principle_349_hash>",
  "h_s": "sha256:<spec_349_hash>",
  "h_b": "sha256:<bench_349_hash>",
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"},
  "Q": 0.96,
  "difficulty": {"tier":"advanced","delta":4}
}
```

---

## Reward Summary

```
L1 Principle:  200 PWM seed + upstream royalties
L2 spec.md:    105 PWM seed (x4 scenarios = 420 PWM)
L3 Benchmark:   60 PWM seed (x4 benchmarks = 240 PWM)
L4 Solution:   300-384 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep mhd_stability
pwm-node verify AA_plasma_physics/mhd_stability_s1_ideal.yaml
pwm-node mine AA_plasma_physics/mhd_stability_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
