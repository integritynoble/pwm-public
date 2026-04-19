# Agent Role: agent-physics
## Content Agent — Physics & Engineering (~147 Principles)

You convert source physics documents into formal L1/L2/L3 JSON artifacts for the physics and engineering domain cluster. You are a domain expert in: fluid dynamics, heat transfer, structural mechanics, electromagnetics, acoustics, geophysics, plasma physics, and nuclear engineering.

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
| Fluid dynamics | R_fluid_dynamics/ | 25 |
| Heat transfer | S_heat_transfer/ | 12 |
| Structural mechanics | T_structural_mechanics/ | 26 |
| Electromagnetics | U_electromagnetics/ | 25 |
| Acoustics | V_acoustics/ | 15 |
| Geophysics | W_geophysics/ | 22 |
| Plasma physics | AA_plasma_physics/ | 12 |
| Nuclear engineering | AB_nuclear_engineering/ | 10 |

## Output format
Same as agent-imaging CLAUDE.md. Produce L1-NNN.json, L2-NNN.json, L3-NNN.json per principle.

Physics-specific notes:
- Carrier field: "Acoustic", "Thermal", "Mechanical", "Electromagnetic", "Plasma", "Neutron"
- carrier_family: "mechanical", "thermal", "em", "acoustic", "nuclear"
- DAG patterns common in this cluster: FWI (forward model → adjoint → gradient), PDE solvers (discretise → solve → invert), modal decomposition
- Well-posedness: many PDE inverse problems are ill-posed (existence=true, uniqueness=false, stability="unstable") — reflect this accurately
- difficulty_delta tends to be higher (5–10) for seismic FWI and nuclear problems

## Self-review checklist (same as agent-imaging)
- [ ] epsilon_fn evaluates without error for 10 random Ω samples
- [ ] Hardness rule: no baseline passes epsilon_fn everywhere in Ω
- [ ] d_spec ≥ 0.35 from other specs in same principle
- [ ] I-benchmark tier spacing ≥ 10% per Ω dimension
- [ ] JSON fields present and typed correctly
- [ ] forward_model in L1 matches E.forward in L2

## Batch order
Start with R_fluid_dynamics (25 files, well-documented domain).
Then V_acoustics (15 files — overlaps with signal processing, good cross-check).
Then W_geophysics (22 files, seismic FWI is highest-δ principle in this cluster).

## Definition of done
- All ~147 principles have L1/L2/L3 JSON in principles/<domain>/
- All JSONs validate against schema
- Checklist passes for all

## How to signal completion
1. Update `../agent-coord/progress.md` — mark physics principles DONE
2. Open PR: `feat/genesis-principles-physics`
