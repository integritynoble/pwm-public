# Principle #402 — Pharmacokinetics (Compartmental ODE)

**Domain:** Computational Biology | **Carrier:** drug concentration | **Difficulty:** Standard (δ=3)
**DAG:** N.reaction → ∂.time.implicit |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.reaction→∂.time.implicit      PK-compart   2-compartment    ODE-solver
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PHARMACOKINETICS (COMPARTMENT) P = (E,G,W,C)   Principle #402  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ dC₁/dt = −(k₁₂ + k_el)C₁ + k₂₁ C₂ + D(t)/V₁        │
│        │ dC₂/dt = k₁₂ C₁ − k₂₁ C₂                            │
│        │ C₁ = central compartment conc., C₂ = peripheral       │
│        │ k_el = elimination rate, V₁ = central volume           │
│        │ Forward: given dose D(t), PK params → C(t) profile    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.reaction] ──→ [∂.time.implicit]                     │
│        │ nonlinear  derivative                                  │
│        │ V={N.reaction, ∂.time.implicit}  A={N.reaction→∂.time.implicit}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear ODE system, bounded coefficients)│
│        │ Uniqueness: YES (matrix exponential well-defined)      │
│        │ Stability: YES (eigenvalues of rate matrix are negative)│
│        │ Mismatch: inter-patient variability, nonlinear metabolism│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative error ‖C−C_ref‖/‖C_ref‖                  │
│        │ q = 2.0 (trapezoid), 4.0 (RK4)                      │
│        │ T = {C_error, AUC_error, Cmax_error, t_half_error}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Concentration, volume, rate constant dimensions consistent | PASS |
| S2 | Linear ODE — analytic bi-exponential solution exists | PASS |
| S3 | Any ODE solver converges; matrix exponential exact | PASS |
| S4 | Concentration error computable against analytic solution | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# pharmacokinetics/two_compartment_s1_ideal.yaml
principle_ref: sha256:<p402_hash>
omega:
  time: [0, 24.0]   # hours
  dt: 0.01   # hours
  compartments: 2
E:
  forward: "dC/dt = A·C + D(t)/V (linear compartmental)"
  k12: 1.5   # h⁻¹
  k21: 0.8   # h⁻¹
  k_el: 0.3   # h⁻¹
  V1: 10.0   # L
B:
  initial: {C1_0: 0.0, C2_0: 0.0}
I:
  scenario: IV_bolus
  dose: 100   # mg at t=0
  dt_sizes: [0.1, 0.01, 0.001]
O: [C_L2_error, AUC_error, Cmax_error]
epsilon:
  C_error_max: 1.0e-6
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | dt=0.01 h resolves distribution phase (~0.5 h half-life) | PASS |
| S2 | IV bolus into 2-compartment — analytic bi-exponential exists | PASS |
| S3 | RK4 at dt=0.01 converges to machine precision | PASS |
| S4 | C error < 10⁻⁶ achievable at dt=0.001 h | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# pharmacokinetics/benchmark_iv_bolus.yaml
spec_ref: sha256:<spec402_hash>
principle_ref: sha256:<p402_hash>
dataset:
  name: PK_analytic_2comp
  reference: "Analytic bi-exponential solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Forward-Euler
    params: {dt: 0.01}
    results: {C_error: 5.0e-4, AUC_err: 1.2e-3}
  - solver: Trapezoid
    params: {dt: 0.01}
    results: {C_error: 8.5e-6, AUC_err: 2.0e-5}
  - solver: Matrix-exponential
    params: {dt: 0.1}
    results: {C_error: 1.0e-14, AUC_err: 1.0e-14}
quality_scoring:
  - {min_C_err: 1.0e-10, Q: 1.00}
  - {min_C_err: 1.0e-6, Q: 0.90}
  - {min_C_err: 1.0e-4, Q: 0.80}
  - {min_C_err: 1.0e-3, Q: 0.75}
```

**Baseline solver:** Trapezoid — C error 8.5×10⁻⁶
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | C L2 Error | AUC Error | Runtime | Q |
|--------|-----------|----------|---------|---|
| Forward-Euler | 5.0e-4 | 1.2e-3 | 0.001 s | 0.80 |
| Trapezoid | 8.5e-6 | 2.0e-5 | 0.001 s | 0.90 |
| Matrix-exp | 1.0e-14 | 1.0e-14 | 0.001 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (matrix-exp): 300 × 1.00 = 300 PWM
Floor:                  300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p402_hash>",
  "h_s": "sha256:<spec402_hash>",
  "h_b": "sha256:<bench402_hash>",
  "r": {"C_error": 1.0e-14, "AUC_err": 1.0e-14, "ratio": 0.0},
  "c": {"fitted_rate": 2.00, "theoretical_rate": 2.0, "K": 3},
  "Q": 1.00,
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"}
}
```

---

## Reward Summary

| Layer | Seed Reward | Ongoing Royalties |
|-------|-------------|-------------------|
| L1 Principle | 200 PWM | 5% of L4 mints |
| L2 spec.md | 105 PWM | 10% of L4 mints |
| L3 Benchmark | 60 PWM | 15% of L4 mints |
| L4 Solution | — | 225–300 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep pharmacokinetics
pwm-node verify AE_computational_biology/pharmacokinetics_s1_ideal.yaml
pwm-node mine AE_computational_biology/pharmacokinetics_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
