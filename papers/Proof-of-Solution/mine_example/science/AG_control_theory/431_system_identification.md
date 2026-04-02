# Principle #431 — System Identification (ARX/ARMAX)

**Domain:** Control Theory & Dynamical Systems | **Carrier:** signal | **Difficulty:** Standard (δ=2)
**DAG:** L.state → ∂.time → S.observation → O.l2 |  **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.state→∂.time→S.observation→O.l2        SysID       IOData-10          LS/PEM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SYSTEM IDENTIFICATION      P = (E, G, W, C)   Principle #431   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ARX: y(k) = Σ aᵢ y(k-i) + Σ bⱼ u(k-j) + e(k)        │
│        │ ARMAX adds MA noise model: + Σ cₘ e(k-m)              │
│        │ Inverse: estimate {a,b,c} from measured (u,y) data     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.state] ──→ [∂.time] ──→ [S.observation] ──→ [O.l2]  │
│        │  linear-op  derivative  sample  optimize                │
│        │ V={L.state, ∂.time, S.observation, O.l2}  A={L.state→∂.time, ∂.time→S.observation, S.observation→O.l2}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (LS always has solution)                │
│        │ Uniqueness: YES when input persistently exciting       │
│        │ Stability: κ depends on data SNR and model order       │
│        │ Mismatch: wrong model order, nonlinearities            │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = output fit % (primary), AIC (secondary)            │
│        │ q = O(1/√N) parametric rate                           │
│        │ T = {output_fit, AIC, residual_whiteness}              │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Model order n_a, n_b consistent with data dimensions | PASS |
| S2 | Input persistently exciting of sufficient order | PASS |
| S3 | LS/PEM converges for given data length and SNR | PASS |
| S4 | Output fit > 85% achievable for linear systems at SNR > 20 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# control/sysid_arx_s1_ideal.yaml
principle_ref: sha256:<p431_hash>
omega:
  description: "2nd-order ARX model, PRBS input, N=1000 samples"
  model_order: {n_a: 2, n_b: 2, delay: 1}
  samples: 1000
E:
  forward: "y(k) = a1*y(k-1) + a2*y(k-2) + b1*u(k-1) + b2*u(k-2) + e(k)"
  method: "least squares / prediction error method"
I:
  dataset: IOData_10
  experiments: 10
  noise: {type: gaussian, SNR_dB: 25}
  scenario: ideal
O: [output_fit_percent, AIC, residual_whiteness]
epsilon:
  fit_min: 85.0
  residual_white: true
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Regressor matrix dimensions N×(n_a+n_b) consistent | PASS |
| S2 | PRBS input persistently exciting of order ≥ n_a+n_b | PASS |
| S3 | LS solution unique for full-rank regressor | PASS |
| S4 | Output fit > 85% feasible at SNR=25 dB | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# control/benchmark_sysid_s1.yaml
spec_ref: sha256:<spec431_hash>
principle_ref: sha256:<p431_hash>
dataset:
  name: IOData_10
  experiments: 10
  samples: 1000
  data_hash: sha256:<dataset_431_hash>
baselines:
  - solver: OLS
    params: {order: 2}
    results: {fit: 92.5, AIC: -1820}
  - solver: PEM
    params: {order: 2, method: ARMAX}
    results: {fit: 95.1, AIC: -1950}
  - solver: N4SID
    params: {order: 2}
    results: {fit: 93.8, AIC: -1880}
quality_scoring:
  - {min_fit: 96.0, Q: 1.00}
  - {min_fit: 93.0, Q: 0.90}
  - {min_fit: 88.0, Q: 0.80}
  - {min_fit: 85.0, Q: 0.75}
```

**Baseline solver:** OLS — fit 92.5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Fit % | AIC | Runtime | Q |
|--------|-------|-----|---------|---|
| OLS | 92.5 | -1820 | 0.01 s | 0.88 |
| PEM (ARMAX) | 95.1 | -1950 | 0.10 s | 0.95 |
| N4SID | 93.8 | -1880 | 0.05 s | 0.91 |
| Deep-SysID | 96.2 | -1980 | 1.0 s | 0.98 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (Deep):  200 × 0.98 = 196 PWM
Floor:             200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p431_hash>",
  "h_s": "sha256:<spec431_hash>",
  "h_b": "sha256:<bench431_hash>",
  "r": {"residual_norm": 0.015, "error_bound": 0.05, "ratio": 0.30},
  "c": {"fitted_rate": 0.49, "theoretical_rate": 0.50, "K": 3},
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
| L4 Solution | — | 150–196 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep system_identification
pwm-node verify control/sysid_arx_s1_ideal.yaml
pwm-node mine control/sysid_arx_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
