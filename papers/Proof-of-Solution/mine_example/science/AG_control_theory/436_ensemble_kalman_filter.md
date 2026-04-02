# Principle #436 — Ensemble Kalman Filter (EnKF)

**Domain:** Control Theory & Dynamical Systems | **Carrier:** signal | **Difficulty:** Research (δ=4)
**DAG:** L.state → ∂.time → S.observation → ∫.ensemble |  **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.state→∂.time→S.observation→∫.ensemble      EnKF-DA     EnKFBench-10      EnKF/LETKF
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ENSEMBLE KALMAN FILTER     P = (E, G, W, C)   Principle #436  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Forecast: xᵢᶠ = M(xᵢᵃ) + wᵢ,  i=1..N_ens            │
│        │ Analysis: xᵢᵃ = xᵢᶠ + K(yᵢ − H xᵢᶠ)                 │
│        │ K = Pᶠ Hᵀ(H Pᶠ Hᵀ + R)⁻¹,  Pᶠ from ensemble         │
│        │ Inverse: sequential DA for high-dim nonlinear systems  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.state] ──→ [∂.time] ──→ [S.observation] ──→ [∫.ensemble] │
│        │  linear-op  derivative  sample  integrate               │
│        │ V={L.state, ∂.time, S.observation, ∫.ensemble}  A={L.state→∂.time, ∂.time→S.observation, S.observation→∫.ensemble}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (ensemble always propagable)            │
│        │ Uniqueness: asymptotic (N_ens → ∞)                     │
│        │ Stability: CONDITIONAL on localization and inflation   │
│        │ Mismatch: sampling error, rank deficiency, model error │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = analysis RMSE (primary), spread-skill (secondary)  │
│        │ q = O(1/√N_ens) sampling convergence                  │
│        │ T = {analysis_RMSE, spread_ratio, rank_histogram}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Ensemble size N_ens, state/obs dimensions consistent | PASS |
| S2 | Localization radius and inflation factor set; Pᶠ well-conditioned | PASS |
| S3 | EnKF update stable with localization; no filter divergence | PASS |
| S4 | Analysis RMSE < background RMSE across cycles | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# control/enkf_s1_ideal.yaml
principle_ref: sha256:<p436_hash>
omega:
  description: "Lorenz-96, n=40, N_ens=40, sequential cycling"
  states: 40
  ensemble_size: 40
  cycles: 100
E:
  forward: "Ensemble propagation through Lorenz-96 model"
  update: "Stochastic EnKF with perturbed observations"
I:
  dataset: EnKFBench_10
  experiments: 10
  noise: {type: gaussian, obs_error: 1.0}
  scenario: ideal
O: [analysis_RMSE, spread_skill_ratio]
epsilon:
  analysis_RMSE_max: 0.25
  spread_skill: [0.8, 1.2]
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 40 ensemble members for 40-dim state; obs operator consistent | PASS |
| S2 | Localization (GC, r=10) prevents spurious correlations | PASS |
| S3 | Filter stable over 100 cycles without divergence | PASS |
| S4 | Analysis RMSE < 0.25 with N_ens=40 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# control/benchmark_enkf_s1.yaml
spec_ref: sha256:<spec436_hash>
principle_ref: sha256:<p436_hash>
dataset:
  name: EnKFBench_10
  experiments: 10
  data_hash: sha256:<dataset_436_hash>
baselines:
  - solver: Stochastic-EnKF
    params: {N_ens: 40, localization: GC_r10}
    results: {RMSE: 0.18, spread_ratio: 1.05}
  - solver: LETKF
    params: {N_ens: 40, localization: local}
    results: {RMSE: 0.15, spread_ratio: 1.02}
  - solver: EnKF-no-loc
    params: {N_ens: 40, localization: none}
    results: {RMSE: 0.35, spread_ratio: 0.60}
quality_scoring:
  - {max_RMSE: 0.10, Q: 1.00}
  - {max_RMSE: 0.16, Q: 0.90}
  - {max_RMSE: 0.22, Q: 0.80}
  - {max_RMSE: 0.30, Q: 0.75}
```

**Baseline solver:** Stochastic-EnKF — RMSE 0.18
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | RMSE | Spread Ratio | Runtime | Q |
|--------|------|-------------|---------|---|
| Stochastic-EnKF | 0.18 | 1.05 | 5 s | 0.86 |
| LETKF | 0.15 | 1.02 | 8 s | 0.92 |
| EnKF (no loc) | 0.35 | 0.60 | 3 s | 0.70 |
| Hybrid EnVar | 0.12 | 1.00 | 15 s | 0.95 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (Hybrid): 400 × 0.95 = 380 PWM
Floor:              400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p436_hash>",
  "h_s": "sha256:<spec436_hash>",
  "h_b": "sha256:<bench436_hash>",
  "r": {"analysis_RMSE": 0.12, "error_bound": 0.25, "ratio": 0.48},
  "c": {"method": "Hybrid-EnVar", "N_ens": 40, "K": 3},
  "Q": 0.95,
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
| L4 Solution | — | 300–380 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep ensemble_kalman
pwm-node verify control/enkf_s1_ideal.yaml
pwm-node mine control/enkf_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
