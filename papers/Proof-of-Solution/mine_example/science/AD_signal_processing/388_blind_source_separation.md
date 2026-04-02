# Principle #388 — Blind Source Separation (ICA/NMF): Four-Layer Walkthrough

**Principle #388: Blind Source Separation (ICA/NMF)**
Domain: Signal & Image Processing | Carrier: data | Difficulty: standard (delta=3) | Reward: 3x base

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
x(t) = A s(t)           (instantaneous linear mixture)
ICA: maximize non-Gaussianity of ŝ = W x  (W ≈ A⁻¹)
NMF: X ≈ W H,  W ≥ 0, H ≥ 0  (non-negative factorization)
Mutual information: min I(ŝ₁; ŝ₂; ...; ŝ_K)
```

### DAG Decomposition G = (V, A)

```
[L.dense] -> [E.hermitian] -> [O.l2]

V = {L.dense, E.hermitian, O.l2}
A = {L.dense->E.hermitian, E.hermitian->O.l2}
L_DAG = 2.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- mixed signals always exist |
| Uniqueness | CONDITIONAL -- unique up to permutation and scaling (ICA); up to rotation (NMF) |
| Stability | CONDITIONAL -- requires sufficient non-Gaussianity or non-negativity |

Mismatch parameters: number of sources, mixing model (instantaneous vs convolutive), noise level

### Error-Bounding Method

```
e  = SIR (signal-to-interference ratio, dB) (primary), SDR (secondary)
q = 0.5 (convergence rate of FastICA)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Number of mixtures ≥ number of sources; dimensions consistent | PASS |
| S2 | Sources non-Gaussian (ICA) or non-negative (NMF); mixing full rank | PASS |
| S3 | FastICA/InfoMax converge; SIR improves with iterations | PASS |
| S4 | SIR >= 15 dB achievable for well-separated sources | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

```yaml
principle_ref: sha256:<principle_388_hash>

omega:
  description: "Audio BSS, K=3 sources, M=3 microphones, 10s @ 16kHz"
  K_sources: 3
  M_sensors: 3
  sample_rate: 16000
  outputs: [separated_sources, mixing_matrix]

E:
  forward: "x(t) = A s(t)"
  dag: "[L.dense] -> [E.hermitian] -> [O.l2]"

B:
  constraints: "A full rank; sources statistically independent"

I:
  scenario: ideal
  parameters: {mixing: random_orthogonal, noise: none}
  mismatch: null

O: [SIR_dB, SDR_dB]

epsilon:
  SIR_min_dB: 15.0
  convergence_order: 0.5

difficulty:
  L_DAG: 2.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Instantaneous mixing, no noise | None | SIR >= 15 dB |
| S2 Mismatch | Convolutive mixing or additive noise | Applied | relaxed 1.5x |
| S3 Oracle | True mixing matrix known | Known | SIR >= 15 dB |
| S4 Blind Cal | Unknown K and A | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

```yaml
spec_ref: sha256:<spec_388_hash>
principle_ref: sha256:<principle_388_hash>

dataset:
  description: "Audio and EEG BSS benchmarks"
  n_trials: 50
  data_hash: sha256:<dataset_388_hash>

baselines:
  - solver: FastICA            SIR_dB: 20.0    q: 0.95
  - solver: InfoMax            SIR_dB: 18.0    q: 0.90
  - solver: NMF-KL             SIR_dB: 12.0    q: 0.78

quality_scoring:
  metric: SIR_dB
  thresholds:
    - {min: 22.0, Q: 1.00}
    - {min: 18.0, Q: 0.90}
    - {min: 15.0, Q: 0.80}
    - {min: 12.0, Q: 0.75}
```

### Baselines

| Solver | SIR_dB | Q | Approx Reward |
|--------|--------|---|---------------|
| FastICA | 20.0 | 0.95 | ~285 PWM |
| InfoMax | 18.0 | 0.90 | ~270 PWM |
| NMF-KL | 12.0 | 0.78 | ~234 PWM |

### Layer 3 Reward

```
Benchmark seed reward = 100 x phi(t) x 0.60 = 60 PWM (builder)
```

---

## Layer 4: Benchmark -> Solution (PoSol Mining)

### Solver Table

| Solver | SIR (dB) | Runtime | Q | Reward |
|--------|----------|---------|---|--------|
| FastICA | 20.0 | 0.5 s | 0.95 | ~285 PWM |
| InfoMax | 18.0 | 2 s | 0.90 | ~270 PWM |
| NMF-KL | 12.0 | 5 s | 0.78 | ~234 PWM |

### Reward Calculation

```
R = R_base x phi(t) x delta x nu_c x q
  = 100 x 1.0 x 3 x 1.0 x q
  = 300 x q  PWM

Best case:  300 x 0.95 = 285 PWM
Worst case: 300 x 0.75 = 225 PWM
```

### S4 Certificate

```json
{
  "principle": "#388 Blind Source Separation (ICA/NMF)",
  "h_p": "sha256:<principle_388_hash>",
  "h_s": "sha256:<spec_388_hash>",
  "h_b": "sha256:<bench_388_hash>",
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"},
  "Q": 0.95,
  "difficulty": {"tier":"standard","delta":3}
}
```

---

## Reward Summary

```
L1 Principle:  200 PWM seed + upstream royalties from L2/L3/L4
L2 spec.md:    105 PWM seed (x4 scenarios = 420 PWM) + upstream from L3/L4
L3 Benchmark:   60 PWM seed (x4 benchmarks = 240 PWM) + upstream from L4
L4 Solution:   225-285 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep blind_source_separation
pwm-node verify AD_signal_processing/blind_source_separation_s1_ideal.yaml
pwm-node mine AD_signal_processing/blind_source_separation_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
