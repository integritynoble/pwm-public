# Principle #470 — Photogrammetry (Structure from Motion)

**Domain:** Geodesy | **Carrier:** N/A (geometric) | **Difficulty:** Standard (δ=3)
**DAG:** [Π.perspective] --> [S.feature] --> [O.bundle] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          Π.persp-->S.feat-->O.bundle  SfM-Photo  ETH3D/Tanks  BA-solver
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PHOTOGRAMMETRY (SfM)          P = (E,G,W,C)   Principle #470   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ x = π(K [R|t] X)  (projection: 3D → 2D)              │
│        │ π([X,Y,Z]ᵀ) = [X/Z, Y/Z]ᵀ  (perspective division)   │
│        │ min Σᵢⱼ ‖xᵢⱼ − π(Kⱼ[Rⱼ|tⱼ]Xᵢ)‖²  (bundle adjust)  │
│        │ Forward: given images → (cameras, 3D points, dense)   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [Π.persp] ──→ [S.feat] ──→ [O.bundle]                  │
│        │  projection  features  bundle-adjust                   │
│        │ V={Π.persp,S.feat,O.bundle}  A={Π.persp→S.feat,S.feat→O.bundle}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (≥ 2 views with sufficient parallax)   │
│        │ Uniqueness: YES up to gauge (7-DOF similarity)         │
│        │ Stability: depends on baseline/depth ratio             │
│        │ Mismatch: feature mismatches, rolling shutter          │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSE(X_est − X_GCP) (3D reconstruction error, m)  │
│        │ q = N/A (nonlinear optimization)                      │
│        │ T = {reprojection_error, GCP_RMSE, completeness}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Projection model consistent; intrinsics K well-calibrated | PASS |
| S2 | Bundle adjustment has unique minimum up to gauge freedom | PASS |
| S3 | Levenberg-Marquardt on sparse Hessian converges | PASS |
| S4 | Reprojection error < 1 px; GCP RMSE bounded | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# sfm_photo/aerial_s1.yaml
principle_ref: sha256:<p470_hash>
omega:
  images: 200
  domain: urban_mapping
  GSD: 0.05   # meters
E:
  forward: "feature extraction → matching → incremental SfM → BA"
  camera: frame_20MP
  lens_model: Brown_radial_tangential
B:
  GCPs: 10_surveyed_points
  check_points: 20_independent
I:
  scenario: UAV_aerial_photogrammetry
  pipelines: [COLMAP, OpenMVG, Metashape]
O: [reprojection_RMSE_px, GCP_RMSE_3D, point_cloud_density]
epsilon:
  reprojection_max: 1.0    # pixels
  GCP_RMSE_max: 0.05       # meters (1 GSD)
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200 images with 80% overlap; 10 GCPs well-distributed | PASS |
| S2 | Sufficient overlap ensures reconstruction completeness | PASS |
| S3 | BA converges within 50 LM iterations | PASS |
| S4 | GCP RMSE < 1 GSD (5 cm) achievable | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# sfm_photo/benchmark_aerial.yaml
spec_ref: sha256:<spec470_hash>
principle_ref: sha256:<p470_hash>
dataset:
  name: ETH3D_multi_view
  reference: "Schops et al. (2017) ETH3D benchmark"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: COLMAP
    params: {matcher: exhaustive, BA: Ceres}
    results: {reproj_RMSE: 0.55, GCP_RMSE: 0.032}
  - solver: OpenMVG
    params: {matcher: cascade_hashing, BA: Ceres}
    results: {reproj_RMSE: 0.62, GCP_RMSE: 0.038}
  - solver: Metashape
    params: {quality: high, dense: ultra_high}
    results: {reproj_RMSE: 0.48, GCP_RMSE: 0.028}
quality_scoring:
  - {min_RMSE: 0.02, Q: 1.00}
  - {min_RMSE: 0.04, Q: 0.90}
  - {min_RMSE: 0.06, Q: 0.80}
  - {min_RMSE: 0.10, Q: 0.75}
```

**Baseline solver:** COLMAP — GCP RMSE 3.2 cm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Reproj (px) | GCP RMSE (m) | Runtime | Q |
|--------|-------------|-------------|---------|---|
| OpenMVG | 0.62 | 0.038 | 300 s | 0.80 |
| COLMAP | 0.55 | 0.032 | 420 s | 0.90 |
| Metashape | 0.48 | 0.028 | 600 s | 0.90 |
| COLMAP + refined BA | 0.42 | 0.019 | 550 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (refined BA): 300 × 1.00 = 300 PWM
Floor:                  300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p470_hash>",
  "h_s": "sha256:<spec470_hash>",
  "h_b": "sha256:<bench470_hash>",
  "r": {"GCP_RMSE": 0.019, "error_bound": 0.05, "ratio": 0.380},
  "c": {"reproj_RMSE": 0.42, "images": 200, "K": 3},
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
pwm-node benchmarks | grep sfm_photo
pwm-node verify sfm_photo/aerial_s1.yaml
pwm-node mine sfm_photo/aerial_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
