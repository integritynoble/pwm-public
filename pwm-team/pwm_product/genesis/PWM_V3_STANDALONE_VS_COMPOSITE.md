# v3 Principles: standalone is the default, composite is the opt-in

**Date:** 2026-04-29
**Owner:** Director
**Audience:** PWM contract authors, Principle authors, governance reviewers, deploy planners
**Status:** design proposal — refines the v3 § 5 composite framework
**Cross-references:**
- `papers/Proof-of-Solution/pwm_overview1.md` § 3 (L_DAG complexity score, primitive decomposition, S1-S4)
- `papers/Proof-of-Solution/pwm_overview3.md` § 5 (composite Principles — to be clarified per this doc)
- `pwm-team/pwm_product/genesis/PWM_GATE_CLASSES_AND_SCALING.md` (gate-class distribution projection)
- `pwm-team/pwm_product/genesis/PWM_V2_GENESIS_INCLUSION.md` (v2 PWDR genesis batch)
- `pwm-team/pwm_product/genesis/PWM_V3_COMPOSITES_AND_GENESIS_COMPONENTS.md` (the prior decision doc this refines)

---

## TL;DR

**A v3 Principle's "v3-ness" does not require composition.** It can come from being registered in v3's hierarchical SUB_DOMAIN structure, being verified by the v3 auto-verifier, being reviewed by a v3 per-domain committee, or having a monolithic multi-physics forward model with its own joint S1-S4 certificates. **Composition (`L1_COMPOSITE` with multi-parent royalty split) is one flavor of v3 Principle, not the definition of v3.**

The corollary: a **standalone multi-physics Principle** — one with a joint coupled forward operator and no parent-component decomposition — is **already supported by v1's analytical class** (v1 § 3 explicitly allows `n_c > 0` coupling constraints in the L_DAG complexity score). It needs no schema change, registers cleanly through v1 `PWMRegistry` and `PWMReward`, and **can go in the auto-promoted genesis batch with no royalty mis-routing**.

This refines the recommendation in `PWM_V3_COMPOSITES_AND_GENESIS_COMPONENTS.md`. Of the eight v3 forward-model exemplars there, **five can be authored as standalone analytical / PWDR Principles and added to the genesis batch directly**. The remaining three genuinely need the v3 `L1_COMPOSITE` framework because they have `data_driven_statistical` components that cannot be folded into a monolithic analytical operator.

---

## The insight

Composition (multi-parent fusion with explicit upstream credit and royalty split) is fundamentally a **statement about HOW you want to credit and pay** for a Principle's physics, not a statement about WHAT the Principle's physics IS.

A Principle's physics is fully captured by:
- `E` — the forward operator
- `G` — the primitive DAG (which can have `n_c > 0` coupling constraints)
- `W` — the well-posedness certificate
- `C` — the convergence and error-bound certificate

Nothing in this quadruple requires multi-parent provenance. A Principle can have a joint coupled forward model, prove well-posedness for the joint system, and prove convergence for a joint solver class — all standalone. v1 § 3 was designed for exactly this case. The L_DAG formula `L_DAG = (|V| - 1) + log₁₀(κ/κ₀) + n_c` includes `n_c` precisely to score Principles where sub-operators are coupled. A Principle with high `n_c` is a multi-physics Principle whether you call it "v1" or "v3."

The v3 `L1_COMPOSITE` artifact is layered on top of this for a different purpose: when contributor A wants to author a fused Principle that **explicitly credits and pays** the authors of pre-existing component Principles, the multi-parent structure makes that credit machine-readable and the 0.4/0.6 royalty split makes it economically real. That's valuable — but it's an **opt-in**, not the only path to multi-physics in PWM.

---

## When to choose composite vs standalone

| Choose **standalone** when | Choose **composite** (`L1_COMPOSITE`) when |
|---|---|
| The joint forward model has a coherent mathematical statement (joint W, joint C) | The Principle is a clean linear / multiplicative / chain combination of pre-existing components |
| The monolithic solver outperforms the iterated component-by-component solver | The component Principles are well-established and you want to credit their authors |
| The component Principles don't yet exist as separate Principles in PWM | The fusion rule is the central novelty, not the components |
| The coupling between sub-operators is intrinsic (e.g., a non-separable cross-term) | The components are loosely coupled and could plausibly be solved independently and then fused |
| You don't want to pay the 0.4/0.6 royalty split | You explicitly want upstream royalty flow to the component creators |
| You want the Principle to be genesis-eligible NOW | You want the multi-parent provenance to be auditable on-chain |

Most multi-physics problems sit in the standalone column. Composite is the right framing only when the contributor is consciously fusing well-established components with a novel fusion rule.

---

## The eight v3 exemplars reframed

Each of the eight composite exemplars from `PWM_V3_COMPOSITES_AND_GENESIS_COMPONENTS.md` is reconsidered here. For each one, the question is: can it be authored as a standalone v1-analytical (or v2-PWDR) Principle with a coherent joint forward model? If yes, it goes in genesis. If no, it stays composite (defers to v3 deploy).

### 1. Multimodal medical diagnosis (CT + EHR text)

**Standalone-feasible? No.** The EHR-text component is `data_driven_statistical` (NLP has no closed-form forward operator from English to clinical findings). A standalone framing would require folding the NLP operator into a monolithic forward model, which is mathematically dishonest — the diagnosis function inherits the EHR component's statistical certificate, not analytical.

**Verdict:** stays composite. Defers to v3 deploy.

### 2. Multi-messenger astronomy (GW + optical + neutrino)

**Standalone-feasible? Yes.** All three components are analytical. The joint forward model is:
```
P(event | t, sky_position) = ∫ s_GW(t, θ) · I_optical(t, θ) · ν_flux(t, θ) dθ
```
This product of three measurement processes is itself an analytical operator with closed-form structure. Joint well-posedness can be proved for the multi-messenger event-localization problem (the cross-correlation structure makes the joint operator better-conditioned than any single-messenger version). Joint convergence: standard cross-correlation bounds. L_DAG ≈ 6-8 with `n_c = 2` (two coupling cross-terms across modalities).

**Verdict:** can be authored as a standalone v1-analytical Principle. **Genesis-eligible.**

### 3. Coupled fluid-structure interaction (FSI)

**Standalone-feasible? Yes.** This is the textbook example. The joint forward model:
```
∂_t u = NS(u, p)              on Ω_fluid
∂_tt w = Cauchy(w)            on Ω_solid
u · n = ∂_t w · n             on Γ
σ_fluid · n = σ_solid · n     on Γ
```
is a standard PDE system with well-developed analytical theory (existence, uniqueness, regularity). Joint W and C certificates exist (e.g., Coutand-Shkoller existence proofs; Bazilevs et al. ALE-FEM convergence). Monolithic FEM solvers (immersed-boundary, ALE, fictitious-domain) routinely outperform iterated NS+elasticity solvers. L_DAG ≈ 6-8 with `n_c = 2` (two boundary-coupling constraints).

**Verdict:** can be authored as a standalone v1-analytical Principle. **Genesis-eligible.** Components NS (`L1-170_incompressible_ns.json`) and elasticity (`L1-207_linear_elasticity.json`) remain in genesis as their own analytical Principles, but the standalone FSI Principle does not reference them as parents.

### 4. Multi-scale materials simulation (DFT + MD + continuum)

**Standalone-feasible? Yes.** The joint forward model is the multi-scale simulation operator with built-in scale bridging:
```
properties(x) = upscale_3 ∘ upscale_2 ∘ DFT_solve(electrons; x) → MD_evolve(atoms) → continuum_solve(grains)
```
Coupling constants between scales (Hellmann-Feynman forces, time-temperature superposition, homogenization tensors) are part of the joint operator. L_DAG ≈ 9-11 with `n_c = 4` (two scale-bridging coupling constraints, each appearing in forward and adjoint directions).

**Verdict:** can be authored as a standalone v1-analytical Principle. **Genesis-eligible.** Components DFT (`L1-294`), MD (`L1-298`), and elasticity remain as their own analytical Principles, but the standalone multi-scale Principle does not reference them as parents.

### 5. Climate-system attribution

**Standalone-feasible? Yes.** Earth-system models (CESM, GFDL, HadGEM) are routinely written as monolithic primitive-equation solvers on coupled atmosphere-ocean-ice-land. Joint forward model:
```
∂_t (atmosphere, ocean, ice, land) = F_coupled((atmosphere, ocean, ice, land); CO2_path, solar_forcing, ...)
```
W: Lions-Temam style compactness arguments for the coupled climate system. C: standard finite-difference/finite-volume convergence on the coupled grid. L_DAG ≈ 10-12 with `n_c = 6` (atmosphere-ocean energy + moisture + momentum couplings; ice-albedo feedback; land-carbon feedback).

**Verdict:** can be authored as a standalone v1-analytical Principle. **Genesis-eligible.**

### 6. Drug-target-disease triplet ranking

**Standalone-feasible? No.** The pathway-association and clinical-outcome components are `data_driven_statistical` (both rely on empirical biological databases without closed-form operators). A standalone framing would force statistical certificates to masquerade as analytical, which violates the gate-class distinction.

**Verdict:** stays composite. Defers to v3 deploy.

### 7. Earthquake → tsunami warning cascade

**Standalone-feasible? Yes.** The cascade is a sequential analytical pipeline ending in a deterministic threshold. Joint forward model:
```
warning_level(seismic_waveform) = threshold_function( shallow_water_solve( FWI_invert(seismic_waveform), bathymetry ) )
```
Joint W: existence/uniqueness of the entire cascade follows from chaining the three component cascades' W-certificates (FWI is well-posed, shallow-water IVP is well-posed, threshold is Lipschitz). Joint C: error propagates through the cascade with a known Lipschitz bound. The threshold readout makes this a `physical_with_discrete_readout` Principle, not pure analytical.

**Verdict:** can be authored as a standalone **v2 PWDR** Principle (gate_class: `physical_with_discrete_readout`). **Genesis-eligible** as part of the v2 batch in `PWM_V2_GENESIS_INCLUSION.md`.

### 8. Genome → phenotype mapping

**Standalone-feasible? Partial.** The codon-translation + flux-balance + protein-fold portions are all analytical (or PWDR). The phenotype-scoring component is `data_driven_statistical`. So a "genome → metabolism" standalone is feasible (analytical chain ending at flux state), but the full "genome → phenotype" requires the statistical scoring step.

**Verdict:** can be split. Author the **analytical sub-chain** (genome → protein → metabolism) as a standalone v1-analytical Principle, **genesis-eligible**. The full phenotype mapping stays composite, defers to v3.

---

## Updated tally

| Composite exemplar | Standalone-eligible? | Genesis-eligible (after authoring)? |
|---|---|---|
| 1. CT + EHR diagnosis | No (DDS component) | No (composite, defers to v3) |
| 2. Multi-messenger astronomy | **Yes** (analytical) | **Yes** |
| 3. Fluid-structure interaction | **Yes** (analytical) | **Yes** |
| 4. Multi-scale materials | **Yes** (analytical) | **Yes** |
| 5. Climate-system attribution | **Yes** (analytical) | **Yes** |
| 6. Drug-target-disease | No (DDS components) | No (composite, defers to v3) |
| 7. Earthquake-tsunami cascade | **Yes** (PWDR) | **Yes** (already in v2 batch) |
| 8. Genome-phenotype | Partial (analytical sub-chain) | **Yes** (sub-chain only; full version defers) |

**5 fully standalone + 1 partial-standalone + 2 genuine composites.** Six of the eight exemplars can have at least a standalone form in the genesis batch.

---

## Genesis composition revision

Updating the recommendation from `PWM_V2_GENESIS_INCLUSION.md` and `PWM_V3_COMPOSITES_AND_GENESIS_COMPONENTS.md`:

| Bucket | Count | Source / status |
|---|---|---|
| Existing analytical | 502 | already present in genesis tree |
| v2 PWDR exemplars | 10-15 | `PWM_V2_GENESIS_INCLUSION.md` |
| Missing analytical components | 4 | `PWM_V3_COMPOSITES_AND_GENESIS_COMPONENTS.md` (neutrino DoA, ice-sheet, FBA, GCM upgrade) |
| **Standalone multi-physics analytical** | **5** | **THIS DOC** — multi-messenger, FSI, multi-scale materials, climate attribution, earthquake-tsunami (this last counts under the v2 PWDR bucket) |
| Standalone analytical sub-chain | 1 | THIS DOC — genome-protein-metabolism |
| **Total genesis batch** | **~522-528** | — |

The five new standalone multi-physics entries (or 4 fully-new + 1 already-counted under v2 PWDR) represent ~4-8 weeks of additional authoring. They cover the most economically interesting multi-physics territory and lock in the protocol's "physics-grounded multi-domain" identity from genesis.

The two genuine composites (CT+EHR diagnosis, drug-target-disease) defer to v3 deploy — same as before. The genome-phenotype composite stays partly deferred (full phenotype mapping is post-v3) but the analytical sub-chain is genesis-eligible.

---

## Spec clarifications needed (small)

The current specs already permit this — they just don't make it explicit enough. Recommended clarifications:

### `pwm_overview3.md` § 5 — "Cross-domain Principle composition"

Add a leading subsection: **"§ 5.0 — Composite is opt-in; standalone is the default."**

> A multi-physics Principle does not need to be authored as a composite. v1's L_DAG complexity score (`pwm_overview1.md` § 3) explicitly accepts coupling constraints (`n_c > 0`), and v1's S1-S4 gates apply to joint coupled forward operators just as they apply to single-physics operators. A standalone v1-analytical Principle with a joint forward model is the default form for multi-physics work in PWM.
>
> The `L1_COMPOSITE` artifact in this section is the **opt-in form** — used when the contributor wants to **explicitly credit** the authors of pre-existing component Principles via the 0.4/0.6 royalty split in § 5.3. The fusion rule is the central novelty when this form is chosen.
>
> If the contributor's Principle is genuinely a fusion of well-established components (e.g., NS + elasticity → FSI where both NS and elasticity are already PWM Principles authored by other people), the composite form is appropriate. If the joint forward model has its own coherent W and C certificates and the contributor wants to claim full L1 royalty without the split, the standalone form is appropriate. **The protocol leaves the choice to the contributor.**

### `pwm_overview3.md` § 2 — Hierarchical Principle registry

Add at the end of § 2.1:

> The hierarchical registry (DOMAIN / SUB_DOMAIN) applies to **all** Principles, not just composites. Standalone v1-analytical and v2-PWDR Principles authored after v3 deploy are also classified by `domain` and `sub_domain` (see § 7.1 manifest schema). The hierarchy is a navigation and reviewer-routing aid, not a composite-only feature.

### `pwm_overview2.md` § 2 — Gate-class field

No change needed. The `gate_class` enum already covers standalone forms:

- `analytical` — covers standalone single-physics AND standalone multi-physics (any L_DAG)
- `physical_with_discrete_readout` — covers standalone analytical-core + threshold-readout Principles
- `data_driven_statistical` — covers standalone Principles that need statistical certificates

A composite Principle's resolved gate_class (per v3 § 5.2 weakest-link) is computed at composite-registration time and is a separate concept.

### `PWM_GATE_CLASSES_AND_SCALING.md` — distribution projection

Currently projects ~30/50/20 (analytical / PWDR / DDS) at 10K Principles. With standalone multi-physics admitted under analytical, the analytical share grows. Revised projection:

| Class | Current projection | Revised projection (under this doc) |
|---|---|---|
| `analytical` | ~30% | **~40%** (absorbs standalone multi-physics that would otherwise be composites) |
| `physical_with_discrete_readout` | ~50% | ~45% (slight decrease — some PWDR-eligible problems become standalone PWDR rather than physical-readout composites) |
| `data_driven_statistical` | ~20% | ~15% (slight decrease — pure-DDS share is more bounded once standalone multi-physics absorbs the soft cases) |
| Composites (separate axis, fraction of all Principles that are L1_COMPOSITE) | implicit | ~5-10% (composites are the explicit-credit minority, not the default form) |

PWM stays "physics / math-grounded" for ~85% of the catalog, slightly higher than the prior projection because standalone multi-physics is admitted under analytical.

---

## Why this is a better design overall

Three reasons beyond the genesis-inclusion benefit:

1. **Authoring is faster.** A contributor with a novel coupled multi-physics Principle doesn't need to wait for component Principles to exist or coordinate with component authors. They write one manifest, prove joint S1-S4, stake. Done.

2. **Royalty math is unambiguous.** Standalone = full 5% L1 royalty, single creator. Composite = 0.4/0.6 split, machine-readable parents. No fuzzy in-between.

3. **The "shoulders of giants" narrative still works.** The d_principle distance metric (Jaccard on physics fingerprint) flags when a standalone Principle's physics overlaps existing Principles. Reviewers can suggest composite framing during review. But the protocol doesn't force it — the contributor decides whether the upstream credit is worth the royalty split.

The current v3 § 5 design effectively forced contributors into composites by making them the only multi-physics path. That over-constrained the design space. Standalone-as-default returns the natural choice to contributors.

---

## Practical execution plan

Same pre-mainnet window as the prior decisions. All three (Reserve resizing, v2 PWDR genesis batch, standalone multi-physics) land at Step 7.

### Phase 1 — author the 5 new standalone multi-physics Principles (~6-10 weeks, parallelizable)

Recommended assignments:

- [ ] **Multi-messenger astronomy** (analytical, L_DAG ~6-8) — astrophysicist with multi-detector experience. Reserve grant via DAO vote. ~2-3 weeks.
- [ ] **Fluid-structure interaction** (analytical, L_DAG ~6-8) — applied math / FEM expert. Could be authored by someone already working on `agent-physics/R_fluid_dynamics` or `T_structural_mechanics`. ~2-3 weeks.
- [ ] **Multi-scale materials simulation** (analytical, L_DAG ~9-11) — materials scientist with QM-MD-continuum experience. ~3-4 weeks (more complex L_DAG).
- [ ] **Climate-system attribution** (analytical, L_DAG ~10-12) — climate scientist with ESM expertise. Likely Reserve grant. ~3-4 weeks.
- [ ] **Genome-protein-metabolism analytical sub-chain** (analytical, L_DAG ~7-9) — computational biologist. ~2-3 weeks.

Total authoring time: 6-10 weeks calendar (parallelizable across 3-5 authors). Cost: ~$15K-40K via Reserve grants.

### Phase 2 — registration

- [ ] Add new manifest paths to `register_genesis.js`'s registration list.
- [ ] Verify final genesis count: 502 + ~10-15 (v2 PWDR) + 4 (analytical components) + 5 (standalone multi-physics) ≈ 521-526 entries.
- [ ] Sepolia dry-run.
- [ ] Mainnet deploy at Step 7.

### Phase 3 — spec clarifications (parallel to authoring)

- [ ] Edit `pwm_overview3.md` § 5 to add the "§ 5.0 standalone is default" subsection.
- [ ] Edit `pwm_overview3.md` § 2.1 to clarify hierarchical registry applies to all Principles.
- [ ] Edit `PWM_GATE_CLASSES_AND_SCALING.md` § distribution projection to revised numbers.
- [ ] Add cross-link to this doc in `PWM_V3_COMPOSITES_AND_GENESIS_COMPONENTS.md`.

### Phase 4 — composites at v3 deploy (~12-18 months later, unchanged)

- [ ] Author the 2 genuine composites (CT+EHR diagnosis, drug-target-disease) and stake via `PWMRegistryV2`.
- [ ] Author the full genome-phenotype composite as the statistical components mature.

---

## Cost estimate

| Item | Effort |
|---|---|
| Author 5 standalone multi-physics Principles | ~6-10 weeks (parallelizable); ~$15K-40K Reserve grants |
| Spec clarifications (3 files) | ~1 week |
| `register_genesis.js` modification + Sepolia dry-run | ~1 day |
| Mainnet registration | folded into Step 7 |
| **Total pre-mainnet** | **~7-12 weeks of authoring + 1 week of spec edits** |
| Composites at v3 deploy | covered by v3 deploy plan |
| **Total contract change cost** | **$0 — no contract modifications, no re-audit** |

This is on top of (not instead of) the v2 PWDR batch authoring (~3-6 weeks) and the analytical component authoring (~4-8 weeks) from prior docs.

Total pre-mainnet authoring across all three batches: ~13-26 weeks parallelized across 5-8 authors. Director's UTSW PI relationship (Dr. Zaman) and prior conversations identify candidate authors in medical AI, materials, geophysics, and computational biology — no severe staffing gap.

---

## Open questions

1. **Should standalone Principles cite related Principles even without the composite royalty split?** Recommendation: yes — manifest field `related_principles: [L1-XXX, L1-YYY, ...]` is informational only (no royalty implication), helps reviewers and downstream solvers understand provenance.

2. **What if a standalone Principle's L_DAG is so high that a single contributor can't author it credibly?** Recommendation: multi-author standalone Principles are allowed — the manifest's `creator` field can be a multisig wallet that splits the L1 royalty among co-authors off-chain.

3. **Should v3's `L1_COMPOSITE` artifact even be needed if standalone is the default?** Recommendation: yes, for the explicit-credit case. There are real situations where contributor A wants to fuse contributor B's well-established Principle and contributor B should get on-chain royalty flow. Composite is the right mechanism for that. It's just no longer the only path.

4. **Could a standalone multi-physics Principle later be reformulated as a composite?** Recommendation: no — Principles are immutable per v1 § 2. A new composite must be a new artifact with a new hash; the old standalone remains accessible. d_principle distance might flag the new composite as "Identical / Very similar" to the standalone, in which case the staking advisory shows the warning per v1 § 3.

5. **Royalty arbitrage.** A contributor could author a standalone multi-physics Principle (full 5% royalty) instead of a composite (0.4 × 5% = 2% retained at composite). Is this a problem? Recommendation: no — this is exactly the design intent. The contributor takes on the burden of proving joint S1-S4 from scratch in exchange for the full royalty. It's a fair trade, and contributors who want to credit upstream authors can still choose composite voluntarily.

---

## Decision log

| Date | Decision |
|---|---|
| 2026-04-29 | Director observed that v3 Principles can be standalone (not require multi-parent composition). Analysis confirmed: v1's analytical class already supports joint coupled forward models via `n_c > 0` in L_DAG. Standalone multi-physics is genesis-eligible without any spec modification. The v3 `L1_COMPOSITE` artifact remains the opt-in form for explicit upstream credit. Recommended adding 5 standalone multi-physics Principles to the genesis batch and clarifying v3 § 5 to make composite-as-opt-in explicit. |
| _TBD_ | Director picks 5 author candidates (some via direct authoring, others via Reserve grant). |
| _TBD_ | Phase 1 standalone multi-physics manifests authored, validated, in repo. |
| _TBD_ | Phase 3 spec clarifications committed. |
| _TBD_ | Mainnet deploy at Step 7 with the expanded genesis batch. |
| _TBD_ | At v3 deploy, the 2 genuine composites (CT+EHR, drug-target-disease) register via `PWMRegistryV2`. |

---

## Summary table

| Question | Answer |
|---|---|
| Does v3 require composition (multi-parent)? | **No.** v3's other features (hierarchical registry, auto-verifier, per-domain committees) apply to standalone Principles too. Composition is one optional flavor of v3. |
| Can a standalone multi-physics Principle exist under the current v1 spec? | **Yes** — v1's L_DAG explicitly supports coupling constraints (`n_c > 0`), and v1's S1-S4 apply to joint coupled forward operators. No schema change needed. |
| How many of the 8 v3 composite exemplars can become standalone? | **6 of 8** (5 fully standalone + 1 partial-standalone sub-chain). Only CT+EHR and drug-target-disease genuinely need composite framework because of `data_driven_statistical` components. |
| Does this enable v3-style Principles in the auto-promoted genesis batch? | **Yes.** Standalone analytical / PWDR Principles register cleanly through v1 contracts, share A_k from epoch 1, with full single-creator royalty (no split). |
| What changes in v2 / v3 specs? | **Small clarifications only.** v3 § 5 gets a leading subsection saying "composite is opt-in, standalone is default." v3 § 2.1 clarifies hierarchical registry applies to all Principles. No schema changes, no contract changes. |
| Cost of executing this? | **~7-12 weeks of authoring + 1 week of spec edits; $0 contract change.** |
| Combined with prior pre-mainnet decisions, total genesis count? | ~521-526 Principles (vs. 502 current), all auto-promoted. |
| Why is standalone-as-default a better design overall? | Faster authoring, unambiguous royalty math, returns the natural choice to contributors instead of forcing them into composites. The composite form remains for the genuine "fuse-and-credit" use case. |

The user's design instinct is correct. The current v3 § 5 design over-constrained the multi-physics path by making composite the only form. Standalone-as-default is more flexible, more permissive of genesis inclusion, and more honest about what a multi-physics Principle actually is — a single coherent piece of physics, not a pile of components.
