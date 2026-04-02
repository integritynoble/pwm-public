# Principle #299 — Classical Molecular Dynamics (MD)

**Domain:** Computational Chemistry | **Carrier:** N/A (Newton's equations) | **Difficulty:** Standard (δ=3)
**DAG:** N.bilinear.pair → ∂.time.symplectic → ∫.ensemble |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.bilinear.pair→∂.time.symplectic→∫.ensemble      class-md    protein-fold      Verlet
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  CLASSICAL MOLECULAR DYNAMICS     P = (E,G,W,C)   Principle #299│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ m_i r̈_i = F_i = −∇_i U({r})  (Newton's 2nd law)      │
│        │ U = Σ_bonds + Σ_angles + Σ_dihedrals + Σ_LJ + Σ_Coul │
│        │ Forward: given force field + IC → trajectory {r(t)}    │
│        │ Observables: RDF, RMSD, diffusion, free energy         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.bilinear.pair] ──→ [∂.time.symplectic] ──→ [∫.ensemble] │
│        │ nonlinear  derivative  integrate                       │
│        │ V={N.bilinear.pair, ∂.time.symplectic, ∫.ensemble}  A={N.bilinear.pair→∂.time.symplectic, ∂.time.symplectic→∫.ensemble}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (ODE system well-posed)                │
│        │ Uniqueness: YES (deterministic for given IC)           │
│        │ Stability: Verlet is symplectic; energy conserved (NVE)│
│        │ Mismatch: force field parameterisation, fixed charges  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSD(structure), ΔG error, D error                │
│        │ q = 1.0 (linear scaling with cutoffs + PME)           │
│        │ T = {RMSD, RDF, diffusion_coeff, density}             │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Force field energy terms consistent; units correct | PASS |
| S2 | Velocity-Verlet symplectic; energy drift < 0.01 kJ/mol/ns | PASS |
| S3 | GROMACS/OpenMM reproduce experimental density of SPC/E water | PASS |
| S4 | Water density within 1% of experiment at 300 K, 1 atm | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# class_md/water_s1_ideal.yaml
principle_ref: sha256:<p299_hash>
omega:
  atoms: 30000  # 10000 water molecules
  box: [64.6, 64.6, 64.6]  # Angstrom
  time: 10.0  # ns
  dt: 2.0  # fs
E:
  forward: "velocity-Verlet with force field potential"
  force_field: TIP4P/2005
  cutoff: 10.0  # Angstrom
  PME: {grid_spacing: 1.2, order: 4}
B:
  ensemble: NPT
  thermostat: {type: v-rescale, tau: 0.5}  # ps
  barostat: {type: Parrinello-Rahman, tau: 2.0}
  PBC: true
I:
  scenario: bulk_water_300K_1atm
  reference_density: 0.997  # g/cm³
  reference_D: 2.3e-5  # cm²/s
O: [density_error, D_error, RDF_OO]
epsilon:
  density_error_max: 0.01  # g/cm³
  D_error_max: 0.5e-5  # cm²/s
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 10000 TIP4P/2005 waters; dt=2 fs with LINCS constraints | PASS |
| S2 | TIP4P/2005 reproduces density maximum and D within 5% | PASS |
| S3 | 10 ns NPT equilibrated trajectory gives converged averages | PASS |
| S4 | Density error < 0.01 g/cm³ achievable | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# class_md/benchmark_water.yaml
spec_ref: sha256:<spec299_hash>
principle_ref: sha256:<p299_hash>
dataset:
  name: bulk_water_TIP4P2005
  reference: "Abascal & Vega (2005) TIP4P/2005"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: GROMACS-VV
    params: {dt: 2fs, cutoff: 10A, PME: true}
    results: {density_err: 0.003, D_err: 0.2e-5}
  - solver: OpenMM-LangevinMiddle
    params: {dt: 2fs, cutoff: 10A, PME: true}
    results: {density_err: 0.004, D_err: 0.3e-5}
  - solver: LAMMPS-Verlet
    params: {dt: 2fs, cutoff: 10A, PPPM: true}
    results: {density_err: 0.003, D_err: 0.2e-5}
quality_scoring:
  - {min_dens_err: 0.001, Q: 1.00}
  - {min_dens_err: 0.003, Q: 0.90}
  - {min_dens_err: 0.010, Q: 0.80}
  - {min_dens_err: 0.020, Q: 0.75}
```

**Baseline solver:** GROMACS — density error 0.003 g/cm³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Density Err | D Error | Runtime | Q |
|--------|-------------|---------|---------|---|
| LAMMPS | 0.003 | 0.2e-5 | 30 min | 0.90 |
| GROMACS | 0.003 | 0.2e-5 | 20 min | 0.90 |
| OpenMM-GPU | 0.004 | 0.3e-5 | 5 min | 0.90 |
| OpenMM-GPU (long) | 0.001 | 0.1e-5 | 50 min | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (long GPU): 300 × 1.00 = 300 PWM
Floor:                300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p299_hash>",
  "h_s": "sha256:<spec299_hash>",
  "h_b": "sha256:<bench299_hash>",
  "r": {"residual_norm": 0.001, "error_bound": 0.01, "ratio": 0.10},
  "c": {"fitted_rate": 1.02, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep class_md
pwm-node verify class_md/water_s1_ideal.yaml
pwm-node mine class_md/water_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
