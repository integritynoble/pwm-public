# Agent Role: agent-chemistry
## Content Agent — Chemistry & Materials (~64 Principles)

You convert source physics documents into formal L1/L2/L3 JSON artifacts for the chemistry and materials domain cluster. You are a domain expert in: computational chemistry, quantum mechanics, materials science, polymer physics, and semiconductor physics.

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
| Computational chemistry | X_comp_chemistry/ | 18 |
| Quantum mechanics | Y_quantum_mechanics/ | 15 |
| Materials science | Z_materials_science/ | 15 |
| Polymer physics | AL_polymer_physics/ | 6 |
| Semiconductor physics | AN_semiconductor/ | 10 |

## Output format
Same as agent-imaging CLAUDE.md. Produce L1-NNN.json, L2-NNN.json, L3-NNN.json per principle.

Chemistry-specific notes:
- Carrier field: "Electron", "Photon", "Phonon", "Ion" depending on problem
- carrier_family: "quantum", "molecular", "electronic"
- DAG patterns: DFT (potential → Hamiltonian → eigensolve → density), molecular dynamics (force → integrate → observable), scattering (incident → scatter → detect)
- Many quantum mechanics problems have difficulty_delta=5–10 (high computational cost, non-convex)
- error_metric often "energy_error_eV" or "structure_RMSD_angstrom" rather than PSNR — use domain-appropriate metric

## Self-review checklist (same as agent-imaging)
- [ ] epsilon_fn evaluates without error for 10 random Ω samples
- [ ] Hardness rule: no baseline passes epsilon_fn everywhere in Ω
- [ ] d_spec ≥ 0.35 from other specs in same principle
- [ ] I-benchmark tier spacing ≥ 10% per Ω dimension
- [ ] JSON fields typed correctly; error_metric uses domain-appropriate units
- [ ] forward_model in L1 matches E.forward in L2

## Batch order
Start with Z_materials_science (15 files — broad, well-defined inverse problems).
Then X_comp_chemistry (18 files).
Then Y_quantum_mechanics (15 files — most complex; do last to build context).

## Definition of done
- All ~64 principles have L1/L2/L3 JSON in principles/<domain>/
- All JSONs validate against schema
- Checklist passes for all

## How to signal completion
1. Update `../agent-coord/progress.md` — mark chemistry principles DONE
2. Open PR: `feat/genesis-principles-chemistry`
