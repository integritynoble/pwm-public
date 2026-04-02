# Principle #54 — Photon-Counting Spectral CT

**Domain:** Medical Imaging | **Carrier:** X-ray | **Difficulty:** Standard (δ=3)
**DAG:** [Π.radon] --> [S.spectral] --> [S.angular]

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          Π.radon --> S.spectral --> S.angular      PCCT-decomp  SpectralCT-15     MatDecomp
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PHOTON-COUNTING SPECTRAL CT   P = (E, G, W, C)  Principle #54 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y_b(θ) = −ln ∫_{E_b} S(E)·exp(−Σ_m μ_m(E)·l_m) dE   │
│        │ b = energy bin index; m = material index               │
│        │ Inverse: decompose multi-energy sinograms into         │
│        │ material-specific basis maps (e.g., bone, soft, iodine)│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [Π.radon] ──→ [S.spectral] ──→ [S.angular]            │
│        │  Propagate Project Disperse  Detect                    │
│        │ V={Π.radon,S.spectral,S.angular}  A={Π.radon→S.spectral, S.spectral→S.angular}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (photon-counting detectors bin energies)│
│        │ Uniqueness: YES (N_bins ≥ N_materials)                 │
│        │ Stability: κ ≈ 15 (3 bins/2 materials), κ ≈ 50 (5/4)  │
│        │ Mismatch: Δ_spectrum (tube), Δ_charge_sharing, Δ_pileup│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = material RMSE mg/mL (primary), CNR (secondary)    │
│        │ q = 2.0 (maximum-likelihood decomposition convergence)│
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Energy bin thresholds and flux consistent with material K-edges | PASS |
| S2 | N_bins ≥ N_materials → invertible decomposition | PASS |
| S3 | ML material decomposition converges | PASS |
| S4 | Iodine RMSE ≤ 0.5 mg/mL achievable at clinical dose | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# pcct/spectral_s1_ideal.yaml
principle_ref: sha256:<p054_hash>
omega:
  grid: [512, 512]
  n_bins: 4
  bin_edges_keV: [25, 50, 70, 90, 120]
  n_projections: 1200
  materials: [water, bone, iodine]
E:
  forward: "y_b = −ln ∫ S(E)exp(−Σ μ_m l_m) dE per bin"
  model: "polychromatic forward model with PCD response"
I:
  dataset: SpectralCT_15
  phantoms: 15
  noise: {type: poisson, photon_count: 5e5}
  scenario: ideal
O: [iodine_RMSE_mg_mL, bone_RMSE_mg_mL, CNR]
epsilon:
  iodine_RMSE_max: 0.5
  bone_RMSE_max: 5.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 4 bins with edges at iodine K-edge (33 keV) resolve 3 materials | PASS |
| S2 | κ ≈ 15 within well-posed regime for 4-bin/3-material | PASS |
| S3 | ML decomposition converges for Poisson noise model | PASS |
| S4 | Iodine RMSE ≤ 0.5 mg/mL feasible at 5×10⁵ photons/ray | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# pcct/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec054_hash>
principle_ref: sha256:<p054_hash>
dataset:
  name: SpectralCT_15
  phantoms: 15
  size: [512, 512]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Image_Domain_Decomp
    params: {method: least_squares}
    results: {iodine_RMSE: 0.8, bone_RMSE: 8.5}
  - solver: Sinogram_Domain_ML
    params: {n_iter: 50}
    results: {iodine_RMSE: 0.45, bone_RMSE: 4.2}
  - solver: DeepSpectralCT
    params: {pretrained: true}
    results: {iodine_RMSE: 0.25, bone_RMSE: 2.8}
quality_scoring:
  - {max_iodine_RMSE: 0.2, Q: 1.00}
  - {max_iodine_RMSE: 0.35, Q: 0.90}
  - {max_iodine_RMSE: 0.5, Q: 0.80}
  - {max_iodine_RMSE: 0.8, Q: 0.75}
```

**Baseline solver:** Image-domain decomposition — iodine RMSE 0.8 mg/mL
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Iodine RMSE (mg/mL) | Bone RMSE | Runtime | Q |
|--------|---------------------|-----------|---------|---|
| Image-Domain LS | 0.80 | 8.5 | 2 s | 0.75 |
| Sinogram ML | 0.45 | 4.2 | 30 s | 0.88 |
| DeepSpectralCT | 0.25 | 2.8 | 3 s | 0.96 |
| Hybrid-ML-DL | 0.18 | 2.0 | 10 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (Hybrid-ML-DL):  300 × 1.00 = 300 PWM
Floor:                     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p054_hash>",
  "h_s": "sha256:<spec054_hash>",
  "h_b": "sha256:<bench054_hash>",
  "r": {"residual_norm": 0.018, "error_bound": 0.04, "ratio": 0.45},
  "c": {"fitted_rate": 1.94, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.96,
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
pwm-node benchmarks | grep pcct
pwm-node verify pcct/spectral_s1_ideal.yaml
pwm-node mine pcct/spectral_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
