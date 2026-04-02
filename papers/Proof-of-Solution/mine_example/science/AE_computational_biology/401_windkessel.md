# Principle #401 — Windkessel Model (Lumped Circulation)

**Domain:** Computational Biology | **Carrier:** arterial pressure | **Difficulty:** Introductory (δ=2)
**DAG:** L.circuit → ∂.time |  **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.circuit→∂.time      windkessel   aortic-pressure   ODE
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  WINDKESSEL MODEL (LUMPED)      P = (E,G,W,C)   Principle #401  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ C dP/dt = Q(t) − P/R                    (2-element)   │
│        │ P(t) = R₁ Q(t) + P_c(t)                 (3-element)   │
│        │ C dP_c/dt = Q(t) − P_c/R₂                             │
│        │ P = arterial pressure, Q = cardiac output flow         │
│        │ Forward: given Q(t), R, C → P(t) over cardiac cycles  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.circuit] ──→ [∂.time]                               │
│        │ linear-op  derivative                                  │
│        │ V={L.circuit, ∂.time}  A={L.circuit→∂.time}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear ODE with bounded forcing)       │
│        │ Uniqueness: YES (first-order linear ODE)               │
│        │ Stability: YES (RC decay — exponentially stable)       │
│        │ Mismatch: R, C estimation from clinical data           │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative pressure error ‖P−P_ref‖/‖P_ref‖         │
│        │ q = 2.0 (trapezoid), 4.0 (RK4)                      │
│        │ T = {P_error, systolic_error, diastolic_error}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Pressure, flow, resistance, compliance dimensionally consistent | PASS |
| S2 | Linear ODE — analytic solution exists (exponential + particular) | PASS |
| S3 | Any standard ODE method converges; analytic available | PASS |
| S4 | Pressure error computable against analytic or clinical reference | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# windkessel/aortic_pressure_s1_ideal.yaml
principle_ref: sha256:<p401_hash>
omega:
  time: [0, 5.0]   # s (5 cardiac cycles)
  dt: 1.0e-3   # s
  model: 3_element
E:
  forward: "P = R1·Q + P_c; C dP_c/dt = Q − P_c/R2"
  R1: 0.06   # mmHg·s/mL (characteristic impedance)
  R2: 1.0    # mmHg·s/mL (peripheral resistance)
  C: 1.5     # mL/mmHg (arterial compliance)
B:
  initial: {P_c0: 80.0}   # mmHg
I:
  scenario: resting_cardiac_output
  Q_waveform: half_sine_70bpm
  dt_sizes: [1e-2, 1e-3, 1e-4]
O: [P_L2_error, systolic_error, diastolic_error]
epsilon:
  P_error_max: 1.0e-4
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | dt=1 ms resolves cardiac cycle (~860 ms); 3-element model standard | PASS |
| S2 | Linear ODE with periodic forcing — bounded solution guaranteed | PASS |
| S3 | Trapezoid rule converges at O(dt²) | PASS |
| S4 | P error < 10⁻⁴ achievable at dt=10⁻⁴ s | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# windkessel/benchmark_aortic.yaml
spec_ref: sha256:<spec401_hash>
principle_ref: sha256:<p401_hash>
dataset:
  name: WK3_analytic_reference
  reference: "Analytic 3-element Windkessel solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Forward-Euler
    params: {dt: 1e-3}
    results: {P_error: 2.5e-3, sys_err: 0.8}
  - solver: Trapezoid
    params: {dt: 1e-3}
    results: {P_error: 1.2e-5, sys_err: 0.01}
  - solver: RK4
    params: {dt: 1e-3}
    results: {P_error: 3.5e-8, sys_err: 0.0001}
quality_scoring:
  - {min_P_err: 1.0e-7, Q: 1.00}
  - {min_P_err: 1.0e-4, Q: 0.90}
  - {min_P_err: 1.0e-3, Q: 0.80}
  - {min_P_err: 1.0e-2, Q: 0.75}
```

**Baseline solver:** Trapezoid — P error 1.2×10⁻⁵
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | P L2 Error | Systolic Error (mmHg) | Runtime | Q |
|--------|-----------|----------------------|---------|---|
| Forward-Euler | 2.5e-3 | 0.8 | 0.001 s | 0.80 |
| Trapezoid | 1.2e-5 | 0.01 | 0.002 s | 0.90 |
| RK4 | 3.5e-8 | 0.0001 | 0.003 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (RK4): 200 × 1.00 = 200 PWM
Floor:           200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p401_hash>",
  "h_s": "sha256:<spec401_hash>",
  "h_b": "sha256:<bench401_hash>",
  "r": {"P_error": 3.5e-8, "sys_err": 0.0001, "ratio": 0.004},
  "c": {"fitted_rate": 4.00, "theoretical_rate": 4.0, "K": 3},
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
pwm-node benchmarks | grep windkessel
pwm-node verify AE_computational_biology/windkessel_s1_ideal.yaml
pwm-node mine AE_computational_biology/windkessel_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
