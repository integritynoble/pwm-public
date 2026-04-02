# Principle #390 — Phase Unwrapping: Four-Layer Walkthrough

**Principle #390: Phase Unwrapping**
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
ψ_wrapped(r) = φ(r) mod 2π       (wrapped phase observation)
φ(r) = ψ_wrapped(r) + 2πk(r)    (true phase = wrapped + integer multiples)
∇φ ≈ W[∇ψ_wrapped]              (Itoh's condition: |Δφ| < π)
min ||∇φ - W[∇ψ_w]||²           (least-squares unwrapping)
```

### DAG Decomposition G = (V, A)

```
[∂.space] -> [N.pointwise] -> [O.l2]

V = {∂.space, N.pointwise, O.l2}
A = {∂.space->N.pointwise, N.pointwise->O.l2}
L_DAG = 2.0   Tier: standard (delta = 3)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- wrapped phase always exists |
| Uniqueness | CONDITIONAL -- unique when Itoh's condition holds; ambiguous at residues |
| Stability | CONDITIONAL -- noise and discontinuities create residues |

Mismatch parameters: noise level, phase discontinuities, spatial undersampling, residue density

### Error-Bounding Method

```
e  = phase RMS error [rad] (primary), residue count (secondary)
q = 2.0 (Poisson solver convergence)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Phase values in [-π, π]; gradient dimensions match grid | PASS |
| S2 | LS unwrapping well-posed as Poisson equation with Neumann BC | PASS |
| S3 | PCG solver converges for LS unwrapping | PASS |
| S4 | Phase error < 0.1 rad achievable for moderate noise | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

```yaml
principle_ref: sha256:<principle_390_hash>

omega:
  description: "2D phase unwrapping, 256x256, InSAR-like phase"
  grid: [256, 256]
  outputs: [unwrapped_phase]

E:
  forward: "ψ_wrapped = φ mod 2π"
  dag: "[∂.space] -> [N.pointwise] -> [O.l2]"

B:
  constraints: "Itoh condition approximately satisfied; phase smooth"

I:
  scenario: ideal
  parameters: {noise_sigma_rad: 0.3, n_fringes: 10}
  mismatch: null

O: [phase_RMSE_rad, residue_count]

epsilon:
  RMSE_max_rad: 0.10
  convergence_order: 2.0

difficulty:
  L_DAG: 2.0
  tier: standard
  delta: 3
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Low noise, smooth phase | None | RMSE < 0.1 rad |
| S2 Mismatch | High noise or discontinuities | Applied | relaxed 1.5x |
| S3 Oracle | True phase known | Known | RMSE < 0.1 rad |
| S4 Blind Cal | Unknown noise + discontinuities | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
```

---

## Layer 3: spec.md -> Benchmark

```yaml
spec_ref: sha256:<spec_390_hash>
principle_ref: sha256:<principle_390_hash>

dataset:
  description: "Simulated InSAR wrapped phase maps"
  n_maps: 50
  data_hash: sha256:<dataset_390_hash>

baselines:
  - solver: Goldstein-branch-cut  RMSE_rad: 0.05    q: 0.92
  - solver: LS-Poisson            RMSE_rad: 0.08    q: 0.85
  - solver: SNAPHU                RMSE_rad: 0.03    q: 0.95

quality_scoring:
  metric: phase_RMSE_rad
  thresholds:
    - {max: 0.02, Q: 1.00}
    - {max: 0.05, Q: 0.90}
    - {max: 0.10, Q: 0.80}
    - {max: 0.20, Q: 0.75}
```

### Baselines

| Solver | RMSE_rad | Q | Approx Reward |
|--------|---------|---|---------------|
| SNAPHU | 0.03 | 0.95 | ~285 PWM |
| Goldstein | 0.05 | 0.92 | ~276 PWM |
| LS-Poisson | 0.08 | 0.85 | ~255 PWM |

### Layer 3 Reward

```
Benchmark seed reward = 100 x phi(t) x 0.60 = 60 PWM (builder)
```

---

## Layer 4: Benchmark -> Solution (PoSol Mining)

### Solver Table

| Solver | RMSE (rad) | Runtime | Q | Reward |
|--------|-----------|---------|---|--------|
| SNAPHU | 0.03 | 10 s | 0.95 | ~285 PWM |
| Goldstein | 0.05 | 2 s | 0.92 | ~276 PWM |
| LS-Poisson | 0.08 | 0.5 s | 0.85 | ~255 PWM |

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
  "principle": "#390 Phase Unwrapping",
  "h_p": "sha256:<principle_390_hash>",
  "h_s": "sha256:<spec_390_hash>",
  "h_b": "sha256:<bench_390_hash>",
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
pwm-node benchmarks | grep phase_unwrapping
pwm-node verify AD_signal_processing/phase_unwrapping_s1_ideal.yaml
pwm-node mine AD_signal_processing/phase_unwrapping_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
