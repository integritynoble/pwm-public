# Principle #28 — Generic Matrix Sensing

**Domain:** Compressive Imaging | **Carrier:** N/A | **Difficulty:** Standard (δ=3)
**DAG:** Λ → S → D | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          Λ→S→D        MatSense    MatSense-Synth-10  Nuclear-Norm
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  GENERIC MATRIX SENSING   P = (E, G, W, C)   Principle #28      │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y_i = <A_i, X> + n_i = tr(A_i^T X) + n_i              │
│        │ X ∈ R^{m×n}, rank(X) = r << min(m,n)                   │
│        │ A_i = known measurement matrices, i = 1..M              │
│        │ Inverse: recover low-rank X from M linear measurements  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [Λ] ──→ [S] ──→ [D]                                   │
│        │  Transform Sample   Detect(scalar measurements)         │
│        │ V={Λ,S,D}  A={Λ→S, S→D}   L_DAG=2.0                  │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (RIP for Gaussian A_i with M ≥ Cr(m+n))│
│        │ Uniqueness: YES under rank constraint + sufficient M    │
│        │ Stability: depends on RIP constant δ_2r                │
│        │ Mismatch: rank model order r, noise level               │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative Frobenius error ||X-X̂||_F/||X||_F         │
│        │ q = 1.0 (proximal gradient for nuclear norm penalty)  │
│        │ T = {rel_error, fitted_rate, rank_recovery_accuracy}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Measurement matrices A_i well-defined; dimensions m,n,M consistent | PASS |
| S2 | M ≥ C r(m+n): sufficient measurements for rank-r recovery | PASS |
| S3 | Proximal gradient on nuclear norm converges with O(1/k) rate | PASS |
| S4 | Relative error ≤ 0.01 achievable at M/(r(m+n)) ≥ 5 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# matrix_sensing/synth_s1_ideal.yaml
principle_ref: sha256:<p028_hash>
omega:
  matrix_size: [100, 100]
  rank: 5
  measurements: 3000
  measurement_type: gaussian_iid
  oversampling: 6.0
E:
  forward: "y_i = tr(A_i^T X) + n"
I:
  dataset: MatSense_Synth_10
  instances: 10
  noise: {type: gaussian, sigma: 0.001}
  scenario: ideal
O: [relative_frobenius_error, rank_recovery]
epsilon:
  rel_error_max: 0.01
  rank_recovery: true
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | M=3000, r=5, m=n=100: oversampling ratio 6x | PASS |
| S2 | Gaussian measurements: RIP holds with high probability | PASS |
| S3 | Proximal gradient converges within 200 iterations | PASS |
| S4 | Relative error ≤ 0.01 at 6x oversampling | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# matrix_sensing/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec028_hash>
dataset:
  name: MatSense_Synth_10
  instances: 10
  matrix_size: [100, 100]
  rank: 5
baselines:
  - solver: Nuclear-Norm-PGD
    params: {lambda: 0.1, max_iter: 200}
    results: {rel_error: 0.0085, rank_exact: true}
  - solver: SVT
    params: {tau: 100, delta: 1.2}
    results: {rel_error: 0.0062, rank_exact: true}
  - solver: AltMin
    params: {rank: 5, max_iter: 100}
    results: {rel_error: 0.0031, rank_exact: true}
  - solver: RGrad
    params: {rank: 5, max_iter: 50}
    results: {rel_error: 0.0018, rank_exact: true}
quality_scoring:
  metric: relative_frobenius_error
  thresholds:
    - {max: 0.002, Q: 1.00}
    - {max: 0.005, Q: 0.90}
    - {max: 0.010, Q: 0.80}
    - {max: 0.020, Q: 0.75}
```

**Baseline:** Nuclear-Norm-PGD — rel. error 0.0085 | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | Rel. Error | Rank OK | Runtime | Q |
|--------|-----------|---------|---------|---|
| Nuclear-Norm-PGD | 0.0085 | YES | 10 s | 0.80 |
| SVT | 0.0062 | YES | 5 s | 0.88 |
| AltMin | 0.0031 | YES | 2 s | 0.94 |
| RGrad | 0.0018 | YES | 1 s | 1.00 |

### Reward Calculation

```
R = 100 × 1.0 × 3 × 1.0 × Q = 300 × Q
Best (RGrad):  300 × 1.00 = 300 PWM
Floor:         300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p028_hash>",
  "h_s": "sha256:<spec028_hash>",
  "h_b": "sha256:<bench028_hash>",
  "r": {"residual_norm": 0.0031, "error_bound": 0.01, "ratio": 0.31},
  "c": {"fitted_rate": 0.96, "theoretical_rate": 1.0, "K": 3},
  "Q": 0.94,
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"}
}
```

---

## Reward Summary

| Layer | Seed Reward | Ongoing Royalties |
|-------|-------------|-------------------|
| L1 Principle | 200 PWM | 5% of L4 mints |
| L2 spec.md | 105 PWM | 10% of L4 mints |
| L3 Benchmark | 60 PWM | 15% of L4 mints |
| L4 Solution | — | 225–300 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep matrix_sensing
pwm-node verify matrix_sensing/synth_s1_ideal.yaml
pwm-node mine matrix_sensing/synth_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
