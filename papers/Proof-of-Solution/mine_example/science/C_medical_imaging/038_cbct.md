# Principle #38 — Cone-Beam CT

**Domain:** Medical Imaging | **Carrier:** X-ray | **Difficulty:** Standard (delta=3)
**DAG:** [Π.radon.cone] --> [S.angular.full]
**Modality:** Cone-beam computed tomography

---

## Four-Layer Pipeline

```
L1 seeds->Principle   L2 Principle->spec   L3 spec->Benchmark   L4 Bench->Solution
 domain expert          task designer        data engineer         solver/miner
 cone-beam geometry +   specific CBCT        projection data +     reconstruct +
 FDK/iterative model    recon tasks          baselines             earn PWM
 200x phi PWM           150x phi x0.70       100x phi x0.60       Rbase x phi x d x q
```

---

## Layer 1: Seeds -> Principle

### Forward Model

```
y(u,v,theta) = integral f(x(s),y(s),z(s)) ds + n     (cone-beam projection)

  Π.radon.cone --> S.angular.full
```

### DAG Primitives

| Node | Primitive | Operation |
|------|-----------|-----------|
| Π.radon.cone | Radon transform | Cone-beam divergent projection |
| S.angular.full | Sample | Full-angle detector sampling |

### Well-Posedness

- Existence: YES -- Tuy's condition satisfied for circular orbit (mid-plane)
- Uniqueness: CONDITIONAL -- cone-beam artifacts at off-axis slices
- Stability: kappa ~ 15 (full rotation), kappa ~ 80 (limited-angle/sparse)
- Mismatch: geometric misalignment (dx,dy,dz,dphi), detector tilt (d_tilt), scatter (d_scatter)

### Error Method

- Primary: PSNR (dB), SSIM
- Secondary: RMSE (HU), cone-beam artifact metric
- Convergence rate: q = 2.0 (FDK), q = 1.0 (iterative SART)

### S1-S4 Gate Checks

| Gate | Check | Result |
|------|-------|--------|
| S1 | Projection dimensions [N_u x N_v x N_theta] match cone geometry | PASS |
| S2 | Circular orbit satisfies Tuy's condition for central slice | PASS |
| S3 | FDK converges analytically; SART converges at O(1/k) | PASS |
| S4 | PSNR >= 28 dB achievable for head phantom | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec (S1 Ideal)

```yaml
principle_ref: sha256:<p38_hash>

omega:
  grid: [256, 256, 256]
  n_projections: 360
  detector: [512, 384]
  SOD_mm: 1000
  SDD_mm: 1500

E:
  forward: "y(u,v,theta) = cone_beam_project{f}(u,v,theta) + n"
  inverse: "recover f from cone-beam projections"

I:
  dataset: CBCT_Head_Sim
  phantoms: 10
  noise: {type: poisson, I0: 5e4}
  scenario: ideal
  mismatch: null

O: [PSNR, SSIM, RMSE_HU]

epsilon:
  PSNR_min: 28.0
  SSIM_min: 0.82
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Calibrated geometry | None | PSNR >= 28 dB |
| S2 Mismatch | Nominal geometry | dx=0.5mm, d_tilt=0.3deg | PSNR >= 24 dB |
| S3 Oracle | True geometry | Known | PSNR >= 26 dB |
| S4 Blind Cal | Estimate geometry | Fiducial markers | Recovery >= 85% |

### Layer 2 Reward

```
spec.md reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark YAML

```yaml
spec_ref: sha256:<spec38_hash>
principle_ref: sha256:<p38_hash>

dataset:
  name: CBCT_Head_Sim
  phantoms: 10
  volume: [256, 256, 256]
  projections: 360
  data_hash: sha256:<dataset_hash>

baselines:
  - solver: FDK
    results: {mean_PSNR: 28.5, mean_SSIM: 0.835}
  - solver: SART_TV
    results: {mean_PSNR: 31.2, mean_SSIM: 0.895}
  - solver: DiffusionMBIR
    results: {mean_PSNR: 34.8, mean_SSIM: 0.940}

quality_scoring:
  metric: mean_PSNR
  thresholds:
    - {min: 36.0, Q: 1.00}
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
| FDK | ~28.5 | 0.835 | ~5 s | 0.80 | 240 PWM |
| SART-TV | ~31.2 | 0.895 | ~60 s | 0.88 | 264 PWM |
| DiffusionMBIR | ~34.8 | 0.940 | ~120 s | 0.95 | 285 PWM |
| NAF-CBCT | ~37+ | 0.960 | ~90 s | 1.00 | 300 PWM |

### Reward Calculation

```
R = 100 x 1.0 x 3 x 1.0 x q = 300 x q PWM
```

### Certificate Snippet

```json
{
  "principle": "sha256:<p38_hash>",
  "spec": "sha256:<spec38_hash>",
  "benchmark": "sha256:<bench38_hash>",
  "r": {"residual_norm": 0.022, "error_bound": 0.045, "ratio": 0.49},
  "c": {"fitted_rate": 1.90, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.95,
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
pwm-node benchmarks | grep cbct
pwm-node verify cbct/head_s1_ideal.yaml
pwm-node mine cbct/head_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
