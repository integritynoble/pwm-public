# Principle #272 — Seismic Travel-time Tomography

**Domain:** Geophysics | **Carrier:** N/A (ray-based inverse) | **Difficulty:** Standard (δ=3)
**DAG:** K.green → ∫.path → O.tikhonov |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.green→∫.path→O.tikhonov      tomo-tt     cross-hole-2D     LSQR/CG
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SEISMIC TRAVEL-TIME TOMOGRAPHY   P = (E,G,W,C)   Principle #272│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ t_i = ∫_{ray_i} s(x) dl   (travel-time integral)      │
│        │ s(x) = 1/v(x) = slowness field                        │
│        │ Forward: given s(x) → compute t_i via ray tracing      │
│        │ Inverse: given {t_i} → recover s(x) over Ω             │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.green] ──→ [∫.path] ──→ [O.tikhonov]                │
│        │ kernel  integrate  optimize                            │
│        │ V={K.green, ∫.path, O.tikhonov}  A={K.green→∫.path, ∫.path→O.tikhonov}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Fredholm integral of 1st kind)         │
│        │ Uniqueness: conditional on ray coverage (Radon-type)   │
│        │ Stability: ill-posed; regularisation required (Tikhonov)│
│        │ Mismatch: picking error, ray-bending neglect           │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖s_rec − s_true‖₂ / ‖s_true‖₂ (relative L2)      │
│        │ q = 1.0 (ray-based), 2.0 (finite-freq kernel)        │
│        │ T = {data_misfit, model_norm, resolution_matrix}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Slowness/travel-time dimensions consistent; ray integral well-formed | PASS |
| S2 | Tikhonov-regularised normal equations guarantee stable least-squares solution | PASS |
| S3 | LSQR/SIRT converge for well-sampled geometries with >100 rays | PASS |
| S4 | Relative L2 error bounded by data noise and regularisation parameter | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# tomo_tt/cross_hole_s1_ideal.yaml
principle_ref: sha256:<p272_hash>
omega:
  grid: [100, 100]
  domain: cross_hole_2D
  time: N/A
  dt: N/A
E:
  forward: "t_i = ∫ s(x) dl along ray_i"
  num_rays: 500
  noise_std: 0.001
B:
  source_positions: left_boundary
  receiver_positions: right_boundary
I:
  scenario: cross_hole_checkerboard
  cells: [100, 100]
  regularisation: Tikhonov_lambda_1e-3
O: [L2_slowness_error, data_misfit_chi2, resolution_spread]
epsilon:
  L2_error_max: 5.0e-2
  chi2_max: 1.05
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 500 rays adequate for 100² cells; overdetermined system | PASS |
| S2 | Tikhonov λ=10⁻³ ensures unique minimum of regularised functional | PASS |
| S3 | LSQR converges in <200 iterations for this geometry | PASS |
| S4 | L2 error < 5×10⁻² achievable with 0.1% noise | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# tomo_tt/benchmark_cross_hole.yaml
spec_ref: sha256:<spec272_hash>
principle_ref: sha256:<p272_hash>
dataset:
  name: synthetic_checkerboard_100x100
  reference: "Synthetic cross-hole geometry, 500 rays"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: LSQR
    params: {iterations: 200, lambda: 1.0e-3}
    results: {L2_error: 3.8e-2, chi2: 1.02}
  - solver: SIRT
    params: {iterations: 500, lambda: 1.0e-3}
    results: {L2_error: 4.5e-2, chi2: 1.04}
  - solver: Conjugate-Gradient
    params: {iterations: 150, lambda: 1.0e-3}
    results: {L2_error: 3.5e-2, chi2: 1.01}
quality_scoring:
  - {min_L2: 1.0e-2, Q: 1.00}
  - {min_L2: 3.0e-2, Q: 0.90}
  - {min_L2: 5.0e-2, Q: 0.80}
  - {min_L2: 1.0e-1, Q: 0.75}
```

**Baseline solver:** LSQR — L2 error 3.8×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | χ² | Runtime | Q |
|--------|----------|----|---------|---|
| SIRT | 4.5e-2 | 1.04 | 8 s | 0.80 |
| LSQR | 3.8e-2 | 1.02 | 3 s | 0.90 |
| CG-regularised | 3.5e-2 | 1.01 | 4 s | 0.90 |
| CG + TV-reg | 1.2e-2 | 1.01 | 10 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (CG+TV): 300 × 1.00 = 300 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p272_hash>",
  "h_s": "sha256:<spec272_hash>",
  "h_b": "sha256:<bench272_hash>",
  "r": {"residual_norm": 1.2e-2, "error_bound": 5.0e-2, "ratio": 0.24},
  "c": {"fitted_rate": 1.05, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep tomo_tt
pwm-node verify tomo_tt/cross_hole_s1_ideal.yaml
pwm-node mine tomo_tt/cross_hole_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
