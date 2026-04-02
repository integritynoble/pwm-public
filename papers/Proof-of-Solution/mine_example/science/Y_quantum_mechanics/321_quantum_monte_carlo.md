# Principle #321 — Quantum Monte Carlo (VMC/DMC)

**Domain:** Quantum Mechanics | **Carrier:** many-body wavefunction | **Difficulty:** Frontier (δ=7)
**DAG:** S.random → E.hermitian → ∫.stochastic |  **Reward:** 7× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          Ψ→W→E_L→⟨E⟩ QMC-energy  He/Be-atom        VMC/DMC
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  QUANTUM MONTE CARLO (VMC/DMC)  P = (E,G,W,C)   Principle #321 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ VMC: E_VMC = ⟨Ψ_T|H|Ψ_T⟩/⟨Ψ_T|Ψ_T⟩                 │
│        │ DMC: ∂f/∂τ = (D∇² − [E_L−E_T])f, f=Ψ_TΦ_0            │
│        │ E_L(R) = Ψ_T⁻¹HΨ_T  (local energy)                   │
│        │ Forward: given H, Ψ_T → sample E_L → ⟨E⟩ ± σ/√N      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [Ψ_T] ──→ [W] ──→ [E_L] ──→ [⟨E⟩] ──→ [Ψ_T]        │
│        │ trial-wfn  walk  local-energy  average  optimize       │
│        │ V={Ψ_T,W,E_L,⟨E⟩}  A={Ψ_T→W,W→E_L,E_L→⟨E⟩,⟨E⟩→Ψ_T}│
│        │ L_DAG=7.0                                              │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (DMC projects exact ground state)       │
│        │ Uniqueness: YES (up to fixed-node approximation)       │
│        │ Stability: variance of E_L measures trial wfn quality  │
│        │ Mismatch: fixed-node bias, time-step error, population │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |E_QMC − E_exact|/|E_exact| (primary)             │
│        │ q = O(1/√N) statistical; fixed-node systematic       │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Hamiltonian and trial wavefunction dimensions consistent | PASS |
| S2 | DMC projects to exact ground state within fixed-node constraint | PASS |
| S3 | VMC/DMC converge as 1/√N with walker count | PASS |
| S4 | Total energy error bounded by variance + fixed-node bias | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# qmc/he_atom_s1_ideal.yaml
principle_ref: sha256:<p321_hash>
omega:
  walkers: 1000
  steps: 100000
  dt: 0.01  # Hartree⁻¹
E:
  forward: "DMC: project Ψ_T onto Φ_0 by imaginary-time diffusion"
  trial_wfn: Slater-Jastrow
B:
  electrons: 2
  nucleus: {Z: 2}
I:
  scenario: helium_ground_state
  E_exact: -2.903724  # Hartree
O: [total_energy, variance, acceptance_ratio]
epsilon:
  energy_error_max: 1.0e-4  # Hartree
  variance_max: 0.01
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 1000 walkers and 100k steps give adequate statistics | PASS |
| S2 | He exact energy known to 10⁻⁶ Hartree precision | PASS |
| S3 | DMC converges as 1/√(walkers×steps) | PASS |
| S4 | Energy error < 10⁻⁴ Hartree achievable with good trial wfn | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# qmc/benchmark_helium.yaml
spec_ref: sha256:<spec321_hash>
principle_ref: sha256:<p321_hash>
dataset:
  name: helium_exact_energy
  reference: "Pekeris (1959): E = −2.903724377 Hartree"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: VMC (Slater-Jastrow)
    params: {walkers: 1000, steps: 50000}
    results: {energy_error: 5.2e-3, variance: 0.03}
  - solver: DMC (Slater-Jastrow)
    params: {walkers: 1000, steps: 100000, dt: 0.01}
    results: {energy_error: 8.1e-5, variance: 0.005}
  - solver: DMC (optimized Jastrow)
    params: {walkers: 2000, steps: 200000, dt: 0.005}
    results: {energy_error: 1.2e-5, variance: 0.001}
quality_scoring:
  - {min_energy_error: 1.0e-5, Q: 1.00}
  - {min_energy_error: 1.0e-4, Q: 0.90}
  - {min_energy_error: 1.0e-3, Q: 0.80}
  - {min_energy_error: 1.0e-2, Q: 0.75}
```

**Baseline solver:** DMC (Slater-Jastrow) — energy error 8.1×10⁻⁵ Hartree
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Energy Error (Ha) | Variance | Runtime | Q |
|--------|------------------|----------|---------|---|
| VMC (SJ) | 5.2e-3 | 0.03 | 5 min | 0.80 |
| DMC (SJ) | 8.1e-5 | 0.005 | 30 min | 0.90 |
| DMC (opt. Jastrow) | 1.2e-5 | 0.001 | 2 h | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 7 × 1.0 × Q
Best case (DMC opt.): 700 × 1.00 = 700 PWM
Floor:                700 × 0.75 = 525 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p321_hash>",
  "h_s": "sha256:<spec321_hash>",
  "h_b": "sha256:<bench321_hash>",
  "r": {"residual_norm": 1.2e-5, "error_bound": 1.0e-4, "ratio": 0.12},
  "c": {"fitted_rate": 0.5, "theoretical_rate": 0.5, "K": 4},
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
| L4 Solution | — | 525–700 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep qmc
pwm-node verify qmc/he_atom_s1_ideal.yaml
pwm-node mine qmc/he_atom_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
