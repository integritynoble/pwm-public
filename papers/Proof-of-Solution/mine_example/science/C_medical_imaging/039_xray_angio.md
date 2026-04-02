# Principle #39 — X-ray Angiography

**Domain:** Medical Imaging | **Carrier:** X-ray | **Difficulty:** Basic (delta=2)
**DAG:** [Π.radon.parallel] --> [S.detector] --> [∫.temporal]
**Modality:** Digital subtraction angiography (DSA)

---

## Four-Layer Pipeline

```
L1 seeds->Principle   L2 Principle->spec   L3 spec->Benchmark   L4 Bench->Solution
 domain expert          task designer        data engineer         solver/miner
 contrast + subtract    specific DSA         pre/post-contrast +   subtract/enhance
 model                  tasks                baselines             + earn PWM
 200x phi PWM           150x phi x0.70       100x phi x0.60       Rbase x phi x d x q
```

---

## Layer 1: Seeds -> Principle

### Forward Model

```
y_mask(u,v) = I0 * exp(-Pi{mu_tissue})  + n1
y_fill(u,v) = I0 * exp(-Pi{mu_tissue + mu_contrast}) + n2
y_DSA(u,v) = ln(y_mask) - ln(y_fill) = Pi{mu_contrast} + noise

  Π.radon.parallel --> S.detector --> ∫.temporal
```

### DAG Primitives

| Node | Primitive | Operation |
|------|-----------|-----------|
| Π.radon.parallel | Radon transform | Parallel-beam line-integral projection |
| S.detector | Sample | 2D detector readout |
| ∫.temporal | Integrate | Temporal integration / accumulation |

### Well-Posedness

- Existence: YES -- subtraction isolates contrast
- Uniqueness: CONDITIONAL -- motion between mask/fill corrupts subtraction
- Stability: kappa ~ 8 (no motion), kappa ~ 40 (with motion artifacts)
- Mismatch: patient motion (d_motion), contrast timing (d_timing), scatter (d_scatter)

### Error Method

- Primary: vessel CNR, PSNR (dB)
- Secondary: SSIM, vessel visibility score
- Convergence rate: q = 2.0 (subtraction), q = 1.5 (motion-corrected)

### S1-S4 Gate Checks

| Gate | Check | Result |
|------|-------|--------|
| S1 | Mask/fill frame dimensions consistent | PASS |
| S2 | Subtraction with motion correction is well-posed | PASS |
| S3 | Registration converges for given motion range | PASS |
| S4 | CNR >= 3.0 achievable for standard vessel phantoms | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec (S1 Ideal)

```yaml
principle_ref: sha256:<p39_hash>

omega:
  grid: [1024, 1024]
  frame_rate: 4
  anatomy: cerebral

E:
  forward: "y_DSA = Pi{mu_contrast} + noise"
  task: "motion-corrected DSA from pre/post-contrast frames"

I:
  dataset: DSA_Cerebral_Sim
  sequences: 30
  noise: {type: poisson, I0: 2e4}
  scenario: ideal
  mismatch: null

O: [CNR, PSNR, vessel_visibility]

epsilon:
  CNR_min: 3.0
  PSNR_min: 28.0
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | No motion | None | CNR >= 3.0 |
| S2 Mismatch | Unregistered | d_motion=3px, d_timing=0.5s | CNR >= 1.5 |
| S3 Oracle | True motion field | Known | CNR >= 2.5 |
| S4 Blind Cal | Estimate motion | Deformable registration | Recovery >= 85% |

### Layer 2 Reward

```
spec.md reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark YAML

```yaml
spec_ref: sha256:<spec39_hash>
principle_ref: sha256:<p39_hash>

dataset:
  name: DSA_Cerebral_Sim
  sequences: 30
  resolution: [1024, 1024]
  data_hash: sha256:<dataset_hash>

baselines:
  - solver: Simple_Subtraction
    results: {mean_CNR: 3.2, mean_PSNR: 28.5}
  - solver: Elastic_Registration_DSA
    results: {mean_CNR: 4.1, mean_PSNR: 32.0}
  - solver: DL_DSA
    results: {mean_CNR: 5.2, mean_PSNR: 35.5}

quality_scoring:
  metric: mean_CNR
  thresholds:
    - {min: 5.5, Q: 1.00}
    - {min: 4.5, Q: 0.90}
    - {min: 3.5, Q: 0.80}
    - {min: 3.0, Q: 0.75}
```

### Layer 3 Reward

```
Benchmark reward = 100 x phi(t) x 0.60 = 60 PWM
```

---

## Layer 4: Benchmark -> Solution

### Solver Table

| Solver | CNR | PSNR (dB) | GPU Time | Q | Reward |
|--------|-----|-----------|----------|---|--------|
| Simple Subtraction | 3.2 | 28.5 | <1 s | 0.75 | 150 PWM |
| Elastic Reg. DSA | 4.1 | 32.0 | ~5 s | 0.85 | 170 PWM |
| DL-DSA | 5.2 | 35.5 | ~1 s | 0.95 | 190 PWM |
| TransDSA | 5.8+ | 37+ | ~2 s | 1.00 | 200 PWM |

### Reward Calculation

```
R = 100 x 1.0 x 2 x 1.0 x q = 200 x q PWM
```

### Certificate Snippet

```json
{
  "principle": "sha256:<p39_hash>",
  "spec": "sha256:<spec39_hash>",
  "benchmark": "sha256:<bench39_hash>",
  "r": {"residual_norm": 0.014, "error_bound": 0.032, "ratio": 0.44},
  "c": {"fitted_rate": 1.85, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.85,
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
pwm-node benchmarks | grep xray_angio
pwm-node verify xray_angio/cerebral_s1_ideal.yaml
pwm-node mine xray_angio/cerebral_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
