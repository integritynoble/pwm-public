# Principle #445 — GARCH Volatility Model

**Domain:** Computational Finance | **Carrier:** price signal | **Difficulty:** Standard (δ=2)
**DAG:** N.pointwise → ∂.time → O.ml |  **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pointwise→∂.time→O.ml        GARCH       GARCHBench-10     MLE/QML
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  GARCH VOLATILITY MODEL     P = (E, G, W, C)   Principle #445  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ r_t = μ + ε_t,  ε_t = σ_t z_t,  z_t ~ N(0,1)        │
│        │ σ²_t = ω + α ε²_{t-1} + β σ²_{t-1}                   │
│        │ Stationarity: α + β < 1                                │
│        │ Inverse: estimate (ω, α, β) from return series        │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pointwise] ──→ [∂.time] ──→ [O.ml]                  │
│        │  nonlinear  derivative  optimize                        │
│        │ V={N.pointwise, ∂.time, O.ml}  A={N.pointwise→∂.time, ∂.time→O.ml}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (MLE well-defined for α+β<1)           │
│        │ Uniqueness: YES (log-likelihood concave near truth)    │
│        │ Stability: κ depends on persistence α+β               │
│        │ Mismatch: non-Gaussian innovations, leverage effects   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = QLIKE loss (primary), MSE of σ² forecast (second.) │
│        │ q = O(1/√T) asymptotic normality of MLE              │
│        │ T = {QLIKE, MSE_vol, log_likelihood}                   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | ω > 0, α ≥ 0, β ≥ 0, α+β < 1 (stationarity) | PASS |
| S2 | Log-likelihood bounded; MLE consistent | PASS |
| S3 | BFGS/L-BFGS-B converges within 200 iterations | PASS |
| S4 | QLIKE score evaluable against realized volatility proxy | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# finance/garch_s1_ideal.yaml
principle_ref: sha256:<p445_hash>
omega:
  description: "Daily equity returns, T=2500 days (~10 years)"
  samples: 2500
  frequency: daily
E:
  forward: "sigma2_t = omega + alpha*eps2_{t-1} + beta*sigma2_{t-1}"
  estimation: "MLE with Gaussian likelihood"
I:
  dataset: GARCHBench_10
  series: 10
  innovations: gaussian
  scenario: ideal
O: [QLIKE, MSE_vol, param_error]
epsilon:
  QLIKE_max: 0.50
  param_err_max: 0.10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | T=2500 sufficient for GARCH(1,1) estimation | PASS |
| S2 | Stationarity constraint enforced in optimizer | PASS |
| S3 | MLE converges for all 10 series | PASS |
| S4 | QLIKE < 0.50 feasible with Gaussian innovations | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# finance/benchmark_garch_s1.yaml
spec_ref: sha256:<spec445_hash>
principle_ref: sha256:<p445_hash>
dataset:
  name: GARCHBench_10
  series: 10
  data_hash: sha256:<dataset_445_hash>
baselines:
  - solver: GARCH-MLE
    params: {distribution: gaussian}
    results: {QLIKE: 0.35, param_err: 0.03}
  - solver: GARCH-t-MLE
    params: {distribution: student_t}
    results: {QLIKE: 0.30, param_err: 0.025}
  - solver: EWMA
    params: {lambda: 0.94}
    results: {QLIKE: 0.42, param_err: null}
quality_scoring:
  - {max_QLIKE: 0.25, Q: 1.00}
  - {max_QLIKE: 0.32, Q: 0.90}
  - {max_QLIKE: 0.40, Q: 0.80}
  - {max_QLIKE: 0.50, Q: 0.75}
```

**Baseline solver:** GARCH-MLE — QLIKE 0.35
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | QLIKE | Param Error | Runtime | Q |
|--------|-------|-----------|---------|---|
| GARCH-MLE | 0.35 | 0.030 | 0.5 s | 0.88 |
| GARCH-t-MLE | 0.30 | 0.025 | 0.8 s | 0.92 |
| EWMA | 0.42 | — | 0.01 s | 0.78 |
| GJR-GARCH-MLE | 0.28 | 0.022 | 1.0 s | 0.95 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (GJR):   200 × 0.95 = 190 PWM
Floor:             200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p445_hash>",
  "h_s": "sha256:<spec445_hash>",
  "h_b": "sha256:<bench445_hash>",
  "r": {"QLIKE": 0.28, "error_bound": 0.50, "ratio": 0.56},
  "c": {"method": "GJR-GARCH", "T": 2500, "K": 3},
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
| L4 Solution | — | 150–190 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep garch
pwm-node verify finance/garch_s1_ideal.yaml
pwm-node mine finance/garch_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
