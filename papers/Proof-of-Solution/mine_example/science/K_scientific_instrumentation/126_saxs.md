# Principle #126 — Small-Angle X-ray Scattering (SAXS)

**Domain:** Scientific Instrumentation | **Carrier:** X-ray Photon | **Difficulty:** Practitioner (δ=3)
**DAG:** K.scatter.bragg --> S.reciprocal --> N.pointwise.abs2 | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.scatter.bragg-->S.reciprocal-->N.pointwise.abs2    SAXS        NanoStruct-30      Reconstruct
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SMALL-ANGLE X-RAY SCATTERING (SAXS)  P = (E, G, W, C)  #126   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I(q) = ∫ P(r) sin(qr)/(qr) dr;  q = 4π sinθ / λ     │
│        │ P(r) = pair distance distribution; Guinier: ln I ∝ −q²R²/3│
│        │ Porod: I(q) → S/(2π²) q⁻⁴ at large q                │
│        │ Inverse: recover P(r) and shape from 1D I(q) profile  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.scatter.bragg] --> [S.reciprocal] --> [N.pointwise.abs2]│
│        │  SmallAngleScatter  Reciprocal  ModSq                  │
│        │ V={K.scatter.bragg, S.reciprocal, N.pointwise.abs2}  A={K.scatter.bragg-->S.reciprocal, S.reciprocal-->N.pointwise.abs2}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (scattering always produced by Δρ)      │
│        │ Uniqueness: LIMITED (1D → 3D shape ambiguity)          │
│        │ Stability: κ ≈ 10 (monodisperse), κ ≈ 60 (polydisperse)│
│        │ Mismatch: buffer subtraction, beam-stop shadow         │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = χ² fit (primary), R_g error Å (secondary)         │
│        │ q = 1.5 (indirect Fourier transform convergence)      │
│        │ T = {chi_squared, R_g_error, D_max_error}              │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | q-range covers Guinier regime (qR_g < 1.3) to Porod regime | PASS |
| S2 | Buffer subtraction yields positive I(q); no beam-stop artifacts | PASS |
| S3 | IFT (GNOM/BayesApp) converges for P(r) with stable D_max | PASS |
| S4 | χ² ≈ 1.0 achievable for monodisperse samples | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# saxs/nanostruct_s1.yaml
principle_ref: sha256:<p126_hash>
omega:
  wavelength_A: 1.54
  q_range_invA: [0.005, 0.5]
  detector: Pilatus_1M
  sample_detector_m: 2.0
  exposure_s: 60
E:
  forward: "I(q) = integral(P(r) * sin(qr)/(qr), dr)"
  model: "indirect Fourier transform"
I:
  dataset: NanoStruct_30
  samples: 30
  particle_types: [sphere, ellipsoid, cylinder, core-shell]
  noise: {type: poisson, counts_per_frame: 10000}
O: [chi_squared, R_g_error_A]
epsilon:
  chi_sq_max: 1.5
  Rg_error_max: 2.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | q-range 0.005–0.5 covers 1–100 nm structures at 1.54 Å | PASS |
| S2 | κ ≈ 10 for monodisperse spheres at 10000 counts | PASS |
| S3 | GNOM IFT converges with Perceptual Criteria ≥ 0.7 | PASS |
| S4 | χ² ≤ 1.5 feasible for specified sample types | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# saxs/benchmark_s1.yaml
spec_ref: sha256:<spec126_hash>
principle_ref: sha256:<p126_hash>
dataset:
  name: NanoStruct_30
  samples: 30
  q_points: 500
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Guinier-Fit
    params: {q_max_Rg: 1.3}
    results: {chi_sq: 3.5, Rg_error: 3.2}
  - solver: GNOM-IFT
    params: {alpha: auto}
    results: {chi_sq: 1.2, Rg_error: 1.0}
  - solver: DAMMIN-Ab-Initio
    params: {runs: 10}
    results: {chi_sq: 1.05, Rg_error: 0.5}
quality_scoring:
  - {max_chi_sq: 1.1, Q: 1.00}
  - {max_chi_sq: 1.3, Q: 0.90}
  - {max_chi_sq: 1.5, Q: 0.80}
  - {max_chi_sq: 2.0, Q: 0.75}
```

**Baseline solver:** Guinier-Fit — χ² 3.5
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | χ² | R_g Error (Å) | Runtime | Q |
|--------|-----|---------------|---------|---|
| Guinier-Fit | 3.5 | 3.2 | 0.01 s | 0.75 |
| GNOM-IFT | 1.2 | 1.0 | 5 s | 0.88 |
| DAMMIN-Ab-Initio | 1.05 | 0.5 | 2 hr | 1.00 |
| DENSS (electron density) | 1.08 | 0.6 | 30 min | 0.98 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (DAMMIN):  300 × 1.00 = 300 PWM
Floor:               300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p126_hash>",
  "h_s": "sha256:<spec126_hash>",
  "h_b": "sha256:<bench126_hash>",
  "r": {"residual_norm": 1.05, "error_bound": 1.50, "ratio": 0.70},
  "c": {"fitted_rate": 1.45, "theoretical_rate": 1.5, "K": 4},
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
pwm-node benchmarks | grep saxs
pwm-node verify saxs/nanostruct_s1.yaml
pwm-node mine saxs/nanostruct_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
