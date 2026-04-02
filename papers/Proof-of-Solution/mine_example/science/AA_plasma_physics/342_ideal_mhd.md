# Principle #342 — Ideal MHD: Four-Layer Walkthrough

**Principle #342: Ideal Magnetohydrodynamics**
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
rho(dv/dt) = -grad(p) + (1/mu0)(curl B) x B
dB/dt = curl(v x B)
drho/dt + div(rho*v) = 0
dp/dt + gamma*qdiv(v) = 0
div(B) = 0
```

### DAG Decomposition G = (V, A)

```
[∂.time] -> [N.bilinear.advection] -> [∂.space.curl] -> [B.conducting]

V = {∂.time, N.bilinear.advection, ∂.space.curl, B.conducting}
A = {∂.time->N.bilinear.advection, N.bilinear.advection->∂.space.curl, ∂.space.curl->B.conducting}
L_DAG = 3.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- hyperbolic system admits classical solutions for smooth initial data |
| Uniqueness | YES -- Lax entropy conditions select unique weak solutions at shocks |
| Stability | CONDITIONAL -- CFL condition; div(B)=0 constraint must be maintained |

Mismatch parameters: resistivity eta (ideal=0 vs small perturbation), adiabatic index gamma, numerical diffusivity

### Error-Bounding Method

```
e  = L2 density error (primary), L1 errors in B and v (secondary)
q = 2.0 (second-order convergence for smooth regions)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Dimensions of rho, v, B, p consistent across MHD equations; units balance | PASS |
| S2 | Hyperbolic system well-posed with Lax conditions; div(B)=0 maintained | PASS |
| S3 | Convergent solvers (HLLD, Roe, Godunov) exist with known CFL bounds | PASS |
| S4 | L2 density error computable against exact Riemann solutions | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_342_hash>

omega:
  description: "Brio-Wu shock tube, 1D domain [0,1], t_final=0.1"
  grid: [1024]
  outputs: [rho, v_x, v_y, B_y, p]

E:
  forward: "rho(dv/dt) = -grad(p) + (1/mu0)(curl B) x B"
  dag: "[∂.time] -> [N.bilinear.advection] -> [∂.space.curl] -> [B.conducting]"

B:
  constraints: "div(B)=0; rho>0; p>0; frozen-in flux"

I:
  scenario: ideal
  initial_conditions:
    left:  {rho: 1.0, p: 1.0, B_y: 1.0}
    right: {rho: 0.125, p: 0.1, B_y: -1.0}
  mismatch: null

O: [L2_density_error, L1_B_error]

epsilon:
  rho_err_max: 0.02
  convergence_order: 1.5

difficulty:
  L_DAG: 3.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact Riemann solver | None | rho_err < 0.02 |
| S2 Mismatch | Wrong gamma or resistivity | Applied | relaxed 1.5x |
| S3 Oracle | True params known | Known | rho_err < 0.02 |
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
spec_ref: sha256:<spec_342_hash>
principle_ref: sha256:<principle_342_hash>

dataset:
  description: "Brio-Wu MHD shock tube at multiple resolutions"
  resolutions: [128, 256, 512, 1024]
  data_hash: sha256:<dataset_342_hash>

baselines:
  - solver: HLLD               L2_density_error: 0.008    q: 0.95
  - solver: Roe                L2_density_error: 0.012    q: 0.88
  - solver: Godunov            L2_density_error: 0.018    q: 0.80

quality_scoring:
  metric: L2_density_error
  thresholds:
    - {max: 0.004, Q: 1.00}
    - {max: 0.008, Q: 0.90}
    - {max: 0.015, Q: 0.80}
    - {max: 0.020, Q: 0.75}
```

### Baselines

| Solver | L2_density_error | Q | Approx Reward |
|--------|-----------------|---|---------------|
| HLLD | 0.008 | 0.95 | ~285 PWM |
| Roe | 0.012 | 0.88 | ~264 PWM |
| Godunov | 0.018 | 0.80 | ~240 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Dataset dimensions match spec grid; initial conditions consistent | PASS |
| S2 | Problem well-posed: Brio-Wu has known exact solution | PASS |
| S3 | HLLD converges; residual decreases monotonically | PASS |
| S4 | Baseline meets threshold (rho_err < 0.02); feasibility confirmed | PASS |

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
| HLLD | 0.008 | ~2 min | 0.95 | ~285 PWM |
| Roe | 0.012 | ~3 min | 0.88 | ~264 PWM |
| Godunov | 0.018 | ~5 min | 0.80 | ~240 PWM |

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
  "principle": "#342 Ideal MHD",
  "h_p": "sha256:<principle_342_hash>",
  "h_s": "sha256:<spec_342_hash>",
  "h_b": "sha256:<bench_342_hash>",
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
pwm-node benchmarks | grep ideal_mhd
pwm-node verify AA_plasma_physics/ideal_mhd_s1_ideal.yaml
pwm-node mine AA_plasma_physics/ideal_mhd_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
