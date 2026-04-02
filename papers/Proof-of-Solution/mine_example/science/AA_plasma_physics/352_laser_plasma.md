# Principle #352 — Laser-Plasma Interaction: Four-Layer Walkthrough

**Principle #352: Laser-Plasma Interaction**
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
PIC + Maxwell:
curl B = mu0*J + mu0*eps0*dE/dt
curl E = -dB/dt
F_i = q*(E(x_i) + v_i x B(x_i))
Wakefield: E_z ~ (m_e*c*omega_p/e) * a0 * sqrt(n_c/n_e)
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
| Existence | YES -- Maxwell + Newton well-posed for bounded fields |
| Uniqueness | YES -- deterministic PIC evolution |
| Stability | CONDITIONAL -- CFL: c*dt < dx; must resolve laser wavelength |

Mismatch parameters: normalized vector potential a0, density ratio n_e/n_c, pulse duration

### Error-Bounding Method

```
e  = peak accelerating field E_z error vs Lu formula
q = 2.0 (convergence in grid resolution)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Maxwell + particle push dimensionally consistent | PASS |
| S2 | CFL satisfiable; laser wavelength resolved | PASS |
| S3 | Explicit PIC (EPOCH, OSIRIS) converges | PASS |
| S4 | E_z computable against Lu wakefield scaling | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_352_hash>

omega:
  description: "LWFA, a0=2.0, n_e/n_c=0.01, lambda=0.8um"
  grid: [4096, 256]   # (x, y)
  outputs: [E_x(x,t), n_e(x,t), electron_spectrum]

E:
  forward: "Maxwell + PIC"
  dag: "[∂.time] -> [N.bilinear] -> [∂.space] -> [∫.volume]"

I:
  scenario: ideal
  a0: 2.0
  n_e_over_nc: 0.01
  lambda_um: 0.8
  mismatch: null

O: [E_z_peak_error]

epsilon:
  E_z_err_max: 0.10

difficulty:
  L_DAG: 5.0
  tier: advanced
  delta: 5
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact a0, n_e | None | E_z_err < 10% |
| S2 Mismatch | Wrong n_e profile | Applied | relaxed 1.5x |
| S3 Oracle | True n_e known | Known | E_z_err < 10% |
| S4 Blind Cal | Estimate n_e from interferometry | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_352_hash>
principle_ref: sha256:<principle_352_hash>

dataset:
  description: "LWFA benchmark at a0=2.0"
  data_hash: sha256:<dataset_352_hash>

baselines:
  - solver: Explicit-PIC        E_z_peak_error: 0.05    q: 0.94
  - solver: Envelope-PIC        E_z_peak_error: 0.08    q: 0.85
  - solver: Fluid-LWFA          E_z_peak_error: 0.12    q: 0.76

quality_scoring:
  metric: E_z_peak_error
  thresholds:
    - {max: 0.025, Q: 1.00}
    - {max: 0.05,  q: 0.90}
    - {max: 0.08,  q: 0.80}
    - {max: 0.10,  q: 0.75}
```

### Baselines

| Solver | E_z_peak_error | Q | Approx Reward |
|--------|---------------|---|---------------|
| Explicit-PIC | 0.05 | 0.94 | ~470 PWM |
| Envelope-PIC | 0.08 | 0.85 | ~425 PWM |
| Fluid-LWFA | 0.12 | 0.76 | ~380 PWM |

### Layer 3 Reward

```
Benchmark seed reward = 100 x phi(t) x 0.60 = 60 PWM
```

---

## Layer 4: Benchmark -> Solution (PoSol Mining)

### Reward Calculation

```
R = 100 x 1.0 x 5 x 1.0 x q = 500 x q PWM
Best case:  500 x 0.94 = 470 PWM
Worst case: 500 x 0.75 = 375 PWM
```

### S4 Certificate

```json
{
  "principle": "#352 Laser-Plasma Interaction",
  "h_p": "sha256:<principle_352_hash>",
  "h_s": "sha256:<spec_352_hash>",
  "h_b": "sha256:<bench_352_hash>",
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"},
  "Q": 0.94,
  "difficulty": {"tier":"advanced","delta":5}
}
```

---

## Reward Summary

```
L1 Principle:  200 PWM seed + upstream royalties
L2 spec.md:    105 PWM seed (x4 scenarios = 420 PWM)
L3 Benchmark:   60 PWM seed (x4 benchmarks = 240 PWM)
L4 Solution:   375-470 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep laser_plasma
pwm-node verify AA_plasma_physics/laser_plasma_s1_ideal.yaml
pwm-node mine AA_plasma_physics/laser_plasma_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
