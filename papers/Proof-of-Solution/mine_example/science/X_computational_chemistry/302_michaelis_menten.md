# Principle #302 — Michaelis-Menten Enzyme Kinetics

**Domain:** Computational Chemistry | **Carrier:** N/A (ODE-based) | **Difficulty:** Standard (δ=3)
**DAG:** N.reaction → ∂.time.implicit |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.reaction→∂.time.implicit      mm-kin      enzyme-assay      NLLS-fit
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MICHAELIS-MENTEN ENZYME KINETICS P = (E,G,W,C)   Principle #302│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ v = V_max [S] / (K_m + [S])  (steady-state rate)      │
│        │ E + S ⇌ ES → E + P  (mechanism)                       │
│        │ d[S]/dt = −v ;  d[P]/dt = +v                           │
│        │ Forward: given V_max, K_m → predict v([S])             │
│        │ Inverse: given v vs [S] data → fit V_max, K_m         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.reaction] ──→ [∂.time.implicit]                     │
│        │ nonlinear  derivative                                  │
│        │ V={N.reaction, ∂.time.implicit}  A={N.reaction→∂.time.implicit}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (quasi-steady-state approx well-posed)  │
│        │ Uniqueness: YES (2 parameters from hyperbolic fit)     │
│        │ Stability: well-conditioned for [S] spanning K_m       │
│        │ Mismatch: substrate inhibition, cooperativity, pH      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖v_fit − v_obs‖₂ / ‖v_obs‖₂ (rate misfit)        │
│        │ q = 2.0 (NLLS converges quadratically)                │
│        │ T = {V_max_error, K_m_error, residual_pattern}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Rate equation hyperbolic; dimensions v=[M/s], K_m=[M] | PASS |
| S2 | QSSA valid when [E]₀ << [S]₀; unique V_max and K_m | PASS |
| S3 | NLLS (Levenberg-Marquardt) converges for 8+ data points | PASS |
| S4 | Parameter errors bounded by data noise and [S] range | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# mm_kin/enzyme_s1_ideal.yaml
principle_ref: sha256:<p302_hash>
omega:
  substrate_range: [0.01, 100]  # mM
  data_points: 12
  replicates: 3
E:
  forward: "v = V_max [S] / (K_m + [S])"
  noise_model: proportional_5%
B:
  enzyme_concentration: 1.0  # nM
  pH: 7.4
  temperature: 25  # °C
I:
  scenario: standard_MM_assay
  true_Vmax: 50.0  # μM/s
  true_Km: 5.0  # mM
O: [Vmax_error, Km_error, rate_residual]
epsilon:
  Vmax_error_max: 5.0e-2  # relative
  Km_error_max: 1.0e-1  # relative
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 12 [S] values spanning 0.01–100 mM bracket K_m=5 mM | PASS |
| S2 | Triplicate measurements reduce noise; QSSA valid at 1 nM [E] | PASS |
| S3 | NLLS converges from Lineweaver-Burk initial guess | PASS |
| S4 | V_max error < 5%, K_m error < 10% with 5% noise | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# mm_kin/benchmark_assay.yaml
spec_ref: sha256:<spec302_hash>
principle_ref: sha256:<p302_hash>
dataset:
  name: synthetic_MM_assay
  reference: "12-point triplicate assay, V_max=50, K_m=5"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Lineweaver-Burk
    params: {method: linear_double_reciprocal}
    results: {Vmax_error: 0.12, Km_error: 0.18}
  - solver: Eadie-Hofstee
    params: {method: linear_v_vs_v/S}
    results: {Vmax_error: 0.08, Km_error: 0.12}
  - solver: NLLS-LevMarq
    params: {method: direct_hyperbolic, iterations: 30}
    results: {Vmax_error: 0.03, Km_error: 0.05}
quality_scoring:
  - {min_Vmax_err: 0.01, Q: 1.00}
  - {min_Vmax_err: 0.03, Q: 0.90}
  - {min_Vmax_err: 0.06, Q: 0.80}
  - {min_Vmax_err: 0.15, Q: 0.75}
```

**Baseline solver:** NLLS-LevMarq — V_max error 3%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | V_max Error | K_m Error | Runtime | Q |
|--------|-------------|-----------|---------|---|
| Lineweaver-Burk | 0.12 | 0.18 | 0.01 s | 0.75 |
| Eadie-Hofstee | 0.08 | 0.12 | 0.01 s | 0.80 |
| NLLS-LevMarq | 0.03 | 0.05 | 0.1 s | 0.90 |
| Bayesian-MCMC | 0.008 | 0.015 | 5 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (Bayesian): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p302_hash>",
  "h_s": "sha256:<spec302_hash>",
  "h_b": "sha256:<bench302_hash>",
  "r": {"residual_norm": 0.008, "error_bound": 0.05, "ratio": 0.16},
  "c": {"fitted_rate": 2.01, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 225–300 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep mm_kin
pwm-node verify mm_kin/enzyme_s1_ideal.yaml
pwm-node mine mm_kin/enzyme_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
