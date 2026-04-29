# Adding v3 Principles to genesis right now — operational paths

**Date:** 2026-04-29
**Owner:** Director
**Audience:** Director, deploy operators, Principle authors
**Status:** operational document — three execution paths depending on Step 7 timeline
**Cross-references:**
- `pwm-team/pwm_product/genesis/PWM_V3_STANDALONE_VS_COMPOSITE.md` (the design recommendation this operationalizes)
- `pwm-team/pwm_product/genesis/PWM_V2_GENESIS_INCLUSION.md` (parallel v2 batch decision)
- `pwm-team/pwm_product/genesis/PWM_V3_COMPOSITES_AND_GENESIS_COMPONENTS.md` (component-coverage audit)
- `pwm-team/pwm_product/genesis/PWM_RESERVE_RESIZING_FOR_V2_V3.md` (parallel Reserve decision)
- `pwm-team/coordination/MAINNET_DEPLOY_HANDOFF.md` (the 13-step deploy chain; Step 7 = mainnet contract deploy)

---

## TL;DR

**Yes, v3 Principles can be added to the auto-promoted genesis batch right now.** The window is fully open — Base mainnet is not yet deployed (Step 7 blocked on Director ETH funding), no contract changes are needed (standalone multi-physics registers as v1-analytical with high L_DAG), and no audit re-run is required. The only real constraint is authoring time. Three execution paths trade off authoring effort against time-to-Step-7.

---

## The window check

| Constraint | Status |
|---|---|
| Base mainnet deployed? | **No** — Step 7 still blocked on deployer ETH funding |
| `register_genesis.js` executed against mainnet? | **No** — only Sepolia (testnet) |
| Contract changes needed for standalone v3 Principles? | **None** — they register as v1-analytical with `n_c > 0` in the L_DAG breakdown |
| Audit re-run needed? | **None** — the v1 audit certified contract logic, not manifest content |
| v3 spec clarifications need to ratify first? | **No** — standalone form already fits under v1 § 3; the v3 § 5.0 clarification in `PWM_V3_STANDALONE_VS_COMPOSITE.md` makes the pattern explicit but isn't required for Principle validity |
| Re-audit of contracts? | **No — manifest content is off-chain JSON; v1 contracts only see the hash** |

The window is fully open. Authoring time is the only constraint.

---

## Three execution paths

### Path A — fastest (1-2 weeks): 1-2 high-confidence standalone v3 Principles

Pick the multi-physics topics where the joint forward model is uncontroversial in the literature, the L_DAG is moderate, and a single careful authoring session can produce a quality manifest.

**Recommended picks:**

1. **Fluid-structure interaction (FSI)** — joint Navier-Stokes + linear elasticity coupled at a shared boundary
   - Math: textbook ALE-FEM, immersed-boundary, fictitious-domain methods
   - W certificate: Coutand-Shkoller existence/uniqueness proofs (well-established)
   - C certificate: Bazilevs et al. ALE-FEM convergence theory
   - L_DAG ≈ 6-8 with `n_c = 2` (boundary-coupling constraints)
   - Authoring time: ~3-5 days for an experienced author
   - Components already in genesis: `L1-170_incompressible_ns.json`, `L1-207_linear_elasticity.json` (cited in `related_principles` informationally)

2. **Multi-scale materials simulation** — joint DFT + MD + continuum mechanics with built-in scale bridging
   - Math: Hellmann-Feynman forces, time-temperature superposition, homogenization tensors
   - L_DAG ≈ 9-11 with `n_c = 4` (two scale-bridging coupling constraints, forward and adjoint)
   - Authoring time: ~5-7 days
   - Components already in genesis: `L1-294_density_functional_theory.json`, `L1-298_ab_initio_md.json`, `L1-215_hyperelasticity.json`

**Outcome:** 2 standalone v3 Principles in genesis. If Director wants to push Step 7 within 2 weeks, this is the realistic ceiling.

**Cost:** ~1-2 weeks elapsed; $0 contract changes; Director or one expert author.

---

### Path B — medium (4-6 weeks): 3-4 standalone v3 Principles

Path A plus:

3. **Multi-messenger astronomy** — GW + optical + neutrino joint event localization
   - Joint forward: `P(event | t, sky) = ∫ s_GW(t, θ) · I_optical(t, θ) · ν_flux(t, θ) dθ`
   - L_DAG ≈ 6-8
   - Authoring time: ~2 weeks (also requires authoring the neutrino direction-of-arrival primitive — small additional component)
   - Reference: LIGO/Virgo + Zwicky Transient Facility + IceCube joint detection literature

4. **Climate-system attribution** — coupled atmosphere-ocean-ice-land primitive equations
   - Joint forward: `T_anomaly = f_atm(CO2) + f_ocean(heat) + f_ice(albedo) + f_land(carbon)`
   - L_DAG ≈ 10-12 with `n_c = 6`
   - Authoring time: ~3 weeks (highest L_DAG; most certificate work)
   - Reference: CESM, GFDL, HadGEM Earth-system model documentation

**Outcome:** 4 standalone v3 Principles in genesis spanning structural-fluid, materials, astrophysics, and earth-system science. Strong "PWM is a physics-grounded multi-domain protocol" signal at genesis.

**Cost:** ~4-6 weeks elapsed (parallelizable across 2-3 authors); ~$10K-25K Reserve grants if contracted out; or Director + 1 collaborator.

---

### Path C — full plan (10-12 weeks): the complete pre-mainnet expansion

Path B plus:

5. **Genome → protein → metabolism analytical sub-chain** — codon translation + protein folding + flux-balance analysis
   - Joint forward: `metabolism_state(genotype) = FBA( fold_energy_min( translate(genotype) ) )`
   - L_DAG ≈ 7-9
   - Authoring time: ~2-3 weeks
   - Reference: AlphaFold-style energy minimization + Cobra Toolbox FBA

6. **Earthquake-tsunami warning cascade** (already in v2 batch as `physical_with_discrete_readout`)
   - Per `PWM_V2_GENESIS_INCLUSION.md` candidate list

Plus the parallel batches:

- **10-15 v2 PWDR exemplars** from `PWM_V2_GENESIS_INCLUSION.md`
- **4 missing analytical components** from `PWM_V3_COMPOSITES_AND_GENESIS_COMPONENTS.md` (neutrino DoA, ice-sheet dynamics, flux-balance analysis, possibly GCM upgrade) — note that some of these are already covered by the multi-physics batch above

**Outcome:** Full genesis expansion to ~525 Principles, all auto-promoted, spanning analytical / PWDR / standalone multi-physics across imaging, physics, chemistry, biology, astronomy, earth science.

**Cost:** ~10-12 weeks elapsed (parallelizable across 3-5 authors); ~$30K-60K Reserve grants for contracted authoring.

If Director funds Reserve grants to domain experts (climate scientist, materials scientist, computational biologist, astrophysicist), this can compress to ~6-8 weeks calendar time.

---

## Path comparison

| Path | Time | New v3 in genesis | Total genesis size | Reserve grant cost | Author count |
|---|---|---|---|---|---|
| A (fastest) | 1-2 weeks | 2 | 504 | $0 (Director-authored) | 1 |
| B (medium) | 4-6 weeks | 4 | 506 | ~$10-25K | 2-3 |
| C (full) | 10-12 weeks (~6-8 with parallelism) | 5-6 + 10-15 v2 + 4 components | ~525 | ~$30-60K | 3-5 |

All three paths are **zero contract change, zero re-audit, and within the open pre-mainnet window**. The choice is purely about authoring effort vs Director's Step 7 timeline.

---

## What can start immediately

If Director wants to start now, the first standalone v3 manifest can be drafted in this session:

**FSI is the recommended first pick** because:

- Math is canonical (no novel research needed)
- Components already in genesis as references (NS, elasticity)
- L_DAG calculation is straightforward
- Joint W and C certificates have textbook treatments (Coutand-Shkoller; Bazilevs et al.)
- It's the most-recognized multi-physics example in computational science — high credibility for genesis
- Single session sufficient for a quality first draft

**Output would be:**

- A new file at `pwm-team/content/agent-physics/principles/T_structural_mechanics/L1-NNN_fluid_structure_interaction.json` (NNN = next available L1 ID), or under a new `agent-applied/AP_multiphysics/` subtree if Director prefers grouping standalone multi-physics separately
- Following the schema of existing analytical L1 manifests (verified against `L1-170_incompressible_ns.json` and `L1-207_linear_elasticity.json`)
- With `gate_class: "analytical"` and `n_c = 2` in the L_DAG breakdown
- A `related_principles: [L1-170, L1-207]` field — informational only, no royalty implication
- Joint forward model written in mathematical notation
- Joint S1-S4 certificates with citations
- P1-P10 validation table

Director reviews, validates, and either commits to genesis or sends back for revision.

---

## Recommendation

**Start with Path A — author FSI + multi-scale materials in this session and the next.** Reasons:

1. **Validates the standalone-as-default pattern in practice.** The current `PWM_V3_STANDALONE_VS_COMPOSITE.md` is a design proposal. Putting two concrete manifests in the repo proves the pattern works and gives reviewers something tangible to evaluate.

2. **Gives Director something to show for the v2/v3 program before Step 7.** When co-founders / reviewers / future grant applications ask "what does PWM cover beyond imaging physics?", Director can point at FSI and multi-scale materials in the genesis batch — concrete, on-chain, auto-promoted from epoch 1.

3. **Doesn't block Step 7.** If Director needs to push mainnet deploy within 2 weeks for unrelated reasons (deployer ETH availability, calendar pressure, audit-tag freshness), Path A is the only option that fits. Paths B and C compress at the cost of author breadth.

4. **Expandable.** If Path A's first 2 manifests land cleanly, Director can decide to extend to Path B / Path C without renegotiating the design. The pattern is already validated.

**If Step 7 is more than 4 weeks out, escalate to Path B.** If Step 7 is more than 10 weeks out, Path C is realistic and gives the strongest genesis composition.

---

## Practical execution checklist

Whichever path Director picks:

### For each new standalone v3 Principle

- [ ] Pick L1 ID (next available — current max is `L1-502` per the 502 genesis count)
- [ ] Choose directory: `agent-physics/`, `agent-imaging/`, `agent-chemistry/`, `agent-applied/`, or new `agent-applied/AP_multiphysics/`
- [ ] Author manifest JSON following existing schema
- [ ] Run validation: P1-P10 + S1-S4 + d_principle distance check (must be ≥ 0.30 from all existing genesis Principles to avoid duplicate-redirect advisory)
- [ ] Sanity-check L_DAG calculation
- [ ] Add path to `register_genesis.js` registration list
- [ ] Sepolia dry-run to verify the new entry registers cleanly

### Pre-mainnet deploy

- [ ] Verify final genesis count matches expectation (504 / 506 / ~525 depending on path)
- [ ] All new manifests committed to repo
- [ ] `register_genesis.js` updated and tested
- [ ] Director re-signs the audit-clean attestation if any new manifests landed after the prior signing (the contract bytecode is unchanged so the audit still applies, but the deployment record should reflect the final genesis state)

### Mainnet deploy at Step 7

- [ ] Same as the existing Step 7 procedure in `MAINNET_DEPLOY_HANDOFF.md`
- [ ] After successful deploy, all new v3 standalone Principles are auto-promoted and share A_k from epoch 1

---

## Open questions

1. **Director's preferred Step 7 timeline?** This determines which path to pick.

2. **Director-authored vs contracted-out?** Director's UTSW context is well-suited for the medical-AI / multi-physics topics. Astrophysics and climate science are stronger Reserve-grant candidates.

3. **Subtree organization?** Put standalone multi-physics under existing subtrees (closest physics domain) or create a new `agent-applied/AP_multiphysics/` subtree? Recommendation: new subtree, more visible to future contributors.

4. **Naming convention?** `L1-NNN_fluid_structure_interaction.json` matches existing imaging convention. Multi-physics names could include all coupled fields: `L1-NNN_FSI_NS_elasticity.json`. Recommendation: short canonical names; the manifest content describes the coupling.

5. **Should I draft FSI now?** Yes / no decision from Director. If yes, the manifest lands in this session.

---

## Decision log

| Date | Decision |
|---|---|
| 2026-04-29 | Director asked whether v3 Principles can be added to genesis now. Analysis confirmed: window open, no contract / audit blockers, only authoring time. Three paths documented (A/B/C). Recommended Path A start with FSI + multi-scale materials. |
| _TBD_ | Director picks Path A / B / C based on Step 7 timeline. |
| _TBD_ | First standalone v3 manifest (likely FSI) drafted. |
| _TBD_ | Manifest validated against P1-P10 + S1-S4. |
| _TBD_ | Path-specific manifests batch-validated and committed. |
| _TBD_ | `register_genesis.js` updated; Sepolia dry-run successful. |
| _TBD_ | Mainnet deploy at Step 7 with the expanded genesis batch. |

---

## Summary table

| Question | Answer |
|---|---|
| Can v3 Principles be added to genesis right now? | **Yes.** The pre-mainnet window is open; no contract or audit blockers. |
| What's the constraint? | **Authoring time only.** |
| What's the fastest path? | **Path A (1-2 weeks)**: author 2 standalone multi-physics Principles (FSI + multi-scale materials), Director-authored. |
| What's the most ambitious path? | **Path C (10-12 weeks; ~6-8 weeks parallelized)**: full pre-mainnet expansion to ~525 Principles spanning analytical / PWDR / standalone multi-physics. |
| Cost? | **$0 contract changes**; ~$0-60K Reserve grants depending on path. |
| Why standalone v3 instead of composite v3 at genesis? | Composite needs `PWMRewardV2` for proper 0.4/0.6 royalty split; v1 contracts can't handle multi-parent royalty. Standalone registers cleanly as v1-analytical with high L_DAG and full single-creator royalty. |
| When does the window close? | **At Step 7** — the mainnet `deploy/mainnet.js` execution. After that, genesis is frozen. |
| What blocks Step 7 currently? | Director ETH funding for the deployer wallet (per `MAINNET_DEPLOY_HANDOFF.md`). Independent of the genesis composition decision. |
| Recommended action right now? | **Path A — author FSI + multi-scale materials this and next session.** Validates the standalone pattern and gives Director something concrete before Step 7. |
| Should Claude draft FSI now? | **Director's call.** If yes, the manifest can land in the next session. |
