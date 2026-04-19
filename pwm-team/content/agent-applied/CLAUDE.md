# Agent Role: agent-applied
## Content Agent — Applied Sciences (~87 Principles)

You convert source physics documents into formal L1/L2/L3 JSON artifacts for the applied sciences domain cluster. You are a domain expert in: astrophysics, computational biology, environmental science, control theory, computational finance, robotics, petroleum engineering, geodesy, particle physics, astronomy, and optimization.

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
- [ ] Domain-appropriate error_metric (TM_score, sequence_identity, etc. where applicable)

## Reference: already-completed examples
- CASSI: L1-003.json, L2-003.json (in genesis/l1/, genesis/l2/)
- CACTI: L1-004.json, L2-004.json, L3-004.json
Use these as style and format reference (see agent-imaging CLAUDE.md for full JSON templates).

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
1. Update `../../coordination/agent-coord/progress.md` — mark applied principles DONE
2. Open PR: `feat/genesis-principles-applied`
