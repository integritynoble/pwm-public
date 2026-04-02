# Principle #404 — Pharmacodynamics (Hill/Emax Model)

**Domain:** Computational Biology | **Carrier:** drug effect | **Difficulty:** Introductory (δ=2)
**DAG:** N.pointwise → ∂.time |  **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.pointwise→∂.time      Hill-Emax    dose-response     NLLS
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PHARMACODYNAMICS (HILL/EMAX)   P = (E,G,W,C)   Principle #404 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ E(C) = E₀ + E_max · Cⁿ / (EC₅₀ⁿ + Cⁿ)              │
│        │ E = pharmacological effect, C = drug concentration     │
│        │ EC₅₀ = half-maximal concentration, n = Hill coefficient│
│        │ E₀ = baseline effect, E_max = maximal effect           │
│        │ Forward: given C(t) from PK → E(t) response curve     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pointwise] ──→ [∂.time]                             │
│        │ nonlinear  derivative                                  │
│        │ V={N.pointwise, ∂.time}  A={N.pointwise→∂.time}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (algebraic map, well-defined for C ≥ 0) │
│        │ Uniqueness: YES (monotonic sigmoid, bijective C→E)     │
│        │ Stability: YES (bounded output for bounded input)      │
│        │ Mismatch: Hill coefficient estimation, hysteresis       │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSE of E_pred vs E_obs (pharmacodynamic response) │
│        │ q = N/A (parameter estimation, not mesh convergence)  │
│        │ T = {RMSE, EC50_error, Hill_n_error, R²}               │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Effect and concentration dimensions consistent; sigmoid well-defined | PASS |
| S2 | Hill equation monotonic — unique E for each C ≥ 0 | PASS |
| S3 | NLLS (Levenberg-Marquardt) converges for well-sampled dose-response | PASS |
| S4 | RMSE computable against in vitro dose-response data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# pharmacodynamics/dose_response_s1_ideal.yaml
principle_ref: sha256:<p404_hash>
omega:
  concentrations: logspace(-3, 2, 50)   # uM
  model: sigmoidal_Emax
E:
  forward: "E = E0 + Emax · C^n / (EC50^n + C^n)"
  E0: 0.0
  Emax: 100.0   # % response
  EC50: 1.0   # uM
  n: 1.5
B:
  constraints: {E0_min: 0, Emax_max: 100}
I:
  scenario: in_vitro_dose_response
  noise_levels: [0.0, 0.02, 0.05]
  n_replicates: 3
O: [RMSE, EC50_error, Hill_n_error, R_squared]
epsilon:
  RMSE_max: 2.0   # % units
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 50 concentrations span 5 log units — adequate for sigmoid fit | PASS |
| S2 | n=1.5 produces well-separated sigmoid; identifiable parameters | PASS |
| S3 | Levenberg-Marquardt converges for Hill equation | PASS |
| S4 | RMSE < 2% achievable with 3 replicates and 2% noise | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# pharmacodynamics/benchmark_dose_response.yaml
spec_ref: sha256:<spec404_hash>
principle_ref: sha256:<p404_hash>
dataset:
  name: synthetic_Hill_DR
  reference: "Synthetic dose-response with known parameters"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Linear-log-regression
    params: {transform: log_logit}
    results: {RMSE: 3.5, EC50_err: 0.15}
  - solver: NLLS-LM
    params: {maxiter: 100}
    results: {RMSE: 1.2, EC50_err: 0.03}
  - solver: Bayesian-MCMC
    params: {samples: 10000}
    results: {RMSE: 1.1, EC50_err: 0.02}
quality_scoring:
  - {max_RMSE: 1.0, Q: 1.00}
  - {max_RMSE: 2.0, Q: 0.90}
  - {max_RMSE: 5.0, Q: 0.80}
  - {max_RMSE: 10.0, Q: 0.75}
```

**Baseline solver:** NLLS-LM — RMSE 1.2
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | RMSE | EC50 Error | Runtime | Q |
|--------|------|-----------|---------|---|
| Linear-log | 3.5 | 0.15 | 0.001 s | 0.80 |
| NLLS-LM | 1.2 | 0.03 | 0.01 s | 0.90 |
| Bayesian-MCMC | 1.1 | 0.02 | 5 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case: 200 × 0.90 = 180 PWM
Floor:     200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p404_hash>",
  "h_s": "sha256:<spec404_hash>",
  "h_b": "sha256:<bench404_hash>",
  "r": {"RMSE": 1.1, "EC50_err": 0.02, "ratio": 0.55},
  "c": {"R_squared": 0.998, "K": 3},
  "Q": 0.90,
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
| L4 Solution | — | 150–180 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep pharmacodynamics
pwm-node verify AE_computational_biology/pharmacodynamics_s1_ideal.yaml
pwm-node mine AE_computational_biology/pharmacodynamics_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
