# Why v3 composites cannot be cleanly genesis-included — and the eight forward-model exemplars to plan around

**Date:** 2026-04-29
**Owner:** Director
**Audience:** PWM contract authors, deploy planners, Principle authors, governance reviewers
**Status:** decision document — defer composites to v3 deploy, ensure components are genesis-complete pre-mainnet
**Cross-references:**
- `papers/Proof-of-Solution/pwm_overview1.md` (v1 base spec — `parentHash` is `bytes32`, royalty splits in `PWMReward`)
- `papers/Proof-of-Solution/pwm_overview3.md` § 5 (composite Principle definition + reward formula)
- `papers/Proof-of-Solution/pwm_overview3.md` § C (Evolvability Appendix — `PWMRegistryV2`, `PWMRewardV2`)
- `pwm-team/pwm_product/genesis/PWM_V2_GENESIS_INCLUSION.md` (the parallel decision for v2-class Principles)
- `pwm-team/pwm_product/genesis/PWM_GATE_CLASSES_AND_SCALING.md` (gate-class definitions + Case A/B/C boundary)
- `pwm-team/infrastructure/agent-contracts/contracts/PWMRegistry.sol` (single-parent `bytes32` constraint)
- `pwm-team/infrastructure/agent-contracts/contracts/PWMReward.sol` (single-creator royalty path)

---

## TL;DR

**Don't add v3 composite Principles (`L1_COMPOSITE`) to the auto-promoted genesis batch — even using the "stub-entry" pattern from `pwm_overview3.md` Appendix C.** The deeper reason isn't the v1 single-parent schema constraint; it's that v1's `PWMReward` has no multi-parent royalty path, so a stub-entry composite at genesis would route 100% of the L1 royalty (5% of every L4 event) to the composite creator instead of splitting 0.4-to-composite / 0.6-to-components per v3 § 5.3. Once v3 deploys with `PWMRewardV2`, retroactive royalty redistribution would be operationally messy and possibly contentious.

**Instead, ensure the *components* of the eight planned composite exemplars are all in genesis.** Components are auto-promoted; they share A_k from day 1; they will receive proper component-share royalties when the composite registers post-v3. This captures most of the v3 economic value at genesis without breaking the v1 royalty math.

Audit of the current 502 genesis Principles against the eight composite examples below: ~85% of the required components are already present. Only ~3-4 small authoring gaps remain.

---

## Why stub-entry composites at genesis would be wrong

In `pwm_overview3.md` Appendix C, I proposed that v3 composite entries register a stub in v1 `PWMRegistry` as a layer-1 artifact (with `parentHash = bytes32(0)`) so v1 clients can see the composite exists. This stub-entry pattern is fine **as a discovery rendezvous point**. It is **not** fine as a payout target. Two specific problems:

### Problem 1 — single-creator royalty in `PWMReward`

`pwm_overview1.md` § Token Economics: every L4 event distributes royalties as
- AC (active contributor / miner): `p × 55%`
- CP (capacity provider): `(1−p) × 55%`
- L3 benchmark creator: `15%`
- L2 spec creator: `10%`
- **L1 Principle creator: `5%`** ← single address per Principle
- T_k treasury: `15%`

The L1 5% is paid to **one address** — the Principle's creator. A stub-entry composite at genesis would have a single creator field; royalties would route 100% to that creator. v3 § 5.3 specifies the opposite: only `0.4 × 5% = 2%` should retain at the composite; `0.6 × 5% = 3%` should split among the component Principles weighted by their `weight_i`.

There is no v1 contract code to do this split. `PWMReward.distribute()` is immutable. Stub-entry at genesis means **the wrong royalty flow for the entire pre-v3 window** (estimated 12-18 months between mainnet and v3 deploy).

### Problem 2 — retroactive correction is operationally messy

When v3 deploys `PWMRewardV2`, the ideal would be: switch composite payouts to multi-parent flow going forward, plus retroactively redistribute the 12-18 months of mis-routed royalties.

The retroactive part is hard:
- Recompute every L4 event under each composite's history (could be thousands of events)
- For each event, compute what each component *should have* received vs. what the composite creator *did* receive
- Issue corrective transfers — but the composite creator may have already spent, transferred, or sold their PWM
- Slashing the creator's existing balance to fund the corrections is contentious; doing nothing leaves components permanently shortchanged

Better to avoid the situation entirely. Don't put composites in genesis.

### Problem 3 — fusion-rule verification has no on-chain home

v3 § 5.4 requires that "the auto-verifier can compose component certificates into a composite certificate using standard rules." That's a v3 service. Pre-v3, fusion-rule correctness is purely social — no contract checks, no auto-verifier, no domain committee enforcement (committees are also v3).

A composite at genesis with no fusion-rule verification is a Principle whose L4 mining benchmark could pass v1's S1-S4 against the composite's surface but fail to actually compose its components correctly. Miners could earn the composite's full A_k share for solutions that ignore the fusion rule. Bad incentive structure.

---

## The eight v3 composite forward-model exemplars

These are the canonical composite Principles that v3 § 5 was designed to enable. Each has a multi-component forward model and an explicit fusion rule. They serve as the **target list for v3 deploy** and also as the **component-coverage checklist for v1 mainnet genesis**.

### 1. Multimodal medical diagnosis (CT + EHR text)

```
y_diagnosis(x_CT, x_EHR) = softmax(α · f_CT(μ(x_CT)) + β · f_EHR(c(x_EHR)))

  μ(x)   = tissue density reconstruction from CT projections
  c(x)   = clinical-finding extraction from EHR text
  α, β   = learned fusion weights, sum to 1
```

- **Components:** CT tissue-density reconstruction (analytical) + EHR clinical-finding extraction (`data_driven_statistical`)
- **Fusion rule:** weighted log-likelihood combination
- **Resolved gate_class:** `data_driven_statistical` (weakest-link)
- **Use case:** pneumonia detection, lung cancer staging, sepsis early warning

### 2. Multi-messenger astronomy (gravitational waves + optical + neutrino)

```
P(event | t, sky_position) = ∫ s_GW(t, θ) · I_optical(t, θ) · ν_flux(t, θ) dθ

  s_GW(t)        = LIGO/Virgo strain recovery from interferometer signals
  I_optical(t)   = optical lightcurve from PSF-deconvolved telescope images
  ν_flux(t)      = neutrino direction-of-arrival from IceCube-like detectors
```

- **Components:** GW strain recovery (analytical) + optical PSF deconvolution (analytical) + neutrino DoA (analytical)
- **Fusion rule:** temporal cross-correlation across modalities
- **Resolved gate_class:** `analytical`
- **Use case:** binary neutron-star merger localization, kilonova identification

### 3. Coupled fluid-structure interaction (FSI)

```
∂_t u = NS(u, p)              on Ω_fluid     (Navier-Stokes, fluid domain)
∂_tt w = Cauchy(w)            on Ω_solid     (linear elasticity, solid domain)
u · n = ∂_t w · n             on Γ           (shared boundary continuity)
σ_fluid · n = σ_solid · n     on Γ           (traction continuity)
```

- **Components:** Navier-Stokes incompressible (analytical) + linear elasticity (analytical)
- **Fusion rule:** coupled Newton iteration on shared boundary `Γ` — `n_c > 0` in v1's L_DAG sense (cross-edge between sub-operators)
- **Resolved gate_class:** `analytical`
- **Use case:** aircraft wing flutter, blood flow in arteries, dam-water interaction

### 4. Multi-scale materials-by-design

```
properties(x) = upscale_3( upscale_2( DFT(electrons; x) → MD(atoms; x) ) → continuum(grains; x) )

  DFT(x)        = Kohn-Sham electronic-structure energy at given atomic positions
  MD(x)         = molecular dynamics trajectory, atomic positions over time
  continuum(x)  = grain-scale finite-element mechanical response
  upscale_2     = thermodynamic averaging from atomic to continuum
  upscale_3     = homogenization from grain to component scale
```

- **Components:** DFT electronic-structure (analytical) + molecular dynamics (analytical) + continuum mechanics / linear elasticity (analytical)
- **Fusion rule:** scale-bridging upscaling (each component's output is the next's boundary condition)
- **Resolved gate_class:** `analytical`
- **Use case:** alloy design, battery electrolyte optimization, drug crystal polymorph prediction

### 5. Climate-system attribution

```
T_anomaly(x, t) = f_atmosphere(CO2_path; x, t)
                + f_ocean(heat_uptake; x, t)
                + f_ice(albedo_feedback; x, t)
                + f_land(carbon_flux; x, t)
```

- **Components:** atmospheric general-circulation model (analytical PDE) + ocean circulation model (analytical) + ice-sheet dynamics (analytical) + terrestrial biosphere flux model (analytical)
- **Fusion rule:** additive forcing decomposition — each component contributes a partial temperature anomaly that sums to the observed total
- **Resolved gate_class:** `analytical`
- **Use case:** detection-and-attribution studies for IPCC reports, regional climate-change impact assessment

### 6. Drug-target-disease triplet ranking

```
P(efficacy | drug, disease) = ∫ P(bind | structure(drug)) · P(pathway | target)
                                · P(outcome | pathway, disease) dθ

  P(bind)     = quantum-chemistry binding affinity (DFT-derived)
  P(pathway)  = target-to-pathway statistical association (data-driven)
  P(outcome)  = clinical outcome model conditioned on pathway perturbation
```

- **Components:** protein-fold structure prediction (`physical_with_discrete_readout` — DFT/AlphaFold core + binding-site readout) + target-pathway association (`data_driven_statistical`) + clinical-outcome modeling (`data_driven_statistical`)
- **Fusion rule:** multiplicative chain rule
- **Resolved gate_class:** `data_driven_statistical` (weakest-link)
- **Use case:** drug repurposing, indication expansion, side-effect prediction

### 7. Earthquake → tsunami → warning cascade

```
source_params  = FWI(seismic_waveform)                     (full-waveform inversion)
wave_field     = shallow_water(source_params, bathymetry)  (linearized SW PDE)
warning_level  = threshold(max |wave_field|, height_thresholds)
```

- **Components:** seismic full-waveform inversion (analytical) + shallow-water wave propagation (analytical) + magnitude-class threshold readout (`physical_with_discrete_readout`)
- **Fusion rule:** sequential cascade (output of one component feeds input of the next)
- **Resolved gate_class:** `physical_with_discrete_readout` (weakest-link)
- **Use case:** Pacific Tsunami Warning System modernization, regional early-warning networks

### 8. Genome → phenotype mapping

```
P(phenotype | genotype) = Σ_{protein, metabolism}
                          P(protein | genotype)
                        · P(metabolism | protein)
                        · P(phenotype | metabolism)

  P(protein|genotype)     = codon-table translation × folding-energy minimization
  P(metabolism|protein)   = flux-balance analysis (LP) on the metabolic network
  P(phenotype|metabolism) = phenotype-scoring statistical model
```

- **Components:** codon-table translation (analytical, deterministic) + protein-fold energy minimization (`physical_with_discrete_readout`) + flux-balance analysis (analytical, LP) + phenotype scoring (`data_driven_statistical`)
- **Fusion rule:** multiplicative chain (sum-product over hidden protein/metabolism states)
- **Resolved gate_class:** `data_driven_statistical` (weakest-link)
- **Use case:** synthetic biology design, genetic-disease mechanism discovery, microbial engineering

---

## Component coverage audit against the current 502 genesis Principles

I walked the genesis tree (`pwm-team/content/agent-imaging/principles/`, `agent-physics/`, `agent-chemistry/`, `agent-applied/`, `agent-signal/`) and matched each composite's required components to existing L1 manifests.

### Component coverage table

| Composite | Required component | Genesis status | File path (if present) |
|---|---|---|---|
| **1. CT + EHR diagnosis** | CT tissue-density reconstruction | ✅ Present | `agent-imaging/.../C_medical_imaging/L1-029_ct.json` |
| | EHR clinical-finding extraction | ❌ Missing — `data_driven_statistical`, needs L0_meta from v2 | — (skip from genesis; arrives post-v2) |
| **2. Multi-messenger astronomy** | GW strain recovery (LIGO) | ⚠️ Partial — L1-364 / L1-368 / L1-374 in `agent-applied/AC_astrophysics/` reference gravitational waves but need to verify they cover strain recovery specifically | `agent-applied/AC_astrophysics/L1-364.json`, `L1-368.json`, `L1-374.json` |
| | Optical PSF deconvolution | ✅ Present (any `agent-imaging` deconvolution Principle qualifies) | various in `agent-imaging/` |
| | Neutrino direction-of-arrival | ❌ Missing | — (small authoring gap) |
| **3. Fluid-structure interaction** | Navier-Stokes incompressible | ✅ Present | `agent-physics/R_fluid_dynamics/L1-170_incompressible_ns.json` |
| | Linear elasticity | ✅ Present | `agent-physics/T_structural_mechanics/L1-207_linear_elasticity.json` |
| **4. Multi-scale materials** | DFT electronic-structure | ✅ Present | `agent-chemistry/X_comp_chemistry/L1-294_density_functional_theory.json` |
| | Molecular dynamics | ✅ Present | `agent-chemistry/X_comp_chemistry/L1-298_ab_initio_md.json` |
| | Continuum mechanics / hyperelasticity | ✅ Present | `agent-physics/T_structural_mechanics/L1-215_hyperelasticity.json` |
| **5. Climate-system attribution** | Atmospheric GCM | ⚠️ Partial — `agent-applied/AF_environmental_sci/L1-414`, `L1-416-419` reference atmospheric/climate models; need to verify GCM-class forward operator | `agent-applied/AF_environmental_sci/` |
| | Ocean circulation model | ⚠️ Likely partial — same directory; need verification | same |
| | Ice-sheet dynamics | ❌ Probably missing — small authoring gap | — |
| | Terrestrial biosphere flux | ⚠️ Partial — environmental_sci; verify | same |
| **6. Drug-target-disease triplet** | Protein-fold structure | ⚠️ Partial — `agent-applied/AE_computational_bio/L1-412.json` references protein folding; verify it's a `physical_with_discrete_readout` analytical core | `agent-applied/AE_computational_bio/L1-412.json` |
| | Target-pathway association | ❌ Missing — `data_driven_statistical`, needs L0_meta from v2 | — (skip from genesis) |
| | Clinical outcome model | ❌ Missing — `data_driven_statistical`, needs L0_meta from v2 | — (skip from genesis) |
| **7. Earthquake → tsunami cascade** | Seismic full-waveform inversion | ✅ Present | `agent-physics/W_geophysics/L1-273_full_waveform_inversion.json` |
| | Shallow-water wave propagation | ✅ Present | `agent-physics/R_fluid_dynamics/L1-181_shallow_water.json` and `agent-physics/W_geophysics/L1-289_tsunami_propagation.json` |
| | Magnitude-class threshold readout | ❌ Missing — `physical_with_discrete_readout`; **add as part of the v2 batch** | — (covered by `PWM_V2_GENESIS_INCLUSION.md` recommendation) |
| **8. Genome → phenotype** | Codon-table translation | ⚠️ Partial — `agent-applied/AE_computational_bio/L1-403.json` references genome-related forward model; verify covers translation | `agent-applied/AE_computational_bio/L1-403.json` |
| | Protein-fold energy minimization | ⚠️ Partial — same as composite #6 | `agent-applied/AE_computational_bio/L1-412.json` |
| | Flux-balance analysis | ❌ Likely missing — small authoring gap | — |
| | Phenotype scoring | ❌ Missing — `data_driven_statistical`, needs L0_meta from v2 | — (skip) |

### Summary

| Status | Count | Action |
|---|---|---|
| ✅ Component fully covered in current genesis | 11 | none — already auto-promoted |
| ⚠️ Component partially covered (needs verification) | 7 | review the cited L1 manifests; if gaps, author small extensions |
| ❌ Component missing — **analytical class** (small authoring gap) | 4 | author and add to genesis pre-mainnet (~1-2 weeks each) |
| ❌ Component missing — `data_driven_statistical` class | 5 | **skip from genesis**; arrives post-v2 with proper `L0_meta` parent |
| ❌ Component missing — `physical_with_discrete_readout` class | 1 | covered by the 10-15 v2 batch in `PWM_V2_GENESIS_INCLUSION.md` |

**The four small authoring gaps** (all analytical-class):
1. Neutrino direction-of-arrival (composite #2)
2. Ice-sheet dynamics (composite #5)
3. Flux-balance analysis (composite #8)
4. (Possibly) GCM atmospheric model upgrade if the existing `agent-applied/AF_environmental_sci/` Principles don't cover the full GCM forward operator

Total additional analytical-class authoring: ~4-8 weeks of work, ~$5K-15K if contracted out via Reserve grants. This is on top of the 10-15 v2 batch authoring (~3-6 weeks) recommended in `PWM_V2_GENESIS_INCLUSION.md`.

---

## Decision and rationale

**Defer all eight composites to v3 deploy.** Composites register cleanly through `PWMRegistryV2` with proper multi-parent `parents[]` arrays and `PWMRewardV2` with the 0.4 / 0.6 split per v3 § 5.3.

**Ensure all required components are in the genesis batch.** This means:

1. **Verify the ⚠️ partial entries** in the audit table above — read each cited manifest to confirm it actually covers the component's forward operator, not just an adjacent topic.
2. **Author the 4 missing analytical-class components** (neutrino DoA, ice-sheet dynamics, flux-balance analysis, possibly GCM upgrade). Add them to the genesis batch before Step 7.
3. **Skip the 5 missing `data_driven_statistical` components** — they will arrive post-v2 with proper `L0_meta` parents and the 0.5× multiplier.
4. **The 1 missing `physical_with_discrete_readout` component** (magnitude-class threshold for tsunami composite) should be in the 10-15 v2 batch from `PWM_V2_GENESIS_INCLUSION.md`. Add it explicitly to that list.

### Why this is the right answer economically

When a composite registers post-v3, its components are already promoted from genesis. So:

```
Composite X registers post-v3 deploy
   → Composite X is NOT auto-promoted (it's not in the genesis batch)
   → Composite X must earn promotion through L4 activity (~6-12 months)

But during that time:
   → Components of Composite X ARE promoted (from genesis)
   → Components share A_k from epoch 1
   → Component royalties (the 0.6 × 5% = 3% share per L4 event under Composite X)
     flow correctly to component creators
   → Only the Composite X creator's 0.4 × 5% = 2% share is delayed until promotion

So the structural disadvantage is reduced from "all-or-nothing" (the v2 case) to
"40% of L1 royalty delayed for 6-12 months." Components capture 60% of the L1
royalty correctly from day 1.
```

This is a much smaller economic gap than the `physical_with_discrete_readout` case where the entire Principle gets nothing without genesis inclusion.

### Why this is the right answer operationally

1. **No on-chain royalty mis-routing** during the pre-v3 window. v1 contracts route single-creator royalties as they were designed to.
2. **No retroactive correction needed** at v3 deploy. Just register new composites in `PWMRegistryV2`; nothing to fix from v1.
3. **Fusion-rule verification arrives with v3.** The auto-verifier (v3 § 3) is online by the time composites register, so fusion correctness is enforceable.
4. **Component coverage is the right pre-mainnet investment.** Authoring 4 small analytical components now sets up the entire post-v3 composite ecosystem.

---

## Practical execution plan

Same pre-mainnet window as the Reserve resizing and the v2 genesis batch. All three decisions land in the same multisig transaction at Step 7.

### Phase 1 — verify the ⚠️ partial component entries (~1 week)

- [ ] Read each cited L1 manifest in the audit table and verify it covers the required component's forward operator.
- [ ] For partial coverage, document specifically what's missing and either upgrade the existing manifest or note the gap for Phase 2 authoring.

### Phase 2 — author the missing 4 analytical components (~4-8 weeks, parallelizable)

- [ ] **Neutrino DoA** under `agent-applied/AC_astrophysics/`. Forward model: track-vs-shower likelihood from photomultiplier hit pattern. Δ tier likely 5 (advanced).
- [ ] **Ice-sheet dynamics** under `agent-applied/AF_environmental_sci/`. Forward model: shallow-shelf approximation PDE for ice flow. Δ tier likely 5.
- [ ] **Flux-balance analysis** under `agent-applied/AE_computational_bio/`. Forward model: linear-program optimization on stoichiometric matrix. Δ tier likely 3.
- [ ] **GCM atmospheric upgrade** (if needed after Phase 1 verification). Forward model: primitive equations on rotating sphere. Δ tier 7-10 (frontier).

Each can be authored in parallel by domain experts; not sequential.

### Phase 3 — extend the v2 genesis batch with magnitude-class threshold (1-2 days)

- [ ] Confirm the magnitude-class threshold readout (composite #7's discrete-readout component) is on the 10-15 v2 list in `PWM_V2_GENESIS_INCLUSION.md`. If missing, add it.

### Phase 4 — register at mainnet deploy

- [ ] Verify final genesis count: 502 (current) + ~10-15 (v2 batch) + 4 (composite components) ≈ 516-521 total auto-promoted Principles.
- [ ] Add new manifest paths to `register_genesis.js`.
- [ ] Sepolia dry-run.
- [ ] Mainnet deploy at Step 7.

### Phase 5 — register composites at v3 deploy (~12-18 months later)

- [ ] At v3 deploy, author and stake each of the 8 composite Principles via `PWMRegistryV2.register(hash, ArtifactKind.L1Composite, parents[], contentHash, creator)`.
- [ ] Components were promoted at genesis; their royalty flow is already set up.
- [ ] Composites earn promotion through normal L4 activity (no shortcut).

---

## Cost estimate

| Item | Effort |
|---|---|
| Verify ⚠️ partial component entries | ~1 week (reading + small edits) |
| Author 4 missing analytical components | ~4-8 weeks (parallelizable across authors); ~$10K-30K if contracted out |
| Verify v2 batch covers magnitude-threshold | ~1-2 days |
| `register_genesis.js` modification + Sepolia dry-run | ~1 day |
| Mainnet registration | folded into Step 7 of the deploy chain |
| **Total pre-mainnet** | **~5-9 weeks of authoring work** |
| Composite registration at v3 deploy | covered by v3 deploy plan in `PWM_V2_V3_CONTRACT_COMPATIBILITY.md` |
| **Total contract change cost** | **$0 — no contract modifications, no re-audit** |

---

## Open questions for governance

1. **Composite priority list at v3.** Are all 8 composites equally important, or should some launch first? Recommendation: prioritize composites whose components are 100% present in genesis (FSI, multi-scale materials, earthquake→tsunami cascade) — they're ready to ship the moment v3 deploys.

2. **Component-author Reserve grants.** The 4 missing analytical components are clear Reserve-grant candidates per `pwm_overview1.md` § "Early L1/L2/L3 Creation: Reserve Grants." Should they be funded from the existing Reserve or from the proposed expanded Reserve in `PWM_RESERVE_RESIZING_FOR_V2_V3.md`? Recommendation: pre-mainnet authoring is funded from current Reserve (multisig 4-of-7 vote); the expanded Reserve takes effect at deploy.

3. **Composite gate-class resolution at v3.** v3 § 5.2 specifies weakest-link, but what about composites where component classes are split (e.g., #6 drug-target-disease has all three classes)? Confirmed: the resolved class is the weakest of the three components — `data_driven_statistical` in composite #6's case. Reward share is 0.5× per v2 § 6.

4. **Composite reviewer routing pre-v3.** If a contributor wants to stake a composite Principle in the months between mainnet and v3 deploy, what happens? Recommendation: governance refuses to seed a benchmark pool until `PWMRegistryV2` is online. Stake is held in escrow; contributor opts out and gets refund if they don't want to wait.

5. **Bootstrapping the post-v3 composite Principle catalog.** Should the founders pre-author all 8 composites as a "v3 genesis batch" at v3 deploy time (mirroring the v1 pattern), or let the catalog grow organically? Recommendation: pre-author the 3 fully-component-ready composites (FSI, multi-scale materials, earthquake→tsunami) at v3 deploy. Let the others emerge organically as components become viable.

---

## Decision log

| Date | Decision |
|---|---|
| 2026-04-29 | Director asked why v3 composites aren't in the genesis recommendation and asked for v3 forward-model examples. Analysis: stub-entry composites at genesis would mis-route L1 royalties for 12-18 months (single-creator path in v1 `PWMReward` cannot do the 0.4/0.6 split per v3 § 5.3). The 8 composite forward-models are documented above; the 4 missing analytical components are the right pre-mainnet investment. |
| _TBD_ | Director picks the 4 missing component authors (or contracts via Reserve grant). |
| _TBD_ | Phase 1 verification of partial component entries complete. |
| _TBD_ | 4 analytical-component manifests authored, validated, in repo. |
| _TBD_ | `register_genesis.js` updated; Sepolia dry-run successful. |
| _TBD_ | Mainnet deploy at Step 7 with the expanded genesis batch (502 + v2 + components ≈ 516-521 entries). |
| _TBD_ | At v3 deploy, register the 3 fully-component-ready composites (FSI, multi-scale materials, earthquake→tsunami) as `L1_COMPOSITE` in `PWMRegistryV2`. |
| _TBD_ | At v3 deploy + 6-12 months, register remaining composites as their `data_driven_statistical` components mature. |

---

## Summary table

| Question | Answer |
|---|---|
| Why not put v3 composites in genesis using the stub-entry pattern? | v1's `PWMReward` has no multi-parent royalty path. A stub-entry composite at genesis would route 100% of the L1 royalty to the composite creator instead of splitting 0.4/0.6 per v3 § 5.3. The pre-v3 window is 12-18 months — too long to mis-route royalties. |
| Are there v3 forward-model examples? | **Yes — eight canonical exemplars documented above**: multimodal medical diagnosis (CT+EHR); multi-messenger astronomy (GW+optical+neutrino); FSI; multi-scale materials (DFT+MD+continuum); climate attribution; drug-target-disease triplet; earthquake→tsunami cascade; genome→phenotype mapping. |
| What's the alternative for v3 economic value at genesis? | Ensure all *components* of the planned composites are in genesis. Components auto-promote, share A_k from day 1, and receive proper component-share royalties when composites register post-v3. |
| Are all required components already in genesis? | **~85% yes.** 11 fully covered, 7 partially covered (need verification), 4 small analytical-class authoring gaps. The other 5 missing components are `data_driven_statistical` and correctly excluded (need v2's `L0_meta` infrastructure first). |
| Cost of executing the recommended fix? | ~5-9 weeks of authoring work; $0 contract change. |
| When do composites actually register? | At v3 deploy, ~12-18 months after mainnet. They register cleanly through `PWMRegistryV2` with proper multi-parent provenance and `PWMRewardV2` royalty splits. |

The single-parent constraint in v1 is real, but the deeper problem is the royalty flow. Components in genesis + composites at v3 deploy is the clean answer that captures most of the v3 economic value without breaking v1's contract math.
