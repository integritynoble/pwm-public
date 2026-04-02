# Principle #127 — MALDI Mass Spectrometry Imaging

**Domain:** Scientific Instrumentation | **Carrier:** Ions (desorbed) | **Difficulty:** Practitioner (δ=3)
**DAG:** G.pulse.laser --> K.scatter.inelastic --> S.spectral | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.pulse.laser-->K.scatter.inelastic-->S.spectral    MALDI-MSI   TissueMetab-25     Segment
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MALDI MASS SPECTROMETRY IMAGING  P = (E, G, W, C)  #127       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ S(x,y,m/z) = η(m/z) × C(x,y) × Σ_k I_k δ(m/z − m_k)│
│        │ UV laser ablates matrix+analyte; TOF measures m/z      │
│        │ Ion yield η depends on matrix, tissue type, local env. │
│        │ Inverse: recover spatial distribution C(x,y) per m/z   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse.laser] --> [K.scatter.inelastic] --> [S.spectral]│
│        │  LaserDesorb  Ionize  MassDisperse                     │
│        │ V={G.pulse.laser, K.scatter.inelastic, S.spectral}  A={G.pulse.laser-->K.scatter.inelastic, K.scatter.inelastic-->S.spectral}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (ions always produced from matrix)      │
│        │ Uniqueness: YES (m/z resolves distinct compounds)      │
│        │ Stability: κ ≈ 15 (lipids), κ ≈ 80 (low-abundance)  │
│        │ Mismatch: ion suppression, matrix heterogeneity        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = segmentation accuracy (primary), m/z precision     │
│        │ q = N/A (direct mapping, no iterative inversion)      │
│        │ T = {segmentation_acc, mz_precision_ppm, coverage}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Raster step ≤ 50 μm; mass range covers target metabolites | PASS |
| S2 | Mass resolving power R ≥ 10000 separates isobaric species | PASS |
| S3 | Normalization (TIC/median) stabilizes intensity across tissue | PASS |
| S4 | Segmentation accuracy ≥ 0.85 for histological regions | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# maldi_msi/tissuemetab_s1.yaml
principle_ref: sha256:<p127_hash>
omega:
  raster_um: 30
  mass_range_Da: [100, 2000]
  resolving_power: 20000
  matrix: DHB
  polarity: positive
E:
  forward: "S(x,y,mz) = eta(mz) * C(x,y) * I_k"
  analyzer: "TOF/TOF"
I:
  dataset: TissueMetab_25
  sections: 25
  tissue_types: [brain, liver, kidney]
  noise: {type: chemical, ion_suppression: variable}
O: [segmentation_accuracy, mz_precision_ppm]
epsilon:
  segmentation_min: 0.85
  mz_precision_max: 5
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 30 μm raster resolves tissue microregions; 100–2000 Da covers lipids/metabolites | PASS |
| S2 | R=20000 at m/z 500 gives ≤ 2.5 ppm precision | PASS |
| S3 | TIC normalization reduces coefficient of variation < 20% | PASS |
| S4 | Segmentation accuracy ≥ 0.85 feasible with ≥ 100 peaks | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# maldi_msi/benchmark_s1.yaml
spec_ref: sha256:<spec127_hash>
principle_ref: sha256:<p127_hash>
dataset:
  name: TissueMetab_25
  sections: 25
  pixels_per_section: 50000
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: PCA-KMeans
    params: {components: 20, k: 5}
    results: {segmentation: 0.78, mz_ppm: 3.5}
  - solver: NMF-Spatial
    params: {components: 10}
    results: {segmentation: 0.86, mz_ppm: 3.0}
  - solver: UMAP-HDBSCAN
    params: {n_neighbors: 15}
    results: {segmentation: 0.92, mz_ppm: 2.5}
quality_scoring:
  - {min_seg: 0.92, Q: 1.00}
  - {min_seg: 0.88, Q: 0.90}
  - {min_seg: 0.85, Q: 0.80}
  - {min_seg: 0.80, Q: 0.75}
```

**Baseline solver:** PCA-KMeans — segmentation 0.78
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Segmentation | m/z Precision (ppm) | Runtime | Q |
|--------|-------------|---------------------|---------|---|
| PCA-KMeans | 0.78 | 3.5 | 5 s | 0.75 |
| NMF-Spatial | 0.86 | 3.0 | 30 s | 0.82 |
| UMAP-HDBSCAN | 0.92 | 2.5 | 60 s | 1.00 |
| VAE-Spatial | 0.90 | 2.8 | 120 s | 0.95 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (UMAP-HDBSCAN):  300 × 1.00 = 300 PWM
Floor:                     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p127_hash>",
  "h_s": "sha256:<spec127_hash>",
  "h_b": "sha256:<bench127_hash>",
  "r": {"residual_norm": 0.08, "error_bound": 0.15, "ratio": 0.53},
  "c": {"fitted_rate": "N/A", "theoretical_rate": "N/A", "K": 5},
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
pwm-node benchmarks | grep maldi_msi
pwm-node verify maldi_msi/tissuemetab_s1.yaml
pwm-node mine maldi_msi/tissuemetab_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
