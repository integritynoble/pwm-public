# Principle #308 — Free Energy Perturbation / Thermodynamic Integration

**Domain:** Computational Chemistry | **Carrier:** N/A (statistical mechanics) | **Difficulty:** Hard (δ=5)
**DAG:** N.bilinear.pair → ∂.time.symplectic → ∫.ensemble |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          λ→S→E→A      fep-ti      binding-FE        alchemical
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  FREE ENERGY PERTURBATION / TI    P = (E,G,W,C)   Principle #308│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ FEP: ΔG = −k_BT ln⟨exp(−(U₁−U₀)/k_BT)⟩₀  (Zwanzig) │
│        │ TI:  ΔG = ∫₀¹ ⟨∂U/∂λ⟩_λ dλ  (Kirkwood)               │
│        │ U(λ) = (1−λ)U₀ + λU₁  (alchemical interpolation)     │
│        │ Forward: given end-states → compute ΔΔG_bind           │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.bilinear.pair] ──→ [∂.time.symplectic] ──→ [∫.ensemble] │
│        │ nonlinear  derivative  integrate                       │
│        │ V={N.bilinear.pair, ∂.time.symplectic, ∫.ensemble}  A={N.bilinear.pair→∂.time.symplectic, ∂.time.symplectic→∫.ensemble}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (thermodynamic identity)               │
│        │ Uniqueness: YES (state function, path independent)    │
│        │ Stability: phase-space overlap needed between λ windows│
│        │ Mismatch: insufficient sampling, end-point singularity │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |ΔΔG_calc − ΔΔG_exp| (kcal/mol)                  │
│        │ q = 1.0 (MD cost × N_λ windows)                      │
│        │ T = {ΔΔG, convergence, overlap_matrix, hysteresis}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Zwanzig/Kirkwood identities thermodynamically exact | PASS |
| S2 | Soft-core potentials eliminate end-point singularities | PASS |
| S3 | MBAR estimator converges for >10 λ windows with 5 ns each | PASS |
| S4 | ΔΔG error < 1 kcal/mol for congeneric ligand series | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# fep_ti/binding_s1_ideal.yaml
principle_ref: sha256:<p308_hash>
omega:
  lambda_windows: 20
  simulation_per_window: 5.0  # ns
  dt: 2.0  # fs
E:
  forward: "alchemical TI with soft-core LJ"
  force_field: AMBER_ff14SB + GAFF2
  water_model: TIP3P
  estimator: MBAR
B:
  ensemble: NPT
  temperature: 298  # K
  pressure: 1.0  # bar
  restraints: Boresch
I:
  scenario: Tyk2_congeneric_series
  ligand_pairs: 10
  reference: experimental_IC50_converted_ΔG
O: [RMSE_kcal, MAE_kcal, correlation_R2]
epsilon:
  RMSE_max: 1.0  # kcal/mol
  R2_min: 0.60
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 20 λ windows × 5 ns = 100 ns total per edge; soft-core defined | PASS |
| S2 | MBAR optimal estimator; overlap matrix checked | PASS |
| S3 | Convergence verified by block averaging and forward/reverse | PASS |
| S4 | RMSE < 1 kcal/mol for Tyk2 series achievable | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# fep_ti/benchmark_tyk2.yaml
spec_ref: sha256:<spec308_hash>
principle_ref: sha256:<p308_hash>
dataset:
  name: Tyk2_FEP_benchmark
  reference: "Wang et al. (2015) FEP+ benchmark"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: TI-AMBER
    params: {windows: 12, time: 2ns}
    results: {RMSE: 1.5, MAE: 1.2, R2: 0.55}
  - solver: FEP-MBAR
    params: {windows: 20, time: 5ns}
    results: {RMSE: 0.85, MAE: 0.65, R2: 0.72}
  - solver: FEP+-Schrodinger
    params: {windows: 24, REST2: true}
    results: {RMSE: 0.65, MAE: 0.50, R2: 0.82}
quality_scoring:
  - {min_RMSE: 0.5, Q: 1.00}
  - {min_RMSE: 0.8, Q: 0.90}
  - {min_RMSE: 1.2, Q: 0.80}
  - {min_RMSE: 2.0, Q: 0.75}
```

**Baseline solver:** FEP-MBAR — RMSE 0.85 kcal/mol
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | RMSE (kcal/mol) | R² | Runtime | Q |
|--------|-----------------|-----|---------|---|
| TI-AMBER (12λ) | 1.5 | 0.55 | 24 h | 0.80 |
| FEP-MBAR (20λ) | 0.85 | 0.72 | 48 h | 0.90 |
| FEP+ (24λ+REST2) | 0.65 | 0.82 | 72 h | 0.90 |
| FEP+REST2+long | 0.45 | 0.88 | 120 h | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (REST2+long): 500 × 1.00 = 500 PWM
Floor:                  500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p308_hash>",
  "h_s": "sha256:<spec308_hash>",
  "h_b": "sha256:<bench308_hash>",
  "r": {"residual_norm": 0.45, "error_bound": 1.0, "ratio": 0.45},
  "c": {"fitted_rate": 0.98, "theoretical_rate": 1.0, "K": 4},
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
pwm-node benchmarks | grep fep_ti
pwm-node verify fep_ti/binding_s1_ideal.yaml
pwm-node mine fep_ti/binding_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
