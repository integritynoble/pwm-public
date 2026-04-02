# Principle #323 — Exact Diagonalization

**Domain:** Quantum Mechanics | **Carrier:** many-body state | **Difficulty:** Standard (δ=3)
**DAG:** L.hamiltonian → E.hermitian |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.hamiltonian→E.hermitian     exact-diag  Hubbard-small      Lanczos
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  EXACT DIAGONALIZATION          P = (E,G,W,C)   Principle #323  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ H|ψₙ⟩ = Eₙ|ψₙ⟩  (full spectrum)                     │
│        │ dim(H) = C(N_sites, N_up) × C(N_sites, N_down)        │
│        │ Lanczos: iterative for ground state / low-lying states │
│        │ Forward: given H_matrix → compute {Eₙ, |ψₙ⟩}         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.hamiltonian] ──→ [E.hermitian]                      │
│        │ linear-op  eigensolve                                  │
│        │ V={L.hamiltonian, E.hermitian}  A={L.hamiltonian→E.hermitian}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (finite Hermitian matrix)               │
│        │ Uniqueness: YES (eigenvalues unique; eigenvectors up to phase)│
│        │ Stability: exact within floating-point arithmetic      │
│        │ Mismatch: finite-size effects only (no approximation)  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |E_num − E_exact|/|E_exact| (primary)             │
│        │ q = exact (limited by machine precision ~10⁻¹⁵)      │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Hilbert space dimension computable; symmetry sectors well-defined | PASS |
| S2 | Hermitian matrix diagonalization always yields real eigenvalues | PASS |
| S3 | Lanczos converges to extremal eigenvalues in O(dim) iterations | PASS |
| S4 | Energy error bounded by machine precision for exact method | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# exact_diag/hubbard_4x4_s1_ideal.yaml
principle_ref: sha256:<p323_hash>
omega:
  lattice: [4, 4]
  N_up: 8
  N_down: 8
  dim: 165636900  # full Hilbert space
E:
  forward: "H = −t Σ c†c + U Σ n↑n↓, Lanczos diag"
  model: Hubbard
B:
  boundary: periodic
I:
  scenario: half_filled_Hubbard
  t: 1.0
  U: 4.0
O: [ground_state_energy, spin_gap, charge_gap]
epsilon:
  energy_error_max: 1.0e-10
  lanczos_tol: 1.0e-12
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Hilbert-space dimension fits in memory with symmetries | PASS |
| S2 | Hermitian Hubbard Hamiltonian has real spectrum | PASS |
| S3 | Lanczos converges to ground state within tolerance | PASS |
| S4 | Energy error < 10⁻¹⁰ achievable with Lanczos | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# exact_diag/benchmark_hubbard.yaml
spec_ref: sha256:<spec323_hash>
principle_ref: sha256:<p323_hash>
dataset:
  name: hubbard_4x4_reference
  reference: "ED benchmark results from literature"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Full diag (LAPACK)
    params: {lattice: [4,2], N_up: 4, N_down: 4}
    results: {energy_error: 0.0, time: 120}
  - solver: Lanczos
    params: {lattice: [4,4], N_up: 8, N_down: 8, n_iter: 200}
    results: {energy_error: 1.2e-12, time: 3600}
  - solver: Lanczos + symmetry
    params: {lattice: [4,4], symmetries: [translation, spin]}
    results: {energy_error: 5.1e-13, time: 900}
quality_scoring:
  - {min_energy_error: 1.0e-12, Q: 1.00}
  - {min_energy_error: 1.0e-10, Q: 0.95}
  - {min_energy_error: 1.0e-8, Q: 0.85}
  - {min_energy_error: 1.0e-6, Q: 0.75}
```

**Baseline solver:** Lanczos + symmetry — energy error 5.1×10⁻¹³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Energy Error | Runtime | Q |
|--------|-------------|---------|---|
| Full diag (4×2) | 0.0 | 120 s | 1.00 |
| Lanczos (4×4) | 1.2e-12 | 3600 s | 1.00 |
| Lanczos + sym (4×4) | 5.1e-13 | 900 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (Lanczos+sym): 300 × 1.00 = 300 PWM
Floor:                   300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p323_hash>",
  "h_s": "sha256:<spec323_hash>",
  "h_b": "sha256:<bench323_hash>",
  "r": {"residual_norm": 5.1e-13, "error_bound": 1.0e-10, "ratio": 0.0051},
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
| L4 Solution | — | 225–300 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep exact_diag
pwm-node verify exact_diag/hubbard_4x4_s1_ideal.yaml
pwm-node mine exact_diag/hubbard_4x4_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
