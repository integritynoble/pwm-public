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

## v2 PWDR Principles (gate_class: physical_with_discrete_readout)

These are paired analytical-core + PWDR-wrapper Principles per the v2 design in `pwm_overview2.md` § 4-7 and the canonical Option-3 recast pattern. Each PWDR wraps an analytical core (either pre-existing in v1 genesis or newly-authored alongside) with a deterministic threshold function on recovered physical state.

| L1 ID (PWDR) | L1 ID (analytical core) | Name | Primary domain folder | Threshold readout | Status |
|---|---|---|---|---|---|
| L1-512 | L1-511 (newly authored) | PillCam-SPECTRA Bleeding-Region Detection | `C_medical_imaging/` | mucosal-region categorical {normal, bleeding, polyp, suspected_neoplasia, mucosal_inflammation} | **Authored** |
| L1-513 | L1-049 (existing fundus) | Diabetic Retinopathy ETDRS Grading | `C_medical_imaging/` | ETDRS severity {none, mild_NPDR, moderate_NPDR, severe_NPDR, PDR} | **Authored** |
| L1-514 | L1-029 (existing CT) | Chest CT Pneumonia/COVID Severity (TSS / CO-RADS) | `C_medical_imaging/` | TSS [0-25] + CO-RADS {1-5} | **Authored** |
| L1-515 | L1-036 (existing mammography) | Mammographic Breast Density BI-RADS | `C_medical_imaging/` | BI-RADS density category {A, B, C, D} | **Authored** |
| L1-516 | L1-044 (existing MRS) | MRS Tumor Grading | `C_medical_imaging/` | brain WHO I-IV / prostate Gleason / breast benign-malignant | **Authored** |
| L1-517 | L1-049 (existing fundus, sibling reflectance core) | Dermoscopy Skin Lesion Malignancy | `C_medical_imaging/` | {benign nevus, atypical, suspected_melanoma, BCC, SCC, seborrheic_keratosis, actinic_keratosis} | **Authored** |
| L1-519 | L1-518 (newly authored XRD core) | XRD Crystal Space-Group Classification | `Z_materials_science/` | 230 space groups (or coarser: 7 crystal systems / 14 Bravais / 32 point groups) | **Authored** |
| L1-520 | L1-413 (existing HMM Sequence Alignment, sibling) | RNA-seq Cell-Type Classification | `AE_computational_bio/` | canonical cell-type taxonomy (immune, epithelial, stromal, neural sub-classes per CellMarker / PanglaoDB / Tabula Sapiens) | **Authored** |
| L1-521 | L1-294 (existing DFT) | Drug-Target Binding Affinity Classification | `X_comp_chemistry/` | {non_binder, weak, moderate, strong, ultra_strong} per Delta-G threshold | **Authored** |
| L1-522 | L1-278 (existing Earthquake Source Inversion) | Earthquake Magnitude Classification | `W_geophysics/` | Mw + categorical {micro, minor, light, moderate, strong, major, great} per Hanks-Kanamori 1979 | **Authored** |
| L1-523 | L1-031 (existing X-ray radiography) | Pneumothorax Detection from Chest X-ray | `C_medical_imaging/` | severity {none, small <15%, moderate 15-30%, large >30%, tension} per Light index 1985 | **Authored** |
| L1-524 | L1-029 (existing CT, dynamic-perfusion mode) | Stroke Ischemic Core / Penumbra Classification (CTP) | `C_medical_imaging/` | triage {no_intervention, IV_thrombolytic, MT_candidate, extended_window_LVO} per DAWN/DEFUSE-3 | **Authored** |
| L1-525 | L1-029 (existing CT, CTPA mode) | Pulmonary Embolism Detection from CTPA | `C_medical_imaging/` | severity {no_PE, isolated_subsegmental, segmental, lobar, central, saddle} + RV-strain per ESC 2019 | **Authored** |
| L1-526 | L1-031 (existing X-ray radiography) | Bone Fracture Detection | `C_medical_imaging/` | severity {none, hairline, complete, displaced, comminuted, intra-articular} + AO/OTA classification | **Authored** |
| L1-527 | L1-031 (existing X-ray radiography) | Knee/Hip OA Kellgren-Lawrence Grading | `C_medical_imaging/` | KL {0, 1, 2, 3, 4} per Kellgren-Lawrence 1957 | **Authored** |
| L1-528 | L1-388 (existing Blind Source Separation) | ECG Arrhythmia Classification | `AD_signal_processing/` | AAMI EC57 {N, S, V, F, Q} per beat | **Authored** |
| L1-529 | L1-049 (existing fundus) | Glaucoma Optic-Disc Cupping | `C_medical_imaging/` | {normal, suspect, glaucoma_likely, advanced} per ICO 2016 + ISNT-rule | **Authored** |
| L1-530 | L1-042 (existing OCT) | AMD OCT Grading | `C_medical_imaging/` | {no_AMD, early, intermediate, late_dry_GA, late_wet_CNV} per AREDS / Beckman | **Authored** |
| L1-531 | L1-068 (existing EEG) | EEG Seizure Detection | `C_medical_imaging/` | seizure type per ILAE 2017 + status epilepticus per Trinka 2015 | **Authored** |
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
| 2026-04-30 | Director requested expanding genesis to include v2 PWDR Principles at higher ratio. First v2 batch authored: L1-511 PillCam-SPECTRA optical core (analytical, n_c=1, L_DAG=4.9) + L1-512 PWDR wrapper (n_c=1, L_DAG=6.9, links L1-511 as physics_core). UTSW GI imaging context. |
| 2026-04-30 | L1-513 Diabetic Retinopathy ETDRS Grading PWDR authored (UTSW Ophthalmology; FDA-cleared autonomous AI; n_c=1, L_DAG=5.0). Wraps existing L1-049 fundus core. |
| 2026-04-30 | L1-514 Chest CT Pneumonia/COVID Severity PWDR authored (UTSW Radiology; universal pneumonia/COVID grading; n_c=1, L_DAG=5.7). Wraps existing L1-029 CT core. |
| 2026-04-30 | L1-515 Mammographic Breast Density BI-RADS PWDR authored (UTSW Simmons Cancer Center; MQSA-mandated; n_c=1, L_DAG=5.8). Wraps existing L1-036 mammography core. **First v2 PWDR batch in genesis: 4 universally-deployed UTSW-relevant PWDR Principles + 1 newly-authored analytical core.** |
| 2026-04-30 | Round 2: L1-516 MRS Tumor Grading PWDR authored (n_c=1, L_DAG=5.9) wrapping existing L1-044 MRS — universal in neuro-oncology, prostate, breast cancer characterization. UTSW Simmons. |
| 2026-04-30 | Round 2: L1-517 Dermoscopy Skin Lesion Malignancy PWDR authored (n_c=1, L_DAG=4.9) wrapping L1-049 fundus as sibling reflectance-imaging core — ABCDE / 7-point / Menzies clinical rules. UTSW Dermatology. |
| 2026-04-30 | Round 2: L1-518 XRD analytical core authored (NEW, n_c=1, L_DAG=6.8) plus L1-519 XRD Space-Group Classification PWDR authored (n_c=1, L_DAG=6.8) — International Tables Vol A 230 space groups. Universal in materials science, structural chemistry, pharma polymorph identification. **Round 2 complete: 9 v2 PWDR Principles + 2 newly-authored analytical cores in genesis after this round.** |
| 2026-04-30 | Round 3: L1-520 RNA-seq Cell-Type Classification PWDR authored (computational biology; UTSW Children's Medical Center Research Institute + Simmons Cancer Center single-cell programs; n_c=1, L_DAG=8.3). Wraps L1-413 HMM Sequence Alignment as sibling computational-biology core. |
| 2026-04-30 | Round 3: L1-521 Drug-Target Binding Affinity Classification PWDR authored (UTSW Drug Discovery Institute + Simmons oncology drug development; n_c=1, L_DAG=7.0). Wraps existing L1-294 DFT. |
| 2026-04-30 | Round 3: L1-522 Earthquake Magnitude Classification PWDR authored (universal seismology; USGS / JMA / EMSC / GFZ / ISC global use; n_c=1, L_DAG=6.3). Wraps existing L1-278 Earthquake Source Inversion. **Round 3 complete: 12 v2 PWDR Principles + 2 newly-authored analytical cores in genesis. Total v2 entries: 14.** |
| 2026-04-30 | Round 4: L1-523 Pneumothorax Detection from Chest X-ray PWDR authored (UTSW Emergency / Trauma Center; FDA-cleared autonomous AI Aidoc/Lunit/Annalise/Qure.ai; n_c=1, L_DAG=4.6). Wraps existing L1-031 X-ray radiography. |
| 2026-04-30 | Round 4: L1-524 Stroke CTP Triage PWDR authored (UTSW Stroke Center Level-1; DAWN/DEFUSE-3 trial criteria; commercial RAPID/Olea/Brainomix; n_c=2, L_DAG=7.3). Wraps existing L1-029 CT in dynamic-perfusion mode. |
| 2026-04-30 | Round 4: L1-525 Pulmonary Embolism CTPA PWDR authored (UTSW Emergency + Pulmonary Hypertension Program; ESC 2019 / AHA 2011 guidelines; commercial Aidoc/RapidAI/Avicenna; n_c=1, L_DAG=7.0). Wraps existing L1-029 CT in CTPA mode. **Round 4 complete: 15 v2 PWDR Principles + 2 newly-authored analytical cores in genesis. Total v2 entries: 17. Genesis count: 525 L1 manifests.** |
| 2026-04-30 | Round 5: L1-526 Bone Fracture PWDR (UTSW Emergency / Orthopedic Surgery; AO/OTA classification; commercial Aidoc Bone, Gleamer BoneView, RBfracture, OsteoDetect; n_c=1, L_DAG=4.6). Wraps L1-031. |
| 2026-04-30 | Round 5: L1-527 Knee/Hip OA Kellgren-Lawrence PWDR (UTSW Orthopedic + Rheumatology; KL 1957 international standard; n_c=1, L_DAG=4.6). Wraps L1-031. |
| 2026-04-30 | Round 5: L1-528 ECG Arrhythmia AAMI PWDR (UTSW Cardiology + ICU; AAMI EC57 standard; commercial Apple Watch ECG, KardiaMobile, Zio Patch; n_c=1, L_DAG=5.9). Wraps L1-388 BSS as sibling biomedical-signal-processing core. |
| 2026-04-30 | Round 6: L1-529 Glaucoma Optic-Disc Cupping PWDR (UTSW Ophthalmology glaucoma clinic; ICO 2016 + DDLS guidelines; n_c=1, L_DAG=5.6). Wraps L1-049 fundus. |
| 2026-04-30 | Round 6: L1-530 AMD OCT Grading PWDR (UTSW Ophthalmology retina clinic; AREDS / Beckman 2013 classification; commercial DeepMind retinal AI, Heidelberg AnyDrusen, NotalVision; n_c=1, L_DAG=5.6). Wraps L1-042 OCT. |
| 2026-04-30 | Round 6: L1-531 EEG Seizure Detection PWDR (UTSW Comprehensive Epilepsy Center Level-4; ILAE 2017 Operational Classification + Trinka 2015 status epilepticus; commercial Persyst, Natus, BioSerenity, NeuroPace RNS; n_c=1, L_DAG=6.0). Wraps L1-068 EEG. **Rounds 5+6 complete: 21 v2 PWDR Principles + 2 newly-authored analytical cores in genesis. Total v2 entries: 23. Genesis count: 531 L1 manifests.** |
| _TBD_ | Path A genesis batch complete (Director's pick); registry reflects all Authored entries. |
| _TBD_ | Mainnet deploy at Step 7; this registry becomes the on-chain catalog of v3 standalone genesis Principles. |
