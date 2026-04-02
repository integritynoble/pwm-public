# Principle #397 — FitzHugh-Nagumo Model

**Domain:** Computational Biology | **Carrier:** excitation variable | **Difficulty:** Standard (δ=3)
**DAG:** N.pointwise → ∂.time |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pointwise→∂.time        FHN-model    oscillation       ODE
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  FITZHUGH-NAGUMO MODEL          P = (E,G,W,C)   Principle #397  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ dv/dt = v − v³/3 − w + I_ext                          │
│        │ dw/dt = ε(v + a − bw)                                  │
│        │ v = fast excitation variable, w = slow recovery         │
│        │ ε ≪ 1 controls time-scale separation                   │
│        │ Forward: given I_ext, ε, a, b → v(t), w(t)            │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pointwise] ──→ [∂.time]                             │
│        │ nonlinear  derivative                                  │
│        │ V={N.pointwise, ∂.time}  A={N.pointwise→∂.time}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (polynomial RHS, globally Lipschitz)    │
│        │ Uniqueness: YES (smooth vector field)                  │
│        │ Stability: Hopf bifurcation at critical I_ext          │
│        │ Mismatch: parameter mapping to biophysical conductances│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖v−v_ref‖/‖v_ref‖              │
│        │ q = 4.0 (RK4), 2.0 (trapezoid)                      │
│        │ T = {v_error, period_error, bifurcation_point}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | v and w dimensionless; parameters a, b, ε well-defined | PASS |
| S2 | Polynomial ODE — global existence guaranteed | PASS |
| S3 | RK4 converges; adaptive stepping handles relaxation oscillations | PASS |
| S4 | L2 error and period computable against high-resolution reference | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# fitzhugh_nagumo/oscillation_s1_ideal.yaml
principle_ref: sha256:<p397_hash>
omega:
  time: [0, 100.0]
  dt: 0.01
E:
  forward: "dv/dt = v − v³/3 − w + I; dw/dt = ε(v + a − bw)"
  a: 0.7
  b: 0.8
  epsilon: 0.08
B:
  initial: {v0: -1.0, w0: -0.5}
I:
  scenario: supra_threshold_oscillation
  I_ext: 0.5
  dt_sizes: [0.1, 0.01, 0.001]
O: [v_L2_error, period_error]
epsilon:
  v_error_max: 1.0e-5
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | dt=0.01 resolves fast excitation dynamics | PASS |
| S2 | I_ext=0.5 above Hopf bifurcation — stable limit cycle | PASS |
| S3 | RK4 at dt=0.01 converges for ε=0.08 | PASS |
| S4 | v error < 10⁻⁵ achievable at dt=0.001 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# fitzhugh_nagumo/benchmark_oscillation.yaml
spec_ref: sha256:<spec397_hash>
principle_ref: sha256:<p397_hash>
dataset:
  name: FHN_reference_solution
  reference: "High-order RK reference at dt=1e-6"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Forward-Euler
    params: {dt: 0.01}
    results: {v_error: 2.1e-3, period_err: 0.05}
  - solver: RK4
    params: {dt: 0.01}
    results: {v_error: 5.5e-7, period_err: 1e-5}
  - solver: DOPRI5-adaptive
    params: {rtol: 1e-8}
    results: {v_error: 1.2e-8, period_err: 1e-7}
quality_scoring:
  - {min_v_err: 1.0e-7, Q: 1.00}
  - {min_v_err: 1.0e-5, Q: 0.90}
  - {min_v_err: 1.0e-3, Q: 0.80}
  - {min_v_err: 1.0e-2, Q: 0.75}
```

**Baseline solver:** RK4 — v error 5.5×10⁻⁷
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | v L2 Error | Period Error | Runtime | Q |
|--------|-----------|-------------|---------|---|
| Forward-Euler | 2.1e-3 | 0.05 | 0.005 s | 0.80 |
| RK4 | 5.5e-7 | 1e-5 | 0.01 s | 1.00 |
| DOPRI5 | 1.2e-8 | 1e-7 | 0.02 s | 1.00 |

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
  "h_p": "sha256:<p397_hash>",
  "h_s": "sha256:<spec397_hash>",
  "h_b": "sha256:<bench397_hash>",
  "r": {"v_error": 1.2e-8, "period_err": 1e-7, "ratio": 0.001},
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
pwm-node benchmarks | grep fitzhugh_nagumo
pwm-node verify AE_computational_biology/fitzhugh_nagumo_s1_ideal.yaml
pwm-node mine AE_computational_biology/fitzhugh_nagumo_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
