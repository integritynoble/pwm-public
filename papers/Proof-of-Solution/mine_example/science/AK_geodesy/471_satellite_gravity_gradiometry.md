# Principle #471 — Satellite Gravity Gradiometry (GOCE)

**Domain:** Geodesy | **Carrier:** N/A (PDE-based) | **Difficulty:** Advanced (δ=4)
**DAG:** [∂.space] --> [L.dense] --> [O.l2] | **Reward:** 4× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.x-->L.dense-->O.l2  GravGrad  GOCE-data  SH-analysis
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SATELLITE GRAVITY GRADIOMETRY (GOCE) P=(E,G,W,C) Princ. #471  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ T_ij = ∂²V/∂x_i∂x_j  (gravity gradient tensor)       │
│        │ V(r,θ,λ) = (GM/R) Σ (R/r)^(n+1) Σ (C_nm cos mλ      │
│        │            + S_nm sin mλ) P_nm(cos θ)  (SH expansion) │
│        │ ∇²V = 0 outside masses  (Laplace equation)            │
│        │ Forward: given SH coefficients → T_ij at satellite     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.x] ──→ [L.dense] ──→ [O.l2]                         │
│        │  gradient-tensor  Gram-matrix  least-squares           │
│        │ V={∂.x,L.dense,O.l2}  A={∂.x→L.dense,L.dense→O.l2}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (SH expansion converges outside sphere) │
│        │ Uniqueness: YES up to maximum resolved degree          │
│        │ Stability: ill-posed at high degree; regularization    │
│        │ Mismatch: gradiometer noise, temporal aliasing         │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = geoid commission error (cm) at degree N_max        │
│        │ q = N/A (spectral truncation)                         │
│        │ T = {geoid_error, degree_variance, gradient_residual}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Gradient tensor symmetric trace-free (5 independent components) | PASS |
| S2 | SH expansion converges; Laplace equation satisfied outside | PASS |
| S3 | Direct and space-wise approaches converge to degree 250+ | PASS |
| S4 | Geoid commission error < 2 cm at degree 200 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# grav_grad/goce_sh_s1.yaml
principle_ref: sha256:<p471_hash>
omega:
  observations: 500_million
  domain: global_satellite_altitude_250km
  time: [0, 126230400.0]   # 4 years
E:
  forward: "SH synthesis of gravity gradients at satellite altitude"
  max_degree: 280
  reference: GRS80
B:
  gradiometer: GOCE_EGG
  noise_PSD: 10_mE/√Hz_in_MBW
  orbit: near_polar_sun_synchronous
I:
  scenario: GOCE_gravity_field_recovery
  approaches: [direct, space_wise, time_wise]
O: [geoid_commission_error_cm, degree_variance, gradient_residual_mE]
epsilon:
  geoid_error_max: 2.0     # cm at degree 200
  gradient_residual_max: 5.0   # mE
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 500M observations; gradiometer MBW well-characterized | PASS |
| S2 | Near-polar orbit provides global coverage (polar gap ~6°) | PASS |
| S3 | All three approaches produce consistent SH models | PASS |
| S4 | Geoid error < 2 cm at degree 200 from GOCE alone | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# grav_grad/benchmark_goce.yaml
spec_ref: sha256:<spec471_hash>
principle_ref: sha256:<p471_hash>
dataset:
  name: GOCE_gravity_field_models
  reference: "Pail et al. (2011) GOCE gravity field models"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Direct approach
    params: {max_degree: 240, regularization: Kaula}
    results: {geoid_error_cm: 2.5, degree_variance_match: 0.95}
  - solver: Space-wise approach
    params: {max_degree: 280, LSCC: local_covariance}
    results: {geoid_error_cm: 1.8, degree_variance_match: 0.97}
  - solver: Time-wise approach
    params: {max_degree: 280, AR_filter: causal}
    results: {geoid_error_cm: 1.6, degree_variance_match: 0.98}
quality_scoring:
  - {min_err_cm: 1.0, Q: 1.00}
  - {min_err_cm: 2.0, Q: 0.90}
  - {min_err_cm: 3.0, Q: 0.80}
  - {min_err_cm: 5.0, Q: 0.75}
```

**Baseline solver:** Time-wise approach — geoid error 1.6 cm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Geoid Error (cm) | Deg Variance | Runtime | Q |
|--------|-----------------|-------------|---------|---|
| Direct (N=240) | 2.5 | 0.95 | 3600 s | 0.80 |
| Space-wise (N=280) | 1.8 | 0.97 | 7200 s | 0.90 |
| Time-wise (N=280) | 1.6 | 0.98 | 5400 s | 0.90 |
| Combined (GOCE+GRACE) | 0.9 | 0.99 | 10800 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 4 × 1.0 × Q
Best case (combined): 400 × 1.00 = 400 PWM
Floor:                400 × 0.75 = 300 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p471_hash>",
  "h_s": "sha256:<spec471_hash>",
  "h_b": "sha256:<bench471_hash>",
  "r": {"geoid_error_cm": 0.9, "error_bound": 2.0, "ratio": 0.450},
  "c": {"max_degree": 280, "observations": 5e8, "K": 3},
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
| L4 Solution | — | 300–400 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep grav_grad
pwm-node verify grav_grad/goce_sh_s1.yaml
pwm-node mine grav_grad/goce_sh_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
