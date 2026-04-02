# Principle #133 — Wide-Angle X-ray Scattering (WAXS)

**Domain:** Scientific Instrumentation | **Carrier:** X-ray Photon | **Difficulty:** Research (δ=5)
**DAG:** K.scatter.bragg --> S.reciprocal --> N.pointwise.abs2 | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.scatter.bragg-->S.reciprocal-->N.pointwise.abs2    WAXS        WAXSPoly-15        Rietveld
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  WIDE-ANGLE X-RAY SCATTERING (WAXS)   P = (E, G, W, C)  #133  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I(2θ) = Σ_hkl m_hkl |F_hkl|² L(2θ) P(2θ) A(2θ)     │
│        │ Bragg peaks at 2θ > 10°; crystallite structure info    │
│        │ F_hkl = structure factor; L,P,A = Lorentz, polar., abs.│
│        │ Inverse: fit crystal structure / phase fractions        │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.scatter.bragg] --> [S.reciprocal] --> [N.pointwise.abs2]│
│        │  WideAngleScatter  Reciprocal  ModSq                   │
│        │ V={K.scatter.bragg, S.reciprocal, N.pointwise.abs2}  A={K.scatter.bragg-->S.reciprocal, S.reciprocal-->N.pointwise.abs2}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Bragg peaks always present for crystals)│
│        │ Uniqueness: YES (peak positions + intensities unique)  │
│        │ Stability: κ ≈ 8 (single phase), κ ≈ 40 (multi-phase) │
│        │ Mismatch: preferred orientation, amorphous background  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = R_wp (primary), χ² (secondary)                     │
│        │ q = 2.0 (Rietveld least-squares convergence)          │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | 2θ range, step size, and wavelength cover all significant Bragg reflections | PASS |
| S2 | Peak-to-background ratio ≥ 3; sufficient resolution to separate overlapping peaks | PASS |
| S3 | Rietveld refinement converges within 50 cycles for known starting model | PASS |
| S4 | R_wp ≤ 10% achievable for well-crystallised single-phase samples | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# waxs/waxspoly_s1.yaml
principle_ref: sha256:<p133_hash>
omega:
  two_theta_range: [10, 90]
  step_deg: 0.02
  wavelength_A: 1.5406
  detector: area_detector
  sample: polycrystalline
E:
  forward: "I(2theta) = sum_hkl m*|F_hkl|^2*L*P*A + background"
  refinement: "Rietveld"
I:
  dataset: WAXSPoly_15
  patterns: 15
  noise: {type: poisson, peak_counts: 10000}
  scenario: ideal
O: [R_wp_pct, chi_sq]
epsilon:
  R_wp_max: 12.0
  chi_sq_max: 2.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 10°–90° at 0.02° step with Cu Kα covers all major reflections | PASS |
| S2 | κ ≈ 8 for single-phase at 10000 peak counts | PASS |
| S3 | Rietveld converges within 30 cycles for polycrystalline patterns | PASS |
| S4 | R_wp ≤ 12% feasible at stated counting statistics | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# waxs/benchmark_s1.yaml
spec_ref: sha256:<spec133_hash>
principle_ref: sha256:<p133_hash>
dataset:
  name: WAXSPoly_15
  patterns: 15
  two_theta_points: 4000
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Le-Bail
    params: {cycles: 20}
    results: {R_wp_pct: 14.0, chi_sq: 2.8}
  - solver: Rietveld-GSAS
    params: {cycles: 50}
    results: {R_wp_pct: 8.5, chi_sq: 1.5}
  - solver: TOPAS-Fundamental
    params: {approach: fundamental_params}
    results: {R_wp_pct: 6.2, chi_sq: 1.1}
quality_scoring:
  - {max_Rwp: 7.0, Q: 1.00}
  - {max_Rwp: 9.0, Q: 0.90}
  - {max_Rwp: 12.0, Q: 0.80}
  - {max_Rwp: 15.0, Q: 0.75}
```

**Baseline solver:** Rietveld-GSAS — R_wp 8.5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | R_wp (%) | χ² | Runtime | Q |
|--------|----------|-----|---------|---|
| Le-Bail | 14.0 | 2.8 | 1 min | 0.75 |
| Rietveld-GSAS | 8.5 | 1.5 | 5 min | 0.90 |
| TOPAS-Fundamental | 6.2 | 1.1 | 3 min | 1.00 |
| DL-XRD (AutoRietveld) | 7.0 | 1.2 | 10 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (TOPAS/DL):  500 × 1.00 = 500 PWM
Floor:                 500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p133_hash>",
  "h_s": "sha256:<spec133_hash>",
  "h_b": "sha256:<bench133_hash>",
  "r": {"residual_norm": 0.062, "error_bound": 0.12, "ratio": 0.52},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
  "Q": 1.00,
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
| L4 Solution | — | 375–500 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep waxs
pwm-node verify waxs/waxspoly_s1.yaml
pwm-node mine waxs/waxspoly_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
