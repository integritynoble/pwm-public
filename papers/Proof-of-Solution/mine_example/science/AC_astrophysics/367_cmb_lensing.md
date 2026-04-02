# Principle #367 — CMB Lensing Reconstruction: Four-Layer Walkthrough

**Principle #367: CMB Lensing Reconstruction**
Domain: Astrophysics & Cosmology | Carrier: electromagnetic | Difficulty: hard (delta=5) | Reward: 5x base

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
T̃(n̂) = T(n̂ + ∇φ(n̂))   (lensed CMB temperature)
φ(n̂) = -2 ∫ dχ (χ_s - χ)/(χ_s χ) Ψ(χn̂, χ)  (lensing potential)
⟨φ̂(L)⟩ ∝ ∫ d²l T(l) T(l+L) f(l, L)  (quadratic estimator)
```

### DAG Decomposition G = (V, A)

```
[∂.time] -> [N.boltzmann] -> [∫.multipole] -> [K.green]

V = {∂.time, N.boltzmann, ∫.multipole, K.green}
A = {∂.time->N.boltzmann, N.boltzmann->∫.multipole, ∫.multipole->K.green}
L_DAG = 3.0   Tier: hard (delta = 5)
```

### Well-Posedness Certificate

| Property | Status |
|----------|--------|
| Existence | YES -- lensing potential is a weighted integral of matter potential |
| Uniqueness | YES -- quadratic estimator is optimal for Gaussian CMB |
| Stability | CONDITIONAL -- requires sufficient sky coverage and noise level for convergence |

Mismatch parameters: beam FWHM, noise level, foreground contamination, sky mask

### Error-Bounding Method

```
e  = lensing power C_l^φφ relative error (primary), cross-correlation r (secondary)
q = 1.0 (quadratic estimator bias scaling)
T  = {residual_norm, error_bound, convergence_rate, fitted_rate, K_resolutions, quality_q}
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Angular scales consistent; lensing potential φ dimensionless | PASS |
| S2 | Quadratic estimator unbiased for Gaussian fields with known CMB power | PASS |
| S3 | Iterative estimators converge; N0 bias subtractable | PASS |
| S4 | C_l^φφ recoverable to 5% per bandpower for Planck-level noise | PASS |

### Layer 1 Reward

```
Principle seed reward = 200 x phi(t) PWM
Upstream: 15% of L2 seeds + 10% of L3 seeds + 5% of L4 mints + 5% of L4 usage
```

---

## Layer 2: Principle -> spec.md

### Example spec.md (S1 Ideal Scenario)

```yaml
principle_ref: sha256:<principle_367_hash>

omega:
  description: "CMB lensing reconstruction, l_max=3000, full-sky simulation"
  l_max: 3000
  beam_arcmin: 5.0
  noise_uK_arcmin: 30
  outputs: [phi_map, Cl_phiphi]

E:
  forward: "T̃(n̂) = T(n̂ + ∇φ(n̂))"
  dag: "[∂.time] -> [N.boltzmann] -> [∫.multipole] -> [K.green]"

B:
  constraints: "φ is curl-free; N0 bias subtracted; mean field removed"

I:
  scenario: ideal
  simulation: full-sky lensed CMB + Gaussian noise
  mismatch: null

O: [Cl_phiphi_error, cross_correlation_r]

epsilon:
  Cl_phi_err_max: 0.05
  cross_corr_min: 0.90

difficulty:
  L_DAG: 3.0
  tier: hard
  delta: 5
```

### S1-S4 Scenarios

| Scenario | Operator | Mismatch | Threshold |
|----------|----------|----------|-----------|
| S1 Ideal | Known beam + noise | None | Cl_phi_err < 5% |
| S2 Mismatch | Wrong beam or noise model | Applied | relaxed 1.5x |
| S3 Oracle | True φ known | Known | Cl_phi_err < 5% |
| S4 Blind Cal | Estimate beam/noise from data | Unknown | recover >= 85% of oracle gap |

### Layer 2 Reward

```
spec.md seed reward = 150 x phi(t) x 0.70 = 105 PWM (designer)
Upstream: 15% -> L1 creator, 15% -> treasury
```

---

## Layer 3: spec.md -> Benchmark

### Benchmark Configuration

```yaml
spec_ref: sha256:<spec_367_hash>
principle_ref: sha256:<principle_367_hash>

dataset:
  description: "Simulated lensed CMB maps at multiple noise levels"
  noise_levels_uK_arcmin: [10, 20, 30, 50]
  data_hash: sha256:<dataset_367_hash>

baselines:
  - solver: Hu-Okamoto QE       Cl_phi_error: 0.03    q: 0.92
  - solver: Iterative-MV        Cl_phi_error: 0.02    q: 0.95
  - solver: Gradient-inversion  Cl_phi_error: 0.06    q: 0.80

quality_scoring:
  metric: Cl_phiphi_error
  thresholds:
    - {max: 0.01, Q: 1.00}
    - {max: 0.03, Q: 0.90}
    - {max: 0.05, Q: 0.80}
    - {max: 0.08, Q: 0.75}
```

### Baselines

| Solver | Cl_phi_error | Q | Approx Reward |
|--------|-------------|---|---------------|
| Iterative-MV | 0.02 | 0.95 | ~475 PWM |
| Hu-Okamoto QE | 0.03 | 0.92 | ~460 PWM |
| Gradient-inversion | 0.06 | 0.80 | ~400 PWM |

### S1-S4 Gate Checks (Layer 3)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Noise levels match spec; map resolution consistent | PASS |
| S2 | Problem well-posed: QE is minimum-variance for Gaussian fields | PASS |
| S3 | Iterative estimator converges; bias decreases with iteration | PASS |
| S4 | Baseline meets threshold (Cl_phi_err < 5%); feasibility confirmed | PASS |

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
| Iterative-MV | 0.02 | ~10 min | 0.95 | ~475 PWM |
| Hu-Okamoto QE | 0.03 | ~2 min | 0.92 | ~460 PWM |
| Gradient-inversion | 0.06 | ~5 min | 0.80 | ~400 PWM |

### Reward Calculation

```
R = R_base x phi(t) x delta x nu_c x q
  = 100 x 1.0 x 5 x 1.0 x q
  = 500 x q  PWM

Best case:  500 x 0.95 = 475 PWM
Worst case: 500 x 0.75 = 375 PWM
```

### S4 Certificate

```json
{
  "principle": "#367 CMB Lensing Reconstruction",
  "h_p": "sha256:<principle_367_hash>",
  "h_s": "sha256:<spec_367_hash>",
  "h_b": "sha256:<bench_367_hash>",
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"},
  "Q": 0.95,
  "difficulty": {"tier":"hard","delta":5}
}
```

---

## Reward Summary

```
L1 Principle:  200 PWM seed + upstream royalties from L2/L3/L4
L2 spec.md:    105 PWM seed (x4 scenarios = 420 PWM) + upstream from L3/L4
L3 Benchmark:   60 PWM seed (x4 benchmarks = 240 PWM) + upstream from L4
L4 Solution:   375-475 PWM per solution (depending on q)
```

---

## Quick-Start

```bash
pwm-node benchmarks | grep cmb_lensing
pwm-node verify AC_astrophysics/cmb_lensing_s1_ideal.yaml
pwm-node mine AC_astrophysics/cmb_lensing_s1_ideal.yaml
pwm-node inspect sha256:<your_cert_hash>
```
