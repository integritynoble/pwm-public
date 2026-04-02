# Principle #373 — Pulsar Timing: Four-Layer Walkthrough

**Principle #373: Pulsar Timing**
Domain: Astrophysics & Cosmology | Carrier: electromagnetic | Difficulty: standard (delta=3) | Reward: 3x base

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
t_bary = t_obs + Δ_solar + Δ_disp + Δ_binary + Δ_Shapiro
φ(t) = φ₀ + ν t + (1/2) ν̇ t²  (pulse phase model)
Δ_disp = DM / (K ν²)           (dispersion delay)
TOA residual: r(t) = t_obs - t_model
```

### DAG Decomposition G = (V, A)

```
[F.dft] -> [∫.temporal] -> [O.l2]

V = {F.dft, ∫.temporal, O.l2}
A = {F.dft->∫.temporal, ∫.temporal->O.l2}
L_DAG = 2.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- timing model is deterministic for given spin/orbital parameters |
| Uniqueness | YES -- parameters uniquely determined with sufficient TOAs |
| Stability | YES -- least-squares fit stable for well-sampled data spans |

Mismatch parameters: DM variations, profile evolution, astrometric errors, unmodeled companions

### Error-Bounding Method

```
e  = RMS timing residual [μs] (primary), parameter uncertainty (secondary)
q = 0.5 (sqrt(N) improvement with number of TOAs)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Time units [s/μs] consistent; frequency [Hz] and DM [pc/cm³] correct | PASS |
| S2 | Linear timing model well-posed; phase-connected solution exists | PASS |
| S3 | TEMPO2/PINT converge for multi-year datasets | PASS |
| S4 | RMS residual < 1 μs achievable for millisecond pulsars | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_373_hash>

omega:
  description: "Millisecond pulsar, 5-year dataset, 500 TOAs"
  n_TOAs: 500
  time_span_years: 5
  outputs: [spin_params, DM, binary_params, residuals]

E:
  forward: "t_bary = t_obs + Δ_solar + Δ_disp + Δ_binary"
  dag: "[F.dft] -> [∫.temporal] -> [O.l2]"

B:
  constraints: "phase connected; DM > 0; orbital period > 0"

I:
  scenario: ideal
  parameters: {P_ms: 3.5, DM: 25.0, P_orb_days: 1.5}
  mismatch: null

O: [rms_residual_us, param_uncertainty]

epsilon:
  rms_max_us: 1.0
  convergence_order: 0.5

difficulty:
  L_DAG: 3.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known timing model | None | rms < 1 μs |
| S2 Mismatch | Unmodeled DM variation | Applied | relaxed 1.5x |
| S3 Oracle | True parameters known | Known | rms < 1 μs |
| S4 Blind Cal | Fit all parameters from TOAs | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_373_hash>
principle_ref: sha256:<principle_373_hash>

dataset:
  description: "Simulated pulsar timing datasets for isolated and binary pulsars"
  n_pulsars: 20
  data_hash: sha256:<dataset_373_hash>

baselines:
  - solver: TEMPO2              rms_residual_us: 0.3    q: 0.95
  - solver: PINT                rms_residual_us: 0.4    q: 0.92
  - solver: Simple-polyco      rms_residual_us: 2.0    q: 0.78

quality_scoring:
  metric: rms_residual_us
  thresholds:
    - {max: 0.2, Q: 1.00}
    - {max: 0.5, Q: 0.90}
    - {max: 1.0, Q: 0.80}
    - {max: 2.0, Q: 0.75}
```

### Baselines

| Solver | rms_residual_us | Q | Approx Reward |
|--------|----------------|---|---------------|
| TEMPO2 | 0.3 | 0.95 | ~285 PWM |
| PINT | 0.4 | 0.92 | ~276 PWM |
| Simple-polyco | 2.0 | 0.78 | ~234 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | TOA count and time spans match spec; frequency channels consistent | PASS |
| S2 | Problem well-posed: simulated TOAs have known solution | PASS |
| S3 | TEMPO2 converges; residual RMS decreases with more parameters | PASS |
| S4 | Baseline meets threshold (rms < 1 μs); feasibility confirmed | PASS |

### Layer 3 Reward

```
Benchmark seed reward = 100 x phi(t) x 0.60 = 60 PWM (builder)
Upstream: 15% -> L2 designer, 10% -> L1 creator, 15% -> treasury
```

---

## Layer 4: Benchmark -> Solution (PoSol Mining)

### Solver Table

| Solver | Expected Error | Time | Q | Reward |
|--------|---------------|------|---|--------|
| TEMPO2 | 0.3 μs | ~2 min | 0.95 | ~285 PWM |
| PINT | 0.4 μs | ~3 min | 0.92 | ~276 PWM |
| Simple-polyco | 2.0 μs | ~10 s | 0.78 | ~234 PWM |

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
  "principle": "#373 Pulsar Timing",
  "h_p": "sha256:<principle_373_hash>",
  "h_s": "sha256:<spec_373_hash>",
  "h_b": "sha256:<bench_373_hash>",
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
pwm-node benchmarks | grep pulsar_timing
pwm-node verify AC_astrophysics/pulsar_timing_s1_ideal.yaml
pwm-node mine AC_astrophysics/pulsar_timing_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
