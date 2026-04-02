# Principle #62 — Contrast-Enhanced Ultrasound

**Domain:** Medical Imaging | **Carrier:** Acoustic | **Difficulty:** Standard (delta=3)
**DAG:** [G.pulse.acoustic] --> [K.green.acoustic] --> [N.pointwise] --> [∫.temporal]
**Modality:** Contrast-enhanced ultrasound (microbubble imaging)

---

## Four-Layer Pipeline

```
L1 seeds->Principle   L2 Principle->spec   L3 spec->Benchmark   L4 Bench->Solution
 domain expert          task designer        data engineer         solver/miner
 nonlinear bubble +     specific CEUS        cine loops +          perfusion quantify
 harmonic model         tasks                baselines             + earn PWM
 200x phi PWM           150x phi x0.70       100x phi x0.60       Rbase x phi x d x q
```

---

## Layer 1: Seeds -> Principle

### Forward Model

```
y_tissue(t) = linear_backscatter(f0)
y_bubble(t) = nonlinear_backscatter(f0, 2*f0, ...) via Rayleigh-Plesset
y_CEUS = y_bubble(2*f0) - y_tissue(2*f0)   (harmonic separation)

  G.pulse.acoustic --> K.green.acoustic --> N.pointwise --> ∫.temporal
```

### DAG Primitives

| Node | Primitive | Operation |
|------|-----------|-----------|
| G.pulse.acoustic | Generate | Acoustic pulse excitation |
| K.green.acoustic | Kernel | Acoustic Green’s function propagation |
| N.pointwise | Nonlinear | Pointwise nonlinear response |
| ∫.temporal | Integrate | Temporal integration / accumulation |

### Well-Posedness

- Existence: YES -- harmonic signal separates bubbles from tissue
- Uniqueness: CONDITIONAL -- perfusion model requires kinetic fitting
- Stability: kappa ~ 15 (high-MI), kappa ~ 40 (low-MI / deep tissue)
- Mismatch: bubble destruction (d_destroy), motion artifact (d_motion), attenuation (d_atten)

### Error Method

- Primary: perfusion parameter RMSE (%), peak enhancement error (%)
- Secondary: wash-in/wash-out time accuracy, CNR
- Convergence rate: q = 2.0 (harmonic imaging), q = 1.0 (kinetic fitting)

### S1-S4 Gate Checks

| Gate | Check | Result |
|------|-------|--------|
| S1 | Pulse sequence and harmonic detection consistent | PASS |
| S2 | Bubble concentration sufficient for harmonic detection | PASS |
| S3 | Time-intensity curve fitting converges | PASS |
| S4 | Perfusion parameter error <= 15% for liver phantom | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
```

---

## Layer 2: Principle -> spec.md

### Example spec (S1 Ideal)

```yaml
principle_ref: sha256:<p62_hash>

omega:
  grid: [256, 192]
  frame_rate: 10
  n_frames: 120
  anatomy: liver

E:
  forward: "y_CEUS = bubble_harmonic + n"
  task: "perfusion parameter quantification from CEUS cine"

I:
  dataset: CEUS_Liver_Sim
  cases: 25
  noise: {type: gaussian, SNR_dB: 25}
  scenario: ideal
  mismatch: null

O: [perfusion_RMSE_pct, peak_enhance_error_pct]

epsilon:
  perfusion_RMSE_max_pct: 15.0
  peak_enhance_error_max_pct: 10.0
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | No bubble destruction | None | perfusion RMSE <= 15% |
| S2 Mismatch | Bubble destruction | d_destroy=10%, d_motion | RMSE <= 25% |
| S3 Oracle | True destruction model | Known | RMSE <= 18% |
| S4 Blind Cal | Estimate destruction rate | Exponential fitting | Recovery >= 85% |

### Layer 2 Reward

```
spec.md reward = 150 x phi(t) x 0.70 = 105 PWM
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark YAML

```yaml
spec_ref: sha256:<spec62_hash>
principle_ref: sha256:<p62_hash>

dataset:
  name: CEUS_Liver_Sim
  cases: 25
  frames: 120
  resolution: [256, 192]
  data_hash: sha256:<dataset_hash>

baselines:
  - solver: Lognormal_Fit
    results: {mean_perfusion_RMSE_pct: 12.5, peak_error_pct: 8.5}
  - solver: Deconvolution
    results: {mean_perfusion_RMSE_pct: 9.8, peak_error_pct: 6.2}
  - solver: DL_CEUS
    results: {mean_perfusion_RMSE_pct: 5.5, peak_error_pct: 3.5}

quality_scoring:
  metric: mean_perfusion_RMSE_pct
  thresholds:
    - {max: 4.0, Q: 1.00}
    - {max: 7.0, Q: 0.90}
    - {max: 12.0, Q: 0.80}
    - {max: 18.0, Q: 0.75}
```

### Layer 3 Reward

```
Benchmark reward = 100 x phi(t) x 0.60 = 60 PWM
```

---

## Layer 4: Benchmark -> Solution

### Solver Table

| Solver | Perf. RMSE (%) | Peak Err (%) | GPU Time | Q | Reward |
|--------|----------------|--------------|----------|---|--------|
| Lognormal Fit | 12.5 | 8.5 | ~2 s | 0.80 | 240 PWM |
| Deconvolution | 9.8 | 6.2 | ~5 s | 0.85 | 255 PWM |
| DL-CEUS | 5.5 | 3.5 | ~1 s | 0.93 | 279 PWM |
| PerfusionNet | 3.5 | 2.0 | ~2 s | 1.00 | 300 PWM |

### Reward Calculation

```
R = 100 x 1.0 x 3 x 1.0 x q = 300 x q PWM
```

### Certificate Snippet

```json
{
  "principle": "sha256:<p62_hash>",
  "spec": "sha256:<spec62_hash>",
  "benchmark": "sha256:<bench62_hash>",
  "r": {"residual_norm": 0.030, "error_bound": 0.058, "ratio": 0.52},
  "c": {"fitted_rate": 1.85, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep ceus
pwm-node verify ceus/liver_s1_ideal.yaml
pwm-node mine ceus/liver_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
