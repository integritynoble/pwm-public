# Principle #295 — Hartree-Fock Method

**Domain:** Computational Chemistry | **Carrier:** N/A (variational) | **Difficulty:** Standard (δ=3)
**DAG:** E.hermitian → L.dense → ∫.volume |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E.hermitian→L.dense→∫.volume      hf-scf      total-energy      SCF
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  HARTREE-FOCK METHOD              P = (E,G,W,C)   Principle #295│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ F φ_i = ε_i φ_i ;  F = h + Σ(2J_j − K_j)            │
│        │ E_HF = Σ h_ii + ½Σ(2J_ij − K_ij) + V_nn             │
│        │ Ψ = antisymmetrised product (Slater determinant)       │
│        │ Forward: given basis + geometry → E_HF, orbitals       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [E.hermitian] ──→ [L.dense] ──→ [∫.volume]             │
│        │ eigensolve  linear-op  integrate                       │
│        │ V={E.hermitian, L.dense, ∫.volume}  A={E.hermitian→L.dense, L.dense→∫.volume}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (variational minimum over Slater dets)  │
│        │ Uniqueness: YES for closed-shell RHF (Brillouin thm)   │
│        │ Stability: SCF convergence; DIIS accelerates           │
│        │ Mismatch: no electron correlation (Ecorr ~ 1% of Etot)│
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |E_HF − E_exact| / |E_exact|  (correlation energy)│
│        │ q = 3.0 (4-index integral, N⁴ formal scaling)        │
│        │ T = {total_energy, orbital_energies, dipole_moment}    │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Fock matrix Hermitian; basis orthogonalised; electron count conserved | PASS |
| S2 | Variational principle guarantees E_HF ≥ E_exact | PASS |
| S3 | SCF+DIIS converges in <50 cycles for closed-shell molecules | PASS |
| S4 | HF total energy within ~1% of exact; basis set limit known | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# hf_scf/energy_s1_ideal.yaml
principle_ref: sha256:<p295_hash>
omega:
  basis: cc-pVDZ
  method: RHF
  convergence: 1.0e-10  # Hartree
E:
  forward: "Roothaan-Hall SCF equations"
  integral_threshold: 1.0e-12
  max_cycles: 150
B:
  initial_guess: core_Hamiltonian
  DIIS: {start: 2, space: 8}
I:
  scenario: small_molecules_set
  molecules: [H2O, NH3, CH4, HF, CO, N2]
  reference: numerical_HF_limit
O: [total_energy_error, basis_set_error, SCF_cycles]
epsilon:
  energy_error_max: 1.0e-4  # Hartree
  SCF_cycles_max: 50
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | cc-pVDZ well-defined for first-row atoms; RHF appropriate | PASS |
| S2 | Numerical HF limit exists as reference for basis set error | PASS |
| S3 | DIIS-accelerated SCF converges in <30 cycles | PASS |
| S4 | Energy error < 10⁻⁴ Hartree at cc-pVDZ (basis set limited) | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# hf_scf/benchmark_small_mol.yaml
spec_ref: sha256:<spec295_hash>
principle_ref: sha256:<p295_hash>
dataset:
  name: small_molecules_HF_limit
  reference: "Numerical HF limit energies (Klopper 2001)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: RHF/STO-3G
    params: {basis: STO-3G}
    results: {MAE_mHa: 45.2, max_cycles: 15}
  - solver: RHF/cc-pVDZ
    params: {basis: cc-pVDZ}
    results: {MAE_mHa: 8.5, max_cycles: 22}
  - solver: RHF/cc-pVQZ
    params: {basis: cc-pVQZ}
    results: {MAE_mHa: 0.3, max_cycles: 28}
quality_scoring:
  - {min_MAE_mHa: 0.1, Q: 1.00}
  - {min_MAE_mHa: 1.0, Q: 0.90}
  - {min_MAE_mHa: 10.0, Q: 0.80}
  - {min_MAE_mHa: 50.0, Q: 0.75}
```

**Baseline solver:** RHF/cc-pVDZ — MAE 8.5 mHa
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | MAE (mHa) | Cycles | Runtime | Q |
|--------|-----------|--------|---------|---|
| RHF/STO-3G | 45.2 | 15 | 0.1 s | 0.75 |
| RHF/cc-pVDZ | 8.5 | 22 | 1 s | 0.80 |
| RHF/cc-pVTZ | 1.8 | 25 | 5 s | 0.90 |
| RHF/cc-pVQZ | 0.3 | 28 | 30 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (cc-pVQZ): 300 × 1.00 = 300 PWM
Floor:               300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p295_hash>",
  "h_s": "sha256:<spec295_hash>",
  "h_b": "sha256:<bench295_hash>",
  "r": {"residual_norm": 0.3, "error_bound": 10.0, "ratio": 0.03},
  "c": {"fitted_rate": 2.95, "theoretical_rate": 3.0, "K": 4},
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
pwm-node benchmarks | grep hf_scf
pwm-node verify hf_scf/energy_s1_ideal.yaml
pwm-node mine hf_scf/energy_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
