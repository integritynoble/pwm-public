# Principle #117 — Machine Vision / Automated Optical Inspection

**Domain:** Industrial Inspection & NDE | **Carrier:** Visible Photon | **Difficulty:** Textbook (δ=1)
**DAG:** G.structured --> K.psf --> S.feature | **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.structured-->K.psf-->S.feature    AOI         PCBDefect-200      Classify
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MACHINE VISION / AOI   P = (E, G, W, C)   Principle #117       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(x,y) = R(x,y) ⊛ L(x,y) + n(x,y)                   │
│        │ R = surface reflectance; L = illumination field         │
│        │ Defect: δR from reference → anomaly in difference image│
│        │ Inverse: detect and classify surface anomalies         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.structured] --> [K.psf] --> [S.feature]               │
│        │  LightPattern  LensImage  FeatureDetect                │
│        │ V={G.structured, K.psf, S.feature}  A={G.structured-->K.psf, K.psf-->S.feature}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (image always captured)                 │
│        │ Uniqueness: YES (reference-based comparison)           │
│        │ Stability: κ ≈ 5 (controlled lighting), κ ≈ 30 (var.) │
│        │ Mismatch: illumination drift, part pose variation      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = classification accuracy (primary), F1 (secondary)  │
│        │ q = N/A (classification task)                         │
│        │ T = {accuracy, precision, recall, false_escape_rate}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Camera resolution resolves minimum defect size; lighting uniform | PASS |
| S2 | Reference template registered; difference image contrast > noise | PASS |
| S3 | Classifier accuracy improves with training data; no overfitting | PASS |
| S4 | Accuracy ≥ 95% on controlled production line images | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# machine_vision_aoi/pcbdefect_s1.yaml
principle_ref: sha256:<p117_hash>
omega:
  resolution: [2048, 2048]
  pixel_um: 10
  channels: 3
  illumination: ring_light
  magnification: 2x
E:
  forward: "y = R * L + n"
  model: "template matching + anomaly detection"
I:
  dataset: PCBDefect_200
  images: 200
  defect_types: [missing_component, solder_bridge, tombstone, scratch]
  noise: {type: gaussian, SNR_dB: 40}
O: [accuracy, F1]
epsilon:
  accuracy_min: 0.95
  F1_min: 0.90
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 10 μm pixel resolves 50 μm solder bridges at 2× magnification | PASS |
| S2 | κ ≈ 5 under controlled ring illumination | PASS |
| S3 | CNN classifier generalizes with 200-image training set | PASS |
| S4 | Accuracy ≥ 0.95 feasible for well-defined defect classes | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# machine_vision_aoi/benchmark_s1.yaml
spec_ref: sha256:<spec117_hash>
principle_ref: sha256:<p117_hash>
dataset:
  name: PCBDefect_200
  images: 200
  size: [2048, 2048]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Template-Diff
    params: {threshold: 3sigma}
    results: {accuracy: 0.88, F1: 0.82}
  - solver: HOG-SVM
    params: {C: 1.0}
    results: {accuracy: 0.92, F1: 0.88}
  - solver: EfficientNet-B0
    params: {pretrained: true, finetune: true}
    results: {accuracy: 0.97, F1: 0.96}
quality_scoring:
  - {min_accuracy: 0.97, Q: 1.00}
  - {min_accuracy: 0.95, Q: 0.90}
  - {min_accuracy: 0.92, Q: 0.80}
  - {min_accuracy: 0.88, Q: 0.75}
```

**Baseline solver:** Template-Diff — accuracy 0.88
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Accuracy | F1 | Runtime | Q |
|--------|----------|-----|---------|---|
| Template-Diff | 0.88 | 0.82 | 0.05 s | 0.75 |
| HOG-SVM | 0.92 | 0.88 | 0.1 s | 0.80 |
| EfficientNet-B0 | 0.97 | 0.96 | 0.2 s | 1.00 |
| AnomalyGAN | 0.95 | 0.93 | 0.5 s | 0.92 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (EfficientNet):  100 × 1.00 = 100 PWM
Floor:                     100 × 0.75 =  75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p117_hash>",
  "h_s": "sha256:<spec117_hash>",
  "h_b": "sha256:<bench117_hash>",
  "r": {"residual_norm": 0.03, "error_bound": 0.05, "ratio": 0.60},
  "c": {"fitted_rate": "N/A", "theoretical_rate": "N/A", "K": 4},
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
pwm-node benchmarks | grep machine_vision_aoi
pwm-node verify machine_vision_aoi/pcbdefect_s1.yaml
pwm-node mine machine_vision_aoi/pcbdefect_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
