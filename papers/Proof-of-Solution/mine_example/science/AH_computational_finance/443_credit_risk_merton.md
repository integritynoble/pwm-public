# Principle #443 — Credit Risk (Merton Model)

**Domain:** Computational Finance | **Carrier:** price signal | **Difficulty:** Standard (δ=2)
**DAG:** N.pointwise → ∫.volume → O.l2 |  **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pointwise→∫.volume→O.l2        Merton      CreditBench-10    BS/KMV
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CREDIT RISK (MERTON)       P = (E, G, W, C)   Principle #443  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ dV = μV dt + σ_V V dW  (firm asset value)             │
│        │ Default: V(T) < D (debt face value)                    │
│        │ Equity = call on assets: E = V·N(d₁) − D·e⁻ʳᵀ·N(d₂) │
│        │ Inverse: estimate (V, σ_V) from observed (E, σ_E)     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pointwise] ──→ [∫.volume] ──→ [O.l2]                │
│        │  nonlinear  integrate  optimize                         │
│        │ V={N.pointwise, ∫.volume, O.l2}  A={N.pointwise→∫.volume, ∫.volume→O.l2}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (GBM + BS framework)                    │
│        │ Uniqueness: YES (two equations for two unknowns V,σ_V)│
│        │ Stability: sensitive to leverage and σ_V estimation    │
│        │ Mismatch: constant σ_V, no jumps, single maturity D   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = default probability error (primary), spread error  │
│        │ q = Newton convergence for (V, σ_V) system            │
│        │ T = {PD_error, spread_error, calibration_residual}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | V > 0, D > 0, σ_V > 0, T > 0 all physical | PASS |
| S2 | Two-equation system (equity value + equity vol) well-conditioned | PASS |
| S3 | Newton solver converges for (V, σ_V) within 10 iterations | PASS |
| S4 | PD error < 5% of true PD for investment-grade firms | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# finance/merton_credit_s1_ideal.yaml
principle_ref: sha256:<p443_hash>
omega:
  description: "Single-firm credit, T=1 year, D/V leverage ratio"
  horizon: 1.0
  risk_free: 0.05
E:
  forward: "E = V*N(d1) - D*exp(-rT)*N(d2); sigma_E = (V/E)*N(d1)*sigma_V"
  inverse: "Solve 2x2 nonlinear system for (V, sigma_V)"
I:
  dataset: CreditBench_10
  firms: 10
  leverage: {range: [0.3, 0.8]}
  scenario: ideal
O: [PD_error, credit_spread_error_bps]
epsilon:
  PD_err_max: 0.05
  spread_err_max_bps: 20
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 10 firms with varied leverage; equity data consistent | PASS |
| S2 | System well-conditioned for leverage in [0.3, 0.8] | PASS |
| S3 | Newton converges for all firms | PASS |
| S4 | PD error < 5% feasible with clean equity data | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# finance/benchmark_merton_s1.yaml
spec_ref: sha256:<spec443_hash>
principle_ref: sha256:<p443_hash>
dataset:
  name: CreditBench_10
  firms: 10
  data_hash: sha256:<dataset_443_hash>
baselines:
  - solver: Newton-Merton
    params: {max_iter: 20}
    results: {PD_err: 0.02, spread_err_bps: 8}
  - solver: KMV-Iterative
    params: {}
    results: {PD_err: 0.025, spread_err_bps: 10}
  - solver: Naive-Leverage
    params: {}
    results: {PD_err: 0.08, spread_err_bps: 35}
quality_scoring:
  - {max_PD_err: 0.01, Q: 1.00}
  - {max_PD_err: 0.025, Q: 0.90}
  - {max_PD_err: 0.04, Q: 0.80}
  - {max_PD_err: 0.06, Q: 0.75}
```

**Baseline solver:** Newton-Merton — PD error 0.02
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | PD Error | Spread (bps) | Runtime | Q |
|--------|---------|-------------|---------|---|
| Newton-Merton | 0.020 | 8 | 0.01 s | 0.92 |
| KMV-Iterative | 0.025 | 10 | 0.02 s | 0.90 |
| Naive Leverage | 0.080 | 35 | 0.001 s | 0.70 |
| ML-Enhanced | 0.012 | 5 | 0.10 s | 0.96 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (ML):    200 × 0.96 = 192 PWM
Floor:             200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p443_hash>",
  "h_s": "sha256:<spec443_hash>",
  "h_b": "sha256:<bench443_hash>",
  "r": {"PD_error": 0.012, "error_bound": 0.05, "ratio": 0.24},
  "c": {"method": "ML-Enhanced", "iterations": 8, "K": 3},
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
| L4 Solution | — | 150–192 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep credit_risk_merton
pwm-node verify finance/merton_credit_s1_ideal.yaml
pwm-node mine finance/merton_credit_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
