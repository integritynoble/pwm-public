# Principle #291 — Well Test Analysis (Pressure Transient)

**Domain:** Geophysics | **Carrier:** N/A (diffusion inverse) | **Difficulty:** Standard (δ=3)
**DAG:** K.green → ∫.temporal → O.l2 |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.green→∫.temporal→O.l2      well-test   drawdown-buildup  type-curve
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  WELL TEST ANALYSIS (PRESSURE)    P = (E,G,W,C)   Principle #291│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ (1/r)∂/∂r(r ∂p/∂r) = (φμc_t/k) ∂p/∂t  (radial diff.) │
│        │ p_wf(t) = p_i − (qμ/4πkh)Ei(−φμc_tr²/4kt) (Theis)   │
│        │ Forward: given k,S,C → predict pressure transient      │
│        │ Inverse: given p(t) → recover k, S (skin), C (storage)│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.green] ──→ [∫.temporal] ──→ [O.l2]                  │
│        │ kernel  integrate  optimize                            │
│        │ V={K.green, ∫.temporal, O.l2}  A={K.green→∫.temporal, ∫.temporal→O.l2}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (radial diffusion has Theis solution)   │
│        │ Uniqueness: YES for homogeneous reservoir with 3 params│
│        │ Stability: well-posed for log-log derivative analysis  │
│        │ Mismatch: heterogeneity, boundaries, multiphase flow   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖p_pred − p_obs‖₂ / ‖p_obs‖₂ (pressure misfit)   │
│        │ q = 2.0 (NLLS type-curve match)                       │
│        │ T = {pressure_match, derivative_match, k_error}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Radial diffusion equation well-formed; Ei function correct | PASS |
| S2 | Theis solution exact for infinite homogeneous reservoir | PASS |
| S3 | Type-curve matching via NLLS converges for drawdown+buildup | PASS |
| S4 | Pressure misfit bounded by gauge resolution and flow rate accuracy | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# well_test/drawdown_s1_ideal.yaml
principle_ref: sha256:<p291_hash>
omega:
  radial_grid: log-spaced_50_cells
  domain: radial_1D
  time: [0, 72]  # hours
  dt: adaptive
E:
  forward: "Theis + skin + wellbore storage"
  parameters: [kh, S, C]
  flow_rate: 500  # m³/day
B:
  outer_boundary: infinite_acting
  wellbore: finite_radius_0.1m
I:
  scenario: drawdown_buildup
  true_params: {kh: 500, S: 5.0, C: 0.1}  # mD·m, -, m³/bar
  gauge_resolution: 0.01  # bar
O: [pressure_misfit, kh_error, skin_error]
epsilon:
  pressure_misfit_max: 1.0e-2
  kh_error_max: 5.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 72-hour test covers radial investigation > 500 m | PASS |
| S2 | Bourdet derivative clearly shows radial flow regime | PASS |
| S3 | NLLS type-curve match converges from log-log initial guess | PASS |
| S4 | kh error < 5% with 0.01-bar gauge | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# well_test/benchmark_drawdown.yaml
spec_ref: sha256:<spec291_hash>
principle_ref: sha256:<p291_hash>
dataset:
  name: synthetic_drawdown_buildup
  reference: "72-hour test, kh=500 mD·m"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Horner-plot
    params: {method: semilog_straight_line}
    results: {kh_error: 3.5e-2, skin_error: 0.5}
  - solver: Type-curve-NLLS
    params: {model: Theis+S+C, iterations: 30}
    results: {pressure_misfit: 8.5e-3, kh_error: 2.2e-2}
  - solver: Deconvolution
    params: {method: von_Schroeter}
    results: {pressure_misfit: 5.5e-3, kh_error: 1.5e-2}
quality_scoring:
  - {min_kh_err: 1.0e-2, Q: 1.00}
  - {min_kh_err: 2.0e-2, Q: 0.90}
  - {min_kh_err: 5.0e-2, Q: 0.80}
  - {min_kh_err: 1.0e-1, Q: 0.75}
```

**Baseline solver:** Type-curve-NLLS — kh error 2.2×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | kh Error | P Misfit | Runtime | Q |
|--------|----------|----------|---------|---|
| Horner-plot | 3.5e-2 | — | 0.1 s | 0.80 |
| Type-curve-NLLS | 2.2e-2 | 8.5e-3 | 1 s | 0.90 |
| Deconvolution | 1.5e-2 | 5.5e-3 | 5 s | 0.90 |
| Bayesian-MCMC | 8.0e-3 | 3.2e-3 | 60 s | 1.00 |

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
  "h_p": "sha256:<p291_hash>",
  "h_s": "sha256:<spec291_hash>",
  "h_b": "sha256:<bench291_hash>",
  "r": {"residual_norm": 8.0e-3, "error_bound": 5.0e-2, "ratio": 0.16},
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
pwm-node benchmarks | grep well_test
pwm-node verify well_test/drawdown_s1_ideal.yaml
pwm-node mine well_test/drawdown_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
