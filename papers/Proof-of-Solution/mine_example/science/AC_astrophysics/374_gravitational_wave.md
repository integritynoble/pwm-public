# Principle #374 — Gravitational Wave Signal (Compact Binary): Four-Layer Walkthrough

**Principle #374: Gravitational Wave Signal (Compact Binary)**
Domain: Astrophysics & Cosmology | Carrier: gravitational | Difficulty: hard (delta=5) | Reward: 5x base

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
h(t) = F₊ h₊(t) + F× h×(t)           (detector strain)
h₊(t) = (4Gμ/c²D) (πf)^{2/3} cos(2Φ(t))  (plus polarization, inspiral)
dΦ/dt = πf(t)                           (orbital phase evolution)
df/dt = (96/5)π^{8/3} (Gℳ/c³)^{5/3} f^{11/3}  (chirp rate)
ℳ = (m₁m₂)^{3/5}/(m₁+m₂)^{1/5}       (chirp mass)
```

### DAG Decomposition G = (V, A)

```
[∂.time] -> [N.einstein] -> [K.green] -> [∫.orbital]

V = {∂.time, N.einstein, K.green, ∫.orbital}
A = {∂.time->N.einstein, N.einstein->K.green, K.green->∫.orbital}
L_DAG = 3.0   Tier: hard (delta = 5)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- GR predicts unique waveform for given binary parameters |
| Uniqueness | YES -- chirp mass + mass ratio + spins determine template |
| Stability | CONDITIONAL -- SNR must exceed threshold; template bank covers parameter space |

Mismatch parameters: chirp mass ℳ, mass ratio q, spin χ₁/χ₂, distance D, inclination ι

### Error-Bounding Method

```
e  = match overlap (primary), parameter estimation error (secondary)
q = 3.5 (post-Newtonian waveform accuracy)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Strain dimensionless; frequency [Hz]; chirp mass [solar masses] consistent | PASS |
| S2 | Waveform template uniquely determined by (ℳ, q, χ) | PASS |
| S3 | Matched filter SNR converges; template bank covers space | PASS |
| S4 | Overlap > 0.97 achievable for BBH signals with SNR > 10 | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_374_hash>

omega:
  description: "BBH inspiral-merger-ringdown, LIGO design sensitivity"
  sample_rate_Hz: 4096
  duration_s: 8
  outputs: [chirp_mass, mass_ratio, spin, distance, waveform]

E:
  forward: "h(t) = F₊h₊ + F×h×; df/dt ∝ f^{11/3}"
  dag: "[∂.time] -> [N.einstein] -> [K.green] -> [∫.orbital]"

B:
  constraints: "m₁,m₂ > 0; |χ| < 1; D > 0; waveform causal"

I:
  scenario: ideal
  parameters: {M_chirp: 30.0, Q: 0.8, chi1: 0.3, chi2: 0.1, D_Mpc: 400}
  mismatch: null

O: [match_overlap, param_error]

epsilon:
  overlap_min: 0.97
  convergence_order: 3.5

difficulty:
  L_DAG: 3.0
  tier: hard
  delta: 5
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known waveform + Gaussian noise | None | overlap > 0.97 |
| S2 Mismatch | Wrong PSD or calibration | Applied | relaxed 1.5x |
| S3 Oracle | True parameters known | Known | overlap > 0.97 |
| S4 Blind Cal | Full parameter estimation from strain | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_374_hash>
principle_ref: sha256:<principle_374_hash>

dataset:
  description: "Injected GW signals in colored Gaussian noise"
  n_injections: 100
  data_hash: sha256:<dataset_374_hash>

baselines:
  - solver: IMRPhenomD           match_overlap: 0.98    q: 0.96
  - solver: SEOBNRv4             match_overlap: 0.99    q: 0.98
  - solver: TaylorF2             match_overlap: 0.92    q: 0.80

quality_scoring:
  metric: match_overlap
  thresholds:
    - {min: 0.99, Q: 1.00}
    - {min: 0.97, Q: 0.90}
    - {min: 0.95, Q: 0.80}
    - {min: 0.90, Q: 0.75}
```

### Baselines

| Solver | match_overlap | Q | Approx Reward |
|--------|-------------|---|---------------|
| SEOBNRv4 | 0.99 | 0.98 | ~490 PWM |
| IMRPhenomD | 0.98 | 0.96 | ~480 PWM |
| TaylorF2 | 0.92 | 0.80 | ~400 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Sample rate and duration match spec; PSD consistent with LIGO design | PASS |
| S2 | Problem well-posed: injected signals have known parameters | PASS |
| S3 | IMRPhenomD converges; overlap improves with template refinement | PASS |
| S4 | Baseline meets threshold (overlap > 0.97); feasibility confirmed | PASS |

### Layer 3 Reward

```
Benchmark seed reward = 100 x phi(t) x 0.60 = 60 PWM (builder)
Upstream: 15% -> L2 designer, 10% -> L1 creator, 15% -> treasury
```

---

## Layer 4: Benchmark -> Solution (PoSol Mining)

### Solver Table

| Solver | Expected Overlap | Time | Q | Reward |
|--------|-----------------|------|---|--------|
| SEOBNRv4 | 0.99 | ~10 min | 0.98 | ~490 PWM |
| IMRPhenomD | 0.98 | ~1 min | 0.96 | ~480 PWM |
| TaylorF2 | 0.92 | ~5 s | 0.80 | ~400 PWM |

### Reward Calculation

```
R = R_base x phi(t) x delta x nu_c x q
  = 100 x 1.0 x 5 x 1.0 x q
  = 500 x q  PWM

Best case:  500 x 0.98 = 490 PWM
Worst case: 500 x 0.75 = 375 PWM
```

### S4 Certificate

```json
{
  "principle": "#374 Gravitational Wave Signal (Compact Binary)",
  "h_p": "sha256:<principle_374_hash>",
  "h_s": "sha256:<spec_374_hash>",
  "h_b": "sha256:<bench_374_hash>",
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"},
  "Q": 0.98,
  "difficulty": {"tier":"hard","delta":5}
}
```

---

## Reward Summary

```
L1 Principle:  200 PWM seed + upstream royalties from L2/L3/L4
L2 spec.md:    105 PWM seed (x4 scenarios = 420 PWM) + upstream from L3/L4
L3 Benchmark:   60 PWM seed (x4 benchmarks = 240 PWM) + upstream from L4
L4 Solution:   375-490 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep gravitational_wave
pwm-node verify AC_astrophysics/gravitational_wave_s1_ideal.yaml
pwm-node mine AC_astrophysics/gravitational_wave_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
