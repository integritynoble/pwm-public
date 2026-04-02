# Principle #409 — Phylogenetic Likelihood (Felsenstein)

**Domain:** Computational Biology | **Carrier:** site likelihood | **Difficulty:** Advanced (δ=5)
**DAG:** L.matrix_exp → ∫.path → O.ml |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.matrix_exp→∫.path→O.ml   Felsenstein   tree-likelihood   pruning
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PHYLOGENETIC LIKELIHOOD (FELS.) P = (E,G,W,C)  Principle #409 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ L(τ,θ|D) = Π_sites Σ_anc Π_edges P(s_j|s_i, t, Q)   │
│        │ P(t) = exp(Qt)  (substitution probability matrix)      │
│        │ Q = rate matrix (JC69, HKY, GTR)                       │
│        │ τ = tree topology, θ = branch lengths + rate params    │
│        │ Forward: given τ, θ, alignment D → log-likelihood      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.matrix_exp] ──→ [∫.path] ──→ [O.ml]                 │
│        │ linear-op  integrate  optimize                         │
│        │ V={L.matrix_exp, ∫.path, O.ml}  A={L.matrix_exp→∫.path, ∫.path→O.ml}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (likelihood well-defined for finite data)│
│        │ Uniqueness: NO (multiple local optima for topology)    │
│        │ Stability: numerically stable with log-scaling         │
│        │ Mismatch: model misspecification (wrong Q), rate hetero.│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |logL − logL_ref| (log-likelihood difference)     │
│        │ q = N/A (exact computation via pruning algorithm)     │
│        │ T = {logL_error, branch_length_error, topology_score}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Alignment matrix and tree topology dimensionally consistent | PASS |
| S2 | Felsenstein pruning computes exact likelihood for given tree | PASS |
| S3 | Pruning algorithm is O(n·k·s) — polynomial in taxa/sites | PASS |
| S4 | Log-likelihood difference computable against PAML/RAxML reference | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# phylogenetics/tree_likelihood_s1_ideal.yaml
principle_ref: sha256:<p409_hash>
omega:
  taxa: 50
  sites: 1000
  model: GTR+Gamma
  categories: 4
E:
  forward: "Felsenstein pruning: L = Π_sites Σ_anc Π_edges exp(Qt)"
  rate_matrix: GTR
  rate_heterogeneity: discrete_gamma
B:
  tree: {topology: known, branch_lengths: ML_optimized}
I:
  scenario: fixed_topology_likelihood
  models: [JC69, HKY, GTR, GTR+G4]
O: [logL_error, branch_length_RMSE]
epsilon:
  logL_error_max: 0.01
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 50 taxa, 1000 sites — moderate but representative dataset | PASS |
| S2 | Fixed topology — likelihood is a smooth function of branch lengths | PASS |
| S3 | Pruning algorithm exact; optimization converges for smooth L | PASS |
| S4 | logL error < 0.01 achievable (numerical precision limited) | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# phylogenetics/benchmark_tree.yaml
spec_ref: sha256:<spec409_hash>
principle_ref: sha256:<p409_hash>
dataset:
  name: simulated_GTR_alignment
  reference: "INDELible simulated alignment under GTR+G4"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: RAxML-v8
    params: {model: GTRGAMMA}
    results: {logL_err: 0.001, BL_RMSE: 2.0e-3}
  - solver: PhyML
    params: {model: GTR, gamma: 4}
    results: {logL_err: 0.005, BL_RMSE: 5.0e-3}
  - solver: IQ-TREE
    params: {model: GTR+G4}
    results: {logL_err: 0.0005, BL_RMSE: 1.5e-3}
quality_scoring:
  - {max_logL_err: 0.001, Q: 1.00}
  - {max_logL_err: 0.01, Q: 0.90}
  - {max_logL_err: 0.1, Q: 0.80}
  - {max_logL_err: 1.0, Q: 0.75}
```

**Baseline solver:** RAxML — logL error 0.001
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | logL Error | BL RMSE | Runtime | Q |
|--------|-----------|---------|---------|---|
| PhyML | 0.005 | 5.0e-3 | 10 s | 0.90 |
| RAxML | 0.001 | 2.0e-3 | 30 s | 1.00 |
| IQ-TREE | 0.0005 | 1.5e-3 | 25 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (IQ-TREE): 500 × 1.00 = 500 PWM
Floor:               500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p409_hash>",
  "h_s": "sha256:<spec409_hash>",
  "h_b": "sha256:<bench409_hash>",
  "r": {"logL_err": 0.0005, "BL_RMSE": 1.5e-3, "ratio": 0.05},
  "c": {"taxa": 50, "sites": 1000, "K": 3},
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
pwm-node benchmarks | grep phylogenetic
pwm-node verify AE_computational_biology/phylogenetic_likelihood_s1_ideal.yaml
pwm-node mine AE_computational_biology/phylogenetic_likelihood_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
