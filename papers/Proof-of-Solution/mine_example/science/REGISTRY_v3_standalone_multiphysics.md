# Registry: v3 standalone multi-physics Principles

**Date:** 2026-04-29
**Owner:** Director (PWM)
**Audience:** Principle authors, reviewers, deploy planners
**Status:** living index — updated as new v3 standalone Principles are authored
**Cross-references:**
- `pwm/papers/Proof-of-Solution/pwm_overview3.md` § 5.0 (composite-as-opt-in; standalone-as-default)
- `pwm/pwm-team/pwm_product/genesis/PWM_V3_STANDALONE_VS_COMPOSITE.md` (the design document)
- `pwm/pwm-team/pwm_product/genesis/PWM_V3_MEDICAL_IMAGING_CANDIDATES.md` (the eight medical imaging candidates)
- `pwm/pwm-team/content/agent-imaging/CLAUDE.md` (the v2/v3-aware schema template)

---

## What this registry is

This is a **cross-cutting index** of v3 standalone multi-physics Principles in the PWM genesis catalog. It catalogs Principles whose forward operators have **`n_c > 0` coupling constraints** in their L_DAG — i.e., genuine multi-physics joint forward models, not single-physics inverse problems.

These Principles register through the v1 `PWMRegistry` as layer-1 entries with `gate_class: "analytical"` and full single-creator royalty. They are auto-promoted at genesis and share A_k from epoch 1, exactly like single-physics analytical Principles. The "v3-ness" of these Principles comes from:

1. Joint coupled forward model with `n_c > 0` (multi-physics)
2. `v3_metadata` block in the manifest declaring `is_standalone_multiphysics: true`
3. Joint W and C certificates that prove well-posedness and convergence for the *coupled* system, not the components separately
4. Eligibility for v3 hierarchical SUB_DOMAIN routing once `pwm_overview3.md` § 2 deploys

---

## Why this registry exists (and not a directory move)

The source MD files for each Principle live in their **primary domain folder** (e.g., QSM source MD lives under `C_medical_imaging/` because it's MR-based imaging). This is the right organizational primitive for domain experts authoring or reviewing Principles.

But standalone multi-physics Principles cut across domains — they're genuinely both medical imaging AND electromagnetism (QSM), or imaging AND mechanics (OCE), or imaging AND chemistry (HP-13C MRI). Without a cross-cutting index, the multi-physics nature is invisible from the per-domain folder structure.

**This registry provides that cross-cutting view without moving any source files.** Symlinks in `pwm-team/content/agent-{imaging,physics,chemistry,applied,signal}/source/` continue to work unchanged. Per-domain organization is preserved. Authors find Principles by domain; reviewers find multi-physics Principles by this index.

---

## Registry table

| L1 ID | Name | Primary domain folder | Carriers / coupling | `n_c` | L_DAG | Status |
|---|---|---|---|---|---|---|
| L1-503 | Quantitative Susceptibility Mapping (QSM) | `C_medical_imaging/` | MR (radio_wave) ⊗ Maxwell magnetostatic | 2 | 7.4 | **Authored** (genesis-eligible) |
| L1-504 | Quantitative Photoacoustic Tomography (qPAT) | `C_medical_imaging/` | optical diffusion ⊗ thermoelastic Grüneisen ⊗ acoustic wave | 2 | 8.5 | **Authored** (genesis-eligible) |
| L1-505 | Pharmacokinetic Dynamic PET (PK-PET) | `C_medical_imaging/` | photon transport (annihilation) ⊗ compartmental ODE kinetics | 2 | 8.3 | **Authored** (genesis-eligible) |
| L1-506 | Hyperpolarized 13C Metabolic MRI | `C_medical_imaging/` | DNP ⊗ chemical exchange ODE ⊗ chemical-shift MR | 3 | 10.4 | **Authored** (genesis-eligible) |
| L1-507 | Joint MEG-EEG Source Imaging | `C_medical_imaging/` | Maxwell magnetostatic ⊗ Poisson electrostatic ⊗ head volume conductor | 2 | 10.0 | **Authored** (genesis-eligible) |
| L1-508 | Optical Coherence Elastography (OCE) | `C_medical_imaging/` | phase-sensitive OCT ⊗ linear elasticity wave ⊗ applied loading | 2 | 8.4 | **Authored** (genesis-eligible) |
| L1-509 | Photoacoustic-Ultrasound Dual-mode (PAUS) | `C_medical_imaging/` | qPAT chain ⊗ pulse-echo ultrasound | 2 | 9.5 | **Authored** (genesis-eligible) |
| L1-510 | Cardiac 4D-flow MRI with hemodynamic biomechanics | `C_medical_imaging/` | MR phase-contrast ⊗ incompressible Navier-Stokes ⊗ physiological BC | 2 | 8.3 | **Authored** (genesis-eligible) |
| _TBD_ | Fluid-Structure Interaction (FSI) | `R_fluid_dynamics/` or `T_structural_mechanics/` | Navier-Stokes ⊗ linear elasticity | 2 | ~6-8 | Candidate — see `PWM_V3_STANDALONE_VS_COMPOSITE.md` |
| _TBD_ | Multi-scale materials simulation | `Z_materials_science/` | DFT ⊗ MD ⊗ continuum mechanics | 4 | ~9-11 | Candidate |
| _TBD_ | Climate-system attribution | `AF_environmental_sci/` | atmosphere ⊗ ocean ⊗ ice ⊗ biosphere | 6 | ~10-12 | Candidate |
| _TBD_ | Multi-messenger astronomy | `AC_astrophysics/` | gravitational waves ⊗ optical ⊗ neutrino | 2 | ~6-8 | Candidate |
| _TBD_ | Earthquake → tsunami warning cascade | `W_geophysics/` | seismic FWI ⊗ shallow-water ⊗ threshold readout | 2 | ~7-9 | Candidate (PWDR variant — has discrete readout) |
| _TBD_ | Genome → protein → metabolism analytical sub-chain | `AE_computational_biology/` | codon translation ⊗ protein folding ⊗ FBA | 2 | ~7-9 | Candidate |

---

## How to add a new entry

When a v3 standalone multi-physics Principle is authored:

1. The author creates the L1 manifest in the primary domain folder under `pwm/pwm-team/content/agent-<X>/principles/<DOMAIN>/L1-NNN_<name>.json` following the schema in `pwm-team/content/agent-imaging/CLAUDE.md` (or the per-agent CLAUDE.md for non-imaging domains once those are updated).

2. The manifest must include:
   - `gate_class: "analytical"` (since standalone multi-physics is the v1-analytical class with `n_c > 0`)
   - `G.n_c >= 2` (the multi-physics signal)
   - `G.coupling_constraints` array describing each coupling
   - `v3_metadata` block with `is_standalone_multiphysics: true`, `coupling_count_n_c`, `joint_well_posedness_references`, `distinctness_audit`, optional `clinical_context`
   - `related_principles` listing component / sibling / parent Principles (informational only — no royalty implication)

3. The author appends a new row to **this registry** with the L1 ID, name, primary domain folder, carrier-coupling description, `n_c`, L_DAG, and Status. Move the row from "Pending" or "Candidate" to "Authored" once the manifest validates.

4. The author commits both the manifest JSON and the registry update in a single PR, with a descriptive commit message naming the new Principle's coupled physics.

---

## Status legend

- **Authored** — manifest JSON exists in repo; validates against schema; ready for `register_genesis.js` inclusion
- **Pending** — Director has named the candidate; manifest not yet authored
- **Candidate** — listed in design docs as a viable v3 standalone direction; awaits Director prioritization

When **Authored** count reaches 5+, this registry should be the primary source for the v3 standalone genesis batch in `register_genesis.js`. Until then, refer to `PWM_V3_GENESIS_NOW.md` Path A/B/C for the operational rollup.

---

## Why this is necessary now (vs after v3 deploy)

Two reasons:

1. **Pre-mainnet window is open.** Base mainnet is not yet deployed (Step 7 blocked on Director ETH funding). The genesis batch can be expanded to include v3 standalone multi-physics Principles, which then auto-promote and share A_k from epoch 1.

2. **The registry is forward-compatible.** When v3 deploys `PWMRegistryV2` with hierarchical SUB_DOMAIN structure, the v3 standalone Principles already registered via v1 carry `domain` and `sub_domain` fields in their manifest JSON (per `pwm_overview3.md` § 2.1 and the schema update in `agent-imaging/CLAUDE.md`). Governance backfills V2's hierarchy registry with a single multisig batch reading directly from the manifests — no re-registration, no royalty redistribution.

Without this registry, the cross-cutting nature of standalone multi-physics is invisible from the per-domain folder structure, and authors of new Principles will under-author the multi-physics field, mistakenly assuming v1-analytical means single-physics only.

---

## Decision log

| Date | Decision |
|---|---|
| 2026-04-29 | Director asked to reorganize `papers/Proof-of-Solution/mine_example/science/`. Chose Option I (minimal): keep per-domain organization; add this cross-cutting registry. Avoids breaking symlinks, preserves domain-expertise organization, makes multi-physics discoverable. First entry: L1-503 QSM (authored). |
| 2026-04-29 | L1-504 qPAT authored — joint optical diffusion + thermoelastic Grüneisen + acoustic wave; n_c=2; L_DAG=8.5; d_principle ~ 0.42 from L1-041 PAT (Distinct). Status: Authored. |
| 2026-04-29 | L1-505 PK-PET authored — joint photon transport + compartmental ODE tracer kinetics; n_c=2; L_DAG=8.3; d_principle ~ 0.55 from L1-033 PET (Distinct). Status: Authored. Path B target reached. |
| 2026-04-29 | L1-506 HP-13C MRI authored — joint DNP + chemical-exchange ODE + chemical-shift MR readout; n_c=3; L_DAG=10.4; d_principle ~ 0.60 from L1-044 MRS (Distinct). Status: Authored. Path B complete (4 medical imaging v3 standalone Principles in genesis). |
| 2026-04-29 | L1-507 Joint MEG-EEG Source Imaging authored — Maxwell magnetostatic + Poisson electrostatic + shared head volume conductor; n_c=2; L_DAG=10.0; d_principle ~ 0.50 from L1-067 MEG and L1-068 EEG (Distinct from each parent). Status: Authored. |
| 2026-04-29 | L1-508 Optical Coherence Elastography (OCE) authored — phase-sensitive OCT + linear elasticity wave + applied loading; n_c=2; L_DAG=8.4; d_principle ~ 0.45 from L1-042 OCT and L1-047 elastography (Distinct). Status: Authored. |
| 2026-04-29 | L1-509 PAUS dual-mode authored — qPAT chain + pulse-echo US with shared tissue acoustic; n_c=2; L_DAG=9.5; d_principle ~ 0.40 from L1-504 qPAT and L1-032 US (Distinct). Status: Authored. |
| 2026-04-29 | L1-510 Cardiac 4D-flow MRI with biomechanics authored — MR phase-contrast + incompressible Navier-Stokes + physiological BC; n_c=2; L_DAG=8.3; d_principle ~ 0.50 from L1-058 MRA (Distinct). Status: Authored. **Path C complete: all 8 medical imaging v3 standalone candidates from PWM_V3_MEDICAL_IMAGING_CANDIDATES.md are now in genesis.** |
| _TBD_ | Path A genesis batch complete (Director's pick); registry reflects all Authored entries. |
| _TBD_ | Mainnet deploy at Step 7; this registry becomes the on-chain catalog of v3 standalone genesis Principles. |
