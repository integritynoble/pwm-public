# Principle #408 — Population Genetics (Wright-Fisher)

**Domain:** Computational Biology | **Carrier:** allele frequency | **Difficulty:** Standard (δ=3)
**DAG:** S.random → N.pointwise → ∫.ensemble |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.random→N.pointwise→∫.ensemble        WF-diffusion allele-freq       SDE/FP
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  WRIGHT-FISHER DIFFUSION        P = (E,G,W,C)   Principle #408  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂f/∂t = (1/4N_e) ∂²[x(1−x)f]/∂x² − s ∂[x(1−x)f]/∂x│
│        │ f(x,t) = density of allele frequency x at time t       │
│        │ N_e = effective population size, s = selection coeff.  │
│        │ Or SDE: dx = s·x(1−x)dt + √(x(1−x)/(2N_e)) dW       │
│        │ Forward: given N_e, s, x(0) → f(x,t) or E[x(t)]     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.random] ──→ [N.pointwise] ──→ [∫.ensemble]          │
│        │ sample  nonlinear  integrate                           │
│        │ V={S.random, N.pointwise, ∫.ensemble}  A={S.random→N.pointwise, N.pointwise→∫.ensemble}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Fokker-Planck on [0,1] with absorbing) │
│        │ Uniqueness: YES (degenerate diffusion; Feller boundary) │
│        │ Stability: fixation absorbing states at x=0, x=1       │
│        │ Mismatch: population size fluctuation, epistasis        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |P_fix − P_fix_ref| (fixation probability error)  │
│        │ q = 0.5 (MC), 2.0 (FDM on Fokker-Planck)            │
│        │ T = {fixation_prob_error, mean_time_error, K_N_values} │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Allele frequency x in [0,1]; N_e and s well-defined | PASS |
| S2 | Fokker-Planck well-posed with Feller boundary classification | PASS |
| S3 | FDM on Fokker-Planck or MC simulation both converge | PASS |
| S4 | Fixation probability computable against Kimura formula | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# wright_fisher/allele_fixation_s1_ideal.yaml
principle_ref: sha256:<p408_hash>
omega:
  grid: [1000]   # frequency bins on [0,1]
  time: [0, 10000]   # generations
  dt: 1.0
E:
  forward: "Fokker-Planck: WF diffusion with selection"
  N_e: 1000
  s: 0.01
B:
  boundary: {x0: absorbing, x1: absorbing}
  initial: {x_init: 0.1}
I:
  scenario: beneficial_allele_fixation
  N_e_values: [100, 1000, 10000]
O: [fixation_prob_error, mean_fixation_time_error]
epsilon:
  fix_prob_error_max: 0.01
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1000 bins on [0,1]; dt=1 generation standard | PASS |
| S2 | N_e·s=10 — selection-drift regime well-characterized | PASS |
| S3 | FDM on Fokker-Planck converges; Kimura formula validates | PASS |
| S4 | Fixation prob error < 1% achievable with 1000 bins | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# wright_fisher/benchmark_fixation.yaml
spec_ref: sha256:<spec408_hash>
principle_ref: sha256:<p408_hash>
dataset:
  name: Kimura_fixation_formula
  reference: "Kimura (1962) fixation probability"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: MC-simulation
    params: {replicates: 1e5}
    results: {fix_prob_err: 0.005, mean_time_err: 15}
  - solver: FDM-Crank-Nicolson
    params: {N_bins: 500, dt: 1.0}
    results: {fix_prob_err: 0.008, mean_time_err: 8}
  - solver: FDM-fine
    params: {N_bins: 2000, dt: 0.5}
    results: {fix_prob_err: 0.001, mean_time_err: 2}
quality_scoring:
  - {max_fix_err: 0.002, Q: 1.00}
  - {max_fix_err: 0.01, Q: 0.90}
  - {max_fix_err: 0.02, Q: 0.80}
  - {max_fix_err: 0.05, Q: 0.75}
```

**Baseline solver:** FDM-CN — fixation prob error 0.8%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Fix. Prob Error | Mean Time Error | Runtime | Q |
|--------|----------------|-----------------|---------|---|
| MC-simulation | 0.005 | 15 gen | 30 s | 0.90 |
| FDM-CN | 0.008 | 8 gen | 2 s | 0.90 |
| FDM-fine | 0.001 | 2 gen | 10 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (FDM-fine): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p408_hash>",
  "h_s": "sha256:<spec408_hash>",
  "h_b": "sha256:<bench408_hash>",
  "r": {"fix_prob_err": 0.001, "mean_time_err": 2, "ratio": 0.10},
  "c": {"fitted_rate": 2.0, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep wright_fisher
pwm-node verify AE_computational_biology/wright_fisher_s1_ideal.yaml
pwm-node mine AE_computational_biology/wright_fisher_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
