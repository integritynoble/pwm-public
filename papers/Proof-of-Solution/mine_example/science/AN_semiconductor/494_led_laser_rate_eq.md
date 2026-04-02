# Principle #494 — LED / Laser Diode Rate Equations

**Domain:** Semiconductor Physics | **Carrier:** N/A (ODE-based) | **Difficulty:** Standard (δ=3)
**DAG:** [N.pointwise] --> [∂.time] --> [B.contact] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pw-->∂.t-->B.cont  LED-Laser  LD-benchmark  ODE-solver
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LED / LASER DIODE RATE EQUATIONS P=(E,G,W,C) Principle #494    │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ dN/dt = J/(qd) − N/τ_sp − v_g g(N) S  (carrier rate) │
│        │ dS/dt = Γ v_g g(N) S − S/τ_p + βN/τ_sp (photon rate) │
│        │ g(N) = g₀ ln(N/N_tr)  (logarithmic gain)              │
│        │ P = η_d (ℏω/q)(I − I_th)  (above threshold)           │
│        │ Forward: given (I, structure) → N(t), S(t), P(I)      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pw] ──→ [∂.t] ──→ [B.cont]                          │
│        │  gain/recomb  rate-eq  mirror-BC                       │
│        │ V={N.pw,∂.t,B.cont}  A={N.pw→∂.t,∂.t→B.cont}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (ODE system with bounded RHS)           │
│        │ Uniqueness: YES (Lipschitz continuous)                 │
│        │ Stability: above threshold → damped relaxation osc.   │
│        │ Mismatch: gain compression, thermal rollover           │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |P_sim − P_meas|/P_meas  (power error)            │
│        │ q = 4.0 (RK4 for ODEs)                               │
│        │ T = {LI_error, threshold_current, modulation_BW}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | N, S ≥ 0; carrier/photon conservation consistent | PASS |
| S2 | Gain model ensures unique steady state above threshold | PASS |
| S3 | RK4/45 integrates stiff rate equations; relaxation oscillations | PASS |
| S4 | L-I curve matches within 5% above threshold | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# led_laser/edge_emitting_s1.yaml
principle_ref: sha256:<p494_hash>
omega:
  time: [0, 10e-9]    # 10 ns transient
  dt: 1e-12
E:
  forward: "carrier + photon rate equations"
  gain_model: logarithmic
  g0: 1500            # cm⁻¹
  N_tr: 1.5e18        # cm⁻³
  Gamma: 0.3          # confinement factor
  tau_sp: 2e-9        # s
  tau_p: 2e-12        # s
B:
  current: [0, 5, 10, 20, 30, 50]   # mA
  cavity_length: 300e-6   # m
I:
  scenario: InGaAs_edge_emitting_laser
  models: [basic_rate, gain_compression, thermal]
O: [LI_curve, threshold_mA, modulation_bandwidth, RIN]
epsilon:
  LI_error_max: 0.05
  threshold_error_max: 0.10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | dt = 1 ps resolves relaxation oscillations at ~5 GHz | PASS |
| S2 | InGaAs parameters well-characterized | PASS |
| S3 | RK45 converges for stiff carrier-photon coupling | PASS |
| S4 | L-I slope efficiency within 5% | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# led_laser/benchmark_laser.yaml
spec_ref: sha256:<spec494_hash>
principle_ref: sha256:<p494_hash>
dataset:
  name: InGaAs_laser_LI_data
  reference: "Coldren et al. (2012) Diode Lasers textbook"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Basic rate equations
    params: {gain: linear, compression: none}
    results: {LI_error: 0.08, threshold_error: 0.05}
  - solver: Rate eq + gain compression
    params: {gain: log, epsilon_c: 3e-17}
    results: {LI_error: 0.04, threshold_error: 0.03}
  - solver: Full (thermal + leakage)
    params: {gain: log, thermal: self_heating}
    results: {LI_error: 0.02, threshold_error: 0.02}
quality_scoring:
  - {min_err: 0.01, Q: 1.00}
  - {min_err: 0.03, Q: 0.90}
  - {min_err: 0.05, Q: 0.80}
  - {min_err: 0.10, Q: 0.75}
```

**Baseline solver:** Rate eq + gain compression — LI error 4%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | LI Error | Threshold Error | Runtime | Q |
|--------|---------|----------------|---------|---|
| Basic rate | 0.08 | 0.05 | 0.01 s | 0.80 |
| Gain compression | 0.04 | 0.03 | 0.02 s | 0.90 |
| Thermal + leakage | 0.02 | 0.02 | 0.1 s | 0.90 |
| Multi-mode + thermal | 0.008 | 0.01 | 1.0 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (multi-mode): 300 × 1.00 = 300 PWM
Floor:                  300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p494_hash>",
  "h_s": "sha256:<spec494_hash>",
  "h_b": "sha256:<bench494_hash>",
  "r": {"LI_error": 0.008, "error_bound": 0.05, "ratio": 0.160},
  "c": {"threshold_error": 0.01, "currents": 6, "K": 3},
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
pwm-node benchmarks | grep led_laser
pwm-node verify led_laser/edge_emitting_s1.yaml
pwm-node mine led_laser/edge_emitting_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
