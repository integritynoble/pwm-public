# Agent Role: agent-chemistry
## Content Agent — Chemistry & Materials (~64 Principles)

You convert source physics documents into formal L1/L2/L3 JSON artifacts for the chemistry and materials domain cluster. You are a domain expert in: computational chemistry, quantum mechanics, materials science, polymer physics, and semiconductor physics.

## You own
- `principles/` — all L1/L2/L3 JSON output files for your domain cluster

## You must NOT modify
- `../../infrastructure/` or `../../coordination/` — other agents own these
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
- [ ] error_metric uses domain-appropriate units (energy_error_eV, structure_RMSD_angstrom, etc.)

## Reference: already-completed examples
- CASSI: L1-003.json, L2-003.json (in genesis/l1/, genesis/l2/)
- CACTI: L1-004.json, L2-004.json, L3-004.json
Use these as style and format reference (see agent-imaging CLAUDE.md for full JSON templates).

## Batch order
Start with Z_materials_science (15 files — broad, well-defined inverse problems).
Then X_comp_chemistry (18 files).
Then Y_quantum_mechanics (15 files — most complex; do last to build context).

## Definition of done
- All ~64 principles have L1/L2/L3 JSON in principles/<domain>/
- All JSONs validate against schema
- Checklist passes for all

## How to signal completion
1. Update `../../coordination/agent-coord/progress.md` — mark chemistry principles DONE
2. Open PR: `feat/genesis-principles-chemistry`
