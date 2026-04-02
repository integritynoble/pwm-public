# Principle #285 — Satellite Gravity Recovery (GRACE)

**Domain:** Geophysics | **Carrier:** N/A (spherical harmonic inverse) | **Difficulty:** Hard (δ=5)
**DAG:** K.green.newton → ∫.volume → O.tikhonov |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.green.newton→∫.volume→O.tikhonov      grace-inv   mass-change       SH-analysis
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SATELLITE GRAVITY RECOVERY (GRACE) P=(E,G,W,C)   Principle #285│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ V(r,θ,λ) = (GM/R)Σ(R/r)^(l+1) Σ(C_lm cos mλ          │
│        │            + S_lm sin mλ) P_lm(cosθ)                  │
│        │ ΔC_lm(t) → Δσ(θ,λ) surface mass density change        │
│        │ Forward: given Δσ → predict inter-satellite range-rate │
│        │ Inverse: given K-band ranging → recover ΔC_lm monthly  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.green.newton] ──→ [∫.volume] ──→ [O.tikhonov]       │
│        │ kernel  integrate  optimize                            │
│        │ V={K.green.newton, ∫.volume, O.tikhonov}  A={K.green.newton→∫.volume, ∫.volume→O.tikhonov}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (SH expansion converges for smooth field)│
│        │ Uniqueness: YES up to maximum SH degree (l_max~96)    │
│        │ Stability: high-degree noise; filtering required       │
│        │ Mismatch: aliasing from tides/atmosphere, N-S striping │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖Δσ_rec − Δσ_true‖₂ / ‖Δσ_true‖₂ (relative L2)  │
│        │ q = 1.0 (Gaussian filter), 2.0 (DDK/mascon)          │
│        │ T = {degree_variance, leakage_error, noise_level}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Spherical harmonic expansion well-defined; Stokes coefficients consistent | PASS |
| S2 | Monthly solutions exist up to degree 96 with GRACE-FO data | PASS |
| S3 | DDK filtering or mascon approach converges for mass balance | PASS |
| S4 | Mass change error bounded by degree truncation and filtering | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# grace_inv/mass_change_s1_ideal.yaml
principle_ref: sha256:<p285_hash>
omega:
  SH_degree_max: 96
  domain: global
  time_span: [2003, 2020]
  cadence: monthly
E:
  forward: "Stokes coefficients → surface mass density"
  filter: DDK5
  C20_replacement: SLR
B:
  dealiasing: AOD1B  # atmosphere+ocean
  GIA_correction: ICE6G-D
I:
  scenario: Greenland_ice_mass_loss
  region: [60N_80N, 20W_60W]
  trend: -260  # Gt/yr
O: [mass_trend_error, seasonal_amplitude, leakage_ratio]
epsilon:
  trend_error_max: 15  # Gt/yr
  leakage_max: 0.10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Degree-96 SH yields ~200 km spatial resolution; adequate for Greenland | PASS |
| S2 | DDK5 filter balances noise reduction and signal retention | PASS |
| S3 | Mascon inversion converges with regional constraint | PASS |
| S4 | Trend error < 15 Gt/yr with GIA correction | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# grace_inv/benchmark_greenland.yaml
spec_ref: sha256:<spec285_hash>
principle_ref: sha256:<p285_hash>
dataset:
  name: GRACE_Greenland_2003_2020
  reference: "GRACE/GRACE-FO Level-2 monthly solutions"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Gaussian-300km
    params: {radius: 300, l_max: 60}
    results: {trend_error: 22, leakage: 0.15}
  - solver: DDK5-SH
    params: {filter: DDK5, l_max: 96}
    results: {trend_error: 12, leakage: 0.08}
  - solver: Mascon-CRI
    params: {resolution: 3deg, constraints: regional}
    results: {trend_error: 8, leakage: 0.04}
quality_scoring:
  - {min_trend_err: 5, Q: 1.00}
  - {min_trend_err: 10, Q: 0.90}
  - {min_trend_err: 15, Q: 0.80}
  - {min_trend_err: 25, Q: 0.75}
```

**Baseline solver:** DDK5-SH — trend error 12 Gt/yr
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Trend Err (Gt/yr) | Leakage | Runtime | Q |
|--------|-------------------|---------|---------|---|
| Gaussian-300km | 22 | 0.15 | 5 s | 0.75 |
| DDK5-SH | 12 | 0.08 | 10 s | 0.90 |
| Mascon-CRI | 8 | 0.04 | 60 s | 0.90 |
| Mascon-Bayesian | 4 | 0.02 | 300 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (Bayesian): 500 × 1.00 = 500 PWM
Floor:                500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p285_hash>",
  "h_s": "sha256:<spec285_hash>",
  "h_b": "sha256:<bench285_hash>",
  "r": {"residual_norm": 4.0, "error_bound": 15.0, "ratio": 0.27},
  "c": {"fitted_rate": 1.85, "theoretical_rate": 2.0, "K": 4},
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
| L4 Solution | — | 375–500 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep grace_inv
pwm-node verify grace_inv/mass_change_s1_ideal.yaml
pwm-node mine grace_inv/mass_change_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
