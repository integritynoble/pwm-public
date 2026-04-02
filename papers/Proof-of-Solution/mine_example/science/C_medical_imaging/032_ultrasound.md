# Principle #32 — Ultrasound B-mode

**Domain:** Medical Imaging | **Carrier:** Acoustic | **Difficulty:** Standard (delta=3)
**DAG:** [G.pulse.acoustic] --> [K.green.acoustic] --> [∫.temporal]
**Modality:** B-mode pulse-echo ultrasound

---

## Four-Layer Pipeline

```
L1 seeds->Principle   L2 Principle->spec   L3 spec->Benchmark   L4 Bench->Solution
 domain expert          task designer        data engineer         solver/miner
 wave equation +        specific US          RF/IQ data +          beamform/recon
 beamforming model      recon tasks          baselines             + earn PWM
 200x phi PWM           150x phi x0.70       100x phi x0.60       Rbase x phi x d x q
```

---

## Layer 1: Seeds -> Principle

### Forward Model

```
y(t, ch) = sum_scatterers sigma_k * h(t - 2*r_k/c, ch) + n

  G.pulse.acoustic --> K.green.acoustic --> ∫.temporal
```

### DAG Primitives

| Node | Primitive | Operation |
|------|-----------|-----------|
| G.pulse.acoustic | Generate | Acoustic pulse excitation |
| K.green.acoustic | Kernel | Acoustic Green’s function propagation |
| ∫.temporal | Integrate | Temporal integration / accumulation |

### Well-Posedness

- Existence: YES -- reflectivity map generates echo signals
- Uniqueness: CONDITIONAL -- speckle is stochastic; DAS beamforming is well-posed
- Stability: kappa ~ 15 (standard), kappa ~ 60 (plane-wave compounding)
- Mismatch: speed-of-sound error (dc), element failure (n_dead), apodization error (da)

### Error Method

- Primary: CNR (contrast-to-noise ratio), lateral resolution (mm)
- Secondary: PSNR, SSIM (for simulation), gCNR
- Convergence rate: q = 1.5 (DAS), q = 2.0 (adaptive beamforming)

### S1-S4 Gate Checks

| Gate | Check | Result |
|------|-------|--------|
| S1 | RF data dimensions [N_samples x N_channels x N_tx] consistent | PASS |
| S2 | Speed-of-sound within physiological range; aperture sufficient | PASS |
| S3 | DAS beamformer converges; MV beamformer converges at O(1/k) | PASS |
| S4 | CNR >= 1.5 achievable for standard cyst phantoms | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec (S1 Ideal)

```yaml
principle_ref: sha256:<p32_hash>

omega:
  grid: [512, 384]
  transducer: linear_128elem
  center_freq_MHz: 5.0
  sampling_freq_MHz: 40.0
  speed_of_sound: 1540

E:
  forward: "y(t,ch) = sum sigma_k * h(t - 2r_k/c, ch) + n"
  task: "plane-wave compounding beamforming"
  n_plane_waves: 75

I:
  dataset: PICMUS_simulation
  phantoms: 8
  noise: {type: gaussian, SNR_dB: 40}
  scenario: ideal
  mismatch: null

O: [CNR, lateral_resolution_mm, FWHM_mm]

epsilon:
  CNR_min: 1.8
  lateral_res_max_mm: 0.5
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known c=1540 m/s | None | CNR >= 1.8 |
| S2 Mismatch | c_assumed=1540 | dc=+20 m/s, 3 dead elem. | CNR >= 1.2 |
| S3 Oracle | c_true known | Known | CNR >= 1.5 |
| S4 Blind Cal | Estimate c from data | Autofocus | Recovery >= 85% |

### Layer 2 Reward

```
spec.md reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark YAML

```yaml
spec_ref: sha256:<spec32_hash>
principle_ref: sha256:<p32_hash>

dataset:
  name: PICMUS_simulation
  phantoms: 8
  rf_channels: 128
  n_plane_waves: 75
  data_hash: sha256:<dataset_hash>

baselines:
  - solver: DAS
    results: {mean_CNR: 1.85, lateral_res_mm: 0.48}
  - solver: MV_beamformer
    results: {mean_CNR: 2.45, lateral_res_mm: 0.32}
  - solver: iMAP
    results: {mean_CNR: 2.8, lateral_res_mm: 0.28}

quality_scoring:
  metric: mean_CNR
  thresholds:
    - {min: 3.0, Q: 1.00}
    - {min: 2.5, Q: 0.90}
    - {min: 2.0, Q: 0.80}
    - {min: 1.8, Q: 0.75}
```

### Layer 3 Reward

```
Benchmark reward = 100 x phi(t) x 0.60 = 60 PWM
```

---

## Layer 4: Benchmark -> Solution

### Solver Table

| Solver | CNR | Lat. Res. (mm) | GPU Time | Q | Reward |
|--------|-----|----------------|----------|---|--------|
| DAS | 1.85 | 0.48 | ~0.1 s | 0.75 | 225 PWM |
| MV Beamformer | 2.45 | 0.32 | ~2 s | 0.88 | 264 PWM |
| iMAP | 2.8 | 0.28 | ~5 s | 0.93 | 279 PWM |
| Deep Beamformer | 3.2+ | 0.25 | ~0.5 s | 1.00 | 300 PWM |

### Reward Calculation

```
R = 100 x 1.0 x 3 x 1.0 x q = 300 x q PWM
```

### Certificate Snippet

```json
{
  "principle": "sha256:<p32_hash>",
  "spec": "sha256:<spec32_hash>",
  "benchmark": "sha256:<bench32_hash>",
  "r": {"residual_norm": 0.032, "error_bound": 0.06, "ratio": 0.53},
  "c": {"fitted_rate": 1.48, "theoretical_rate": 1.5, "K": 3},
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
L4       300 x q PWM per solve  Miner keeps 100%
```

---

## Quick-Start Commands

```bash
pwm-node benchmarks | grep ultrasound
pwm-node verify ultrasound/picmus_s1_ideal.yaml
pwm-node mine ultrasound/picmus_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
