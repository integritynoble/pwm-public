# Principle #444 — Portfolio Optimization (Markowitz)

**Domain:** Computational Finance | **Carrier:** price signal | **Difficulty:** Textbook (δ=1)
**DAG:** L.dense → E.hermitian → O.l2 |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.dense→E.hermitian→O.l2        MVO-port    PortBench-10      QP/CVX
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PORTFOLIO OPTIMIZATION     P = (E, G, W, C)   Principle #444  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ min wᵀΣw  s.t. wᵀμ ≥ r_target, wᵀ1 = 1, w ≥ 0       │
│        │ Σ = asset covariance matrix, μ = expected returns      │
│        │ Efficient frontier: {(σ,r) : σ minimal for each r}    │
│        │ Inverse: estimate Σ and μ from historical returns      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.dense] ──→ [E.hermitian] ──→ [O.l2]                 │
│        │  linear-op  eigensolve  optimize                        │
│        │ V={L.dense, E.hermitian, O.l2}  A={L.dense→E.hermitian, E.hermitian→O.l2}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Σ > 0 → QP always feasible)           │
│        │ Uniqueness: YES (strictly convex QP)                   │
│        │ Stability: sensitive to Σ estimation; shrinkage helps  │
│        │ Mismatch: estimation error in μ and Σ                  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = out-of-sample Sharpe ratio (primary), turnover     │
│        │ q = optimal for given (μ, Σ)                          │
│        │ T = {sharpe_ratio, volatility, max_drawdown}           │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Σ positive definite; μ and w dimensions match n_assets | PASS |
| S2 | QP strictly convex → unique global minimum | PASS |
| S3 | Interior-point / active-set converges in polynomial time | PASS |
| S4 | Sharpe ratio computable from realized returns | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# finance/markowitz_s1_ideal.yaml
principle_ref: sha256:<p444_hash>
omega:
  description: "10-asset portfolio, monthly returns, 60-month history"
  assets: 10
  history: 60
E:
  forward: "min w'Σw s.t. w'μ >= target, w'1 = 1, w >= 0"
  estimation: "sample covariance + Ledoit-Wolf shrinkage"
I:
  dataset: PortBench_10
  portfolios: 10
  rebalance: monthly
  scenario: ideal
O: [sharpe_ratio, volatility, max_drawdown]
epsilon:
  sharpe_min: 0.5
  vol_max: 0.15
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 10 assets, 60 months history → Σ estimable | PASS |
| S2 | Shrinkage ensures Σ well-conditioned | PASS |
| S3 | QP solver (OSQP/CVXPY) converges | PASS |
| S4 | Sharpe > 0.5 feasible with diversified assets | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# finance/benchmark_markowitz_s1.yaml
spec_ref: sha256:<spec444_hash>
principle_ref: sha256:<p444_hash>
dataset:
  name: PortBench_10
  portfolios: 10
  data_hash: sha256:<dataset_444_hash>
baselines:
  - solver: MVO-QP
    params: {shrinkage: Ledoit-Wolf}
    results: {sharpe: 0.72, vol: 0.12}
  - solver: Equal-Weight
    params: {}
    results: {sharpe: 0.55, vol: 0.14}
  - solver: Risk-Parity
    params: {}
    results: {sharpe: 0.68, vol: 0.10}
quality_scoring:
  - {min_sharpe: 0.85, Q: 1.00}
  - {min_sharpe: 0.70, Q: 0.90}
  - {min_sharpe: 0.55, Q: 0.80}
  - {min_sharpe: 0.45, Q: 0.75}
```

**Baseline solver:** MVO-QP — Sharpe 0.72
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Sharpe | Volatility | Max DD | Q |
|--------|--------|-----------|--------|---|
| MVO-QP | 0.72 | 0.12 | -0.15 | 0.90 |
| Equal Weight | 0.55 | 0.14 | -0.20 | 0.80 |
| Risk Parity | 0.68 | 0.10 | -0.12 | 0.88 |
| Black-Litterman | 0.82 | 0.11 | -0.13 | 0.96 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (BL):    100 × 0.96 = 96 PWM
Floor:             100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p444_hash>",
  "h_s": "sha256:<spec444_hash>",
  "h_b": "sha256:<bench444_hash>",
  "r": {"sharpe": 0.82, "error_bound": 0.50, "ratio": 1.64},
  "c": {"method": "Black-Litterman", "assets": 10, "K": 3},
  "Q": 0.96,
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
| L4 Solution | — | 75–96 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep portfolio_markowitz
pwm-node verify finance/markowitz_s1_ideal.yaml
pwm-node mine finance/markowitz_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
