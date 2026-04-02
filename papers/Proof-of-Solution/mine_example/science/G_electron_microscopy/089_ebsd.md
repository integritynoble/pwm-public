# Principle #89 — Electron Backscatter Diffraction (EBSD)

**Domain:** Electron Microscopy | **Carrier:** Electron | **Difficulty:** Standard (δ=3)
**DAG:** K.scatter.bragg --> S.reciprocal --> N.pointwise | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.scatter.bragg-->S.reciprocal-->N.pointwise    EBSD-map   EBSD-PolyCrystal   Indexing
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  EBSD   P = (E, G, W, C)   Principle #89                       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I(k) = |Σ_g F_g · δ(k − g)|² ⊛ PSF_det + n           │
│        │ Kikuchi pattern from crystal lattice backscatter        │
│        │ F_g = structure factor; g = reciprocal lattice vectors  │
│        │ Inverse: recover crystal orientation (φ₁,Φ,φ₂) per px  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.scatter.bragg] --> [S.reciprocal] --> [N.pointwise]   │
│        │  BraggScatter  Reciprocal  Index                        │
│        │ V={K.scatter.bragg, S.reciprocal, N.pointwise}  A={K.scatter.bragg-->S.reciprocal, S.reciprocal-->N.pointwise}   L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Kikuchi bands encode orientation)      │
│        │ Uniqueness: YES up to crystal symmetry equivalents      │
│        │ Stability: κ ≈ 8 (clean patterns), κ ≈ 60 (noisy)     │
│        │ Mismatch: pattern-center error, detector tilt            │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = indexing accuracy (primary), misorientation (sec)  │
│        │ q = N/A (discrete indexing, not iterative)            │
│        │ T = {orientation_accuracy, confidence_index}           │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Kikuchi pattern resolution matches detector pixel count | PASS |
| S2 | Hough-transform indexing yields unique orientation per pattern | PASS |
| S3 | Dictionary indexing or DI-NN converges to correct orientation | PASS |
| S4 | Indexing rate > 95% achievable for clean Kikuchi patterns | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# ebsd/polycrystal_s1_ideal.yaml
principle_ref: sha256:<p089_hash>
omega:
  scan_grid: [512, 512]
  step_um: 0.5
  detector_px: [120, 160]
  voltage_kV: 20
E:
  forward: "Kikuchi_pattern = Backscatter(crystal_orientation) + n"
  crystal_system: cubic
I:
  dataset: EBSD_PolyCrystal
  maps: 20
  noise: {type: gaussian, SNR: 15}
  scenario: ideal
O: [indexing_rate_pct, misorientation_deg]
epsilon:
  indexing_rate_min: 95.0
  misorientation_max_deg: 1.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 120×160 detector captures sufficient Kikuchi bands for cubic | PASS |
| S2 | κ ≈ 8 at SNR=15; well-posed for Hough indexing | PASS |
| S3 | Hough + dictionary indexing converges for cubic symmetry | PASS |
| S4 | Indexing rate > 95% feasible at SNR=15 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# ebsd/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec089_hash>
principle_ref: sha256:<p089_hash>
dataset:
  name: EBSD_PolyCrystal
  maps: 20
  scan_size: [512, 512]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Hough-Indexing
    params: {n_bands: 8, rho_res: 1}
    results: {indexing_rate: 96.2, misorientation_deg: 0.8}
  - solver: Dictionary-Indexing
    params: {dict_size: 50000}
    results: {indexing_rate: 97.8, misorientation_deg: 0.5}
  - solver: DI-NN
    params: {pretrained: cubic}
    results: {indexing_rate: 98.5, misorientation_deg: 0.3}
quality_scoring:
  - {min_rate: 99.0, Q: 1.00}
  - {min_rate: 98.0, Q: 0.90}
  - {min_rate: 96.0, Q: 0.80}
  - {min_rate: 94.0, Q: 0.75}
```

**Baseline solver:** Hough-Indexing — 96.2% rate
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Index Rate | Misorient. (°) | Runtime | Q |
|--------|------------|-----------------|---------|---|
| Hough-Indexing | 96.2% | 0.8 | 5 min | 0.80 |
| Dictionary-Indexing | 97.8% | 0.5 | 30 min | 0.88 |
| DI-NN | 98.5% | 0.3 | 2 min | 0.92 |
| EBSD-Transformer | 99.2% | 0.2 | 3 min | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (EBSD-TF):  300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p089_hash>",
  "h_s": "sha256:<spec089_hash>",
  "h_b": "sha256:<bench089_hash>",
  "r": {"indexing_rate": 98.5, "confidence_index": 0.92},
  "c": {"misorientation_mean": 0.3, "K": 3},
  "Q": 0.92,
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
pwm-node benchmarks | grep ebsd
pwm-node verify ebsd/polycrystal_s1_ideal.yaml
pwm-node mine ebsd/polycrystal_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
