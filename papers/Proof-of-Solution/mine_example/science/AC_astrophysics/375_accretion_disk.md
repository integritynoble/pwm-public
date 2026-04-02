# Principle #375 — Black Hole Accretion Disk: Four-Layer Walkthrough

**Principle #375: Black Hole Accretion Disk**
Domain: Astrophysics & Cosmology | Carrier: electromagnetic/gravitational | Difficulty: hard (delta=5) | Reward: 5x base

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
∂(√-g ρu^μ)/∂x^μ = 0                    (mass conservation, GR)
∂T^μν/∂x^ν = 0                           (stress-energy conservation)
∂(√-g B^i)/∂t + ∂(√-g(B^iv^j - B^jv^i))/∂x^j = 0  (induction, ideal MHD)
∇·B = 0                                   (solenoidal constraint)
```

### DAG Decomposition G = (V, A)

```
[∂.time] -> [N.bilinear.advection] -> [∂.space]

V = {∂.time, N.bilinear.advection, ∂.space}
A = {∂.time->N.bilinear.advection, N.bilinear.advection->∂.space}
L_DAG = 2.0   Tier: hard (delta = 5)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- GRMHD equations admit solutions for smooth initial data |
| Uniqueness | CONDITIONAL -- turbulent MHD requires statistical convergence |
| Stability | CONDITIONAL -- MRI-driven turbulence; statistical steady state after saturation |

Mismatch parameters: spin a/M, accretion rate, magnetic field topology, electron thermodynamics

### Error-Bounding Method

```
e  = time-averaged accretion rate error (primary), jet power error (secondary)
q = 2.0 (second-order GRMHD convergence in smooth regions)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Metric coefficients consistent with Kerr; stress-energy tensor balanced | PASS |
| S2 | GRMHD well-posed in 3+1 ADM decomposition with divergence cleaning | PASS |
| S3 | HARM/iharm3d converge; turbulent statistics stabilize after ~5 orbits | PASS |
| S4 | Accretion rate reproducible to 10% across independent runs | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_375_hash>

omega:
  description: "Kerr BH accretion, a/M=0.9, MAD state, 2D axisymmetric"
  grid: [256, 256]
  spin: 0.9
  outputs: [accretion_rate, jet_power, SED]

E:
  forward: "GRMHD + ray-traced radiative transfer"
  dag: "[∂.time] -> [N.bilinear.advection] -> [∂.space]"

B:
  constraints: "∇·B=0; floor on density; r_in > r_horizon"

I:
  scenario: ideal
  initial_conditions: Fishbone-Moncrief torus + poloidal B field
  mismatch: null

O: [accretion_rate_error, jet_power_error]

epsilon:
  Mdot_err_max: 0.10
  convergence_order: 2.0

difficulty:
  L_DAG: 4.0
  tier: hard
  delta: 5
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known spin + FM torus | None | Mdot_err < 10% |
| S2 Mismatch | Wrong spin or B topology | Applied | relaxed 1.5x |
| S3 Oracle | True parameters known | Known | Mdot_err < 10% |
| S4 Blind Cal | Infer spin from image/SED | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_375_hash>
principle_ref: sha256:<principle_375_hash>

dataset:
  description: "GRMHD accretion simulations at multiple resolutions"
  resolutions: [128x128, 256x256, 512x256]
  data_hash: sha256:<dataset_375_hash>

baselines:
  - solver: iharm3d           Mdot_error: 0.05    q: 0.95
  - solver: HARM-2D           Mdot_error: 0.08    q: 0.88
  - solver: Zeus-GRMHD        Mdot_error: 0.12    q: 0.80

quality_scoring:
  metric: accretion_rate_error
  thresholds:
    - {max: 0.03, Q: 1.00}
    - {max: 0.06, Q: 0.90}
    - {max: 0.10, Q: 0.80}
    - {max: 0.15, Q: 0.75}
```

### Baselines

| Solver | Mdot_error | Q | Approx Reward |
|--------|-----------|---|---------------|
| iharm3d | 0.05 | 0.95 | ~475 PWM |
| HARM-2D | 0.08 | 0.88 | ~440 PWM |
| Zeus-GRMHD | 0.12 | 0.80 | ~400 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Grid resolutions match spec; initial torus parameters consistent | PASS |
| S2 | Problem well-posed: FM torus + MRI leads to quasi-steady accretion | PASS |
| S3 | iharm3d converges; time-averaged Mdot stable with resolution | PASS |
| S4 | Baseline meets threshold (Mdot_err < 10%); feasibility confirmed | PASS |

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
| iharm3d | 0.05 | ~2 hr | 0.95 | ~475 PWM |
| HARM-2D | 0.08 | ~30 min | 0.88 | ~440 PWM |
| Zeus-GRMHD | 0.12 | ~1 hr | 0.80 | ~400 PWM |

### Reward Calculation

```
R = R_base x phi(t) x delta x nu_c x q
  = 100 x 1.0 x 5 x 1.0 x q
  = 500 x q  PWM

Best case:  500 x 0.95 = 475 PWM
Worst case: 500 x 0.75 = 375 PWM
```

### S4 Certificate

```json
{
  "principle": "#375 Black Hole Accretion Disk",
  "h_p": "sha256:<principle_375_hash>",
  "h_s": "sha256:<spec_375_hash>",
  "h_b": "sha256:<bench_375_hash>",
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"},
  "Q": 0.95,
  "difficulty": {"tier":"hard","delta":5}
}
```

---

## Reward Summary

```
L1 Principle:  200 PWM seed + upstream royalties from L2/L3/L4
L2 spec.md:    105 PWM seed (x4 scenarios = 420 PWM) + upstream from L3/L4
L3 Benchmark:   60 PWM seed (x4 benchmarks = 240 PWM) + upstream from L4
L4 Solution:   375-475 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep accretion_disk
pwm-node verify AC_astrophysics/accretion_disk_s1_ideal.yaml
pwm-node mine AC_astrophysics/accretion_disk_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
