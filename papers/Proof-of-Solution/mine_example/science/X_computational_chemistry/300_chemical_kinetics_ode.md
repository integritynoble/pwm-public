# Principle #300 — Chemical Kinetics ODE System

**Domain:** Computational Chemistry | **Carrier:** N/A (ODE-based) | **Difficulty:** Standard (δ=3)
**DAG:** N.reaction → ∂.time.implicit |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.reaction→∂.time.implicit      chem-kin    stiff-reaction     BDF/CVODE
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CHEMICAL KINETICS ODE SYSTEM     P = (E,G,W,C)   Principle #300│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ dc_i/dt = Σ ν_ij r_j(c,T)  (species balance ODEs)     │
│        │ r_j = k_j(T) Π c_i^α_ij  (mass-action rate law)       │
│        │ k_j(T) = A_j T^n exp(−E_a/RT)  (Arrhenius)            │
│        │ Forward: given {k_j}, c(0) → c(t) time profiles       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.reaction] ──→ [∂.time.implicit]                     │
│        │ nonlinear  derivative                                  │
│        │ V={N.reaction, ∂.time.implicit}  A={N.reaction→∂.time.implicit}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Lipschitz for bounded concentrations)  │
│        │ Uniqueness: YES (Picard-Lindelof theorem)              │
│        │ Stability: stiff systems require implicit methods      │
│        │ Mismatch: rate constant uncertainty, mechanism errors  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖c_num − c_ref‖₂ / ‖c_ref‖₂ (concentration error)│
│        │ q = varies by order (BDF up to 5th order)             │
│        │ T = {concentration_profiles, stiffness_ratio, mass_bal}│
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Stoichiometry matrix ν consistent; mass conservation checked | PASS |
| S2 | ODE system satisfies Picard-Lindelof for c ≥ 0 | PASS |
| S3 | CVODE/LSODA converge for stiffness ratios up to 10¹⁰ | PASS |
| S4 | Concentration error bounded by tolerance and method order | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# chem_kin/stiff_s1_ideal.yaml
principle_ref: sha256:<p300_hash>
omega:
  species: 9
  reactions: 25
  time: [0, 1.0]  # seconds
  dt: adaptive
E:
  forward: "ODE system dc/dt = S · r(c,T)"
  temperature: 1500  # K (fixed)
  mechanism: H2_O2_detailed
B:
  initial: {H2: 2.0, O2: 1.0, others: 0.0}  # mol/m³
  pressure: 1.0e5  # Pa
I:
  scenario: H2_O2_ignition
  stiffness_ratio: 1.0e8
  reference: Cantera_SUNDIALS
O: [concentration_L2, ignition_delay, mass_conservation]
epsilon:
  L2_error_max: 1.0e-6
  mass_balance_max: 1.0e-12
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 9 species, 25 reactions; stoichiometry balanced | PASS |
| S2 | Stiffness ratio 10⁸ handled by implicit BDF | PASS |
| S3 | CVODE converges with adaptive dt from 10⁻¹² to 10⁻³ s | PASS |
| S4 | L2 error < 10⁻⁶ with rtol=1e-8, atol=1e-12 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# chem_kin/benchmark_h2o2.yaml
spec_ref: sha256:<spec300_hash>
principle_ref: sha256:<p300_hash>
dataset:
  name: H2_O2_ignition_Cantera
  reference: "Cantera with GRI-Mech 3.0 subset"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Explicit-RK45
    params: {rtol: 1e-6, atol: 1e-10}
    results: {L2_error: 5.2e-4, steps: 125000}
  - solver: LSODA
    params: {rtol: 1e-8, atol: 1e-12}
    results: {L2_error: 8.5e-7, steps: 850}
  - solver: CVODE-BDF
    params: {rtol: 1e-8, atol: 1e-12, order: 5}
    results: {L2_error: 3.2e-7, steps: 620}
quality_scoring:
  - {min_L2: 1.0e-8, Q: 1.00}
  - {min_L2: 1.0e-6, Q: 0.90}
  - {min_L2: 1.0e-4, Q: 0.80}
  - {min_L2: 1.0e-2, Q: 0.75}
```

**Baseline solver:** CVODE-BDF — L2 error 3.2×10⁻⁷
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Steps | Runtime | Q |
|--------|----------|-------|---------|---|
| RK45 (explicit) | 5.2e-4 | 125000 | 5 s | 0.80 |
| LSODA | 8.5e-7 | 850 | 0.05 s | 0.90 |
| CVODE-BDF | 3.2e-7 | 620 | 0.03 s | 0.90 |
| CVODE-BDF (tight) | 5.0e-9 | 1200 | 0.06 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (tight BDF): 300 × 1.00 = 300 PWM
Floor:                 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p300_hash>",
  "h_s": "sha256:<spec300_hash>",
  "h_b": "sha256:<bench300_hash>",
  "r": {"residual_norm": 5.0e-9, "error_bound": 1.0e-6, "ratio": 0.005},
  "c": {"fitted_rate": 4.95, "theoretical_rate": 5.0, "K": 3},
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
pwm-node benchmarks | grep chem_kin
pwm-node verify chem_kin/stiff_s1_ideal.yaml
pwm-node mine chem_kin/stiff_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
