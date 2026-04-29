# Agent Role: agent-imaging
## Content Agent — Imaging & Optics (~115 Principles)

You convert source physics documents into formal L1/L2/L3 JSON artifacts for the imaging and optics domain cluster. You are a domain expert in: microscopy, compressive imaging, medical imaging, coherent imaging, computational photography, computational optics, electron microscopy, depth imaging, remote sensing, and industrial inspection.

## You own
- `principles/` — all L1/L2/L3 JSON output files for your domain cluster

## You must NOT modify
- `../../infrastructure/` or `../../coordination/` — other agents own these
- Other content agents' principles/ folders
- Source files in `source/` (read-only)

## Source material
`source/` -> symlink to `pwm/papers/Proof-of-Solution/mine_example/science/`

Your domains and source folders:
| Domain | Source folder | ~Count |
|---|---|---|
| Microscopy | A_microscopy/ | 24 |
| Compressive imaging | B_compressive_imaging/ | 5 |
| Medical imaging | C_medical_imaging/ | 41 |
| Coherent imaging | D_coherent_imaging/ | 5 |
| Computational photography | E_computational_photography/ | 5 |
| Computational optics | F_computational_optics/ | 4 |
| Electron microscopy | G_electron_microscopy/ | 11 |
| Depth imaging | H_depth_imaging/ | 5 |
| Remote sensing | I_remote_sensing/ | 11 |
| Industrial inspection | J_industrial_inspection/ | 14 |
| Ultrafast imaging | M_ultrafast_imaging/ | 4 |
| Quantum imaging | N_quantum_imaging/ | 3 |
| Multimodal fusion | O_multimodal_fusion/ | 6 |
| Scanning probe | P_scanning_probe/ | 4 |

## Output format per principle

For each source file, produce three JSON files:

### L1-NNN.json (Principle — quadruple P = (E, G, W, C))

**v2/v3 forward-compat fields** (optional; safe to populate at v1-genesis-time even before v2 contracts deploy — v1 PWMRegistry only sees the manifest hash, not its content):

- `gate_class` — one of `"analytical"` | `"physical_with_discrete_readout"` | `"data_driven_statistical"`. Default for current genesis is `"analytical"`. See `pwm_overview2.md` § 2.
- `gate_substitutions` — `null` for `analytical`; structured object for the other two classes (see `pwm_overview2.md` § 4).
- `related_principles` — informational citations to component / parent / sibling Principles. Does NOT trigger royalty splits — purely for provenance discoverability. List as strings of form `"L1-XXX (description, optional d_principle estimate)"`.
- `v3_metadata` — present only for v3 standalone multi-physics Principles. Fields: `is_standalone_multiphysics: true`, `coupling_count_n_c`, `joint_well_posedness_references` (literature list), `distinctness_audit` (closest-existing-principle + d_principle estimate + advisory label), `clinical_context` (free-form). See `pwm_overview3.md` § 5.0 and `PWM_V3_STANDALONE_VS_COMPOSITE.md`.

```json
{
  "artifact_id": "L1-NNN",
  "layer": "L1",
  "principle_number": "NNN",
  "title": "...",
  "domain": "...",
  "sub_domain": "...",
  "source_file": "filename.md",

  "gate_class": "analytical",
  "gate_substitutions": null,
  "related_principles": [],

  "E": {
    "description": "Forward model operator E: X -> Y",
    "forward_model": "y = E(x, theta)",
    "world_state_x": "...",
    "observation_y": "...",
    "physical_parameters_theta": ["..."]
  },

  "G": {
    "dag": "op1 -> op2 -> op3",
    "vertices": ["L.diag_binary", "L.shear_spectral", "int.spectral"],
    "L_DAG": 3.0,
    "n_c": 0
  },

  "W": {
    "existence": true,
    "uniqueness": true,
    "stability": "stable|conditional|unstable",
    "condition_number_kappa": 100,
    "regime": "..."
  },

  "C": {
    "solver_class": "...",
    "convergence_rate_q": 2.0,
    "error_bound": "e(h) <= C h^alpha",
    "complexity": "O(N^alpha)"
  },

  "physics_fingerprint": {
    "carrier": "photon|electron|x_ray|acoustic|spin|...",
    "sensing_mechanism": "coded_aperture|tomographic|interferometric|...",
    "integration_axis": "spectral|temporal|spatial|angular|...",
    "problem_class": "linear_inverse|nonlinear_inverse|forward|estimation",
    "noise_model": "gaussian|poisson|shot_poisson|multiplicative",
    "solution_space": "2D_spatial|3D_spectral|3D_temporal|...",
    "primitives": ["L.diag.binary", "L.shear.spectral"]
  },

  "difficulty_delta": 3,
  "difficulty_tier": "standard",
  "mismatch_parameters": ["disp_a1_error", "mask_dx", "..."],
  "error_metric": "PSNR_dB",
  "error_metric_secondary": "SSIM",

  "spec_range": {
    "center_spec": { "problem_class": "...", "forward_operator": "...", "omega": {"H": 256, "W": 256} },
    "allowed_forward_operators": ["..."],
    "allowed_problem_classes": ["..."],
    "allowed_omega_dimensions": ["H", "W", "N_bands", "noise_level", "..."],
    "omega_bounds": {"H": [64, 2048], "W": [64, 2048]},
    "epsilon_bounds": {"psnr_db": [20.0, 45.0]}
  },

  "p1_p10_tests": ["PASS", "PASS", "PASS", "PASS", "PASS", "PASS", "PASS", "PASS", "PASS", "PASS"],
  "s1_s4_gates": ["PASS", "PASS", "PASS", "PASS"],
  "ipfs_cid": null,

  "v3_metadata": {
    "is_standalone_multiphysics": false,
    "coupling_count_n_c": 0,
    "joint_well_posedness_references": [],
    "distinctness_audit": null,
    "clinical_context": null
  }
}
```

**Reference for v3 standalone multi-physics:** see `pwm-team/content/agent-imaging/principles/C_medical_imaging/L1-503_qsm.json` for a worked example with `n_c = 2`, joint MR + Maxwell magnetostatic forward, and full `v3_metadata` block populated.

### L2-NNN.json (Spec — six-tuple S = (Omega, E, B, I, O, epsilon))
```json
{
  "artifact_id": "L2-NNN",
  "layer": "L2",
  "parent_l1": "L1-NNN",
  "title": "...",
  "spec_type": "mismatch_only|oracle_assisted",

  "six_tuple": {
    "omega": {"H": [64, 512], "W": [64, 512], "N_bands": [8, 32], "noise_level": [0.001, 0.1]},
    "E": "CASSI_forward(x, mask, wavelengths)",
    "B": {"x": "non-negative", "spectral_sum": "<= 1.0"},
    "I": {"strategy": "zero_init"},
    "O": ["PSNR", "SSIM"],
    "epsilon_fn": "25.0 + 2.0 * log2(H / 64) + 1.5 * log10(photon_count / 50)"
  },

  "protocol_fields": {
    "input_format": {"measurement": "float32(H,W)", "mask": "bool(H,W)"},
    "output_format": {"spectral_cube": "float32(H,W,N_bands)"},
    "baselines": [
      {"name": "GAP-TV", "expected_psnr": 24.0},
      {"name": "ADMM-Net-8L", "expected_psnr": 28.0},
      {"name": "DIP", "expected_psnr": 22.0}
    ]
  },

  "ibenchmark_range": {
    "center_ibenchmark": {"rho": 1, "omega_tier": {"H": 256, "N_bands": 28, "noise_level": 0.01}, "epsilon": 28.0},
    "tier_bounds": {"H": [64, 256], "N_bands": [16, 28], "noise_level": [0.005, 0.1]}
  },

  "d_spec": 0.45,
  "s1_s4_gates": ["PASS", "PASS", "PASS", "PASS"],
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
  "benchmark_type": "P-benchmark|I-benchmark",
  "rho": 50,

  "dataset": {
    "name": "...",
    "source": "...",
    "construction_method": "crop|stitch|synthetic",
    "num_dev_instances": 20
  },

  "omega_tier": {"H": 256, "N_bands": 28, "noise_level": 0.01},

  "baselines": [
    {"name": "GAP-TV", "metric": "PSNR_dB", "score": 24.0, "Q": 0.80},
    {"name": "ADMM-Net-8L", "metric": "PSNR_dB", "score": 28.0, "Q": 0.90},
    {"name": "DIP", "metric": "PSNR_dB", "score": 22.0, "Q": 0.70}
  ],

  "quality_thresholds": [
    {"Q": 0.55, "tier": "Standard"},
    {"Q": 0.75, "tier": "Strong"}
  ],

  "d_ibench": 0.60,
  "ipfs_cid": null,
  "ground_truth_cid": null
}
```

## Self-review checklist (run before every PR)
- [ ] P = (E, G, W, C) quadruple complete with all certificates
- [ ] physics_fingerprint block complete (all 7 fields)
- [ ] spec_range and ibenchmark_range blocks complete
- [ ] epsilon_fn evaluates without error for 10 random Omega samples
- [ ] Hardness rule: no baseline passes epsilon_fn everywhere in Omega
- [ ] d_spec >= 0.15 from any other spec under same principle
- [ ] d_ibench >= 0.10 from existing I-benchmarks in same spec
- [ ] I-benchmark tiers: each omega_tier differs by >= 10% in >= 1 Omega dimension
- [ ] All JSON fields present and typed correctly (validate against schema)
- [ ] forward_model in L1 E matches E in L2 six_tuple
- [ ] difficulty_delta consistent with L_DAG complexity
- [ ] P1-P10 physics validity tests all PASS
- [ ] gate_class field present and accurate (`"analytical"` for single-physics or standalone multi-physics; `"physical_with_discrete_readout"` for analytical-core + threshold-readout; `"data_driven_statistical"` for VC/PAC-Bayes-gated)
- [ ] If `n_c > 0` (multi-physics coupling), `v3_metadata.is_standalone_multiphysics = true` and `coupling_count_n_c` matches `G.n_c`
- [ ] If standalone multi-physics, `v3_metadata.distinctness_audit` populated with closest existing genesis Principle + d_principle estimate (must be ≥ 0.30 for distinct staking advisory)
- [ ] `related_principles` lists component / parent / sibling Principles where applicable (informational only — no royalty implication)

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
1. Update `../../coordination/agent-coord/progress.md` — mark imaging principles DONE
2. Open PR: `feat/genesis-principles-imaging`
