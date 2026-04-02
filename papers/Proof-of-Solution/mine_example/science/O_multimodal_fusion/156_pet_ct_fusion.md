# Principle #156 — PET/CT Fusion

**Domain:** Multimodal Fusion | **Carrier:** Photon (γ + X-ray) | **Difficulty:** Research (δ=2)
**DAG:** M₁ → R₁, M₂ → R₂, R₁+R₂ → F → D | **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          dual-acq     PET-CT      PETCTFuse-10      Register+Fuse
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PET/CT FUSION   P = (E, G, W, C)   Principle #156              │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ f_fused(r) = W_PET(r)·f_PET(r) + W_CT(r)·f_CT(r)     │
│        │ PET: y = H·λ + scatter + randoms (Poisson emission)    │
│        │ CT: y = ∫ μ(r,E) dl (Beer-Lambert attenuation)        │
│        │ Inverse: co-register + fuse metabolic & anatomical     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [M₁]→[R₁] (PET recon), [M₂]→[R₂] (CT recon)         │
│        │  [R₁]+[R₂]→[F]→[D]                                   │
│        │ V={M₁,M₂,R₁,R₂,F,D}   L_DAG=2.5                     │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (shared patient geometry)               │
│        │ Uniqueness: YES with rigid-body registration            │
│        │ Stability: κ ≈ 8 (hardware co-registered scanners)     │
│        │ Mismatch: respiratory motion, CT-based AC errors        │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = TRE_mm (registration), PSNR (fusion quality)       │
│        │ q = 2.0 (mutual-information registration convergence) │
│        │ T = {TRE_mm, PSNR_fused, MI_score, Dice_tumor}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | PET voxel grid resampled to CT resolution; FOV overlap ≥ 95% | PASS |
| S2 | Rigid registration κ ≈ 8 for hardware-fused scanners | PASS |
| S3 | MI-based registration converges monotonically | PASS |
| S4 | TRE ≤ 2 mm and PSNR ≥ 30 dB achievable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# pet_ct_fusion/petctfuse_s1_ideal.yaml
principle_ref: sha256:<p156_hash>
omega:
  grid_CT: [512, 512, 256]
  grid_PET: [128, 128, 64]
  voxel_CT_mm: [0.98, 0.98, 1.5]
  voxel_PET_mm: [4.0, 4.0, 4.0]
  tracer: FDG
E:
  forward_PET: "y = H·λ + s + r"
  forward_CT: "y = -ln(I/I0) = ∫ μ dl"
  fusion: "f_fused = W_PET·f_PET + W_CT·f_CT"
I:
  dataset: PETCTFuse_10
  patients: 10
  noise: {PET: poisson, CT: gaussian_sigma_HU: 15}
  scenario: ideal
O: [TRE_mm, PSNR_fused, Dice_tumor]
epsilon:
  TRE_max_mm: 2.0
  PSNR_min: 30.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | PET 4 mm resampled to CT 0.98 mm grid; FOV matched | PASS |
| S2 | Hardware co-registration: κ ≈ 8 | PASS |
| S3 | MI registration converges for CT/PET pair | PASS |
| S4 | TRE ≤ 2 mm feasible for co-registered scanner | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# pet_ct_fusion/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec156_hash>
dataset:
  name: PETCTFuse_10
  patients: 10
  modalities: [PET, CT]
baselines:
  - solver: Rigid-MI
    params: {optimizer: Powell, metric: MI}
    results: {TRE_mm: 1.8, PSNR: 31.2}
  - solver: Wavelet-Fusion
    params: {wavelet: db4, levels: 3}
    results: {TRE_mm: 1.8, PSNR: 33.5}
  - solver: DL-FuseNet
    params: {arch: DualEncoder, pretrained: true}
    results: {TRE_mm: 1.2, PSNR: 36.1}
quality_scoring:
  - {min: 36.0, Q: 1.00}
  - {min: 33.0, Q: 0.90}
  - {min: 30.0, Q: 0.80}
  - {min: 28.0, Q: 0.75}
```

**Baseline:** Rigid-MI + Wavelet — PSNR 33.5 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | TRE (mm) | PSNR (dB) | Dice | Q |
|--------|----------|-----------|------|---|
| Rigid-MI + Average | 1.8 | 31.2 | 0.81 | 0.80 |
| Rigid-MI + Wavelet | 1.8 | 33.5 | 0.84 | 0.90 |
| DL-FuseNet | 1.2 | 36.1 | 0.91 | 1.00 |
| Laplacian-Pyramid | 1.8 | 32.4 | 0.83 | 0.85 |

### Reward Calculation

```
R = 100 × 1.0 × 2 × 1.0 × Q = 200 × Q
Best (DL-FuseNet):  200 × 1.00 = 200 PWM
Floor:              200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p156_hash>",
  "h_s": "sha256:<spec156_hash>",
  "h_b": "sha256:<bench156_hash>",
  "r": {"residual_norm": 1.2, "error_bound": 2.0, "ratio": 0.60},
  "c": {"fitted_rate": 1.92, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.91,
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
pwm-node benchmarks | grep pet_ct
pwm-node verify pet_ct_fusion/petctfuse_s1_ideal.yaml
pwm-node mine pet_ct_fusion/petctfuse_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
