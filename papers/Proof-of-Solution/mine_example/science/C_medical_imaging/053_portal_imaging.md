# Principle #53 — Portal Imaging (EPID)

**Domain:** Medical Imaging | **Carrier:** X-ray | **Difficulty:** Basic (δ=2)
**DAG:** [Π.radon.parallel] --> [S.detector]

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          Π.radon.parallel --> S.detector        EPID-verify  PortalQA-20       GammaIdx
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PORTAL IMAGING (EPID)   P = (E, G, W, C)   Principle #53      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(u,v) = ∫ μ_MV(x,y,z)·Φ(x,y,z) dz + n              │
│        │ Φ = MV photon fluence; μ_MV = attenuation at MV energy│
│        │ Inverse: verify beam alignment by comparing measured   │
│        │ portal image to digitally reconstructed radiograph      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [Π.radon.parallel] ──→ [S.detector]                   │
│        │  Propagate Project  Detect                             │
│        │ V={Π.radon.parallel,S.detector}  A={Π.radon.parallel→S.detector}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (MV beam produces measurable image)     │
│        │ Uniqueness: YES (single 2D projection per beam angle)  │
│        │ Stability: κ ≈ 5 (high dose), κ ≈ 15 (low dose)       │
│        │ Mismatch: Δ_setup (patient shift), Δ_scatter (MV)     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = gamma pass rate % (primary), shift RMSE mm (sec.)  │
│        │ q = 2.0 (registration convergence)                    │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | EPID pixel size and panel area consistent with treatment field | PASS |
| S2 | DRR-to-portal registration well-conditioned for bony anatomy | PASS |
| S3 | Rigid registration converges for normalized cross-correlation | PASS |
| S4 | Gamma pass ≥ 95% (3%/3mm) achievable for standard fields | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# portal/qa_s1_ideal.yaml
principle_ref: sha256:<p053_hash>
omega:
  panel_pixels: [1024, 768]
  pixel_mm: 0.39
  beam_energy_MV: 6
  SDD_mm: 1600
E:
  forward: "y = ∫ μ_MV·Φ dz + n"
  comparison: "portal vs. DRR registration"
I:
  dataset: PortalQA_20
  fields: 20
  noise: {type: poisson, dose_MU: 2}
  scenario: ideal
O: [gamma_pass_pct, shift_RMSE_mm]
epsilon:
  gamma_min_pct: 95.0
  shift_RMSE_max_mm: 2.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 0.39 mm pixel at 1.6 m SDD resolves bony landmarks at MV | PASS |
| S2 | κ ≈ 5 within well-posed regime for rigid registration | PASS |
| S3 | NCC-based registration converges | PASS |
| S4 | Gamma ≥ 95% feasible for 2 MU portal dose | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# portal/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec053_hash>
principle_ref: sha256:<p053_hash>
dataset:
  name: PortalQA_20
  fields: 20
  panel_size: [1024, 768]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Rigid_NCC
    params: {optimizer: powell}
    results: {gamma_pass: 95.5, shift_RMSE: 1.8}
  - solver: Mutual_Info_Reg
    params: {optimizer: gradient}
    results: {gamma_pass: 97.0, shift_RMSE: 1.2}
  - solver: DeepPortal
    params: {pretrained: true}
    results: {gamma_pass: 98.5, shift_RMSE: 0.6}
quality_scoring:
  - {min_gamma: 99.0, Q: 1.00}
  - {min_gamma: 97.0, Q: 0.90}
  - {min_gamma: 95.0, Q: 0.80}
  - {min_gamma: 93.0, Q: 0.75}
```

**Baseline solver:** Rigid NCC — gamma 95.5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Gamma (%) | Shift RMSE (mm) | Runtime | Q |
|--------|----------|-----------------|---------|---|
| Rigid NCC | 95.5 | 1.8 | 1 s | 0.80 |
| Mutual-Info Reg | 97.0 | 1.2 | 2 s | 0.90 |
| DeepPortal (learned) | 98.5 | 0.6 | 0.3 s | 0.97 |
| PortalTransformer | 99.2 | 0.4 | 0.5 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 2 × 1.0 × Q
Best case (PortalTransformer):  200 × 1.00 = 200 PWM
Floor:                         200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p053_hash>",
  "h_s": "sha256:<spec053_hash>",
  "h_b": "sha256:<bench053_hash>",
  "r": {"residual_norm": 0.008, "error_bound": 0.02, "ratio": 0.40},
  "c": {"fitted_rate": 1.97, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.97,
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
| L4 Solution | — | 150–200 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep portal
pwm-node verify portal/qa_s1_ideal.yaml
pwm-node mine portal/qa_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
