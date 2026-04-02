# Principle #464 — Decline Curve Analysis (Arps)

**Domain:** Petroleum Engineering | **Carrier:** N/A (analytical) | **Difficulty:** Basic (δ=2)
**DAG:** [N.pointwise] --> [O.l2] | **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pw-->O.l2   DCA-Arps  field-prod-data  regression
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  DECLINE CURVE ANALYSIS (ARPS)   P = (E,G,W,C)   Principle #464│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ q(t) = q_i (1 + b D_i t)^(−1/b)  (general Arps)      │
│        │ b = 0: exponential  q = q_i exp(−D_i t)               │
│        │ b = 1: harmonic     q = q_i / (1 + D_i t)             │
│        │ 0<b<1: hyperbolic                                      │
│        │ Forward: given (q_i, D_i, b) → q(t), N_p(t)           │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pw] ──→ [O.l2]                                      │
│        │  decline-model  least-squares                          │
│        │ V={N.pw,O.l2}  A={N.pw→O.l2}  L_DAG=1.0                          │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (analytical closed-form)                │
│        │ Uniqueness: YES for given (q_i, D_i, b)               │
│        │ Stability: b > 1 → unphysical infinite EUR             │
│        │ Mismatch: b constrained [0,1]; real data noisy         │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSE(q_pred − q_obs) / mean(q_obs)  (relative)    │
│        │ q = N/A (regression fit)                              │
│        │ T = {fit_RMSE, EUR_error, forecast_MAPE}               │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Rate q > 0, D_i > 0, 0 ≤ b ≤ 1; dimensions consistent | PASS |
| S2 | Closed-form solution exists; unique for fixed parameters | PASS |
| S3 | Nonlinear regression (Levenberg-Marquardt) converges | PASS |
| S4 | Fit RMSE bounded; EUR within confidence interval | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# dca_arps/field_decline_s1.yaml
principle_ref: sha256:<p464_hash>
omega:
  wells: 50
  domain: unconventional_shale
  time: [0, 1825.0]   # 5 years production
E:
  forward: "q(t) = q_i(1+bD_i t)^(-1/b)"
  params_to_fit: [q_i, D_i, b]
  constraint: 0 <= b <= 1
B:
  min_rate: 10.0   # STB/d economic limit
  data: monthly_production_rates
I:
  scenario: shale_well_decline
  training_fraction: [0.5, 0.7, 0.9]
O: [fit_RMSE, forecast_MAPE, EUR_error]
epsilon:
  forecast_MAPE_max: 0.15
  EUR_error_max: 0.10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 50 wells with monthly data; b constrained [0,1] | PASS |
| S2 | Arps model well-posed with bounded parameters | PASS |
| S3 | Levenberg-Marquardt converges for all wells | PASS |
| S4 | Forecast MAPE < 15% achievable with 70%+ training data | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# dca_arps/benchmark_shale.yaml
spec_ref: sha256:<spec464_hash>
principle_ref: sha256:<p464_hash>
dataset:
  name: Shale_production_decline
  reference: "Unconventional well production data (anonymized)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Exponential (b=0)
    params: {fixed_b: 0}
    results: {fit_RMSE: 0.18, forecast_MAPE: 0.22, EUR_error: 0.25}
  - solver: Hyperbolic (free b)
    params: {optimizer: LM}
    results: {fit_RMSE: 0.08, forecast_MAPE: 0.12, EUR_error: 0.11}
  - solver: Modified Hyperbolic (Arps + exp tail)
    params: {b_switch: 0.3, D_min: 0.06}
    results: {fit_RMSE: 0.06, forecast_MAPE: 0.08, EUR_error: 0.06}
quality_scoring:
  - {min_MAPE: 0.05, Q: 1.00}
  - {min_MAPE: 0.10, Q: 0.90}
  - {min_MAPE: 0.15, Q: 0.80}
  - {min_MAPE: 0.25, Q: 0.75}
```

**Baseline solver:** Hyperbolic (free b) — forecast MAPE 12%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Fit RMSE | Forecast MAPE | EUR Error | Q |
|--------|----------|---------------|-----------|---|
| Exponential | 0.18 | 0.22 | 0.25 | 0.75 |
| Hyperbolic | 0.08 | 0.12 | 0.11 | 0.80 |
| Modified Hyperbolic | 0.06 | 0.08 | 0.06 | 0.90 |
| Bayesian DCA | 0.05 | 0.05 | 0.04 | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (Bayesian): 200 × 1.00 = 200 PWM
Floor:                200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p464_hash>",
  "h_s": "sha256:<spec464_hash>",
  "h_b": "sha256:<bench464_hash>",
  "r": {"forecast_MAPE": 0.05, "error_bound": 0.15, "ratio": 0.333},
  "c": {"R2_fit": 0.97, "wells_tested": 50, "K": 3},
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
| L4 Solution | — | 150–200 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep dca_arps
pwm-node verify dca_arps/field_decline_s1.yaml
pwm-node mine dca_arps/field_decline_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
