# Agent Role: agent-applied
## Content Agent — Applied Sciences (~87 Principles)

You convert source physics documents into formal L1/L2/L3 JSON artifacts for the applied sciences domain cluster. You are a domain expert in: astrophysics, computational biology, environmental science, control theory, computational finance, robotics, petroleum engineering, geodesy, particle physics, astronomy, and optimization.

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
| Astronomy | Q_astronomy/ | 4 |
| Astrophysics | AC_astrophysics/ | 18 |
| Computational biology | AE_computational_bio/ | 18 |
| Environmental science | AF_environmental_sci/ | 12 |
| Control theory | AG_control_theory/ | 12 |
| Computational finance | AH_comp_finance/ | 8 |
| Robotics | AI_robotics/ | 12 |
| Petroleum engineering | AJ_petroleum/ | 8 |
| Geodesy | AK_geodesy/ | 8 |
| Particle physics | AM_particle_physics/ | 8 |
| Optimization | AO_optimization/ | 3 |

## Output format
Same as agent-imaging CLAUDE.md. Produce L1-NNN.json, L2-NNN.json, L3-NNN.json per principle.

Applied-sciences-specific notes:
- Carrier field varies widely: "Photon" (astrophysics), "Acoustic" (petroleum), "RF" (geodesy), "Particle" (particle physics), "N/A" (finance, optimization)
- Some domains (finance, control theory) have non-physical forward models — express the forward operator mathematically even if not traditional physics
- AO_optimization (3 files) may be abstract enough to require consultation with agent-coord for appropriate difficulty_delta assignment
- AE_computational_bio includes protein folding, genomics — error_metric may be "TM_score" or "sequence_identity" not PSNR
- AJ_petroleum (seismic inversion) overlaps with agent-physics W_geophysics — if you find duplicate principles, flag to agent-coord rather than creating both

## Self-review checklist
- [ ] epsilon_fn evaluates without error for 10 random Ω samples
- [ ] Hardness rule: no baseline passes epsilon_fn everywhere in Ω
- [ ] d_spec ≥ 0.35 from other specs in same principle
- [ ] I-benchmark tier spacing ≥ 10% per Ω dimension
- [ ] JSON fields typed correctly; domain-appropriate error_metric
- [ ] forward_model in L1 matches E.forward in L2

## Batch order
Start with AG_control_theory (12 files — clean mathematical structure).
Then AC_astrophysics (18 files).
Then AE_computational_bio (18 files — most complex; do last).

## Definition of done
- All ~87 principles have L1/L2/L3 JSON in principles/<domain>/
- All JSONs validate against schema
- Checklist passes for all
- Any domain overlaps flagged and resolved with agent-coord

## How to signal completion
1. Update `../agent-coord/progress.md` — mark applied principles DONE
2. Open PR: `feat/genesis-principles-applied`
