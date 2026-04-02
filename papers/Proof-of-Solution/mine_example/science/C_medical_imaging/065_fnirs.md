# Principle #65 — fNIRS

**Domain:** Medical Imaging | **Carrier:** Photon | **Difficulty:** Standard (delta=3)
**DAG:** [G.broadband] --> [K.scatter.diffuse] --> [S.boundary]
**Modality:** Functional near-infrared spectroscopy

---

## Four-Layer Pipeline

```
L1 seeds->Principle   L2 Principle->spec   L3 spec->Benchmark   L4 Bench->Solution
 domain expert          task designer        data engineer         solver/miner
 modified Beer-Lambert  specific fNIRS       time-series data +    estimate HbO/HbR
 + chromophore model    quantification       baselines             + earn PWM
 200x phi PWM           150x phi x0.70       100x phi x0.60       Rbase x phi x d x q
```

---

## Layer 1: Seeds -> Principle

### Forward Model

```
Delta_OD(lambda, t) = -ln(I(t)/I0) = DPF(lambda) * (epsilon_HbO*Delta_c_HbO + epsilon_HbR*Delta_c_HbR) * d + n

  G.broadband --> K.scatter.diffuse --> S.boundary
```

### DAG Primitives

| Node | Primitive | Operation |
|------|-----------|-----------|
| G.broadband | Generate | Broadband source illumination |
| K.scatter.diffuse | Kernel | Diffuse scattering propagation |
| S.boundary | Sample | Boundary measurement |

### Well-Posedness

- Existence: YES -- optical density change measurable
- Uniqueness: YES -- two wavelengths determine two unknowns (HbO, HbR)
- Stability: kappa ~ 15 (good contact, short separation), kappa ~ 50 (long separation)
- Mismatch: DPF error (d_DPF), motion artifact (d_motion), scalp hemodynamics (d_scalp)

### Error Method

- Primary: HbO/HbR concentration error (uM), correlation with ground truth
- Secondary: temporal SNR, activation detection AUC
- Convergence rate: q = 2.0 (modified Beer-Lambert, analytic)

### S1-S4 Gate Checks

| Gate | Check | Result |
|------|-------|--------|
| S1 | Wavelengths and source-detector separations consistent | PASS |
| S2 | Two wavelengths sufficient for HbO/HbR separation | PASS |
| S3 | MBLL fitting converges; GLM converges | PASS |
| S4 | HbO error <= 1 uM for finger tapping task | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec (S1 Ideal)

```yaml
principle_ref: sha256:<p65_hash>

omega:
  n_channels: 36
  wavelengths_nm: [760, 850]
  sampling_rate_Hz: 10
  source_detector_mm: 30

E:
  forward: "Delta_OD = DPF*(eps_HbO*Dc_HbO + eps_HbR*Dc_HbR)*d + n"
  task: "HbO/HbR concentration change estimation"

I:
  dataset: fNIRS_Motor_Sim
  subjects: 25
  noise: {type: gaussian, SNR_dB: 20}
  scenario: ideal
  mismatch: null

O: [HbO_error_uM, HbR_error_uM, activation_AUC]

epsilon:
  HbO_error_max_uM: 1.0
  activation_AUC_min: 0.80
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known DPF + no motion | None | HbO error <= 1 uM |
| S2 Mismatch | Nominal DPF | d_DPF=15%, d_motion | HbO error <= 2 uM |
| S3 Oracle | True DPF | Known | HbO error <= 1.5 uM |
| S4 Blind Cal | Estimate DPF from data | Optimization | Recovery >= 85% |

### Layer 2 Reward

```
spec.md reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark YAML

```yaml
spec_ref: sha256:<spec65_hash>
principle_ref: sha256:<p65_hash>

dataset:
  name: fNIRS_Motor_Sim
  subjects: 25
  channels: 36
  data_hash: sha256:<dataset_hash>

baselines:
  - solver: MBLL_Standard
    results: {mean_HbO_error_uM: 0.85, activation_AUC: 0.82}
  - solver: GLM_fNIRS
    results: {mean_HbO_error_uM: 0.65, activation_AUC: 0.87}
  - solver: DL_fNIRS
    results: {mean_HbO_error_uM: 0.35, activation_AUC: 0.93}

quality_scoring:
  metric: mean_HbO_error_uM
  thresholds:
    - {max: 0.25, Q: 1.00}
    - {max: 0.50, Q: 0.90}
    - {max: 0.85, Q: 0.80}
    - {max: 1.20, Q: 0.75}
```

### Layer 3 Reward

```
Benchmark reward = 100 x phi(t) x 0.60 = 60 PWM
```

---

## Layer 4: Benchmark -> Solution

### Solver Table

| Solver | HbO Error (uM) | AUC | GPU Time | Q | Reward |
|--------|----------------|-----|----------|---|--------|
| MBLL Standard | 0.85 | 0.82 | <1 s | 0.80 | 240 PWM |
| GLM-fNIRS | 0.65 | 0.87 | ~2 s | 0.85 | 255 PWM |
| DL-fNIRS | 0.35 | 0.93 | ~1 s | 0.93 | 279 PWM |
| fNIRS-Transformer | 0.20 | 0.96 | ~2 s | 1.00 | 300 PWM |

### Reward Calculation

```
R = 100 x 1.0 x 3 x 1.0 x q = 300 x q PWM
```

### Certificate Snippet

```json
{
  "principle": "sha256:<p65_hash>",
  "spec": "sha256:<spec65_hash>",
  "benchmark": "sha256:<bench65_hash>",
  "r": {"residual_norm": 0.020, "error_bound": 0.042, "ratio": 0.48},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
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
L4       300 x q PWM per solve  Miner keeps 100%
```

---

## Quick-Start Commands

```bash
pwm-node benchmarks | grep fnirs
pwm-node verify fnirs/motor_s1_ideal.yaml
pwm-node mine fnirs/motor_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
