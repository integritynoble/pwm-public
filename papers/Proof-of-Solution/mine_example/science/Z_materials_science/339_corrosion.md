# Principle #339 — Corrosion Modeling

**Domain:** Materials Science | **Carrier:** corrosion current | **Difficulty:** Standard (δ=3)
**DAG:** N.reaction → ∂.time → ∂.space |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E→i→c→η     corrosion   Fe-acid-BV         FEM/analytic
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CORROSION MODELING             P = (E,G,W,C)   Principle #339 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ i = i₀[exp(αₐFη/RT) − exp(−αcFη/RT)] (Butler-Volmer) │
│        │ η = E − E_eq  (overpotential)                         │
│        │ ∂c/∂t = D∇²c  (mass transport in electrolyte)        │
│        │ Forward: given E_corr, i₀, environment → corrosion rate│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.reaction] ──→ [∂.time] ──→ [∂.space]                │
│        │ nonlinear  derivative  derivative                      │
│        │ V={N.reaction, ∂.time, ∂.space}  A={N.reaction→∂.time, ∂.time→∂.space}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (coupled ODE/PDE system)                │
│        │ Uniqueness: YES (for given kinetic and transport params)│
│        │ Stability: steady-state corrosion potential stable     │
│        │ Mismatch: i₀ uncertainty, passive film, pH gradients   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |i_corr^sim − i_corr^expt|/i_corr (primary)      │
│        │ q = 2.0 (FEM for transport-limited case)             │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Butler-Volmer kinetics and Fick's law dimensionally consistent | PASS |
| S2 | Mixed-potential theory gives unique E_corr | PASS |
| S3 | Newton-Raphson for BV + FEM for transport converge | PASS |
| S4 | Corrosion current density measurable via polarization curves | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# corrosion/fe_acid_s1_ideal.yaml
principle_ref: sha256:<p339_hash>
omega:
  grid: [100]
  domain: [0, 0.01]  # 1 cm diffusion layer
  time: steady_state
E:
  forward: "Butler-Volmer kinetics + diffusion transport"
  kinetics: Butler_Volmer
B:
  electrode: {material: Fe, E_eq: -0.44}  # V vs SHE
  solution: {pH: 2, O2: 0.21}
I:
  scenario: iron_acid_corrosion
  i0_Fe: 1.0e-5  # A/cm²
  i0_H2: 1.0e-3  # A/cm²
  alpha_a: 0.5
  alpha_c: 0.5
O: [E_corr, i_corr, polarization_curve]
epsilon:
  i_corr_rel_error: 0.10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Diffusion layer resolved; BV parameters physical | PASS |
| S2 | Mixed-potential theory yields unique E_corr, i_corr | PASS |
| S3 | Newton-Raphson converges for BV intersection | PASS |
| S4 | i_corr within 10% of Tafel extrapolation from experiment | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# corrosion/benchmark_fe_acid.yaml
spec_ref: sha256:<spec339_hash>
principle_ref: sha256:<p339_hash>
dataset:
  name: fe_acid_polarization
  reference: "Stern & Geary (1957) polarization resistance"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Tafel extrapolation
    params: {analytic: true}
    results: {i_corr_error: 0.05}
  - solver: BV + diffusion (FEM)
    params: {N: 100}
    results: {i_corr_error: 0.08}
  - solver: COMSOL (corrosion module)
    params: {mesh: fine}
    results: {i_corr_error: 0.06}
quality_scoring:
  - {min_i_corr_error: 0.02, Q: 1.00}
  - {min_i_corr_error: 0.05, Q: 0.90}
  - {min_i_corr_error: 0.10, Q: 0.80}
  - {min_i_corr_error: 0.20, Q: 0.75}
```

**Baseline solver:** Tafel extrapolation — i_corr error 5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | i_corr Error | Runtime | Q |
|--------|-------------|---------|---|
| BV + diffusion (FEM) | 0.08 | 1 s | 0.80 |
| COMSOL | 0.06 | 10 s | 0.90 |
| Tafel extrapolation | 0.05 | 0.01 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case: 300 × 0.90 = 270 PWM
Floor:     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p339_hash>",
  "h_s": "sha256:<spec339_hash>",
  "h_b": "sha256:<bench339_hash>",
  "r": {"residual_norm": 0.05, "error_bound": 0.10, "ratio": 0.50},
  "c": {"fitted_rate": 2.0, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.90,
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
| L4 Solution | — | 225–270 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep corrosion
pwm-node verify corrosion/fe_acid_s1_ideal.yaml
pwm-node mine corrosion/fe_acid_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
