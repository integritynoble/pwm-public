# Principle #358 — Burnup/Depletion (Bateman Equations)

**Domain:** Nuclear Engineering | **Carrier:** nuclide inventory | **Difficulty:** Advanced (δ=5)
**DAG:** N.reaction → ∂.time.implicit → ∫.temporal |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.reaction→∂.time.implicit→∫.temporal   bateman      UO2-burnup        CRAM/RK
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  BURNUP / DEPLETION (BATEMAN)   P = (E,G,W,C)   Principle #358 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ dN_i/dt = Σ_j (λ_j b_{ji} + σ_j φ y_{ji}) N_j       │
│        │          − (λ_i + σ_i φ) N_i                           │
│        │ N_i = atom density of nuclide i                        │
│        │ λ = decay constant, σ = one-group cross-section        │
│        │ Forward: given N(0), φ, σ, λ → solve N_i(t)           │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.reaction] ──→ [∂.time.implicit] ──→ [∫.temporal]    │
│        │ nonlinear  derivative  integrate                       │
│        │ V={N.reaction, ∂.time.implicit, ∫.temporal}  A={N.reaction→∂.time.implicit, ∂.time.implicit→∫.temporal}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (linear ODE system, bounded matrix)     │
│        │ Uniqueness: YES (matrix exponential is well-defined)   │
│        │ Stability: STIFF (decay constants span 10⁻¹⁸–10¹⁸ s⁻¹)│
│        │ Mismatch: one-group cross-section collapse, flux shape │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative error in nuclide densities |N−N_ref|/N_ref│
│        │ q = depends on method (CRAM: exponential convergence) │
│        │ T = {nuclide_errors, mass_conservation, K_timesteps}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Nuclide inventory dimensions consistent; branching ratios sum ≤ 1 | PASS |
| S2 | Linear ODE — matrix exponential exists for any burnup matrix | PASS |
| S3 | CRAM-16 converges for extremely stiff depletion chains | PASS |
| S4 | Nuclide density errors computable against ORIGEN reference | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# burnup/uo2_depletion_s1_ideal.yaml
principle_ref: sha256:<p358_hash>
omega:
  nuclides: 1600
  burnup_range: [0, 60]   # GWd/tHM
  power_density: 40.0     # kW/kgU
  time_steps: 50
E:
  forward: "dN/dt = A·N  (Bateman matrix, flux-weighted)"
  chain: ENDF-VIII.0_decay + JEFF-3.3_fission_yields
B:
  initial: {U235: 0.04, U238: 0.96}   # 4% enriched UO2
I:
  scenario: PWR_UO2_depletion
  burnup_steps: [0, 10, 20, 40, 60]
  mesh_sizes_dt: [1.0, 0.5, 0.1]   # days
O: [U235_error, Pu239_error, fission_product_error]
epsilon:
  nuclide_error_max: 0.01   # 1% relative
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1600 nuclides cover full actinide+FP chain; burnup range realistic | PASS |
| S2 | Bateman matrix well-posed; constant-flux approximation per step | PASS |
| S3 | CRAM-16 handles stiffness spanning 36 orders of magnitude | PASS |
| S4 | Nuclide errors < 1% achievable vs ORIGEN at 50 steps | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# burnup/benchmark_uo2.yaml
spec_ref: sha256:<spec358_hash>
principle_ref: sha256:<p358_hash>
dataset:
  name: SFCOMPO_UO2_PWR
  reference: "SFCOMPO spent fuel composition database"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: ORIGEN-S
    params: {substeps: 10}
    results: {U235_err: 0.8e-2, Pu239_err: 1.2e-2}
  - solver: CRAM-16
    params: {substeps: 1}
    results: {U235_err: 0.3e-2, Pu239_err: 0.5e-2}
  - solver: Runge-Kutta-DOPRI
    params: {rtol: 1e-8}
    results: {U235_err: 0.4e-2, Pu239_err: 0.6e-2}
quality_scoring:
  - {max_err: 0.005, Q: 1.00}
  - {max_err: 0.01, Q: 0.90}
  - {max_err: 0.02, Q: 0.80}
  - {max_err: 0.05, Q: 0.75}
```

**Baseline solver:** CRAM-16 — U235 error 0.3%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | U235 Error | Pu239 Error | Runtime | Q |
|--------|-----------|-------------|---------|---|
| ORIGEN-S | 0.8% | 1.2% | 5 s | 0.90 |
| CRAM-16 | 0.3% | 0.5% | 2 s | 1.00 |
| RK-DOPRI | 0.4% | 0.6% | 8 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (CRAM): 500 × 1.00 = 500 PWM
Floor:            500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p358_hash>",
  "h_s": "sha256:<spec358_hash>",
  "h_b": "sha256:<bench358_hash>",
  "r": {"U235_err": 0.003, "Pu239_err": 0.005, "mass_conservation": 1.0e-12},
  "c": {"substeps": 50, "K": 3},
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
| L4 Solution | — | 375–500 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep burnup
pwm-node verify AB_nuclear_engineering/burnup_depletion_s1_ideal.yaml
pwm-node mine AB_nuclear_engineering/burnup_depletion_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
