# Principle #101 — Sonar Imaging

**Domain:** Remote Sensing | **Carrier:** Acoustic | **Difficulty:** Standard (δ=3)
**DAG:** G.pulse.acoustic --> K.green.acoustic --> integral.temporal | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │        G.pulse.acoustic-->K.green.acoustic-->integral.temporal    Sonar-img  SAS-Seabed          Beamform
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SONAR   P = (E, G, W, C)   Principle #101                     │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(t,m) = Σ_k σ_k·s(t − 2r_k/c_w)·a(θ_k, m) + n     │
│        │ Acoustic pulse → target reflection → array reception   │
│        │ c_w = sound speed in water (~1500 m/s)                 │
│        │ Inverse: recover seabed reflectivity from echo data    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse.acoustic] --> [K.green.acoustic] --> [integral.temporal]│
│        │ AcousticPulse  AcousticProp  BeamForm                   │
│        │ V={G.pulse.acoustic, K.green.acoustic, integral.temporal}  A={G.pulse.acoustic-->K.green.acoustic, K.green.acoustic-->integral.temporal}   L_DAG=3.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (beamforming is well-defined)           │
│        │ Uniqueness: YES within Rayleigh resolution              │
│        │ Stability: κ ≈ 8 (high SNR), κ ≈ 60 (reverberant)     │
│        │ Mismatch: sound-speed profile error, platform motion    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = PSNR (primary), detection rate (secondary)         │
│        │ q = 2.0 (DAS/MVDR beamformer convergence)             │
│        │ T = {residual_norm, sidelobe_level, K_resolutions}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Array geometry and pulse bandwidth match resolution target | PASS |
| S2 | Beamformer well-conditioned for stated array aperture | PASS |
| S3 | DAS/MVDR beamforming converges for given SNR | PASS |
| S4 | PSNR ≥ 24 dB achievable for side-scan/SAS imagery | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# sonar/sas_s1_ideal.yaml
principle_ref: sha256:<p101_hash>
omega:
  grid: [1024, 2048]
  pixel_m: 0.1
  frequency_kHz: 100
  bandwidth_kHz: 30
E:
  forward: "y = beamform(Σ σ_k·s(t-2r_k/c) · a(θ,m)) + n"
I:
  dataset: SAS_Seabed
  scenes: 30
  noise: {type: gaussian, SNR_dB: 20}
  scenario: ideal
O: [PSNR, SSIM]
epsilon:
  PSNR_min: 24.0
  SSIM_min: 0.72
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 30 kHz bandwidth → 2.5 cm range resolution; pixel 10 cm OK | PASS |
| S2 | κ ≈ 8 at SNR 20 dB | PASS |
| S3 | SAS focusing converges for stated geometry | PASS |
| S4 | PSNR ≥ 24 dB feasible at SNR 20 dB | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# sonar/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec101_hash>
principle_ref: sha256:<p101_hash>
dataset:
  name: SAS_Seabed
  scenes: 30
  size: [1024, 2048]
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: DAS-Beamform
    params: {apodization: hanning}
    results: {PSNR: 24.8, SSIM: 0.741}
  - solver: MVDR
    params: {diagonal_loading: 0.01}
    results: {PSNR: 27.2, SSIM: 0.812}
  - solver: SonarNet
    params: {pretrained: seabed}
    results: {PSNR: 30.1, SSIM: 0.891}
quality_scoring:
  - {min: 31.0, Q: 1.00}
  - {min: 28.0, Q: 0.90}
  - {min: 25.0, Q: 0.80}
  - {min: 23.0, Q: 0.75}
```

**Baseline:** DAS — PSNR 24.8 dB | **Layer 3 reward:** 60 PWM + upstream

---

## Layer 4 — Benchmark → Solution

| Solver | PSNR (dB) | SSIM | Runtime | Q |
|--------|-----------|------|---------|---|
| DAS | 24.8 | 0.741 | 2 s | 0.80 |
| MVDR | 27.2 | 0.812 | 10 s | 0.88 |
| SonarNet | 30.1 | 0.891 | 3 s | 0.95 |
| AcousticFormer | 31.5 | 0.918 | 5 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q
Best: 300 × 1.00 = 300 PWM | Floor: 300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p101_hash>",
  "h_s": "sha256:<spec101_hash>",
  "h_b": "sha256:<bench101_hash>",
  "r": {"residual_norm": 0.011, "error_bound": 0.028, "ratio": 0.39},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.95,
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"}
}
```

---

## Reward Summary

| Layer | Seed Reward | Ongoing Royalties |
|-------|-------------|-------------------|
| L1 Principle | 200 PWM | 5% of L4 mints |
| L2 spec.md | 105 PWM | 10% of L4 mints |
| L3 Benchmark | 60 PWM | 15% of L4 mints |
| L4 Solution | — | 225–300 PWM per solve |

## Quick-Start

```bash
pwm-node benchmarks | grep sonar
pwm-node verify sonar/sas_s1_ideal.yaml
pwm-node mine sonar/sas_s1_ideal.yaml
```
