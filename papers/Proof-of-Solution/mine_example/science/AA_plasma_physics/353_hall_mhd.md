# Principle #353 — Hall MHD: Four-Layer Walkthrough

**Principle #353: Hall Magnetohydrodynamics**
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
dB/dt = curl((v - J/(n*e)) x B) + eta*nabla^2(B)
J = (1/mu0) curl(B)
Hall term: -(1/(n*e)) J x B  (adds whistler dispersion omega ~ k^2)
Ion inertial length: d_i = c/omega_pi
```

### DAG Decomposition G = (V, A)

```
[∂.time] -> [N.bilinear.advection] -> [∂.space.curl] -> [B.conducting]

V = {∂.time, N.bilinear.advection, ∂.space.curl, B.conducting}
A = {∂.time->N.bilinear.advection, N.bilinear.advection->∂.space.curl, ∂.space.curl->B.conducting}
L_DAG = 3.0   Tier: advanced (delta = 4)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- Hall term is a dispersive correction; solutions exist |
| Uniqueness | YES -- with appropriate boundary conditions |
| Stability | CONDITIONAL -- d_i/L ~ O(1) required; whistler CFL more restrictive |

Mismatch parameters: ion inertial length d_i, resistivity eta, guide field B_g

### Error-Bounding Method

```
e  = reconnection rate error vs GEM benchmark
q = 2.0 (second-order convergence)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Hall term dimensions consistent with MHD + J/(ne) correction | PASS |
| S2 | Hall MHD well-posed; dispersive regularization | PASS |
| S3 | Hall-MHD FV and spectral methods converge | PASS |
| S4 | Reconnection rate computable against GEM challenge results | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_353_hash>

omega:
  description: "GEM reconnection challenge, Harris current sheet"
  grid: [512, 256]
  outputs: [B_x, B_y, v_x, v_y, J_z, reconnection_rate]

E:
  forward: "dB/dt = curl((v - J/(ne)) x B) + eta*nabla^2(B)"
  dag: "[∂.time] -> [N.bilinear.advection] -> [∂.space.curl] -> [B.conducting]"

I:
  scenario: ideal
  d_i: 1.0
  eta: 0.005
  guide_field: 0.0
  mismatch: null

O: [reconnection_rate_error]

epsilon:
  rate_err_max: 0.05

difficulty:
  L_DAG: 4.0
  tier: advanced
  delta: 4
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact d_i, eta | None | rate_err < 5% |
| S2 Mismatch | Wrong d_i | Applied | relaxed 1.5x |
| S3 Oracle | True d_i known | Known | rate_err < 5% |
| S4 Blind Cal | Estimate d_i from current sheet width | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_353_hash>
principle_ref: sha256:<principle_353_hash>

dataset:
  description: "GEM reconnection challenge benchmark"
  data_hash: sha256:<dataset_353_hash>

baselines:
  - solver: HallMHD-FV         reconnection_rate_error: 0.025   q: 0.94
  - solver: Spectral-Hall       reconnection_rate_error: 0.035   q: 0.87
  - solver: Hybrid-PIC          reconnection_rate_error: 0.04    q: 0.80

quality_scoring:
  metric: reconnection_rate_error
  thresholds:
    - {max: 0.012, Q: 1.00}
    - {max: 0.025, Q: 0.90}
    - {max: 0.035, Q: 0.80}
    - {max: 0.050, Q: 0.75}
```

### Baselines

| Solver | reconnection_rate_error | Q | Approx Reward |
|--------|------------------------|---|---------------|
| HallMHD-FV | 0.025 | 0.94 | ~376 PWM |
| Spectral-Hall | 0.035 | 0.87 | ~348 PWM |
| Hybrid-PIC | 0.04 | 0.80 | ~320 PWM |

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
  "principle": "#353 Hall MHD",
  "h_p": "sha256:<principle_353_hash>",
  "h_s": "sha256:<spec_353_hash>",
  "h_b": "sha256:<bench_353_hash>",
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
pwm-node benchmarks | grep hall_mhd
pwm-node verify AA_plasma_physics/hall_mhd_s1_ideal.yaml
pwm-node mine AA_plasma_physics/hall_mhd_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
