# Principle #394 — Spectral Estimation (Periodogram/MUSIC): Four-Layer Walkthrough

**Principle #394: Spectral Estimation (Periodogram/MUSIC)**
Domain: Signal & Image Processing | Carrier: data | Difficulty: textbook (delta=1) | Reward: 1x base

---

## Four-Layer Pipeline

```
LAYER 1              LAYER 2              LAYER 3              LAYER 4
seeds -> Useful(B)   Principle + S1-S4    spec.md + Principle   spec.md + Benchmark
designs the          designs              + S1-S4 designs &     + Principle + S1-S4
PRINCIPLE            spec.md (PoInf)      verifies BENCHMARK    verifies SOLUTION

[Seed] --> [Principle] --> [spec.md] --> [Benchmark] --> [Solution]
  L1          L1              L2             L3             L4
```

---

## Layer 1: Seeds -> Principle

### Governing Equation

```
x(t) = Σ_k A_k e^{j2πf_k t} + n(t)     (sinusoidal signal model)
Periodogram: P̂(f) = (1/N)|Σ x(t)e^{-j2πft}|²
Welch: average periodograms of overlapping segments
MUSIC: P(f) = 1 / [e^H(f) E_n E_n^H e(f)]  (subspace method)
```

### DAG Decomposition G = (V, A)

```
[F.dft] -> [∫.temporal] -> [O.l2]

V = {F.dft, ∫.temporal, O.l2}
A = {F.dft->∫.temporal, ∫.temporal->O.l2}
L_DAG = 2.0   Tier: textbook (delta = 1)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- DFT always computable from finite samples |
| Uniqueness | YES -- MUSIC resolves K frequencies for K < N |
| Stability | CONDITIONAL -- resolution limited by N and SNR |

Mismatch parameters: number of sinusoids K, window function, segment length, noise floor

### Error-Bounding Method

```
e  = frequency RMSE [Hz] (primary), amplitude error (secondary)
q = 0.5 (CRB scaling with N)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Sampling rate > 2 f_max (Nyquist); frequency units [Hz] consistent | PASS |
| S2 | MUSIC subspace well-posed for K < N | PASS |
| S3 | Periodogram/Welch computable; MUSIC converges | PASS |
| S4 | Frequency RMSE < 0.01/N achievable for SNR > 10 dB | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

```yaml
principle_ref: sha256:<principle_394_hash>

omega:
  description: "Spectral estimation, K=3 sinusoids, N=256 samples, SNR=15dB"
  N_samples: 256
  K_sinusoids: 3
  outputs: [frequencies, amplitudes, power_spectrum]

E:
  forward: "x(t) = Σ A_k exp(j2πf_k t) + n(t)"
  dag: "[F.dft] -> [∫.temporal] -> [O.l2]"

B:
  constraints: "f_k < f_s/2; K < N; noise stationary"

I:
  scenario: ideal
  parameters: {SNR_dB: 15, frequencies_Hz: [0.1, 0.25, 0.35]}
  mismatch: null

O: [freq_RMSE, amplitude_error]

epsilon:
  freq_RMSE_max: 0.001

difficulty:
  L_DAG: 2.0
  tier: textbook
  delta: 1
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known K, white noise | None | freq_RMSE < 0.001 |
| S2 Mismatch | Colored noise or wrong K | Applied | relaxed 1.5x |
| S3 Oracle | True frequencies known | Known | freq_RMSE < 0.001 |
| S4 Blind Cal | Unknown K and noise color | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
```

---

## Layer 3: spec.md -> Benchmark

```yaml
spec_ref: sha256:<spec_394_hash>
principle_ref: sha256:<principle_394_hash>

dataset:
  description: "Sinusoidal signals at multiple SNR levels"
  SNR_dB: [0, 5, 10, 15, 20]
  n_trials: 500
  data_hash: sha256:<dataset_394_hash>

baselines:
  - solver: MUSIC              freq_RMSE: 0.0003    q: 0.95
  - solver: ESPRIT             freq_RMSE: 0.0004    q: 0.92
  - solver: Welch              freq_RMSE: 0.003     q: 0.78

quality_scoring:
  metric: freq_RMSE
  thresholds:
    - {max: 0.0001, Q: 1.00}
    - {max: 0.0005, Q: 0.90}
    - {max: 0.001, Q: 0.80}
    - {max: 0.005, Q: 0.75}
```

### Baselines

| Solver | freq_RMSE | Q | Approx Reward |
|--------|----------|---|---------------|
| MUSIC | 0.0003 | 0.95 | ~95 PWM |
| ESPRIT | 0.0004 | 0.92 | ~92 PWM |
| Welch | 0.003 | 0.78 | ~78 PWM |

### Layer 3 Reward

```
Benchmark seed reward = 100 x phi(t) x 0.60 = 60 PWM (builder)
```

---

## Layer 4: Benchmark -> Solution (PoSol Mining)

### Reward Calculation

```
R = R_base x phi(t) x delta x nu_c x q
  = 100 x 1.0 x 1 x 1.0 x q
  = 100 x q  PWM

Best case:  100 x 0.95 = 95 PWM
Worst case: 100 x 0.75 = 75 PWM
```

### S4 Certificate

```json
{
  "principle": "#394 Spectral Estimation (Periodogram/MUSIC)",
  "h_p": "sha256:<principle_394_hash>",
  "h_s": "sha256:<spec_394_hash>",
  "h_b": "sha256:<bench_394_hash>",
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"},
  "Q": 0.95,
  "difficulty": {"tier":"textbook","delta":1}
}
```

---

## Reward Summary

```
L1 Principle:  200 PWM seed + upstream royalties from L2/L3/L4
L2 spec.md:    105 PWM seed (x4 scenarios = 420 PWM) + upstream from L3/L4
L3 Benchmark:   60 PWM seed (x4 benchmarks = 240 PWM) + upstream from L4
L4 Solution:   75-95 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep spectral_estimation
pwm-node verify AD_signal_processing/spectral_estimation_s1_ideal.yaml
pwm-node mine AD_signal_processing/spectral_estimation_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
