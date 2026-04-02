# Principle #364 — N-Body Gravitational Simulation: Four-Layer Walkthrough

**Principle #364: N-Body Gravitational Simulation**
Domain: Astrophysics & Cosmology | Carrier: gravitational | Difficulty: standard (delta=3) | Reward: 3x base

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
d²r_i/dt² = -G Σ_{j≠i} m_j (r_i - r_j) / |r_i - r_j|³
F_ij = -G m_i m_j / |r_i - r_j|²  (pairwise gravitational force)
Total energy E = T + V  (kinetic + potential, conserved)
```

### DAG Decomposition G = (V, A)

```
[N.bilinear.pair] -> [∂.time.symplectic]

V = {N.bilinear.pair, ∂.time.symplectic}
A = {N.bilinear.pair->∂.time.symplectic}
L_DAG = 1.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- smooth solutions exist for non-colliding configurations |
| Uniqueness | YES -- Lipschitz continuous RHS away from close encounters |
| Stability | CONDITIONAL -- softening parameter prevents singularities; symplectic integrators conserve energy |

Mismatch parameters: softening length epsilon, opening angle theta (tree code), time-step eta

### Error-Bounding Method

```
e  = relative energy error |dE/E| (primary), position RMS error (secondary)
q = 2.0 (leapfrog) or 4.0 (Hermite integrator)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Force dimensions [M L T⁻²] consistent; gravitational constant G units match | PASS |
| S2 | Softened potential bounded; symplectic integrator preserves phase-space volume | PASS |
| S3 | Leapfrog/Hermite converges with adaptive time-stepping | PASS |
| S4 | Energy conservation |dE/E| < 1e-6 achievable for N < 10⁴ | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_364_hash>

omega:
  description: "Plummer sphere, N=1024, t_final=10 crossing times"
  N_particles: 1024
  outputs: [positions, velocities, energy]

E:
  forward: "d²r_i/dt² = -G Σ m_j (r_i-r_j)/|r_i-r_j|³"
  dag: "[N.bilinear.pair] -> [∂.time.symplectic]"

B:
  constraints: "total energy conserved; center of mass fixed; softening epsilon=0.01"

I:
  scenario: ideal
  initial_conditions:
    model: Plummer
    N: 1024
    virial_ratio: 0.5
  mismatch: null

O: [energy_error, position_rms]

epsilon:
  energy_err_max: 1.0e-6
  convergence_order: 2.0

difficulty:
  L_DAG: 2.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Direct summation | None | energy_err < 1e-6 |
| S2 Mismatch | Wrong softening or theta | Applied | relaxed 1.5x |
| S3 Oracle | True params known | Known | energy_err < 1e-6 |
| S4 Blind Cal | Estimate optimal dt from data | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_364_hash>
principle_ref: sha256:<principle_364_hash>

dataset:
  description: "Plummer sphere N-body at multiple particle counts"
  N_values: [256, 512, 1024, 4096]
  data_hash: sha256:<dataset_364_hash>

baselines:
  - solver: Hermite-4th       energy_error: 2.0e-8    q: 0.95
  - solver: Leapfrog          energy_error: 5.0e-7    q: 0.88
  - solver: Barnes-Hut        energy_error: 1.0e-5    q: 0.80

quality_scoring:
  metric: energy_error
  thresholds:
    - {max: 1.0e-8, Q: 1.00}
    - {max: 1.0e-7, Q: 0.90}
    - {max: 1.0e-6, Q: 0.80}
    - {max: 1.0e-5, Q: 0.75}
```

### Baselines

| Solver | energy_error | Q | Approx Reward |
|--------|-------------|---|---------------|
| Hermite-4th | 2.0e-8 | 0.95 | ~285 PWM |
| Leapfrog | 5.0e-7 | 0.88 | ~264 PWM |
| Barnes-Hut | 1.0e-5 | 0.80 | ~240 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Particle counts match spec; initial conditions consistent with Plummer model | PASS |
| S2 | Problem well-posed: Plummer sphere has known virial equilibrium | PASS |
| S3 | Hermite integrator converges; energy error decreases with smaller dt | PASS |
| S4 | Baseline meets threshold (energy_err < 1e-6); feasibility confirmed | PASS |

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
| Hermite-4th | 2.0e-8 | ~5 min | 0.95 | ~285 PWM |
| Leapfrog | 5.0e-7 | ~2 min | 0.88 | ~264 PWM |
| Barnes-Hut | 1.0e-5 | ~1 min | 0.80 | ~240 PWM |

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
  "principle": "#364 N-Body Gravitational Simulation",
  "h_p": "sha256:<principle_364_hash>",
  "h_s": "sha256:<spec_364_hash>",
  "h_b": "sha256:<bench_364_hash>",
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
pwm-node benchmarks | grep nbody_gravitational
pwm-node verify AC_astrophysics/nbody_gravitational_s1_ideal.yaml
pwm-node mine AC_astrophysics/nbody_gravitational_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
