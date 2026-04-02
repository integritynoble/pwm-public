# Principle #383 — Image Super-Resolution: Four-Layer Walkthrough

**Principle #383: Image Super-Resolution**
Domain: Signal & Image Processing | Carrier: data | Difficulty: standard (delta=3) | Reward: 3x base

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
y = D H x + n           (observation model: downsample + blur + noise)
x̂ = argmin ||y - DHx||² + λR(x)  (regularized super-resolution)
D: downsampling operator (factor s)
H: anti-aliasing blur kernel
```

### DAG Decomposition G = (V, A)

```
[K.psf] -> [L.sparse] -> [O.l1]

V = {K.psf, L.sparse, O.l1}
A = {K.psf->L.sparse, L.sparse->O.l1}
L_DAG = 2.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- downsampled observations always exist |
| Uniqueness | NO -- severely underdetermined; prior/learned model required |
| Stability | CONDITIONAL -- depends on regularization strength and scale factor |

Mismatch parameters: downsampling kernel, scale factor s, noise model, image prior

### Error-Bounding Method

```
e  = PSNR (primary), SSIM (secondary), LPIPS (perceptual)
q = 1.0 (iterative back-projection convergence)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Scale factor s integer; LR/HR grid sizes consistent | PASS |
| S2 | Bounded inverse with sparse/learned prior; consistency constraint met | PASS |
| S3 | SRCNN/EDSR converge; PSNR saturates with training | PASS |
| S4 | PSNR >= 28 dB achievable for x4 upscaling on natural images | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_383_hash>

omega:
  description: "Single-image SR, x4 scale, bicubic degradation, 48x48 -> 192x192"
  scale: 4
  LR_size: [48, 48]
  outputs: [HR_image]

E:
  forward: "y = D H x + n"
  dag: "[K.psf] -> [L.sparse] -> [O.l1]"

B:
  constraints: "HR consistent with LR at downsampled scale; pixel range [0,255]"

I:
  scenario: ideal
  degradation: {kernel: bicubic, noise_sigma: 0}
  mismatch: null

O: [PSNR, SSIM]

epsilon:
  PSNR_min: 28.0
  SSIM_min: 0.80

difficulty:
  L_DAG: 3.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known bicubic degradation | None | PSNR >= 28 dB |
| S2 Mismatch | Unknown degradation kernel | Applied | relaxed 1.5x |
| S3 Oracle | True HR known | Known | PSNR >= 28 dB |
| S4 Blind Cal | Blind SR (unknown kernel) | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_383_hash>
principle_ref: sha256:<principle_383_hash>

dataset:
  description: "Set5 + Set14 + BSD100 standard SR benchmarks"
  images: 119
  data_hash: sha256:<dataset_383_hash>

baselines:
  - solver: Bicubic             PSNR: 24.5    q: 0.75
  - solver: SRCNN               PSNR: 27.5    q: 0.82
  - solver: EDSR                PSNR: 32.5    q: 0.95

quality_scoring:
  metric: PSNR
  thresholds:
    - {min: 33.0, Q: 1.00}
    - {min: 30.0, Q: 0.90}
    - {min: 28.0, Q: 0.80}
    - {min: 26.0, Q: 0.75}
```

### Baselines

| Solver | PSNR | Q | Approx Reward |
|--------|------|---|---------------|
| EDSR | 32.5 | 0.95 | ~285 PWM |
| SRCNN | 27.5 | 0.82 | ~246 PWM |
| Bicubic | 24.5 | 0.75 | ~225 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Image datasets and scale factor match spec | PASS |
| S2 | Problem bounded: bicubic + prior yields finite error | PASS |
| S3 | EDSR converges; PSNR saturates with training epochs | PASS |
| S4 | Baseline meets threshold (PSNR >= 28 dB); feasibility confirmed | PASS |

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
| Bicubic | 24.5 | 0.68 | 0.01 s | 0.75 |
| SRCNN | 27.5 | 0.79 | 0.1 s | 0.82 |
| EDSR | 32.5 | 0.93 | 0.5 s | 0.95 |

### Reward Calculation

```
R = R_base x phi(t) x delta x nu_c x q
  = 100 x 1.0 x 3 x 1.0 x q
  = 300 x q  PWM

Best case:  300 x 0.95 = 285 PWM
Worst case: 300 x 0.75 = 225 PWM
```

### S4 Certificate

```json
{
  "principle": "#383 Image Super-Resolution",
  "h_p": "sha256:<principle_383_hash>",
  "h_s": "sha256:<spec_383_hash>",
  "h_b": "sha256:<bench_383_hash>",
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"},
  "Q": 0.95,
  "difficulty": {"tier":"standard","delta":3}
}
```

---

## Reward Summary

```
L1 Principle:  200 PWM seed + upstream royalties from L2/L3/L4
L2 spec.md:    105 PWM seed (x4 scenarios = 420 PWM) + upstream from L3/L4
L3 Benchmark:   60 PWM seed (x4 benchmarks = 240 PWM) + upstream from L4
L4 Solution:   225-285 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep image_super_resolution
pwm-node verify AD_signal_processing/image_super_resolution_s1_ideal.yaml
pwm-node mine AD_signal_processing/image_super_resolution_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
