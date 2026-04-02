# Principle #348 — Grad-Shafranov Equilibrium: Four-Layer Walkthrough

**Principle #348: Grad-Shafranov Equation**
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
Delta*(psi) = -mu0 * R * dp/dpsi - (1/2) * dF^2/dpsi
Delta* = R * d/dR(1/R * d/dR) + d^2/dZ^2   (Grad-Shafranov operator)
p(psi) = pressure profile
F(psi) = R * B_phi (toroidal field function)
```

### DAG Decomposition G = (V, A)

```
[∂.space.laplacian] -> [N.pointwise] -> [B.conducting]

V = {∂.space.laplacian, N.pointwise, B.conducting}
A = {∂.space.laplacian->N.pointwise, N.pointwise->B.conducting}
L_DAG = 2.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- nonlinear elliptic PDE with regular RHS admits solutions |
| Uniqueness | YES -- for given p(psi), F(psi) profiles and boundary conditions |
| Stability | CONDITIONAL -- Picard iteration convergent for moderate beta |

Mismatch parameters: pressure profile parameter, current profile parameter, elongation kappa, triangularity delta

### Error-Bounding Method

```
e  = L2 error in psi vs analytic Solov'ev solution
q = 2.0 (second-order FEM/FD convergence)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | GS operator dimensions consistent in (R,Z) coordinates | PASS |
| S2 | Elliptic PDE well-posed with Dirichlet boundary conditions | PASS |
| S3 | Newton-Krylov and Picard solvers converge | PASS |
| S4 | psi error computable against Solov'ev analytic solution | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_348_hash>

omega:
  description: "Solov'ev equilibrium, R0=1.0m, a=0.3m, kappa=1.7, delta=0.3"
  grid: [128, 128]   # (R, Z)
  outputs: [psi(R,Z), p(psi), F(psi), J_phi(R,Z)]

E:
  forward: "Delta*(psi) = -mu0*R*dp/dpsi - (1/2)*dF^2/dpsi"
  dag: "[∂.space.laplacian] -> [N.pointwise] -> [B.conducting]"

I:
  scenario: ideal
  R0: 1.0
  a: 0.3
  kappa: 1.7
  triangularity: 0.3
  mismatch: null

O: [psi_L2_error]

epsilon:
  psi_err_max: 1.0e-6

difficulty:
  L_DAG: 3.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact Solov'ev profiles | None | psi_err < 1e-6 |
| S2 Mismatch | Wrong pressure profile | Applied | relaxed 1.5x |
| S3 Oracle | True profiles known | Known | psi_err < 1e-6 |
| S4 Blind Cal | Estimate profiles from measurements | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_348_hash>
principle_ref: sha256:<principle_348_hash>

dataset:
  description: "Solov'ev equilibrium at multiple grid resolutions"
  data_hash: sha256:<dataset_348_hash>

baselines:
  - solver: Newton-Krylov       psi_L2_error: 5.0e-8    q: 0.98
  - solver: Picard              psi_L2_error: 1.0e-6    q: 0.90
  - solver: FD-SOR              psi_L2_error: 5.0e-6    q: 0.80

quality_scoring:
  metric: psi_L2_error
  thresholds:
    - {max: 1.0e-8, Q: 1.00}
    - {max: 1.0e-7, Q: 0.90}
    - {max: 5.0e-7, Q: 0.80}
    - {max: 1.0e-6, Q: 0.75}
```

### Baselines

| Solver | psi_L2_error | Q | Approx Reward |
|--------|-------------|---|---------------|
| Newton-Krylov | 5e-8 | 0.98 | ~294 PWM |
| Picard | 1e-6 | 0.90 | ~270 PWM |
| FD-SOR | 5e-6 | 0.80 | ~240 PWM |

### Layer 3 Reward

```
Benchmark seed reward = 100 x phi(t) x 0.60 = 60 PWM
```

---

## Layer 4: Benchmark -> Solution (PoSol Mining)

### Solver Table

| Solver | Expected Error | Time | Q | Reward |
|--------|---------------|------|---|--------|
| Newton-Krylov | 5e-8 | ~1 min | 0.98 | ~294 PWM |
| Picard | 1e-6 | ~3 min | 0.90 | ~270 PWM |
| FD-SOR | 5e-6 | ~5 min | 0.80 | ~240 PWM |

### Reward Calculation

```
R = 100 x 1.0 x 3 x 1.0 x q = 300 x q PWM
Best case:  300 x 0.98 = 294 PWM
Worst case: 300 x 0.75 = 225 PWM
```

### S4 Certificate

```json
{
  "principle": "#348 Grad-Shafranov",
  "h_p": "sha256:<principle_348_hash>",
  "h_s": "sha256:<spec_348_hash>",
  "h_b": "sha256:<bench_348_hash>",
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"},
  "Q": 0.98,
  "difficulty": {"tier":"standard","delta":3}
}
```

---

## Reward Summary

```
L1 Principle:  200 PWM seed + upstream royalties
L2 spec.md:    105 PWM seed (x4 scenarios = 420 PWM)
L3 Benchmark:   60 PWM seed (x4 benchmarks = 240 PWM)
L4 Solution:   225-294 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep grad_shafranov
pwm-node verify AA_plasma_physics/grad_shafranov_s1_ideal.yaml
pwm-node mine AA_plasma_physics/grad_shafranov_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
