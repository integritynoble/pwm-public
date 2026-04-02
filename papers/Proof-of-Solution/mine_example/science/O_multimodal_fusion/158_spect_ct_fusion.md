# Principle #158 — SPECT/CT Fusion

**Domain:** Multimodal Fusion | **Carrier:** Photon (γ + X-ray) | **Difficulty:** Research (δ=2)
**DAG:** M₁ → R₁, M₂ → R₂, R₁+R₂ → F → D | **Reward:** 2× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          dual-acq     SPECT-CT    SPECTCTFuse-10    AC+Fuse
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SPECT/CT FUSION   P = (E, G, W, C)   Principle #158            │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ f_fused(r) = W_SPECT(r)·f_SPECT(r) + W_CT(r)·f_CT(r) │
│        │ SPECT: y = H·f + scatter (collimated γ projection)    │
│        │ CT: y = ∫ μ(r,E) dl (attenuation line integrals)      │
│        │ Inverse: CT-AC for SPECT, co-register, fuse            │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [M₁]→[R₁] (SPECT recon), [M₂]→[R₂] (CT recon)       │
│        │  [R₁]+[R₂]→[F]→[D]                                   │
│        │ V={M₁,M₂,R₁,R₂,F,D}   L_DAG=2.5                     │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (shared patient anatomy)                │
│        │ Uniqueness: YES with CT-derived attenuation correction  │
│        │ Stability: κ ≈ 12 (sequential scan, collimator blur)   │
│        │ Mismatch: patient motion between scans, scatter model   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = TRE_mm, PSNR_fused, quantification_accuracy (%)    │
│        │ q = 2.0 (OSEM with CT-AC convergence)                │
│        │ T = {TRE_mm, PSNR, quant_acc_pct, CNR_lesion}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | SPECT voxels resampled to CT grid; collimator PSF modeled | PASS |
| S2 | CT-AC yields bounded μ-map; κ ≈ 12 | PASS |
| S3 | OSEM with resolution recovery converges | PASS |
| S4 | TRE ≤ 3 mm and PSNR ≥ 28 dB achievable | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# spect_ct_fusion/spectctfuse_s1_ideal.yaml
principle_ref: sha256:<p158_hash>
omega:
  grid_CT: [512, 512, 256]
  grid_SPECT: [128, 128, 128]
  voxel_CT_mm: [0.98, 0.98, 1.5]
  voxel_SPECT_mm: [4.42, 4.42, 4.42]
  isotope: Tc99m
  collimator: LEHR
E:
  forward_SPECT: "y = H·f + scatter"
  forward_CT: "y = -ln(I/I0)"
  fusion: "f_fused = W_SPECT·f_SPECT + W_CT·f_CT"
I:
  dataset: SPECTCTFuse_10
  patients: 10
  noise: {SPECT: poisson, CT: gaussian_sigma_HU: 12}
  scenario: ideal
O: [TRE_mm, PSNR_fused, CNR_lesion]
epsilon:
  TRE_max_mm: 3.0
  PSNR_min: 28.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | SPECT 4.42 mm resampled to CT 0.98 mm; FOV matched | PASS |
| S2 | CT-AC for Tc99m (140 keV): κ ≈ 12 | PASS |
| S3 | OSEM + CDR converges within 30 iterations | PASS |
| S4 | TRE ≤ 3 mm and PSNR ≥ 28 dB feasible | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# spect_ct_fusion/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec158_hash>
dataset:
  name: SPECTCTFuse_10
  patients: 10
  modalities: [SPECT, CT]
baselines:
  - solver: OSEM-AC + Alpha-Blend
    params: {iterations: 10, subsets: 8, alpha: 0.5}
    results: {TRE_mm: 2.5, PSNR: 28.8}
  - solver: OSEM-AC + Wavelet
    params: {wavelet: sym4, levels: 3}
    results: {TRE_mm: 2.5, PSNR: 31.2}
  - solver: DL-SPECTFuse
    params: {arch: AttentionUNet, pretrained: true}
    results: {TRE_mm: 1.8, PSNR: 34.0}
quality_scoring:
  - {min: 34.0, Q: 1.00}
  - {min: 31.0, Q: 0.90}
  - {min: 28.0, Q: 0.80}
  - {min: 26.0, Q: 0.75}
```

**Baseline:** OSEM-AC + Alpha-Blend — PSNR 28.8 dB | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | TRE (mm) | PSNR (dB) | CNR | Q |
|--------|----------|-----------|-----|---|
| OSEM-AC + Alpha-Blend | 2.5 | 28.8 | 4.2 | 0.80 |
| OSEM-AC + Wavelet | 2.5 | 31.2 | 5.8 | 0.90 |
| DL-SPECTFuse | 1.8 | 34.0 | 8.1 | 1.00 |
| Laplacian-Pyramid | 2.5 | 30.1 | 5.1 | 0.85 |

### Reward Calculation

```
R = 100 × 1.0 × 2 × 1.0 × Q = 200 × Q
Best (DL-SPECTFuse):  200 × 1.00 = 200 PWM
Floor:                200 × 0.75 = 150 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p158_hash>",
  "h_s": "sha256:<spec158_hash>",
  "h_b": "sha256:<bench158_hash>",
  "r": {"residual_norm": 1.8, "error_bound": 3.0, "ratio": 0.60},
  "c": {"fitted_rate": 1.90, "theoretical_rate": 2.0, "K": 3},
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
| L4 Solution | — | 150–200 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep spect_ct
pwm-node verify spect_ct_fusion/spectctfuse_s1_ideal.yaml
pwm-node mine spect_ct_fusion/spectctfuse_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
