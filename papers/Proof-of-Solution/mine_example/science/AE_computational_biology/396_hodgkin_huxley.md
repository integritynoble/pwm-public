# Principle #396 — Hodgkin-Huxley Neuron Model

**Domain:** Computational Biology | **Carrier:** membrane potential | **Difficulty:** Standard (δ=3)
**DAG:** N.gating → ∂.time → L.circuit |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.gating→∂.time→L.circuit      HH-neuron   squid-axon-AP     stiff-ODE
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  HODGKIN-HUXLEY NEURON MODEL    P = (E,G,W,C)   Principle #396  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ C_m dV/dt = −g_Na m³h(V−E_Na) − g_K n⁴(V−E_K)       │
│        │            − g_L(V−E_L) + I_ext                        │
│        │ dm/dt = α_m(V)(1−m) − β_m(V)m   (likewise h, n)      │
│        │ V = membrane potential, m,h,n = gating variables       │
│        │ Forward: given I_ext(t) → V(t), m(t), h(t), n(t)     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.gating] ──→ [∂.time] ──→ [L.circuit]                │
│        │ nonlinear  derivative  linear-op                       │
│        │ V={N.gating, ∂.time, L.circuit}  A={N.gating→∂.time, ∂.time→L.circuit}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (smooth ODE, Lipschitz RHS)            │
│        │ Uniqueness: YES (Picard-Lindelof)                     │
│        │ Stability: limit cycle for supra-threshold I_ext       │
│        │ Mismatch: temperature coefficient Q₁₀, channel density │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖V−V_ref‖/‖V_ref‖              │
│        │ q = 4.0 (RK4), 2.0 (implicit trapezoid)             │
│        │ T = {V_error, spike_time_error, gating_error}          │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Voltage, conductance, gating dimensions consistent | PASS |
| S2 | Smooth ODE — existence/uniqueness guaranteed | PASS |
| S3 | RK4 and implicit methods converge for stiff gating kinetics | PASS |
| S4 | V(t) error computable against high-resolution reference | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# hodgkin_huxley/squid_axon_s1_ideal.yaml
principle_ref: sha256:<p396_hash>
omega:
  time: [0, 50.0]   # ms
  dt: 0.01   # ms
E:
  forward: "C_m dV/dt = −I_Na − I_K − I_L + I_ext"
  C_m: 1.0   # uF/cm²
  g_Na: 120.0   # mS/cm²
  g_K: 36.0
  g_L: 0.3
B:
  initial: {V0: -65.0, m0: 0.05, h0: 0.6, n0: 0.32}
I:
  scenario: single_action_potential
  I_ext: 10.0   # uA/cm²
  dt_sizes: [0.1, 0.01, 0.001]
O: [V_L2_error, spike_timing_error, peak_V_error]
epsilon:
  V_error_max: 1.0e-4
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | dt=0.01 ms resolves action potential upstroke (~1 ms) | PASS |
| S2 | I_ext=10 uA/cm² is supra-threshold; produces clear AP | PASS |
| S3 | RK4 at dt=0.01 converges; implicit handles stiffness | PASS |
| S4 | V error < 10⁻⁴ achievable at dt=0.001 ms | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# hodgkin_huxley/benchmark_squid.yaml
spec_ref: sha256:<spec396_hash>
principle_ref: sha256:<p396_hash>
dataset:
  name: HH1952_original
  reference: "Hodgkin & Huxley (1952) J. Physiol. 117:500"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Forward-Euler
    params: {dt: 0.01}
    results: {V_error: 5.2e-3, spike_err: 0.15}
  - solver: RK4
    params: {dt: 0.01}
    results: {V_error: 8.1e-6, spike_err: 0.001}
  - solver: CVODE-BDF
    params: {rtol: 1e-8}
    results: {V_error: 3.2e-7, spike_err: 0.0001}
quality_scoring:
  - {min_V_err: 1.0e-6, Q: 1.00}
  - {min_V_err: 1.0e-4, Q: 0.90}
  - {min_V_err: 1.0e-3, Q: 0.80}
  - {min_V_err: 1.0e-2, Q: 0.75}
```

**Baseline solver:** RK4 — V error 8.1×10⁻⁶
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | V L2 Error | Spike Timing Error | Runtime | Q |
|--------|-----------|-------------------|---------|---|
| Forward-Euler | 5.2e-3 | 0.15 ms | 0.01 s | 0.80 |
| RK4 | 8.1e-6 | 0.001 ms | 0.02 s | 1.00 |
| CVODE-BDF | 3.2e-7 | 0.0001 ms | 0.05 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (CVODE): 300 × 1.00 = 300 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p396_hash>",
  "h_s": "sha256:<spec396_hash>",
  "h_b": "sha256:<bench396_hash>",
  "r": {"V_error": 3.2e-7, "spike_err": 0.0001, "ratio": 0.003},
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
pwm-node benchmarks | grep hodgkin_huxley
pwm-node verify AE_computational_biology/hodgkin_huxley_s1_ideal.yaml
pwm-node mine AE_computational_biology/hodgkin_huxley_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
