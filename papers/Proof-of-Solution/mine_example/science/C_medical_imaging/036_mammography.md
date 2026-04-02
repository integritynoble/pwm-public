# Principle #36 — Mammography

**Domain:** Medical Imaging | **Carrier:** X-ray | **Difficulty:** Basic (delta=2)
**DAG:** [Π.radon.parallel] --> [S.detector]
**Modality:** Full-field digital mammography

---

## Four-Layer Pipeline

```
L1 seeds->Principle   L2 Principle->spec   L3 spec->Benchmark   L4 Bench->Solution
 domain expert          task designer        data engineer         solver/miner
 breast attenuation +   specific mammo       projection data +     enhance/detect
 scatter model          tasks                baselines             + earn PWM
 200x phi PWM           150x phi x0.70       100x phi x0.60       Rbase x phi x d x q
```

---

## Layer 1: Seeds -> Principle

### Forward Model

```
y(u,v) = I0 * exp(- integral mu_breast(x,y,z) dl ) * ASF + n

  Π.radon.parallel --> S.detector
  ASF = anti-scatter factor
```

### DAG Primitives

| Node | Primitive | Operation |
|------|-----------|-----------|
| Π.radon.parallel | Radon transform | Parallel-beam line-integral projection |
| S.detector | Sample | 2D detector readout |

### Well-Posedness

- Existence: YES -- projection well-defined for non-negative mu
- Uniqueness: NO -- single-view (enhancement/detection tasks)
- Stability: kappa ~ 6 (enhancement), kappa ~ 15 (with scatter)
- Mismatch: scatter fraction (alpha_s), compression thickness error (dz), heel effect (d_he)

### Error Method

- Primary: PSNR (dB) for enhancement; sensitivity/specificity for detection
- Secondary: SSIM, AUC
- Convergence rate: q = 2.0 (denoising)

### S1-S4 Gate Checks

| Gate | Check | Result |
|------|-------|--------|
| S1 | Image dimensions match detector geometry | PASS |
| S2 | Enhancement task well-posed for single-view | PASS |
| S3 | Denoiser converges for given noise level | PASS |
| S4 | PSNR >= 30 dB achievable for dose-reduced images | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec (S1 Ideal)

```yaml
principle_ref: sha256:<p36_hash>

omega:
  grid: [3328, 4096]
  pixel_pitch_um: 70
  bit_depth: 14

E:
  forward: "y = I0*exp(-Pi{mu_breast})*ASF + n"
  task: "low-dose mammogram enhancement"

I:
  dataset: VinDr_Mammo
  images: 200
  noise: {type: poisson, dose_reduction: 4x}
  scenario: ideal
  mismatch: null

O: [PSNR, SSIM]

epsilon:
  PSNR_min: 30.0
  SSIM_min: 0.88
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known dose + scatter | None | PSNR >= 30 dB |
| S2 Mismatch | Nominal scatter model | alpha_s=0.20, d_he=5% | PSNR >= 26 dB |
| S3 Oracle | True scatter map | Known | PSNR >= 28 dB |
| S4 Blind Cal | Estimate scatter from image | Polynomial fit | Recovery >= 85% |

### Layer 2 Reward

```
spec.md reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark YAML

```yaml
spec_ref: sha256:<spec36_hash>
principle_ref: sha256:<p36_hash>

dataset:
  name: VinDr_Mammo
  images: 200
  resolution: [3328, 4096]
  data_hash: sha256:<dataset_hash>

baselines:
  - solver: BM3D
    results: {mean_PSNR: 30.8, mean_SSIM: 0.895}
  - solver: RED-CNN
    results: {mean_PSNR: 33.5, mean_SSIM: 0.932}
  - solver: Restormer
    results: {mean_PSNR: 35.2, mean_SSIM: 0.950}

quality_scoring:
  metric: mean_PSNR
  thresholds:
    - {min: 36.0, Q: 1.00}
    - {min: 33.0, Q: 0.90}
    - {min: 30.0, Q: 0.80}
    - {min: 28.0, Q: 0.75}
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
| BM3D | ~30.8 | 0.895 | ~8 s | 0.80 | 160 PWM |
| RED-CNN | ~33.5 | 0.932 | ~0.5 s | 0.90 | 180 PWM |
| Restormer | ~35.2 | 0.950 | ~1 s | 0.95 | 190 PWM |
| SwinIR | ~36+ | 0.960 | ~1.5 s | 1.00 | 200 PWM |

### Reward Calculation

```
R = 100 x 1.0 x 2 x 1.0 x q = 200 x q PWM
```

### Certificate Snippet

```json
{
  "principle": "sha256:<p36_hash>",
  "spec": "sha256:<spec36_hash>",
  "benchmark": "sha256:<bench36_hash>",
  "r": {"residual_norm": 0.011, "error_bound": 0.028, "ratio": 0.39},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep mammography
pwm-node verify mammography/vindr_s1_ideal.yaml
pwm-node mine mammography/vindr_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
