# Principle #157 — PET/MR Fusion

**Domain:** Multimodal Fusion | **Carrier:** Photon (γ) + RF | **Difficulty:** Advanced (δ=3)
**DAG:** M₁ → R₁, M₂ → R₂, R₁+R₂ → F → D | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          dual-acq     PET-MR      PETMRFuse-8       AC+Fuse
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PET/MR FUSION   P = (E, G, W, C)   Principle #157              │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ f_fused(r) = W_PET(r)·f_PET(r) + W_MR(r)·f_MR(r)     │
│        │ PET: y = H·λ + s + r (γ-photon emission)              │
│        │ MR: y_k = ∫ m(r)·e^{-i2πk·r} dr (k-space encoding)   │
│        │ Inverse: MR-based AC, co-register, fuse modalities     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [M₁]→[R₁] (PET recon), [M₂]→[R₂] (MR recon)         │
│        │  [R₁]+[R₂]→[F]→[D]                                   │
│        │ V={M₁,M₂,R₁,R₂,F,D}   L_DAG=3.5                     │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (simultaneous acquisition in hybrid)    │
│        │ Uniqueness: YES with MR-derived attenuation map         │
│        │ Stability: κ ≈ 20 (MR-AC uncertainty adds ill-posedness)│
│        │ Mismatch: MR-AC errors (bone/air), motion, susceptibility│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = TRE_mm, PSNR, quantification bias (%)              │
│        │ q = 2.0 (iterative MR-AC + OSEM convergence)         │
│        │ T = {TRE_mm, PSNR, quant_bias_pct, Dice_lesion}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | MR and PET grids co-aligned; simultaneous acquisition eliminates motion | PASS |
| S2 | MR-AC with UTE/Dixon yields bounded μ-map error | PASS |
| S3 | OSEM + MR-AC converges; quantification bias < 5% | PASS |
| S4 | TRE ≤ 1.5 mm (simultaneous) and PSNR ≥ 28 dB achievable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# pet_mr_fusion/petmrfuse_s1_ideal.yaml
principle_ref: sha256:<p157_hash>
omega:
  grid_MR: [256, 256, 192]
  grid_PET: [128, 128, 89]
  voxel_MR_mm: [1.0, 1.0, 1.0]
  voxel_PET_mm: [2.08, 2.08, 2.03]
  tracer: FDG
  MR_sequence: Dixon
E:
  forward_PET: "y = H·λ + s + r"
  forward_MR: "y_k = FT{m(r)}"
  attenuation_correction: "MR-AC via Dixon segmentation"
I:
  dataset: PETMRFuse_8
  patients: 8
  noise: {PET: poisson, MR: rician_sigma: 0.03}
  scenario: ideal
O: [TRE_mm, PSNR_fused, quant_bias_pct]
epsilon:
  TRE_max_mm: 1.5
  PSNR_min: 28.0
  quant_bias_max_pct: 5.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Simultaneous PET/MR: inherent co-registration | PASS |
| S2 | Dixon MR-AC: κ ≈ 20 with tissue/air/fat segmentation | PASS |
| S3 | OSEM converges with MR-AC μ-map | PASS |
| S4 | TRE ≤ 1.5 mm, PSNR ≥ 28 dB, bias ≤ 5% feasible | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# pet_mr_fusion/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec157_hash>
dataset:
  name: PETMRFuse_8
  patients: 8
  modalities: [PET, MR_Dixon]
baselines:
  - solver: Dixon-AC + OSEM
    params: {OSEM_subsets: 21, iterations: 3}
    results: {TRE_mm: 1.2, PSNR: 29.1, quant_bias: 4.5}
  - solver: UTE-AC + Wavelet-Fuse
    params: {wavelet: db4}
    results: {TRE_mm: 1.2, PSNR: 31.5, quant_bias: 3.8}
  - solver: DeepAC-FuseNet
    params: {arch: VNet, pretrained: true}
    results: {TRE_mm: 0.9, PSNR: 34.2, quant_bias: 2.1}
quality_scoring:
  - {min: 34.0, Q: 1.00}
  - {min: 31.0, Q: 0.90}
  - {min: 28.0, Q: 0.80}
  - {min: 26.0, Q: 0.75}
```

**Baseline:** Dixon-AC + OSEM — PSNR 29.1 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | TRE (mm) | PSNR (dB) | Bias (%) | Q |
|--------|----------|-----------|----------|---|
| Dixon-AC + OSEM | 1.2 | 29.1 | 4.5 | 0.80 |
| UTE-AC + Wavelet-Fuse | 1.2 | 31.5 | 3.8 | 0.90 |
| DeepAC-FuseNet | 0.9 | 34.2 | 2.1 | 1.00 |
| MLAA-Joint | 1.0 | 30.8 | 3.2 | 0.85 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q
Best (DeepAC-FuseNet):  300 × 1.00 = 300 PWM
Floor:                  300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p157_hash>",
  "h_s": "sha256:<spec157_hash>",
  "h_b": "sha256:<bench157_hash>",
  "r": {"residual_norm": 0.9, "error_bound": 1.5, "ratio": 0.60},
  "c": {"fitted_rate": 1.88, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep pet_mr
pwm-node verify pet_mr_fusion/petmrfuse_s1_ideal.yaml
pwm-node mine pet_mr_fusion/petmrfuse_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
