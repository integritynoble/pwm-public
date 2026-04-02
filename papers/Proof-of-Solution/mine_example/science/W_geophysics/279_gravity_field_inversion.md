# Principle #279 — Gravity Field Inversion

**Domain:** Geophysics | **Carrier:** N/A (potential field inverse) | **Difficulty:** Standard (δ=3)
**DAG:** K.green.newton → ∫.volume |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.green.newton→∫.volume      grav-inv    density-2D        Tikhonov
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  GRAVITY FIELD INVERSION          P = (E,G,W,C)   Principle #279│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ g(x) = G ∫ Δρ(x') (x−x')/|x−x'|³ dV'  (Newton)      │
│        │ Δρ = density contrast; g = gravity anomaly             │
│        │ Forward: given Δρ(x) → compute g at surface            │
│        │ Inverse: given g(x_obs) → recover Δρ(x) at depth      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.green.newton] ──→ [∫.volume]                        │
│        │ kernel  integrate                                      │
│        │ V={K.green.newton, ∫.volume}  A={K.green.newton→∫.volume}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Newtonian potential well-defined)      │
│        │ Uniqueness: NO (inherent non-uniqueness of pot. fields)│
│        │ Stability: ill-posed; depth weighting + reg required   │
│        │ Mismatch: regional trend removal, terrain correction   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖Δρ_rec − Δρ_true‖₂ / ‖Δρ_true‖₂ (relative L2)  │
│        │ q = 1.0 (Tikhonov), 2.0 (compact inversion)          │
│        │ T = {data_misfit, model_norm, depth_resolution}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Newton's integral dimensionally correct; kernel well-formed | PASS |
| S2 | Tikhonov + depth weighting constrains non-uniqueness | PASS |
| S3 | CG solver converges for discretised kernel matrix | PASS |
| S4 | Relative L2 error bounded by noise, depth, and regularisation | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# grav_inv/density_2d_s1_ideal.yaml
principle_ref: sha256:<p279_hash>
omega:
  grid: [50, 20]
  domain: cross_section_2D
  depth_range: [0, 2000]  # metres
E:
  forward: "g = G ∫ Δρ (z/r³) dA  (2-D line integral)"
  stations: 50
  noise_std: 0.05  # mGal
B:
  depth_weighting: z^1.5
  regional_removed: true
I:
  scenario: buried_dyke
  true_density_contrast: 500  # kg/m³
  depth: [200, 800]
O: [L2_density_error, data_misfit, depth_extent]
epsilon:
  L2_error_max: 1.0e-1
  chi2_max: 1.10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 50 stations over 5 km profile; 50×20 cells adequate | PASS |
| S2 | Depth weighting z^1.5 counteracts kernel decay | PASS |
| S3 | CG with Tikhonov converges in <50 iterations | PASS |
| S4 | L2 error < 10% achievable for 500 kg/m³ contrast | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# grav_inv/benchmark_density.yaml
spec_ref: sha256:<spec279_hash>
principle_ref: sha256:<p279_hash>
dataset:
  name: synthetic_buried_dyke
  reference: "50-station 2-D gravity profile"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Tikhonov-CG
    params: {lambda: 1e-2, depth_weight: z1.5}
    results: {L2_error: 8.5e-2, chi2: 1.05}
  - solver: Compact-Inversion
    params: {p_norm: 1, lambda: 1e-3}
    results: {L2_error: 6.2e-2, chi2: 1.03}
  - solver: Bayesian-MCMC
    params: {samples: 20000, chains: 4}
    results: {L2_error: 5.5e-2, chi2: 1.02}
quality_scoring:
  - {min_L2: 3.0e-2, Q: 1.00}
  - {min_L2: 6.0e-2, Q: 0.90}
  - {min_L2: 1.0e-1, Q: 0.80}
  - {min_L2: 2.0e-1, Q: 0.75}
```

**Baseline solver:** Tikhonov-CG — L2 error 8.5×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | χ² | Runtime | Q |
|--------|----------|----|---------|---|
| Tikhonov-CG | 8.5e-2 | 1.05 | 2 s | 0.80 |
| Compact-L1 | 6.2e-2 | 1.03 | 5 s | 0.90 |
| Bayesian-MCMC | 5.5e-2 | 1.02 | 60 s | 0.90 |
| Joint grav+mag | 2.8e-2 | 1.01 | 120 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (joint): 300 × 1.00 = 300 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p279_hash>",
  "h_s": "sha256:<spec279_hash>",
  "h_b": "sha256:<bench279_hash>",
  "r": {"residual_norm": 2.8e-2, "error_bound": 1.0e-1, "ratio": 0.28},
  "c": {"fitted_rate": 1.02, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep grav_inv
pwm-node verify grav_inv/density_2d_s1_ideal.yaml
pwm-node mine grav_inv/density_2d_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
