# Principle #357 — Reactor Point Kinetics

**Domain:** Nuclear Engineering | **Carrier:** neutron population | **Difficulty:** Standard (δ=3)
**DAG:** N.reaction.fission → ∂.time |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.reaction.fission→∂.time      pt-kinetics  step-reactivity   ODE-stiff
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  REACTOR POINT KINETICS         P = (E,G,W,C)   Principle #357  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ dn/dt = (ρ−β)/Λ · n + Σ_i λ_i C_i + S               │
│        │ dC_i/dt = β_i/Λ · n − λ_i C_i   (i=1..6 groups)     │
│        │ n = neutron population, C_i = delayed precursor conc.  │
│        │ ρ = reactivity, Λ = prompt neutron lifetime            │
│        │ Forward: given ρ(t), Λ, β_i, λ_i → solve n(t), C_i(t)│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.reaction.fission] ──→ [∂.time]                      │
│        │ nonlinear  derivative                                  │
│        │ V={N.reaction.fission, ∂.time}  A={N.reaction.fission→∂.time}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear ODE system with bounded coeffs) │
│        │ Uniqueness: YES (Lipschitz continuous RHS)             │
│        │ Stability: stiff system (Λ ~ 10⁻⁵ s); needs implicit  │
│        │ Mismatch: reactivity insertion rate, β_eff uncertainty  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative error |n(t)−n_ref(t)|/n_ref(t)           │
│        │ q = 2.0 (implicit trapezoid), 4.0 (RK4-implicit)     │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | n and C_i dimensions consistent; β = Σβ_i constraint satisfied | PASS |
| S2 | Linear ODE system — unique solution by Picard-Lindelof | PASS |
| S3 | Stiff ODE solvers (BDF, implicit RK) converge for Λ ~ 10⁻⁵ | PASS |
| S4 | Relative error computable against Inhour analytic solution | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# point_kinetics/step_reactivity_s1_ideal.yaml
principle_ref: sha256:<p357_hash>
omega:
  time: [0, 10.0]
  dt: 1.0e-4
  delayed_groups: 6
E:
  forward: "dn/dt = (ρ−β)/Λ·n + Σλ_iC_i; dC_i/dt = β_i/Λ·n − λ_iC_i"
  Lambda: 1.0e-5
  beta_eff: 0.0065
B:
  initial: {n0: 1.0, C_i0: equilibrium}
I:
  scenario: step_reactivity_insertion
  rho_step: 0.003   # ~$0.46 reactivity
  mesh_sizes_dt: [1e-3, 1e-4, 1e-5]
O: [n_relative_error, precursor_error]
epsilon:
  n_error_max: 1.0e-5
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 6 delayed groups standard; dt=10⁻⁴ resolves prompt jump | PASS |
| S2 | Sub-prompt-critical insertion (ρ < β) — bounded response | PASS |
| S3 | BDF-2 converges for stiff system at O(dt²) | PASS |
| S4 | n error < 10⁻⁵ achievable with dt=10⁻⁵ | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# point_kinetics/benchmark_step_rho.yaml
spec_ref: sha256:<spec357_hash>
principle_ref: sha256:<p357_hash>
dataset:
  name: Inhour_step_reactivity
  reference: "Analytic Inhour equation solution for step ρ insertion"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Euler-implicit
    params: {dt: 1e-4}
    results: {n_error: 8.5e-3, max_error: 1.2e-2}
  - solver: BDF-2
    params: {dt: 1e-4}
    results: {n_error: 3.1e-4, max_error: 5.8e-4}
  - solver: CRAM (Chebyshev Rational)
    params: {order: 16, dt: 1e-3}
    results: {n_error: 2.0e-6, max_error: 5.1e-6}
quality_scoring:
  - {min_err: 1.0e-6, Q: 1.00}
  - {min_err: 1.0e-4, Q: 0.90}
  - {min_err: 1.0e-3, Q: 0.80}
  - {min_err: 1.0e-2, Q: 0.75}
```

**Baseline solver:** BDF-2 — n error 3.1×10⁻⁴
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | n Error | Max Error | Runtime | Q |
|--------|---------|-----------|---------|---|
| Euler-implicit | 8.5e-3 | 1.2e-2 | 0.1 s | 0.75 |
| BDF-2 | 3.1e-4 | 5.8e-4 | 0.3 s | 0.90 |
| CRAM-16 | 2.0e-6 | 5.1e-6 | 0.2 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (CRAM): 300 × 1.00 = 300 PWM
Floor:            300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p357_hash>",
  "h_s": "sha256:<spec357_hash>",
  "h_b": "sha256:<bench357_hash>",
  "r": {"residual_norm": 2.0e-6, "error_bound": 1.0e-5, "ratio": 0.20},
  "c": {"fitted_rate": 2.02, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep point_kinetics
pwm-node verify AB_nuclear_engineering/point_kinetics_s1_ideal.yaml
pwm-node mine AB_nuclear_engineering/point_kinetics_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
