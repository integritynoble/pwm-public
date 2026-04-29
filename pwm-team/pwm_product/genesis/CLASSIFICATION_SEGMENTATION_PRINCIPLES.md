# Writing PWM principles for classification and segmentation

**Date:** 2026-04-29
**Owner:** Director
**Audience:** future principle contributors; PillCam-SPECTRA flagship co-authors
**Status:** design guide; templates ready for filing under `genesis/l1/`
**Cross-references:**
- `papers/Proof-of-Solution/pwm_overview1.md` § 3-5 (Principle / Spec / Benchmark schemas)
- `papers/Proof-of-Solution/mine_example/principle.md` (400-Principle catalog by domain)
- `papers/universal_simulation/arxiv/main.pdf` (cross-cutting framework)
- `pwm-team/pwm_product/genesis/l1/L1-003.json` (canonical CASSI Principle as schema reference)
- `pwm-team/pwm_product/genesis/l2/L2-003.json` (canonical CASSI Spec)

---

## TL;DR

The PWM L1/L2/L3 schema is built around forward-model inverse problems
(measurement physics → solve for hidden state). Classification and
segmentation aren't natively physics-inverse problems, but the
framework absorbs them cleanly if you cast them as **estimating
discrete labels from a noisy sensing process**.

The minimal cast:

| Task | Forward model E | Inversion target |
|---|---|---|
| **Classification** | `x = R(c, θ, φ) + n`; observation is the noisy image, latent is the **scalar** class label `c ∈ {1,…,K}` | x → ĉ |
| **Segmentation** | `x = R(L, θ, φ) + n`; latent is the **per-pixel** label tensor `L ∈ {1,…,K}^{H×W}` | x → L̂ |

Both are well-posed when class manifolds are separable enough
(Bayes-optimal error bounded), have a primitive decomposition
(featurization → projection → softmax / per-pixel softmax), and
admit error bounds (cross-entropy generalization for classification;
pixel-wise Dice/IoU concentration for segmentation).

---

## L1 template — image classification

`pwm-team/pwm_product/genesis/l1/L1-CLS-001.json`:

```json
{
  "artifact_id": "L1-CLS-001",
  "layer": "L1",
  "title": "Image Classification under Sensor Noise",
  "domain": "Computer Vision",
  "sub_domain": "Discrete-label inference",
  "E": {
    "description": "Forward sensing of a scene drawn from one of K class manifolds, observed through a noisy sensor.",
    "forward_model": "x = R(c, θ, φ) + n,  c ~ p(c),  θ ~ p(θ|c),  n ~ N(0, σ²)",
    "world_state_x": "discrete class label c ∈ {1,…,K}; latent scene θ ∈ Θ_c (class-conditional manifold)",
    "observation_y": "image x ∈ R^{H × W × C} (sensor-quantized + noised)",
    "physical_parameters_theta": [
      "K: number of classes",
      "Θ_c: class-conditional scene manifold",
      "φ: sensor parameters (resolution, noise, color profile)",
      "p(c): class prior"
    ]
  },
  "G": {
    "dag": "F.feature_extract -> Π.linear -> N.softmax",
    "vertices": ["F.feature_extract", "Π.linear", "N.softmax"],
    "L_DAG": 2.5,
    "n_c": 0
  },
  "W": {
    "existence": true,
    "uniqueness_condition": "Bayes-irreducibility — posterior p(c|x) has unique mode for Lebesgue-a.e. x; equivalent to no two class-conditionals being identical on a positive-measure set",
    "stability_condition": "Lipschitz in x with constant L_post depending on class separation Δ and noise σ",
    "regime": "K classes, Gaussian sensor noise σ, class-manifold separation Δ; well-posed iff Δ ≥ c·σ for c = c(K). Boundary samples (Δ ≈ σ) admit irreducible Bayes error and are treated as distributional uncertainty, not Hadamard violation.",
    "S2_status": "conditionally_satisfied"
  },
  "C": {
    "solver_class": "ERM with cross-entropy loss; deep neural network (CNN / ViT / linear-probe-on-foundation-model)",
    "convergence_rate_q": 0.5,
    "convergence_rate_q_realizable": 1.0,
    "convergence_h": "h = 1/sqrt(n_train)",
    "error_bound_VC": "excess_risk(ĥ_n) ≤ C · sqrt(VC_dim · log(n_train) / n_train)",
    "error_bound_PAC_Bayes": "pop_err(ĥ_n) ≤ train_err + sqrt((KL(posterior || prior) + log(2·sqrt(n)/δ)) / (2(n-1)))",
    "error_bound_conformal": "P[c_true ∈ ĉ_set(x)] ≥ 1 − α (marginal coverage, computable post-hoc)",
    "S3_status": "satisfied",
    "S4_status": "satisfied — VC + PAC-Bayes + conformal certificates all computable from (dataset, trained model)"
  },
  "physics_fingerprint": {
    "carrier": "photon",
    "sensing_mechanism": "imaging",
    "integration_axis": "spatial",
    "problem_class": "categorical_inverse",
    "noise_model": "gaussian",
    "solution_space": "categorical_K"
  }
}
```

---

## L1 template — semantic segmentation

`pwm-team/pwm_product/genesis/l1/L1-SEG-001.json`:

```json
{
  "artifact_id": "L1-SEG-001",
  "layer": "L1",
  "title": "Semantic Segmentation under Sensor Noise",
  "domain": "Computer Vision",
  "sub_domain": "Per-pixel label inference",
  "E": {
    "forward_model": "x[i,j] = R(L[i,j], θ_neighbor, φ) + n[i,j]",
    "world_state_x": "label tensor L ∈ {1,…,K}^{H × W}; class-conditional appearance + neighbor coupling θ_neighbor",
    "observation_y": "image x ∈ R^{H × W × C}",
    "physical_parameters_theta": [
      "K: number of classes",
      "appearance model R: per-class texture distribution",
      "neighbor coupling: spatial smoothness of L (MRF/CRF prior)",
      "φ: sensor"
    ]
  },
  "G": {
    "dag": "F.feature_extract_multiscale -> K.spatial_aggregate -> N.softmax_per_pixel",
    "vertices": ["F.feature_extract_multiscale", "K.spatial_aggregate", "N.softmax_per_pixel"],
    "L_DAG": 3.5,
    "n_c": 1
  },
  "W": {
    "existence": true,
    "uniqueness_condition": "per-pixel Bayes-irreducibility — posterior p(L[i,j] | x, neighbors) has unique mode for Lebesgue-a.e. x in the interior of regions",
    "stability_condition": "per-pixel Lipschitz with class-separation-dependent constant; boundary regions admit distributional discontinuities (sharp class transitions) — treated as standard distributional relaxation, NOT Hadamard violation",
    "regime": "K classes per pixel, sensor noise σ, class-manifold separation Δ; well-posed in the interior of regions iff Δ ≥ c·σ. Boundary pixels: irreducible Bayes error scaling with edge length / image area.",
    "S2_status": "conditionally_satisfied"
  },
  "C": {
    "solver_class": "FCN / U-Net / DeepLab / SAM-class with per-pixel cross-entropy + Dice loss",
    "convergence_rate_q": 0.5,
    "convergence_rate_q_realizable": 1.0,
    "convergence_h": "h = 1/sqrt(n_train_pixels)  (pixel-wise) or 1/sqrt(n_train_images)",
    "error_bound_per_pixel_VC": "per_pixel_excess_risk ≤ C · sqrt(VC_dim · log(n) / n)",
    "error_bound_mIoU": "|empirical_mIoU − Bayes_mIoU| ≤ C · sqrt(log(K/δ) / n_test)  (McDiarmid concentration; mIoU is a smooth function of the K×K confusion matrix; changing one prediction changes mIoU by O(1/n_pixel))",
    "error_bound_conformal_mask": "P[L_true ⊆ L̂_set(x)] ≥ 1 − α (mask-set conformal coverage, computable post-hoc)",
    "S3_status": "satisfied",
    "S4_status": "satisfied — pixel-wise VC + mIoU McDiarmid + conformal-mask certificates"
  }
}
```

`n_c = 1` reflects the spatial-coupling cross-edge in the DAG: the
neighbor-aggregation primitive `K.spatial_aggregate` shares state
with itself across pixels (it's not a pure feed-forward chain).

---

## What R actually is (rigorous form)

The one-line `forward_model` strings in the templates above are
shorthand. Here are the explicit generative processes they encode.

### Classification — class-conditional data-generating process

```
c       ~ p(c)                         (class prior)
θ       ~ p(θ | c)                     (class-conditional latent: pose, instance, scene)
x_clean = render(c, θ, φ)              (deterministic given (c, θ, φ))
x       = x_clean + n,  n ~ N(0, σ²I)  (sensor + noise)
```

`render` does NOT need a closed analytical form. For natural-image
benchmarks it's specified implicitly by the empirical distribution of
the training/benchmark dataset — `render` is "nature's renderer"
sampled by the dataset. For synthetic benchmarks (e.g., dSprites,
CLEVR), it's a literal graphics engine.

For PWM purposes the specification of R reduces to:
**dataset registry** (defines `p(x | c)`) + **noise model** (defines
`n` distribution).

### Segmentation — per-pixel class-conditional appearance + spatial coupling

```
L                 ~ p(L) = MRF/CRF prior over {1,…,K}^{H×W}
                          (smoothness within regions, boundaries between)
θ_neighbor[i,j]   = (texture patch, illumination, geometry context for (i,j))
x_clean[i,j]      = appearance(L[i,j], θ_neighbor[i,j], φ)
x[i,j]            = x_clean[i,j] + n[i,j]
```

`θ_neighbor[i,j]` couples adjacent pixels — that's the `n_c = 1`
cross-edge in the L1 DAG. The MRF prior `p(L)` is what makes "the
cat's leg pixels are mostly cat" preferred over salt-and-pepper class
noise. Concretely realized by the dataset's labeled masks (defines
the empirical distribution of label tensors) plus an explicit
smoothness prior used at inference time.

---

## Do these satisfy S2 / S3 / S4?

| Gate | Classification | Segmentation |
|---|---|---|
| **S2** Hadamard well-posedness | **Conditionally ✓** (Bayes-irreducibility + σ < Δ regime) | **Conditionally ✓** (per-pixel Bayes-irreducibility; boundaries admit distributional discontinuities) |
| **S3** Convergent solver exists | ✓ | ✓ |
| **S4** Bounded error certificate | ✓ | ✓ |

### S2 — Well-posedness (Hadamard)

**Existence.** The MAP estimator `ĉ = argmax_c p(c|x)` is well-defined
for any x — c ∈ {1,…,K} is finite, so argmax always exists. Same for
per-pixel `L̂[i,j]`. Unconditionally ✓.

**Uniqueness.** Unique iff `p(c|x)` has a unique mode. Equivalently:
for almost every x, no two classes share posterior probability —
the **Bayes-irreducibility condition**:

```
For Lebesgue-a.e. x:   argmax_c  p(x|c) p(c)   is a singleton.
```

This holds when class-conditional distributions don't perfectly
overlap on a positive-measure set. Fails on fundamentally ambiguous
samples (e.g., a 28×28 binary image that's both a "1" and a "7" with
positive probability).

For segmentation: per-pixel Bayes-irreducibility. **Boundaries are a
known soft-failure** — sharp class transitions are discontinuities in
the posterior and so technically violate Hadamard's continuous-
dependence condition, but they're treated as standard distributional
relaxations (the same way CASSI treats spectral edges).

**Continuity.** When class-conditional likelihoods are continuous in
x, the posterior is continuous in x — small noise → small posterior
change. ✓ when σ is small relative to class separation Δ; **fails**
near decision boundaries where Δ ≈ σ.

**Net S2 verdict:** satisfied in the regime where `Δ > c·σ` (class
separation exceeds c standard deviations of noise; c depends on K).
The L1 manifest's `W.regime` field encodes this. Boundary samples
generate **irreducible Bayes error** rather than violating the gate.

### S3 — Convergent solver exists

For supervised tasks "convergence" means the learned classifier
converges to the Bayes-optimal one as training data grows. Natural
`h = 1/sqrt(n_train)`.

**Classification.** ERM with cross-entropy + bounded-VC-dimension
classifier achieves:

```
excess_risk(ĥ_n)  =  E[L(ĥ_n)] − L*  ≤  C · sqrt(VC_dim · log(n) / n)
```

This is the standard Vapnik-Chervonenkis bound (1971; refined by
Bartlett et al.). Convergence rate `q = 1/2` in `h = 1/sqrt(n)`.
Faster rates (`q = 1`) under realizable / margin / Tsybakov noise
conditions.

For deep networks: results by Schmidt-Hieber (2020) and
Bartlett-Foster-Telgarsky (2017) give similar O(1/sqrt(n)) bounds for
ReLU networks under Sobolev-smoothness assumptions on the
class-conditional distributions.

**Segmentation.** Per-pixel ERM gives the same per-pixel bound;
McDiarmid concentration on mIoU (since changing one pixel prediction
changes mIoU by O(1/n_pixel)) gives mIoU concentration around the
Bayes-optimal value at the same O(1/sqrt(n)) rate.

`q = 0.5` (or `1.0` under margin assumptions) ✓.

### S4 — Bounded error certificate

Three classes of computable, certified bounds — each yields an
explicit `e(h) ≤ C h^α`.

**(a) Held-out test bound (classification + segmentation):**

```
|test_err − population_err|  ≤  sqrt(log(2/δ) / (2 n_test))   w.p. ≥ 1 − δ
```

Hoeffding inequality. No architecture dependence; just needs an iid
held-out set.

**(b) PAC-Bayes (for trained networks):**

```
pop_err(ĥ_n)  ≤  train_err  +  sqrt( (KL(posterior || prior) + log(2 sqrt(n)/δ)) / (2(n−1)) )
```

McAllester (1999); Catoni (2007). Computable for any specific
architecture + training procedure (the KL term is the cost of
deviating from a chosen prior).

**(c) Conformal prediction (set-valued certificate):**

For classification:
```
P[ c_true ∈ ĉ_set(x) ]  ≥  1 − α   (marginal coverage)
```

For segmentation, the analogue is **conformal mask sets**:
```
P[ L_true ⊆ L̂_set(x) ]  ≥  1 − α   (per-pixel or per-region coverage)
```

Computable post-hoc on a calibration set. Always honest (no
distribution assumptions beyond exchangeability).

For mIoU specifically (segmentation), McDiarmid gives:

```
|empirical_mIoU − Bayes_mIoU|  ≤  C · sqrt( log(K/δ) / n_test )
```

where the constant absorbs the Lipschitz constant of mIoU as a
function of the K×K confusion matrix.

**Net S4 verdict:** satisfied for both tasks. Multiple
complementary certificates available; pick one (or stack them) for
the L4 acceptance check.

---

## Honest critique: do they REALLY satisfy S1-S4?

The "conditionally ✓" verdicts above are technically correct but
gloss over a deeper structural difference. PWM was designed for
**analytical** gate satisfaction, and the substitutes I gave for
classification / segmentation are **statistical / empirical**. Those
substitutes are real and rigorous, but they are a weaker class of
certificate.

### Where the analytical-vs-statistical split shows up

| Aspect | CASSI / CT / MRI (canonical) | Generic classification / segmentation |
|---|---|---|
| E | Closed-form analytical operator (Radon, integral equation, mask × shift) | Empirical distribution `p(x\|c)` defined by dataset |
| S1 | Provable from the operator's signature | Provable (tensor shapes are a-priori) |
| S2 | **Theorem** (RIP, sparsity, mask quality) | **Empirical claim** (no two class-conditionals overlap; depends on dataset) |
| S3 | **Theorem** (Cèa, regularization theory) | **Empirical claim** (ERM converges; rate depends on architecture + smoothness assumptions) |
| S4 | **Analytical** (`‖f̂−f‖ ≤ C₁σ/√m + C₂‖f−f_s‖₁`) | **Distributional** (Hoeffding / PAC-Bayes / conformal — needs an iid sample) |

This isn't just notation. The CASSI principle's W block guarantees
recovery is unique under sparsity priors **regardless of any
dataset** — it's a theorem about the operator. The generic
classification principle's W block guarantees uniqueness **only on
the empirical distribution observed so far** — it's a property of
the training set.

A reviewer evaluating the two manifests should see this difference.
A staked Principle that promises analytical S1-S4 is a stronger
claim than one that promises statistical S1-S4*.

### Four ways to handle the gap

**Option 1 — Reject. These aren't PWM principles.**

Classification / segmentation as generic CV tasks live in MLPerf,
Papers With Code, OpenAI Evals. Don't pollute PWM with them. PWM
stays rigorous; the framework's value is precisely that every
Principle has analytical S1-S4 certificates.

- Pro: preserves PWM's analytical brand.
- Con: excludes a huge research area; PillCam-SPECTRA can't be a
  PWM L3 anchor under this rule.

**Option 2 — Add a meta-layer (`L0_meta`) for data-driven principles.**

Define a meta-Principle at a layer ABOVE L1:

```
L0_meta: "Discrete-output supervised learning under iid sampling
          with bounded-VC hypothesis class"

  E:    R(c, θ, φ) defined empirically by a held-out distribution
  S1:   tensor-shape consistency (analytical)
  S2*:  empirical Bayes-irreducibility (measurable on dev set)
  S3*:  ERM convergence q ≥ 0.5 (theorem, but conditional on
        data smoothness assumptions)
  S4*:  VC / PAC-Bayes / conformal certificates
        (computable; assumption-bounded)
```

Specific tasks become L1 instances of `L0_meta`. The `*` is honest
notation: these are **statistical** gate satisfactions, not
analytical.

- Pro: makes the difference explicit; lets PWM cover both worlds.
- Con: requires a protocol revision (`pwm_overview2.md`); reviewers
  see two grades of certificate.

**Option 3 — Recast medical / scientific segmentation as physics-inverse.**

This is the cleanest path **for the work that actually matters in
this codebase** (PillCam-SPECTRA, MRI segmentation, materials-
microstructure segmentation, etc.). Re-frame the problem: the L1
isn't "label-tensor inference" — it's **physical-property estimation
that happens to discretize at the end.**

For PillCam-SPECTRA, the principled cast is two L1 principles in
sequence:

```
L1-PHYS-GI-001a  "GI Tissue Optical-Property Reconstruction
                  from Wireless Capsule Multispectral Imaging"

  E (analytical forward model):
     x[i,j,λ]  =  ∫ Φ_LED(λ) · exp(-μ_a(tissue, λ)·d) · BRDF(tissue, λ)  dΩ
                + scattering(μ_s, g)
                + sensor_response(φ)
                + n[i,j,λ]

     World state: per-pixel optical properties — hemoglobin
     concentration cHb[i,j], oxygen saturation SO₂[i,j], scattering
     anisotropy g[i,j], tissue depth d[i,j].

     Observation: the multispectral capsule frame x.

  S1: ✓ analytical (radiative transfer is dimensionally consistent)
  S2: ✓ analytical under known regularity conditions on optical
        properties (smoothness + boundary continuity in tissue)
  S3: ✓ analytical (Levenberg-Marquardt + Monte Carlo unfolding;
        published convergence rates from biomedical-optics literature)
  S4: ✓ analytical (Cramér-Rao bounds on cHb / SO₂ recovery;
        Wasserman & DeWeese 2007 + follow-ups)


L1-PHYS-GI-001b  "GI Tissue Class Inference from Optical Properties"

  E: deterministic threshold function over (cHb, SO₂, g, d):
     bleeding   ↔ cHb high, SO₂ varies, μ_s elevated
     AVM        ↔ vascular density anomaly
     polyp      ↔ tissue depth + cHb signature
     normal     ↔ baseline
  S1-S4: trivially satisfied for piecewise-deterministic
         classifiers over continuous physical state
```

The Director's MDPI paper's **Monte Carlo–guided hemoglobin prior**
is exactly the analytical operator for `L1-PHYS-GI-001a`. The
"multi-task AI pipeline" (Module 1/2/3) implements the inverse of
THIS operator, not a generic image-classification operator.
Recasting in this form makes PillCam-SPECTRA a properly-grounded
PWM Principle with **analytical** S1-S4, the same standard as CASSI.

- Pro: preserves analytical rigor; PillCam-SPECTRA becomes a
  textbook PWM Principle; the segmentation labels (bleeding /
  polyp / normal) are derived from physically meaningful
  intermediate state.
- Con: requires more rigorous physical modeling than "FCN on
  labels"; doesn't help generic CV tasks (CIFAR-10 has no
  underlying physics).

**Option 4 — Construct an implicit operator via a generative model.**

A trained class-conditional diffusion model defines an explicit
(if complex) `render(c, θ, φ) = sample_diffusion(noise_seed,
conditioning=c, ...)`. The forward operator is now a learned
function — analytical in the sense that it's a fixed neural network,
just with a learned parameter set rather than a hand-derived one.

S1-S4 can then be evaluated against this learned operator:
- S1: the diffusion model's input/output tensor shapes are explicit
- S2: well-posedness of inverting `render` (recover c from a sample)
      becomes a property of the score function — measurable
- S3: classifier-free guidance + class-conditional denoising has
      known convergence rates
- S4: bounds on inversion error available
      (denoising-diffusion-implicit / posterior-sampling literature)

- Pro: brings even non-physical tasks (CIFAR-10) into a partially-
  analytical frame. The forward "operator" is at least an explicit
  function, even if learned.
- Con: S2-S4 quality depends on the diffusion model's quality; a bad
  diffusion model gives a bad Principle; reviewers must inspect the
  model card alongside the manifest.

### Recommendation

For PWM as a protocol, **Option 3 is the canonical path** for
science-domain tasks (medical imaging, materials, biology,
spectroscopy). It's also what the Director's research already does
implicitly — the MDPI paper's Monte Carlo physics prior is exactly
the analytical forward operator. Make this explicit in the L1
manifest and segmentation becomes a textbook PWM Principle.

For non-physics-domain classification (CIFAR, ImageNet),
**Option 1 + Option 4 in combination**: don't make these PWM
Principles; if a contributor must, register them under an explicit
`L0_meta` layer (Option 2) with `*`-marked statistical gate
satisfaction so reviewers know the difference.

For PillCam-SPECTRA / GI_Multi_Task specifically, the Principle
should be:

| Don't | Do |
|---|---|
| `L1-SEG-GI-001` (generic segmentation; statistical gates marked `*`) | `L1-PHYS-GI-001a` (optical-property recovery; analytical gates) + `L1-PHYS-GI-001b` (threshold classifier on optical properties; trivially satisfied) |

This connects the PWM-flagship paper's "GI L3 anchor" cleanly to the
canonical PWM framework — the same standard of rigor as CASSI / CT /
MRI — and gives the MDPI paper's physics-informed multi-task
pipeline a principled home. The segmentation isn't an afterthought
fitted into a non-physics framework; it's the natural readout of an
underlying physics-inverse problem the paper has already solved.

### What needs to land in `pwm_overview2.md`

A revision of the canonical Principle spec should add:

1. **A "discrete-output extension" subsection** explicitly handling
   the substitutions: `κ → Δ` (class separation), `mesh resolution →
   1/sqrt(n_train)`, `conservation laws → softmax-simplex closure +
   permutation invariance`.

2. **A `gate_class` field** in the L1 manifest that takes one of:
   - `"analytical"` (CASSI, CT, MRI, etc. — all four S-gates proved)
   - `"physical_with_discrete_readout"` (Option 3 — analytical
     gates on the physics core; trivial classifier on top)
   - `"data_driven_statistical"` (Options 2 / 4 — gates marked
     with `*`, statistical certificates required)

3. **Stricter reward differentiation**: analytical-gate Principles
   earn full reward share; `data_driven_statistical` Principles
   earn at most a configurable fraction (e.g., 50%). This
   incentivizes the Option-3 recast where it's possible.

4. **Reviewer checklist** — manifest reviewers must verify:
   for `analytical`, the operator is closed-form; for
   `physical_with_discrete_readout`, the threshold function is
   continuous in the physical state; for `data_driven_statistical`,
   the certificates are computed and the assumptions are listed.

Until `pwm_overview2.md` lands, contributors should follow Option 3
where physics is available and Option 2's `L0_meta` framing where
it isn't — and explicitly mark the gate class in the manifest's
`notes` field.

---

## How this compares to the canonical L1-003 (CASSI) gate satisfaction

| Aspect | L1-003 CASSI (continuous inverse) | L1-CLS-001 / L1-SEG-001 (discrete inverse) |
|---|---|---|
| Forward model E | analytical (`y = ∑ C·shift(x_b)`) | empirical (dataset-defined `p(x\|c)`) + noise model |
| Uniqueness condition | sparsity prior + RIP-like mask | Bayes-irreducibility (no two class-conditionals identical a.e.) |
| Stability bound | condition number κ (bounded by mask quality) | class-manifold separation Δ vs noise σ |
| Convergence "h" | mesh / iteration count | 1/sqrt(n_train) |
| Error bound C | Cèa-style: `‖f̂ − f‖₂ ≤ C₁σ/√m + C₂‖f − f_s‖₁` | VC / PAC-Bayes / conformal: `excess_risk ≤ C·sqrt(d·log(n)/n)` |
| P1 (conservation) | mass / energy / momentum | softmax-simplex closure + label-permutation invariance |

The structural parallel is exact. The discrete-output extension
just substitutes the right asymptotic regime (n_train instead of
mesh resolution) and the right stability quantifier (Δ instead of
κ). Future PWM revision (`pwm_overview2.md`) should add a
"discrete-output extension" subsection codifying these substitutions
so each new classification/segmentation Principle doesn't have to
re-derive them.

---

## L2 carve-up (for both classification and segmentation)

Both follow the same six-tuple pattern as `L2-003.json` (Ω, E, B, I, O, ε):

| Field | Classification | Segmentation |
|---|---|---|
| **Ω** (parameter ranges) | image size [32, 4096], K [2, 1000], noise [0, 0.2], class-imbalance ratio, foundation-model size | same + label density per class, mask granularity (pixel vs panoptic), boundary tolerance |
| **B** (constraints) | softmax simplex output; ŷ ∈ Δ^K | per-pixel softmax simplex; optional smoothness / CRF / connected-component priors |
| **I** (init) | foundation-model prior (CLIP / DINO / SAM) or random | same |
| **O** (output metrics) | top-1 accuracy, top-5, macro-F1, ECE (calibration), ROC-AUC, balanced-accuracy | mIoU, Dice, pixel accuracy, boundary-F1, panoptic quality (PQ) |
| **ε(Ω)** (acceptance threshold) | `25.0 + 5.0·log₂(K/10) − 3.0·noise/0.05` (PSNR-style; in top-1-accuracy points) | `25.0 + 5.0·log₂(K/5) + 2.0·log₁₀(H·W/65536) − 3.0·noise/0.05` |

`epsilon_fn` formulas above are illustrative — calibrate against
published baselines on the chosen L3 benchmark before staking.

---

## L3 anchor suggestions

| Task | Tier | Dataset | Why |
|---|---|---|---|
| Classification | T1_textbook | CIFAR-10 | small, well-understood; baselines abundant |
| Classification | T2_standard | CIFAR-100 | 10× more classes; tougher manifold separation |
| Classification | T3_advanced | ImageNet-1k | the canonical large-scale benchmark |
| Classification | T4_frontier | iNaturalist 2021 | long-tail, fine-grained; tests calibration |
| Segmentation | T1_textbook | Pascal VOC 2012 | 21 classes, 1.5K val images |
| Segmentation | T2_standard | Cityscapes-fine, COCO-Stuff | road-scene + complex backgrounds |
| Segmentation | T3_advanced | ADE20K | 150 classes, scene-level diversity |
| Segmentation (medical) | T2_standard | CVC-ClinicDB (polyp seg) | small but clean clinical baseline |
| Segmentation (medical) | T3_advanced | EndoVis / Kvasir-Capsule masks | large-scale GI endoscopy |
| Segmentation (medical) | T4_frontier | UTSW multi-center retrospective (post-IRB) | clinical translation cohort |

---

## PillCam-SPECTRA / GI_Multi_Task mapping (the Director's research)

The `integritynoble/GI_Multi_Task` work is literally
classification + segmentation on wireless-capsule-endoscopy frames.
The natural mapping into PWM:

```
L1-SEG-GI-001
  title: "Wireless Capsule Endoscopy Semantic Segmentation
          under Low-Light + Glare"
  domain: "Medical Imaging"
  sub_domain: "GI endoscopy, multi-task per-pixel labeling"
  E.physical_parameters_theta:
    - K = 5 classes (bleeding, AVM, polyp, normal_mucosa, void)
    - capsule LED illumination model φ_LED
    - WCE optics + bayer-pattern sensor model φ_optics
    - Monte Carlo hemoglobin prior (per the MDPI paper)
  G.dag:
    "F.feature_extract_capsule -> K.spatial_aggregate -> N.softmax_per_pixel
     ⊕ Module 1 (physics-informed prior: MC hemoglobin map) -> N.condition"
  W.regime:
    "small-bowel illumination geometry; bleeding contrast > 3:1 over
     mucosa; glare regions classified as void"
  C.solver_class:
    "physics-informed multi-task CNN (PillCam-SPECTRA Module 2)
     with Monte Carlo prior fed as auxiliary channel (paper's
     Module 1 → Module 2 → Module 3 pipeline)"
```

```
L2-SEG-GI-001:
  Ω: WCE-typical (256×256 to 512×512), K=5, noise σ ∈ [0.01, 0.08],
     glare fraction ∈ [0, 0.3], blood-presence prior ∈ [0, 1]
  B: smoothness CRF + bleeding-class fragility = 0.7
  I: ImageNet-pretrained EfficientNet-B0 (per the MDPI paper backbone)
  O: per-class IoU, blood-detection sensitivity, blood-detection specificity,
     reading-time-reduction proxy
  ε: mIoU ≥ 0.45 on T2_standard tier; bleeding-class IoU ≥ 0.55

L3-SEG-GI-001 (T2_standard):
  primary: Kvasir-Capsule (public, with masks)
  secondary: CVC-ClinicDB (polyp segmentation)
  holdout: UTSW retrospective frames from Vemulapalli/Casey
           (Phase 2, post-IRB; not in MDPI paper)
```

This connects the PWM-protocol L3 catalog directly to the
`paper/Capsule-Endoscopy/` MDPI work and the PillCam-SPECTRA
flagship — exactly the GI/endoscopy L3 anchor that
`pwm-team/coordination/strategy/PWM_VS_PILLCAM_FLAGSHIPS.md`
Option B promises to cite from the PWM-flagship Application case
studies.

---

## What the schema does NOT cover (yet)

Three places where classification/segmentation principles need
extensions or deviations from the canonical L1-003 (CASSI) shape:

1. **Discrete output space.** The L1-003 W-tuple talks about
   `condition_number_kappa` of E. For categorical inverse, the
   condition number is replaced by **class-manifold separation Δ**
   (geometric margin between class-conditional distributions).
   `physics_fingerprint.problem_class` should be
   `categorical_inverse` rather than `linear_inverse`.

2. **Generalization-bound flavor of C.** Convergence rate `q` for
   inverse problems is asymptotic in mesh resolution. For
   classification/segmentation the analogue is a learning-theoretic
   bound `O(√(VC_dim/n_train))`. Both fit `e(h) ≤ C·h^α` if you
   read `h = 1/sqrt(n_train)` for supervised tasks.

3. **Conservation laws (P1).** Forward sensing of categorical
   labels doesn't conserve mass / energy / momentum the way
   physical imaging does. Use **softmax-simplex closure**
   (probabilities sum to 1) and **label permutation invariance**
   as the analogue conservation laws for the P1 test. Document
   this in the Principle's `physics_fingerprint`.

Future PWM revision: `pwm_overview2.md` should add a
"discrete-output extension" subsection that codifies these
deviations so each new classification/segmentation Principle
doesn't have to re-derive them.

---

## Filing checklist (for the contributor)

To get a classification or segmentation Principle accepted on
mainnet (per HANDOFF Step 1 + the Principle's S1-S4 + P1-P10 gates):

- [ ] L1 JSON in `pwm-team/pwm_product/genesis/l1/` (template above)
- [ ] L2 JSON in `pwm-team/pwm_product/genesis/l2/` (six-tuple per L2-003 schema)
- [ ] L3 JSON in `pwm-team/pwm_product/genesis/l3/` (with concrete dataset registry)
- [ ] Worked example doc: `papers/Proof-of-Solution/mine_example/<task>.md`
- [ ] Reference solver in `pwm-team/pwm_product/reference_solvers/<task>/`
- [ ] Quality test in `pwm-team/pwm_product/tests/test_<task>_quality.py`
- [ ] PSNR/IoU/etc target documented + reproducer that hits it on one sample
- [ ] Stake the Principle (USD-denominated PWM burn at L1 deploy time —
      see `pwm_overview1.md` § 10 Token Economics)

---

## Decision log

| Date | Decision |
|---|---|
| 2026-04-29 | Wrote this guide in response to Director's question on how to extend PWM L1/L2/L3 schema to classification + segmentation. Templates align with `L1-003.json` schema. Filed for future principle contributors and as scaffolding for `L1-SEG-GI-001` (PillCam-SPECTRA GI anchor). |
| _TBD_ | Director (or Claude Code on Director approval) writes `L1-CLS-001.json`, `L1-SEG-001.json`, `L1-SEG-GI-001.json` as committable JSON files under `genesis/l1/`. |
| _TBD_ | Reference solvers + quality tests + L3 datasets staged for each. |
| _TBD_ | Stake on mainnet post-deploy (Step 8 PASS). |
