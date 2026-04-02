# Antenna Radiation — Four-Layer Walkthrough

**Principle #236 · Antenna Radiation Pattern & Impedance**
Domain: Electromagnetics & Optics | Carrier: photon/EM-field | Difficulty: standard (δ=3) | DAG: [K.green.em] --> [L.dense] --> [B.surface] --> [∫.spatial]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Current → far    │→│ Dipole/patch/    │→│ Analytical gain, │→│ MoM / FEM / FDTD │
│ field, directivi-│ │ array geometry,  │ │ impedance refs   │ │ antenna solver   │
│ ty, impedance    │ │ S1-S4 scenarios  │ │ baselines        │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

E_far(θ,φ) = −jkη₀ (e^{−jkr}/4πr) ∫_V J(r') e^{jk·r̂·r'} dV'
Directivity: D(θ,φ) = 4πU(θ,φ)/P_rad
Input impedance: Z_in = V_gap/I_in

### DAG

```
[K.green.em] --> [L.dense] --> [B.surface] --> [∫.spatial]
Green-kernel  impedance-solve  surface-BC  far-field-integral
```

V={K.green.em,L.dense,B.surface,∫.spatial}  L_DAG=3.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | Integral radiation exists for bounded current |
| Uniqueness | YES | Far field uniquely determined by current distribution |
| Stability | YES | Continuous dependence on current |

Mismatch: feed model, ground plane, mutual coupling, manufacturing tolerance

### Error Method

e = gain error (dB), impedance error |ΔZ_in|/|Z_in|, pattern correlation
q = 2.0 (MoM with RWG)

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #236"
omega:
  antenna: half_wave_dipole
  freq_GHz: 2.4
  length_mm: 62.5
E:
  forward: "E_far = -jk*eta0/(4pi*r) * integral(J*exp(jk*r_hat.r') dV')"
I:
  scenario: S1_ideal
  feed: delta_gap
  ground: free_space
O: [gain_error_dB, impedance_error_pct, pattern_correlation]
epsilon:
  gain_error_max_dB: 0.3
  impedance_error_max_pct: 5.0
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Exact geometry + feed | None | gain err ≤ 0.3 dB |
| S2 Mismatch | ±2mm length error | Δℓ | gain err ≤ 1.0 dB |
| S3 Oracle | True length given | Known Δℓ | gain err ≤ 0.5 dB |
| S4 Blind Cal | Estimate length from S11 | Self-cal | recovery ≥ 85% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: antenna_patterns
  cases: 8  # dipole, monopole, patch, Yagi, array
  analytical_ref: dipole_theory, cavity_model
baselines:
  - solver: MoM_NEC
    gain_err_dB: 0.2
    Z_err_pct: 3.0
  - solver: FDTD_antenna
    gain_err_dB: 0.4
    Z_err_pct: 5.0
quality_scoring:
  metric: gain_error_dB
  thresholds:
    - {max: 0.1, Q: 1.00}
    - {max: 0.2, Q: 0.90}
    - {max: 0.3, Q: 0.80}
    - {max: 1.0, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | Gain err | Z err | Q | Reward |
|--------|---------|-------|---|--------|
| MoM_NEC | 0.2 dB | 3% | 0.90 | 270 PWM |
| FDTD_antenna | 0.4 dB | 5% | 0.75 | 225 PWM |
| FEM_HFSS_style | 0.08 dB | 1.5% | 1.00 | 300 PWM |

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q PWM
```

### Certificate

```json
{
  "principle": 236,
  "r": {"residual_norm": 0.008, "error_bound": 0.03, "ratio": 0.27},
  "c": {"resolutions": [100,200,400], "fitted_rate": 2.0, "theoretical_rate": 2.0},
  "Q": 0.90,
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
| L4 Solution | — | 225–300 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep antenna
pwm-node mine antenna/dipole_s1_ideal.yaml
```
