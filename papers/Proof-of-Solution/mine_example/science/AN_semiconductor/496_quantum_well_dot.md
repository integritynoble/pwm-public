# Principle #496 — Quantum Well / Dot Energy Levels

**Domain:** Semiconductor Physics | **Carrier:** N/A (eigenvalue) | **Difficulty:** Standard (δ=3)
**DAG:** [L.sparse] --> [E.hermitian] --> [∫.volume] | **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          L.sparse-->E.herm-->∫.vol  QW-QD  GaAs/AlGaAs  Schrodinger
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  QUANTUM WELL / DOT ENERGY LEVELS P=(E,G,W,C) Principle #496   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ [−ℏ²/(2m*(z)) d²/dz² + V(z)] ψ_n = E_n ψ_n (1D QW)  │
│        │ V(z) = 0 in well, V₀ in barrier (finite well)         │
│        │ QD: 3D confinement → discrete spectrum E_{n,l,m}      │
│        │ Strained QW: m* → m*(ε), V → V(ε)  (deformation pot.)│
│        │ Forward: given well structure → E_n, ψ_n, DOS         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [L.sparse] ──→ [E.herm] ──→ [∫.vol]                    │
│        │  potential  eigensolver  confinement-integ             │
│        │ V={L.sparse,E.herm,∫.vol}  A={L.sparse→E.herm,E.herm→∫.vol}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (self-adjoint H → real eigenvalues)     │
│        │ Uniqueness: YES (eigenvalues discrete and ordered)     │
│        │ Stability: perturbation theory bounds δE ≤ ‖δV‖       │
│        │ Mismatch: effective mass approx, non-parabolicity      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |E_n_calc − E_n_ref|/E_n_ref  (energy error)      │
│        │ q = 2.0 (FD), spectral for smooth V                  │
│        │ T = {energy_error, wavefunction_overlap, transition_E} │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Hamiltonian self-adjoint; energy E_n real and positive above ground | PASS |
| S2 | Finite well has finite number of bound states; well-posed | PASS |
| S3 | FD eigenvalue solver / shooting method converges | PASS |
| S4 | Energy levels within 1 meV of analytical (infinite well limit) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# qw_qd/gaas_algaas_s1.yaml
principle_ref: sha256:<p496_hash>
omega:
  grid: 500
  domain: GaAs_AlGaAs_single_QW
  well_width: 10e-9    # m
E:
  forward: "1D Schrodinger with position-dependent m*(z)"
  materials: {well: GaAs, barrier: Al0.3Ga0.7As}
  V_offset: 0.228      # eV (conduction band)
  m_well: 0.067        # m₀
  m_barrier: 0.092
B:
  boundary: decaying_in_barrier
  n_states: 5
I:
  scenario: GaAs_AlGaAs_quantum_well
  well_widths: [3, 5, 8, 10, 15, 20]   # nm
O: [energy_levels, transition_energies, oscillator_strengths]
epsilon:
  energy_error_max: 1.0    # meV
  transition_error_max: 2.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 500 grid points resolve 10 nm well; 5 bound states | PASS |
| S2 | GaAs/AlGaAs 30% well-characterized; V₀ = 228 meV | PASS |
| S3 | FD eigensolver converges for all well widths | PASS |
| S4 | Energy levels within 1 meV of transfer matrix solution | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# qw_qd/benchmark_gaas.yaml
spec_ref: sha256:<spec496_hash>
principle_ref: sha256:<p496_hash>
dataset:
  name: GaAs_QW_PL_spectroscopy
  reference: "Bastard (1988) Wave Mechanics Applied to Semiconductor Heterostructures"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Infinite well (analytical)
    params: {model: infinite_well}
    results: {energy_error_meV: 15.0, transition_error: 25.0}
  - solver: Finite well (transfer matrix)
    params: {model: transfer_matrix}
    results: {energy_error_meV: 0.5, transition_error: 1.0}
  - solver: k·p (8-band)
    params: {bands: 8, strain: none}
    results: {energy_error_meV: 0.2, transition_error: 0.5}
quality_scoring:
  - {min_meV: 0.1, Q: 1.00}
  - {min_meV: 0.5, Q: 0.90}
  - {min_meV: 2.0, Q: 0.80}
  - {min_meV: 10.0, Q: 0.75}
```

**Baseline solver:** Transfer matrix — energy error 0.5 meV
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Energy Error (meV) | Transition Error | Runtime | Q |
|--------|-------------------|-----------------|---------|---|
| Infinite well | 15.0 | 25.0 | 0.001 s | 0.75 |
| Transfer matrix | 0.5 | 1.0 | 0.01 s | 0.90 |
| k·p 8-band | 0.2 | 0.5 | 1.0 s | 0.90 |
| k·p + strain + SO | 0.08 | 0.15 | 10 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (k·p full): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p496_hash>",
  "h_s": "sha256:<spec496_hash>",
  "h_b": "sha256:<bench496_hash>",
  "r": {"energy_error_meV": 0.08, "error_bound": 1.0, "ratio": 0.080},
  "c": {"transition_error": 0.15, "well_widths": 6, "K": 6},
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
pwm-node benchmarks | grep qw_qd
pwm-node verify qw_qd/gaas_algaas_s1.yaml
pwm-node mine qw_qd/gaas_algaas_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
