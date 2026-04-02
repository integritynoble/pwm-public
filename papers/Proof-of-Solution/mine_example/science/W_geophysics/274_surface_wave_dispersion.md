# Principle #274 — Surface Wave Dispersion Inversion

**Domain:** Geophysics | **Carrier:** N/A (1-D inverse) | **Difficulty:** Standard (δ=3)
**DAG:** E.hermitian → ∫.path → O.tikhonov |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E.hermitian→∫.path→O.tikhonov      sw-disp     1D-profile        linearised
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SURFACE WAVE DISPERSION INVERSION P = (E,G,W,C)  Principle #274│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ c(f) = F[Vs(z), Vp(z), ρ(z)]  (dispersion relation)   │
│        │ Rayleigh/Love wave phase/group velocity vs frequency    │
│        │ Forward: given Vs(z) profile → compute c(f)            │
│        │ Inverse: given observed c(f) → recover Vs(z)           │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [E.hermitian] ──→ [∫.path] ──→ [O.tikhonov]            │
│        │ eigensolve  integrate  optimize                        │
│        │ V={E.hermitian, ∫.path, O.tikhonov}  A={E.hermitian→∫.path, ∫.path→O.tikhonov}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (secular equation has real roots)       │
│        │ Uniqueness: conditional; mode identification needed    │
│        │ Stability: moderate; depth resolution degrades with z  │
│        │ Mismatch: higher-mode contamination, near-field effects│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖Vs_rec − Vs_true‖₂ / ‖Vs_true‖₂ (relative L2)   │
│        │ q = 1.0 (linearised), 2.0 (neighbourhood algorithm)  │
│        │ T = {data_misfit, depth_resolution, mode_fit}          │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Vs/frequency dimensions consistent; secular equation well-formed | PASS |
| S2 | Damped least-squares ensures stable inversion for layered model | PASS |
| S3 | Linearised inversion converges for 10-layer models with f=1–50 Hz | PASS |
| S4 | Relative L2 error bounded by frequency bandwidth and noise level | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# sw_disp/layered_s1_ideal.yaml
principle_ref: sha256:<p274_hash>
omega:
  layers: 10
  depth_max: 50.0  # metres
  freq_range: [1.0, 50.0]
E:
  forward: "secular equation for Rayleigh wave"
  num_freq: 50
  noise_std: 5.0  # m/s
B:
  half_space: {Vs: 500, Vp: 1000, rho: 2000}
I:
  scenario: layered_gradient
  layers: 10
  Vs_range: [100, 500]
O: [L2_Vs_error, dispersion_misfit, depth_resolution]
epsilon:
  L2_error_max: 5.0e-2
  misfit_max: 10.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 50 frequencies over 1–50 Hz adequate for 10 layers | PASS |
| S2 | Damped least-squares with λ auto-tuned ensures convergence | PASS |
| S3 | Linearised inversion converges in <20 iterations | PASS |
| S4 | L2 error < 5% achievable with 5 m/s noise | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# sw_disp/benchmark_layered.yaml
spec_ref: sha256:<spec274_hash>
principle_ref: sha256:<p274_hash>
dataset:
  name: synthetic_layered_gradient
  reference: "10-layer Vs gradient model"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Linearised-LeastSquares
    params: {iterations: 20, damping: 0.1}
    results: {L2_error: 4.2e-2, misfit: 7.5}
  - solver: Neighbourhood-Algorithm
    params: {samples: 5000, resamples: 1000}
    results: {L2_error: 3.1e-2, misfit: 5.8}
  - solver: MCMC-Bayesian
    params: {chains: 4, samples: 10000}
    results: {L2_error: 2.8e-2, misfit: 5.2}
quality_scoring:
  - {min_L2: 1.0e-2, Q: 1.00}
  - {min_L2: 3.0e-2, Q: 0.90}
  - {min_L2: 5.0e-2, Q: 0.80}
  - {min_L2: 1.0e-1, Q: 0.75}
```

**Baseline solver:** Linearised-LS — L2 error 4.2×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Misfit | Runtime | Q |
|--------|----------|--------|---------|---|
| Linearised-LS | 4.2e-2 | 7.5 | 2 s | 0.80 |
| Neighbourhood-Alg | 3.1e-2 | 5.8 | 30 s | 0.90 |
| MCMC-Bayesian | 2.8e-2 | 5.2 | 120 s | 0.90 |
| Trans-D Bayesian | 9.5e-3 | 4.8 | 300 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (Trans-D): 300 × 1.00 = 300 PWM
Floor:               300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p274_hash>",
  "h_s": "sha256:<spec274_hash>",
  "h_b": "sha256:<bench274_hash>",
  "r": {"residual_norm": 9.5e-3, "error_bound": 5.0e-2, "ratio": 0.19},
  "c": {"fitted_rate": 1.10, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep sw_disp
pwm-node verify sw_disp/layered_s1_ideal.yaml
pwm-node mine sw_disp/layered_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
