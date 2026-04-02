# Principle #34 — SPECT

**Domain:** Medical Imaging | **Carrier:** Gamma | **Difficulty:** Standard (delta=3)
**DAG:** [Π.radon.parallel] --> [L.diag.spectral] --> [S.angular]
**Modality:** Single Photon Emission Computed Tomography

---

## Four-Layer Pipeline

```
L1 seeds->Principle   L2 Principle->spec   L3 spec->Benchmark   L4 Bench->Solution
 domain expert          task designer        data engineer         solver/miner
 collimator model +     specific SPECT       projection data +     reconstruct +
 attenuation/scatter    recon tasks          baselines             earn PWM
 200x phi PWM           150x phi x0.70       100x phi x0.60       Rbase x phi x d x q
```

---

## Layer 1: Seeds -> Principle

### Forward Model

```
y_i = sum_j c_ij * a_ij * d_ij * f_j + s_i + n_i

  Π.radon.parallel --> L.diag.spectral --> S.angular
  c_ij = collimator response, a_ij = attenuation, d_ij = depth-dependent blur
```

### DAG Primitives

| Node | Primitive | Operation |
|------|-----------|-----------|
| Π.radon.parallel | Radon transform | Parallel-beam line-integral projection |
| L.diag.spectral | Linear diagonal | Energy-dependent attenuation weighting |
| S.angular | Sample | Angular detector sampling |

### Well-Posedness

- Existence: YES -- collimated projections define a limited-angle Radon transform
- Uniqueness: YES -- sufficient angular sampling with attenuation correction
- Stability: CONDITIONAL -- kappa ~ 30 (full-angle), kappa ~ 120 (limited-angle)
- Mismatch: collimator-detector response error (d_cdr), attenuation map error (d_mu), center-of-rotation offset (d_cor)

### Error Method

- Primary: PSNR (dB), NMSE
- Secondary: CNR (lesion detectability), quantitative accuracy (%)
- Convergence rate: q = 1.0 (MLEM), q = 1.5 (OSEM with depth correction)

### S1-S4 Gate Checks

| Gate | Check | Result |
|------|-------|--------|
| S1 | Projection dimensions match detector heads and rotation angles | PASS |
| S2 | Angular sampling and count level sufficient for stable recon | PASS |
| S3 | OSEM converges with monotonic log-likelihood increase | PASS |
| S4 | PSNR >= 22 dB achievable for Jaszczak phantom | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec (S1 Ideal)

```yaml
principle_ref: sha256:<p34_hash>

omega:
  grid: [128, 128, 128]
  n_projections: 120
  detector_size: [128, 128]
  collimator: LEHR

E:
  forward: "y_i = sum_j c_ij * a_ij * d_ij * f_j + s + n"
  inverse: "recover tracer f from collimated projections"

I:
  dataset: SIMIND_cardiac
  phantoms: 10
  noise: {type: poisson, total_counts: 2e7}
  scenario: ideal
  mismatch: null

O: [PSNR, NMSE, CNR]

epsilon:
  PSNR_min: 22.0
  NMSE_max: 0.15
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known CDR + mu-map | None | PSNR >= 22 dB |
| S2 Mismatch | Nominal CDR | d_cdr=10%, d_cor=2px | PSNR >= 18 dB |
| S3 Oracle | True CDR + mu-map | Known | PSNR >= 20 dB |
| S4 Blind Cal | Estimate COR from data | Sinogram fitting | Recovery >= 85% |

### Layer 2 Reward

```
spec.md reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark YAML

```yaml
spec_ref: sha256:<spec34_hash>
principle_ref: sha256:<p34_hash>

dataset:
  name: SIMIND_cardiac
  phantoms: 10
  resolution: [128, 128, 128]
  data_hash: sha256:<dataset_hash>

baselines:
  - solver: FBP
    results: {mean_PSNR: 18.5, mean_NMSE: 0.22}
  - solver: OSEM_8sub
    results: {mean_PSNR: 23.2, mean_NMSE: 0.12}
  - solver: MAP_OSEM
    results: {mean_PSNR: 25.1, mean_NMSE: 0.09}

quality_scoring:
  metric: mean_PSNR
  thresholds:
    - {min: 28.0, Q: 1.00}
    - {min: 25.0, Q: 0.90}
    - {min: 22.0, Q: 0.80}
    - {min: 20.0, Q: 0.75}
```

### Layer 3 Reward

```
Benchmark reward = 100 x phi(t) x 0.60 = 60 PWM
```

---

## Layer 4: Benchmark -> Solution

### Solver Table

| Solver | PSNR (dB) | NMSE | GPU Time | Q | Reward |
|--------|-----------|------|----------|---|--------|
| FBP | ~18 | 0.22 | <1 s | 0.75 | 225 PWM |
| OSEM | ~23 | 0.12 | ~15 s | 0.82 | 246 PWM |
| MAP-OSEM | ~25 | 0.09 | ~30 s | 0.90 | 270 PWM |
| DL-SPECT | ~29+ | 0.05 | ~3 s | 1.00 | 300 PWM |

### Reward Calculation

```
R = 100 x 1.0 x 3 x 1.0 x q = 300 x q PWM
```

### Certificate Snippet

```json
{
  "principle": "sha256:<p34_hash>",
  "spec": "sha256:<spec34_hash>",
  "benchmark": "sha256:<bench34_hash>",
  "r": {"residual_norm": 0.042, "error_bound": 0.08, "ratio": 0.52},
  "c": {"fitted_rate": 1.05, "theoretical_rate": 1.0, "K": 3},
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
L4       300 x q PWM per solve  Miner keeps 100%
```

---

## Quick-Start Commands

```bash
pwm-node benchmarks | grep spect
pwm-node verify spect/simind_s1_ideal.yaml
pwm-node mine spect/simind_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
