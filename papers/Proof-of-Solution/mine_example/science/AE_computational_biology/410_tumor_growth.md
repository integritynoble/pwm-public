# Principle #410 — Tumor Growth (Gompertz/Logistic)

**Domain:** Computational Biology | **Carrier:** tumor volume | **Difficulty:** Introductory (δ=2)
**DAG:** N.reaction → ∂.time → ∂.space.laplacian |  **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.reaction→∂.time→∂.space.laplacian        tumor-ODE    growth-curve      ODE/fit
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  TUMOR GROWTH (GOMPERTZ/LOGISTIC) P = (E,G,W,C) Princ. #410   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Logistic:  dV/dt = r V (1 − V/K)                      │
│        │ Gompertz:  dV/dt = −α V ln(V/K)                       │
│        │ V = tumor volume, K = carrying capacity                │
│        │ r = growth rate, α = Gompertz decay constant           │
│        │ Forward: given V(0), model params → V(t)              │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.reaction] ──→ [∂.time] ──→ [∂.space.laplacian]      │
│        │ nonlinear  derivative  derivative                      │
│        │ V={N.reaction, ∂.time, ∂.space.laplacian}  A={N.reaction→∂.time, ∂.time→∂.space.laplacian}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (smooth ODE, globally bounded)          │
│        │ Uniqueness: YES (Lipschitz for V > 0)                  │
│        │ Stability: V=K is globally stable attractor            │
│        │ Mismatch: model selection (logistic vs Gompertz), noise │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSE of V_pred vs V_obs (tumor volume data)       │
│        │ q = N/A (parameter fitting, not mesh convergence)     │
│        │ T = {RMSE, R², doubling_time_error, K_estimate_error}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Volume, growth rate, carrying capacity dimensionally consistent | PASS |
| S2 | Smooth ODE on V > 0 — unique solution; V → K as t → ∞ | PASS |
| S3 | Analytic solutions exist for both logistic and Gompertz | PASS |
| S4 | RMSE computable against clinical/experimental growth data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# tumor_growth/gompertz_s1_ideal.yaml
principle_ref: sha256:<p410_hash>
omega:
  time: [0, 100.0]   # days
  dt: 0.1
E:
  forward: "dV/dt = −α V ln(V/K) (Gompertz)"
  alpha: 0.05   # day⁻¹
  K: 1000.0   # mm³
B:
  initial: {V0: 10.0}   # mm³
I:
  scenario: untreated_tumor_growth
  models: [logistic, gompertz, von_bertalanffy]
  dt_sizes: [1.0, 0.1, 0.01]
O: [V_RMSE, doubling_time_error, K_error]
epsilon:
  V_error_max: 1.0e-4
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | dt=0.1 day resolves growth dynamics; 100 days covers saturation | PASS |
| S2 | Gompertz ODE — analytic solution V(t) = K exp(−exp(−αt) ln(K/V₀)) | PASS |
| S3 | RK4 converges; analytic comparison available | PASS |
| S4 | V error < 10⁻⁴ achievable at dt=0.01 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# tumor_growth/benchmark_gompertz.yaml
spec_ref: sha256:<spec410_hash>
principle_ref: sha256:<p410_hash>
dataset:
  name: Gompertz_analytic
  reference: "Analytic Gompertz solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Forward-Euler
    params: {dt: 0.1}
    results: {V_error: 8.0e-4, K_err: 0.5}
  - solver: RK4
    params: {dt: 0.1}
    results: {V_error: 2.1e-8, K_err: 0.0001}
  - solver: Analytic
    params: {}
    results: {V_error: 0.0, K_err: 0.0}
quality_scoring:
  - {min_V_err: 1.0e-7, Q: 1.00}
  - {min_V_err: 1.0e-4, Q: 0.90}
  - {min_V_err: 1.0e-3, Q: 0.80}
  - {min_V_err: 1.0e-2, Q: 0.75}
```

**Baseline solver:** RK4 — V error 2.1×10⁻⁸
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | V L2 Error | K Error | Runtime | Q |
|--------|-----------|---------|---------|---|
| Forward-Euler | 8.0e-4 | 0.5 mm³ | 0.001 s | 0.80 |
| RK4 | 2.1e-8 | 0.0001 mm³ | 0.002 s | 1.00 |
| Analytic | 0.0 | 0.0 | 0.001 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (analytic): 200 × 1.00 = 200 PWM
Floor:                200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p410_hash>",
  "h_s": "sha256:<spec410_hash>",
  "h_b": "sha256:<bench410_hash>",
  "r": {"V_error": 0.0, "K_err": 0.0, "ratio": 0.0},
  "c": {"method": "analytic", "K": 3},
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
pwm-node benchmarks | grep tumor_growth
pwm-node verify AE_computational_biology/tumor_growth_s1_ideal.yaml
pwm-node mine AE_computational_biology/tumor_growth_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
