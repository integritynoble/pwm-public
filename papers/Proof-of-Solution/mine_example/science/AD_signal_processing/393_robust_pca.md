# Principle #393 — Robust PCA (Low-Rank + Sparse): Four-Layer Walkthrough

**Principle #393: Robust PCA (Low-Rank + Sparse)**
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
M = L + S + N           (observed = low-rank + sparse + noise)
min ||L||_* + λ||S||₁   s.t. ||M - L - S||_F ≤ ε
λ = 1/√max(m,n)        (universal choice, Candes et al.)
```

### DAG Decomposition G = (V, A)

```
[L.sparse] -> [O.l1] -> [L.dense]

V = {L.sparse, O.l1, L.dense}
A = {L.sparse->O.l1, O.l1->L.dense}
L_DAG = 2.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- convex optimization always has solution |
| Uniqueness | YES -- unique when L is incoherent and S is sufficiently sparse |
| Stability | YES -- stable decomposition with bounded noise |

Mismatch parameters: rank of L, sparsity fraction of S, noise level, λ tuning

### Error-Bounding Method

```
e  = L recovery NMSE (primary), S support F1 (secondary)
q = 1.0 (ADMM convergence)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Matrix M dimensions m x n consistent; λ > 0 | PASS |
| S2 | Convex problem; incoherence + sparsity guarantee recovery | PASS |
| S3 | ADMM / ALM converge; objective decreases monotonically | PASS |
| S4 | L recovery NMSE < 0.01 for r << min(m,n) and sparse S | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

```yaml
principle_ref: sha256:<principle_393_hash>

omega:
  description: "RPCA on 200x200 matrix, rank-5 + 5% sparse outliers"
  size: [200, 200]
  rank: 5
  sparsity_fraction: 0.05
  outputs: [low_rank_L, sparse_S]

E:
  forward: "M = L + S + N"
  dag: "[L.sparse] -> [O.l1] -> [L.dense]"

B:
  constraints: "L incoherent; S sparse; λ = 1/√n"

I:
  scenario: ideal
  parameters: {noise_sigma: 0.01}
  mismatch: null

O: [L_NMSE, S_F1]

epsilon:
  L_NMSE_max: 0.01

difficulty:
  L_DAG: 2.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known rank + sparse fraction | None | L_NMSE < 0.01 |
| S2 Mismatch | Higher sparsity or noise | Applied | relaxed 1.5x |
| S3 Oracle | True decomposition known | Known | L_NMSE < 0.01 |
| S4 Blind Cal | Unknown rank and sparsity | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
```

---

## Layer 3: spec.md -> Benchmark

```yaml
spec_ref: sha256:<spec_393_hash>
principle_ref: sha256:<principle_393_hash>

dataset:
  description: "Surveillance video background-foreground separation"
  n_sequences: 20
  data_hash: sha256:<dataset_393_hash>

baselines:
  - solver: IALM               L_NMSE: 0.004    q: 0.95
  - solver: GoDec              L_NMSE: 0.008    q: 0.88
  - solver: Online-RPCA        L_NMSE: 0.010    q: 0.82

quality_scoring:
  metric: L_NMSE
  thresholds:
    - {max: 0.002, Q: 1.00}
    - {max: 0.005, Q: 0.90}
    - {max: 0.010, Q: 0.80}
    - {max: 0.020, Q: 0.75}
```

### Baselines

| Solver | L_NMSE | Q | Approx Reward |
|--------|--------|---|---------------|
| IALM | 0.004 | 0.95 | ~285 PWM |
| GoDec | 0.008 | 0.88 | ~264 PWM |
| Online-RPCA | 0.010 | 0.82 | ~246 PWM |

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
  "principle": "#393 Robust PCA (Low-Rank + Sparse)",
  "h_p": "sha256:<principle_393_hash>",
  "h_s": "sha256:<spec_393_hash>",
  "h_b": "sha256:<bench_393_hash>",
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
pwm-node benchmarks | grep robust_pca
pwm-node verify AD_signal_processing/robust_pca_s1_ideal.yaml
pwm-node mine AD_signal_processing/robust_pca_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
