# Principle #423 — Contaminant Source Identification

**Domain:** Environmental Science | **Carrier:** source parameters | **Difficulty:** Advanced (δ=5)
**DAG:** G.point → K.psf.gaussian → O.l2 |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.point→K.psf.gaussian→O.l2   source-ID    plume-inverse      Bayesian
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CONTAMINANT SOURCE ID          P = (E,G,W,C)   Principle #423 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Inverse: given C_obs(x_i, t_j) → find (x_s, Q_s, t_s)│
│        │ Forward model: ∂C/∂t + u·∇C = D∇²C + Q_s δ(x−x_s)   │
│        │ θ = (x_s, y_s, Q_s, t_start) = source parameters      │
│        │ P(θ|C_obs) ∝ P(C_obs|θ) P(θ)  (Bayesian inversion)   │
│        │ Forward: given observations → posterior P(θ|data)      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.point] ──→ [K.psf.gaussian] ──→ [O.l2]              │
│        │ source  kernel  optimize                               │
│        │ V={G.point, K.psf.gaussian, O.l2}  A={G.point→K.psf.gaussian, K.psf.gaussian→O.l2}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (posterior well-defined with proper prior)│
│        │ Uniqueness: CONDITIONAL (ill-posed; regularization needed)│
│        │ Stability: sensitive to measurement noise & density     │
│        │ Mismatch: wind field error, turbulence model            │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = location error ‖x_s − x_true‖ + Q_s relative error│
│        │ q = N/A (inverse problem, MCMC convergence)           │
│        │ T = {location_error, Q_error, posterior_coverage}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Observation locations, forward model, prior dimensions consistent | PASS |
| S2 | Bayesian posterior well-defined with proper likelihood and prior | PASS |
| S3 | MCMC (Metropolis-Hastings) or adjoint-based optimization converge | PASS |
| S4 | Location and strength error computable against known-source experiments | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# source_id/plume_inverse_s1_ideal.yaml
principle_ref: sha256:<p423_hash>
omega:
  domain: [0, 5000, 0, 5000]   # m
  sensors: 20
  time_samples: 50
E:
  forward: "2D ADE: ∂C/∂t + u·∇C = D∇²C + Q δ(x−x_s)"
  inverse: "MCMC on P(x_s, Q_s | C_obs)"
  u: [3.0, 0.5]   # m/s wind
  D: 5.0   # m²/s
B:
  prior: {x_s: uniform_domain, Q_s: log_uniform(1, 1000)}
I:
  scenario: single_continuous_source
  noise_levels: [0.01, 0.05, 0.10]
  sensor_counts: [5, 10, 20]
O: [location_error, Q_relative_error, 95CI_coverage]
epsilon:
  location_error_max: 50.0   # m
  Q_error_max: 0.20
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 20 sensors over 5 km domain adequate for single source | PASS |
| S2 | Bayesian posterior converges with 50 time samples | PASS |
| S3 | MCMC with 10⁵ samples explores posterior adequately | PASS |
| S4 | Location error < 50 m achievable at 1% noise with 20 sensors | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# source_id/benchmark_plume.yaml
spec_ref: sha256:<spec423_hash>
principle_ref: sha256:<p423_hash>
dataset:
  name: synthetic_plume_source
  reference: "Synthetic plume with known source parameters"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Adjoint-gradient
    params: {iterations: 100}
    results: {loc_err: 35, Q_err: 0.08}
  - solver: MCMC-MH
    params: {samples: 1e5}
    results: {loc_err: 25, Q_err: 0.05}
  - solver: Ensemble-smoother
    params: {ensemble: 500}
    results: {loc_err: 30, Q_err: 0.06}
quality_scoring:
  - {max_loc_err: 10, Q: 1.00}
  - {max_loc_err: 30, Q: 0.90}
  - {max_loc_err: 50, Q: 0.80}
  - {max_loc_err: 100, Q: 0.75}
```

**Baseline solver:** MCMC-MH — location error 25 m
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Location Error (m) | Q Error | Runtime | Q |
|--------|-------------------|---------|---------|---|
| Adjoint-gradient | 35 | 0.08 | 10 s | 0.80 |
| Ensemble-smoother | 30 | 0.06 | 30 s | 0.90 |
| MCMC-MH | 25 | 0.05 | 120 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case: 500 × 0.90 = 450 PWM
Floor:     500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p423_hash>",
  "h_s": "sha256:<spec423_hash>",
  "h_b": "sha256:<bench423_hash>",
  "r": {"loc_err": 25, "Q_err": 0.05, "coverage_95": 0.94},
  "c": {"MCMC_samples": 1e5, "K": 3},
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
| L4 Solution | — | 375–450 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep source_id
pwm-node verify AF_environmental_science/source_id_s1_ideal.yaml
pwm-node mine AF_environmental_science/source_id_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
