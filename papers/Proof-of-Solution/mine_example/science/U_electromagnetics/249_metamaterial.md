# Metamaterial Effective Medium — Four-Layer Walkthrough

**Principle #249 · Metamaterial Homogenization**
Domain: Electromagnetics & Optics | Carrier: photon/EM-field | Difficulty: hard (δ=5) | DAG: [∂.time] --> [∂.space.curl] --> [N.pointwise.drude] --> [O.adjoint]

---

## Four-Layer Pipeline

```
L1 seeds→Principle   L2 Principle→spec   L3 spec→Benchmark   L4 Bench→Solution
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ S-parameter      │→│ SRR / wire medium│→│ Full-wave unit   │→│ S-param retrieval│
│ retrieval, effec-│ │ unit cell config,│ │ cell sims, known │ │ / Bloch analysis │
│ tive ε_eff, μ_eff│ │ S1-S4 scenarios │ │ ε_eff, μ_eff     │ │ solver           │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Layer 1 — Principle

### Governing Equation

S-parameter retrieval: n_eff = (1/kd)cos⁻¹[(1−S₁₁²+S₂₁²)/(2S₂₁)]
z_eff = √[(1+S₁₁)²−S₂₁²]/[(1−S₁₁)²−S₂₁²]
ε_eff = n_eff/z_eff, μ_eff = n_eff·z_eff

### DAG

```
[∂.time] --> [∂.space.curl] --> [N.pointwise.drude] --> [O.adjoint]
time-stepping  curl-operators  Drude-dispersion  adjoint-optimization
```
V={∂.time,∂.space.curl,N.pointwise.drude,O.adjoint}  L_DAG=5.0

### Well-Posedness

| Property | Status | Justification |
|----------|--------|---------------|
| Existence | YES | S-parameters always computable for finite unit cell |
| Uniqueness | CONDITIONAL | Branch ambiguity in cos⁻¹; requires Kramers-Kronig |
| Stability | CONDITIONAL | Near resonance: S₂₁→0, retrieval ill-conditioned |

Mismatch: unit cell periodicity, spatial dispersion, higher-order modes

### Error Method

e = relative ε_eff, μ_eff error; q = 2.0 (mesh convergence)

---

## Layer 2 — spec.md

```yaml
principle_ref: "Principle #249"
omega:
  unit_cell: SRR_wire
  period_mm: 3.0
  freq_GHz: [4, 12]
E:
  forward: "NRW retrieval: eps_eff, mu_eff from S11, S21"
I:
  scenario: S1_ideal
O: [eps_eff_error_pct, mu_eff_error_pct, n_eff_error]
epsilon:
  eps_eff_error_max_pct: 5.0
  mu_eff_error_max_pct: 5.0
```

### S1-S4 Table

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Converged full-wave | None | ε err ≤ 5% |
| S2 Mismatch | Coarse mesh | Discretization | ε err ≤ 15% |
| S3 Oracle | Fine mesh reference | Known correction | ε err ≤ 7% |
| S4 Blind Cal | Adaptive mesh refinement | Auto | recovery ≥ 80% |

---

## Layer 3 — Benchmark

```yaml
dataset:
  name: metamaterial_retrieval
  cases: 8  # SRR, wire, fishnet, chiral
  ref: published_retrieval_results
baselines:
  - solver: FDTD_NRW
    eps_err_pct: 3.0
  - solver: FEM_Bloch
    eps_err_pct: 2.0
quality_scoring:
  metric: eps_eff_error_pct
  thresholds:
    - {max: 1.0, Q: 1.00}
    - {max: 3.0, Q: 0.90}
    - {max: 5.0, Q: 0.80}
    - {max: 15.0, Q: 0.75}
```

---

## Layer 4 — Solution

| Solver | ε err | Time | Q | Reward |
|--------|-------|------|---|--------|
| FDTD_NRW | 3% | 300s | 0.90 | 450 PWM |
| FEM_Bloch | 2% | 600s | 0.90 | 450 PWM |
| spectral_Bloch | 0.8% | 900s | 1.00 | 500 PWM |

```
R = 100 × 1.0 × 5 × 1.0 × Q = 500 × Q PWM
```

### Certificate

```json
{
  "principle": 249,
  "r": {"residual_norm": 0.02, "error_bound": 0.05, "ratio": 0.40},
  "c": {"resolutions": [10,20,40], "fitted_rate": 2.0, "theoretical_rate": 2.0},
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
| L4 Solution | — | 450–500 PWM each |

## Quick-Start

```bash
pwm-node benchmarks | grep metamaterial
pwm-node mine metamaterial/srr_s1_ideal.yaml
```
