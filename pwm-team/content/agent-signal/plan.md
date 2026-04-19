# agent-signal: Execution Plan

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
| Signal processing | K_signal_processing/ | ~20 | principles/K_signal_processing/ |
| Instrumentation | L_instrumentation/ | ~15 | principles/L_instrumentation/ |
| Spectroscopy | AD_spectroscopy/ | ~20 | principles/AD_spectroscopy/ |

**Total: ~55 principles**

> **Note:** Domains M (Ultrafast), N (Quantum imaging), O (Multimodal fusion), P (Scanning probe) are assigned to **agent-imaging** — they share optical physics context. If you see references to those domains in source/, skip them.

---

## Batch Order (work in this order)

1. **L_instrumentation** (~15 files) — start here
2. **K_signal_processing** (~20 files) — work in sub-batches of 7
3. **AD_spectroscopy** (~20 files) — work in sub-batches of 7

---

## Per-Principle Process (repeat for every source file)

### Step A — Parse source .md → L1-NNN.json

- [ ] **A.1** Read source file. Extract:
  - `forward_model`: measurement equation (e.g., `y = A·x + n` for compressed sensing, `Y(f) = H(f)·X(f)` for convolution)
  - `dag`: operator chain (e.g., `"A.sample → B.filter → C.reconstruct"`)
  - `world_state_x`: signal being recovered (time series, spectrum, field map)
  - `observation_y`: observed measurements (ADC samples, spectrometer readings, sensor array output)
  - `physical_parameters_theta`: filter coefficients, sampling matrix, noise floor, SNR
  - `mismatch_parameters`: which parameters are uncertain (noise model, calibration offsets)
  - `well_posedness`: existence, uniqueness, stability, condition_number
  - `error_metric`: primary (e.g., `SNR_dB`, `NMSE`, `spectral_accuracy`) and secondary
  - `convergence_rate_q`: 2.0 default; may be 1.0 for iterative signal recovery
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
- [ ] **B.5** Confirm `d_spec ≥ 0.35` from any other spec under same principle.
- [ ] **B.6** Write `principles/<domain>/L2-NNN.json`.

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
- [ ] **C.5** Write `principles/<domain>/L3-NNN.json`.

### Step D — Self-Review Checklist

- [ ] epsilon_fn evaluates without error for 10 random Ω samples
- [ ] Hardness rule: no baseline passes epsilon_fn everywhere in Ω
- [ ] d_spec ≥ 0.35 from any other spec under same principle
- [ ] I-benchmark tiers: each omega_tier differs ≥10% in ≥1 Ω dimension
- [ ] All JSON fields present and typed correctly
- [ ] forward_model in L1 matches E.forward in L2
- [ ] difficulty_delta consistent with signal complexity

---

## Signal-Specific Notes

- **Signal processing**: CS (compressed sensing) inverse problems are hard when measurement ratio <0.3. Sparsity basis choice matters for difficulty.
- **Instrumentation**: calibration-inversion problems are often Standard-Challenging. Blind calibration is Hard.
- **Spectroscopy**: peak deconvolution is Standard when peaks are well-separated; Hard when overlapping.

---

## Progress Tracking

After completing each domain, update `../../coordination/agent-coord/progress.md`:

```
| agent-signal | K_signal_processing | 0/20 | IN_PROGRESS |
| agent-signal | L_instrumentation   | 15/15 | DONE |
```

---

## Final Step — Signal Completion

- [ ] All ~55 principles have L1, L2, L3 JSON in `principles/<domain>/`.
- [ ] All JSONs pass schema validation.
- [ ] Self-review checklist passes for all.
- [ ] Update `../../coordination/agent-coord/progress.md` — mark signal principles `DONE`.
- [ ] Open PR: `feat/genesis-principles-signal`
  - PR description: count per domain, any blind/Frontier principles flagged for review
