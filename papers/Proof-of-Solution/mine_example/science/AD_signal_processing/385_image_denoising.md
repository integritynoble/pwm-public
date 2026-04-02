# Principle #385 — Image Denoising: Four-Layer Walkthrough

**Principle #385: Image Denoising**
Domain: Signal & Image Processing | Carrier: data | Difficulty: textbook (delta=1) | Reward: 1x base

---

## Four-Layer Pipeline

```
LAYER 1              LAYER 2              LAYER 3              LAYER 4
seeds -> Useful(B)   Principle + S1-S4    spec.md + Principle   spec.md + Benchmark
designs the          designs              + S1-S4 designs &     + Principle + S1-S4
PRINCIPLE            spec.md (PoInf)      verifies BENCHMARK    verifies SOLUTION

[Seed] --> [Principle] --> [spec.md] --> [Benchmark] --> [Solution]
  L1          L1              L2             L3             L4
```

---

## Layer 1: Seeds -> Principle

### Governing Equation

```
y = x + n,  n ~ N(0, σ²I)   (additive white Gaussian noise)
x̂ = argmin ||y - x||² + λR(x)   (MAP denoising)
R(x): sparsity (wavelet), self-similarity (NLM), or learned (DnCNN)
```

### DAG Decomposition G = (V, A)

```
[K.psf] -> [O.tikhonov]

V = {K.psf, O.tikhonov}
A = {K.psf->O.tikhonov}
L_DAG = 1.0   Tier: textbook (delta = 1)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- noisy image always exists |
| Uniqueness | YES -- MAP estimator unique for strictly convex R |
| Stability | YES -- Lipschitz continuous denoiser for bounded σ |

Mismatch parameters: noise level σ, noise distribution, signal prior model

### Error-Bounding Method

```
e  = PSNR (primary), SSIM (secondary)
q = 0.5 (minimax rate for nonparametric estimation)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Noise variance σ² matches declared level; image dimensions consistent | PASS |
| S2 | MAP estimator bounded for convex regularizer | PASS |
| S3 | BM3D / DnCNN converge; PSNR well-defined | PASS |
| S4 | PSNR >= 30 dB achievable for σ=25 on natural images | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

```yaml
principle_ref: sha256:<principle_385_hash>

omega:
  description: "Gaussian denoising, σ=25, 256x256 grayscale images"
  grid: [256, 256]
  noise: {type: gaussian, sigma: 25}
  outputs: [denoised_image]

E:
  forward: "y = x + n"
  dag: "[K.psf] -> [O.tikhonov]"

B:
  constraints: "pixel range [0,255]; noise i.i.d."

I:
  scenario: ideal
  noise: {type: gaussian, sigma: 25}
  mismatch: null

O: [PSNR, SSIM]

epsilon:
  PSNR_min: 29.0
  SSIM_min: 0.82

difficulty:
  L_DAG: 2.0
  tier: textbook
  delta: 1
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known σ, Gaussian noise | None | PSNR >= 29 dB |
| S2 Mismatch | Wrong σ or non-Gaussian noise | Applied | relaxed 1.5x |
| S3 Oracle | True σ known | Known | PSNR >= 29 dB |
| S4 Blind Cal | Estimate σ from noisy image | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

```yaml
spec_ref: sha256:<spec_385_hash>
principle_ref: sha256:<principle_385_hash>

dataset:
  description: "BSD68 + Set12 denoising benchmark, σ=25"
  images: 80
  data_hash: sha256:<dataset_385_hash>

baselines:
  - solver: BM3D               PSNR: 28.6    q: 0.80
  - solver: DnCNN              PSNR: 29.2    q: 0.88
  - solver: DRUNet             PSNR: 29.8    q: 0.95

quality_scoring:
  metric: PSNR
  thresholds:
    - {min: 30.5, Q: 1.00}
    - {min: 29.5, Q: 0.90}
    - {min: 28.5, Q: 0.80}
    - {min: 27.5, Q: 0.75}
```

### Baselines

| Solver | PSNR | Q | Approx Reward |
|--------|------|---|---------------|
| DRUNet | 29.8 | 0.95 | ~95 PWM |
| DnCNN | 29.2 | 0.88 | ~88 PWM |
| BM3D | 28.6 | 0.80 | ~80 PWM |

### Layer 3 Reward

```
Benchmark seed reward = 100 x phi(t) x 0.60 = 60 PWM (builder)
Upstream: 15% -> L2 designer, 10% -> L1 creator, 15% -> treasury
```

---

## Layer 4: Benchmark -> Solution (PoSol Mining)

### Solver Table

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| BM3D | 28.6 | 0.80 | 1 s | 0.80 |
| DnCNN | 29.2 | 0.86 | 0.05 s | 0.88 |
| DRUNet | 29.8 | 0.89 | 0.1 s | 0.95 |

### Reward Calculation

```
R = R_base x phi(t) x delta x nu_c x q
  = 100 x 1.0 x 1 x 1.0 x q
  = 100 x q  PWM

Best case:  100 x 0.95 = 95 PWM
Worst case: 100 x 0.75 = 75 PWM
```

### S4 Certificate

```json
{
  "principle": "#385 Image Denoising",
  "h_p": "sha256:<principle_385_hash>",
  "h_s": "sha256:<spec_385_hash>",
  "h_b": "sha256:<bench_385_hash>",
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"},
  "Q": 0.95,
  "difficulty": {"tier":"textbook","delta":1}
}
```

---

## Reward Summary

```
L1 Principle:  200 PWM seed + upstream royalties from L2/L3/L4
L2 spec.md:    105 PWM seed (x4 scenarios = 420 PWM) + upstream from L3/L4
L3 Benchmark:   60 PWM seed (x4 benchmarks = 240 PWM) + upstream from L4
L4 Solution:   75-95 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep image_denoising
pwm-node verify AD_signal_processing/image_denoising_s1_ideal.yaml
pwm-node mine AD_signal_processing/image_denoising_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
