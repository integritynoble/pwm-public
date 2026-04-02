# Principle #344 — Vlasov Equation: Four-Layer Walkthrough

**Principle #344: Vlasov-Poisson / Vlasov-Maxwell**
Domain: Plasma Physics | Carrier: electromagnetic | Difficulty: advanced (delta=5) | Reward: 5x base

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
df/dt + v * grad_x(f) + (q/m)(E + v x B) * grad_v(f) = 0
Poisson: nabla^2(phi) = -rho/eps0 = -(q/eps0) int f dv
Self-consistent: E = -grad(phi)
```

### DAG Decomposition G = (V, A)

```
[∂.time] -> [N.bilinear] -> [∂.space] -> [∫.volume]

V = {∂.time, N.bilinear, ∂.space, ∫.volume}
A = {∂.time->N.bilinear, N.bilinear->∂.space, ∂.space->∫.volume}
L_DAG = 3.0   Tier: advanced (delta = 5)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- Vlasov-Poisson has global classical solutions in 1D |
| Uniqueness | YES -- characteristics do not cross for smooth f |
| Stability | CONDITIONAL -- phase-space resolution must capture filamentation |

Mismatch parameters: wavenumber k, perturbation amplitude eps, thermal velocity v_th

### Error-Bounding Method

```
e  = Landau damping rate error vs analytic theory
q = 2.0 (spectral convergence for smooth distributions)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Phase-space f(x,v) dimensions consistent with Poisson coupling | PASS |
| S2 | Vlasov-Poisson well-posed; characteristics well-defined | PASS |
| S3 | Semi-Lagrangian and spectral solvers converge | PASS |
| S4 | Damping rate computable against Landau's analytic result | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_344_hash>

omega:
  description: "Landau damping: 1D1V, k=0.5, eps=0.01, L=4*pi"
  grid: [256, 512]   # x: 256, v: 512
  outputs: [f(x,v,t), E(x,t), damping_rate]

E:
  forward: "df/dt + v*grad_x(f) + (q/m)*E*grad_v(f) = 0"
  dag: "[∂.time] -> [N.bilinear] -> [∂.space] -> [∫.volume]"

I:
  scenario: ideal
  k: 0.5
  epsilon: 0.01
  v_range: [-6, 6]
  mismatch: null

O: [damping_rate_error]

epsilon:
  gamma_err_max: 0.02

difficulty:
  L_DAG: 5.0
  tier: advanced
  delta: 5
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact k, eps | None | gamma_err < 2% |
| S2 Mismatch | Wrong k or v_th | Applied | relaxed 1.5x |
| S3 Oracle | True params known | Known | gamma_err < 2% |
| S4 Blind Cal | Estimate k from data | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_344_hash>
principle_ref: sha256:<principle_344_hash>

dataset:
  description: "Landau damping at k=0.5, multiple phase-space resolutions"
  data_hash: sha256:<dataset_344_hash>

baselines:
  - solver: Semi-Lagrangian     damping_rate_error: 0.008   q: 0.96
  - solver: Spectral            damping_rate_error: 0.012   q: 0.90
  - solver: DG                  damping_rate_error: 0.015   q: 0.85

quality_scoring:
  metric: damping_rate_error
  thresholds:
    - {max: 0.004, Q: 1.00}
    - {max: 0.008, Q: 0.90}
    - {max: 0.015, Q: 0.80}
    - {max: 0.020, Q: 0.75}
```

### Baselines

| Solver | damping_rate_error | Q | Approx Reward |
|--------|-------------------|---|---------------|
| Semi-Lagrangian | 0.008 | 0.96 | ~480 PWM |
| Spectral | 0.012 | 0.90 | ~450 PWM |
| DG | 0.015 | 0.85 | ~425 PWM |

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
| Semi-Lagrangian | 0.008 | ~10 min | 0.96 | ~480 PWM |
| Spectral | 0.012 | ~8 min | 0.90 | ~450 PWM |
| DG | 0.015 | ~15 min | 0.85 | ~425 PWM |

### Reward Calculation

```
R = 100 x 1.0 x 5 x 1.0 x q = 500 x q PWM
Best case:  500 x 0.96 = 480 PWM
Worst case: 500 x 0.75 = 375 PWM
```

### S4 Certificate

```json
{
  "principle": "#344 Vlasov Equation",
  "h_p": "sha256:<principle_344_hash>",
  "h_s": "sha256:<spec_344_hash>",
  "h_b": "sha256:<bench_344_hash>",
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"},
  "Q": 0.96,
  "difficulty": {"tier":"advanced","delta":5}
}
```

---

## Reward Summary

```
L1 Principle:  200 PWM seed + upstream royalties
L2 spec.md:    105 PWM seed (x4 scenarios = 420 PWM)
L3 Benchmark:   60 PWM seed (x4 benchmarks = 240 PWM)
L4 Solution:   375-480 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep vlasov
pwm-node verify AA_plasma_physics/vlasov_s1_ideal.yaml
pwm-node mine AA_plasma_physics/vlasov_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
