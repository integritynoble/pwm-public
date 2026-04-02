# Principle #469 — LiDAR Point Cloud Processing

**Domain:** Geodesy | **Carrier:** N/A (geometric) | **Difficulty:** Standard (δ=3)
**DAG:** [Π.perspective] --> [S.sparse] --> [O.l2] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          Π.persp-->S.sparse-->O.l2  LiDAR-PC  ALS-benchmark  filter+class
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LIDAR POINT CLOUD PROCESSING  P = (E,G,W,C)  Principle #469   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ r_ground = R_boresight · R_IMU · [x_scan] + r_GNSS    │
│        │ (georeferencing: scanner → IMU → GNSS → ground)        │
│        │ z_i = f(x_i, y_i) + ε_i  (ground surface model)       │
│        │ Classification: ground / vegetation / building / noise │
│        │ Forward: given raw returns → classified DEM/DSM        │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [Π.persp] ──→ [S.sparse] ──→ [O.l2]                    │
│        │  range-model  point-cloud  least-squares               │
│        │ V={Π.persp,S.sparse,O.l2}  A={Π.persp→S.sparse,S.sparse→O.l2}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (point cloud with finite density)       │
│        │ Uniqueness: surface model unique for given filter       │
│        │ Stability: depends on point density and terrain slope  │
│        │ Mismatch: vegetation penetration, multi-path returns   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSE(z_DEM − z_control)  (vertical accuracy, m)   │
│        │ q = N/A (classification accuracy)                     │
│        │ T = {vertical_RMSE, classification_F1, completeness}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Georeferencing chain dimensionally consistent (3D rotation + translation) | PASS |
| S2 | Ground filter well-defined for slope < 70°; density ≥ 1 pt/m² | PASS |
| S3 | Progressive morphological / cloth simulation filters converge | PASS |
| S4 | Vertical RMSE bounded by ≤ 15 cm for flat terrain (ALS) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# lidar_pc/als_dem_s1.yaml
principle_ref: sha256:<p469_hash>
omega:
  area_km2: 4.0
  domain: mixed_terrain
  point_density: 8.0   # pts/m²
E:
  forward: "georeferencing + ground filtering + DEM interpolation"
  scanner: discrete_return_4echo
  accuracy: {horizontal: 0.30, vertical: 0.10}   # m
B:
  control_points: 50_GPS_surveyed
  datum: WGS84_UTM
I:
  scenario: ALS_DEM_generation
  filters: [progressive_morphological, cloth_simulation, TIN_densification]
O: [vertical_RMSE, ground_classification_F1, completeness]
epsilon:
  vertical_RMSE_max: 0.15    # meters
  classification_F1_min: 0.90
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 8 pts/m² sufficient; 50 control points for validation | PASS |
| S2 | Mixed terrain well-defined; ground filter applicable | PASS |
| S3 | All three filters produce valid ground classification | PASS |
| S4 | Vertical RMSE < 15 cm on open terrain | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# lidar_pc/benchmark_als_dem.yaml
spec_ref: sha256:<spec469_hash>
principle_ref: sha256:<p469_hash>
dataset:
  name: ISPRS_filter_test
  reference: "Sithole & Vosselman (2004) ISPRS filter comparison"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Progressive Morphological Filter
    params: {max_window: 20m, slope_threshold: 0.3}
    results: {vertical_RMSE: 0.12, F1_ground: 0.92}
  - solver: Cloth Simulation Filter
    params: {cloth_resolution: 1.0m, rigidness: 2}
    results: {vertical_RMSE: 0.10, F1_ground: 0.94}
  - solver: TIN Densification
    params: {angle: 10deg, distance: 1.0m}
    results: {vertical_RMSE: 0.11, F1_ground: 0.93}
quality_scoring:
  - {min_RMSE: 0.05, Q: 1.00}
  - {min_RMSE: 0.10, Q: 0.90}
  - {min_RMSE: 0.15, Q: 0.80}
  - {min_RMSE: 0.25, Q: 0.75}
```

**Baseline solver:** Cloth Simulation Filter — vertical RMSE 10 cm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Vert RMSE (m) | F1 Ground | Runtime | Q |
|--------|--------------|-----------|---------|---|
| Prog. Morphological | 0.12 | 0.92 | 30 s | 0.80 |
| Cloth Simulation | 0.10 | 0.94 | 45 s | 0.90 |
| TIN Densification | 0.11 | 0.93 | 25 s | 0.80 |
| Hybrid (CSF + ML) | 0.06 | 0.97 | 120 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (hybrid): 300 × 1.00 = 300 PWM
Floor:              300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p469_hash>",
  "h_s": "sha256:<spec469_hash>",
  "h_b": "sha256:<bench469_hash>",
  "r": {"vertical_RMSE": 0.06, "error_bound": 0.15, "ratio": 0.400},
  "c": {"F1_ground": 0.97, "control_pts": 50, "K": 3},
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
pwm-node benchmarks | grep lidar_pc
pwm-node verify lidar_pc/als_dem_s1.yaml
pwm-node mine lidar_pc/als_dem_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
