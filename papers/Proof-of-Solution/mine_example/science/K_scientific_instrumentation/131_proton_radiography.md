# Principle #131 — Proton Radiography

**Domain:** Scientific Instrumentation | **Carrier:** Proton | **Difficulty:** Research (δ=5)
**DAG:** Pi.radon --> K.scatter.nuclear --> integral.spatial | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          Pi.radon-->K.scatter.nuclear-->integral.spatial    pRad        pRadPhantom-12     MLP/CSDA
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PROTON RADIOGRAPHY   P = (E, G, W, C)   Principle #131        │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ΔE(x,y) = ∫ S(E, ρ(x,y,z)) dz  (energy loss)        │
│        │ θ_rms(x,y) = (14.1 MeV/pβc)√(L/X₀)  (MCS angle)     │
│        │ S = stopping power (Bethe-Bloch); X₀ = radiation len. │
│        │ Inverse: recover ρ or ρL from energy loss / scattering │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [Pi.radon] --> [K.scatter.nuclear] --> [integral.spatial]│
│        │  ProtonProj  CoulombScatter  Integrate                 │
│        │ V={Pi.radon, K.scatter.nuclear, integral.spatial}  A={Pi.radon-->K.scatter.nuclear, K.scatter.nuclear-->integral.spatial}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Bethe-Bloch well-defined for E > 1MeV)│
│        │ Uniqueness: YES (energy + angle give two contrasts)    │
│        │ Stability: κ ≈ 15 (200 MeV), κ ≈ 60 (low E, thick)   │
│        │ Mismatch: nuclear reactions, range straggling, MCS     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RSP accuracy % (primary), spatial res. mm (sec.)   │
│        │ q = 1.5 (MLP convergence for path estimation)         │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Proton energy, detector spacing, and tracker resolution yield consistent geometry | PASS |
| S2 | Entry/exit angle + energy loss provide over-determined system for RSP | PASS |
| S3 | Most-likely-path (MLP) estimation converges; FBP/iterative recon stable | PASS |
| S4 | RSP accuracy ≤ 1% achievable for 200 MeV protons through 20 cm water | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# proton_radiography/pradphantom_s1.yaml
principle_ref: sha256:<p131_hash>
omega:
  grid: [256, 256]
  pixel_mm: 1.0
  proton_energy_MeV: 200
  phantom_thickness_cm: 20
  n_protons: 1e6
E:
  forward: "dE/dx = Bethe-Bloch; theta_rms = Highland formula"
  path_model: "most_likely_path"
I:
  dataset: pRadPhantom_12
  projections: 180
  noise: {type: stochastic, straggling: true}
  scenario: ideal
O: [RSP_error_pct, spatial_res_mm]
epsilon:
  RSP_error_max: 1.0
  spatial_res_max: 1.5
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200 MeV protons penetrate 20 cm water with ≥ 50 MeV residual energy | PASS |
| S2 | κ ≈ 15 with MLP path estimation and 10⁶ protons per projection | PASS |
| S3 | Iterative recon with MLP converges within 20 iterations | PASS |
| S4 | RSP error ≤ 1% feasible for 10⁶ proton statistics | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# proton_radiography/benchmark_s1.yaml
spec_ref: sha256:<spec131_hash>
principle_ref: sha256:<p131_hash>
dataset:
  name: pRadPhantom_12
  phantoms: 12
  projections: 180
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FBP-StraightLine
    params: {filter: shepp_logan}
    results: {RSP_error_pct: 2.5, spatial_res_mm: 2.0}
  - solver: MLP-FBP
    params: {path: MLP}
    results: {RSP_error_pct: 1.2, spatial_res_mm: 1.2}
  - solver: DROP-TV
    params: {n_iter: 20, lambda: 0.005}
    results: {RSP_error_pct: 0.8, spatial_res_mm: 1.0}
quality_scoring:
  - {max_err: 0.8, Q: 1.00}
  - {max_err: 1.0, Q: 0.90}
  - {max_err: 1.5, Q: 0.80}
  - {max_err: 2.5, Q: 0.75}
```

**Baseline solver:** MLP-FBP — RSP error 1.2%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | RSP err (%) | Spatial res (mm) | Runtime | Q |
|--------|-------------|-------------------|---------|---|
| FBP-StraightLine | 2.5 | 2.0 | 5 s | 0.75 |
| MLP-FBP | 1.2 | 1.2 | 30 s | 0.88 |
| DROP-TV | 0.8 | 1.0 | 5 min | 1.00 |
| DL-pCT (TransRecon) | 0.7 | 0.9 | 15 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (DROP-TV/DL):  500 × 1.00 = 500 PWM
Floor:                   500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p131_hash>",
  "h_s": "sha256:<spec131_hash>",
  "h_b": "sha256:<bench131_hash>",
  "r": {"residual_norm": 0.007, "error_bound": 0.015, "ratio": 0.47},
  "c": {"fitted_rate": 1.45, "theoretical_rate": 1.5, "K": 3},
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
pwm-node benchmarks | grep proton_radiography
pwm-node verify proton_radiography/pradphantom_s1.yaml
pwm-node mine proton_radiography/pradphantom_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
