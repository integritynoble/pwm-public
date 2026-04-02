# Principle #144 — DESI Mass Spectrometry Imaging

**Domain:** Spectroscopy | **Carrier:** Ion (desorption) | **Difficulty:** Advanced (δ=3)
**DAG:** G.beam --> K.scatter.inelastic --> S.spectral | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.beam-->K.scatter.inelastic-->S.spectral    DESI        DESITissue-12      Unmix
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  DESI MASS SPECTROMETRY IMAGING   P = (E, G, W, C)   #144      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I(m/z, r) = η(m/z) · C(r) · Φ_spray                  │
│        │ Electrospray desorption ionises surface molecules       │
│        │ m/z spectrum encodes lipid/metabolite composition       │
│        │ Inverse: classify tissue / map metabolites from spectra │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.beam] --> [K.scatter.inelastic] --> [S.spectral]      │
│        │  Electrospray  Desorb  MassDisperse                    │
│        │ V={G.beam, K.scatter.inelastic, S.spectral}  A={G.beam-->K.scatter.inelastic, K.scatter.inelastic-->S.spectral}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (ambient ionisation for surface analytes│
│        │ Uniqueness: YES (high mass-resolution separates isobars│
│        │ Stability: κ ≈ 8 (stable spray), κ ≈ 35 (variable)    │
│        │ Mismatch: ion suppression, spray variability, matrix   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = classification accuracy (primary), AUC (secondary) │
│        │ q = 2.0 (linear classifier for lipid ratios)          │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Mass range, spray geometry, and scan speed yield consistent pixel coverage | PASS |
| S2 | m/z resolution ≥ 20000 separates isobaric lipids; unique classification | PASS |
| S3 | PCA + LDA converges for ≥ 3 tissue classes with ≥ 50 training spectra | PASS |
| S4 | Classification accuracy ≥ 90% for tumor vs. normal tissue | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# desi_msi/desitissue_s1.yaml
principle_ref: sha256:<p144_hash>
omega:
  grid: [200, 200]
  pixel_um: 100
  mass_range: [100, 1200]
  mass_resolution: 30000
  polarity: negative
E:
  forward: "I(m/z, r) = eta * C(r) * Phi_spray"
  classification: "PCA_LDA"
I:
  dataset: DESITissue_12
  sections: 12
  noise: {type: multiplicative, cv: 0.15}
  scenario: ideal
O: [classification_acc_pct, AUC]
epsilon:
  classification_acc_min: 88.0
  AUC_min: 0.92
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 100–1200 Da at 30000 mass resolution covers lipid region | PASS |
| S2 | κ ≈ 8 for negative-mode lipid fingerprinting | PASS |
| S3 | PCA(20) + LDA converges for 3 tissue classes | PASS |
| S4 | Classification ≥ 88% and AUC ≥ 0.92 feasible | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# desi_msi/benchmark_s1.yaml
spec_ref: sha256:<spec144_hash>
principle_ref: sha256:<p144_hash>
dataset:
  name: DESITissue_12
  sections: 12
  pixels_per: 40000
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Single-Ion
    params: {m_z: 885.55}
    results: {classification_acc_pct: 78, AUC: 0.85}
  - solver: PCA-LDA
    params: {components: 20}
    results: {classification_acc_pct: 91, AUC: 0.95}
  - solver: Lasso-MSI
    params: {alpha: 0.01}
    results: {classification_acc_pct: 94, AUC: 0.97}
quality_scoring:
  - {min_acc: 93, Q: 1.00}
  - {min_acc: 90, Q: 0.90}
  - {min_acc: 85, Q: 0.80}
  - {min_acc: 78, Q: 0.75}
```

**Baseline solver:** PCA-LDA — accuracy 91%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Class. acc (%) | AUC | Runtime | Q |
|--------|----------------|------|---------|---|
| Single-Ion | 78 | 0.85 | 0.1 s | 0.75 |
| PCA-LDA | 91 | 0.95 | 5 s | 0.90 |
| Lasso-MSI | 94 | 0.97 | 10 s | 1.00 |
| DL-DESI (1D-CNN) | 95 | 0.98 | 2 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (Lasso/DL):  300 × 1.00 = 300 PWM
Floor:                 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p144_hash>",
  "h_s": "sha256:<spec144_hash>",
  "h_b": "sha256:<bench144_hash>",
  "r": {"residual_norm": 0.05, "error_bound": 0.10, "ratio": 0.50},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep desi_msi
pwm-node verify desi_msi/desitissue_s1.yaml
pwm-node mine desi_msi/desitissue_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
