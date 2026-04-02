# Principle #345 — Gyrokinetic Equation: Four-Layer Walkthrough

**Principle #345: Gyrokinetic Equation**
Domain: Plasma Physics | Carrier: electromagnetic | Difficulty: expert (delta=6) | Reward: 6x base

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
df/dt + v_par * b_hat * grad(f) + v_d * grad(f) + (q/m) * E_par * dv_par(f) = C[f]
Gyro-averaged fields: <phi>_alpha = (1/2pi) int phi(R + rho) d_alpha
Quasi-neutrality: sum_s q_s int <f_s> d^3v = 0
rho_i / L << 1 (gyro-ordering)
```

### DAG Decomposition G = (V, A)

```
[∂.time] -> [N.bilinear] -> [∂.space] -> [∫.volume]

V = {∂.time, N.bilinear, ∂.space, ∫.volume}
A = {∂.time->N.bilinear, N.bilinear->∂.space, ∂.space->∫.volume}
L_DAG = 3.0   Tier: expert (delta = 6)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- gyrokinetic ordering valid for rho_i/L << 1 |
| Uniqueness | YES -- under appropriate boundary conditions on flux tube |
| Stability | CONDITIONAL -- resolution must capture rho_i scale; collision operator must be conservative |

Mismatch parameters: temperature gradient R/L_T, density gradient R/L_n, safety factor q, magnetic shear s

### Error-Bounding Method

```
e  = ion heat flux error Q_i vs gradient-driven benchmark
q = 2.0 (convergence in rho* = rho_i / a)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Gyro-averaged fields dimensionally consistent with 5D phase space | PASS |
| S2 | Ordering parameter rho* << 1 maintained; quasi-neutrality satisfied | PASS |
| S3 | GS2, GENE codes converge for ITG benchmark | PASS |
| S4 | Heat flux Q_i computable and bounded | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_345_hash>

omega:
  description: "ITG turbulence, tokamak flux tube, rho*=1/150"
  grid: [64, 32, 16, 32, 8]   # (x, y, z, v_par, mu)
  outputs: [delta_f, phi, Q_i]

E:
  forward: "df/dt + v_par*b*grad(f) + v_d*grad(f) + (q/m)*E_par*dv_par(f) = C[f]"
  dag: "[∂.time] -> [N.bilinear] -> [∂.space] -> [∫.volume]"

I:
  scenario: ideal
  R_LT: 6.9
  R_Ln: 2.2
  q: 1.4
  magnetic_shear: 0.8
  mismatch: null

O: [Q_i_error]

epsilon:
  Q_err_max: 0.10

difficulty:
  L_DAG: 6.0
  tier: expert
  delta: 6
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact gradients | None | Q_err < 10% |
| S2 Mismatch | Wrong R/L_T | Applied | relaxed 1.5x |
| S3 Oracle | True gradients known | Known | Q_err < 10% |
| S4 Blind Cal | Estimate gradients from profiles | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_345_hash>
principle_ref: sha256:<principle_345_hash>

dataset:
  description: "Cyclone Base Case ITG benchmark"
  data_hash: sha256:<dataset_345_hash>

baselines:
  - solver: GENE              Q_i_error: 0.05    q: 0.94
  - solver: GS2               Q_i_error: 0.07    q: 0.88
  - solver: PIC-GK            Q_i_error: 0.09    q: 0.82

quality_scoring:
  metric: Q_i_error
  thresholds:
    - {max: 0.025, Q: 1.00}
    - {max: 0.05,  q: 0.90}
    - {max: 0.08,  q: 0.80}
    - {max: 0.10,  q: 0.75}
```

### Baselines

| Solver | Q_i_error | Q | Approx Reward |
|--------|----------|---|---------------|
| GENE | 0.05 | 0.94 | ~564 PWM |
| GS2 | 0.07 | 0.88 | ~528 PWM |
| PIC-GK | 0.09 | 0.82 | ~492 PWM |

### Layer 3 Reward

```
Benchmark seed reward = 100 x phi(t) x 0.60 = 60 PWM (builder)
```

---

## Layer 4: Benchmark -> Solution (PoSol Mining)

### Solver Table

| Solver | Expected Error | Time | Q | Reward |
|--------|---------------|------|---|--------|
| GENE | 0.05 | ~2 hr | 0.94 | ~564 PWM |
| GS2 | 0.07 | ~3 hr | 0.88 | ~528 PWM |
| PIC-GK | 0.09 | ~4 hr | 0.82 | ~492 PWM |

### Reward Calculation

```
R = 100 x 1.0 x 6 x 1.0 x q = 600 x q PWM
Best case:  600 x 0.94 = 564 PWM
Worst case: 600 x 0.75 = 450 PWM
```

### S4 Certificate

```json
{
  "principle": "#345 Gyrokinetic Equation",
  "h_p": "sha256:<principle_345_hash>",
  "h_s": "sha256:<spec_345_hash>",
  "h_b": "sha256:<bench_345_hash>",
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"},
  "Q": 0.94,
  "difficulty": {"tier":"expert","delta":6}
}
```

---

## Reward Summary

```
L1 Principle:  200 PWM seed + upstream royalties
L2 spec.md:    105 PWM seed (x4 scenarios = 420 PWM)
L3 Benchmark:   60 PWM seed (x4 benchmarks = 240 PWM)
L4 Solution:   450-564 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep gyrokinetic
pwm-node verify AA_plasma_physics/gyrokinetic_s1_ideal.yaml
pwm-node mine AA_plasma_physics/gyrokinetic_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
