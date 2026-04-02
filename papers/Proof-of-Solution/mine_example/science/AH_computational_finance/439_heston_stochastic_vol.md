# Principle #439 — Heston Stochastic Volatility

**Domain:** Computational Finance | **Carrier:** price signal | **Difficulty:** Standard (δ=3)
**DAG:** ∂.time → ∂.space → N.pointwise → B.terminal |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→∂.space→N.pointwise→B.terminal      Heston      HestonBench-10    FFT/MC
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  HESTON STOCHASTIC VOL      P = (E, G, W, C)   Principle #439  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ dS = μS dt + √v S dW₁                                 │
│        │ dv = κ(θ−v)dt + σ_v √v dW₂,  corr(dW₁,dW₂) = ρ      │
│        │ Semi-analytic via characteristic function (Fourier)    │
│        │ Inverse: calibrate (κ,θ,σ_v,ρ,v₀) to option surface  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [∂.space] ──→ [N.pointwise] ──→ [B.terminal] │
│        │  derivative  derivative  nonlinear  boundary            │
│        │ V={∂.time, ∂.space, N.pointwise, B.terminal}  A={∂.time→∂.space, ∂.space→N.pointwise, N.pointwise→B.terminal}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Feller condition 2κθ > σ_v²)          │
│        │ Uniqueness: YES (strong solution under Feller)         │
│        │ Stability: CIR process mean-reverts; bounded moments  │
│        │ Mismatch: constant κ,θ; no jumps in S or v             │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative pricing error (primary), IV RMSE (second.)│
│        │ q = O(1/√N) for MC; spectral for FFT                  │
│        │ T = {price_error, iv_rmse, calibration_residual}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Parameters (κ,θ,σ_v,ρ,v₀) physical; Feller condition checked | PASS |
| S2 | Characteristic function well-defined; Fourier inversion converges | PASS |
| S3 | Carr-Madan FFT pricing converges with N=2^12 points | PASS |
| S4 | Pricing error < 0.5% vs semi-analytic for typical params | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# finance/heston_s1_ideal.yaml
principle_ref: sha256:<p439_hash>
omega:
  description: "Heston model, S0=100, v0=0.04, kappa=2, theta=0.04"
  params: {sigma_v: 0.3, rho: -0.7, r: 0.05}
E:
  forward: "Heston SDE pair + Fourier pricing"
  method: "Carr-Madan FFT"
I:
  dataset: HestonBench_10
  option_chains: 10
  strikes: [80, 90, 95, 100, 105, 110, 120]
  scenario: ideal
O: [price_error, iv_rmse]
epsilon:
  price_err_max: 0.005
  iv_rmse_max: 0.01
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 7 strikes across moneyness range; Feller satisfied | PASS |
| S2 | Char. function analytic; no singularities for given params | PASS |
| S3 | FFT with N=4096 converges to < 0.1% error | PASS |
| S4 | Price error < 0.5% feasible | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# finance/benchmark_heston_s1.yaml
spec_ref: sha256:<spec439_hash>
principle_ref: sha256:<p439_hash>
dataset:
  name: HestonBench_10
  option_chains: 10
  data_hash: sha256:<dataset_439_hash>
baselines:
  - solver: Carr-Madan-FFT
    params: {N: 4096}
    results: {price_err: 0.0005, iv_rmse: 0.002}
  - solver: COS-Method
    params: {N: 128}
    results: {price_err: 0.0003, iv_rmse: 0.001}
  - solver: Monte-Carlo
    params: {paths: 100000}
    results: {price_err: 0.003, iv_rmse: 0.008}
quality_scoring:
  - {max_err: 0.0002, Q: 1.00}
  - {max_err: 0.001, Q: 0.90}
  - {max_err: 0.003, Q: 0.80}
  - {max_err: 0.005, Q: 0.75}
```

**Baseline solver:** Carr-Madan-FFT — price error 0.0005
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Price Error | IV RMSE | Runtime | Q |
|--------|-----------|---------|---------|---|
| Carr-Madan FFT | 0.0005 | 0.002 | 0.05 s | 0.92 |
| COS Method | 0.0003 | 0.001 | 0.02 s | 0.96 |
| Monte Carlo | 0.0030 | 0.008 | 5.0 s | 0.80 |
| Deep-Heston NN | 0.0004 | 0.0015 | 0.01 s | 0.94 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (COS):   300 × 0.96 = 288 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p439_hash>",
  "h_s": "sha256:<spec439_hash>",
  "h_b": "sha256:<bench439_hash>",
  "r": {"price_error": 0.0003, "error_bound": 0.005, "ratio": 0.06},
  "c": {"method": "COS", "N_terms": 128, "K": 3},
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
| L4 Solution | — | 225–288 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep heston
pwm-node verify finance/heston_s1_ideal.yaml
pwm-node mine finance/heston_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
