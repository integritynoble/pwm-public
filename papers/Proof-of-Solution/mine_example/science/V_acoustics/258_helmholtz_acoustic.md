# Helmholtz Acoustic — Four-Layer Walkthrough

**Principle #258 · Acoustic Helmholtz Equation (Frequency Domain)**
Domain: Acoustics & Vibration | Carrier: pressure wave | Difficulty: standard (δ=3) | DAG: ∂.space.laplacian → L.sparse → B.impedance

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ (∇²+k²)p = s,   │→│ Interior/exterior│→│ Analytical modes │→│ FEM / BEM /      │
│ radiation cond,  │ │ acoustic config, │ │ or series soln,  │ │ spectral solver  │
│ impedance BCs    │ │ S1-S4 scenarios  │ │ baselines        │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

∇²p + k²p = −s(r),  k = ω/c
Interior: room modes; Exterior: Sommerfeld radiation condition
Impedance BC: ∂p/∂n + jkβp = 0, β = ρc/Z_surface

### DAG

```
[∂.space.laplacian] --> [L.sparse] --> [B.impedance]
```
V={∂.space.laplacian, L.sparse, B.impedance}  A={∂.space.laplacian→L.sparse, L.sparse→B.impedance}  L_DAG=2.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Fredholm alternative (interior); radiation condition (exterior) |
| Uniqueness | YES | With absorption or radiation condition |
| Stability | CONDITIONAL | Near resonance: high Q → large amplification |

Mismatch: impedance BC error, sound speed, source position

### Error Method

e = SPL error (dB), relative pressure error; q = 2.0 (linear FEM)

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #258"
omega:
  domain: rectangular_room
  dims_m: [5, 4, 3]
  freq_Hz: [20, 500]
  absorption: {alpha: 0.1}
E:
  forward: "nabla^2 p + k^2 p = -s(r)"
I:
  scenario: S1_ideal
  source: {type: monopole, pos: [1,1,1]}
O: [SPL_error_dB, relative_pressure_error, mode_freq_error_Hz]
epsilon:
  SPL_error_max_dB: 1.0
  mode_freq_error_max_Hz: 0.5
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known room, absorption | None | SPL err ≤ 1 dB |
| S2 Mismatch | α ± 0.05 | Δα | SPL err ≤ 3 dB |
| S3 Oracle | True α given | Known Δα | SPL err ≤ 1.5 dB |
| S4 Blind Cal | Estimate α from measurements | Self-cal | recovery ≥ 85% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: helmholtz_acoustic
  cases: 8
  analytical_ref: room_mode_decomposition, Green_function
baselines:
  - solver: FEM_p2
    SPL_err_dB: 0.5
  - solver: BEM_acoustic
    SPL_err_dB: 0.8
quality_scoring:
  metric: SPL_error_dB
  thresholds:
    - {max: 0.2, Q: 1.00}
    - {max: 0.5, Q: 0.90}
    - {max: 1.0, Q: 0.80}
    - {max: 3.0, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | SPL err | Time | Q | Reward |
|--------|---------|------|---|--------|
| FEM_p2 | 0.5 dB | 30s | 0.90 | 270 PWM |
| BEM | 0.8 dB | 20s | 0.80 | 240 PWM |
| spectral_p8 | 0.15 dB | 60s | 1.00 | 300 PWM |

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q PWM
```

### Certificate

```json
{
  "principle": 258,
  "r": {"residual_norm": 0.15, "error_bound": 1.0, "ratio": 0.15},
  "c": {"resolutions": [20,40,80], "fitted_rate": 2.0, "theoretical_rate": 2.0},
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
pwm-node benchmarks | grep helmholtz_acoustic
pwm-node mine helmholtz_acoustic/room_s1_ideal.yaml
```
