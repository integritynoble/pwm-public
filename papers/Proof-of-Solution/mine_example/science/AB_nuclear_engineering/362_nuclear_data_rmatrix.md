# Principle #362 — Nuclear Data Evaluation (R-matrix)

**Domain:** Nuclear Engineering | **Carrier:** cross-section | **Difficulty:** Advanced (δ=5)
**DAG:** E.hermitian → N.reaction → L.dense |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E.hermitian→N.reaction→L.dense   R-matrix     U235-resonance    SAMMY/fit
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  NUCLEAR DATA EVALUATION (R-MATRIX) P = (E,G,W,C) Princ. #362  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ σ(E) = πg λ² |Σ_λ γ_λc γ_λc' / (E_λ − E − iΓ_λ/2)|²│
│        │ R-matrix: U = I + 2i P^{1/2} (I − RL)^{-1} R P^{1/2} │
│        │ R_cc' = Σ_λ γ_λc γ_λc' / (E_λ − E)                   │
│        │ Forward: given resonance params {E_λ, Γ_λ} → σ(E)     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [E.hermitian] ──→ [N.reaction] ──→ [L.dense]           │
│        │ eigensolve  nonlinear  linear-op                       │
│        │ V={E.hermitian, N.reaction, L.dense}  A={E.hermitian→N.reaction, N.reaction→L.dense}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (R-matrix is complete representation)   │
│        │ Uniqueness: NO (parameter ambiguities; level-density)  │
│        │ Stability: CONDITIONAL (ill-conditioned near overlapping)│
│        │ Mismatch: background R-matrix, channel radius choice   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = χ²/N (goodness of fit to experimental data)        │
│        │ q = N/A (nonlinear least-squares, not mesh convergence)│
│        │ T = {chi2_per_dof, covariance_matrix, K_energy_ranges} │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Cross-section dimensions [barn]; resonance parameters consistent | PASS |
| S2 | R-matrix formalism complete for compound nucleus reactions | PASS |
| S3 | SAMMY/REFIT Bayesian fitting converges for resolved resonances | PASS |
| S4 | χ²/N measurable against experimental transmission/capture data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# nuclear_data/u235_rmatrix_s1_ideal.yaml
principle_ref: sha256:<p362_hash>
omega:
  energy_range: [1.0e-5, 20.0]   # eV (thermal to 20 eV)
  nuclide: U-235
  channels: [elastic, fission, capture]
  num_resonances: 50
E:
  forward: "Reich-Moore R-matrix → σ_n, σ_f, σ_γ"
  formalism: Reich-Moore
B:
  boundary: {channel_radius: 0.948e-12}   # cm
I:
  scenario: resolved_resonance_evaluation
  data_source: EXFOR
  energy_points: 10000
O: [chi2_per_dof, resonance_integral_error]
epsilon:
  chi2_max: 1.5
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 50 resonances cover 0-20 eV for U-235; channels complete | PASS |
| S2 | Reich-Moore handles fission channel adequately | PASS |
| S3 | SAMMY Bayesian fit converges with analytic derivatives | PASS |
| S4 | χ²/N < 1.5 achievable for high-quality transmission data | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# nuclear_data/benchmark_u235.yaml
spec_ref: sha256:<spec362_hash>
principle_ref: sha256:<p362_hash>
dataset:
  name: ORELA_U235_transmission
  reference: "Harvey et al. U-235 transmission at ORELA"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: SAMMY-Bayes
    params: {resonances: 50, iterations: 20}
    results: {chi2: 1.2, RI_err: 0.8e-2}
  - solver: REFIT
    params: {resonances: 50}
    results: {chi2: 1.3, RI_err: 1.0e-2}
  - solver: CONRAD
    params: {resonances: 50, marginalization: true}
    results: {chi2: 1.1, RI_err: 0.6e-2}
quality_scoring:
  - {max_chi2: 1.0, Q: 1.00}
  - {max_chi2: 1.2, Q: 0.90}
  - {max_chi2: 1.5, Q: 0.80}
  - {max_chi2: 2.0, Q: 0.75}
```

**Baseline solver:** SAMMY-Bayes — χ²/N = 1.2
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | χ²/N | RI Error | Runtime | Q |
|--------|------|----------|---------|---|
| REFIT | 1.3 | 1.0% | 30 s | 0.80 |
| SAMMY-Bayes | 1.2 | 0.8% | 60 s | 0.90 |
| CONRAD-marginal | 1.1 | 0.6% | 120 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (CONRAD): 500 × 0.90 = 450 PWM
Floor:              500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p362_hash>",
  "h_s": "sha256:<spec362_hash>",
  "h_b": "sha256:<bench362_hash>",
  "r": {"chi2": 1.1, "RI_err": 0.006, "ratio": 0.73},
  "c": {"num_resonances": 50, "iterations": 20, "K": 3},
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
pwm-node benchmarks | grep nuclear_data
pwm-node verify AB_nuclear_engineering/nuclear_data_rmatrix_s1_ideal.yaml
pwm-node mine AB_nuclear_engineering/nuclear_data_rmatrix_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
