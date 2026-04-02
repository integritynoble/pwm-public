# Principle #407 — Lotka-Volterra (Predator-Prey)

**Domain:** Computational Biology | **Carrier:** population size | **Difficulty:** Standard (δ=3)
**DAG:** N.bilinear → ∂.time |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.bilinear→∂.time      LV-model     oscillation       ODE
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LOTKA-VOLTERRA (PREDATOR-PREY) P = (E,G,W,C)   Principle #407 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ dx/dt = αx − βxy          (prey growth − predation)   │
│        │ dy/dt = δxy − γy          (predator growth − death)   │
│        │ x = prey population, y = predator population           │
│        │ α,β,δ,γ > 0 interaction parameters                    │
│        │ Forward: given α,β,δ,γ, x(0),y(0) → x(t), y(t)      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.bilinear] ──→ [∂.time]                              │
│        │ nonlinear  derivative                                  │
│        │ V={N.bilinear, ∂.time}  A={N.bilinear→∂.time}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (smooth ODE in positive quadrant)       │
│        │ Uniqueness: YES (locally Lipschitz)                    │
│        │ Stability: center (neutrally stable periodic orbits)   │
│        │ Mismatch: density-dependent terms, stochastic effects  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖x−x_ref‖/‖x_ref‖              │
│        │ q = 4.0 (RK4); energy-preserving methods preferred   │
│        │ T = {x_error, period_error, conserved_quantity_drift}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Population dimensions consistent; parameters positive | PASS |
| S2 | Smooth ODE on positive quadrant — unique orbits | PASS |
| S3 | RK4 converges; symplectic methods preserve invariant H | PASS |
| S4 | L2 error and invariant drift computable against reference | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# lotka_volterra/oscillation_s1_ideal.yaml
principle_ref: sha256:<p407_hash>
omega:
  time: [0, 100.0]
  dt: 0.01
E:
  forward: "dx/dt = αx − βxy; dy/dt = δxy − γy"
  alpha: 1.0
  beta: 0.1
  delta: 0.075
  gamma: 1.5
B:
  initial: {x0: 40.0, y0: 9.0}
I:
  scenario: periodic_oscillation
  dt_sizes: [0.1, 0.01, 0.001]
O: [x_L2_error, period_error, H_drift]
epsilon:
  x_error_max: 1.0e-5
  H_drift_max: 1.0e-8
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | dt=0.01 resolves oscillation period (~15 time units) | PASS |
| S2 | Parameters give stable periodic orbits around coexistence point | PASS |
| S3 | RK4 converges; symplectic integrator preserves H exactly | PASS |
| S4 | x error < 10⁻⁵ and H drift < 10⁻⁸ achievable | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# lotka_volterra/benchmark_oscillation.yaml
spec_ref: sha256:<spec407_hash>
principle_ref: sha256:<p407_hash>
dataset:
  name: LV_reference_orbits
  reference: "High-precision symplectic reference"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Forward-Euler
    params: {dt: 0.01}
    results: {x_error: 3.5e-3, H_drift: 2.1e-2}
  - solver: RK4
    params: {dt: 0.01}
    results: {x_error: 1.2e-7, H_drift: 5.0e-6}
  - solver: Symplectic-Euler
    params: {dt: 0.01}
    results: {x_error: 8.0e-4, H_drift: 1.0e-14}
quality_scoring:
  - {min_x_err: 1.0e-6, Q: 1.00}
  - {min_x_err: 1.0e-4, Q: 0.90}
  - {min_x_err: 1.0e-3, Q: 0.80}
  - {min_x_err: 1.0e-2, Q: 0.75}
```

**Baseline solver:** RK4 — x error 1.2×10⁻⁷
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | x L2 Error | H Drift | Runtime | Q |
|--------|-----------|---------|---------|---|
| Forward-Euler | 3.5e-3 | 2.1e-2 | 0.002 s | 0.80 |
| Symplectic-Euler | 8.0e-4 | 1.0e-14 | 0.003 s | 0.80 |
| RK4 | 1.2e-7 | 5.0e-6 | 0.005 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (RK4): 300 × 1.00 = 300 PWM
Floor:           300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p407_hash>",
  "h_s": "sha256:<spec407_hash>",
  "h_b": "sha256:<bench407_hash>",
  "r": {"x_error": 1.2e-7, "H_drift": 5.0e-6, "ratio": 0.012},
  "c": {"fitted_rate": 4.01, "theoretical_rate": 4.0, "K": 3},
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
pwm-node benchmarks | grep lotka_volterra
pwm-node verify AE_computational_biology/lotka_volterra_s1_ideal.yaml
pwm-node mine AE_computational_biology/lotka_volterra_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
