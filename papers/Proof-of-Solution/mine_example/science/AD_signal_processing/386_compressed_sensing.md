# Principle #386 — Compressed Sensing: Four-Layer Walkthrough

**Principle #386: Compressed Sensing**
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
y = Φx + n,   y ∈ ℝ^m, x ∈ ℝ^n, m << n   (underdetermined system)
x̂ = argmin ||x||₁  s.t. ||y - Φx||₂ ≤ ε   (basis pursuit denoising)
RIP: (1-δ_s)||x||² ≤ ||Φx||² ≤ (1+δ_s)||x||²  for s-sparse x
Recovery: m ≥ C s log(n/s) measurements suffice
```

### DAG Decomposition G = (V, A)

```
[L.sparse] -> [O.l1]

V = {L.sparse, O.l1}
A = {L.sparse->O.l1}
L_DAG = 1.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- measurements always exist |
| Uniqueness | YES -- RIP guarantees unique s-sparse recovery |
| Stability | YES -- stable recovery with bounded noise (BPDN) |

Mismatch parameters: sparsity level s, measurement matrix Φ, noise level, sparsifying basis

### Error-Bounding Method

```
e  = normalized MSE ||x̂-x||/||x|| (primary), support recovery rate (secondary)
q = 1.0 (ISTA convergence rate)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Measurement matrix m x n dimensions correct; m < n | PASS |
| S2 | RIP satisfied for Gaussian Φ with m = O(s log n/s) | PASS |
| S3 | ISTA/FISTA/ADMM converge monotonically | PASS |
| S4 | NMSE < 0.01 achievable for m/n = 0.3, s/n = 0.05 | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

```yaml
principle_ref: sha256:<principle_386_hash>

omega:
  description: "CS recovery, n=1024, m=256, Gaussian Φ, s=50 sparse"
  n: 1024
  m: 256
  outputs: [recovered_signal, support]

E:
  forward: "y = Φx + n"
  dag: "[L.sparse] -> [O.l1]"

B:
  constraints: "||x||₀ ≤ s; Φ satisfies RIP"

I:
  scenario: ideal
  parameters: {sparsity: 50, noise_sigma: 0.01}
  mismatch: null

O: [NMSE, support_recovery]

epsilon:
  NMSE_max: 0.01
  convergence_order: 1.0

difficulty:
  L_DAG: 2.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known Φ, known sparsity basis | None | NMSE < 0.01 |
| S2 Mismatch | Basis mismatch or noise underestimate | Applied | relaxed 1.5x |
| S3 Oracle | True support known | Known | NMSE < 0.01 |
| S4 Blind Cal | Unknown sparsity level | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

```yaml
spec_ref: sha256:<spec_386_hash>
principle_ref: sha256:<principle_386_hash>

dataset:
  description: "Random sparse signals at multiple m/n ratios"
  ratios: [0.15, 0.25, 0.35, 0.50]
  n_trials: 100
  data_hash: sha256:<dataset_386_hash>

baselines:
  - solver: FISTA              NMSE: 0.005    q: 0.95
  - solver: OMP                NMSE: 0.008    q: 0.90
  - solver: LASSO              NMSE: 0.012    q: 0.85

quality_scoring:
  metric: NMSE
  thresholds:
    - {max: 0.002, Q: 1.00}
    - {max: 0.005, Q: 0.90}
    - {max: 0.010, Q: 0.80}
    - {max: 0.020, Q: 0.75}
```

### Baselines

| Solver | NMSE | Q | Approx Reward |
|--------|------|---|---------------|
| FISTA | 0.005 | 0.95 | ~285 PWM |
| OMP | 0.008 | 0.90 | ~270 PWM |
| LASSO | 0.012 | 0.85 | ~255 PWM |

### Layer 3 Reward

```
Benchmark seed reward = 100 x phi(t) x 0.60 = 60 PWM (builder)
Upstream: 15% -> L2 designer, 10% -> L1 creator, 15% -> treasury
```

---

## Layer 4: Benchmark -> Solution (PoSol Mining)

### Solver Table

| Solver | NMSE | Runtime | Q | Reward |
|--------|------|---------|---|--------|
| FISTA | 0.005 | 0.5 s | 0.95 | ~285 PWM |
| OMP | 0.008 | 0.1 s | 0.90 | ~270 PWM |
| LASSO | 0.012 | 1 s | 0.85 | ~255 PWM |

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
  "principle": "#386 Compressed Sensing",
  "h_p": "sha256:<principle_386_hash>",
  "h_s": "sha256:<spec_386_hash>",
  "h_b": "sha256:<bench_386_hash>",
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
pwm-node benchmarks | grep compressed_sensing
pwm-node verify AD_signal_processing/compressed_sensing_s1_ideal.yaml
pwm-node mine AD_signal_processing/compressed_sensing_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
