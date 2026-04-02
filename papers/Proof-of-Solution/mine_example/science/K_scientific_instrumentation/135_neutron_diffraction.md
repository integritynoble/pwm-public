# Principle #135 — Neutron Diffraction

**Domain:** Scientific Instrumentation | **Carrier:** Neutron | **Difficulty:** Research (δ=5)
**DAG:** K.scatter.bragg --> S.reciprocal --> N.pointwise.abs2 | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          K.scatter.bragg-->S.reciprocal-->N.pointwise.abs2    NeutDiff    NeutXtal-15        Rietveld
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  NEUTRON DIFFRACTION   P = (E, G, W, C)   Principle #135       │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ I(hkl) = N|F_N(hkl)|² · m · L · A                    │
│        │ F_N = Σ b_j exp(2πi h·r_j); b = neutron scattering len│
│        │ Sensitive to light atoms (H/D) and magnetic moments    │
│        │ Inverse: refine atomic positions from |F_N| intensities│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [K.scatter.bragg] --> [S.reciprocal] --> [N.pointwise.abs2]│
│        │  NeutronDiffract  Reciprocal  ModSq                    │
│        │ V={K.scatter.bragg, S.reciprocal, N.pointwise.abs2}  A={K.scatter.bragg-->S.reciprocal, S.reciprocal-->N.pointwise.abs2}   L_DAG=1.0│
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Bragg peaks from crystalline order)    │
│        │ Uniqueness: YES (b_j isotope-specific; H/D contrast)   │
│        │ Stability: κ ≈ 10 (high-flux), κ ≈ 60 (low-flux/abs.) │
│        │ Mismatch: absorption (Cd, B, Gd), preferred orient.   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = R_wp (primary), χ² (secondary)                     │
│        │ q = 2.0 (Rietveld least-squares convergence)          │
│        │ T = {residual_norm, fitted_rate, K_resolutions}        │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Neutron wavelength, d-spacing range, and detector coverage span required hkl set | PASS |
| S2 | Scattering-length contrast between H and D enables unique site assignment | PASS |
| S3 | Rietveld refinement converges within 50 cycles for known space group | PASS |
| S4 | R_wp ≤ 8% achievable for well-ordered deuterated crystals | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# neutron_diffraction/neutxtal_s1.yaml
principle_ref: sha256:<p135_hash>
omega:
  wavelength_A: 1.54
  d_range_A: [0.5, 10.0]
  instrument: powder_diffractometer
  two_theta_range: [5, 160]
  step_deg: 0.05
E:
  forward: "I(hkl) = N*|F_N|^2 * m * L * A"
  refinement: "Rietveld_FullProf"
I:
  dataset: NeutXtal_15
  patterns: 15
  noise: {type: poisson, peak_counts: 5000}
  scenario: ideal
O: [R_wp_pct, chi_sq]
epsilon:
  R_wp_max: 10.0
  chi_sq_max: 2.5
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1.54 Å wavelength over 5°–160° covers d from 0.8–17.6 Å | PASS |
| S2 | κ ≈ 10 at 5000 peak counts for deuterated samples | PASS |
| S3 | FullProf Rietveld converges within 40 cycles | PASS |
| S4 | R_wp ≤ 10% feasible at stated statistics | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# neutron_diffraction/benchmark_s1.yaml
spec_ref: sha256:<spec135_hash>
principle_ref: sha256:<p135_hash>
dataset:
  name: NeutXtal_15
  patterns: 15
  data_points_per: 3100
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Le-Bail-Neutron
    params: {cycles: 20}
    results: {R_wp_pct: 12.5, chi_sq: 3.0}
  - solver: Rietveld-FullProf
    params: {cycles: 50}
    results: {R_wp_pct: 7.5, chi_sq: 1.6}
  - solver: GSAS-II-Neutron
    params: {cycles: 40}
    results: {R_wp_pct: 6.0, chi_sq: 1.2}
quality_scoring:
  - {max_Rwp: 6.5, Q: 1.00}
  - {max_Rwp: 8.0, Q: 0.90}
  - {max_Rwp: 10.0, Q: 0.80}
  - {max_Rwp: 13.0, Q: 0.75}
```

**Baseline solver:** Rietveld-FullProf — R_wp 7.5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | R_wp (%) | χ² | Runtime | Q |
|--------|----------|-----|---------|---|
| Le-Bail-Neutron | 12.5 | 3.0 | 2 min | 0.75 |
| Rietveld-FullProf | 7.5 | 1.6 | 10 min | 0.90 |
| GSAS-II-Neutron | 6.0 | 1.2 | 8 min | 1.00 |
| DiffPy-CMI | 6.8 | 1.3 | 5 min | 0.95 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (GSAS-II):   500 × 1.00 = 500 PWM
Floor:                 500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p135_hash>",
  "h_s": "sha256:<spec135_hash>",
  "h_b": "sha256:<bench135_hash>",
  "r": {"residual_norm": 0.060, "error_bound": 0.10, "ratio": 0.60},
  "c": {"fitted_rate": 1.92, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep neutron_diffraction
pwm-node verify neutron_diffraction/neutxtal_s1.yaml
pwm-node mine neutron_diffraction/neutxtal_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
