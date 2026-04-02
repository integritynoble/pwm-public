# Principle #37 — DEXA

**Domain:** Medical Imaging | **Carrier:** X-ray | **Difficulty:** Basic (delta=2)
**DAG:** [Π.radon.parallel] --> [L.diag.spectral] --> [S.detector]
**Modality:** Dual-Energy X-ray Absorptiometry

---

## Four-Layer Pipeline

```
L1 seeds->Principle   L2 Principle->spec   L3 spec->Benchmark   L4 Bench->Solution
 domain expert          task designer        data engineer         solver/miner
 dual-energy model +    specific DEXA        dual-energy data +    decompose/quantify
 tissue decomposition   decomp tasks         baselines             + earn PWM
 200x phi PWM           150x phi x0.70       100x phi x0.60       Rbase x phi x d x q
```

---

## Layer 1: Seeds -> Principle

### Forward Model

```
y_lo(u,v) = I0_lo * exp(-(mu_b_lo*t_b + mu_s_lo*t_s)) + n_lo
y_hi(u,v) = I0_hi * exp(-(mu_b_hi*t_b + mu_s_hi*t_s)) + n_hi

  Π.radon.parallel --> L.diag.spectral --> S.detector
```

### DAG Primitives

| Node | Primitive | Operation |
|------|-----------|-----------|
| Π.radon.parallel | Radon transform | Parallel-beam line-integral projection |
| L.diag.spectral | Linear diagonal | Energy-dependent attenuation weighting |
| S.detector | Sample | 2D detector readout |

### Well-Posedness

- Existence: YES -- two equations for two unknowns (bone + soft tissue)
- Uniqueness: YES -- dual-energy decomposition is unique when mu_b/mu_s differ
- Stability: kappa ~ 12 (high-dose), kappa ~ 40 (low-dose)
- Mismatch: beam hardening (d_bh), soft-tissue composition error (d_st), positioning error (d_pos)

### Error Method

- Primary: BMD accuracy (g/cm^2), T-score error
- Secondary: PSNR (dB) for bone image, precision error (%)
- Convergence rate: q = 2.0 (analytic decomposition)

### S1-S4 Gate Checks

| Gate | Check | Result |
|------|-------|--------|
| S1 | Low/high energy images match detector grid | PASS |
| S2 | Dual-energy separation sufficient for bone/soft decomposition | PASS |
| S3 | Analytic decomposition converges; iterative denoising converges | PASS |
| S4 | BMD accuracy within 2% achievable for calibrated phantoms | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec (S1 Ideal)

```yaml
principle_ref: sha256:<p37_hash>

omega:
  grid: [512, 256]
  energies_kVp: [70, 140]
  anatomy: lumbar_spine

E:
  forward: "y_E = I0_E * exp(-(mu_b_E*t_b + mu_s_E*t_s)) + n"
  task: "bone mineral density quantification from dual-energy projections"

I:
  dataset: DEXA_Spine_Phantom
  scans: 50
  noise: {type: poisson, I0_lo: 1e4, I0_hi: 2e4}
  scenario: ideal
  mismatch: null

O: [BMD_error_pct, PSNR_bone, precision_pct]

epsilon:
  BMD_error_max_pct: 2.0
  PSNR_bone_min: 28.0
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known spectra + calibration | None | BMD error <= 2% |
| S2 Mismatch | Nominal spectra | d_bh=5%, d_st=3% | BMD error <= 5% |
| S3 Oracle | True spectra | Known | BMD error <= 3% |
| S4 Blind Cal | Estimate from phantom region | Linear regression | Recovery >= 85% |

### Layer 2 Reward

```
spec.md reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark YAML

```yaml
spec_ref: sha256:<spec37_hash>
principle_ref: sha256:<p37_hash>

dataset:
  name: DEXA_Spine_Phantom
  scans: 50
  resolution: [512, 256]
  data_hash: sha256:<dataset_hash>

baselines:
  - solver: Analytic_Decomp
    results: {mean_BMD_error_pct: 1.8, mean_PSNR_bone: 28.5}
  - solver: Iterative_ML
    results: {mean_BMD_error_pct: 1.2, mean_PSNR_bone: 31.0}
  - solver: DL_DEXA
    results: {mean_BMD_error_pct: 0.8, mean_PSNR_bone: 34.2}

quality_scoring:
  metric: mean_BMD_error_pct
  thresholds:
    - {max: 0.5, Q: 1.00}
    - {max: 1.0, Q: 0.90}
    - {max: 2.0, Q: 0.80}
    - {max: 3.0, Q: 0.75}
```

### Layer 3 Reward

```
Benchmark reward = 100 x phi(t) x 0.60 = 60 PWM
```

---

## Layer 4: Benchmark -> Solution

### Solver Table

| Solver | BMD Error (%) | PSNR Bone | GPU Time | Q | Reward |
|--------|---------------|-----------|----------|---|--------|
| Analytic Decomp | 1.8 | 28.5 | <1 s | 0.80 | 160 PWM |
| Iterative ML | 1.2 | 31.0 | ~5 s | 0.88 | 176 PWM |
| DL-DEXA | 0.8 | 34.2 | ~0.3 s | 0.93 | 186 PWM |
| Physics-DL | 0.4 | 36+ | ~0.5 s | 1.00 | 200 PWM |

### Reward Calculation

```
R = 100 x 1.0 x 2 x 1.0 x q = 200 x q PWM
```

### Certificate Snippet

```json
{
  "principle": "sha256:<p37_hash>",
  "spec": "sha256:<spec37_hash>",
  "benchmark": "sha256:<bench37_hash>",
  "r": {"residual_norm": 0.009, "error_bound": 0.022, "ratio": 0.41},
  "c": {"fitted_rate": 1.96, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.88,
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
pwm-node benchmarks | grep dexa
pwm-node verify dexa/spine_s1_ideal.yaml
pwm-node mine dexa/spine_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
