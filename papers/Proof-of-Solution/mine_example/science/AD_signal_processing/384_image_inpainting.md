# Principle #384 — Image Inpainting: Four-Layer Walkthrough

**Principle #384: Image Inpainting**
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
y = M ⊙ x + n           (masked observation)
M: binary mask (1 = observed, 0 = missing)
x̂ = argmin ||M⊙(y - x)||² + λR(x)  (regularized inpainting)
R(x): total variation, patch-based, or learned prior
```

### DAG Decomposition G = (V, A)

```
[L.sparse] -> [S.random] -> [O.l1]

V = {L.sparse, S.random, O.l1}
A = {L.sparse->S.random, S.random->O.l1}
L_DAG = 2.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- masked image always exists |
| Uniqueness | NO -- severely underdetermined in masked regions; prior required |
| Stability | CONDITIONAL -- depends on mask ratio and prior strength |

Mismatch parameters: mask pattern, texture complexity, prior model, hole size

### Error-Bounding Method

```
e  = PSNR (primary), SSIM (secondary), FID (perceptual)
q = 1.0 (iterative optimization convergence)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Mask binary; image dimensions consistent; observed pixels sufficient | PASS |
| S2 | Data fidelity in observed region bounded; TV regularization stabilizes | PASS |
| S3 | PatchMatch / deep inpainting converges | PASS |
| S4 | PSNR >= 28 dB achievable for < 50% missing pixels | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

```yaml
principle_ref: sha256:<principle_384_hash>

omega:
  description: "Center-mask inpainting, 128x128 hole in 256x256 image"
  grid: [256, 256]
  mask: {type: center, size: 128}
  outputs: [inpainted_image]

E:
  forward: "y = M ⊙ x + n"
  dag: "[L.sparse] -> [S.random] -> [O.l1]"

B:
  constraints: "pixel range [0,255]; observed pixels unchanged"

I:
  scenario: ideal
  noise: {type: none}
  mismatch: null

O: [PSNR, SSIM]

epsilon:
  PSNR_min: 25.0
  SSIM_min: 0.80

difficulty:
  L_DAG: 2.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known mask + clean input | None | PSNR >= 25 dB |
| S2 Mismatch | Irregular mask or noisy input | Applied | relaxed 1.5x |
| S3 Oracle | True image known | Known | PSNR >= 25 dB |
| S4 Blind Cal | Arbitrary mask shape | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

```yaml
spec_ref: sha256:<spec_384_hash>
principle_ref: sha256:<principle_384_hash>

dataset:
  description: "Places2 / CelebA inpainting benchmark"
  images: 100
  data_hash: sha256:<dataset_384_hash>

baselines:
  - solver: PatchMatch          PSNR: 26.0    q: 0.80
  - solver: DeepFill-v2         PSNR: 30.5    q: 0.92
  - solver: LaMa                PSNR: 32.0    q: 0.95

quality_scoring:
  metric: PSNR
  thresholds:
    - {min: 33.0, Q: 1.00}
    - {min: 30.0, Q: 0.90}
    - {min: 27.0, Q: 0.80}
    - {min: 25.0, Q: 0.75}
```

### Baselines

| Solver | PSNR | Q | Approx Reward |
|--------|------|---|---------------|
| LaMa | 32.0 | 0.95 | ~285 PWM |
| DeepFill-v2 | 30.5 | 0.92 | ~276 PWM |
| PatchMatch | 26.0 | 0.80 | ~240 PWM |

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
| PatchMatch | 26.0 | 0.78 | 2 s | 0.80 |
| DeepFill-v2 | 30.5 | 0.90 | 0.1 s | 0.92 |
| LaMa | 32.0 | 0.93 | 0.2 s | 0.95 |

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
  "principle": "#384 Image Inpainting",
  "h_p": "sha256:<principle_384_hash>",
  "h_s": "sha256:<spec_384_hash>",
  "h_b": "sha256:<bench_384_hash>",
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
pwm-node benchmarks | grep image_inpainting
pwm-node verify AD_signal_processing/image_inpainting_s1_ideal.yaml
pwm-node mine AD_signal_processing/image_inpainting_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
