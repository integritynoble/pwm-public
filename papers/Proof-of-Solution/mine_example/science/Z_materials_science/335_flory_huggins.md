# Principle #335 — Polymer Chain Statistics (Flory-Huggins)

**Domain:** Materials Science | **Carrier:** composition field | **Difficulty:** Textbook (δ=1)
**DAG:** N.pointwise → ∫.volume → O.l2 |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          φ→ΔG→μ→bin  FH-mixing   PS/PMMA-blend      analytic
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  FLORY-HUGGINS MIXING           P = (E,G,W,C)   Principle #335 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ΔG_mix/kT = (φ/N_A)ln(φ) + ((1−φ)/N_B)ln(1−φ) + χφ(1−φ)│
│        │ χ = A/T + B  (Flory-Huggins interaction parameter)    │
│        │ Spinodal: ∂²ΔG/∂φ² = 0;  Binodal: μ_A^α = μ_A^β     │
│        │ Forward: given N_A, N_B, χ(T) → phase diagram         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.pointwise] ──→ [∫.volume] ──→ [O.l2]                │
│        │ nonlinear  integrate  optimize                         │
│        │ V={N.pointwise, ∫.volume, O.l2}  A={N.pointwise→∫.volume, ∫.volume→O.l2}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (convex analysis of ΔG_mix)             │
│        │ Uniqueness: YES (common-tangent construction unique)   │
│        │ Stability: spinodal separates stable from unstable     │
│        │ Mismatch: mean-field approximation, χ fitting          │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |φ_binodal^calc − φ_binodal^expt| (primary)       │
│        │ q = exact (root-finding on analytic expressions)     │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Composition φ ∈ (0,1); free energy well-formed | PASS |
| S2 | Common tangent yields unique binodal for given χ, N | PASS |
| S3 | Newton-Raphson converges for binodal/spinodal roots | PASS |
| S4 | Binodal composition measurable against cloud-point data | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# flory_huggins/polymer_blend_s1_ideal.yaml
principle_ref: sha256:<p335_hash>
omega:
  T_range: [300, 600]  # K
  phi_range: [0.01, 0.99]
E:
  forward: "ΔG_mix/kT = (φ/N_A)ln φ + ((1-φ)/N_B)ln(1-φ) + χφ(1-φ)"
  model: Flory_Huggins
B:
  N_A: 1000
  N_B: 1000
I:
  scenario: symmetric_polymer_blend
  chi_A: 500  # χ = A/T + B
  chi_B: -0.5
O: [binodal_curve, spinodal_curve, UCST, critical_composition]
epsilon:
  phi_binodal_error: 0.005
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | T and φ ranges span full phase diagram | PASS |
| S2 | Symmetric blend has φ_c = 0.5, χ_c = 2/N | PASS |
| S3 | Root-finding converges for smooth ΔG | PASS |
| S4 | Binodal error < 0.005 achievable analytically | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# flory_huggins/benchmark_blend.yaml
spec_ref: sha256:<spec335_hash>
principle_ref: sha256:<p335_hash>
dataset:
  name: symmetric_blend_analytic
  reference: "Flory (1953) analytic UCST phase diagram"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Analytic (Newton)
    params: {T_pts: 100}
    results: {phi_error: 0.0, UCST_error: 0.0}
  - solver: Numerical minimization
    params: {phi_pts: 1000}
    results: {phi_error: 1.2e-4, UCST_error: 0.1}
  - solver: SCFT
    params: {chain_contour: 100}
    results: {phi_error: 0.01, UCST_error: 2.0}
quality_scoring:
  - {min_phi_error: 1.0e-4, Q: 1.00}
  - {min_phi_error: 1.0e-3, Q: 0.90}
  - {min_phi_error: 1.0e-2, Q: 0.80}
  - {min_phi_error: 5.0e-2, Q: 0.75}
```

**Baseline solver:** Analytic (Newton) — exact
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | φ Error | UCST Error (K) | Runtime | Q |
|--------|---------|---------------|---------|---|
| SCFT | 0.01 | 2.0 | 30 s | 0.80 |
| Numerical min. | 1.2e-4 | 0.1 | 0.1 s | 1.00 |
| Analytic (Newton) | 0.0 | 0.0 | 0.01 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (analytic): 100 × 1.00 = 100 PWM
Floor:                100 × 0.75 =  75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p335_hash>",
  "h_s": "sha256:<spec335_hash>",
  "h_b": "sha256:<bench335_hash>",
  "r": {"residual_norm": 0.0, "error_bound": 1.0e-3, "ratio": 0.0},
  "c": {"fitted_rate": "exact", "theoretical_rate": "exact", "K": 3},
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
| L4 Solution | — | 75–100 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep flory_huggins
pwm-node verify flory_huggins/polymer_blend_s1_ideal.yaml
pwm-node mine flory_huggins/polymer_blend_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
