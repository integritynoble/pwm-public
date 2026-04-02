# Principle #283 — Electrical Resistivity Tomography (ERT)

**Domain:** Geophysics | **Carrier:** N/A (DC resistivity inverse) | **Difficulty:** Standard (δ=3)
**DAG:** K.green → L.sparse → O.tikhonov |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.green→L.sparse→O.tikhonov      ert-inv     resistivity-2D    GN-smooth
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ELECTRICAL RESISTIVITY TOMOGRAPHY P = (E,G,W,C)  Principle #283│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∇·(σ∇φ) = −Iδ(x−x_s)  (DC resistivity equation)      │
│        │ ρ_a = K · ΔV/I  (apparent resistivity from 4-electrode)│
│        │ Forward: given σ(x) → solve Laplace for φ → ρ_a       │
│        │ Inverse: given ρ_a measurements → recover σ(x,z)      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.green] ──→ [L.sparse] ──→ [O.tikhonov]              │
│        │ kernel  linear-op  optimize                            │
│        │ V={K.green, L.sparse, O.tikhonov}  A={K.green→L.sparse, L.sparse→O.tikhonov}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (elliptic PDE, unique φ for given σ)    │
│        │ Uniqueness: YES for sufficient electrode coverage      │
│        │ Stability: moderate; regularisation needed for depth    │
│        │ Mismatch: electrode contact resistance, 3-D effects    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = ‖log σ_rec − log σ_true‖₂ / ‖log σ_true‖₂        │
│        │ q = 1.0 (L2-smooth), 2.0 (L1-blocky)                 │
│        │ T = {data_misfit_RMS, model_roughness, DOI}            │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Poisson equation with source well-formed; geometric factor K correct | PASS |
| S2 | Gauss-Newton with smooth regularisation ensures stable inversion | PASS |
| S3 | GN converges for Wenner/dipole-dipole arrays with 48 electrodes | PASS |
| S4 | Log-resistivity error bounded by data error and electrode spacing | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# ert_inv/resistivity_2d_s1_ideal.yaml
principle_ref: sha256:<p283_hash>
omega:
  grid: [96, 24]
  domain: surface_2D
  electrodes: 48
  spacing: 2.0  # metres
E:
  forward: "FE solution of ∇·(σ∇φ) = −Iδ(x−x_s)"
  array: dipole_dipole
  measurements: 1128
  noise_std: 2%  # of |ρ_a|
B:
  surface: flat
  depth_investigation: 20  # metres
I:
  scenario: buried_cavity
  background_resistivity: 100  # Ohm·m
  cavity_resistivity: 10000  # Ohm·m (air-filled)
  depth: [3, 8]
O: [log_resistivity_L2, RMS_misfit, DOI]
epsilon:
  L2_error_max: 1.0e-1
  RMS_max: 1.05
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1128 measurements from 48 electrodes; dipole-dipole well-suited | PASS |
| S2 | GN with L2 regularisation ensures convergent inversion | PASS |
| S3 | Converges in <10 GN iterations to RMS ≈ 1.0 | PASS |
| S4 | Log-resistivity error < 10% for cavity at 3–8 m depth | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# ert_inv/benchmark_cavity.yaml
spec_ref: sha256:<spec283_hash>
principle_ref: sha256:<p283_hash>
dataset:
  name: synthetic_buried_cavity
  reference: "48-electrode dipole-dipole survey"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: L2-smooth-GN
    params: {iterations: 7, lambda: 10}
    results: {L2_error: 8.8e-2, RMS: 1.02}
  - solver: L1-blocky-IRLS
    params: {iterations: 10, lambda: 5}
    results: {L2_error: 6.5e-2, RMS: 1.01}
  - solver: Bayesian-MCMC
    params: {samples: 50000, chains: 4}
    results: {L2_error: 5.8e-2, RMS: 1.00}
quality_scoring:
  - {min_L2: 3.0e-2, Q: 1.00}
  - {min_L2: 6.0e-2, Q: 0.90}
  - {min_L2: 1.0e-1, Q: 0.80}
  - {min_L2: 2.0e-1, Q: 0.75}
```

**Baseline solver:** L2-smooth-GN — L2 error 8.8×10⁻²
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | RMS | Runtime | Q |
|--------|----------|-----|---------|---|
| L2-smooth-GN | 8.8e-2 | 1.02 | 5 s | 0.80 |
| L1-blocky-IRLS | 6.5e-2 | 1.01 | 12 s | 0.90 |
| Bayesian-MCMC | 5.8e-2 | 1.00 | 300 s | 0.90 |
| 3D-GN unstructured | 2.5e-2 | 1.00 | 120 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (3D-GN): 300 × 1.00 = 300 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p283_hash>",
  "h_s": "sha256:<spec283_hash>",
  "h_b": "sha256:<bench283_hash>",
  "r": {"residual_norm": 2.5e-2, "error_bound": 1.0e-1, "ratio": 0.25},
  "c": {"fitted_rate": 1.08, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep ert_inv
pwm-node verify ert_inv/resistivity_2d_s1_ideal.yaml
pwm-node mine ert_inv/resistivity_2d_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
