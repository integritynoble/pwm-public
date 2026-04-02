# Principle #31 — X-ray Radiography

**Domain:** Medical Imaging | **Carrier:** X-ray | **Difficulty:** Basic (delta=2)
**DAG:** [Π.radon.parallel] --> [S.detector]
**Modality:** Projection radiography (single-view)

---

## Four-Layer Pipeline

```
L1 seeds->Principle   L2 Principle->spec   L3 spec->Benchmark   L4 Bench->Solution
 domain expert          task designer        data engineer         solver/miner
 Beer-Lambert +         specific radiog.     projection data +     enhance/segment
 attenuation model      enhancement tasks    baselines             + earn PWM
 200x phi PWM           150x phi x0.70       100x phi x0.60       Rbase x phi x d x q
```

---

## Layer 1: Seeds -> Principle

### Forward Model

```
y(u,v) = I0 * exp(- integral mu(x,y,z) dl ) + n

  Π.radon.parallel --> S.detector
```

### DAG Primitives

| Node | Primitive | Operation |
|------|-----------|-----------|
| Π.radon.parallel | Radon transform | Parallel-beam line-integral projection |
| S.detector | Sample | 2D detector readout |

### Well-Posedness

- Existence: YES -- projection is well-defined for non-negative mu
- Uniqueness: NO -- single-view projection loses depth; 2D recovery only
- Stability: STABLE -- kappa ~ 5 (single-view enhancement tasks)
- Mismatch: scatter fraction (alpha_s), beam hardening (alpha_bh), detector gain drift (dg)

### Error Method

- Primary: PSNR (dB), SSIM for enhancement; Dice/IoU for segmentation
- Convergence rate: q = 2.0 (denoising), q = 1.5 (scatter correction)

### S1-S4 Gate Checks

| Gate | Check | Result |
|------|-------|--------|
| S1 | Projection dimensions match detector geometry | PASS |
| S2 | Enhancement/scatter correction is well-posed for single-view | PASS |
| S3 | U-Net denoiser converges; scatter estimator converges | PASS |
| S4 | PSNR >= 32 dB achievable for denoising tasks | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec (S1 Ideal)

```yaml
principle_ref: sha256:<p31_hash>

omega:
  grid: [2048, 2048]
  bit_depth: 14
  anatomy: chest

E:
  forward: "y = I0 * exp(-Pi{mu}) + scatter + n"
  task: "low-dose denoising: recover full-dose from quarter-dose"

I:
  dataset: NIH_ChestXray14
  images: 200
  noise: {type: poisson, I0_quarter: 2.5e4}
  scenario: ideal
  mismatch: null

O: [PSNR, SSIM]

epsilon:
  PSNR_min: 32.0
  SSIM_min: 0.90
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known dose level | None | PSNR >= 32 dB |
| S2 Mismatch | Nominal scatter model | alpha_s=0.15, dg=3% | PSNR >= 28 dB |
| S3 Oracle | True scatter + gain | Known | PSNR >= 30 dB |
| S4 Blind Cal | Estimate scatter from image | Grid search | Recovery >= 85% |

### Layer 2 Reward

```
spec.md reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark YAML

```yaml
spec_ref: sha256:<spec31_hash>
principle_ref: sha256:<p31_hash>

dataset:
  name: NIH_ChestXray14
  images: 200
  resolution: [2048, 2048]
  data_hash: sha256:<dataset_hash>

baselines:
  - solver: BM3D
    results: {mean_PSNR: 32.5, mean_SSIM: 0.905}
  - solver: RED-CNN
    results: {mean_PSNR: 35.2, mean_SSIM: 0.938}
  - solver: Restormer
    results: {mean_PSNR: 37.1, mean_SSIM: 0.955}

quality_scoring:
  metric: mean_PSNR
  thresholds:
    - {min: 38.0, Q: 1.00}
    - {min: 35.0, Q: 0.90}
    - {min: 32.0, Q: 0.80}
    - {min: 30.0, Q: 0.75}
```

### Layer 3 Reward

```
Benchmark reward = 100 x phi(t) x 0.60 = 60 PWM
```

---

## Layer 4: Benchmark -> Solution

### Solver Table

| Solver | PSNR (dB) | SSIM | GPU Time | Q | Reward |
|--------|-----------|------|----------|---|--------|
| BM3D | ~32.5 | 0.905 | ~5 s | 0.80 | 160 PWM |
| RED-CNN | ~35.2 | 0.938 | ~0.3 s | 0.90 | 180 PWM |
| Restormer | ~37.1 | 0.955 | ~0.8 s | 0.95 | 190 PWM |
| SwinIR | ~38+ | 0.962 | ~1 s | 1.00 | 200 PWM |

### Reward Calculation

```
R = 100 x 1.0 x 2 x 1.0 x q = 200 x q PWM
```

### Certificate Snippet

```json
{
  "principle": "sha256:<p31_hash>",
  "spec": "sha256:<spec31_hash>",
  "benchmark": "sha256:<bench31_hash>",
  "r": {"residual_norm": 0.010, "error_bound": 0.025, "ratio": 0.40},
  "c": {"fitted_rate": 1.92, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.90,
  "gate_verdicts": {"S1": "pass", "S2": "pass", "S3": "pass", "S4": "pass"}
}
```

---

## Reward Summary

```
Layer    One-time Seed          Ongoing Upstream
L1       200 x phi PWM          15% L2 + 10% L3 + 5% L4 mint
L2       105 PWM (x4 specs)     15% L3 + 10% L4 mint
L3        60 PWM (x4 benches)   15% L4 mint
L4       200 x q PWM per solve  Miner keeps 100%
```

---

## Quick-Start Commands

```bash
pwm-node benchmarks | grep xray_radiography
pwm-node verify xray_radiography/nih_s1_ideal.yaml
pwm-node mine xray_radiography/nih_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
