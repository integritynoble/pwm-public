# Principle #97 — Structured Light Depth Imaging

**Domain:** Depth Imaging | **Carrier:** Photon (NIR) | **Difficulty:** Standard (δ=3)
**DAG:** G.structured.stripe --> Pi.perspective --> S.feature | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.structured.stripe-->Pi.perspective-->S.feature    SL-depth   SL-Indoor          Triangulate
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  STRUCTURED LIGHT   P = (E, G, W, C)   Principle #97           │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(u_c) = I_p(u_p(d(u_c))) + n                         │
│        │ Projector casts coded pattern; camera observes deform. │
│        │ Triangulation: d from correspondence (u_p, u_c)        │
│        │ Inverse: recover dense depth d(u_c) from coded images  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.structured.stripe] --> [Pi.perspective] --> [S.feature]│
│        │ StripeProject  Triangulate  Correspond                  │
│        │ V={G.structured.stripe, Pi.perspective, S.feature}  A={G.structured.stripe-->Pi.perspective, Pi.perspective-->S.feature}   L_DAG=2.5│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (triangulation geometry is invertible)  │
│        │ Uniqueness: YES for single-valued surfaces              │
│        │ Stability: κ ≈ 5 (textured), κ ≈ 40 (specular/dark)   │
│        │ Mismatch: projector-camera calibration, ambient light   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = depth MAE (primary), completeness (secondary)      │
│        │ q = 2.0 (least-squares triangulation)                 │
│        │ T = {depth_MAE, completeness_pct, K_resolutions}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Baseline distance and FOV consistent with depth range | PASS |
| S2 | Triangulation geometry well-conditioned; κ < 40 | PASS |
| S3 | Phase-shifting or Gray-code decoding converges | PASS |
| S4 | Depth MAE < 1 mm achievable for close-range scanning | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# structured_light/indoor_s1_ideal.yaml
principle_ref: sha256:<p097_hash>
omega:
  camera_res: [1024, 1280]
  projector_res: [768, 1024]
  baseline_mm: 100
  working_distance_mm: [300, 1000]
E:
  forward: "y = I_proj(correspondence(d)) + n"
  coding: "4-step phase shift + Gray code"
I:
  dataset: SL_Indoor
  scenes: 30
  noise: {type: gaussian, sigma_DN: 3}
  scenario: ideal
O: [depth_MAE_mm, completeness_pct]
epsilon:
  depth_MAE_max_mm: 0.5
  completeness_min_pct: 95.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 100 mm baseline at 300–1000 mm working distance; valid geometry | PASS |
| S2 | κ ≈ 5 at stated baseline/distance ratio | PASS |
| S3 | Phase-shift + Gray-code decoding converges | PASS |
| S4 | MAE < 0.5 mm feasible at σ_DN=3 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# structured_light/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec097_hash>
principle_ref: sha256:<p097_hash>
dataset:
  name: SL_Indoor
  scenes: 30
  size: [1024, 1280]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Gray-Code
    params: {n_patterns: 10}
    results: {depth_MAE_mm: 0.42, completeness_pct: 96.5}
  - solver: Phase-Shift
    params: {n_steps: 4, n_freq: 3}
    results: {depth_MAE_mm: 0.28, completeness_pct: 97.8}
  - solver: DeepSL
    params: {pretrained: true}
    results: {depth_MAE_mm: 0.15, completeness_pct: 99.1}
quality_scoring:
  - {max_MAE: 0.15, Q: 1.00}
  - {max_MAE: 0.30, Q: 0.90}
  - {max_MAE: 0.50, Q: 0.80}
  - {max_MAE: 0.80, Q: 0.75}
```

**Baseline solver:** Gray-Code — MAE 0.42 mm
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | MAE (mm) | Completeness | Runtime | Q |
|--------|----------|--------------|---------|---|
| Gray-Code | 0.42 | 96.5% | 0.5 s | 0.80 |
| Phase-Shift | 0.28 | 97.8% | 0.3 s | 0.90 |
| DeepSL | 0.15 | 99.1% | 0.1 s | 1.00 |
| SL-Former | 0.12 | 99.3% | 0.15 s | 1.00 |

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
  "h_p": "sha256:<p097_hash>",
  "h_s": "sha256:<spec097_hash>",
  "h_b": "sha256:<bench097_hash>",
  "r": {"depth_MAE_mm": 0.15, "completeness_pct": 99.1},
  "c": {"fitted_rate": 1.99, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep structured_light
pwm-node verify structured_light/indoor_s1_ideal.yaml
pwm-node mine structured_light/indoor_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
