# Principle #293 — Subsurface Temperature Inversion

**Domain:** Geophysics | **Carrier:** N/A (heat equation inverse) | **Difficulty:** Standard (δ=3)
**DAG:** ∂.space.laplacian → B.dirichlet → O.tikhonov |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.space.laplacian→B.dirichlet→O.tikhonov      temp-inv    borehole-T        Tikhonov
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SUBSURFACE TEMPERATURE INVERSION P = (E,G,W,C)  Principle #293 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂T/∂t = κ ∂²T/∂z²  (1-D heat diffusion)              │
│        │ T(z,t) = T_s(t) ⊛ G(z,t)  (convolution with Green's)  │
│        │ Forward: given T_s(t) surface history → T(z) profile   │
│        │ Inverse: given borehole T(z) → recover T_s(t) history  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.space.laplacian] ──→ [B.dirichlet] ──→ [O.tikhonov] │
│        │ derivative  boundary  optimize                         │
│        │ V={∂.space.laplacian, B.dirichlet, O.tikhonov}  A={∂.space.laplacian→B.dirichlet, B.dirichlet→O.tikhonov}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (heat equation backward in time)        │
│        │ Uniqueness: severely ill-posed (exponential damping)   │
│        │ Stability: Tikhonov regularisation essential            │
│        │ Mismatch: groundwater advection, thermal conductivity  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖T_s,rec − T_s,true‖₂ / ‖T_s,true‖₂ (relative)   │
│        │ q = 1.0 (Tikhonov), 2.0 (singular value truncation)  │
│        │ T = {profile_misfit, history_resolution, depth_of_info}│
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Heat equation and Green's function dimensionally correct | PASS |
| S2 | Tikhonov/SVD truncation regularises backward-in-time inversion | PASS |
| S3 | SVD inversion converges for 500 m borehole with 1 m sampling | PASS |
| S4 | Surface history resolution ~50 yr for last 500 yr from 500 m hole | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# temp_inv/borehole_s1_ideal.yaml
principle_ref: sha256:<p293_hash>
omega:
  depth_range: [0, 500]  # metres
  sampling: 1.0  # metre
  time_range: [0, 500]  # years before present
E:
  forward: "1-D heat diffusion Green's function"
  thermal_diffusivity: 1.0e-6  # m²/s
  geothermal_gradient: 0.025  # K/m
B:
  bottom: constant_heat_flux
  surface: free
I:
  scenario: Little_Ice_Age_warming
  surface_temp_change: 1.5  # K over 200 years
  noise_std: 0.02  # K
O: [surface_history_L2, profile_misfit, resolution_length]
epsilon:
  history_L2_max: 1.0e-1
  profile_misfit_max: 0.05  # K
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 500 depth samples; thermal diffusivity = 1e-6 m²/s standard | PASS |
| S2 | SVD truncation at noise level ensures stable inversion | PASS |
| S3 | Tikhonov inversion converges for regularisation parameter from GCV | PASS |
| S4 | History error < 10% for centennial-scale temperature changes | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# temp_inv/benchmark_borehole.yaml
spec_ref: sha256:<spec293_hash>
principle_ref: sha256:<p293_hash>
dataset:
  name: synthetic_LIA_warming
  reference: "500-m borehole, 1.5 K warming signal"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: SVD-truncated
    params: {singular_values: 10}
    results: {history_L2: 1.2e-1, profile_misfit: 0.04}
  - solver: Tikhonov-GCV
    params: {lambda: auto_GCV}
    results: {history_L2: 8.5e-2, profile_misfit: 0.03}
  - solver: Bayesian-MCMC
    params: {samples: 20000, prior: smooth}
    results: {history_L2: 6.2e-2, profile_misfit: 0.02}
quality_scoring:
  - {min_L2: 3.0e-2, Q: 1.00}
  - {min_L2: 7.0e-2, Q: 0.90}
  - {min_L2: 1.0e-1, Q: 0.80}
  - {min_L2: 2.0e-1, Q: 0.75}
```

**Baseline solver:** Tikhonov-GCV — history L2 8.5×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | History L2 | Profile Misfit (K) | Runtime | Q |
|--------|------------|---------------------|---------|---|
| SVD-truncated | 1.2e-1 | 0.04 | 0.1 s | 0.80 |
| Tikhonov-GCV | 8.5e-2 | 0.03 | 0.5 s | 0.90 |
| Bayesian-MCMC | 6.2e-2 | 0.02 | 30 s | 0.90 |
| Multi-borehole joint | 2.5e-2 | 0.01 | 120 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (multi-bore): 300 × 1.00 = 300 PWM
Floor:                  300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p293_hash>",
  "h_s": "sha256:<spec293_hash>",
  "h_b": "sha256:<bench293_hash>",
  "r": {"residual_norm": 2.5e-2, "error_bound": 1.0e-1, "ratio": 0.25},
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
pwm-node benchmarks | grep temp_inv
pwm-node verify temp_inv/borehole_s1_ideal.yaml
pwm-node mine temp_inv/borehole_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
