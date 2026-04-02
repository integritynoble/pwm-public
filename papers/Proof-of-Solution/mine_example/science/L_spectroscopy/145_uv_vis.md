# Principle #145 — UV-Vis Absorption Spectroscopy

**Domain:** Spectroscopy | **Carrier:** Photon (UV-Vis) | **Difficulty:** Textbook (δ=1)
**DAG:** G.broadband --> L.diag.spectral --> N.pointwise | **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.broadband-->L.diag.spectral-->N.pointwise    UVVis       UVVisMix-20        Deconv
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  UV-VIS ABSORPTION SPECTROSCOPY   P = (E, G, W, C)   #145      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ A(λ) = −log₁₀(I/I₀) = Σ_k ε_k(λ) · c_k · l         │
│        │ Beer-Lambert law: absorbance linear in concentration   │
│        │ ε = molar absorptivity; l = path length                │
│        │ Inverse: determine c_k from multi-wavelength absorbance│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.broadband] --> [L.diag.spectral] --> [N.pointwise]    │
│        │  BroadbandSource  SpectralFilter  Absorption           │
│        │ V={G.broadband, L.diag.spectral, N.pointwise}  A={G.broadband-->L.diag.spectral, L.diag.spectral-->N.pointwise}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (electronic transitions always present) │
│        │ Uniqueness: YES (multi-λ resolves ≤ N components)      │
│        │ Stability: κ ≈ 3 (well-separated bands), κ ≈ 20 (over)│
│        │ Mismatch: stray light, non-linearity at high A, scatter│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = concentration RMSE (primary), R² (secondary)       │
│        │ q = 2.0 (linear least-squares exact)                   │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Wavelength range 200–800 nm, bandwidth ≤ 2 nm, path length calibrated | PASS |
| S2 | ε spectra linearly independent for target analytes → unique solution | PASS |
| S3 | NNLS converges in single step for overdetermined system | PASS |
| S4 | Concentration RMSE ≤ 2% for A in [0.1, 1.5] range | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# uv_vis/uvvismix_s1.yaml
principle_ref: sha256:<p145_hash>
omega:
  wavelength_range_nm: [200, 800]
  bandwidth_nm: 1.0
  path_cm: 1.0
  spectral_points: 601
E:
  forward: "A(lambda) = sum_k eps_k(lambda) * c_k * l"
  solver: "NNLS"
I:
  dataset: UVVisMix_20
  spectra: 20
  noise: {type: gaussian, sigma_abs: 0.002}
  scenario: ideal
O: [concentration_RMSE_pct, R_squared]
epsilon:
  concentration_RMSE_max: 3.0
  R_squared_min: 0.995
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200–800 nm at 1 nm bandwidth covers UV-Vis electronic transitions | PASS |
| S2 | κ ≈ 3 for well-separated chromophores at σ = 0.002 | PASS |
| S3 | Linear least-squares converges in one step | PASS |
| S4 | RMSE ≤ 3% and R² ≥ 0.995 feasible | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# uv_vis/benchmark_s1.yaml
spec_ref: sha256:<spec145_hash>
principle_ref: sha256:<p145_hash>
dataset:
  name: UVVisMix_20
  spectra: 20
  wavelength_points: 601
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Single-Lambda
    params: {wavelength_nm: 450}
    results: {concentration_RMSE_pct: 5.0, R_squared: 0.985}
  - solver: CLS
    params: {method: classical_least_squares}
    results: {concentration_RMSE_pct: 2.0, R_squared: 0.998}
  - solver: PLS-UVVis
    params: {n_components: 4}
    results: {concentration_RMSE_pct: 1.2, R_squared: 0.999}
quality_scoring:
  - {max_RMSE: 1.5, Q: 1.00}
  - {max_RMSE: 2.5, Q: 0.90}
  - {max_RMSE: 3.5, Q: 0.80}
  - {max_RMSE: 5.0, Q: 0.75}
```

**Baseline solver:** CLS — RMSE 2.0%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Conc. RMSE (%) | R² | Runtime | Q |
|--------|----------------|------|---------|---|
| Single-Lambda | 5.0 | 0.985 | 0.01 s | 0.75 |
| CLS | 2.0 | 0.998 | 0.05 s | 0.88 |
| PLS-UVVis | 1.2 | 0.999 | 0.1 s | 1.00 |
| ANN-UVVis | 1.0 | 0.999 | 0.05 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (PLS/ANN):   100 × 1.00 = 100 PWM
Floor:                 100 × 0.75 = 75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p145_hash>",
  "h_s": "sha256:<spec145_hash>",
  "h_b": "sha256:<bench145_hash>",
  "r": {"residual_norm": 0.010, "error_bound": 0.03, "ratio": 0.33},
  "c": {"fitted_rate": 1.98, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 75–100 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep uv_vis
pwm-node verify uv_vis/uvvismix_s1.yaml
pwm-node mine uv_vis/uvvismix_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
