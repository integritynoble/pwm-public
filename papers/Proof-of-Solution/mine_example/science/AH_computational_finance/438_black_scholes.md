# Principle #438 — Black-Scholes Option Pricing

**Domain:** Computational Finance | **Carrier:** price signal | **Difficulty:** Textbook (δ=1)
**DAG:** ∂.time → ∂.space.laplacian → N.payoff → B.terminal |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→∂.space.laplacian→N.payoff→B.terminal        BS-price    BSBench-10         FD/Analytic
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  BLACK-SCHOLES PRICING      P = (E, G, W, C)   Principle #438  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂V/∂t + ½σ²S²∂²V/∂S² + rS∂V/∂S − rV = 0             │
│        │ Terminal: V(S,T) = max(S−K, 0) for call                │
│        │ Analytic: V = S·N(d₁) − K·e⁻ʳᵀ·N(d₂)                 │
│        │ Inverse: calibrate σ from observed option prices       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [∂.space.laplacian] ──→ [N.payoff] ──→ [B.terminal] │
│        │  derivative  derivative  nonlinear  boundary            │
│        │ V={∂.time, ∂.space.laplacian, N.payoff, B.terminal}  A={∂.time→∂.space.laplacian, ∂.space.laplacian→N.payoff, N.payoff→B.terminal}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (closed-form solution exists)           │
│        │ Uniqueness: YES (parabolic PDE, unique solution)       │
│        │ Stability: well-posed; Greeks bounded for S>0          │
│        │ Mismatch: constant σ assumption, no jumps, no div.     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative pricing error |V̂−V|/V (primary)          │
│        │ q = 2.0 (Crank-Nicolson second-order)                 │
│        │ T = {price_error, greeks_error, convergence_rate}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | S, K, r, σ, T all positive; grid covers (0, S_max) | PASS |
| S2 | Parabolic PDE well-posed with terminal condition | PASS |
| S3 | Analytic formula exact; FD converges as O(Δx², Δt²) | PASS |
| S4 | Pricing error < 0.1% vs analytic for European options | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# finance/black_scholes_s1_ideal.yaml
principle_ref: sha256:<p438_hash>
omega:
  description: "European call/put, S0=100, K=100, r=0.05, T=1.0"
  grid_S: 200
  grid_t: 100
E:
  forward: "BS PDE with constant volatility σ"
  analytic: "V = S·N(d1) - K·exp(-rT)·N(d2)"
I:
  dataset: BSBench_10
  options: 10
  sigma: {range: [0.1, 0.5]}
  scenario: ideal
O: [relative_price_error, delta_error, gamma_error]
epsilon:
  price_err_max: 0.001
  delta_err_max: 0.005
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid 200×100 resolves S and t adequately | PASS |
| S2 | Boundary conditions at S=0 and S=S_max consistent | PASS |
| S3 | Crank-Nicolson stable unconditionally | PASS |
| S4 | Price error < 0.1% vs analytic formula | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# finance/benchmark_bs_s1.yaml
spec_ref: sha256:<spec438_hash>
principle_ref: sha256:<p438_hash>
dataset:
  name: BSBench_10
  options: 10
  data_hash: sha256:<dataset_438_hash>
baselines:
  - solver: Analytic
    params: {}
    results: {price_err: 0.0, delta_err: 0.0}
  - solver: Crank-Nicolson-FD
    params: {N_S: 200, N_t: 100}
    results: {price_err: 0.0003, delta_err: 0.002}
  - solver: Binomial-Tree
    params: {steps: 500}
    results: {price_err: 0.0008, delta_err: 0.004}
quality_scoring:
  - {max_err: 0.0001, Q: 1.00}
  - {max_err: 0.0005, Q: 0.90}
  - {max_err: 0.001, Q: 0.80}
  - {max_err: 0.005, Q: 0.75}
```

**Baseline solver:** Analytic — exact
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Price Error | Delta Error | Runtime | Q |
|--------|-----------|------------|---------|---|
| Analytic | 0.0 | 0.0 | 0.001 s | 1.00 |
| Crank-Nicolson | 0.0003 | 0.002 | 0.05 s | 0.92 |
| Binomial Tree | 0.0008 | 0.004 | 0.10 s | 0.85 |
| Monte Carlo | 0.0012 | 0.005 | 1.0 s | 0.78 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (Analytic): 100 × 1.00 = 100 PWM
Floor:                100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p438_hash>",
  "h_s": "sha256:<spec438_hash>",
  "h_b": "sha256:<bench438_hash>",
  "r": {"price_error": 0.0, "error_bound": 0.001, "ratio": 0.00},
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
| L4 Solution | — | 75–100 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep black_scholes
pwm-node verify finance/black_scholes_s1_ideal.yaml
pwm-node mine finance/black_scholes_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
