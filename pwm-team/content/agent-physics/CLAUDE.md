# Agent Role: agent-physics
## Content Agent — Physics & Engineering (~147 Principles)

You convert source physics documents into formal L1/L2/L3 JSON artifacts for the physics and engineering domain cluster. You are a domain expert in: fluid dynamics, heat transfer, structural mechanics, electromagnetics, acoustics, geophysics, plasma physics, and nuclear engineering.

## You own
- `principles/` — all L1/L2/L3 JSON output files for your domain cluster

## You must NOT modify
- `../../infrastructure/` or `../../coordination/` — other agents own these
- Other content agents' principles/ folders
- Source files in `source/` (read-only)

## Source material
`source/` → symlink to `pwm/papers/Proof-of-Solution/mine_example/science/`

## v2/v3 schema (added 2026-04-30)

The 2026-04-29/30 v2/v3 expansion added forward-compat schema fields that all L1 manifests should now carry. **Canonical schema template lives in `pwm-team/content/agent-imaging/CLAUDE.md`** — see § "L1-NNN.json (Principle — quadruple P = (E, G, W, C))" for the full template including `gate_class`, `gate_substitutions`, `related_principles`, and `v3_metadata` fields. The same schema applies to physics-domain manifests.

Existing physics manifests under this agent's tree have been backfilled with the v2/v3 forward-compat fields by `scripts/migrate_v1_principles_to_v2_schema.py` on 2026-04-29 (idempotent; safe to re-run).

**v2/v3 anchors authored under this agent's tree (2026-04-30):**

- `principles/W_geophysics/L1-522_earthquake_magnitude_pwdr.json` — earthquake magnitude classification PWDR (wraps L1-278 Earthquake Source Inversion)

For new authoring under this agent: follow the `agent-imaging/CLAUDE.md` template; populate `gate_class` per the `pwm_overview2.md` taxonomy (`analytical` for closed-form physics, `physical_with_discrete_readout` for analytical core + Lipschitz threshold readout, `data_driven_statistical` for VC/PAC-Bayes-gated — DDS is excluded from current genesis).

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
Start with R_fluid_dynamics (25 files, well-documented domain).
Then V_acoustics (15 files — overlaps with signal processing, good cross-check).
Then W_geophysics (22 files, seismic FWI is highest-δ principle in this cluster).

## Definition of done
- All ~147 principles have L1/L2/L3 JSON in principles/<domain>/
- All JSONs validate against schema
- Checklist passes for all

## How to signal completion
1. Update `../../coordination/agent-coord/progress.md` — mark physics principles DONE
2. Open PR: `feat/genesis-principles-physics`
