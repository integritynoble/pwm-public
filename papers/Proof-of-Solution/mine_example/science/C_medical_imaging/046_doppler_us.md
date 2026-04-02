# Principle #46 — Doppler Ultrasound

**Domain:** Medical Imaging | **Carrier:** Acoustic | **Difficulty:** Standard (delta=3)
**DAG:** [G.pulse.acoustic] --> [K.green.acoustic] --> [F.dft]
**Modality:** Color/pulsed-wave Doppler ultrasound

---

## Four-Layer Pipeline

```
L1 seeds->Principle   L2 Principle->spec   L3 spec->Benchmark   L4 Bench->Solution
 domain expert          task designer        data engineer         solver/miner
 Doppler shift model    specific Doppler     IQ data +             velocity estimate
 + autocorrelation      velocity tasks       baselines             + earn PWM
 200x phi PWM           150x phi x0.70       100x phi x0.60       Rbase x phi x d x q
```

---

## Layer 1: Seeds -> Principle

### Forward Model

```
f_d = 2 * f0 * v * cos(theta) / c
y(slow_time) = A * exp(i*2*pi*f_d*t_slow) * w(t_slow) + clutter + n

  G.pulse.acoustic --> K.green.acoustic --> F.dft
  Doppler shift encodes velocity along beam axis
```

### DAG Primitives

| Node | Primitive | Operation |
|------|-----------|-----------|
| G.pulse.acoustic | Generate | Acoustic pulse excitation |
| K.green.acoustic | Kernel | Acoustic Green’s function propagation |
| F.dft | Fourier | Discrete Fourier transform encoding |

### Well-Posedness

- Existence: YES -- Doppler shift measurable for v > v_min
- Uniqueness: CONDITIONAL -- aliasing for |v| > PRF*c/(4*f0); angle-dependent
- Stability: kappa ~ 10 (high PRF), kappa ~ 35 (low PRF / deep vessel)
- Mismatch: angle error (d_theta), clutter filter error (d_clutter), PRF aliasing (d_prf)

### Error Method

- Primary: velocity RMSE (cm/s), velocity bias (%)
- Secondary: clutter-to-signal ratio, spectral broadening
- Convergence rate: q = 2.0 (autocorrelation), q = 1.5 (spectral estimation)

### S1-S4 Gate Checks

| Gate | Check | Result |
|------|-------|--------|
| S1 | Ensemble size and PRF consistent with velocity range | PASS |
| S2 | Velocity range within Nyquist limit; angle known | PASS |
| S3 | Autocorrelation estimator converges; clutter filter converges | PASS |
| S4 | Velocity RMSE <= 5 cm/s achievable for carotid flow | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec (S1 Ideal)

```yaml
principle_ref: sha256:<p46_hash>

omega:
  ensemble_size: 16
  PRF_kHz: 8.0
  f0_MHz: 5.0
  beam_angle_deg: 60
  max_velocity_cms: 100

E:
  forward: "f_d = 2*f0*v*cos(theta)/c"
  task: "velocity field estimation from Doppler IQ data"

I:
  dataset: Doppler_Carotid_Sim
  sequences: 30
  noise: {type: gaussian, SNR_dB: 30}
  scenario: ideal
  mismatch: null

O: [velocity_RMSE_cms, velocity_bias_pct]

epsilon:
  velocity_RMSE_max: 5.0
  velocity_bias_max_pct: 3.0
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known angle + PRF | None | RMSE <= 5 cm/s |
| S2 Mismatch | Nominal angle | d_theta=5deg, d_clutter | RMSE <= 10 cm/s |
| S3 Oracle | True angle | Known | RMSE <= 7 cm/s |
| S4 Blind Cal | Estimate angle from B-mode | Vessel tracking | Recovery >= 85% |

### Layer 2 Reward

```
spec.md reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark YAML

```yaml
spec_ref: sha256:<spec46_hash>
principle_ref: sha256:<p46_hash>

dataset:
  name: Doppler_Carotid_Sim
  sequences: 30
  ensemble_size: 16
  data_hash: sha256:<dataset_hash>

baselines:
  - solver: Autocorrelation
    results: {mean_RMSE_cms: 4.5, velocity_bias_pct: 2.8}
  - solver: Spectral_Estimator
    results: {mean_RMSE_cms: 3.8, velocity_bias_pct: 2.0}
  - solver: DL_Doppler
    results: {mean_RMSE_cms: 2.1, velocity_bias_pct: 1.2}

quality_scoring:
  metric: mean_RMSE_cms
  thresholds:
    - {max: 1.5, Q: 1.00}
    - {max: 3.0, Q: 0.90}
    - {max: 5.0, Q: 0.80}
    - {max: 8.0, Q: 0.75}
```

### Layer 3 Reward

```
Benchmark reward = 100 x phi(t) x 0.60 = 60 PWM
```

---

## Layer 4: Benchmark -> Solution

### Solver Table

| Solver | RMSE (cm/s) | Bias (%) | GPU Time | Q | Reward |
|--------|-------------|----------|----------|---|--------|
| Autocorrelation | 4.5 | 2.8 | <0.1 s | 0.80 | 240 PWM |
| Spectral Est. | 3.8 | 2.0 | ~1 s | 0.85 | 255 PWM |
| DL-Doppler | 2.1 | 1.2 | ~0.3 s | 0.93 | 279 PWM |
| FlowNet-US | 1.2 | 0.5 | ~0.5 s | 1.00 | 300 PWM |

### Reward Calculation

```
R = 100 x 1.0 x 3 x 1.0 x q = 300 x q PWM
```

### Certificate Snippet

```json
{
  "principle": "sha256:<p46_hash>",
  "spec": "sha256:<spec46_hash>",
  "benchmark": "sha256:<bench46_hash>",
  "r": {"residual_norm": 0.022, "error_bound": 0.045, "ratio": 0.49},
  "c": {"fitted_rate": 1.92, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep doppler_us
pwm-node verify doppler_us/carotid_s1_ideal.yaml
pwm-node mine doppler_us/carotid_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
