# Principle #376 — Cosmic Ray Propagation: Four-Layer Walkthrough

**Principle #376: Cosmic Ray Propagation**
Domain: Astrophysics & Cosmology | Carrier: particle | Difficulty: standard (delta=3) | Reward: 3x base

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
∂ψ/∂t = ∇·(D∇ψ) - ∇·(vψ) + Q(r,E) - ψ/τ_f - ∂(bψ)/∂E
ψ(r,E,t): cosmic ray density per unit energy
D(E): energy-dependent diffusion coefficient
b(E) = -dE/dt: energy loss rate (synchrotron, IC, ionization)
τ_f: fragmentation/spallation lifetime
```

### DAG Decomposition G = (V, A)

```
[∂.time] -> [K.scatter.nuclear] -> [∂.space]

V = {∂.time, K.scatter.nuclear, ∂.space}
A = {∂.time->K.scatter.nuclear, K.scatter.nuclear->∂.space}
L_DAG = 2.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- diffusion-loss equation has Green's function solutions |
| Uniqueness | YES -- unique for given source distribution and transport parameters |
| Stability | YES -- parabolic PDE; smooth dependence on D, b, Q |

Mismatch parameters: diffusion coefficient D₀, spectral index δ, halo height L, source distribution

### Error-Bounding Method

```
e  = B/C ratio error (primary), proton spectrum error (secondary)
q = 2.0 (Crank-Nicolson convergence)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Diffusion [cm²/s], energy [GeV], density [cm⁻³ GeV⁻¹] units consistent | PASS |
| S2 | Diffusion-loss equation well-posed with boundary conditions | PASS |
| S3 | GALPROP/DRAGON converge; B/C ratio stable with spatial resolution | PASS |
| S4 | B/C ratio match to AMS-02 data within 5% achievable | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_376_hash>

omega:
  description: "Galactic CR propagation, cylindrical halo, E=[1,1000] GeV"
  grid: [100, 100, 50]
  energy_bins: 100
  outputs: [proton_spectrum, BC_ratio, antiproton_flux]

E:
  forward: "∂ψ/∂t = ∇·(D∇ψ) - ∇·(vψ) + Q - ψ/τ - ∂(bψ)/∂E"
  dag: "[∂.time] -> [K.scatter.nuclear] -> [∂.space]"

B:
  constraints: "ψ=0 at halo boundary; ψ≥0; steady state"

I:
  scenario: ideal
  parameters: {D0: 5.0e28, delta: 0.4, L_kpc: 4.0, v_A: 30}
  mismatch: null

O: [BC_ratio_error, proton_spectrum_error]

epsilon:
  BC_err_max: 0.05
  convergence_order: 2.0

difficulty:
  L_DAG: 3.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known transport parameters | None | BC_err < 5% |
| S2 Mismatch | Wrong D₀ or halo height | Applied | relaxed 1.5x |
| S3 Oracle | True parameters known | Known | BC_err < 5% |
| S4 Blind Cal | Fit transport from B/C data | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_376_hash>
principle_ref: sha256:<principle_376_hash>

dataset:
  description: "AMS-02 CR spectra and secondary-to-primary ratios"
  species: [proton, helium, B/C, antiproton]
  data_hash: sha256:<dataset_376_hash>

baselines:
  - solver: GALPROP            BC_error: 0.03    q: 0.95
  - solver: DRAGON             BC_error: 0.04    q: 0.90
  - solver: Leaky-box          BC_error: 0.10    q: 0.78

quality_scoring:
  metric: BC_ratio_error
  thresholds:
    - {max: 0.02, Q: 1.00}
    - {max: 0.04, Q: 0.90}
    - {max: 0.06, Q: 0.80}
    - {max: 0.10, Q: 0.75}
```

### Baselines

| Solver | BC_error | Q | Approx Reward |
|--------|---------|---|---------------|
| GALPROP | 0.03 | 0.95 | ~285 PWM |
| DRAGON | 0.04 | 0.90 | ~270 PWM |
| Leaky-box | 0.10 | 0.78 | ~234 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Energy range and species match spec; data format consistent | PASS |
| S2 | Problem well-posed: steady-state solution exists for bounded halo | PASS |
| S3 | GALPROP converges; B/C stable with grid refinement | PASS |
| S4 | Baseline meets threshold (BC_err < 5%); feasibility confirmed | PASS |

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
| GALPROP | 0.03 | ~10 min | 0.95 | ~285 PWM |
| DRAGON | 0.04 | ~8 min | 0.90 | ~270 PWM |
| Leaky-box | 0.10 | ~10 s | 0.78 | ~234 PWM |

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
  "principle": "#376 Cosmic Ray Propagation",
  "h_p": "sha256:<principle_376_hash>",
  "h_s": "sha256:<spec_376_hash>",
  "h_b": "sha256:<bench_376_hash>",
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
pwm-node benchmarks | grep cosmic_ray
pwm-node verify AC_astrophysics/cosmic_ray_s1_ideal.yaml
pwm-node mine AC_astrophysics/cosmic_ray_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
