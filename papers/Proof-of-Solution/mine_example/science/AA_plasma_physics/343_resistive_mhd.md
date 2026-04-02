# Principle #343 — Resistive MHD: Four-Layer Walkthrough

**Principle #343: Resistive Magnetohydrodynamics**
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
dB/dt = curl(v x B) + eta * nabla^2(B)
rho(dv/dt) = -grad(p) + J x B + mu*nabla^2(v)
J = (1/mu0) curl(B)
Ohmic dissipation: eta |J|^2
```

### DAG Decomposition G = (V, A)

```
[∂.time] -> [N.bilinear.advection] -> [∂.space.curl] -> [N.pointwise]

V = {∂.time, N.bilinear.advection, ∂.space.curl, N.pointwise}
A = {∂.time->N.bilinear.advection, N.bilinear.advection->∂.space.curl, ∂.space.curl->N.pointwise}
L_DAG = 3.0   Tier: advanced (delta = 4)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- parabolic regularization from eta ensures smooth solutions |
| Uniqueness | YES -- dissipation selects unique solution |
| Stability | CONDITIONAL -- Lundquist number S = mu0*L*v_A/eta must be resolved |

Mismatch parameters: resistivity eta, Lundquist number S, viscosity mu

### Error-Bounding Method

```
e  = growth rate error vs analytic tearing mode prediction
q = 2.0 (second-order convergence)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Dimensions of B, v, J, eta consistent; Ohmic dissipation units correct | PASS |
| S2 | Parabolic system well-posed; eta > 0 ensures regularity | PASS |
| S3 | Implicit time-stepping and spectral methods converge | PASS |
| S4 | Growth rate error computable against analytic theory | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_343_hash>

omega:
  description: "Resistive tearing mode, Harris current sheet, Lx=2pi, Ly=pi"
  grid: [512, 256]
  outputs: [B_x, B_y, v_x, v_y, J_z]

E:
  forward: "dB/dt = curl(v x B) + eta * nabla^2(B)"
  dag: "[∂.time] -> [N.bilinear.advection] -> [∂.space.curl] -> [N.pointwise]"

I:
  scenario: ideal
  Lundquist_number: 1000
  perturbation: 1e-4
  mismatch: null

O: [growth_rate_error]

epsilon:
  gamma_err_max: 0.05

difficulty:
  L_DAG: 4.0
  tier: advanced
  delta: 4
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact eta | None | gamma_err < 5% |
| S2 Mismatch | Wrong eta | Applied | relaxed 1.5x |
| S3 Oracle | True eta known | Known | gamma_err < 5% |
| S4 Blind Cal | Estimate eta from data | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_343_hash>
principle_ref: sha256:<principle_343_hash>

dataset:
  description: "Harris sheet tearing mode at S=1000"
  resolutions: [128x64, 256x128, 512x256]
  data_hash: sha256:<dataset_343_hash>

baselines:
  - solver: Spectral            growth_rate_error: 0.02    q: 0.94
  - solver: FV-implicit         growth_rate_error: 0.035   q: 0.86
  - solver: FD-explicit         growth_rate_error: 0.048   q: 0.78

quality_scoring:
  metric: growth_rate_error
  thresholds:
    - {max: 0.01, Q: 1.00}
    - {max: 0.02, Q: 0.90}
    - {max: 0.04, Q: 0.80}
    - {max: 0.05, Q: 0.75}
```

### Baselines

| Solver | growth_rate_error | Q | Approx Reward |
|--------|------------------|---|---------------|
| Spectral | 0.02 | 0.94 | ~376 PWM |
| FV-implicit | 0.035 | 0.86 | ~344 PWM |
| FD-explicit | 0.048 | 0.78 | ~312 PWM |

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
| Spectral | 0.02 | moderate | 0.94 | ~376 PWM |
| FV-implicit | 0.035 | moderate | 0.86 | ~344 PWM |
| FD-explicit | 0.048 | moderate | 0.78 | ~312 PWM |

### Reward Calculation

```
R = 100 x 1.0 x 4 x 1.0 x q = 400 x q PWM
Best case:  400 x 0.94 = 376 PWM
Worst case: 400 x 0.75 = 300 PWM
```

### S4 Certificate

```json
{
  "principle": "#343 Resistive MHD",
  "h_p": "sha256:<principle_343_hash>",
  "h_s": "sha256:<spec_343_hash>",
  "h_b": "sha256:<bench_343_hash>",
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
pwm-node benchmarks | grep resistive_mhd
pwm-node verify AA_plasma_physics/resistive_mhd_s1_ideal.yaml
pwm-node mine AA_plasma_physics/resistive_mhd_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
