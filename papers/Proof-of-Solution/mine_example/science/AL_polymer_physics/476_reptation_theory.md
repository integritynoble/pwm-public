# Principle #476 — Reptation Theory (Doi-Edwards)

**Domain:** Polymer Physics | **Carrier:** N/A (stochastic/analytical) | **Difficulty:** Standard (δ=3)
**DAG:** [N.pointwise] --> [∫.temporal] --> [O.l2] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pw-->∫.temp-->O.l2  Reptation  entangled-melt  tube-model
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  REPTATION THEORY (DOI-EDWARDS) P = (E,G,W,C)  Principle #476  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ τ_d = L²/(π²D_c)  (disengagement / reptation time)    │
│        │ D_c = k_BT/(Nζ)   (curvilinear diffusion)             │
│        │ G(t) = G_N⁰ Σ (8/p²π²) exp(−p²t/τ_d)  (stress relax)│
│        │ η₀ = (π²/12) G_N⁰ τ_d ∝ N³·⁴  (zero-shear viscosity)│
│        │ Forward: given (N, ζ, a, G_N⁰) → G(t), η₀, D_self    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pw] ──→ [∫.temp] ──→ [O.l2]                         │
│        │  tube-model  relaxation  rheology-fit                  │
│        │ V={N.pw,∫.temp,O.l2}  A={N.pw→∫.temp,∫.temp→O.l2}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (analytic series solution for G(t))     │
│        │ Uniqueness: YES for given tube model parameters        │
│        │ Stability: series converges; modes decay exponentially │
│        │ Mismatch: CLF and constraint release modify scaling    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖G_pred(t)−G_expt(t)‖/‖G_expt(t)‖ (relaxation)  │
│        │ q = N/A (analytical + corrections)                    │
│        │ T = {G_t_error, viscosity_error, diffusion_error}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Tube parameters (a, N_e, G_N⁰) physically consistent | PASS |
| S2 | Series for G(t) converges; τ_d well-defined for N >> N_e | PASS |
| S3 | Pure reptation + CLF corrections match η ∝ N^3.4 | PASS |
| S4 | G(t) prediction within 10% of experiment for monodisperse | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# reptation/entangled_melt_s1.yaml
principle_ref: sha256:<p476_hash>
omega:
  molecular_weights: [50k, 100k, 200k, 500k]
  domain: polyethylene_melt
  temperature: 450   # K
E:
  forward: "reptation + CLF + constraint release → G(t), η₀"
  tube_diameter: 4.8e-9   # m
  entanglement_MW: 1200    # g/mol
  plateau_modulus: 2.6e6   # Pa
B:
  conditions: equilibrium_melt
  strain: linear_viscoelastic_regime
I:
  scenario: monodisperse_PE_relaxation
  models: [pure_reptation, reptation_CLF, Likhtman_McLeish]
O: [G_t_error, viscosity_error, diffusion_scaling]
epsilon:
  G_t_error_max: 0.10
  viscosity_error_max: 0.15
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | MW range spans 40-400 entanglements; T above melt | PASS |
| S2 | Entangled regime ensures tube model validity | PASS |
| S3 | All three models produce convergent G(t) | PASS |
| S4 | η₀ prediction within 15% of experiment | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# reptation/benchmark_pe_melt.yaml
spec_ref: sha256:<spec476_hash>
principle_ref: sha256:<p476_hash>
dataset:
  name: PE_melt_rheology
  reference: "Likhtman & McLeish (2002) quantitative tube model"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Pure reptation (Doi-Edwards)
    params: {CLF: false, CR: false}
    results: {G_t_error: 0.25, viscosity_error: 0.40}
  - solver: Reptation + CLF
    params: {CLF: true, CR: false}
    results: {G_t_error: 0.12, viscosity_error: 0.18}
  - solver: Likhtman-McLeish (full)
    params: {CLF: true, CR: true}
    results: {G_t_error: 0.05, viscosity_error: 0.08}
quality_scoring:
  - {min_err: 0.03, Q: 1.00}
  - {min_err: 0.08, Q: 0.90}
  - {min_err: 0.15, Q: 0.80}
  - {min_err: 0.30, Q: 0.75}
```

**Baseline solver:** Reptation + CLF — G(t) error 12%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | G(t) Error | η₀ Error | Runtime | Q |
|--------|-----------|----------|---------|---|
| Pure reptation | 0.25 | 0.40 | 0.01 s | 0.75 |
| Reptation + CLF | 0.12 | 0.18 | 0.05 s | 0.80 |
| Likhtman-McLeish | 0.05 | 0.08 | 0.5 s | 0.90 |
| Slip-link simulation | 0.03 | 0.04 | 300 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (slip-link): 300 × 1.00 = 300 PWM
Floor:                 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p476_hash>",
  "h_s": "sha256:<spec476_hash>",
  "h_b": "sha256:<bench476_hash>",
  "r": {"G_t_error": 0.03, "error_bound": 0.10, "ratio": 0.300},
  "c": {"viscosity_error": 0.04, "MW_tested": 4, "K": 4},
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
pwm-node benchmarks | grep reptation
pwm-node verify reptation/entangled_melt_s1.yaml
pwm-node mine reptation/entangled_melt_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
