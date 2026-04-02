# Principle #52 — Brachytherapy Imaging

**Domain:** Medical Imaging | **Carrier:** X-ray | **Difficulty:** Basic (δ=2)
**DAG:** [Π.radon.parallel] --> [S.angular]

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          Π.radon.parallel --> S.angular        Brachy-loc   SeedPhantom-15    Triangul
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  BRACHYTHERAPY IMAGING   P = (E, G, W, C)   Principle #52      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y_k(u,v) = Σ_i δ(u − P_k·r_i) + n                    │
│        │ P_k = projection matrix for view k                     │
│        │ Inverse: localize 3D positions {r_i} of radioactive   │
│        │ seeds from multi-view X-ray projections                │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [Π.radon.parallel] ──→ [S.angular]                    │
│        │  Project  Accumulate Detect                            │
│        │ V={Π.radon.parallel,S.angular}  A={Π.radon.parallel→S.angular}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (seeds visible as high-Z objects)       │
│        │ Uniqueness: YES (≥2 views resolve 3D positions)        │
│        │ Stability: κ ≈ 5 (well-separated seeds), κ ≈ 30 (clust)│
│        │ Mismatch: Δ_geometry (C-arm flex), Δ_overlap           │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = localization RMSE mm (primary), missed % (second.) │
│        │ q = 2.0 (triangulation convergence)                   │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | View angles and detector resolution consistent with seed spacing | PASS |
| S2 | ≥2 views with known geometry → bounded triangulation | PASS |
| S3 | RANSAC-based seed matching converges | PASS |
| S4 | RMSE ≤ 1 mm achievable for 80-seed implant with 3 views | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# brachytherapy/seed_s1_ideal.yaml
principle_ref: sha256:<p052_hash>
omega:
  n_views: 3
  detector_pixels: [1024, 1024]
  pixel_mm: 0.2
  source_det_mm: 1000
E:
  forward: "y_k = P_k · {r_i} + n"
  model: "pinhole projection, known geometry"
I:
  dataset: SeedPhantom_15
  implants: 15
  noise: {type: gaussian, SNR_dB: 40}
  scenario: ideal
O: [RMSE_mm, detection_rate_pct]
epsilon:
  RMSE_max_mm: 1.0
  detection_min_pct: 95.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 0.2 mm pixel at 1 m SDD resolves seeds separated by 5 mm | PASS |
| S2 | κ ≈ 5 within well-posed regime for 3-view triangulation | PASS |
| S3 | Triangulation converges for Gaussian noise | PASS |
| S4 | RMSE ≤ 1 mm feasible at SNR=40 dB | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# brachytherapy/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec052_hash>
principle_ref: sha256:<p052_hash>
dataset:
  name: SeedPhantom_15
  implants: 15
  n_views: 3
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Triangulation_RANSAC
    params: {n_iter: 1000}
    results: {RMSE_mm: 0.85, detection_pct: 96}
  - solver: Epipolar_Match
    params: {threshold_px: 3}
    results: {RMSE_mm: 0.70, detection_pct: 98}
  - solver: DeepSeedLoc
    params: {pretrained: true}
    results: {RMSE_mm: 0.45, detection_pct: 99}
quality_scoring:
  - {max_RMSE: 0.4, Q: 1.00}
  - {max_RMSE: 0.6, Q: 0.90}
  - {max_RMSE: 0.8, Q: 0.80}
  - {max_RMSE: 1.0, Q: 0.75}
```

**Baseline solver:** Triangulation-RANSAC — RMSE 0.85 mm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | RMSE (mm) | Detection (%) | Runtime | Q |
|--------|----------|---------------|---------|---|
| Triangulation-RANSAC | 0.85 | 96 | 2 s | 0.78 |
| Epipolar Match | 0.70 | 98 | 1 s | 0.85 |
| DeepSeedLoc (learned) | 0.45 | 99 | 0.5 s | 0.95 |
| SeedNet-3D | 0.35 | 99.5 | 0.8 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (SeedNet-3D):  200 × 1.00 = 200 PWM
Floor:                   200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p052_hash>",
  "h_s": "sha256:<spec052_hash>",
  "h_b": "sha256:<bench052_hash>",
  "r": {"residual_norm": 0.010, "error_bound": 0.025, "ratio": 0.40},
  "c": {"fitted_rate": 1.96, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.95,
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
| L4 Solution | — | 150–200 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep brachytherapy
pwm-node verify brachytherapy/seed_s1_ideal.yaml
pwm-node mine brachytherapy/seed_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
