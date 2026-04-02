# Principle #405 — SIR Epidemic Model

**Domain:** Computational Biology | **Carrier:** population fractions | **Difficulty:** Introductory (δ=2)
**DAG:** N.reaction.sir → ∂.time |  **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.reaction.sir→∂.time        SIR-model    outbreak-curve    ODE
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SIR EPIDEMIC MODEL             P = (E,G,W,C)   Principle #405  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ dS/dt = −β S I / N                                    │
│        │ dI/dt = β S I / N − γ I                               │
│        │ dR/dt = γ I                                            │
│        │ S+I+R = N (conserved), R₀ = β/γ                      │
│        │ Forward: given β, γ, S(0), I(0) → S(t), I(t), R(t)  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.reaction.sir] ──→ [∂.time]                          │
│        │ nonlinear  derivative                                  │
│        │ V={N.reaction.sir, ∂.time}  A={N.reaction.sir→∂.time}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (smooth ODE, positive invariant set)    │
│        │ Uniqueness: YES (Lipschitz on compact domain)          │
│        │ Stability: disease-free equilibrium stable iff R₀ < 1  │
│        │ Mismatch: time-varying β, heterogeneous mixing         │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative error ‖I−I_ref‖/‖I_ref‖                  │
│        │ q = 4.0 (RK4), 2.0 (trapezoid)                      │
│        │ T = {I_error, peak_time_error, final_size_error}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | S+I+R=N preserved; β, γ > 0 well-defined | PASS |
| S2 | Smooth ODE on bounded domain — existence/uniqueness | PASS |
| S3 | RK4 converges; analytic implicit solution exists for comparison | PASS |
| S4 | I(t) error and final size computable against analytic reference | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# sir/outbreak_s1_ideal.yaml
principle_ref: sha256:<p405_hash>
omega:
  time: [0, 200.0]   # days
  dt: 0.1   # days
  N: 100000
E:
  forward: "dS/dt = −βSI/N; dI/dt = βSI/N − γI; dR/dt = γI"
  beta: 0.3   # per day
  gamma: 0.1   # per day (R₀ = 3.0)
B:
  initial: {S0: 99999, I0: 1, R0: 0}
I:
  scenario: single_outbreak
  R0: 3.0
  dt_sizes: [1.0, 0.1, 0.01]
O: [I_L2_error, peak_time_error, final_size_error]
epsilon:
  I_error_max: 1.0e-6
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | N=10⁵ population; dt=0.1 resolves epidemic curve | PASS |
| S2 | R₀=3.0 — epidemic occurs; unique trajectory | PASS |
| S3 | RK4 at dt=0.1 converges to high precision | PASS |
| S4 | I error < 10⁻⁶ achievable at dt=0.01 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# sir/benchmark_outbreak.yaml
spec_ref: sha256:<spec405_hash>
principle_ref: sha256:<p405_hash>
dataset:
  name: SIR_reference_R0_3
  reference: "High-precision RK reference (dt=1e-6)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Forward-Euler
    params: {dt: 0.1}
    results: {I_error: 1.8e-3, peak_err: 0.3}
  - solver: RK4
    params: {dt: 0.1}
    results: {I_error: 2.5e-8, peak_err: 0.0001}
  - solver: DOPRI5-adaptive
    params: {rtol: 1e-10}
    results: {I_error: 5.0e-11, peak_err: 1e-8}
quality_scoring:
  - {min_I_err: 1.0e-8, Q: 1.00}
  - {min_I_err: 1.0e-6, Q: 0.90}
  - {min_I_err: 1.0e-4, Q: 0.80}
  - {min_I_err: 1.0e-2, Q: 0.75}
```

**Baseline solver:** RK4 — I error 2.5×10⁻⁸
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | I L2 Error | Peak Time Error | Runtime | Q |
|--------|-----------|----------------|---------|---|
| Forward-Euler | 1.8e-3 | 0.3 days | 0.001 s | 0.80 |
| RK4 | 2.5e-8 | 0.0001 days | 0.002 s | 1.00 |
| DOPRI5 | 5.0e-11 | 1e-8 days | 0.005 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (DOPRI5): 200 × 1.00 = 200 PWM
Floor:              200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p405_hash>",
  "h_s": "sha256:<spec405_hash>",
  "h_b": "sha256:<bench405_hash>",
  "r": {"I_error": 5.0e-11, "peak_err": 1e-8, "ratio": 0.0},
  "c": {"fitted_rate": 4.99, "theoretical_rate": 5.0, "K": 3},
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
| L4 Solution | — | 150–200 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep sir_epidemic
pwm-node verify AE_computational_biology/sir_epidemic_s1_ideal.yaml
pwm-node mine AE_computational_biology/sir_epidemic_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
