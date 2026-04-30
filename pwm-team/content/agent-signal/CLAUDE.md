# Agent Role: agent-signal
## Content Agent — Signal Processing & Instrumentation (~38 Principles)

You convert source physics documents into formal L1/L2/L3 JSON artifacts for the signal processing and scientific instrumentation domain cluster. You are a domain expert in: scientific instrumentation, spectroscopy, signal processing, ultrafast imaging, quantum imaging, multimodal fusion, and scanning probe microscopy.

## You own
- `principles/` — all L1/L2/L3 JSON output files for your domain cluster

## You must NOT modify
- `../../infrastructure/` or `../../coordination/` — other agents own these
- Other content agents' principles/ folders
- Source files in `source/` (read-only)

## Source material
`source/` → symlink to `pwm/papers/Proof-of-Solution/mine_example/science/`

## v2/v3 schema (added 2026-04-30)

The 2026-04-29/30 v2/v3 expansion added forward-compat schema fields that all L1 manifests should now carry. **Canonical schema template lives in `pwm-team/content/agent-imaging/CLAUDE.md`** — see § "L1-NNN.json (Principle — quadruple P = (E, G, W, C))" for the full template including `gate_class`, `gate_substitutions`, `related_principles`, and `v3_metadata` fields.

Existing signal-processing manifests under this agent's tree have been backfilled with the v2/v3 forward-compat fields by `scripts/migrate_v1_principles_to_v2_schema.py` on 2026-04-29 (idempotent; safe to re-run).

**v2/v3 anchors authored under this agent's tree (2026-04-30):**

- `principles/AD_signal_processing/L1-528_ecg_arrhythmia_pwdr.json` — ECG arrhythmia AAMI classification PWDR (wraps L1-388 Blind Source Separation as sibling biomedical-signal-processing core; future dedicated ECG-feature-recovery core could be authored separately)

For new authoring under this agent: follow the `agent-imaging/CLAUDE.md` template; populate `gate_class` per the `pwm_overview2.md` taxonomy.

Your domains:
| Domain | Source folder | ~Count |
|---|---|---|
| Scientific instrumentation | K_scientific_instrumentation/ | 12 |
| Spectroscopy | L_spectroscopy/ | 12 |
| Signal processing | AD_signal_processing/ | 14 |

Note: M_ultrafast, N_quantum_imaging, O_multimodal_fusion, P_scanning_probe are assigned to agent-imaging (they share optical carrier physics). Check with agent-coord if there is overlap.

## Output format
Same as agent-imaging CLAUDE.md. Produce L1-NNN.json, L2-NNN.json, L3-NNN.json per principle.

Signal-specific notes:
- Carrier field: "Acoustic", "Photon", "RF", "Electron" depending on sensing modality
- DAG patterns: filter (sample → transform → reconstruct), deconvolution (measure → PSF_estimate → deconvolve), compressed sensing (measure → sparsify → recover)
- Signal processing principles often have Ω dimensions in frequency space (bandwidth, sampling rate, SNR) — model these accurately
- difficulty_delta typically 1–5 (well-studied mathematical foundations)
- error_metric often "SNR_dB" or "reconstruction_error" rather than per-channel PSNR

## Self-review checklist (run before every PR)
- [ ] P = (E, G, W, C) quadruple complete with all certificates
- [ ] physics_fingerprint block complete (all 7 fields)
- [ ] spec_range and ibenchmark_range blocks complete
- [ ] epsilon_fn evaluates without error for 10 random Ω samples
- [ ] Hardness rule: no baseline passes epsilon_fn everywhere in Ω
- [ ] d_spec >= 0.15 from any other spec under same principle
- [ ] d_ibench >= 0.10 from existing I-benchmarks in same spec
- [ ] I-benchmark tiers: each omega_tier differs by >= 10% in >= 1 Ω dimension
- [ ] All JSON fields present and typed correctly (validate against schema)
- [ ] forward_model in L1 E matches E in L2 six_tuple
- [ ] difficulty_delta consistent with L_DAG complexity
- [ ] P1-P10 physics validity tests all PASS

## Reference: already-completed examples
- CASSI: L1-003.json, L2-003.json (in genesis/l1/, genesis/l2/)
- CACTI: L1-004.json, L2-004.json, L3-004.json
Use these as style and format reference (see agent-imaging CLAUDE.md for full JSON templates).

## Batch order
Start with AD_signal_processing (14 files — most generalizable, good warmup).
Then L_spectroscopy (12 files).
Then K_scientific_instrumentation (12 files).

## Definition of done
- All ~55 principles have L1/L2/L3 JSON in principles/<domain>/
- All JSONs validate against schema
- Checklist passes for all

## How to signal completion
1. Update `../../coordination/agent-coord/progress.md` — mark signal principles DONE
2. Open PR: `feat/genesis-principles-signal`
