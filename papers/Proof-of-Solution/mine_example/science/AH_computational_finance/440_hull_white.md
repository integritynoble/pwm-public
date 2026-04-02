# Principle #440 — Hull-White Interest Rate Model

**Domain:** Computational Finance | **Carrier:** price signal | **Difficulty:** Standard (δ=2)
**DAG:** ∂.time → ∂.space.laplacian → N.pointwise → B.terminal |  **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→∂.space.laplacian→N.pointwise→B.terminal        HW-rate     HWBench-10        Tree/FD
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  HULL-WHITE INTEREST RATE   P = (E, G, W, C)   Principle #440  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ dr = [θ(t) − a·r] dt + σ dW                           │
│        │ θ(t) chosen to fit initial term structure exactly      │
│        │ Bond price: P(t,T) = A(t,T)·exp(−B(t,T)·r(t))        │
│        │ Inverse: calibrate (a, σ) from swaption/cap prices    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [∂.space.laplacian] ──→ [N.pointwise] ──→ [B.terminal] │
│        │  derivative  derivative  nonlinear  boundary            │
│        │ V={∂.time, ∂.space.laplacian, N.pointwise, B.terminal}  A={∂.time→∂.space.laplacian, ∂.space.laplacian→N.pointwise, N.pointwise→B.terminal}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Gaussian OU process, explicit soln)    │
│        │ Uniqueness: YES (linear SDE → unique strong solution)  │
│        │ Stability: mean-reversion ensures bounded variance     │
│        │ Mismatch: negative rates possible (Gaussian model)     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = swaption price error (primary), yield curve fit    │
│        │ q = analytic for bonds; O(Δt²) for derivatives       │
│        │ T = {price_error, yield_fit, calibration_residual}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Parameters a > 0, σ > 0; θ(t) calibrated to yield curve | PASS |
| S2 | OU process well-posed; bond prices analytic | PASS |
| S3 | Trinomial tree converges; FD Crank-Nicolson stable | PASS |
| S4 | Swaption pricing error < 1 bp feasible | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# finance/hull_white_s1_ideal.yaml
principle_ref: sha256:<p440_hash>
omega:
  description: "HW 1-factor, a=0.1, sigma=0.01, flat yield 5%"
  maturities: [1, 2, 3, 5, 7, 10, 20, 30]
E:
  forward: "dr = [theta(t) - a*r]dt + sigma*dW"
  pricing: "analytic bond + trinomial tree for exotics"
I:
  dataset: HWBench_10
  instruments: 10
  type: swaptions
  scenario: ideal
O: [price_error_bps, yield_fit_RMSE]
epsilon:
  price_err_max_bps: 5.0
  yield_RMSE_max: 0.001
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 8 maturities span 1-30 years; θ(t) consistent | PASS |
| S2 | Analytic bond prices well-defined for all maturities | PASS |
| S3 | Trinomial tree with 100 steps/year converges | PASS |
| S4 | Price error < 5 bps feasible | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# finance/benchmark_hw_s1.yaml
spec_ref: sha256:<spec440_hash>
principle_ref: sha256:<p440_hash>
dataset:
  name: HWBench_10
  instruments: 10
  data_hash: sha256:<dataset_440_hash>
baselines:
  - solver: Analytic
    params: {}
    results: {price_err_bps: 0.0, yield_RMSE: 0.0}
  - solver: Trinomial-Tree
    params: {steps_per_year: 100}
    results: {price_err_bps: 0.8, yield_RMSE: 0.0002}
  - solver: Monte-Carlo
    params: {paths: 50000}
    results: {price_err_bps: 3.5, yield_RMSE: 0.0008}
quality_scoring:
  - {max_bps: 0.5, Q: 1.00}
  - {max_bps: 1.5, Q: 0.90}
  - {max_bps: 3.0, Q: 0.80}
  - {max_bps: 5.0, Q: 0.75}
```

**Baseline solver:** Analytic — exact
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Error (bps) | Yield RMSE | Runtime | Q |
|--------|-----------|-----------|---------|---|
| Analytic | 0.0 | 0.0 | 0.001 s | 1.00 |
| Trinomial Tree | 0.8 | 0.0002 | 0.10 s | 0.92 |
| Crank-Nicolson FD | 0.5 | 0.0001 | 0.08 s | 0.95 |
| Monte Carlo | 3.5 | 0.0008 | 2.0 s | 0.78 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (Analytic): 200 × 1.00 = 200 PWM
Floor:                200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p440_hash>",
  "h_s": "sha256:<spec440_hash>",
  "h_b": "sha256:<bench440_hash>",
  "r": {"price_err_bps": 0.0, "error_bound": 5.0, "ratio": 0.00},
  "c": {"method": "Analytic", "convergence": "exact", "K": 3},
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
pwm-node benchmarks | grep hull_white
pwm-node verify finance/hull_white_s1_ideal.yaml
pwm-node mine finance/hull_white_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
