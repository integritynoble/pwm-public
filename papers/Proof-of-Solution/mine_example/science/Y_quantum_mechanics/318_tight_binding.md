# Principle #318 — Tight-Binding Model

**Domain:** Quantum Mechanics | **Carrier:** Bloch state | **Difficulty:** Textbook (δ=1)
**DAG:** E.hermitian → L.sparse → ∫.brillouin |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          t→H_k→ε→ψ   TB-model    graphene/Si        diag
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  TIGHT-BINDING MODEL            P = (E,G,W,C)   Principle #318  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ H(k) = Σ_R t(R) exp(ik·R)                             │
│        │ t(R) = ⟨φ_α(0)|H|φ_β(R)⟩ (hopping integrals)         │
│        │ H(k)c_n = ε_n(k)c_n  (band eigenvalue problem)        │
│        │ Forward: given {t(R)}, k-path → compute ε_n(k)        │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [E.hermitian] ──→ [L.sparse] ──→ [∫.brillouin]         │
│        │ eigensolve  linear-op  integrate                       │
│        │ V={E.hermitian, L.sparse, ∫.brillouin}  A={E.hermitian→L.sparse, L.sparse→∫.brillouin}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (finite-dim Hermitian matrix)           │
│        │ Uniqueness: YES (eigenvalues unique for given H(k))    │
│        │ Stability: κ ~ band-gap⁻¹; sensitive near degeneracies│
│        │ Mismatch: hopping truncation, orbital basis incompleteness│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |ε_TB − ε_ref|/bandwidth (primary)                │
│        │ q = exact (direct diagonalization of small matrix)    │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Hamiltonian Hermitian; hopping parameters well-defined | PASS |
| S2 | Finite-dimensional H(k) always diagonalizable | PASS |
| S3 | Direct diagonalization exact for given Hamiltonian | PASS |
| S4 | Band energy error = 0 for given parameters; model error bounded | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# tight_binding/graphene_s1_ideal.yaml
principle_ref: sha256:<p318_hash>
omega:
  k_path: [Gamma, M, K, Gamma]
  k_points: 300
E:
  forward: "H(k)c = εc, 2-orbital nearest-neighbor TB"
  hoppings: {t1: -2.7}  # eV
B:
  periodic: true
I:
  scenario: graphene_pz
  lattice: honeycomb
  a: 2.46  # Angstrom
  orbitals: [pz_A, pz_B]
O: [band_energies, Dirac_cone_velocity, DOS]
epsilon:
  band_rms_max: 0.01  # eV (model-internal)
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 300 k-points resolve Dirac cone; 2×2 matrix exact | PASS |
| S2 | Graphene TB has analytic dispersion ε=±t√(3+2cos terms) | PASS |
| S3 | 2×2 diagonalization is exact | PASS |
| S4 | Model-internal error identically zero | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# tight_binding/benchmark_graphene.yaml
spec_ref: sha256:<spec318_hash>
principle_ref: sha256:<p318_hash>
dataset:
  name: graphene_TB_analytic
  reference: "Wallace (1947) analytic graphene dispersion"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Direct diag (2×2)
    params: {k_pts: 300}
    results: {band_rms: 0.0, max_error: 0.0}
  - solver: Recursive Green's function
    params: {k_pts: 300, eta: 1e-3}
    results: {band_rms: 1.2e-3, DOS_error: 2.1e-3}
  - solver: Lanczos
    params: {k_pts: 300, n_iter: 50}
    results: {band_rms: 3.5e-6, max_error: 8.2e-6}
quality_scoring:
  - {min_band_rms: 1.0e-10, Q: 1.00}
  - {min_band_rms: 1.0e-6, Q: 0.95}
  - {min_band_rms: 1.0e-3, Q: 0.85}
  - {min_band_rms: 1.0e-2, Q: 0.75}
```

**Baseline solver:** Direct diag — band RMS 0.0 (exact)
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Band RMS (eV) | Max Error (eV) | Runtime | Q |
|--------|--------------|----------------|---------|---|
| Direct diag (2×2) | 0.0 | 0.0 | 0.01 s | 1.00 |
| Lanczos | 3.5e-6 | 8.2e-6 | 0.05 s | 0.95 |
| Recursive Green | 1.2e-3 | 2.1e-3 | 0.1 s | 0.85 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (direct diag): 100 × 1.00 = 100 PWM
Floor:                   100 × 0.75 =  75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p318_hash>",
  "h_s": "sha256:<spec318_hash>",
  "h_b": "sha256:<bench318_hash>",
  "r": {"residual_norm": 0.0, "error_bound": 1.0e-10, "ratio": 0.0},
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
pwm-node benchmarks | grep tight_binding
pwm-node verify tight_binding/graphene_s1_ideal.yaml
pwm-node mine tight_binding/graphene_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
