# Should v2-class Principles be added to the auto-promoted genesis batch?

**Date:** 2026-04-29
**Owner:** Director
**Audience:** PWM contract authors, deploy planners, Principle authors, governance reviewers
**Status:** decision document — recommends adding 10-15 `physical_with_discrete_readout` exemplars to genesis pre-mainnet
**Cross-references:**
- `papers/Proof-of-Solution/pwm_overview1.md:1202` — "The 500 genesis Principles are pre-written and auto-promoted"
- `papers/Proof-of-Solution/pwm_overview1.md:2128` — A_k allocation formula (promoted Principles only)
- `papers/Proof-of-Solution/pwm_overview2.md` — gate_class field, reward differentiation
- `pwm-team/pwm_product/genesis/CLASSIFICATION_SEGMENTATION_PRINCIPLES.md` — Option-3 recast pattern, 8 worked recast examples
- `pwm-team/pwm_product/genesis/PWM_GATE_CLASSES_AND_SCALING.md` — Case A/B/C boundary, projected ~30/50/20 distribution
- `pwm-team/pwm_product/genesis/PWM_RESERVE_RESIZING_FOR_V2_V3.md` — same pre-mainnet window
- `pwm-team/infrastructure/agent-contracts/scripts/register_genesis.js` — the script that batch-registers genesis Principles
- `pwm-team/infrastructure/agent-contracts/contracts/PWMMinting.sol` — A_k allocation logic

---

## TL;DR

**Yes — add 10-15 `physical_with_discrete_readout` exemplar Principles to the auto-promoted genesis batch before Base mainnet deploy.** Genesis Principles share A_k (protocol minting) from day 1 per `pwm_overview1.md:1202`. The current genesis of 502 Principles is 100% `analytical`. Without v2-class Principles in genesis, post-launch v2/v3 contributors face a **double disadvantage**: no A_k head start (must earn promotion through activity) plus the proposed 0.5× multiplier on `data_driven_statistical` payouts. Adding 10-15 v2-class exemplars to the genesis batch fixes the head-start half of that asymmetry without any contract changes.

`data_driven_statistical` Principles are **excluded** from genesis because they require an `L0_meta` artifact that has no on-chain home until v2 deploys `PWML0MetaRegistry`.

---

## The auto-promoted genesis fact

`pwm_overview1.md:1202`:

> The 500 genesis Principles are pre-written and **auto-promoted**. They are the safest starting points for new miners.

`pwm_overview1.md:2128`:

```
A_k = (M_pool − M(t)) × w_k / Σ_k(w_k)    (promoted principles only)
```

`pwm_overview1.md:2135`:

> Promotion gate: A_k and T_k are only allocated to promoted artifacts. Before promotion, Pool = B only.

So the protocol's minting flow goes only to promoted Principles. Genesis Principles are auto-promoted at registration. Post-genesis Principles must earn promotion via L4 activity, which takes time and cumulative L4 events. **The genesis batch is the only batch that gets A_k from epoch 1 with zero activity**.

---

## What's in genesis today

Counted directly from the principles directories:

| Domain | Count | All `analytical`? |
|---|---|---|
| `agent-imaging/principles/` (microscopy, medical, coherent, depth, remote sensing, computational photo / optics, multimodal fusion, scanning probe, electron microscopy, ultrafast, quantum, industrial inspection, …) | ~330 | Yes |
| `agent-physics/principles/` (fluid, heat transfer, EM, acoustics, structural mechanics, plasma, geophysics, nuclear engineering) | ~170 | Yes |
| **Total** | **502** | **All analytical** |
| `physical_with_discrete_readout` | **0** | — |
| `data_driven_statistical` | **0** | — |

Every genesis Principle uses a closed-form forward operator with a primitive DAG and analytical S1-S4 certificates. The PillCam-SPECTRA pair (`L1-PHYS-GI-001a` + `L1-PHYS-GI-001b`) referenced as the canonical `physical_with_discrete_readout` pilot in `CLASSIFICATION_SEGMENTATION_PRINCIPLES.md` has not been authored yet — it exists only as a design proposal.

---

## Why the asymmetry matters

A post-launch v2/v3 Principle author faces compounding disadvantages relative to a genesis author:

| Disadvantage | Source | Impact |
|---|---|---|
| **No A_k head start** | Genesis is auto-promoted; post-genesis must earn promotion via L4 activity | A `physical_with_discrete_readout` Principle staked in year 2 starts with zero A_k flow while genesis Principles have been compounding for ~600+ epochs |
| **0.5× multiplier on `data_driven_statistical`** | v2 § 6 reward differentiation | Half the share of the multiplier-adjusted payout |
| **Promotion gate latency** | Activity-driven; depends on miner adoption | Even a high-quality v2 Principle may take 6-12 months to reach promotion threshold |
| **No reviewer infrastructure for v2/v3 yet** | Pre-v2 deploy: no `PWMGateClassRegistry`, no auto-verifier | Reviewers must hand-verify the discrete-readout continuity proof manually |

Rough first-2-years A_k accumulation comparison (illustrative):

| Principle type | A_k share at year 0 | A_k share at year 2 | Cumulative A_k (year 2) |
|---|---|---|---|
| Genesis analytical | full share from epoch 1 | full share | 100% baseline |
| Post-launch `physical_with_discrete_readout` (year 1 stake) | 0 (unpromoted) | full share once promoted | ~30-50% of genesis baseline |
| Post-launch `data_driven_statistical` (year 1 stake) | 0 | 0.5× share once promoted | ~15-25% of genesis baseline |

**The structural moat for genesis-era analytical Principles is real and economically large.** Without intervention, PWM at 5 years looks like an imaging-physics protocol with a thin v2/v3 fringe, regardless of v2 spec quality. That contradicts the design intent in `PWM_GATE_CLASSES_AND_SCALING.md` (~30/50/20 target distribution at 10K Principles).

---

## Four options

### Option A — status quo

Genesis stays 502 analytical Principles. v2/v3 Principles arrive post-launch with no A_k head start.

- **Pro:** Cleanest deploy. No new authoring work. No risk of pre-v2 manifests with fields the v1 contracts don't read.
- **Con:** Reinforces the "imaging-physics protocol" optic. Structural disadvantage for Option-3-recast contributors. Director's stated design intent (~30/50/20 at scale) is undermined by genesis composition.

### Option B — add a small v2 batch to genesis (recommended)

Author 10-15 `physical_with_discrete_readout` exemplar Principles. Add them to the auto-promoted genesis batch.

- **Pro:** A_k allocation is automatic — `PWMMinting` weights by `w_k = δ_k × max(activity_k, 1)` and doesn't read `gate_class`. So v2-class genesis Principles share A_k correctly without any contract change. Symbolic value: genesis includes medical AI / materials / biology from day 1, signaling the protocol's breadth.
- **Con:** ~2-4 weeks of authoring work. The `gate_class` field sits unused on-chain until `PWMGateClassRegistry` deploys (v2 Phase 2). The PillCam-SPECTRA pair needs a citable physics core (the MDPI paper's Monte Carlo prior — already documented in `CLASSIFICATION_SEGMENTATION_PRINCIPLES.md`).

### Option C — add v2 batch + v3 composite seed

Option B plus 1-2 `L1_COMPOSITE` mock entries (e.g., multimodal CT + EHR pneumonia diagnosis).

- **Pro:** Even broader symbolic statement.
- **Con:** v1 `PWMRegistry.Artifact.parentHash` is `bytes32` (single parent). Multi-parent composites cannot validly register on v1 contracts — they need `PWMRegistryV2` from v3. Forcing the issue at genesis would require either ugly stub entries or a v3 deploy concurrent with v1 mainnet (massively expanding scope and audit cost). **Skip.**

### Option D — reserve a "v2/v3 genesis quota" without pre-authoring

Don't add Principles now. Reserve, say, 50 slots in the registered genesis pool to be **retroactively** auto-promoted once v2 deploys.

- **Pro:** No authoring work pre-mainnet.
- **Con:** "Retroactive auto-promotion" isn't a v1 contract feature. `PWMMinting` has no concept of "promoted later." Implementing it would require governance to mint A_k retroactively for the reserved slots, which is operationally messy and politically suspect (looks like the foundation playing favorites). Weaker than Option B.

---

## Recommendation: Option B

**Author 10-15 `physical_with_discrete_readout` exemplar Principles and add them to the auto-promoted genesis batch before Base mainnet deploy.**

Three reasons:

1. **The window is the same window.** Genesis batch is finalized when `register_genesis.js` runs — at Base mainnet deploy. Same hard deadline as the Reserve resizing decision in `PWM_RESERVE_RESIZING_FOR_V2_V3.md`.
2. **A_k allocation is automatic and contract-untouched.** `PWMMinting.A_k` formula uses `w_k = δ_k × max(activity_k, 1)`. The contract has no gate_class awareness. So v2-class genesis Principles share A_k the same way analytical genesis Principles do — no contract change, no re-audit.
3. **Director already has the 8 worked Option-3 recasts.** Documented in `CLASSIFICATION_SEGMENTATION_PRINCIPLES.md` and `PWM_GATE_CLASSES_AND_SCALING.md`. Converting the design table into JSON manifests is mechanical authoring work, not novel research.

---

## The 8 (+ a few more) candidate exemplars from prior docs

These are listed in `PWM_GATE_CLASSES_AND_SCALING.md` § "Case A — Tasks with physical / scientific ground truth" as canonical Option-3 recasts. Each one is a strong candidate for a genesis `physical_with_discrete_readout` Principle:

| # | Original task | Option-3 recast | Physics core | Discrete readout |
|---|---|---|---|---|
| 1 | Bleeding detection on capsule frames | optical-property recovery → bleeding threshold | PillCam-SPECTRA Monte Carlo prior (MDPI paper) | bleeding/polyp threshold function |
| 2 | Crystal structure classification from XRD | lattice-parameter inversion → space-group lookup | Bragg's-law forward model + Rietveld refinement | space-group lookup table (230 groups) |
| 3 | Pneumonia detection from chest X-ray | tissue-density reconstruction → severity threshold | attenuation-coefficient inversion (existing CT physics) | severity-grade threshold |
| 4 | Cell-type classification from RNA-seq | gene-expression vector recovery → cell-state manifold lookup | RNA-counting forward model | cell-type manifold lookup |
| 5 | Galaxy classification from telescope images | galaxy-morphology parameter estimation → typological threshold | PSF + atmospheric turbulence forward model | morphology-class threshold |
| 6 | Drug-target binding affinity prediction | quantum-chemistry energy estimation → binding threshold | DFT forward model | affinity threshold |
| 7 | Earthquake magnitude classification | source-parameter inversion → magnitude scale | seismic FWI forward model (existing genesis Principle) | Richter / moment-magnitude scale |
| 8 | Protein function prediction | structure-folding inversion → functional motif lookup | AlphaFold-style energy forward model | motif lookup (Pfam) |

Additional candidates worth including for breadth:

| # | Original task | Option-3 recast |
|---|---|---|
| 9 | Diabetic retinopathy grading from fundus | retinal vasculature reconstruction → grading threshold |
| 10 | Skin lesion classification from dermoscopy | optical-property recovery → malignancy threshold |
| 11 | Soil composition from hyperspectral satellite | spectral-signature recovery → soil-type threshold |
| 12 | Material defect classification from ultrasound | acoustic-property inversion → defect-class threshold |
| 13 | Tumor grading from MRS | metabolite-concentration recovery → tumor-grade threshold |

**Recommended target: 10-15 of these for the v2 genesis batch.** This is broad enough to cover medical, materials, biology, astronomy, and chemistry — defending the projected 30/50/20 distribution at scale — without bloating the genesis to the point that authoring becomes a multi-month bottleneck.

---

## Manifest structure for v2-class genesis entries

Each entry is a JSON manifest in `pwm-team/content/agent-imaging/principles/X_subdomain/L1-NNN_name.json` (or under `agent-physics/` / a new `agent-medical/` subtree depending on category).

```yaml
type: L1
id: L1-NNN
name: "PillCam-SPECTRA bleeding-region detection"
description: "..."
domain: "medical_ai"
sub_domain: "GI_endoscopy"   # populated for v3-readiness; v1 contracts ignore

# v2 fields — present in manifest, ignored by v1 contracts, read by v2 PWMGateClassRegistry
gate_class: "physical_with_discrete_readout"
gate_substitutions:
  kappa_substitute: null      # physics core retains analytical κ
  h_substitute: null
  conservation_substitute: "softmax simplex closure on label readout"
discrete_readout:
  threshold_function: "..."
  lipschitz_constant: ...
  underlying_physical_state: "tissue optical-absorption coefficient μ_a(λ)"
  physics_core_principle: L1-NNN-CORE   # the analytical core sibling Principle

# v1 fields (unchanged from analytical Principles)
E:
  forward_model: "..."
G: { vertices: [...], arcs: [...] }
W: { ... }
C: { ... }
physics_fingerprint: { ... }
spec_range: { ... }
delta: 3   # difficulty tier
```

The `physics_core_principle` field references a sibling `analytical` Principle that contains the closed-form physics. For the PillCam example: `L1-PHYS-GI-001a` is the analytical core (optical-property recovery), `L1-PHYS-GI-001b` is the `physical_with_discrete_readout` wrapper. Both are auto-promoted at genesis.

For some recast tasks, the analytical core already exists in genesis (e.g., earthquake-magnitude reuses an existing seismic FWI Principle). In those cases, only the readout wrapper Principle is new. This reduces authoring work — only ~5-8 of the 10-15 entries need a new analytical core authored from scratch.

---

## What goes wrong if v1 contracts see a `gate_class` field they don't understand

**Nothing.** v1 `PWMCertificate.submit` and `PWMRegistry.register` accept a content hash and a small set of typed fields (layer, parent, creator). They don't deserialize the manifest JSON. The `gate_class`, `discrete_readout`, `gate_substitutions`, `domain`, and `sub_domain` fields live in the off-chain JSON content; the on-chain hash is a black box from the contract's perspective.

When v2 deploys `PWMGateClassRegistry`, the genesis multisig batch-writes `gateClassOf[certHash] = PhysicalWithDiscreteReadout` for each v2-class genesis entry. Backfill is a single multisig transaction.

For the 502 analytical genesis entries, the same backfill writes `gateClassOf[certHash] = Analytical`. Symmetric treatment.

---

## Why exclude `data_driven_statistical` from genesis

Two structural reasons:

1. **Requires `L0_meta` artifact.** `data_driven_statistical` manifests reference an `L0_meta` parent (per v2 § 3). `L0_meta` artifacts have no on-chain home until v2 deploys `PWML0MetaRegistry`. Adding a `data_driven_statistical` Principle to genesis creates a manifest reference (`inherits_l0_meta: L0M-...`) that can't resolve to anything until ~2-4 weeks after mainnet — a temporary broken link.

2. **No closed-form S2/S3/S4 to verify at genesis.** Genesis Principles' analytical certificates can be audited mechanically (the v3 auto-verifier will do this, but even pre-auto-verifier the certificates are on the manifest face). `data_driven_statistical` certificates require numerical bound computation against a held-out test set. Doing that at genesis would force founders to commit to a specific dataset and a specific bound at deploy — heavy and not reversible.

The clean v2 ramp is: ship v2 Phase 2 → deploy `L0M-CLS-BAYES-001` (the canonical genesis L0_meta) → first `data_driven_statistical` Principles stake against it. They earn promotion the normal way (activity-driven). The 0.5× multiplier handles their reward share.

This is acceptable because `data_driven_statistical` is the ~20% tail in `PWM_GATE_CLASSES_AND_SCALING.md`'s projected distribution. The economically large class (`physical_with_discrete_readout`, ~50% of the projected catalog) is what gets the genesis head start.

---

## Practical execution plan

Same pre-mainnet window as the Reserve resizing — both decisions land in the same multisig transaction batch.

### Phase 1 — author the v2 genesis batch (~2-4 weeks)

- [ ] Director picks 10-15 from the candidate list (preferably covering medical, materials, biology, astronomy, chemistry).
- [ ] For each pick: identify the analytical core Principle. If it exists in current genesis, link it via `physics_core_principle`. If not, author it as a new analytical sibling.
- [ ] Author each `physical_with_discrete_readout` manifest as JSON. Reuse the structure from § "Manifest structure" above.
- [ ] Run each manifest through the existing genesis-validation pipeline (P1-P10 + S1-S4 on the analytical core; threshold-continuity proof on the readout).
- [ ] Place under `pwm-team/content/agent-imaging/principles/` or `agent-physics/principles/` or a new `agent-medical/principles/` subtree depending on subject.

### Phase 2 — register at mainnet deploy

- [ ] Add the new manifest paths to `register_genesis.js`'s registration list.
- [ ] Verify the registered count: 502 + (10 to 15) = 512 to 517 total auto-promoted Principles.
- [ ] Run `register_genesis.js` against Sepolia first as a dry-run to verify the new entries register cleanly.
- [ ] Run against Base mainnet at Step 7 of the deploy chain.

### Phase 3 — backfill at v2 deploy (~2-3 months later)

- [ ] When `PWMGateClassRegistry` deploys (v2 Phase 2), governance batch-signs `setGateClass` calls for all genesis entries:
  - 502 analytical entries → `Analytical`
  - 10-15 v2-class entries → `PhysicalWithDiscreteReadout`
- [ ] Off-chain matchers and the v2 settlement service start respecting the gate_class flag.

### Phase 4 — observe in production

- [ ] After 6-12 months of mainnet operation, measure: do the v2-class genesis Principles actually attract miners? If yes, validates the Option-3 recast as a productive pattern. If no, signals that the recast is harder than the design assumed and reviewer guidance needs sharpening.

---

## Cost estimate

| Item | Effort |
|---|---|
| Author 10-15 `physical_with_discrete_readout` JSON manifests | ~2-4 weeks (Director or contracted Principle author) |
| Author ~5-8 new analytical core sibling Principles where missing | ~1-2 weeks |
| Validation (P1-P10 + S1-S4) | ~2-3 days |
| `register_genesis.js` modification + Sepolia dry-run | ~1 day |
| Mainnet registration | folded into Step 7 of the deploy chain |
| **Total pre-mainnet** | **~3-6 weeks of authoring work** |
| v2-deploy-time gate-class backfill | 1 multisig batch transaction (~30 minutes) |
| **Total contract change cost** | **$0 — no contract modifications, no re-audit** |

Authoring work can run in parallel with the Reserve resizing decision and Step 6 / 7 prep. The deploy chain doesn't slip if authoring is started promptly.

---

## Open questions for governance

1. **How many to add?** 10 is the floor (covers medical + materials + biology + astronomy + chemistry breadth). 15 is the ceiling before authoring becomes a multi-month task. Recommend 12-13 as the practical target.

2. **Where do they go in the directory tree?** Existing options: `agent-imaging/principles/C_medical_imaging/` or `agent-physics/principles/`. New option: create `agent-medical/principles/` for the medical-AI ones specifically. Recommendation: create `agent-medical/principles/` as a new top-level genesis subtree — it cleanly separates the v2-class entries and makes the "PWM is broader than imaging" point structurally.

3. **Difficulty tier (`δ`) assignment.** v2-class Principles inherit `δ` from their analytical core in most cases. PillCam-SPECTRA's analytical core is plausibly `δ = 3` (standard). Crystal-XRD is `δ = 3`. Should v2-class wrappers get a small `δ` bump for the additional readout-continuity proof, or share their core's `δ`? Recommendation: share the core's `δ` — the readout adds work but not difficulty.

4. **Authoring labor.** Director writes them, or contract out via Reserve grant? Recommendation: Director writes 5-7 (the medical-AI ones, where Director's UTSW context is directly relevant), Reserve-grant the rest to domain experts (XRD = materials scientist; galaxy classification = astronomer).

5. **Should the v2-class genesis entries' Reserve grants (per v1's "Early L1/L2/L3 Creation: Reserve Grants" rule) be paid out at deploy or deferred?** Recommendation: defer until v2 reviewer infrastructure is live (Phase 2 of v2 rollout), so the gate-class verification can happen properly. Authors are credited for genesis inclusion immediately; the Reserve cash payment lands later.

---

## Decision log

| Date | Decision |
|---|---|
| 2026-04-29 | Director asked whether the genesis 500 contains v2/v3-class Principles that share A_k from day 1, given the auto-promotion fact in `pwm_overview1.md:1202`. Analysis: current 502 are 100% analytical; adding 10-15 `physical_with_discrete_readout` exemplars to the auto-promoted batch costs zero contract change and ~3-6 weeks authoring. Recommended Option B. |
| _TBD_ | Director picks the 10-15 from the 13 candidates listed above. |
| _TBD_ | Authoring complete; manifests in repo; validation passing. |
| _TBD_ | `register_genesis.js` updated; Sepolia dry-run successful. |
| _TBD_ | Mainnet deploy at Step 7 with the expanded genesis batch. |
| _TBD_ | At v2 deploy, governance batch-signs gate_class backfill for all genesis entries. |
| _TBD_ | 6-12 months post-mainnet: measure miner activity on v2-class genesis Principles. |

---

## Summary table

| Question | Answer |
|---|---|
| Are any v2/v3-class Principles in the current genesis? | **No.** All 502 are `analytical`. |
| Do genesis Principles share A_k from day 1? | **Yes** — they are auto-promoted per `pwm_overview1.md:1202`. |
| Do post-launch Principles share A_k from day 1? | **No** — they earn promotion via L4 activity, taking 6-12+ months. |
| Is this asymmetry contract-enforced or social? | **Contract-enforced** — `PWMMinting.A_k` formula sums only over promoted Principles. |
| Can the asymmetry be fixed without contract changes? | **Yes** — by adding v2-class Principles to the genesis batch (which is just a JSON list and a `register_genesis.js` argument). |
| Should `data_driven_statistical` Principles also be added to genesis? | **No** — they need an `L0_meta` parent that has no on-chain home until v2 Phase 2. They can stake post-v2 with the 0.5× multiplier. |
| Cost of executing the recommended fix? | **~3-6 weeks of authoring work; $0 in contract changes.** |
| Is the deadline the same as the Reserve resizing? | **Yes** — both are finalized at Base mainnet deploy (Step 7). |
| Cost of NOT executing it? | The first wave of `physical_with_discrete_readout` Principles arrives years later with no A_k head start, validating the "PWM is just imaging" critique even though v2 spec was designed to broaden the protocol. |

The asymmetry is structural, the fix is cheap, the deadline is the same one already on the calendar. **Add 10-15 `physical_with_discrete_readout` exemplars to the genesis batch before Step 7.**
