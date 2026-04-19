# agent-applied: Execution Plan

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
| Astronomy | Q_astronomy/ | 4 | principles/Q_astronomy/ |
| Astrophysics | AC_astrophysics/ | 18 | principles/AC_astrophysics/ |
| Computational biology | AE_computational_bio/ | 18 | principles/AE_computational_bio/ |
| Environmental science | AF_environmental_sci/ | 12 | principles/AF_environmental_sci/ |
| Control theory | AG_control_theory/ | 12 | principles/AG_control_theory/ |
| Computational finance | AH_comp_finance/ | 8 | principles/AH_comp_finance/ |
| Robotics | AI_robotics/ | 12 | principles/AI_robotics/ |
| Petroleum engineering | AJ_petroleum/ | 8 | principles/AJ_petroleum/ |
| Geodesy | AK_geodesy/ | 8 | principles/AK_geodesy/ |
| Particle physics | AM_particle_physics/ | 8 | principles/AM_particle_physics/ |
| Optimization | AO_optimization/ | 3 | principles/AO_optimization/ |

**Total: ~111 principles**

---

## Batch Order (work in this order)

1. **AO_optimization** (3 files) — start here, smallest
2. **Q_astronomy** (4 files)
3. **AK_geodesy** (8 files)
4. **AH_comp_finance** (8 files)
5. **AJ_petroleum** (8 files)
6. **AM_particle_physics** (8 files)
7. **AF_environmental_sci** (12 files)
8. **AG_control_theory** (12 files) — clean mathematical structure
9. **AI_robotics** (12 files)
10. **AC_astrophysics** (18 files)
11. **AE_computational_bio** (18 files) — most complex; do last

---

## Per-Principle Process (repeat for every source file)

### Step A — Parse source .md → L1-NNN.json

- [ ] **A.1** Read source file. Extract:
  - `P = (E, G, W, C)` quadruple explicitly:
    - `E` (forward model): the observation/measurement model appropriate to the domain
      - Astrophysics: `y = PSF * x + noise` (deconvolution)
      - Finance: `y = F(theta) + epsilon` (parameter calibration)
      - Robotics: `y = g(x, u) + v` (state estimation)
      - Computational bio: `y = H * x + n` (structure from measurements)
    - `G` (DAG): operator chain
    - `W` (well-posedness): existence, uniqueness, stability, condition_number
    - `C` (convergence): solver_class, convergence_rate_q (2.0 default), error_bound, complexity
  - `world_state_x`: what is being estimated (state, parameters, distribution, field)
  - `observation_y`: observable measurements
  - `physical_parameters_theta`: model parameters
  - `mismatch_parameters`: uncertain / misspecified parameters
  - `error_metric`: domain-appropriate (PSNR for imaging, MAE for prediction, etc.)
  - `physics_fingerprint` block (all 7 fields):
    - `carrier`, `sensing_mechanism`, `integration_axis`, `problem_class`, `noise_model`, `solution_space`, `primitives`
  - `spec_range` block:
    - `center_spec`, `allowed_forward_operators`, `allowed_problem_classes`, `allowed_omega_dimensions`, `omega_bounds`, `epsilon_bounds`
- [ ] **A.2** Assign `difficulty_delta`: Trivial→1, Standard→3, Challenging→5, Hard→10, Frontier→50
- [ ] **A.3** Write `principles/<domain>/L1-NNN.json`.
- [ ] **A.4** Validate: every required field present, typed correctly.

### Step B — Write L2-NNN.json (Spec)

- [ ] **B.1** Write at least one spec. Two specs preferred:
  - Spec 1: nominal inversion (well-characterized system)
  - Spec 2: mismatch-robust inversion (model mismatch in Ω)
- [ ] **B.2** Write `epsilon_fn` — calibrate so `d(Ω_centroid) ∈ [0.3, 0.7]`.
  - Applied note: error metrics are domain-specific. Use units that make practical sense
    (e.g., MAE in km for geodesy, relative error for finance, PSNR for astrophysics imaging).
- [ ] **B.3** Write S1-S4 gate justifications.
- [ ] **B.4** Test `epsilon_fn` evaluates without error for 10 random Ω samples.
- [ ] **B.5** Include `ibenchmark_range` (center_ibenchmark, tier_bounds).
- [ ] **B.6** Confirm `d_spec >= 0.15` from any other spec under same principle.
- [ ] **B.7** Write `principles/<domain>/L2-NNN.json`.

### Step C — Write L3-NNN.json (Benchmark)

- [ ] **C.1** Write 4 I-benchmark tiers (T1–T4):
  - T1 nominal: standard conditions for the domain (good SNR, low mismatch), ρ=1
  - T2 low: easiest regime (clean data, simple model), ρ=3
  - T3 moderate: real-world conditions (some noise, mild mismatch), ρ=5
  - T4 blind: challenging conditions (low SNR, large mismatch, real data artifacts), ρ=10
- [ ] **C.2** Write P-benchmark: real observational or experimental dataset:
  - Astrophysics: HST/JWST public data, Sloan DSS
  - Environmental science: ERA5 reanalysis, MODIS satellite data
  - Computational finance: historical market data (Yahoo Finance, FRED)
  - Computational biology: PDB structures, cryo-EM public datasets
  - P-benchmark ρ=50.
- [ ] **C.3** Write ≥ 2 baseline solvers (domain-standard algorithms):
  - Astrophysics: CLEAN, Richardson-Lucy
  - Computational finance: Black-Scholes calibration, MCMC
  - Robotics: EKF, UKF, particle filter
  - Computational biology: Gaussian network model, normal mode analysis
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
- [ ] difficulty_delta consistent with domain complexity
- [ ] P1-P10 physics validity tests all PASS

---

## Applied-Domain Notes

- **Astrophysics** (AC): deconvolution of telescope PSF is Standard-Challenging. Gravitational lensing inversion is Frontier.
- **Astronomy** (Q): astrometric inversion, orbit determination. Often Standard (δ=3).
- **Computational biology** (AE): protein folding inverse problem is Frontier (δ=50). Genomics structure from sequencing is Challenging.
- **Environmental science** (AF): climate model inversion, pollution source identification. Often Challenging (δ=5).
- **Control theory** (AG): system identification, state estimation. Clean mathematical structure, often Standard-Challenging.
- **Computational finance** (AH): volatility surface calibration is Challenging (δ=5). Regime-switching parameter identification is Hard.
- **Robotics** (AI): SLAM is Challenging to Hard depending on sensor model.
- **Petroleum** (AJ): seismic inversion overlaps with agent-physics W_geophysics — flag duplicates to agent-coord.
- **Geodesy** (AK): GPS/GNSS inversion is Standard; ionospheric tomography is Hard.
- **Particle physics** (AM): jet reconstruction is Challenging; neutrino mass inversion is Frontier.
- **Optimization** (AO): abstract enough to require consultation with agent-coord for appropriate difficulty_delta assignment.

---

## Progress Tracking

After completing each domain, update `../../coordination/agent-coord/progress.md`:

```
| agent-applied | AC_astrophysics    | 0/18 | IN_PROGRESS |
| agent-applied | AO_optimization    | 3/3  | DONE |
```

---

## Final Step — Signal Completion

- [ ] All ~111 principles have L1, L2, L3 JSON in `principles/<domain>/`.
- [ ] All JSONs pass schema validation.
- [ ] Self-review checklist passes for all.
- [ ] Update `../../coordination/agent-coord/progress.md` — mark applied principles `DONE`.
- [ ] Open PR: `feat/genesis-principles-applied`
  - PR description: count per domain, any Frontier (δ=50) principles flagged for review
