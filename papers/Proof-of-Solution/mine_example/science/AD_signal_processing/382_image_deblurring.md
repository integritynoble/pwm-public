# Principle #382 — Image Deblurring (Deconvolution): Four-Layer Walkthrough

**Principle #382: Image Deblurring (Deconvolution)**
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
y = h ⊛ x + n           (blurred noisy observation)
Y(f) = H(f)·X(f) + N(f) (Fourier domain)
Inverse: x̂ = argmin ||y - h⊛x||² + λR(x)  (regularized deconvolution)
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
| Existence | YES -- convolution with bounded PSF always produces output |
| Uniqueness | YES -- unique within OTF support with regularization |
| Stability | CONDITIONAL -- ill-posed without regularization; Wiener or TV stabilizes |

Mismatch parameters: PSF model error, noise level, boundary conditions, regularization λ

### Error-Bounding Method

```
e  = PSNR (primary), SSIM (secondary)
q = 2.0 (Richardson-Lucy O(1/k²) convergence)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | PSF dimensions match image grid; kernel normalized to sum=1 | PASS |
| S2 | OTF non-zero over support; Wiener filter bounded | PASS |
| S3 | Richardson-Lucy / ADMM converges monotonically | PASS |
| S4 | PSNR >= 30 dB achievable for moderate blur + noise | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_382_hash>

omega:
  description: "Gaussian blur σ=2px, AWGN σ_n=5, 256x256 natural images"
  grid: [256, 256]
  blur: {type: gaussian, sigma: 2.0}
  outputs: [restored_image]

E:
  forward: "y = h ⊛ x + n"
  dag: "[K.psf] -> [O.tikhonov]"

B:
  constraints: "x ≥ 0; PSF known; boundary: periodic"

I:
  scenario: ideal
  noise: {type: gaussian, sigma: 5.0}
  mismatch: null

O: [PSNR, SSIM]

epsilon:
  PSNR_min: 30.0
  SSIM_min: 0.85

difficulty:
  L_DAG: 2.0
  tier: textbook
  delta: 1
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known PSF + known noise level | None | PSNR >= 30 dB |
| S2 Mismatch | Wrong PSF width or noise level | Applied | relaxed 1.5x |
| S3 Oracle | True PSF known | Known | PSNR >= 30 dB |
| S4 Blind Cal | Estimate PSF from blurred image | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_382_hash>
principle_ref: sha256:<principle_382_hash>

dataset:
  description: "Standard test images with Gaussian blur + AWGN"
  images: 20
  size: [256, 256]
  data_hash: sha256:<dataset_382_hash>

baselines:
  - solver: Wiener              PSNR: 29.5    q: 0.78
  - solver: Richardson-Lucy     PSNR: 31.0    q: 0.85
  - solver: IRCNN-deblur        PSNR: 34.5    q: 0.95

quality_scoring:
  metric: PSNR
  thresholds:
    - {min: 35.0, Q: 1.00}
    - {min: 32.0, Q: 0.90}
    - {min: 30.0, Q: 0.80}
    - {min: 28.0, Q: 0.75}
```

### Baselines

| Solver | PSNR | Q | Approx Reward |
|--------|------|---|---------------|
| IRCNN-deblur | 34.5 | 0.95 | ~95 PWM |
| Richardson-Lucy | 31.0 | 0.85 | ~85 PWM |
| Wiener | 29.5 | 0.78 | ~78 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Image sizes and blur parameters match spec | PASS |
| S2 | Problem well-posed: known PSF + Wiener filter bounded | PASS |
| S3 | IRCNN converges; PSNR improves with iterations | PASS |
| S4 | Baseline meets threshold (PSNR >= 30 dB); feasibility confirmed | PASS |

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
| Wiener | 29.5 | 0.82 | 0.05 s | 0.78 |
| Richardson-Lucy | 31.0 | 0.87 | 1 s | 0.85 |
| IRCNN-deblur | 34.5 | 0.94 | 0.3 s | 0.95 |

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
  "principle": "#382 Image Deblurring (Deconvolution)",
  "h_p": "sha256:<principle_382_hash>",
  "h_s": "sha256:<spec_382_hash>",
  "h_b": "sha256:<bench_382_hash>",
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
pwm-node benchmarks | grep image_deblurring
pwm-node verify AD_signal_processing/image_deblurring_s1_ideal.yaml
pwm-node mine AD_signal_processing/image_deblurring_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
