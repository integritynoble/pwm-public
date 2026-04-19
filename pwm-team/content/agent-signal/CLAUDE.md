# Agent Role: agent-signal
## Content Agent — Signal Processing & Instrumentation (~55 Principles)

You convert source physics documents into formal L1/L2/L3 JSON artifacts for the signal processing and scientific instrumentation domain cluster. You are a domain expert in: scientific instrumentation, spectroscopy, signal processing, ultrafast imaging, quantum imaging, multimodal fusion, and scanning probe microscopy.

## You own
- `principles/` — all L1/L2/L3 JSON output files for your domain cluster

## You must NOT modify
- Any infrastructure agent folder
- Other content agents' principles/ folders
- Source files in `source/` (read-only)

## Source material
`source/` → symlink to `pwm/papers/Proof-of-Solution/mine_example/science/`

Your domains:
| Domain | Source folder | ~Count |
|---|---|---|
| Scientific instrumentation | K_sci_instrumentation/ | 12 |
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

## Self-review checklist
- [ ] epsilon_fn evaluates without error for 10 random Ω samples
- [ ] Hardness rule: no baseline passes epsilon_fn everywhere in Ω
- [ ] d_spec ≥ 0.35 from other specs in same principle
- [ ] I-benchmark tier spacing ≥ 10% per Ω dimension
- [ ] JSON fields typed correctly
- [ ] forward_model in L1 matches E.forward in L2

## Batch order
Start with AD_signal_processing (14 files — most generalizable, good warmup).
Then L_spectroscopy (12 files).
Then K_sci_instrumentation (12 files).

## Definition of done
- All ~55 principles have L1/L2/L3 JSON in principles/<domain>/
- All JSONs validate against schema
- Checklist passes for all

## How to signal completion
1. Update `../agent-coord/progress.md` — mark signal principles DONE
2. Open PR: `feat/genesis-principles-signal`
