# Principle #297 — Time-Dependent DFT (TD-DFT)

**Domain:** Computational Chemistry | **Carrier:** N/A (linear response) | **Difficulty:** Hard (δ=5)
**DAG:** ∂.time → E.hermitian → N.xc |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ρ₀→K→Ω→S    tddft       excitations       Casida
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  TIME-DEPENDENT DFT (TD-DFT)      P = (E,G,W,C)   Principle #297│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ [A  B][X] = ω[1  0 ][X]  (Casida equation)            │
│        │ [B  A][Y]    [0 −1][Y]                                 │
│        │ A_ia,jb = δ_ij δ_ab (ε_a−ε_i) + (ia|jb) + (ia|f_xc|jb)│
│        │ Forward: given ground-state KS → excitation energies ω │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [E.hermitian] ──→ [N.xc]                  │
│        │ derivative  eigensolve  nonlinear                      │
│        │ V={∂.time, E.hermitian, N.xc}  A={∂.time→E.hermitian, E.hermitian→N.xc}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Runge-Gross theorem)                   │
│        │ Uniqueness: YES for given v_ext(t) and initial state   │
│        │ Stability: adiabatic approximation limits accuracy      │
│        │ Mismatch: charge-transfer states, double excitations   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |ω_TDDFT − ω_ref| (eV, excitation energy error)   │
│        │ q = 3.0 (same scaling as ground-state DFT)            │
│        │ T = {excitation_energy, oscillator_strength, character} │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Casida matrix Hermitian; excitation energies real and positive | PASS |
| S2 | Runge-Gross theorem guarantees well-defined response | PASS |
| S3 | Davidson diagonalisation converges for lowest 10 roots | PASS |
| S4 | Valence excitation MAE < 0.3 eV for B3LYP on organic dyes | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# tddft/excitations_s1_ideal.yaml
principle_ref: sha256:<p297_hash>
omega:
  basis: 6-31+G(d)
  functional: B3LYP
  nroots: 10
E:
  forward: "Casida linear response equations"
  convergence: 1.0e-6  # eV
  max_davidson: 100
B:
  ground_state: converged_SCF
  TDA: false  # full TD-DFT
I:
  scenario: Thiel_benchmark_set
  molecules: 28
  reference: CC3/aug-cc-pVTZ
O: [MAE_eV, max_error_eV, oscillator_strength_corr]
epsilon:
  MAE_max: 0.30  # eV
  max_error_max: 0.80
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 6-31+G(d) includes diffuse functions for Rydberg states | PASS |
| S2 | B3LYP response well-defined for valence excitations | PASS |
| S3 | Davidson solver converges for 10 roots in <60 iterations | PASS |
| S4 | MAE < 0.3 eV for Thiel set with B3LYP | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# tddft/benchmark_thiel.yaml
spec_ref: sha256:<spec297_hash>
principle_ref: sha256:<p297_hash>
dataset:
  name: Thiel_benchmark_28
  reference: "Schreiber et al. (2008) Thiel benchmark"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: TD-LDA
    params: {basis: 6-31+G(d)}
    results: {MAE: 0.52, max_error: 1.20}
  - solver: TD-B3LYP
    params: {basis: 6-31+G(d)}
    results: {MAE: 0.28, max_error: 0.75}
  - solver: TD-CAM-B3LYP
    params: {basis: 6-31+G(d)}
    results: {MAE: 0.22, max_error: 0.55}
quality_scoring:
  - {min_MAE: 0.10, Q: 1.00}
  - {min_MAE: 0.25, Q: 0.90}
  - {min_MAE: 0.40, Q: 0.80}
  - {min_MAE: 0.60, Q: 0.75}
```

**Baseline solver:** TD-B3LYP — MAE 0.28 eV
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | MAE (eV) | Max Error (eV) | Runtime | Q |
|--------|----------|----------------|---------|---|
| TD-LDA | 0.52 | 1.20 | 5 s | 0.75 |
| TD-B3LYP | 0.28 | 0.75 | 10 s | 0.90 |
| TD-CAM-B3LYP | 0.22 | 0.55 | 12 s | 0.90 |
| TD-ωB97X-D/aug-TZ | 0.08 | 0.25 | 60 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (ωB97X-D): 500 × 1.00 = 500 PWM
Floor:               500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p297_hash>",
  "h_s": "sha256:<spec297_hash>",
  "h_b": "sha256:<bench297_hash>",
  "r": {"residual_norm": 0.08, "error_bound": 0.30, "ratio": 0.27},
  "c": {"fitted_rate": 2.98, "theoretical_rate": 3.0, "K": 4},
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
pwm-node benchmarks | grep tddft
pwm-node verify tddft/excitations_s1_ideal.yaml
pwm-node mine tddft/excitations_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
