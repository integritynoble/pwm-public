# agent-signal: Execution Plan

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
  - `../../pwm_product/genesis/l3/L3-004.json` (CACTI L3)
- [ ] Source files are in `source/` (symlink to `pwm/papers/Proof-of-Solution/mine_example/science/`).

---

## Your Domains

| Domain | Source folder | Count | Output folder |
|---|---|---|---|
| Scientific instrumentation | K_scientific_instrumentation/ | 12 | principles/K_scientific_instrumentation/ |
| Spectroscopy | L_spectroscopy/ | 12 | principles/L_spectroscopy/ |
| Signal processing | AD_signal_processing/ | 14 | principles/AD_signal_processing/ |

**Total: ~38 principles**

> **Note:** Domains M (Ultrafast), N (Quantum imaging), O (Multimodal fusion), P (Scanning probe) are assigned to **agent-imaging** -- they share optical carrier physics. If you see references to those domains in source/, skip them.

---

## Batch Order (work in this order)

1. **AD_signal_processing** (14 files) — start here, most generalizable
2. **L_spectroscopy** (12 files)
3. **K_scientific_instrumentation** (12 files)

---

## Per-Principle Process (repeat for every source file)

### Step A — Parse source .md → L1-NNN.json

- [ ] **A.1** Read source file. Extract:
  - `P = (E, G, W, C)` quadruple explicitly:
    - `E` (forward model): measurement equation (e.g., `y = A·x + n` for compressed sensing, `Y(f) = H(f)·X(f)` for convolution)
    - `G` (DAG): operator chain (e.g., `"A.sample → B.filter → C.reconstruct"`)
    - `W` (well-posedness): existence, uniqueness, stability, condition_number
    - `C` (convergence): solver_class, convergence_rate_q (2.0 default; may be 1.0 for iterative signal recovery), error_bound, complexity
  - `world_state_x`: signal being recovered (time series, spectrum, field map)
  - `observation_y`: observed measurements (ADC samples, spectrometer readings, sensor array output)
  - `physical_parameters_theta`: filter coefficients, sampling matrix, noise floor, SNR
  - `mismatch_parameters`: which parameters are uncertain (noise model, calibration offsets)
  - `error_metric`: primary (e.g., `SNR_dB`, `NMSE`, `spectral_accuracy`) and secondary
  - `physics_fingerprint` block (all 7 fields):
    - `carrier`, `sensing_mechanism`, `integration_axis`, `problem_class`, `noise_model`, `solution_space`, `primitives`
  - `spec_range` block:
    - `center_spec`, `allowed_forward_operators`, `allowed_problem_classes`, `allowed_omega_dimensions`, `omega_bounds`, `epsilon_bounds`
- [ ] **A.2** Assign `difficulty_delta`: Trivial→1, Standard→3, Challenging→5, Hard→10, Frontier→50
- [ ] **A.3** Write `principles/<domain>/L1-NNN.json`.
- [ ] **A.4** Validate: every required field present, typed correctly.

### Step B — Write L2-NNN.json (Spec)

- [ ] **B.1** Write at least one spec. Two specs preferred:
  - Spec 1: blind deconvolution or blind source separation (Ω includes filter uncertainty)
  - Spec 2: known-filter inversion (oracle filter provided, focus on noise robustness)
- [ ] **B.2** Write `epsilon_fn` — calibrate so `d(Ω_centroid) ∈ [0.3, 0.7]`.
  - Signal note: epsilon_fn often in SNR_dB. Reasonable baseline SNRs: 20–35 dB for Standard.
- [ ] **B.3** Write S1-S4 gate justifications.
- [ ] **B.4** Test `epsilon_fn` evaluates without error for 10 random Ω samples.
- [ ] **B.5** Include `ibenchmark_range` (center_ibenchmark, tier_bounds).
- [ ] **B.6** Confirm `d_spec >= 0.15` from any other spec under same principle.
- [ ] **B.7** Write `principles/<domain>/L2-NNN.json`.

### Step C — Write L3-NNN.json (Benchmark)

- [ ] **C.1** Write 4 I-benchmark tiers (T1–T4):
  - T1 nominal: standard SNR, well-calibrated system, ρ=1
  - T2 low: high SNR (easier reconstruction), ρ=3
  - T3 moderate: medium SNR with mild calibration mismatch, ρ=5
  - T4 blind: low SNR or large calibration mismatch (blind deconvolution), ρ=10
- [ ] **C.2** Write P-benchmark: real measurement dataset:
  - Examples: ECG/EEG datasets (PhysioNet), MNIST audio, NMR FID datasets, acoustic recordings
  - P-benchmark ρ=50.
- [ ] **C.3** Write ≥ 2 baseline solvers:
  - Signal: LASSO, OMP, Wiener filter, MUSIC/ESPRIT
  - Spectroscopy: Tikhonov regularization, iterative NMF
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
- [ ] difficulty_delta consistent with signal complexity
- [ ] P1-P10 physics validity tests all PASS

---

## Signal-Specific Notes

- **Signal processing** (AD): CS (compressed sensing) inverse problems are hard when measurement ratio <0.3. Sparsity basis choice matters for difficulty.
- **Scientific instrumentation** (K): calibration-inversion problems are often Standard-Challenging. Blind calibration is Hard.
- **Spectroscopy** (L): peak deconvolution is Standard when peaks are well-separated; Hard when overlapping.

---

## Progress Tracking

After completing each domain, update `../../coordination/agent-coord/progress.md`:

```
| agent-signal | AD_signal_processing   | 0/14 | IN_PROGRESS |
| agent-signal | L_spectroscopy         | 12/12 | DONE |
| agent-signal | K_scientific_instrumentation  | 0/12 | NOT_STARTED |
```

---

## Final Step — Signal Completion

- [ ] All ~38 principles have L1, L2, L3 JSON in `principles/<domain>/`.
- [ ] All JSONs pass schema validation.
- [ ] Self-review checklist passes for all.
- [ ] Update `../../coordination/agent-coord/progress.md` — mark signal principles `DONE`.
- [ ] Open PR: `feat/genesis-principles-signal`
  - PR description: count per domain, any blind/Frontier principles flagged for review

> **→ SIGNAL OUT (per batch):** After each domain cluster is complete, add to `progress.md`:
> `agent-signal/<domain> = DONE  # <count> principles — <date>`
> agent-coord watches these lines to know when to schedule reviews.

> **→ SIGNAL OUT (final):** After PR is open, write in `progress.md`:
> `agent-signal = PR_OPEN  # feat/genesis-principles-signal — <date>`
> agent-coord will review and merge.
