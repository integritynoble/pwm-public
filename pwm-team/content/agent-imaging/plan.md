# agent-imaging: Execution Plan

Read `CLAUDE.md` first (your role, domain list, and full JSON schemas). This file is your step-by-step work order.

---

## Before You Start

> **← WAIT FOR:** Check `../../coordination/agent-coord/progress.md` for the line:
> `REPO_READY = true`
> Do not begin until agent-coord has set this flag (Day 2 at latest).

- [ ] Read `CLAUDE.md` — all JSON field specs and the self-review checklist are there.
- [ ] Read `../../papers/Proof-of-Solution/mine_example/cassi.md` and `cacti.md` — completed reference examples.
- [ ] Read `../../papers/Proof-of-Solution/pwm_overview1.md` §Difficulty Score, §ρ Tier Mapping, §Track A/B/C.
- [ ] Look at existing completed artifacts for style reference:
  - `../../pwm_product/genesis/l1/L1-003.json` (CASSI L1)
  - `../../pwm_product/genesis/l2/L2-003.json` (CASSI L2)
  - `../../pwm_product/genesis/l3/L3-004.json` (CACTI L3 — includes P-benchmark spec)
- [ ] Source files are in `source/` (symlink to `pwm/papers/Proof-of-Solution/mine_example/science/`).

---

## Your Domains

| Domain | Source folder | Count | Output folder |
|---|---|---|---|
| Compressive imaging | B_compressive_imaging/ | 5 | principles/B_compressive_imaging/ |
| Medical imaging | C_medical_imaging/ | 41 | principles/C_medical_imaging/ |
| Microscopy | A_microscopy/ | 24 | principles/A_microscopy/ |
| Coherent imaging | D_coherent_imaging/ | 5 | principles/D_coherent_imaging/ |
| Computational photo | E_computational_photography/ | 5 | principles/E_computational_photography/ |
| Computational optics | F_computational_optics/ | 4 | principles/F_computational_optics/ |
| Electron microscopy | G_electron_microscopy/ | 11 | principles/G_electron_microscopy/ |
| Depth imaging | H_depth_imaging/ | 5 | principles/H_depth_imaging/ |
| Remote sensing | I_remote_sensing/ | 11 | principles/I_remote_sensing/ |
| Industrial inspection | J_industrial_inspection/ | 14 | principles/J_industrial_inspection/ |
| Ultrafast imaging | M_ultrafast_imaging/ | 4 | principles/M_ultrafast_imaging/ |
| Quantum imaging | N_quantum_imaging/ | 3 | principles/N_quantum_imaging/ |
| Multimodal fusion | O_multimodal_fusion/ | 6 | principles/O_multimodal_fusion/ |
| Scanning probe | P_scanning_probe/ | 4 | principles/P_scanning_probe/ |

**Total: ~115 principles**

---

## Batch Order (work in this order)

1. **B_compressive_imaging** (5 files) — start here, smallest cluster
2. **D_coherent_imaging** (5 files)
3. **E_computational_photography** (5 files)
4. **F_computational_optics** (4 files)
5. **H_depth_imaging** (5 files)
6. **A_microscopy** (24 files) — work in sub-batches of 8
7. **G_electron_microscopy** (11 files)
8. **I_remote_sensing** (11 files)
9. **J_industrial_inspection** (14 files)
10. **C_medical_imaging** (41 files) — work in sub-batches of 10
11. **M, N, O, P** (17 files) — finish with these

---

## Per-Principle Process (repeat for every source file)

### Step A — Parse source .md → L1-NNN.json

- [ ] **A.1** Read source file. Extract:
  - `P = (E, G, W, C)` quadruple explicitly:
    - `E` (forward model): the governing equation (e.g., `y = Φx + ε`)
    - `G` (DAG): operator chain (e.g., `"A.coded_aperture → B.shear → C.spectral_unmix"`)
    - `W` (well-posedness): existence, uniqueness, stability, condition_number
    - `C` (convergence): solver_class, convergence_rate_q (2.0 unless source says otherwise), error_bound, complexity
  - `world_state_x`: what x represents physically
  - `observation_y`: what y represents physically
  - `physical_parameters_theta`: list of physical constants / system parameters
  - `mismatch_parameters`: which parameters are uncertain / mismatched
  - `error_metric`: primary (e.g., `PSNR_dB`) and secondary (e.g., `SSIM`)
  - `physics_fingerprint` block (all 7 fields):
    - `carrier`, `sensing_mechanism`, `integration_axis`, `problem_class`, `noise_model`, `solution_space`, `primitives`
  - `spec_range` block:
    - `center_spec`, `allowed_forward_operators`, `allowed_problem_classes`, `allowed_omega_dimensions`, `omega_bounds`, `epsilon_bounds`
- [ ] **A.2** Assign `difficulty_delta` from source difficulty label:
  - Trivial → 1, Standard → 3, Challenging → 5, Hard → 10, Frontier → 50
- [ ] **A.3** Write `principles/<domain>/L1-NNN.json` (follow schema in CLAUDE.md exactly).
- [ ] **A.4** Validate: every required field present, typed correctly.

### Step B — Write L2-NNN.json (Spec)

- [ ] **B.1** Write at least one spec. Two specs preferred:
  - Spec 1: mismatch-only (Ω includes mismatch dims)
  - Spec 2: oracle-assisted (mismatch in true_phi input)
- [ ] **B.2** Write `epsilon_fn` — calibrate so `d(Ω_centroid) ∈ [0.3, 0.7]`:
  - Compute `d(Ω_centroid)` using the formula: `(ε_fn(Ω_centroid) − floor) / (sota − floor)`
  - If d < 0.3: lower ε (make harder); if d > 0.7: raise ε (make easier)
- [ ] **B.3** Write S1-S4 gate justifications for this spec.
- [ ] **B.4** Test `epsilon_fn` evaluates without error:
  ```python
  from pwm_scoring.epsilon import eval_epsilon
  result = eval_epsilon(spec["E"]["epsilon_fn"], omega_centroid)
  assert isinstance(result, float)
  ```
- [ ] **B.5** Include `ibenchmark_range` (center_ibenchmark, tier_bounds).
- [ ] **B.6** Confirm `d_spec >= 0.15` from any other spec under same principle.
- [ ] **B.7** Write `principles/<domain>/L2-NNN.json`.

### Step C — Write L3-NNN.json (Benchmark)

- [ ] **C.1** Write 4 I-benchmark tiers (T1–T4):
  - T1 nominal: Ω_centroid, ρ=1 (d<0.2)
  - T2 low: easy end of Ω, ρ=3 (d∈[0.2,0.4])
  - T3 moderate: mid Ω, ρ=5 (d∈[0.4,0.6])
  - T4 blind: hard end of Ω, ρ=10 (d∈[0.6,0.8])
  - Each tier: `omega_tier`, `dataset_description`, `quality_thresholds`
- [ ] **C.2** Write P-benchmark tier:
  - `dataset_p_benchmark`: real dataset, covers full Ω, ρ=50
  - Stitch rule: if H×W > 480×480, use 2×2 hard stitch (seam_map in true_phi)
- [ ] **C.3** Write ≥ 2 baseline solvers with expected PSNR and Q:
  - Use domain-standard algorithms (e.g., GAP-TV for compressive imaging, FBP for CT)
  - Baselines must NOT all pass epsilon_fn everywhere (hardness rule)
- [ ] **C.4** Confirm tier spacing: each omega_tier differs by ≥10% in ≥1 Ω dimension.
- [ ] **C.5** Confirm `d_ibench >= 0.10` from existing I-benchmarks in same spec.
- [ ] **C.6** Write `principles/<domain>/L3-NNN.json`.

### Step D — Self-Review Checklist (before moving to next principle)

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
- [ ] difficulty_delta in L1 consistent with L_DAG complexity
- [ ] P1-P10 physics validity tests all PASS

---

## Progress Tracking (update as you go)

After completing each domain cluster, note the count in `../../coordination/agent-coord/progress.md`:

```
| agent-imaging | B_compressive_imaging | 5/5 | DONE |
| agent-imaging | C_medical_imaging     | 0/41 | IN_PROGRESS |
```

> **→ SIGNAL OUT (per batch):** After each domain cluster is complete, add to `progress.md`:
> `agent-imaging/<domain> = DONE  # <count> principles — <date>`
> agent-coord watches these lines to know when to schedule reviews.

---

## Final Step — Signal Completion

- [ ] All ~115 principles have L1, L2, L3 JSON in `principles/<domain>/`.
- [ ] All JSONs pass schema validation.
- [ ] Self-review checklist passes for all.
- [ ] Update `../../coordination/agent-coord/progress.md` — mark imaging principles `DONE`.
- [ ] Open PR: `feat/genesis-principles-imaging`
  - PR description: count per domain, any principles flagged as "needs specialist review"

> **→ SIGNAL OUT (final):** After PR is open, write in `progress.md`:
> `agent-imaging = PR_OPEN  # feat/genesis-principles-imaging — <date>`
> agent-coord will review and merge.
