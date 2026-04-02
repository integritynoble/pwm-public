# Principle #261 — Acoustic Scattering (BEM)

**Domain:** Acoustics | **Carrier:** Acoustic | **Difficulty:** Standard (δ=3)
**DAG:** K.green.acoustic → L.dense → B.surface |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.green.acoustic→L.dense→B.surface    scattering   sphere_plane_wave   BEM/FMM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  ACOUSTIC SCATTERING (BEM)           P = (E,G,W,C)   Principle #261 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ p_s(x) = ∫_Γ [G ∂p/∂n − p ∂G/∂n] dΓ                 │
│        │ Kirchhoff-Helmholtz boundary integral equation         │
│        │ Forward: given incident field, shape → scattered field │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.green.acoustic] ──→ [L.dense] ──→ [B.surface]       │
│        │ kernel  linear-op  boundary                            │
│        │ V={K.green.acoustic, L.dense, B.surface}  A={K.green.acoustic→L.dense, L.dense→B.surface}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Fredholm integral equation theory)     │
│        │ Uniqueness: YES (Burton-Miller removes fictitious eigs)│
│        │ Stability: condition number grows with ka              │
│        │ Mismatch: surface mesh resolution, integration order   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖p_s−p_ref‖/‖p_ref‖ (primary)  │
│        │ q = 2.0 (constant BEM), 4.0 (quadratic BEM)          │
│        │ T = {far_field_pattern, scattering_cross_section}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Incident field and scatterer geometry well-defined; Sommerfeld BC | PASS |
| S2 | BIE theory guarantees unique solution with Burton-Miller | PASS |
| S3 | BEM converges with 6+ elements per wavelength on surface | PASS |
| S4 | Scattered field L2 error bounded by BEM convergence analysis | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# scattering_bem/sphere_plane_wave.yaml
principle_ref: sha256:<p261_hash>
omega:
  scatterer: sphere
  radius: 1.0  # meters
  frequency: 500  # Hz
E:
  forward: "Kirchhoff-Helmholtz BIE for plane wave scattering"
  incident: plane_wave
B:
  surface: rigid (∂p/∂n = 0)
I:
  scenario: sphere_plane_wave_scattering
  mesh_densities: [4, 6, 10]  # elements per wavelength
O: [L2_scattered_error, far_field_pattern_error]
epsilon:
  L2_error_max: 1.0e-3
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Sphere ka=9.2 at 500 Hz; well-posed BIE | PASS |
| S2 | Analytic Mie-series solution exists for sphere | PASS |
| S3 | BEM with 10 elements/λ converges for ka~10 | PASS |
| S4 | L2 error < 10⁻³ achievable at 10 elements/λ | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# scattering_bem/benchmark_sphere.yaml
spec_ref: sha256:<spec261_hash>
principle_ref: sha256:<p261_hash>
dataset:
  name: sphere_scattering_reference
  reference: "Analytic Mie-series solution for rigid sphere"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: BEM-constant
    params: {elements_per_lambda: 6}
    results: {L2_error: 4.2e-2, max_error: 8.5e-2}
  - solver: BEM-linear
    params: {elements_per_lambda: 6}
    results: {L2_error: 1.8e-3, max_error: 4.5e-3}
  - solver: FMM-BEM
    params: {elements_per_lambda: 10, FMM_order: 5}
    results: {L2_error: 2.1e-4, max_error: 5.8e-4}
quality_scoring:
  - {min_L2: 1.0e-4, Q: 1.00}
  - {min_L2: 1.0e-3, Q: 0.90}
  - {min_L2: 1.0e-2, Q: 0.80}
  - {min_L2: 5.0e-2, Q: 0.75}
```

**Baseline solver:** BEM-linear — L2 error 1.8×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | L2 Error | Max Error | Runtime | Q |
|--------|----------|-----------|---------|---|
| BEM-constant | 4.2e-2 | 8.5e-2 | 8 s | 0.75 |
| BEM-linear | 1.8e-3 | 4.5e-3 | 25 s | 0.90 |
| BEM-quadratic | 2.5e-4 | 6.2e-4 | 60 s | 1.00 |
| FMM-BEM | 2.1e-4 | 5.8e-4 | 30 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case: 300 × 1.00 = 300 PWM
Floor:     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p261_hash>",
  "h_s": "sha256:<spec261_hash>",
  "h_b": "sha256:<bench261_hash>",
  "r": {"residual_norm": 2.1e-4, "error_bound": 1.0e-3, "ratio": 0.21},
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
pwm-node benchmarks | grep scattering_bem
pwm-node verify scattering_bem/sphere_plane_wave.yaml
pwm-node mine scattering_bem/sphere_plane_wave.yaml
pwm-node inspect sha256:<cert_hash>
```
