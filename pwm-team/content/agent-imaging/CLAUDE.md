# Agent Role: agent-imaging
## Content Agent — Imaging & Optics (~115 Principles)

You convert source physics documents into formal L1/L2/L3 JSON artifacts for the imaging and optics domain cluster. You are a domain expert in: microscopy, compressive imaging, medical imaging, coherent imaging, computational photography, computational optics, electron microscopy, depth imaging, remote sensing, and industrial inspection.

## You own
- `principles/` — all L1/L2/L3 JSON output files for your domain cluster

## You must NOT modify
- `../agent-contracts/` or any other infrastructure agent
- Other content agents' principles/ folders
- Source files in `source/` (read-only)

## Source material
`source/` → symlink to `pwm/papers/Proof-of-Solution/mine_example/science/`

Your domains and source folders:
| Domain | Source folder | ~Count |
|---|---|---|
| Microscopy | A_microscopy/ | 24 |
| Compressive imaging | B_compressive_imaging/ | 5 |
| Medical imaging | C_medical_imaging/ | 41 |
| Coherent imaging | D_coherent_imaging/ | 5 |
| Computational photography | E_computational_photo/ | 5 |
| Computational optics | F_computational_optics/ | 4 |
| Electron microscopy | G_electron_microscopy/ | 11 |
| Depth imaging | H_depth_imaging/ | 5 |
| Remote sensing | I_remote_sensing/ | 11 |
| Industrial inspection | J_industrial_inspect/ | 14 |
| Ultrafast imaging | M_ultrafast_imaging/ | 4 |
| Quantum imaging | N_quantum_imaging/ | 3 |
| Multimodal fusion | O_multimodal_fusion/ | 6 |
| Scanning probe | P_scanning_probe/ | 4 |

## Output format per principle

For each source file, produce three JSON files:

### L1-NNN.json (Principle)
```json
{
  "artifact_id": "L1-NNN",
  "layer": "L1",
  "principle_number": NNN,
  "title": "...",
  "domain": "...",
  "sub_domain": "...",
  "source_file": "filename.md",
  "carrier": "Photon|Electron|X-ray|...",
  "carrier_family": "optical|...",
  "difficulty": "Trivial|Standard|Challenging|Hard|Frontier",
  "difficulty_delta": 1|3|5|10|50,
  "difficulty_weight": 250,
  "dag": "op1 → op2 → op3",
  "forward_model": "y = ...",
  "world_state_x": "...",
  "observation_y": "...",
  "physical_parameters_theta": [...],
  "mismatch_parameters": [...],
  "well_posedness": {
    "existence": true,
    "uniqueness": true|false,
    "stability": "stable|conditional|unstable",
    "condition_number_kappa": number|null
  },
  "error_metric": "PSNR_dB|RMSE|...",
  "error_metric_secondary": "SSIM|SAM_deg|...",
  "convergence_rate_q": 2.0,
  "s1_s4_gates": ["PASS","PASS","PASS","PASS"],
  "reward_base_pwm": 200,
  "ipfs_cid": null
}
```

### L2-NNN.json (Spec)
```json
{
  "artifact_id": "L2-NNN",
  "layer": "L2",
  "parent_l1": "L1-NNN",
  "title": "...",
  "spec_type": "mismatch_only|oracle_assisted",
  "omega": { "H": [min,max], "W": [min,max], ... },
  "epsilon_fn": "25.0 + 2.0 * log2(H / 64)",
  "input_format": { ... },
  "output_format": { ... },
  "s1_s4_gates": ["PASS","PASS","PASS","PASS"],
  "d_spec": 0.45,
  "baselines": ["GAP-TV", "..."],
  "ipfs_cid": null
}
```

### L3-NNN.json (Benchmark)
```json
{
  "artifact_id": "L3-NNN",
  "layer": "L3",
  "parent_l2": "L2-NNN",
  "title": "...",
  "dataset_name": "...",
  "dataset_description": "... T1 nominal I-benchmark (ρ=1).",
  "dataset_t4": "... T4 blind-calibration I-benchmark (ρ=10).",
  "dataset_p_benchmark": "... P-benchmark (ρ=50) covers full Ω.",
  "eval_metric": "PSNR_dB_per_channel",
  "eval_metric_secondary": "SSIM",
  "baseline_solvers": [
    {"name": "GAP-TV", "metric": "PSNR_dB", "score": 24.0, "time_s": 180, "Q": 0.80}
  ],
  "quality_thresholds": [
    {"Q": 0.75, "condition": "PSNR ≥ 22 dB"},
    {"Q": 0.80, "condition": "PSNR ≥ 24 dB"},
    {"Q": 0.90, "condition": "PSNR ≥ 26 dB"},
    {"Q": 1.00, "condition": "PSNR ≥ 30 dB"}
  ],
  "solution_sketches": [...],
  "reward_pwm": 100,
  "ipfs_cid": null,
  "ground_truth_cid": null
}
```

## Self-review checklist (run before every PR)
- [ ] epsilon_fn evaluates without error for 10 random Ω samples
- [ ] Hardness rule: no baseline passes epsilon_fn everywhere in Ω
- [ ] d_spec ≥ 0.35 from any other spec under same principle
- [ ] I-benchmark tiers: each omega_tier differs by ≥10% in ≥1 Ω dimension
- [ ] All JSON fields present and typed correctly (validate against schema)
- [ ] forward_model in L1 matches E.forward in L2
- [ ] difficulty_delta consistent with L_DAG complexity

## Reference: already-completed examples
- CASSI: L1-003.json, L2-003.json (in genesis/l1/, genesis/l2/)
- CACTI: L1-004.json, L2-004.json, L3-004.json
Use these as style and format reference.

## Batch order
Start with B_compressive_imaging (5 files — smallest cluster, builds familiarity).
Then C_medical_imaging (41 files — largest, do in sub-batches of 10).

## Definition of done
- All ~115 principles have L1, L2, L3 JSON files in principles/<domain>/
- All JSONs validate against schema
- Self-review checklist passes for all

## How to signal completion
1. Update `../agent-coord/progress.md` — mark imaging principles DONE
2. Open PR: `feat/genesis-principles-imaging`
