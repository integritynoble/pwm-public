# Principle #442 — Implied Volatility Surface Calibration

**Domain:** Computational Finance | **Carrier:** price signal | **Difficulty:** Research (δ=4)
**DAG:** N.pointwise → O.l2 |  **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pointwise→O.l2      IVSurf      IVBench-10        Newton/Dupire
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  IMPLIED VOL SURFACE CALIB  P = (E, G, W, C)   Principle #442  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ C_mkt(K,T) = BS(S, K, T, r, σ_imp(K,T))              │
│        │ σ_imp(K,T) = BS⁻¹(C_mkt) via Newton-Raphson          │
│        │ Dupire: σ_loc²(K,T) = 2(∂C/∂T + rK∂C/∂K)/K²∂²C/∂K² │
│        │ Inverse: extract local vol from observed option prices │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pointwise] ──→ [O.l2]                               │
│        │  nonlinear  optimize                                    │
│        │ V={N.pointwise, O.l2}  A={N.pointwise→O.l2}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (monotone vega → unique σ_imp per K,T) │
│        │ Uniqueness: YES for each (K,T) slice                   │
│        │ Stability: ill-conditioned near OTM; regularize        │
│        │ Mismatch: bid-ask noise, discrete strikes, no-arb viol.│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = IV RMSE vs market (primary), arb-free score (sec.) │
│        │ q = superlinear (Newton convergence for σ_imp)        │
│        │ T = {iv_rmse, arb_violations, smoothness}              │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Strike/maturity grid covers liquid range; prices arbitrage-free | PASS |
| S2 | Vega > 0 for all in-scope options → Newton well-defined | PASS |
| S3 | Newton-Raphson converges within 5 iterations for each (K,T) | PASS |
| S4 | IV RMSE < 50 bps achievable from clean market data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# finance/iv_surface_s1_ideal.yaml
principle_ref: sha256:<p442_hash>
omega:
  description: "Equity IV surface, 10 strikes x 6 maturities"
  strikes: 10
  maturities: 6
E:
  forward: "BS inverse for implied vol; Dupire for local vol"
  regularization: "cubic spline interpolation + no-arb filter"
I:
  dataset: IVBench_10
  surfaces: 10
  noise: {type: bid_ask, spread_bps: 5}
  scenario: ideal
O: [iv_rmse_bps, arb_violations, reprice_error]
epsilon:
  iv_rmse_max_bps: 50
  arb_violations: 0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 60 option prices span strike-maturity grid | PASS |
| S2 | All options have positive vega; no deep OTM issues | PASS |
| S3 | Newton converges; spline interpolation smooth | PASS |
| S4 | IV RMSE < 50 bps from noisy data feasible | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# finance/benchmark_iv_s1.yaml
spec_ref: sha256:<spec442_hash>
principle_ref: sha256:<p442_hash>
dataset:
  name: IVBench_10
  surfaces: 10
  data_hash: sha256:<dataset_442_hash>
baselines:
  - solver: Newton-Raphson
    params: {interpolation: cubic_spline}
    results: {iv_rmse_bps: 15, arb_violations: 0}
  - solver: SVI-Parametric
    params: {}
    results: {iv_rmse_bps: 20, arb_violations: 0}
  - solver: SSVI
    params: {}
    results: {iv_rmse_bps: 12, arb_violations: 0}
quality_scoring:
  - {max_bps: 8, Q: 1.00}
  - {max_bps: 15, Q: 0.90}
  - {max_bps: 30, Q: 0.80}
  - {max_bps: 50, Q: 0.75}
```

**Baseline solver:** Newton-Raphson + spline — IV RMSE 15 bps
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | IV RMSE (bps) | Arb Violations | Runtime | Q |
|--------|-------------|---------------|---------|---|
| Newton + Spline | 15 | 0 | 0.05 s | 0.90 |
| SVI | 20 | 0 | 0.02 s | 0.85 |
| SSVI | 12 | 0 | 0.03 s | 0.92 |
| Neural-SDE Calib | 8 | 0 | 0.50 s | 0.98 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (Neural): 400 × 0.98 = 392 PWM
Floor:              400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p442_hash>",
  "h_s": "sha256:<spec442_hash>",
  "h_b": "sha256:<bench442_hash>",
  "r": {"iv_rmse_bps": 8, "error_bound": 50, "ratio": 0.16},
  "c": {"method": "Neural-SDE", "arb_free": true, "K": 3},
  "Q": 0.98,
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
| L4 Solution | — | 300–392 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep implied_volatility
pwm-node verify finance/iv_surface_s1_ideal.yaml
pwm-node mine finance/iv_surface_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
