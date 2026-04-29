# PWM gate classes + scaling to 10,000+ Principles

**Date:** 2026-04-29
**Owner:** Director
**Audience:** PWM protocol designers; future `pwm_overview2.md` revision authors
**Status:** design proposal — not yet ratified
**Cross-references:**
- `papers/Proof-of-Solution/pwm_overview1.md` § 3 (current S1-S4 / P1-P10 framework)
- `pwm-team/pwm_product/genesis/CLASSIFICATION_SEGMENTATION_PRINCIPLES.md` (the case study that exposed the gap)

---

## The scaling problem

The current `principle.md` catalog has ~400 imaging Principles. Imaging
is one of dozens of computational-science domains. ML / CV alone has
thousands of distinct tasks; NLP has hundreds; RL, drug discovery,
recommendations, code generation each have hundreds more. So the long
tail is dominated by tasks where the operator E is implicit-in-the-
dataset rather than closed-form.

If PWM admits all of them with **statistical** gates, the protocol's
"analytical-rigor" brand dilutes. If it rejects all of them, PWM cuts
off most of computer science / ML / data science. **Neither extreme
works.** The protocol needs a stratification.

This doc proposes how.

---

## Is Option 2 (a meta-layer for data-driven Principles) sufficient on its own?

> Option 2 (from `CLASSIFICATION_SEGMENTATION_PRINCIPLES.md` § "Four
> ways to handle the gap"): add an `L0_meta` layer for data-driven
> Principles with `*`-marked statistical gates.

**Necessary but not sufficient.** Option 2 honestly captures the
analytical-vs-statistical split, which is the right minimum step. But
on its own it leaves three problems unsolved:

| Problem | Why Option 2 alone fails |
|---|---|
| **Reviewer load** | Two certificate classes; reviewers must check both. Adds friction. |
| **Reward dilution** | If `data_driven_statistical` Principles earn the same as `analytical` ones, the protocol over-rewards the easier-to-stake class — gravity pulls toward statistical. |
| **No recast incentive** | A contributor staking a "generic image classification" Principle has no nudge to consider whether the underlying problem is actually a physics-inverse (Option 3 from the principles guide) — they take the easier path. |

So **Option 2 + reward differentiation + an explicit `gate_class`
field + a reviewer checklist** is the full answer, not Option 2 alone.

### Proposed `gate_class` field

A new mandatory field on every L1 manifest:

```yaml
gate_class:
  one_of:
    "analytical"                       # full S1-S4, closed-form E
    "physical_with_discrete_readout"   # closed-form physics + threshold classifier
    "data_driven_statistical"          # statistical S2*/S3*/S4* gates
```

**Class definitions:**

```
"analytical"
  All four S-gates proved against a closed-form operator.
  The 400 current imaging Principles. CASSI, CT, MRI, FWI, etc.
  Reward share: FULL.

"physical_with_discrete_readout"
  Underlying physics is closed-form (Option-3 recast); a deterministic
  threshold/discretization function on top produces categorical labels.
  PillCam-SPECTRA (optical-property recovery → bleeding/polyp threshold);
  materials-microstructure classification; cell-type from RNA-seq;
  most medical AI when tissue properties are recoverable.
  Reward share: FULL — physics provides analytical gates.

"data_driven_statistical"
  No closed-form operator; gates are S2*/S3*/S4* (statistical certificates
  via VC / PAC-Bayes / conformal prediction).
  Generic CIFAR / ImageNet, NLP tasks, recommendations, code generation
  judged by human preference.
  Reward share: FRACTIONAL (e.g., 50%) — incentivizes Option-3 recast.
```

The reward differentiation is what makes the system work: contributors
have a real economic incentive to find the physics-recast wherever
it's possible.

---

## Can all non-S1-S4 problems be re-expressed to satisfy S1-S4?

**No — but more can than you'd think.** Three cases.

### Case A — Tasks with physical / scientific ground truth: YES

Wherever the labels correspond to physically real states, an Option-3
recast works:

| Task framed as | Recast as physics-inverse |
|---|---|
| "Bleeding detection on capsule frames" | `optical-property recovery → threshold` (PillCam-SPECTRA) |
| "Crystal structure classification from XRD" | `lattice-parameter inversion → space-group lookup` |
| "Pneumonia detection from chest X-ray" | `tissue-density reconstruction → severity threshold` |
| "Cell-type classification from RNA-seq" | `gene-expression vector recovery → cell-state manifold lookup` |
| "Galaxy classification from telescope images" | `galaxy-morphology parameter estimation → typological threshold` |
| "Drug-target binding affinity prediction" | `quantum-chemistry energy estimation → binding threshold` |
| "Earthquake magnitude classification" | `source-parameter inversion → magnitude scale` |
| "Protein function prediction" | `structure-folding inversion → functional motif lookup` |

In every row, labels are derivative — they're a discretization of a
continuous physical / chemical / biological state that admits a
closed-form forward model. The discretization is trivially gate-
satisfied (piecewise-constant function on continuous physical state).

### Case B — Tasks with mathematical / algorithmic ground truth: YES

When the task has a formal correctness criterion that's checkable
analytically, an analytical gate works:

| Task | Operator E | Analytical S1-S4? |
|---|---|---|
| Theorem proving (premise → proof) | proof-checker function | ✓ (operator IS the proof verifier; gates check soundness) |
| Code generation (formal spec → code) | spec compliance + test pass | ✓ (operator IS the test suite) |
| Combinatorial optimization (constraints → optimum) | objective function | ✓ (operator IS the provably-correct objective) |
| SAT solving | clause satisfaction | ✓ |
| Numerical-method certification (PDE solver verification) | residual + convergence proof | ✓ |
| Graph algorithm correctness | invariant checker | ✓ |

### Case C — Tasks with PURE conventional / social structure: NO

Some tasks have no underlying physical or mathematical ground truth —
only human convention or preference. These genuinely **cannot** be
cast as analytical S1-S4 because there's no objective operator. They
need Option 2's statistical gates:

| Task | Why no analytical recast |
|---|---|
| Machine translation (English → Spanish) | Language is conventional; no operator from English semantics to Spanish (translation is multi-valued, judged by humans) |
| Sentiment classification | "Positive / negative" is a human construct, not a measurable property |
| Recommendation systems | Preference is subjective; no operator from user state to "correct" recommendation |
| Image generation aesthetics | "Pretty" is contextual / cultural, not a physical property |
| Style transfer | "Style" is a perceptual category without a closed-form operator |
| Most NLP tasks (sentiment, NER, summarization) | Language has no physical operator |
| Humor / sarcasm detection | Pure cultural-context judgment |
| Music recommendation | Subjective taste |

For these, Option 2 (statistical gates with `*`) is the only honest
framing. Option 4 (diffusion-as-operator from the principles guide)
gives a *learned* operator but inherits the diffusion model's quality
limits — strictly weaker than analytical.

---

## The boundary, in one sentence

> **A task can be analytically gated by S1-S4 if and only if there's
> an objective ground truth defined by physics, mathematics, or formal
> verification — not by human convention or empirical aggregation.**

This is the litmus test for Principle reviewers. If a contributor
staking a Principle can't point at the closed-form operator (or
the verifier function), the manifest must declare
`gate_class: "data_driven_statistical"` and the reward share is
fractional.

---

## Concrete projection for a 10,000-Principle PWM

If PWM grew to 10,000+ Principles across the full breadth of
computational science + ML, the distribution would likely be:

| `gate_class` | Original projection | Revised projection (under standalone-as-default) | Domains |
|---|---|---|---|
| `analytical` | ~30% | **~40%** | Imaging (current 400), PDE, signals, scientific computation, formal CS (theorem proving, code gen, optimization, SAT), **plus standalone multi-physics** (FSI, multi-scale materials, climate attribution, multi-messenger astronomy, QSM, qPAT, joint MEG-EEG, etc. — see `PWM_V3_STANDALONE_VS_COMPOSITE.md` and `PWM_V3_MEDICAL_IMAGING_CANDIDATES.md`) |
| `physical_with_discrete_readout` | ~50% | **~45%** | Most medical AI with thresholdable physics (PillCam-SPECTRA, crystal-XRD classification, tissue-density classification), materials microstructure classification, cell-type from RNA-seq, galaxy morphology classification |
| `data_driven_statistical` | ~20% | **~15%** | Pure NLP, recommendations, aesthetics, cultural / linguistic tasks, subjective preference |
| Composites (separate axis — fraction of all Principles registered as `L1_COMPOSITE`) | implicit | ~5-10% | Explicit-credit fusion with multi-parent royalty; the minority form, used when contributor wants on-chain upstream royalty flow |

The revision reflects the design refinement in `PWM_V3_STANDALONE_VS_COMPOSITE.md`: standalone multi-physics Principles register as v1-analytical with `n_c > 0` in their L_DAG breakdown. This absorbs methods like FSI, qPAT, QSM, and multi-scale materials into the analytical bucket rather than forcing them into the composite framework.

PWM stays "physics / math-grounded" for **~85% of the catalog** under the revised projection — slightly higher than the original ~80% because standalone multi-physics is admitted under analytical.

This is the right balance: the protocol covers most of computational
science + ML without diluting its analytical brand, and the reward
mechanism naturally pushes contributors toward the cleanest available
gate class. The composite form remains for the explicit-credit minority — used when contributors specifically want on-chain royalty flow to upstream authors.

---

## Recommended PWM evolution sequence

| Phase | Spec | What changes |
|---|---|---|
| **Now** | `pwm_overview1.md` | 100% `analytical`. Imaging-only. The current state. |
| **Next major revision** | `pwm_overview2.md` | Add `gate_class` field. Add `L0_meta` for data-driven. Reward differentiation table (full / full / fractional). Document Option-3 recast as canonical pattern. Reviewer checklist enforces `gate_class`. |
| **Further out** | `pwm_overview3.md` | Hierarchical Principle registry (domain → sub-domain → task). Automated S1-S4 verification tooling. AI-assisted Principle authoring per § 9 of the current spec. Handles the 10K+-Principle scaling. |

### What `pwm_overview2.md` must include

1. **A new "discrete-output extension" subsection** explicitly handling
   the gate substitutions for non-continuous problems:
   - `condition number κ` → `class-manifold separation Δ`
   - `mesh resolution h` → `1/sqrt(n_train)`
   - `conservation laws (P1)` → `softmax-simplex closure + permutation invariance`

2. **A `gate_class` field** in the L1 manifest (described above).

3. **A reward differentiation table:**
   ```
   gate_class                          | reward_share
   ────────────────────────────────────────────────────
   analytical                          | 1.00 × base
   physical_with_discrete_readout      | 1.00 × base
   data_driven_statistical             | 0.50 × base
   ```

4. **A reviewer checklist** — manifest reviewers must verify:
   - For `analytical`: the operator is closed-form, written explicitly in the `E.forward_model` field
   - For `physical_with_discrete_readout`: the threshold function is continuous in the underlying physical state, and the physics core has its own analytical S1-S4
   - For `data_driven_statistical`: the certificates are computed and the assumptions are listed (iid sampling, smoothness, bounded VC dimension, etc.)

5. **Distance metrics extension** — the current `d_principle` Jaccard
   distance compares physics fingerprints. For data-driven Principles,
   the analogue is dataset / task overlap (Jaccard on dataset
   identifiers + task type). Both metrics coexist depending on the
   gate class being compared.

---

## What `pwm_overview3.md` must include (longer-horizon scaling)

When the Principle catalog grows past ~1000 entries, the protocol
needs:

1. **Hierarchical registry.** Top-level domains (Computer Vision,
   NLP, Materials, Biology, Imaging Physics, Formal CS, …); each
   domain has sub-domains; each sub-domain has Principles. Reviewer
   workload is bounded by domain assignment.

2. **Automated S1-S4 verification.** Tooling that checks the
   manifest's claimed gates against the operator (for `analytical`),
   computes the bound (for `data_driven_statistical`), or verifies
   the threshold-function continuity (for
   `physical_with_discrete_readout`). Reduces reviewer load by 5-10×.

3. **AI-assisted Principle authoring.** The `pwm_overview1.md` § 9
   already mentions "Agent opens a new principle from a seed." When
   there are 10K candidate Principles and only 50 expert reviewers,
   AI agents draft the manifests; humans review for correctness.
   The `gate_class` field is what makes AI authoring possible — the
   class determines the manifest template.

4. **Cross-domain Principle composition.** Some problems combine
   multiple Principles (e.g., a multimodal medical-AI task uses
   imaging physics + biology + statistics). The protocol needs a
   composition operator that aggregates gate classes appropriately
   (the result is at most as strong as the weakest component).

---

## Decision log

| Date | Decision |
|---|---|
| 2026-04-29 | Director asked the scaling question after the classification/segmentation case study exposed the analytical-vs-statistical gap. This doc proposes the `gate_class` + reward differentiation framework as the response. |
| _TBD_ | `pwm_overview2.md` revision authored, with `gate_class` field + reward table + reviewer checklist + L0_meta layer + discrete-output extension subsection |
| _TBD_ | First batch of `physical_with_discrete_readout` Principles registered (PillCam-SPECTRA `L1-PHYS-GI-001a` + `L1-PHYS-GI-001b` is the canonical pilot per `CLASSIFICATION_SEGMENTATION_PRINCIPLES.md`) |
| _TBD_ | Reviewer training on the new gate-class system |
| _TBD_ | `pwm_overview3.md` for the 10K+ scaling regime |
