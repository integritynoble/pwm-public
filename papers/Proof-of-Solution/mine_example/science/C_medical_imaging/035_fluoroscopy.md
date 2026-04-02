# Principle #35 — Fluoroscopy

**Domain:** Medical Imaging | **Carrier:** X-ray | **Difficulty:** Basic (delta=2)
**DAG:** [Π.radon.parallel] --> [S.detector] --> [∫.temporal]
**Modality:** Real-time X-ray fluoroscopy

---

## Four-Layer Pipeline

```
L1 seeds->Principle   L2 Principle->spec   L3 spec->Benchmark   L4 Bench->Solution
 domain expert          task designer        data engineer         solver/miner
 temporal projection    specific fluoro      video sequence +      denoise/enhance
 + low-dose model       enhancement tasks    baselines             + earn PWM
 200x phi PWM           150x phi x0.70       100x phi x0.60       Rbase x phi x d x q
```

---

## Layer 1: Seeds -> Principle

### Forward Model

```
y_t(u,v) = I0(t) * exp(- integral mu(x,y,z,t) dl ) + n_t

  Π.radon.parallel --> S.detector --> ∫.temporal
```

### DAG Primitives

| Node | Primitive | Operation |
|------|-----------|-----------|
| Π.radon.parallel | Radon transform | Parallel-beam line-integral projection |
| S.detector | Sample | 2D detector readout |
| ∫.temporal | Integrate | Temporal integration / accumulation |

### Well-Posedness

- Existence: YES -- each frame is a standard projection
- Uniqueness: NO -- single-view (2D recovery per frame)
- Stability: kappa ~ 8 (temporal denoising), kappa ~ 25 (low-pulse-rate)
- Mismatch: dose fluctuation (dI0), motion blur (d_motion), lag artifact (d_lag)

### Error Method

- Primary: PSNR (dB), SSIM (per frame)
- Secondary: temporal consistency (TPSNR), motion artifact score
- Convergence rate: q = 2.0 (spatial denoising), q = 1.5 (temporal)

### S1-S4 Gate Checks

| Gate | Check | Result |
|------|-------|--------|
| S1 | Frame dimensions and temporal sampling rate consistent | PASS |
| S2 | Temporal correlation exploitable for denoising | PASS |
| S3 | BM4D / temporal denoiser converges | PASS |
| S4 | PSNR >= 28 dB achievable for denoised fluoroscopy | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec (S1 Ideal)

```yaml
principle_ref: sha256:<p35_hash>

omega:
  grid: [512, 512]
  frame_rate: 15
  n_frames: 100
  anatomy: cardiac

E:
  forward: "y_t = I0*exp(-Pi{mu_t}) + n_t"
  task: "low-dose temporal denoising"

I:
  dataset: Fluoro_Cardiac_Sim
  sequences: 20
  noise: {type: poisson, I0: 5e3}
  scenario: ideal
  mismatch: null

O: [PSNR, SSIM, TPSNR]

epsilon:
  PSNR_min: 28.0
  SSIM_min: 0.85
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known dose level | None | PSNR >= 28 dB |
| S2 Mismatch | Nominal dose | dI0=15%, d_lag=5% | PSNR >= 24 dB |
| S3 Oracle | True dose + lag model | Known | PSNR >= 26 dB |
| S4 Blind Cal | Estimate dose/lag | Adaptive filtering | Recovery >= 85% |

### Layer 2 Reward

```
spec.md reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark YAML

```yaml
spec_ref: sha256:<spec35_hash>
principle_ref: sha256:<p35_hash>

dataset:
  name: Fluoro_Cardiac_Sim
  sequences: 20
  frames_per_seq: 100
  resolution: [512, 512]
  data_hash: sha256:<dataset_hash>

baselines:
  - solver: Temporal_Average
    results: {mean_PSNR: 28.5, mean_SSIM: 0.86}
  - solver: BM4D
    results: {mean_PSNR: 31.2, mean_SSIM: 0.91}
  - solver: FastDVDnet
    results: {mean_PSNR: 33.8, mean_SSIM: 0.94}

quality_scoring:
  metric: mean_PSNR
  thresholds:
    - {min: 35.0, Q: 1.00}
    - {min: 32.0, Q: 0.90}
    - {min: 28.0, Q: 0.80}
    - {min: 26.0, Q: 0.75}
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
| Temporal Avg | ~28.5 | 0.86 | <0.1 s/fr | 0.80 | 160 PWM |
| BM4D | ~31.2 | 0.91 | ~2 s/fr | 0.88 | 176 PWM |
| FastDVDnet | ~33.8 | 0.94 | ~0.05 s/fr | 0.93 | 186 PWM |
| RVRT | ~35+ | 0.96 | ~0.1 s/fr | 1.00 | 200 PWM |

### Reward Calculation

```
R = 100 x 1.0 x 2 x 1.0 x q = 200 x q PWM
```

### Certificate Snippet

```json
{
  "principle": "sha256:<p35_hash>",
  "spec": "sha256:<spec35_hash>",
  "benchmark": "sha256:<bench35_hash>",
  "r": {"residual_norm": 0.015, "error_bound": 0.035, "ratio": 0.43},
  "c": {"fitted_rate": 1.88, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.93,
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
pwm-node benchmarks | grep fluoroscopy
pwm-node verify fluoroscopy/cardiac_s1_ideal.yaml
pwm-node mine fluoroscopy/cardiac_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
