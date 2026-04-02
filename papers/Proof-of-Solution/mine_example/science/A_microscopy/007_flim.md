# Principle #7 — Fluorescence Lifetime Imaging (FLIM)

**Domain:** Microscopy | **Carrier:** Photon | **Difficulty:** Frontier (δ=5)
**DAG:** G.pulse --> K.psf.irf --> ∫.temporal | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          G.pulse-->K.psf.irf-->∫.temporal  FLIM  FLIM-Cells-10  Lifetime-Fit
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  FLIM  P = (E, G, W, C)   Principle #7                        │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ y(r,t) = IRF(t) ⊛ Σ_i α_i(r)·exp(-t/τ_i(r)) + n    │
│        │ Multi-exponential decay; IRF = instrument response    │
│        │ Inverse: recover lifetime maps τ_i(r) and fractions  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [G.pulse] ──→ [K.psf.irf] ──→ [∫.temporal]            │
│        │  Source(pulsed)  Conv(IRF)   Accumulate(TCSPC)         │
│        │ V={G,K,∫}  A={G-->K, K-->∫}   L_DAG=3.5              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (exponential decay uniquely determined)│
│        │ Uniqueness: CONDITIONAL (mono-exp YES; bi-exp needs   │
│        │   sufficient time bins and photon counts)              │
│        │ Stability: κ ≈ 35 (mono-exp); κ ≈ 150 (bi-exp)      │
│        │ Mismatch: IRF width, background, pile-up distortion   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSE(τ) in ns, fraction error Δα                  │
│        │ q = 2.0 (MLE convergence for exponential model)      │
│        │ T = {residual_norm, chi_squared, lifetime_accuracy}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | TCSPC histogram bins consistent with laser rep rate and τ range | PASS |
| S2 | Mono-exponential well-posed; bi-exp needs > 500 photons/pixel | PASS |
| S3 | MLE and phasor methods converge for Poisson-distributed counts | PASS |
| S4 | τ accuracy ≤ 0.2 ns achievable at > 1000 photons | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# flim/cells_s1_ideal.yaml
principle_ref: sha256:<p007_hash>
omega:
  grid: [256, 256]
  time_bins: 256
  bin_width_ps: 50
  rep_rate_MHz: 80
E:
  forward: "y(r,t) = IRF ⊛ Σ α_i·exp(-t/τ_i) + n"
  components: 2  # bi-exponential
I:
  dataset: FLIM_Cells_10
  images: 10
  photons_per_pixel: 1000
  noise: {type: poisson}
  scenario: ideal
O: [RMSE_tau_ns, fraction_error, chi_squared]
epsilon:
  RMSE_tau_max: 0.20
  fraction_error_max: 0.05
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 256 bins × 50 ps = 12.8 ns window covers typical lifetimes | PASS |
| S2 | 1000 photons/px for bi-exp: κ ≈ 80, manageable | PASS |
| S3 | MLE converges within 100 iterations for bi-exp | PASS |
| S4 | RMSE(τ) ≤ 0.20 ns feasible at 1000 photons | PASS |

**Layer 2 reward:** 105 PWM + upstream

---

## Layer 3 — spec → Benchmark

```yaml
# flim/benchmark_s1_ideal.yaml
spec_ref: sha256:<spec007_hash>
dataset:
  name: FLIM_Cells_10
  images: 10
  size: [256, 256, 256]
baselines:
  - solver: SPCImage-MLE
    params: {components: 2, n_iter: 200}
    results: {RMSE_tau: 0.18, fraction_error: 0.042}
  - solver: Phasor-FLIM
    params: {harmonics: 1}
    results: {RMSE_tau: 0.25, fraction_error: 0.068}
  - solver: FLIMnet
    params: {arch: 1DCNN}
    results: {RMSE_tau: 0.09, fraction_error: 0.021}
quality_scoring:
  metric: RMSE_tau_ns
  thresholds:
    - {max: 0.08, Q: 1.00}
    - {max: 0.12, Q: 0.90}
    - {max: 0.20, Q: 0.80}
    - {max: 0.30, Q: 0.75}
```

**Baseline:** SPCImage-MLE — RMSE 0.18 ns | **Layer 3 reward:** 60 PWM

---

## Layer 4 — Benchmark → Solution

| Solver | RMSE(τ) ns | Δα | Runtime | Q |
|--------|-----------|-----|---------|---|
| Phasor-FLIM | 0.25 | 0.068 | 0.2 s | 0.75 |
| SPCImage-MLE | 0.18 | 0.042 | 15 s | 0.80 |
| FLIMnet (CNN) | 0.09 | 0.021 | 0.5 s | 0.95 |
| FLIMJ-Bayes | 0.11 | 0.028 | 8 s | 0.90 |

### Reward Calculation

```
R = 100 × 1.0 × 5 × 1.0 × Q = 500 × Q
Best (FLIMnet):  500 × 0.95 = 475 PWM
Floor:           500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p007_hash>",
  "r": {"residual_norm": 0.09, "error_bound": 0.20, "ratio": 0.45},
  "c": {"fitted_rate": 1.88, "theoretical_rate": 2.0, "K": 3},
  "Q": 0.90,
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
| L4 Solution | — | 375–475 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep flim
pwm-node verify flim/cells_s1_ideal.yaml
pwm-node mine flim/cells_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
