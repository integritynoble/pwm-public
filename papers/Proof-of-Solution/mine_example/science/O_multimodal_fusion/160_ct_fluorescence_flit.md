# Principle #160 — CT + Fluorescence (FLIT)

**Domain:** Multimodal Fusion | **Carrier:** Photon (X-ray + NIR) | **Difficulty:** Advanced (δ=3)
**DAG:** M₁ → R₁, M₂ → R₂, R₁+R₂ → F → D | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          dual-acq     CT-FLIT     FLIT-Phantom-8    Recon+Fuse
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CT + FLUORESCENCE (FLIT)   P = (E, G, W, C)   Principle #160   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ CT: y = ∫ μ(r,E) dl  (attenuation tomography)         │
│        │ FLIT: Φ(r_d) = ∫ G(r_d,r)·η(r)·Φ_ex(r) dr            │
│        │ (diffuse fluorescence transport, G = Green's function)  │
│        │ Inverse: CT provides anatomical prior for FLIT recon    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [M₁]→[R₁] (CT recon), [M₂]→[R₂] (FLIT recon)        │
│        │  [R₁]+[R₂]→[F]→[D]                                   │
│        │ V={M₁,M₂,R₁,R₂,F,D}   L_DAG=3.5                     │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (CT structural prior regularizes FLIT)  │
│        │ Uniqueness: YES with anatomical spatial prior           │
│        │ Stability: κ ≈ 50 (FLIT alone), κ ≈ 15 (CT-guided)   │
│        │ Mismatch: optical property heterogeneity, autofluor.    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = localization_error_mm, DICE_fluorescent_region      │
│        │ q = 1.5 (regularized diffusion inverse convergence)   │
│        │ T = {loc_err_mm, Dice_fluor, quant_accuracy, CNR}      │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | CT mesh → optical property map; source/detector geometry consistent | PASS |
| S2 | CT-guided prior reduces FLIT κ from 50 to 15 | PASS |
| S3 | Gauss-Newton with CT prior converges within 20 iterations | PASS |
| S4 | Localization ≤ 2 mm and Dice ≥ 0.75 achievable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# ct_fluorescence/flit_phantom_s1_ideal.yaml
principle_ref: sha256:<p160_hash>
omega:
  grid_CT: [512, 512, 256]
  voxel_CT_mm: [0.5, 0.5, 1.0]
  FLIT_sources: 8
  FLIT_detectors: 16
  excitation_nm: 750
  emission_nm: 830
  fluorophore: ICG
E:
  forward_CT: "y = -ln(I/I0) = ∫ μ dl"
  forward_FLIT: "Φ_m = ∫ G(r_d,r)·η(r)·Φ_ex(r) dr"
  prior: "CT-derived tissue segmentation → optical properties"
I:
  dataset: FLIT_Phantom_8
  phantoms: 8
  noise: {CT: gaussian_HU: 10, FLIT: poisson_snr: 30}
  scenario: ideal
O: [loc_err_mm, Dice_fluor, CNR]
epsilon:
  loc_err_max_mm: 2.0
  Dice_min: 0.75
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 8 sources, 16 detectors with CT mesh: adequate sampling | PASS |
| S2 | CT-guided optical properties: κ ≈ 15 | PASS |
| S3 | Gauss-Newton converges with CT anatomical prior | PASS |
| S4 | loc_err ≤ 2 mm and Dice ≥ 0.75 feasible | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# ct_fluorescence/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec160_hash>
dataset:
  name: FLIT_Phantom_8
  phantoms: 8
  modalities: [CT, FLIT]
baselines:
  - solver: Diffusion-BornNorm
    params: {regularization: Tikhonov, lambda: 0.01}
    results: {loc_err_mm: 3.5, Dice: 0.65}
  - solver: CT-Guided-GaussNewton
    params: {iterations: 20, prior: CT_segmentation}
    results: {loc_err_mm: 1.8, Dice: 0.79}
  - solver: DL-FLITNet
    params: {arch: 3DUNet, pretrained: true}
    results: {loc_err_mm: 1.2, Dice: 0.88}
quality_scoring:
  metric: Dice_fluor
  thresholds:
    - {min: 0.85, Q: 1.00}
    - {min: 0.78, Q: 0.90}
    - {min: 0.72, Q: 0.80}
    - {min: 0.65, Q: 0.75}
```

**Baseline:** Diffusion-BornNorm — Dice 0.65 | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | Loc err (mm) | Dice | CNR | Q |
|--------|-------------|------|-----|---|
| Diffusion-BornNorm | 3.5 | 0.65 | 3.2 | 0.75 |
| CT-Guided-GaussNewton | 1.8 | 0.79 | 6.5 | 0.90 |
| DL-FLITNet | 1.2 | 0.88 | 9.1 | 1.00 |
| Sparse-L1-Recon | 2.4 | 0.74 | 5.0 | 0.82 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q
Best (DL-FLITNet):  300 × 1.00 = 300 PWM
Floor:              300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p160_hash>",
  "h_s": "sha256:<spec160_hash>",
  "h_b": "sha256:<bench160_hash>",
  "r": {"residual_norm": 1.2, "error_bound": 2.0, "ratio": 0.60},
  "c": {"fitted_rate": 1.42, "theoretical_rate": 1.5, "K": 3},
  "Q": 0.90,
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
pwm-node benchmarks | grep ct_fluorescence
pwm-node verify ct_fluorescence/flit_phantom_s1_ideal.yaml
pwm-node mine ct_fluorescence/flit_phantom_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
