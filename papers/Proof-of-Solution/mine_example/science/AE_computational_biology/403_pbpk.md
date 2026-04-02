# Principle #403 — PBPK (Physiologically-Based Pharmacokinetics)

**Domain:** Computational Biology | **Carrier:** tissue drug concentration | **Difficulty:** Advanced (δ=5)
**DAG:** N.reaction → ∂.time.implicit → ∫.volume |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.reaction→∂.time.implicit→∫.volume   PBPK-model   whole-body        stiff-ODE
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PBPK (PHYSIOL. PHARMACOKINETICS) P=(E,G,W,C)   Principle #403 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ V_t dC_t/dt = Q_t(C_art − C_t/K_p) − CL_t·C_t       │
│        │ V_b dC_art/dt = Σ_t Q_t(C_t/K_p − C_art) + dose_rate │
│        │ C_t = tissue concentration, C_art = arterial blood     │
│        │ Q_t = tissue blood flow, K_p = partition coefficient   │
│        │ Forward: given dose, physiology → C_t(t) for all organs│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.reaction] ──→ [∂.time.implicit] ──→ [∫.volume]      │
│        │ nonlinear  derivative  integrate                       │
│        │ V={N.reaction, ∂.time.implicit, ∫.volume}  A={N.reaction→∂.time.implicit, ∂.time.implicit→∫.volume}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (ODE system with physiological bounds)  │
│        │ Uniqueness: YES (Lipschitz for bounded rate constants) │
│        │ Stability: stiff (fast perfusion, slow elimination)    │
│        │ Mismatch: K_p prediction, inter-species scaling        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = fold-error = max(C_pred/C_obs, C_obs/C_pred)      │
│        │ q = method-dependent (stiff ODE solver)               │
│        │ T = {fold_error, AUC_ratio, Cmax_ratio, K_tissues}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Mass balance: Σ(V_t·C_t) + eliminated = dose; flow-limited consistent | PASS |
| S2 | Well-posed for positive flows and partition coefficients | PASS |
| S3 | LSODA/BDF handle stiffness from disparate organ perfusion rates | PASS |
| S4 | Fold-error computable against clinical PK data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# pbpk/whole_body_s1_ideal.yaml
principle_ref: sha256:<p403_hash>
omega:
  time: [0, 72.0]   # hours
  dt: adaptive
  organs: [lung, liver, kidney, gut, muscle, fat, brain, rest]
E:
  forward: "V_t dC_t/dt = Q_t(C_art − C_t/K_p) − CL_t·C_t"
  species: human
  body_weight: 70   # kg
B:
  initial: {all_C: 0.0}
I:
  scenario: oral_dose_human
  dose: 100   # mg
  drug: midazolam
  rtol_sizes: [1e-4, 1e-6, 1e-8]
O: [plasma_fold_error, AUC_ratio, Cmax_ratio]
epsilon:
  fold_error_max: 2.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 8 organ compartments cover major drug distribution tissues | PASS |
| S2 | Human physiological parameters well-characterized for midazolam | PASS |
| S3 | LSODA handles stiff perfusion/metabolism coupling | PASS |
| S4 | Fold-error < 2.0 achievable with validated K_p predictions | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# pbpk/benchmark_midazolam.yaml
spec_ref: sha256:<spec403_hash>
principle_ref: sha256:<p403_hash>
dataset:
  name: clinical_midazolam_PK
  reference: "Gertz et al. (2011) PBPK for CYP3A substrates"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Simcyp
    params: {virtual_pop: 100}
    results: {fold_err: 1.3, AUC_ratio: 1.15}
  - solver: PK-Sim
    params: {mechanistic_absorption: true}
    results: {fold_err: 1.4, AUC_ratio: 1.2}
  - solver: Custom-LSODA
    params: {rtol: 1e-8}
    results: {fold_err: 1.5, AUC_ratio: 1.25}
quality_scoring:
  - {max_fold: 1.25, Q: 1.00}
  - {max_fold: 1.5, Q: 0.90}
  - {max_fold: 2.0, Q: 0.80}
  - {max_fold: 3.0, Q: 0.75}
```

**Baseline solver:** Simcyp — fold error 1.3
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Fold Error | AUC Ratio | Runtime | Q |
|--------|-----------|----------|---------|---|
| Custom-LSODA | 1.5 | 1.25 | 0.5 s | 0.90 |
| PK-Sim | 1.4 | 1.20 | 5 s | 0.90 |
| Simcyp | 1.3 | 1.15 | 30 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case:  500 × 0.90 = 450 PWM
Floor:      500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p403_hash>",
  "h_s": "sha256:<spec403_hash>",
  "h_b": "sha256:<bench403_hash>",
  "r": {"fold_err": 1.3, "AUC_ratio": 1.15, "ratio": 0.52},
  "c": {"organs_validated": 8, "K": 3},
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
| L4 Solution | — | 375–450 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep pbpk
pwm-node verify AE_computational_biology/pbpk_s1_ideal.yaml
pwm-node mine AE_computational_biology/pbpk_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
