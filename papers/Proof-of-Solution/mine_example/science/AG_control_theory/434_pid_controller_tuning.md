# Principle #434 — PID Controller Tuning

**Domain:** Control Theory & Dynamical Systems | **Carrier:** signal | **Difficulty:** Textbook (δ=1)
**DAG:** L.state → ∂.time → L.gain |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.state→∂.time→L.gain        PID-tune    PIDPlant-10        ZN/IMC
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PID CONTROLLER TUNING      P = (E, G, W, C)   Principle #434  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ u(t) = Kp·e(t) + Ki·∫e(τ)dτ + Kd·de/dt               │
│        │ Plant: G(s) = K·exp(-Ls)/(τs+1) (FOPDT model)         │
│        │ Inverse: identify (K,τ,L) then compute (Kp,Ki,Kd)     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.state] ──→ [∂.time] ──→ [L.gain]                    │
│        │  linear-op  derivative  linear-op                       │
│        │ V={L.state, ∂.time, L.gain}  A={L.state→∂.time, ∂.time→L.gain}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (PID always computable for FOPDT)       │
│        │ Uniqueness: tuning-rule dependent (ZN, IMC, SIMC)      │
│        │ Stability: YES for proper gain/phase margins           │
│        │ Mismatch: higher-order dynamics, nonlinearities        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = IAE (primary), overshoot % (secondary)             │
│        │ q = depends on tuning rule                            │
│        │ T = {IAE, overshoot, settling_time, gain_margin}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | FOPDT parameters (K, τ, L) physically meaningful | PASS |
| S2 | Gain and phase margins positive for tuned PID | PASS |
| S3 | Step response converges to setpoint | PASS |
| S4 | IAE computable from closed-loop step response | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# control/pid_tuning_s1_ideal.yaml
principle_ref: sha256:<p434_hash>
omega:
  description: "FOPDT plant, step response identification"
  plant: {K: 1.0, tau: 5.0, L: 1.0}
E:
  forward: "u = Kqe + Ki*int(e) + Kd*de/dt"
  identification: "FOPDT from step response"
I:
  dataset: PIDPlant_10
  plants: 10
  noise: {type: gaussian, SNR_dB: 30}
  scenario: ideal
O: [IAE, overshoot_percent, settling_time, gain_margin_dB]
epsilon:
  IAE_max: 5.0
  overshoot_max: 20.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Plant parameters physical; PID gains computable | PASS |
| S2 | Gain margin > 6 dB, phase margin > 30° | PASS |
| S3 | Closed-loop step response settles within 30 s | PASS |
| S4 | IAE < 5.0 feasible for given plant | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# control/benchmark_pid_s1.yaml
spec_ref: sha256:<spec434_hash>
principle_ref: sha256:<p434_hash>
dataset:
  name: PIDPlant_10
  plants: 10
  data_hash: sha256:<dataset_434_hash>
baselines:
  - solver: Ziegler-Nichols
    params: {method: ultimate_gain}
    results: {IAE: 4.2, overshoot: 25.0}
  - solver: IMC
    params: {lambda: 2.0}
    results: {IAE: 3.1, overshoot: 5.0}
  - solver: SIMC
    params: {tau_c: 1.0}
    results: {IAE: 2.8, overshoot: 8.0}
quality_scoring:
  - {max_IAE: 2.0, Q: 1.00}
  - {max_IAE: 3.0, Q: 0.90}
  - {max_IAE: 4.5, Q: 0.80}
  - {max_IAE: 6.0, Q: 0.75}
```

**Baseline solver:** Ziegler-Nichols — IAE 4.2
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | IAE | Overshoot % | Settling (s) | Q |
|--------|-----|-------------|-------------|---|
| Ziegler-Nichols | 4.2 | 25.0 | 18 | 0.78 |
| IMC | 3.1 | 5.0 | 12 | 0.88 |
| SIMC | 2.8 | 8.0 | 10 | 0.92 |
| Auto-Tune (BO) | 2.2 | 6.0 | 9 | 0.96 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (BO):    100 × 0.96 = 96 PWM
Floor:             100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p434_hash>",
  "h_s": "sha256:<spec434_hash>",
  "h_b": "sha256:<bench434_hash>",
  "r": {"IAE": 2.2, "error_bound": 5.0, "ratio": 0.44},
  "c": {"method": "Bayesian-Opt", "overshoot": 6.0, "K": 3},
  "Q": 0.96,
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
| L4 Solution | — | 75–96 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep pid_controller
pwm-node verify control/pid_tuning_s1_ideal.yaml
pwm-node mine control/pid_tuning_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
