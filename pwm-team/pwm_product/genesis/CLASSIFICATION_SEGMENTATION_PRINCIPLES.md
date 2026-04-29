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
    "uniqueness": "almost-surely-unique under class-manifold separability",
    "stability": "Bayes-optimal error rate bounded by class overlap; Lipschitz under bounded sensor noise",
    "regime": "K classes, noise σ, manifold separation Δ; identifiability when Δ ≥ c·σ for c depending on K"
  },
  "C": {
    "solver_class": "ERM with cross-entropy loss; deep CNN / ViT / linear-probe-on-foundation-model",
    "error_bound": "test_error ≤ Bayes_error + O(√(VC_dim/n_train))  (generalization)",
    "convergence_rate_q": 1.0
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
    "uniqueness": "unique up to label-symmetry; pixel-wise identifiability under bounded noise + class separability",
    "stability": "per-pixel Lipschitz; boundary regions sensitive to noise — well-posed in the interior of regions"
  },
  "C": {
    "solver_class": "FCN/U-Net/DeepLab/SAM-class with per-pixel cross-entropy + Dice loss",
    "error_bound": "mIoU ≥ Bayes-mIoU − O(√(VC_dim/n_train))",
    "convergence_rate_q": 1.0
  }
}
```

`n_c = 1` reflects the spatial-coupling cross-edge in the DAG: the
neighbor-aggregation primitive `K.spatial_aggregate` shares state
with itself across pixels (it's not a pure feed-forward chain).

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
