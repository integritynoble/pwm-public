# agent-chemistry: Execution Plan

Read `CLAUDE.md` first (your role, domain list, and full JSON schemas). This file is your step-by-step work order.

---

## Before You Start

- [ ] Read `CLAUDE.md` — all JSON field specs and the self-review checklist are there.
- [ ] Read `../../papers/Proof-of-Solution/mine_example/cassi.md` and `cacti.md` — completed reference examples.
- [ ] Read `../../papers/Proof-of-Solution/pwm_overview1.md` §Difficulty Score, §ρ Tier Mapping, §Track A/B/C.
- [ ] Look at existing completed artifacts for style reference:
  - `../../pwm_product/genesis/l1/L1-003.json` (CASSI L1)
  - `../../pwm_product/genesis/l2/L2-003.json` (CASSI L2)
  - `../../pwm_product/genesis/l3/L3-004.json` (CACTI L3)
- [ ] Source files are in `source/` (symlink to `pwm/papers/Proof-of-Solution/mine_example/science/`).

---

## Your Domains

| Domain | Source folder | Count | Output folder |
|---|---|---|---|
| Computational chemistry | X_computational_chemistry/ | ~18 | principles/X_computational_chemistry/ |
| Quantum mechanics | Y_quantum_mechanics/ | ~16 | principles/Y_quantum_mechanics/ |
| Materials science | Z_materials_science/ | ~14 | principles/Z_materials_science/ |
| Polymer science | AL_polymer_science/ | ~8 | principles/AL_polymer_science/ |
| Semiconductor physics | AN_semiconductor/ | ~8 | principles/AN_semiconductor/ |

**Total: ~64 principles**

---

## Batch Order (work in this order)

1. **AL_polymer_science** (~8 files) — start here, smallest cluster
2. **AN_semiconductor** (~8 files)
3. **Z_materials_science** (~14 files)
4. **Y_quantum_mechanics** (~16 files)
5. **X_computational_chemistry** (~18 files) — work in sub-batches of 6

---

## Per-Principle Process (repeat for every source file)

### Step A — Parse source .md → L1-NNN.json

- [ ] **A.1** Read source file. Extract:
  - `forward_model`: the governing equation (Schrödinger eq., DFT functional, force field, etc.)
  - `dag`: operator chain (e.g., `"A.hamiltonian → B.solve_eigenstates → C.compute_spectrum"`)
  - `world_state_x`: molecular geometry, electron density, atomic positions, wavefunction
  - `observation_y`: NMR spectrum, XRD pattern, absorption spectrum, binding energy
  - `physical_parameters_theta`: exchange-correlation functional, force field parameters, etc.
  - `mismatch_parameters`: which model parameters are uncertain
  - `well_posedness`: existence, uniqueness, stability, condition_number
  - `error_metric`: primary (e.g., `MAE_eV`, `RMSE_angstrom`, `spectral_distance`) and secondary
  - `convergence_rate_q`: 2.0 for FEM/basis set convergence; varies for iterative solvers
- [ ] **A.2** Assign `difficulty_delta`: Trivial→1, Standard→3, Challenging→5, Hard→10, Frontier→50
- [ ] **A.3** Write `principles/<domain>/L1-NNN.json`.
- [ ] **A.4** Validate: every required field present, typed correctly.

### Step B — Write L2-NNN.json (Spec)

- [ ] **B.1** Write at least one spec. Two specs preferred:
  - Spec 1: structure-to-property inversion (reconstruct molecular structure from spectrum)
  - Spec 2: parameter inversion (identify force field / exchange-correlation parameters)
- [ ] **B.2** Write `epsilon_fn` — calibrate so `d(Ω_centroid) ∈ [0.3, 0.7]`.
  - Chemistry note: error metrics vary (MAE in eV, spectral overlap, RMSE in Å). Ensure epsilon_fn units match error_metric.
- [ ] **B.3** Write S1-S4 gate justifications.
- [ ] **B.4** Test `epsilon_fn` evaluates without error for 10 random Ω samples.
- [ ] **B.5** Confirm `d_spec ≥ 0.35` from any other spec under same principle.
- [ ] **B.6** Write `principles/<domain>/L2-NNN.json`.

### Step C — Write L3-NNN.json (Benchmark)

- [ ] **C.1** Write 4 I-benchmark tiers (T1–T4):
  - T1 nominal: small molecule / simple system, ρ=1
  - T2 low: slightly larger system, ρ=3
  - T3 moderate: medium system (e.g., 50-atom cluster), ρ=5
  - T4 blind: large or complex system (e.g., protein fragment), ρ=10
- [ ] **C.2** Write P-benchmark: real experimental or high-quality DFT dataset:
  - Examples: QM9, Materials Project, NIST spectral library, Cambridge Structural Database
  - P-benchmark ρ=50; covers full Ω.
- [ ] **C.3** Write ≥ 2 baseline solvers:
  - Quantum chemistry: HF, DFT-B3LYP, PM6, XTBGFN2
  - Materials: classical FF, DFTB, ML-FF (SchNet, DimeNet)
- [ ] **C.4** Confirm tier spacing ≥10% in ≥1 Ω dimension.
- [ ] **C.5** Write `principles/<domain>/L3-NNN.json`.

### Step D — Self-Review Checklist

- [ ] epsilon_fn evaluates without error for 10 random Ω samples
- [ ] Hardness rule: no baseline passes epsilon_fn everywhere in Ω
- [ ] d_spec ≥ 0.35 from any other spec under same principle
- [ ] I-benchmark tiers: each omega_tier differs ≥10% in ≥1 Ω dimension
- [ ] All JSON fields present and typed correctly
- [ ] forward_model in L1 matches E.forward in L2
- [ ] difficulty_delta consistent with system complexity

---

## Chemistry-Specific Notes

- **Computational chemistry**: inverse problems are often structure determination from spectra. Non-uniqueness is common (δ≥5 typical).
- **Quantum mechanics**: wavefunction reconstruction from measurements is Challenging to Frontier. Decoherence makes it Hard.
- **Materials science**: crystal structure inversion from XRD. Phase ambiguity → Hard (δ=10).
- **Polymer science**: chain structure from rheology or NMR. Often Standard-Challenging.
- **Semiconductors**: band structure from transport measurements. Inverse doping problems are Challenging.

---

## Progress Tracking

After completing each domain, update `../../coordination/agent-coord/progress.md`:

```
| agent-chemistry | X_computational_chemistry | 0/18 | IN_PROGRESS |
| agent-chemistry | AL_polymer_science         | 8/8  | DONE |
```

---

## Final Step — Signal Completion

- [ ] All ~64 principles have L1, L2, L3 JSON in `principles/<domain>/`.
- [ ] All JSONs pass schema validation.
- [ ] Self-review checklist passes for all.
- [ ] Update `../../coordination/agent-coord/progress.md` — mark chemistry principles `DONE`.
- [ ] Open PR: `feat/genesis-principles-chemistry`
  - PR description: count per domain, any quantum/Frontier principles flagged for review
