# Principle #387 — Direction of Arrival Estimation: Four-Layer Walkthrough

**Principle #387: Direction of Arrival Estimation**
Domain: Signal & Image Processing | Carrier: electromagnetic/acoustic | Difficulty: standard (delta=3) | Reward: 3x base

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
x(t) = A(θ) s(t) + n(t)         (array signal model)
A(θ) = [a(θ₁), ..., a(θ_K)]    (steering matrix)
a(θ) = [1, e^{j2πd sin(θ)/λ}, ..., e^{j2π(M-1)d sin(θ)/λ}]ᵀ  (ULA steering vector)
R_xx = A R_ss A^H + σ²I         (covariance model)
MUSIC: P(θ) = 1 / [a^H(θ) E_n E_n^H a(θ)]  (pseudo-spectrum)
```

### DAG Decomposition G = (V, A)

```
[S.array] -> [∫.temporal] -> [E.hermitian]

V = {S.array, ∫.temporal, E.hermitian}
A = {S.array->∫.temporal, ∫.temporal->E.hermitian}
L_DAG = 2.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- array data always exists for physical sources |
| Uniqueness | YES -- MUSIC resolves K < M sources uniquely |
| Stability | CONDITIONAL -- resolution degrades at low SNR or correlated sources |

Mismatch parameters: array calibration errors, mutual coupling, source coherence, number of sources K

### Error-Bounding Method

```
e  = angle RMSE [degrees] (primary), source count accuracy (secondary)
q = 0.5 (CRB scaling with snapshots)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Array element spacing d, wavelength λ, angles [rad] consistent | PASS |
| S2 | MUSIC subspace decomposition well-posed for K < M | PASS |
| S3 | MUSIC/ESPRIT converge with increasing snapshots | PASS |
| S4 | Angle RMSE < 0.5° achievable for SNR > 10 dB, 100 snapshots | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

```yaml
principle_ref: sha256:<principle_387_hash>

omega:
  description: "ULA, M=8 elements, d=λ/2, K=3 sources, 200 snapshots"
  M_elements: 8
  K_sources: 3
  snapshots: 200
  outputs: [estimated_angles, pseudo_spectrum]

E:
  forward: "x(t) = A(θ)s(t) + n(t)"
  dag: "[S.array] -> [∫.temporal] -> [E.hermitian]"

B:
  constraints: "K < M; sources uncorrelated; half-wavelength spacing"

I:
  scenario: ideal
  parameters: {SNR_dB: 15, angles_deg: [-20, 5, 30]}
  mismatch: null

O: [angle_RMSE_deg, source_count_accuracy]

epsilon:
  RMSE_max_deg: 0.5
  convergence_order: 0.5

difficulty:
  L_DAG: 3.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known array + uncorrelated sources | None | RMSE < 0.5° |
| S2 Mismatch | Array calibration error or mutual coupling | Applied | relaxed 1.5x |
| S3 Oracle | True DOAs known | Known | RMSE < 0.5° |
| S4 Blind Cal | Unknown K and array errors | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

```yaml
spec_ref: sha256:<spec_387_hash>
principle_ref: sha256:<principle_387_hash>

dataset:
  description: "Simulated ULA data at multiple SNR levels"
  SNR_dB: [0, 5, 10, 15, 20]
  n_trials: 500
  data_hash: sha256:<dataset_387_hash>

baselines:
  - solver: MUSIC              RMSE_deg: 0.3    q: 0.95
  - solver: ESPRIT             RMSE_deg: 0.35   q: 0.92
  - solver: Beamformer         RMSE_deg: 2.0    q: 0.78

quality_scoring:
  metric: angle_RMSE_deg
  thresholds:
    - {max: 0.1, Q: 1.00}
    - {max: 0.3, Q: 0.90}
    - {max: 0.5, Q: 0.80}
    - {max: 1.0, Q: 0.75}
```

### Baselines

| Solver | RMSE_deg | Q | Approx Reward |
|--------|---------|---|---------------|
| MUSIC | 0.3 | 0.95 | ~285 PWM |
| ESPRIT | 0.35 | 0.92 | ~276 PWM |
| Beamformer | 2.0 | 0.78 | ~234 PWM |

### Layer 3 Reward

```
Benchmark seed reward = 100 x phi(t) x 0.60 = 60 PWM (builder)
```

---

## Layer 4: Benchmark -> Solution (PoSol Mining)

### Solver Table

| Solver | RMSE (deg) | Runtime | Q | Reward |
|--------|-----------|---------|---|--------|
| MUSIC | 0.3 | 0.1 s | 0.95 | ~285 PWM |
| ESPRIT | 0.35 | 0.05 s | 0.92 | ~276 PWM |
| Beamformer | 2.0 | 0.01 s | 0.78 | ~234 PWM |

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
  "principle": "#387 Direction of Arrival Estimation",
  "h_p": "sha256:<principle_387_hash>",
  "h_s": "sha256:<spec_387_hash>",
  "h_b": "sha256:<bench_387_hash>",
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
pwm-node benchmarks | grep doa_estimation
pwm-node verify AD_signal_processing/doa_estimation_s1_ideal.yaml
pwm-node mine AD_signal_processing/doa_estimation_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
