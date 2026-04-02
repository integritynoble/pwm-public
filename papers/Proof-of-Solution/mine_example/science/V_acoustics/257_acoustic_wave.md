# Acoustic Wave Equation — Four-Layer Walkthrough

**Principle #257 · Acoustic Wave Propagation (Time-Domain)**
Domain: Acoustics & Vibration | Carrier: pressure wave | Difficulty: standard (δ=3) | DAG: ∂.time → ∂.space.laplacian → B.impedance

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Wave equation,   │→│ Source in homo-  │→│ Analytical Green │→│ FDTD / SEM / DG  │
│ speed of sound,  │ │ geneous medium,  │ │ function, time   │ │ acoustic solver  │
│ source, BCs      │ │ S1-S4 scenarios  │ │ series baselines │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

∂²p/∂t² = c²∇²p + s(r,t)
p = acoustic pressure, c(r) = speed of sound, s = source term
Boundary: rigid (∂p/∂n=0), pressure release (p=0), impedance (∂p/∂n + p/(ρc)=0)

### DAG

```
[∂.time] --> [∂.space.laplacian] --> [B.impedance]
```
V={∂.time, ∂.space.laplacian, B.impedance}  A={∂.time→∂.space.laplacian, ∂.space.laplacian→B.impedance}  L_DAG=2.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Hyperbolic PDE, well-posed initial-value problem |
| Uniqueness | YES | Unique solution for given ICs and BCs |
| Stability | CONDITIONAL | CFL: Δt ≤ Δx/(c√d) for explicit schemes |

Mismatch: sound speed error, boundary impedance, source waveform

### Error Method

e = relative pressure error ‖p_num−p_ref‖/‖p_ref‖, arrival time error
q = 2.0 (second-order FD), q = 4+ (spectral element)

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #257"
omega:
  domain_m: [10, 10, 10]
  c_m_s: 343.0
  grid: [200, 200, 200]
  time_s: 0.05
E:
  forward: "d2p/dt2 = c^2 * laplacian(p) + s(r,t)"
  boundary: absorbing_PML
I:
  source: {type: gaussian_pulse, freq_Hz: 1000, pos: [5,5,5]}
  scenario: S1_ideal
O: [relative_pressure_error, arrival_time_error_ms, energy_decay_rate]
epsilon:
  rel_err_max: 0.02
  arrival_time_max_ms: 0.1
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact c, BCs | None | rel err ≤ 0.02 |
| S2 Mismatch | c ± 5% | Δc | rel err ≤ 0.08 |
| S3 Oracle | True c given | Known Δc | rel err ≤ 0.03 |
| S4 Blind Cal | Estimate c from arrival times | Self-cal | recovery ≥ 85% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: acoustic_wave_3D
  cases: 8
  analytical_ref: Green_function_free_space, mode_decomposition
baselines:
  - solver: FDTD_2nd_order
    rel_err: 0.015
    time_s: 90
  - solver: spectral_element
    rel_err: 0.003
    time_s: 200
quality_scoring:
  metric: relative_pressure_error
  thresholds:
    - {max: 0.003, Q: 1.00}
    - {max: 0.008, Q: 0.90}
    - {max: 0.020, Q: 0.80}
    - {max: 0.050, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | rel err | Time | Q | Reward |
|--------|---------|------|---|--------|
| FDTD_2nd | 0.015 | 90s | 0.80 | 240 PWM |
| SEM | 0.003 | 200s | 1.00 | 300 PWM |
| DG_p4 | 0.005 | 150s | 0.90 | 270 PWM |

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q PWM
```

### Certificate

```json
{
  "principle": 257,
  "r": {"residual_norm": 0.003, "error_bound": 0.02, "ratio": 0.15},
  "c": {"resolutions": [100,200,400], "fitted_rate": 2.0, "theoretical_rate": 2.0},
  "Q": 1.00,
  "gates": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"}
}
```

---

## Reward Summary

| Layer | One-time | Ongoing |
|-------|----------|---------|
| L1 Principle | 200 PWM | 5% of L4 mints |
| L2 spec | 150 PWM × 4 | 10% of L4 mints |
| L3 Benchmark | 100 PWM × 4 | 15% of L4 mints |
| L4 Solution | — | 240–300 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep acoustic_wave
pwm-node mine acoustic_wave/free_field_s1_ideal.yaml
```
