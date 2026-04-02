# Principle #96 — LiDAR Point Cloud Imaging

**Domain:** Depth Imaging | **Carrier:** Photon (NIR laser) | **Difficulty:** Standard (δ=3)
**DAG:** G.pulse.laser --> K.green --> integral.temporal | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.pulse.laser-->K.green-->integral.temporal    LiDAR      KITTI-LiDAR        Completion
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LIDAR   P = (E, G, W, C)   Principle #96                      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(θ,φ) = (2d(θ,φ)/c)·δ(t) ⊛ p(t) + n(t)             │
│        │ Pulsed laser: time-of-flight → range measurement       │
│        │ Sparse angular sampling, intensity ∝ reflectance        │
│        │ Inverse: dense depth/3D from sparse point cloud        │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse.laser] --> [K.green] --> [integral.temporal]    │
│        │ LaserPulse  Propagate  ToFAccum                         │
│        │ V={G.pulse.laser, K.green, integral.temporal}  A={G.pulse.laser-->K.green, K.green-->integral.temporal}   L_DAG=2.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (ToF → range is direct)                 │
│        │ Uniqueness: YES per beam direction                      │
│        │ Stability: κ ≈ 5 (strong return), κ ≈ 40 (weak)       │
│        │ Mismatch: beam divergence, multipath, weather scatter   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = depth MAE (primary), completion IoU (secondary)    │
│        │ q = 2.0 (interpolation convergence)                   │
│        │ T = {depth_MAE, completion_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Angular resolution consistent with beam count; range bins valid | PASS |
| S2 | Direct ToF → range bijective; sparse completion regularizable | PASS |
| S3 | Bilateral filter / guided completion converge | PASS |
| S4 | Depth MAE < 10 cm achievable for automotive LiDAR | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# lidar/kitti_s1_ideal.yaml
principle_ref: sha256:<p096_hash>
omega:
  beams: 64
  angular_res_deg: 0.4
  max_range_m: 80
  points_per_frame: 120000
E:
  forward: "d = c·t_return/2; sparse angular sampling"
I:
  dataset: KITTI_LiDAR
  frames: 200
  noise: {type: gaussian, sigma_m: 0.02}
  scenario: ideal
O: [depth_MAE_m, completion_rate_pct]
epsilon:
  depth_MAE_max_m: 0.10
  completion_rate_min: 95.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 64-beam at 0.4° gives ~120k pts/frame; range 80 m valid | PASS |
| S2 | Direct measurement + completion well-posed with priors | PASS |
| S3 | Guided depth completion converges for 64-beam input | PASS |
| S4 | MAE < 0.10 m feasible with σ = 2 cm noise | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# lidar/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec096_hash>
principle_ref: sha256:<p096_hash>
dataset:
  name: KITTI_LiDAR
  frames: 200
  points_per_frame: 120000
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: IP-Basic
    params: {morphological: true}
    results: {depth_MAE_m: 0.085, completion_pct: 96.2}
  - solver: SparseConv
    params: {pretrained: KITTI}
    results: {depth_MAE_m: 0.052, completion_pct: 98.1}
  - solver: CompletionFormer
    params: {pretrained: true}
    results: {depth_MAE_m: 0.028, completion_pct: 99.3}
quality_scoring:
  - {max_MAE: 0.03, Q: 1.00}
  - {max_MAE: 0.05, Q: 0.90}
  - {max_MAE: 0.08, Q: 0.80}
  - {max_MAE: 0.12, Q: 0.75}
```

**Baseline solver:** IP-Basic — MAE 0.085 m
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | MAE (m) | Completion (%) | Runtime | Q |
|--------|---------|----------------|---------|---|
| IP-Basic | 0.085 | 96.2 | 0.1 s | 0.80 |
| SparseConv | 0.052 | 98.1 | 0.05 s | 0.90 |
| CompletionFormer | 0.028 | 99.3 | 0.1 s | 1.00 |
| DepthAnything-LiDAR | 0.025 | 99.5 | 0.08 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case:  300 × 1.00 = 300 PWM
Floor:      300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p096_hash>",
  "h_s": "sha256:<spec096_hash>",
  "h_b": "sha256:<bench096_hash>",
  "r": {"depth_MAE_m": 0.028, "completion_pct": 99.3},
  "c": {"fitted_rate": 1.97, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep lidar
pwm-node verify lidar/kitti_s1_ideal.yaml
pwm-node mine lidar/kitti_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
