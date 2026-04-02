# Principle #391 — Sparse Signal Recovery (LASSO/Basis Pursuit): Four-Layer Walkthrough

**Principle #391: Sparse Signal Recovery (LASSO/Basis Pursuit)**
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
y = Ax + n,   x sparse (||x||₀ ≤ s)
LASSO: x̂ = argmin (1/2)||y - Ax||₂² + λ||x||₁
Basis Pursuit Denoising: x̂ = argmin ||x||₁  s.t. ||y-Ax||₂ ≤ ε
Dantzig selector: x̂ = argmin ||x||₁  s.t. ||A^T(y-Ax)||_∞ ≤ λ
```

### DAG Decomposition G = (V, A)

```
[L.sparse] -> [O.l1]

V = {L.sparse, O.l1}
A = {L.sparse->O.l1}
L_DAG = 1.0   Tier: textbook (delta = 1)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- convex optimization always has solution |
| Uniqueness | YES -- strictly convex for sufficient measurements |
| Stability | YES -- LASSO error bounded by O(λ√(s log n)) |

Mismatch parameters: regularization λ, sparsity level s, dictionary mismatch

### Error-Bounding Method

```
e  = NMSE ||x̂-x||/||x|| (primary), support recovery F1 (secondary)
q = 1.0 (ISTA convergence rate)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Matrix A dimensions m x n correct; λ > 0 | PASS |
| S2 | Convex problem; unique solution for strongly convex case | PASS |
| S3 | ISTA/FISTA converge; objective decreases monotonically | PASS |
| S4 | NMSE < 0.01 achievable for appropriate λ | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

```yaml
principle_ref: sha256:<principle_391_hash>

omega:
  description: "LASSO recovery, n=500, m=200, s=20, Gaussian A"
  n: 500
  m: 200
  sparsity: 20
  outputs: [recovered_coefficients, support]

E:
  forward: "y = Ax + n"
  dag: "[L.sparse] -> [O.l1]"

B:
  constraints: "λ > 0; A satisfies RIP"

I:
  scenario: ideal
  parameters: {noise_sigma: 0.01, lambda: 0.1}
  mismatch: null

O: [NMSE, support_F1]

epsilon:
  NMSE_max: 0.01
  convergence_order: 1.0

difficulty:
  L_DAG: 2.0
  tier: textbook
  delta: 1
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known A, optimal λ | None | NMSE < 0.01 |
| S2 Mismatch | Suboptimal λ or dictionary error | Applied | relaxed 1.5x |
| S3 Oracle | True support known | Known | NMSE < 0.01 |
| S4 Blind Cal | Cross-validate λ | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
```

---

## Layer 3: spec.md -> Benchmark

```yaml
spec_ref: sha256:<spec_391_hash>
principle_ref: sha256:<principle_391_hash>

dataset:
  description: "Sparse recovery at multiple undersampling ratios"
  m_over_n: [0.2, 0.3, 0.4, 0.5]
  n_trials: 200
  data_hash: sha256:<dataset_391_hash>

baselines:
  - solver: FISTA              NMSE: 0.004    q: 0.95
  - solver: ADMM-LASSO         NMSE: 0.005    q: 0.92
  - solver: Coordinate-descent NMSE: 0.006    q: 0.90

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
| FISTA | 0.004 | 0.95 | ~95 PWM |
| ADMM-LASSO | 0.005 | 0.92 | ~92 PWM |
| Coordinate-descent | 0.006 | 0.90 | ~90 PWM |

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
  "principle": "#391 Sparse Signal Recovery (LASSO/Basis Pursuit)",
  "h_p": "sha256:<principle_391_hash>",
  "h_s": "sha256:<spec_391_hash>",
  "h_b": "sha256:<bench_391_hash>",
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
pwm-node benchmarks | grep sparse_signal
pwm-node verify AD_signal_processing/sparse_signal_s1_ideal.yaml
pwm-node mine AD_signal_processing/sparse_signal_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
