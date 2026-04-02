# Principle #329 — CALPHAD (Computational Thermodynamics)

**Domain:** Materials Science | **Carrier:** phase equilibrium | **Difficulty:** Standard (δ=3)
**DAG:** N.pointwise → O.l2 → ∫.ensemble |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pointwise→O.l2→∫.ensemble    CALPHAD     Fe-C-phase-diag    Gibbs-min
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CALPHAD (COMP. THERMODYNAMICS) P = (E,G,W,C)   Principle #329 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ min_φ Σ_φ n_φ G_φ(T,P,x)  s.t. mass balance          │
│        │ G_φ = G_ref + G_ideal_mix + G_excess (Redlich-Kister)  │
│        │ Equilibrium: μ_i^α = μ_i^β for all components i       │
│        │ Forward: given T, P, composition → compute phase fractions│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G] ──→ [∂G] ──→ [μ] ──→ [X_eq] ──→ [G]              │
│        │ Gibbs  derivative  chem-pot  equilibrium  repeat       │
│        │ V={G,∂G,μ,X_eq}  A={G→∂G,∂G→μ,μ→X_eq,X_eq→G}         │
│        │ L_DAG=3.0                                              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (convex hull of Gibbs energies)         │
│        │ Uniqueness: YES (global minimum unique for convex G)   │
│        │ Stability: common tangent construction geometrically stable│
│        │ Mismatch: database parameter uncertainty, metastable phases│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |T_boundary^calc − T_boundary^expt| (primary, K)  │
│        │ q = exact (optimization convergence)                  │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Gibbs energy models thermodynamically consistent | PASS |
| S2 | Global Gibbs minimization has unique solution | PASS |
| S3 | Newton-Raphson/global optimization converges | PASS |
| S4 | Phase boundary temperatures measurable against experiments | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# calphad/fe_c_s1_ideal.yaml
principle_ref: sha256:<p329_hash>
omega:
  T_range: [300, 2000]  # K
  composition: {C: [0, 0.067]}  # weight fraction
  P: 101325  # Pa
E:
  forward: "min G(T,x) over all phase combinations"
  database: TCFE
B:
  phases: [BCC_A2, FCC_A1, Cementite, Liquid]
I:
  scenario: Fe-C_binary_phase_diagram
  reference_boundaries: {A1: 996, A3: "composition-dependent", eutectic: 1420}
O: [phase_boundaries, phase_fractions, liquidus_solidus]
epsilon:
  boundary_T_error_max: 5.0  # K
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Fe-C system with 4 phases; T and composition ranges adequate | PASS |
| S2 | Fe-C phase diagram well-established experimentally | PASS |
| S3 | Global minimization converges for given database | PASS |
| S4 | Phase boundary error < 5 K achievable with TCFE database | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# calphad/benchmark_fe_c.yaml
spec_ref: sha256:<spec329_hash>
principle_ref: sha256:<p329_hash>
dataset:
  name: Fe_C_experimental_phase_diagram
  reference: "ASM Handbook: Fe-C binary"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Thermo-Calc (TCFE)
    params: {database: TCFE12}
    results: {A1_error: 2, eutectic_error: 3}
  - solver: OpenCalphad
    params: {database: TCFE9}
    results: {A1_error: 5, eutectic_error: 8}
  - solver: FactSage
    params: {database: FSstel}
    results: {A1_error: 3, eutectic_error: 5}
quality_scoring:
  - {min_boundary_error: 1.0, Q: 1.00}
  - {min_boundary_error: 5.0, Q: 0.90}
  - {min_boundary_error: 10.0, Q: 0.80}
  - {min_boundary_error: 20.0, Q: 0.75}
```

**Baseline solver:** Thermo-Calc — A1 error 2 K
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | A1 Error (K) | Eutectic Error (K) | Runtime | Q |
|--------|-------------|-------------------|---------|---|
| OpenCalphad | 5 | 8 | 2 s | 0.90 |
| FactSage | 3 | 5 | 3 s | 0.90 |
| Thermo-Calc | 2 | 3 | 5 s | 0.90 |

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
  "h_p": "sha256:<p329_hash>",
  "h_s": "sha256:<spec329_hash>",
  "h_b": "sha256:<bench329_hash>",
  "r": {"residual_norm": 2.0, "error_bound": 5.0, "ratio": 0.40},
  "c": {"fitted_rate": "database", "theoretical_rate": "N/A", "K": 3},
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
pwm-node benchmarks | grep calphad
pwm-node verify calphad/fe_c_s1_ideal.yaml
pwm-node mine calphad/fe_c_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
