# agent-physics: Execution Plan

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
| Fluid dynamics | R_fluid_dynamics/ | ~25 | principles/R_fluid_dynamics/ |
| Heat transfer | S_heat_transfer/ | ~18 | principles/S_heat_transfer/ |
| Structural mechanics | T_structural_mechanics/ | ~20 | principles/T_structural_mechanics/ |
| Electromagnetics | U_electromagnetics/ | ~22 | principles/U_electromagnetics/ |
| Acoustics | V_acoustics/ | ~15 | principles/V_acoustics/ |
| Geophysics | W_geophysics/ | ~20 | principles/W_geophysics/ |
| Plasma physics | AA_plasma_physics/ | ~18 | principles/AA_plasma_physics/ |
| Nuclear/radiation | AB_nuclear_radiation/ | ~9 | principles/AB_nuclear_radiation/ |

**Total: ~147 principles**

---

## Batch Order (work in this order)

1. **V_acoustics** (~15 files) — start here, well-defined inverse problems
2. **S_heat_transfer** (~18 files)
3. **AB_nuclear_radiation** (~9 files)
4. **U_electromagnetics** (~22 files) — work in sub-batches of 8
5. **T_structural_mechanics** (~20 files)
6. **W_geophysics** (~20 files)
7. **AA_plasma_physics** (~18 files)
8. **R_fluid_dynamics** (~25 files) — work in sub-batches of 8

---

## Per-Principle Process (repeat for every source file)

### Step A — Parse source .md → L1-NNN.json

- [ ] **A.1** Read source file. Extract:
  - `P = (E, G, W, C)` quadruple explicitly:
    - `E` (forward model): PDE or governing equation (e.g., `∂u/∂t = ν∇²u + f`)
    - `G` (DAG): operator chain (e.g., `"A.discretize → B.time_integrate → C.measure"`)
    - `W` (well-posedness): existence, uniqueness, stability, condition_number
    - `C` (convergence): solver_class, convergence_rate_q (2.0 for FEM/FDM; 1.0 for some spectral methods), error_bound, complexity
  - `world_state_x`: physical field being reconstructed (velocity, temperature, displacement, etc.)
  - `observation_y`: sensor readings (pressure, temperature probes, seismic traces, etc.)
  - `physical_parameters_theta`: viscosity, density, conductivity, etc.
  - `mismatch_parameters`: which physical constants are uncertain
  - `error_metric`: primary (e.g., `RMSE`, `relative_L2`) and secondary
  - `physics_fingerprint` block (all 7 fields):
    - `carrier`, `sensing_mechanism`, `integration_axis`, `problem_class`, `noise_model`, `solution_space`, `primitives`
  - `spec_range` block:
    - `center_spec`, `allowed_forward_operators`, `allowed_problem_classes`, `allowed_omega_dimensions`, `omega_bounds`, `epsilon_bounds`
- [ ] **A.2** Assign `difficulty_delta`: Trivial→1, Standard→3, Challenging→5, Hard→10, Frontier→50
- [ ] **A.3** Write `principles/<domain>/L1-NNN.json`.
- [ ] **A.4** Validate: every required field present, typed correctly.

### Step B — Write L2-NNN.json (Spec)

- [ ] **B.1** Write at least one spec. Two specs preferred:
  - Spec 1: mismatch-only (Ω covers uncertain physical parameters)
  - Spec 2: oracle-assisted (true parameter values provided, focus on reconstruction)
- [ ] **B.2** Write `epsilon_fn` — calibrate so `d(Ω_centroid) ∈ [0.3, 0.7]`.
  - Physics note: for fluid/heat problems, error is often relative_L2 not PSNR.
    Use `epsilon_fn` units consistent with your `error_metric`.
- [ ] **B.3** Write S1-S4 gate justifications.
- [ ] **B.4** Test `epsilon_fn` evaluates without error for 10 random Ω samples.
- [ ] **B.5** Include `ibenchmark_range` (center_ibenchmark, tier_bounds).
- [ ] **B.6** Confirm `d_spec >= 0.15` from any other spec under same principle.
- [ ] **B.7** Write `principles/<domain>/L2-NNN.json`.

### Step C — Write L3-NNN.json (Benchmark)

- [ ] **C.1** Write 4 I-benchmark tiers (T1–T4):
  - T1 nominal: Ω_centroid, ρ=1 (d<0.2)
  - T2 low: easy regime (coarse mesh, low Reynolds/Rayleigh number), ρ=3
  - T3 moderate: mid regime, ρ=5
  - T4 blind: hard regime (fine mesh, turbulent/high-Ra), ρ=10
- [ ] **C.2** Write P-benchmark: real simulation data (OpenFOAM, FEniCS, etc.) or experimental dataset.
  - P-benchmark ρ=50; covers full Ω including turbulent / high-mismatch regime.
- [ ] **C.3** Write ≥ 2 baseline solvers:
  - Standard physics solvers: FEM, FDM, spectral methods
  - Data-driven baselines where applicable (PINN, FNO)
- [ ] **C.4** Confirm tier spacing ≥10% in ≥1 Ω dimension.
- [ ] **C.5** Confirm `d_ibench >= 0.10` from existing I-benchmarks in same spec.
- [ ] **C.6** Write `principles/<domain>/L3-NNN.json`.

### Step D — Self-Review Checklist

- [ ] P = (E, G, W, C) quadruple complete with all certificates
- [ ] physics_fingerprint block complete (all 7 fields)
- [ ] spec_range and ibenchmark_range blocks complete
- [ ] epsilon_fn evaluates without error for 10 random Ω samples
- [ ] Hardness rule: no baseline passes epsilon_fn everywhere in Ω
- [ ] d_spec >= 0.15 from any other spec under same principle
- [ ] d_ibench >= 0.10 from existing I-benchmarks in same spec
- [ ] I-benchmark tiers: each omega_tier differs ≥10% in ≥1 Ω dimension
- [ ] All JSON fields present and typed correctly
- [ ] forward_model in L1 matches E.forward in L2
- [ ] difficulty_delta consistent with PDE complexity
- [ ] P1-P10 physics validity tests all PASS

---

## Physics-Specific Notes

- **Fluid dynamics**: inverse problems include flow field reconstruction from sparse probes, turbulence parameter estimation. Many are Challenging (δ=5) or Hard (δ=10) due to chaotic sensitivity.
- **Heat transfer**: conductivity inversion, source localization. Often Standard (δ=3). Well-posed with unique solutions.
- **Electromagnetics**: Maxwell inversion (tomography, antenna arrays). Condition number can be extreme.
- **Geophysics**: seismic inversion is a classic Frontier (δ=50) problem — highly non-unique.
- **Plasma physics**: parameter estimation from spectroscopy. Note non-LTE regimes for Hard tier.

---

## Progress Tracking

After completing each domain, update `../../coordination/agent-coord/progress.md`:

```
| agent-physics | R_fluid_dynamics     | 0/25 | IN_PROGRESS |
| agent-physics | S_heat_transfer      | 18/18 | DONE |
```

---

## Final Step — Signal Completion

- [ ] All ~147 principles have L1, L2, L3 JSON in `principles/<domain>/`.
- [ ] All JSONs pass schema validation.
- [ ] Self-review checklist passes for all.
- [ ] Update `../../coordination/agent-coord/progress.md` — mark physics principles `DONE`.
- [ ] Open PR: `feat/genesis-principles-physics`
  - PR description: count per domain, any Frontier (δ=50) principles flagged for extra review
