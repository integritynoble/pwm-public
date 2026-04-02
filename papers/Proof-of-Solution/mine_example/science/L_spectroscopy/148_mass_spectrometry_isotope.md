# Principle #148 — Mass Spectrometry (Isotope Pattern Analysis)

**Domain:** Spectroscopy | **Carrier:** Ion | **Difficulty:** Advanced (δ=3)
**DAG:** G.beam --> K.scatter.inelastic --> S.spectral | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.beam-->K.scatter.inelastic-->S.spectral    MS-Iso      MSIsoRef-15        Deconv
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MASS SPECTROMETRY (ISOTOPE PATTERN)   P = (E, G, W, C)  #148  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ P(m/z) = Σ_{compositions} w_i · IsoPat(C_n H_m O_p …) │
│        │ Isotope pattern = convolution of elemental distributions│
│        │ ¹³C, ²H, ¹⁸O natural abundances determine envelope     │
│        │ Inverse: determine molecular formula from isotope dist. │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.beam] --> [K.scatter.inelastic] --> [S.spectral]      │
│        │  IonSource  Ionize  MassAnalyze                        │
│        │ V={G.beam, K.scatter.inelastic, S.spectral}  A={G.beam-->K.scatter.inelastic, K.scatter.inelastic-->S.spectral}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (isotope pattern always present)        │
│        │ Uniqueness: YES (mass accuracy ≤ 1 ppm + pattern unique│
│        │ Stability: κ ≈ 3 (high-res FTICR), κ ≈ 20 (low-res)   │
│        │ Mismatch: space charge, isobaric overlap, adducts      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = formula assignment accuracy (primary), mass err ppm│
│        │ q = 2.0 (combinatorial search + scoring exact)         │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Mass resolution ≥ 50000 and accuracy ≤ 2 ppm separate isotopologues | PASS |
| S2 | Isotope pattern matching with ≤ 5 ppm tolerance yields unique formula | PASS |
| S3 | Scoring function (cosine similarity) converges for candidate ranking | PASS |
| S4 | Formula assignment accuracy ≥ 95% for m/z ≤ 500 Da | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# ms_isotope/msisoref_s1.yaml
principle_ref: sha256:<p148_hash>
omega:
  mass_range_Da: [100, 1000]
  mass_resolution: 100000
  mass_accuracy_ppm: 1.0
  ionization: ESI_positive
E:
  forward: "P(m/z) = convolution of elemental isotope distributions"
  scoring: "cosine_similarity"
I:
  dataset: MSIsoRef_15
  spectra: 15
  noise: {type: gaussian, sigma_rel: 0.02}
  scenario: ideal
O: [formula_accuracy_pct, mass_error_ppm]
epsilon:
  formula_accuracy_min: 92.0
  mass_error_max: 2.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 100000 resolution at 1 ppm accuracy over 100–1000 Da | PASS |
| S2 | κ ≈ 3 for FTICR-quality isotope patterns | PASS |
| S3 | Cosine scoring + ranking converges for ≤ 100 candidate formulae | PASS |
| S4 | Formula accuracy ≥ 92% feasible at σ_rel = 0.02 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# ms_isotope/benchmark_s1.yaml
spec_ref: sha256:<spec148_hash>
principle_ref: sha256:<p148_hash>
dataset:
  name: MSIsoRef_15
  spectra: 15
  compounds: 500
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Mass-Only
    params: {tolerance_ppm: 2}
    results: {formula_accuracy_pct: 75, mass_error_ppm: 1.5}
  - solver: Isotope-Match
    params: {tolerance_ppm: 2, iso_score: cosine}
    results: {formula_accuracy_pct: 93, mass_error_ppm: 1.0}
  - solver: SIRIUS-CSI
    params: {database: PubChem}
    results: {formula_accuracy_pct: 98, mass_error_ppm: 0.5}
quality_scoring:
  - {min_acc: 97, Q: 1.00}
  - {min_acc: 93, Q: 0.90}
  - {min_acc: 88, Q: 0.80}
  - {min_acc: 80, Q: 0.75}
```

**Baseline solver:** Isotope-Match — accuracy 93%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Formula acc (%) | Mass err (ppm) | Runtime | Q |
|--------|-----------------|-----------------|---------|---|
| Mass-Only | 75 | 1.5 | 0.01 s | 0.75 |
| Isotope-Match | 93 | 1.0 | 0.5 s | 0.90 |
| SIRIUS-CSI | 98 | 0.5 | 10 s | 1.00 |
| DL-Formula (MassGNN) | 96 | 0.7 | 1 s | 0.98 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (SIRIUS):    300 × 1.00 = 300 PWM
Floor:                 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p148_hash>",
  "h_s": "sha256:<spec148_hash>",
  "h_b": "sha256:<bench148_hash>",
  "r": {"residual_norm": 0.02, "error_bound": 0.05, "ratio": 0.40},
  "c": {"fitted_rate": 1.96, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep ms_isotope
pwm-node verify ms_isotope/msisoref_s1.yaml
pwm-node mine ms_isotope/msisoref_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
