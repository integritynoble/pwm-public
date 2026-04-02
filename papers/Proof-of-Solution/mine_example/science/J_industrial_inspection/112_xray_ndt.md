# Principle #112 — X-ray Radiographic NDT

**Domain:** Industrial Inspection | **Carrier:** X-ray | **Difficulty:** Standard (δ=3)
**DAG:** Pi.radon --> N.pointwise --> integral.spatial | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          Pi.radon-->N.pointwise-->integral.spatial    XrayNDT    Weld-Defect         DetectNet
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  X-RAY NDT   P = (E, G, W, C)   Principle #112                │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r) = ∫ I_0(E)·exp(-∫ μ(r,E) dl) dE + n(r)         │
│        │ Projection radiograph: 2D shadow of 3D defect         │
│        │ Contrast depends on defect size and Δμ                 │
│        │ Inverse: detect and classify defects from radiograph   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [Pi.radon] --> [N.pointwise] --> [integral.spatial]      │
│        │  XrayProject  BeerLambert  Integrate                    │
│        │ V={Pi.radon, N.pointwise, integral.spatial}  A={Pi.radon-->N.pointwise, N.pointwise-->integral.spatial}   L_DAG=2.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (attenuation contrast detectable)       │
│        │ Uniqueness: CONDITIONAL (depth ambiguity in projection)│
│        │ Stability: κ ≈ 8 (high contrast), κ ≈ 40 (low Δμ)    │
│        │ Mismatch: scatter, beam-hardening, geometric magnif.   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = detection mAP (primary), false positive rate (sec.)│
│        │ q = 2.0 (detection network convergence)               │
│        │ T = {mAP, FPR, recall}                                 │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | kV and exposure consistent with part thickness | PASS |
| S2 | Defect contrast above noise floor; detectable | PASS |
| S3 | YOLO/Faster-RCNN converge on labeled radiographs | PASS |
| S4 | mAP > 0.80 achievable for standard weld defects | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# xray_ndt/weld_s1_ideal.yaml
principle_ref: sha256:<p112_hash>
omega:
  grid: [2048, 2048]
  pixel_um: 100
  voltage_kV: 200
E:
  forward: "y = ∫ I_0·exp(-∫ μ dl) dE + n"
I:
  dataset: Weld_Defect
  images: 200
  defect_types: [porosity, crack, slag, lack_of_fusion]
  noise: {type: poisson, flux: 5e5}
  scenario: ideal
O: [mAP, recall, FPR]
epsilon:
  mAP_min: 0.80
  recall_min: 0.90
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 200 kV appropriate for steel welds; 100 μm pixel | PASS |
| S2 | κ ≈ 8 for porosity/crack detection | PASS |
| S3 | Detection CNN converges on 200-image training set | PASS |
| S4 | mAP > 0.80 feasible for stated defect types | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# xray_ndt/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec112_hash>
principle_ref: sha256:<p112_hash>
dataset:
  name: Weld_Defect
  images: 200
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Traditional-CV
    results: {mAP: 0.72, recall: 0.81}
  - solver: YOLOv5
    results: {mAP: 0.85, recall: 0.92}
  - solver: DefectNet
    results: {mAP: 0.92, recall: 0.96}
quality_scoring:
  - {min_mAP: 0.93, Q: 1.00}
  - {min_mAP: 0.87, Q: 0.90}
  - {min_mAP: 0.80, Q: 0.80}
  - {min_mAP: 0.72, Q: 0.75}
```

**Baseline:** Traditional-CV — mAP 0.72 | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | mAP | Recall | Q |
|--------|-----|--------|---|
| Traditional-CV | 0.72 | 0.81 | 0.75 |
| YOLOv5 | 0.85 | 0.92 | 0.88 |
| DefectNet | 0.92 | 0.96 | 0.98 |
| NDT-Former | 0.94 | 0.97 | 1.00 |

### Reward: `R = 100 × 3 × q` → Best: 300 PWM | Floor: 225 PWM

```json
{
  "h_p": "sha256:<p112_hash>", "Q": 0.98,
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

## Quick-Start

```bash
pwm-node benchmarks | grep xray_ndt
pwm-node mine xray_ndt/weld_s1_ideal.yaml
```
