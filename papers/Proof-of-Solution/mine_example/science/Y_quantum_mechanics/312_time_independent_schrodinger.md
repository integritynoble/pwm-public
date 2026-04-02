# Principle #312 — Time-Independent Schrodinger Equation

**Domain:** Quantum Mechanics | **Carrier:** wavefunction | **Difficulty:** Textbook (δ=1)
**DAG:** E.hermitian → L.hamiltonian |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E.hermitian→L.hamiltonian   TISE-1D     hydrogen-atom     FEM/spectral
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  TIME-INDEPENDENT SCHRODINGER   P = (E,G,W,C)   Principle #312  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Hψ = Eψ                                                │
│        │ H = −(ℏ²/2m)∇² + V(r)                                 │
│        │ ψ = wavefunction, E = energy eigenvalue                │
│        │ Forward: given V(r), BC → solve for {Eₙ, ψₙ}          │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [E.hermitian] ──→ [L.hamiltonian]                      │
│        │ eigensolve  linear-op                                  │
│        │ V={E.hermitian, L.hamiltonian}  A={E.hermitian→L.hamiltonian}  L_DAG=1.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (self-adjoint H on L² has spectrum)     │
│        │ Uniqueness: YES (eigenvalues discrete for bound states)│
│        │ Stability: κ ~ gap⁻¹ (spectral gap controls sensitivity)│
│        │ Mismatch: potential perturbation, boundary truncation   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |E_num − E_exact|/|E_exact| (primary)             │
│        │ q = 2.0 (FEM-linear), 4.0+ (spectral)                │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Hamiltonian self-adjoint; boundary conditions well-defined | PASS |
| S2 | Discrete spectrum guaranteed for confining potentials | PASS |
| S3 | FEM and spectral methods converge for smooth potentials | PASS |
| S4 | Energy eigenvalue error bounded by variational principle | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# tise/hydrogen_s1_ideal.yaml
principle_ref: sha256:<p312_hash>
omega:
  grid: [512]
  domain: radial_0_to_50
  r_max: 50.0
E:
  forward: "Hψ = Eψ,  H = −(1/2)d²/dr² + l(l+1)/(2r²) − 1/r"
  potential: coulomb
B:
  r0: {psi: 0}
  r_max: {psi: 0}
I:
  scenario: hydrogen_1s_2s_3s
  Z: 1
  l_values: [0, 1, 2]
  n_max: 5
O: [eigenvalue_error, wavefunction_L2_error]
epsilon:
  eigenvalue_rel_max: 1.0e-8
  wfn_L2_max: 1.0e-6
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Grid 512 pts on [0,50] resolves hydrogen wavefunctions | PASS |
| S2 | Coulomb potential yields known analytic eigenvalues E_n = −1/(2n²) | PASS |
| S3 | Spectral/FEM converges exponentially for smooth ψ | PASS |
| S4 | Eigenvalue error < 10⁻⁸ achievable with 512 basis functions | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# tise/benchmark_hydrogen.yaml
spec_ref: sha256:<spec312_hash>
principle_ref: sha256:<p312_hash>
dataset:
  name: hydrogen_eigenvalues_exact
  reference: "Analytic: E_n = −Z²/(2n²) Hartree"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: FEM-linear
    params: {N: 256, r_max: 50}
    results: {eigenvalue_error: 3.2e-5, wfn_L2: 1.1e-3}
  - solver: B-spline (order 7)
    params: {N: 128, r_max: 50}
    results: {eigenvalue_error: 1.8e-8, wfn_L2: 4.5e-6}
  - solver: Spectral (Laguerre)
    params: {N: 64}
    results: {eigenvalue_error: 2.1e-12, wfn_L2: 8.3e-9}
quality_scoring:
  - {min_eigenvalue_error: 1.0e-10, Q: 1.00}
  - {min_eigenvalue_error: 1.0e-8, Q: 0.95}
  - {min_eigenvalue_error: 1.0e-6, Q: 0.85}
  - {min_eigenvalue_error: 1.0e-4, Q: 0.75}
```

**Baseline solver:** B-spline — eigenvalue error 1.8×10⁻⁸
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Eigenvalue Error | Wfn L2 | Runtime | Q |
|--------|-----------------|---------|---------|---|
| FEM-linear | 3.2e-5 | 1.1e-3 | 0.2 s | 0.75 |
| B-spline (order 7) | 1.8e-8 | 4.5e-6 | 0.5 s | 0.95 |
| Spectral (Laguerre) | 2.1e-12 | 8.3e-9 | 0.1 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (spectral): 100 × 1.00 = 100 PWM
Floor:                100 × 0.75 =  75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p312_hash>",
  "h_s": "sha256:<spec312_hash>",
  "h_b": "sha256:<bench312_hash>",
  "r": {"residual_norm": 2.1e-12, "error_bound": 1.0e-8, "ratio": 0.00021},
  "c": {"fitted_rate": 7.0, "theoretical_rate": 7.0, "K": 3},
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
pwm-node benchmarks | grep tise
pwm-node verify tise/hydrogen_s1_ideal.yaml
pwm-node mine tise/hydrogen_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
