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
| Astrophysics | Q_astrophysics/ | ~10 | principles/Q_astrophysics/ |
| Environmental science | AC_environmental/ | ~10 | principles/AC_environmental/ |
| Robotics & control | AE_robotics_control/ | ~8 | principles/AE_robotics_control/ |
| Finance & economics | AF_finance/ | ~8 | principles/AF_finance/ |
| Biophysics | AG_biophysics/ | ~10 | principles/AG_biophysics/ |
| Geodesy & navigation | AH_geodesy/ | ~8 | principles/AH_geodesy/ |
| Petroleum & reservoir | AI_petroleum/ | ~8 | principles/AI_petroleum/ |
| Particle physics | AJ_particle_physics/ | ~8 | principles/AJ_particle_physics/ |
| Astronomy | AK_astronomy/ | ~8 | principles/AK_astronomy/ |
| Optimization & OR | AM_optimization/ | ~7 | principles/AM_optimization/ |
| Oceanography | AO_oceanography/ | ~2 | principles/AO_oceanography/ |

**Total: ~87 principles**

---

## Batch Order (work in this order)

1. **AM_optimization** (~7 files) — start here, smallest
2. **AO_oceanography** (~2 files)
3. **AE_robotics_control** (~8 files)
4. **AF_finance** (~8 files)
5. **AH_geodesy** (~8 files)
6. **AI_petroleum** (~8 files)
7. **AJ_particle_physics** (~8 files)
8. **AK_astronomy** (~8 files)
9. **Q_astrophysics** (~10 files)
10. **AC_environmental** (~10 files)
11. **AG_biophysics** (~10 files)

---

## Per-Principle Process (repeat for every source file)

### Step A — Parse source .md → L1-NNN.json

- [ ] **A.1** Read source file. Extract:
  - `forward_model`: the observation/measurement model appropriate to the domain
    - Astrophysics: `y = PSF * x + noise` (deconvolution)
    - Finance: `y = F(theta) + epsilon` (parameter calibration)
    - Robotics: `y = g(x, u) + v` (state estimation)
    - Biophysics: `y = H * x + n` (structure from measurements)
  - `dag`: operator chain
  - `world_state_x`: what is being estimated (state, parameters, distribution, field)
  - `observation_y`: observable measurements
  - `physical_parameters_theta`: model parameters
  - `mismatch_parameters`: uncertain / misspecified parameters
  - `well_posedness`: existence, uniqueness, stability, condition_number
  - `error_metric`: domain-appropriate (PSNR for imaging, MAE for prediction, etc.)
  - `convergence_rate_q`: 2.0 default
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
- [ ] **B.5** Confirm `d_spec ≥ 0.35` from any other spec under same principle.
- [ ] **B.6** Write `principles/<domain>/L2-NNN.json`.

### Step C — Write L3-NNN.json (Benchmark)

- [ ] **C.1** Write 4 I-benchmark tiers (T1–T4):
  - T1 nominal: standard conditions for the domain (good SNR, low mismatch), ρ=1
  - T2 low: easiest regime (clean data, simple model), ρ=3
  - T3 moderate: real-world conditions (some noise, mild mismatch), ρ=5
  - T4 blind: challenging conditions (low SNR, large mismatch, real data artifacts), ρ=10
- [ ] **C.2** Write P-benchmark: real observational or experimental dataset:
  - Astrophysics: HST/JWST public data, Sloan DSS
  - Environmental: ERA5 reanalysis, MODIS satellite data
  - Finance: historical market data (Yahoo Finance, FRED)
  - Biophysics: PDB structures, cryo-EM public datasets
  - P-benchmark ρ=50.
- [ ] **C.3** Write ≥ 2 baseline solvers (domain-standard algorithms):
  - Astrophysics: CLEAN, Richardson-Lucy
  - Finance: Black-Scholes calibration, MCMC
  - Robotics: EKF, UKF, particle filter
  - Biophysics: Gaussian network model, normal mode analysis
- [ ] **C.4** Confirm tier spacing ≥10% in ≥1 Ω dimension.
- [ ] **C.5** Write `principles/<domain>/L3-NNN.json`.

### Step D — Self-Review Checklist

- [ ] epsilon_fn evaluates without error for 10 random Ω samples
- [ ] Hardness rule: no baseline passes epsilon_fn everywhere in Ω
- [ ] d_spec ≥ 0.35 from any other spec under same principle
- [ ] I-benchmark tiers: each omega_tier differs ≥10% in ≥1 Ω dimension
- [ ] All JSON fields present and typed correctly
- [ ] forward_model in L1 matches E.forward in L2
- [ ] difficulty_delta consistent with domain complexity

---

## Applied-Domain Notes

- **Astrophysics**: deconvolution of telescope PSF is Standard-Challenging. Gravitational lensing inversion is Frontier.
- **Finance**: volatility surface calibration is Challenging (δ=5). Regime-switching parameter identification is Hard.
- **Robotics**: SLAM is Challenging to Hard depending on sensor model.
- **Biophysics**: protein folding inverse problem is Frontier (δ=50). Membrane potential estimation from patch clamp is Standard.
- **Geodesy**: GPS/GNSS inversion is Standard; ionospheric tomography is Hard.
- **Particle physics**: jet reconstruction is Challenging; neutrino mass inversion is Frontier.

---

## Progress Tracking

After completing each domain, update `../../coordination/agent-coord/progress.md`:

```
| agent-applied | Q_astrophysics    | 0/10 | IN_PROGRESS |
| agent-applied | AM_optimization   | 7/7  | DONE |
```

---

## Final Step — Signal Completion

- [ ] All ~87 principles have L1, L2, L3 JSON in `principles/<domain>/`.
- [ ] All JSONs pass schema validation.
- [ ] Self-review checklist passes for all.
- [ ] Update `../../coordination/agent-coord/progress.md` — mark applied principles `DONE`.
- [ ] Open PR: `feat/genesis-principles-applied`
  - PR description: count per domain, any Frontier (δ=50) principles flagged for review
