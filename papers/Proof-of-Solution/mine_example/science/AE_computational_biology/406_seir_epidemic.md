# Principle #406 — SEIR Epidemic Model

**Domain:** Computational Biology | **Carrier:** population fractions | **Difficulty:** Standard (δ=3)
**DAG:** N.reaction.sir → ∂.time |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.reaction.sir→∂.time      SEIR-model   latent-outbreak   ODE
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SEIR EPIDEMIC MODEL            P = (E,G,W,C)   Principle #406  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ dS/dt = −β S I / N                                    │
│        │ dE/dt = β S I / N − σ E                               │
│        │ dI/dt = σ E − γ I                                      │
│        │ dR/dt = γ I                                            │
│        │ σ = 1/latent_period, R₀ = β/γ                         │
│        │ Forward: given β, σ, γ, ICs → S(t), E(t), I(t), R(t) │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.reaction.sir] ──→ [∂.time]                          │
│        │ nonlinear  derivative                                  │
│        │ V={N.reaction.sir, ∂.time}  A={N.reaction.sir→∂.time}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (smooth ODE, positive invariant set)    │
│        │ Uniqueness: YES (Lipschitz on compact domain)          │
│        │ Stability: DFE stable iff R₀ < 1; endemic equilibrium │
│        │ Mismatch: latent period variability, time-varying β    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative error ‖I−I_ref‖/‖I_ref‖                  │
│        │ q = 4.0 (RK4), 2.0 (trapezoid)                      │
│        │ T = {I_error, peak_time_error, final_size_error}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | S+E+I+R=N conserved; σ, β, γ > 0 | PASS |
| S2 | Smooth 4D ODE — unique trajectory on positive simplex | PASS |
| S3 | RK4 converges; latent period introduces delay but no stiffness | PASS |
| S4 | I(t) error computable against high-resolution reference | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# seir/latent_outbreak_s1_ideal.yaml
principle_ref: sha256:<p406_hash>
omega:
  time: [0, 300.0]   # days
  dt: 0.1
  N: 100000
E:
  forward: "SEIR: dS/dt=−βSI/N, dE/dt=βSI/N−σE, dI/dt=σE−γI, dR/dt=γI"
  beta: 0.5
  sigma: 0.2   # 5-day latent period
  gamma: 0.1   # 10-day infectious period (R₀ = 5.0)
B:
  initial: {S0: 99999, E0: 1, I0: 0, R0: 0}
I:
  scenario: single_wave_with_latency
  R0: 5.0
  dt_sizes: [1.0, 0.1, 0.01]
O: [I_L2_error, peak_time_error, E_peak_error]
epsilon:
  I_error_max: 1.0e-6
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | dt=0.1 resolves epidemic dynamics; 300 days covers full wave | PASS |
| S2 | R₀=5.0 — strong epidemic with well-defined peak | PASS |
| S3 | RK4 converges; no stiffness in SEIR with these parameters | PASS |
| S4 | I error < 10⁻⁶ achievable at dt=0.01 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# seir/benchmark_latent.yaml
spec_ref: sha256:<spec406_hash>
principle_ref: sha256:<p406_hash>
dataset:
  name: SEIR_reference_R0_5
  reference: "High-precision adaptive RK reference"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Forward-Euler
    params: {dt: 0.1}
    results: {I_error: 2.2e-3, peak_err: 0.4}
  - solver: RK4
    params: {dt: 0.1}
    results: {I_error: 3.8e-8, peak_err: 0.0002}
  - solver: DOPRI5-adaptive
    params: {rtol: 1e-10}
    results: {I_error: 8.0e-11, peak_err: 1e-8}
quality_scoring:
  - {min_I_err: 1.0e-8, Q: 1.00}
  - {min_I_err: 1.0e-6, Q: 0.90}
  - {min_I_err: 1.0e-4, Q: 0.80}
  - {min_I_err: 1.0e-2, Q: 0.75}
```

**Baseline solver:** RK4 — I error 3.8×10⁻⁸
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | I L2 Error | Peak Time Error | Runtime | Q |
|--------|-----------|----------------|---------|---|
| Forward-Euler | 2.2e-3 | 0.4 days | 0.001 s | 0.80 |
| RK4 | 3.8e-8 | 0.0002 days | 0.003 s | 1.00 |
| DOPRI5 | 8.0e-11 | 1e-8 days | 0.008 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (DOPRI5): 300 × 1.00 = 300 PWM
Floor:              300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p406_hash>",
  "h_s": "sha256:<spec406_hash>",
  "h_b": "sha256:<bench406_hash>",
  "r": {"I_error": 8.0e-11, "peak_err": 1e-8, "ratio": 0.0},
  "c": {"fitted_rate": 4.98, "theoretical_rate": 5.0, "K": 3},
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
pwm-node benchmarks | grep seir_epidemic
pwm-node verify AE_computational_biology/seir_epidemic_s1_ideal.yaml
pwm-node mine AE_computational_biology/seir_epidemic_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
