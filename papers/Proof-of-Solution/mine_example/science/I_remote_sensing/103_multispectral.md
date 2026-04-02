# Principle #103 — Multispectral Remote Sensing

**Domain:** Remote Sensing | **Carrier:** Photon (VIS/NIR) | **Difficulty:** Textbook (δ=1)
**DAG:** L.diag.spectral --> S.spectral --> integral.spatial | **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.diag.spectral-->S.spectral-->integral.spatial    MSI-RS     Sentinel2-SR        Pansharp
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MULTISPECTRAL RS   P = (E, G, W, C)   Principle #103          │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y_b(r) = ∫ ρ(r,λ)·S_b(λ)·L(λ) dλ + n_b(r)          │
│        │ S_b = spectral response of band b (4–13 bands)        │
│        │ Pan-sharpening: fuse low-res MS + high-res PAN        │
│        │ Inverse: super-resolve MS bands using PAN guidance     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.diag.spectral] --> [S.spectral] --> [integral.spatial]│
│        │ BandFilter  SpectralSample  Integrate                   │
│        │ V={L.diag.spectral, S.spectral, integral.spatial}  A={L.diag.spectral-->S.spectral, S.spectral-->integral.spatial}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (spectral bands well-separated)         │
│        │ Uniqueness: YES with PAN constraint                     │
│        │ Stability: κ ≈ 5 (pan-sharpening), κ ≈ 20 (MS alone)  │
│        │ Mismatch: co-registration error, spectral response cal.│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), SAM, ERGAS (secondary)             │
│        │ q = 2.0 (variational pan-sharpening convergence)      │
│        │ T = {PSNR, SAM, ERGAS, K_resolutions}                  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Band count and spectral ranges consistent with sensor model | PASS |
| S2 | PAN + MS fusion well-posed; κ ≈ 5 | PASS |
| S3 | Component substitution / MRA methods converge | PASS |
| S4 | PSNR ≥ 30 dB achievable for 4× pan-sharpening | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# multispectral/sentinel2_s1_ideal.yaml
principle_ref: sha256:<p103_hash>
omega:
  grid_MS: [128, 128]
  grid_PAN: [512, 512]
  bands: 13
  scale_factor: 4
E:
  forward: "y_MS = downsample(ρ, 4) + n; y_PAN = Σ_b S_b·ρ_b"
I:
  dataset: Sentinel2_SR
  scenes: 60
  noise: {type: gaussian, SNR_dB: 35}
  scenario: ideal
O: [PSNR, SAM_deg, ERGAS]
epsilon:
  PSNR_min: 30.0
  SAM_max_deg: 3.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 4× scale factor; 13 bands consistent with Sentinel-2 | PASS |
| S2 | κ ≈ 5 with PAN guidance | PASS |
| S3 | BDSD / variational methods converge | PASS |
| S4 | PSNR ≥ 30 dB feasible for 4× fusion | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# multispectral/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec103_hash>
principle_ref: sha256:<p103_hash>
dataset:
  name: Sentinel2_SR
  scenes: 60
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: BDSD
    results: {PSNR: 31.2, SAM_deg: 2.5, ERGAS: 2.1}
  - solver: MTF-GLP
    results: {PSNR: 32.5, SAM_deg: 2.1, ERGAS: 1.8}
  - solver: PanNet
    results: {PSNR: 35.8, SAM_deg: 1.2, ERGAS: 1.1}
quality_scoring:
  - {min: 36.0, Q: 1.00}
  - {min: 33.0, Q: 0.90}
  - {min: 30.0, Q: 0.80}
  - {min: 28.0, Q: 0.75}
```

**Baseline:** BDSD — PSNR 31.2 dB | **Layer 3 reward:** 60 PWM + upstream

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | SAM (°) | Q |
|--------|-----------|---------|---|
| BDSD | 31.2 | 2.5 | 0.82 |
| MTF-GLP | 32.5 | 2.1 | 0.88 |
| PanNet | 35.8 | 1.2 | 0.98 |
| FusionFormer | 36.5 | 1.0 | 1.00 |

### Reward: `R = 100 × 1 × q` → Best: 100 PWM | Floor: 75 PWM

```json
{
  "h_p": "sha256:<p103_hash>",
  "Q": 0.98,
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
| L4 Solution | — | 75–100 PWM per solve |

## Quick-Start

```bash
pwm-node benchmarks | grep multispectral
pwm-node mine multispectral/sentinel2_s1_ideal.yaml
```
