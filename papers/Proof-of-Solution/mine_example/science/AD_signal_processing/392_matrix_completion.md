# Principle #392 — Matrix Completion: Four-Layer Walkthrough

**Principle #392: Matrix Completion**
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
Y_ij = X_ij + n_ij,  (i,j) ∈ Ω   (observed entries)
X̂ = argmin ||X||_*  s.t. ||P_Ω(Y - X)||_F ≤ ε  (nuclear norm minimization)
||X||_* = Σ σ_i(X)                 (nuclear norm = sum of singular values)
Recovery: |Ω| ≥ C r n polylog(n)   (sufficient observations for rank-r, n x n matrix)
```

### DAG Decomposition G = (V, A)

```
[S.random] -> [L.sparse] -> [O.l1]

V = {S.random, L.sparse, O.l1}
A = {S.random->L.sparse, L.sparse->O.l1}
L_DAG = 2.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- nuclear norm minimization always has solution |
| Uniqueness | YES -- unique for incoherent matrices with sufficient observations |
| Stability | YES -- stable with bounded noise (Candes & Plan) |

Mismatch parameters: rank r, observation density, incoherence condition, noise level

### Error-Bounding Method

```
e  = NMSE ||X̂-X||_F/||X||_F (primary), rank recovery (secondary)
q = 1.0 (SVT convergence)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Matrix dimensions m x n; observation set Ω well-defined | PASS |
| S2 | Nuclear norm minimization convex; incoherence condition met | PASS |
| S3 | SVT / ALS converge; NMSE decreases with observations | PASS |
| S4 | NMSE < 0.01 achievable for |Ω|/mn > 5r/min(m,n) | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

```yaml
principle_ref: sha256:<principle_392_hash>

omega:
  description: "Matrix completion, 500x500, rank=10, 20% observed"
  size: [500, 500]
  rank: 10
  obs_fraction: 0.20
  outputs: [completed_matrix]

E:
  forward: "Y_ij = X_ij + n_ij, (i,j) in Ω"
  dag: "[S.random] -> [L.sparse] -> [O.l1]"

B:
  constraints: "rank(X) ≤ r; incoherence; |Ω| sufficient"

I:
  scenario: ideal
  parameters: {noise_sigma: 0.01}
  mismatch: null

O: [NMSE, rank_recovered]

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
| S1 Ideal | Known rank + uniform sampling | None | NMSE < 0.01 |
| S2 Mismatch | Non-uniform sampling or wrong rank | Applied | relaxed 1.5x |
| S3 Oracle | True rank known | Known | NMSE < 0.01 |
| S4 Blind Cal | Estimate rank from data | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
```

---

## Layer 3: spec.md -> Benchmark

```yaml
spec_ref: sha256:<spec_392_hash>
principle_ref: sha256:<principle_392_hash>

dataset:
  description: "Low-rank matrices at multiple observation fractions"
  obs_fractions: [0.10, 0.20, 0.30, 0.50]
  n_trials: 100
  data_hash: sha256:<dataset_392_hash>

baselines:
  - solver: SVT                NMSE: 0.005    q: 0.95
  - solver: ALS                NMSE: 0.008    q: 0.90
  - solver: SoftImpute         NMSE: 0.006    q: 0.92

quality_scoring:
  metric: NMSE
  thresholds:
    - {max: 0.003, Q: 1.00}
    - {max: 0.006, Q: 0.90}
    - {max: 0.010, Q: 0.80}
    - {max: 0.020, Q: 0.75}
```

### Baselines

| Solver | NMSE | Q | Approx Reward |
|--------|------|---|---------------|
| SVT | 0.005 | 0.95 | ~285 PWM |
| SoftImpute | 0.006 | 0.92 | ~276 PWM |
| ALS | 0.008 | 0.90 | ~270 PWM |

### Layer 3 Reward

```
Benchmark seed reward = 100 x phi(t) x 0.60 = 60 PWM (builder)
```

---

## Layer 4: Benchmark -> Solution (PoSol Mining)

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
  "principle": "#392 Matrix Completion",
  "h_p": "sha256:<principle_392_hash>",
  "h_s": "sha256:<spec_392_hash>",
  "h_b": "sha256:<bench_392_hash>",
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
pwm-node benchmarks | grep matrix_completion
pwm-node verify AD_signal_processing/matrix_completion_s1_ideal.yaml
pwm-node mine AD_signal_processing/matrix_completion_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
