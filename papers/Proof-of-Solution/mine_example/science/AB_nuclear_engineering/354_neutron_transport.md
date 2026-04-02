# Principle #354 — Neutron Transport: Four-Layer Walkthrough

**Principle #354: Neutron Transport (Boltzmann)**
Domain: Nuclear Engineering | Carrier: neutron | Difficulty: advanced (delta=5) | Reward: 5x base

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
Omega*grad(psi) + Sigma_t*psi = int Sigma_s(Omega'->Omega,E'->E)*psi dOmega' dE'
                                + (chi(E)/(4*pi*k)) int nu*Sigma_f*psi dOmega' dE'
                                + Q_ext
psi(r, Omega, E) = angular neutron flux
Sigma_t, Sigma_s, Sigma_f = total, scattering, fission cross-sections
```

### DAG Decomposition G = (V, A)

```
[∂.angular] -> [K.scatter.nuclear] -> [∫.angular] -> [N.reaction.fission]

V = {∂.angular, K.scatter.nuclear, ∫.angular, N.reaction.fission}
A = {∂.angular->K.scatter.nuclear, K.scatter.nuclear->∫.angular, ∫.angular->N.reaction.fission}
L_DAG = 3.0   Tier: advanced (delta = 5)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- linear Boltzmann equation with bounded cross-sections |
| Uniqueness | YES -- for subcritical systems with given source; eigenvalue for critical |
| Stability | CONDITIONAL -- ray effects in S_N; convergence of source iteration |

Mismatch parameters: cross-section library version, energy group structure, scattering anisotropy order

### Error-Bounding Method

```
e  = scalar flux error vs reference Monte Carlo
q = 2.0 (S_N spatial convergence)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Angular flux dimensions (r, Omega, E) consistent with cross-sections | PASS |
| S2 | Subcritical transport well-posed; critical eigenvalue exists | PASS |
| S3 | S_N discrete ordinates and Monte Carlo converge | PASS |
| S4 | Scalar flux error computable against MCNP reference | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_354_hash>

omega:
  description: "Kobayashi 3D benchmark, fixed source, void+scatterer"
  grid: [100, 100, 100]
  energy_groups: 1
  S_N_order: 8
  outputs: [scalar_flux(r), dose_rate(r)]

E:
  forward: "Omega*grad(psi) + Sigma_t*psi = Sigma_s*phi/(4pi) + Q"
  dag: "[∂.angular] -> [K.scatter.nuclear] -> [∫.angular] -> [N.reaction.fission]"

I:
  scenario: ideal
  cross_sections: ENDF-VIII.0
  mismatch: null

O: [scalar_flux_error]

epsilon:
  flux_err_max: 0.05

difficulty:
  L_DAG: 5.0
  tier: advanced
  delta: 5
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact cross-sections | None | flux_err < 5% |
| S2 Mismatch | Wrong cross-section library | Applied | relaxed 1.5x |
| S3 Oracle | True cross-sections known | Known | flux_err < 5% |
| S4 Blind Cal | Estimate cross-sections from measurements | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_354_hash>
principle_ref: sha256:<principle_354_hash>

dataset:
  description: "Kobayashi 3D transport benchmark"
  data_hash: sha256:<dataset_354_hash>

baselines:
  - solver: S_N-diamond         scalar_flux_error: 0.025   q: 0.94
  - solver: S_N-LDFE            scalar_flux_error: 0.035   q: 0.87
  - solver: Monte-Carlo         scalar_flux_error: 0.015   q: 0.97

quality_scoring:
  metric: scalar_flux_error
  thresholds:
    - {max: 0.01, Q: 1.00}
    - {max: 0.025, Q: 0.90}
    - {max: 0.04, Q: 0.80}
    - {max: 0.05, Q: 0.75}
```

### Baselines

| Solver | scalar_flux_error | Q | Approx Reward |
|--------|------------------|---|---------------|
| Monte-Carlo | 0.015 | 0.97 | ~485 PWM |
| S_N-diamond | 0.025 | 0.94 | ~470 PWM |
| S_N-LDFE | 0.035 | 0.87 | ~435 PWM |

### Layer 3 Reward

```
Benchmark seed reward = 100 x phi(t) x 0.60 = 60 PWM
```

---

## Layer 4: Benchmark -> Solution (PoSol Mining)

### Reward Calculation

```
R = 100 x 1.0 x 5 x 1.0 x q = 500 x q PWM
Best case:  500 x 0.97 = 485 PWM
Worst case: 500 x 0.75 = 375 PWM
```

### S4 Certificate

```json
{
  "principle": "#354 Neutron Transport",
  "h_p": "sha256:<principle_354_hash>",
  "h_s": "sha256:<spec_354_hash>",
  "h_b": "sha256:<bench_354_hash>",
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
L4 Solution:   375-485 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep neutron_transport
pwm-node verify AB_nuclear_engineering/neutron_transport_s1_ideal.yaml
pwm-node mine AB_nuclear_engineering/neutron_transport_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
