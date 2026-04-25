# CACTI — Complete Four-Layer Walkthrough

**Principle #27: Coded Aperture Compressive Temporal Imaging (CACTI)**
Domain: Compressive Imaging | Difficulty: Standard (delta=3) | Carrier: Photon
Verification: triple-verified — canonical reference principle; reviewed 2026-04-21 by physics/numerics/cross-domain verifiers; 3× ACCEPT after L1-004.json L_DAG fix (2.0→1.4); full review files at pwm-team/coordination/agent-*-verifier/reviews/027_cacti.md

---

## The Four-Layer Pipeline for CACTI

```
LAYER 1              LAYER 2              LAYER 3              LAYER 4
seeds → Valid(B)     Principle + S1-S4    spec.md + Principle   spec.md + Benchmark
designs the           designs              + S1-S4 builds &      + Principle + S1-S4
PRINCIPLE             spec.md              verifies BENCHMARK    verifies SOLUTION

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  LAYER 1        │    │  LAYER 2        │    │  LAYER 3        │    │  LAYER 4        │
│  seed→Principle │    │  Principle→spec │    │  spec→Benchmark │    │  Bench→Solution │
│                 │    │                 │    │                 │    │                 │
│  Domain expert  │    │  Task designer  │    │  Data engineer  │    │  SP + CP        │
│  writes seeds   │───>│  writes spec.md │───>│  builds dataset │───>│  solve task     │
│  about coded    │    │  for CACTI      │    │  + baselines    │    │  + earn PWM     │
│  temporal masks │    │  imaging tasks  │    │  + thresholds   │    │                 │
│  + snapshot     │    │                 │    │                 │    │  (PoSol reward) │
│  compression    │    │                 │    │                 │    │                 │
│  Reward: Reserve│    │  Reward: Reserve│    │  Reward: Reserve│    │  Reward: Ranked │
│  grant (DAO)    │    │  grant (DAO)    │    │  grant (DAO)    │    │  draw from      │
│  + upstream %   │    │  + upstream %   │    │  + upstream %   │    │  Pool_{k,j,b}   │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## Layer 1: Seeds → Principle (The Physics Foundation)

### What the domain expert writes (seeds)

The seeds are raw domain knowledge — the physics of coded aperture compressive temporal imaging expressed as a six-tuple:

```yaml
# ─── CACTI SEED (Layer 1 input) ───
# Written by: domain expert (high-speed video / compressive imaging researcher)
# Purpose: define the forward model and physics constraints

omega:
  description: "3D video datacube"
  spatial: [H, W]                    # spatial dimensions
  temporal: B                        # number of temporal frames per snapshot
  frame_rate: "B× higher than detector exposure rate"

E:
  forward_model: "y(i,j) = sum_{b=1}^{B} C_b(i,j) * x(i,j,b) + n"
  components:
    modulation: "C_b ∈ {0,1}^{H×W}, temporally varying binary coded masks"
    accumulation: "Detector integrates all masked frames into single exposure"
    detection: "Single 2D snapshot y ∈ R^{H×W}"
  DAG: "Modulate(M) → Accumulate(Σ) → Detect(D)"

B:
  nonnegativity: "x(i,j,b) >= 0 (radiance)"
  temporal_continuity: "Adjacent frames are correlated"
  sparsity: "Video cube is compressible in some spatio-temporal basis"

I:
  carrier: photon
  mask_type: binary_random
  compression_ratio: "B:1 (e.g. 8:1 for 8 frames)"
  noise_model: shot_noise

O:
  metrics: [per_frame_PSNR, SSIM, temporal_consistency, residual_norm]

epsilon:
  description: "Domain-level feasibility thresholds"
  e_img: "< 10^-4"
  PSNR_achievable: ">= 26 dB for any well-posed CACTI geometry"
```

### What S1-S4 discovers (the Principle)

Layer 1 runs Valid(B) = S1 ∧ S2 ∧ S3 ∧ S4 ∧ (δ ≥ δ_min) ∧ P1-P10 on the seeds. S1-S4 extracts the **Principle P = (E, G, W, C)**:

```
┌────────────────────────────────────────────────────────────────────────────┐
│  CACTI PRINCIPLE  P = (E, G, W, C)                                       │
│  Principle #27 in the PWM registry                                       │
│  sha256: <principle_hash>  (immutable once committed)                    │
├────────┬───────────────────────────────────────────────────────────────────┤
│   E    │ FORWARD MODEL                                                   │
│        │                                                                  │
│        │ y(i,j) = Σ_{b=1}^{B} C_b(i,j) · x(i,j,b) + n                 │
│        │                                                                  │
│        │ Physical chain:                                                  │
│        │   Video x(i,j,b) ──→ Modulate by mask C_b ──→ Accumulate      │
│        │   across B frames ──→ Detect on 2D sensor                      │
│        │                                                                  │
│        │ Inverse problem: recover x ∈ R^{H×W×B} from y ∈ R^{H×W}      │
│        │ Compression ratio: B : 1 (8:1 for 8 frames)                    │
├────────┼───────────────────────────────────────────────────────────────────┤
│   G    │ DAG DECOMPOSITION  G = (V, A)                                   │
│        │ Directed acyclic graph where:                                    │
│        │   V = nodes (hierarchical primitives from the 12-root basis)    │
│        │   A = arcs (data dependencies between primitives)               │
│        │ Made explicit by S1 (dimensional consistency across nodes).      │
│        │                                                                  │
│        │ Hierarchical primitive notation: root.sub.subsub                 │
│        │   Level 1 (root): WHAT computation — cross-domain comparable    │
│        │   Level 2 (sub):  WHAT structure — determines complexity class  │
│        │   Level 3 (subsub): WHAT variant — affects conditioning/flow    │
│        │   (See primitives.md for the full 149-leaf hierarchy)           │
│        │                                                                  │
│        │ CACTI forward DAG:                                               │
│        │                                                                  │
│        │   [S.temporal.coded] ──→ [∫.temporal]                           │
│        │         │                     │                                  │
│        │    coded mask             sum over b                            │
│        │    C(i,j,b)∈{0,1}       detector exposure                      │
│        │    selects sub-frames    collapses 3D->2D                       │
│        │                                                                  │
│        │ V = {S.temporal.coded, ∫.temporal}                              │
│        │ A = {S.temporal.coded -> ∫.temporal}                            │
│        │ |V| = 2,  |A| = 1,  n_c = 0 (no coupling)                     │
│        │                                                                  │
│        │ Node semantics (hierarchical decomposition):                     │
│        │   S.temporal.coded:                                              │
│        │     root S = sample (select/observe a subset of data)           │
│        │     sub  temporal = in the time dimension                       │
│        │     subsub coded = binary coded mask per sub-frame              │
│        │     C(i,j,b) ∈ {0,1}^{H×W×B} selects which sub-frame          │
│        │     photons pass through at each pixel (i,j)                    │
│        │                                                                  │
│        │   ∫.temporal:                                                   │
│        │     root ∫ = integrate / accumulate                             │
│        │     sub  temporal = sum over time dimension                     │
│        │     y(i,j) = Σ_b C(i,j,b) · x(i,j,b)  (collapse 3D->2D)     │
│        │                                                                  │
│        │ Why S (not L.diag) for CACTI:                                   │
│        │   CASSI has a physical prism shear -> needs L.diag + L.shear   │
│        │   CACTI has no shear — the mask C(i,j,b) is a 3D binary        │
│        │   tensor that independently gates each (pixel, sub-frame).      │
│        │   This is coded temporal sampling, not spatial modulation.       │
│        │   S1 gate checks: C(i,j,b) dimensions match x(i,j,b).         │
│        │                                                                  │
│        │ Cross-domain pattern: S.temporal appears in                      │
│        │   CACTI (#27), SCI, event cameras, compressed ultrafast         │
│        │   -> "temporal compressive sensing" family                       │
│        │   Compare: CASSI uses L.diag.binary + L.shear.spectral         │
│        │   (spectral modulation + physical dispersion)                    │
│        │                                                                  │
│        │ L_DAG = (|V|-1) + log10(κ/κ_0) + n_c = 1 + 1 + 0 = 2.0       │
│        │ Tier: standard (δ = 3)                                           │
├────────┼───────────────────────────────────────────────────────────────────┤
│   W    │ WELL-POSEDNESS CERTIFICATE                                      │
│        │                                                                  │
│        │ Existence: YES — underdetermined but regularizable               │
│        │   (H×W observations for H×W×B unknowns;                        │
│        │    compressive sensing theory guarantees recovery               │
│        │    when masks satisfy RIP-like conditions)                       │
│        │                                                                  │
│        │ Uniqueness: YES — under sparsity assumption                     │
│        │   (video cube compressible in spatio-temporal basis;            │
│        │    binary random masks with varying patterns satisfy RIP)       │
│        │                                                                  │
│        │ Stability: CONDITIONAL — depends on mask calibration quality    │
│        │   Mismatch: sub-pixel shift causes 10.4× residual ratio        │
│        │   EfficientSCI drops by 20.58 dB under mismatch                │
│        │                                                                  │
│        │ Mismatch model (8 parameters):                                   │
│        │   dx = horiz shift, dy = vert shift, θ = rotation               │
│        │   dt = clock offset, η = duty cycle                             │
│        │   γ = gain, o = offset, σ_n = noise std                        │
├────────┼───────────────────────────────────────────────────────────────────┤
│   C    │ ERROR-BOUNDING METHODOLOGY                                      │
│        │                                                                  │
│        │ e = per-frame PSNR (primary), SSIM (secondary)                  │
│        │ e_img < 10^-4                                                    │
│        │ q = 2.0  (O(h²) convergence for iterative solvers)            │
│        │ T = {residual_norm, error_bound, convergence_rate,              │
│        │      fitted_rate, K_resolutions, quality_Q}                     │
│        │                                                                  │
│        │ S3 convergence check: ||y - Φ·x̂||₂ must decrease               │
│        │   monotonically across iterations                               │
│        │ S4 certificate template:                                         │
│        │   r = {residual_norm, error_bound, ratio}                       │
│        │   c = {resolutions[], fitted_rate, theoretical_rate, K}         │
│        │   d = {consistent: bool}                                         │
│        │   Q = quality score ∈ [0.75, 1.0]                               │
│        │                                                                  │
│        │ Recovery ratio: 1.00 (GAP-TV, 60s calibration)                  │
│        │ GAP-TV achieves 100% autonomous recovery of oracle ceiling      │
└────────┴───────────────────────────────────────────────────────────────────┘
```

### What S1-S4 checks at Layer 1

| Gate | What it checks on the CACTI seeds | Result |
|------|-----------------------------------|--------|
| **S1** | Dimensions: masks C_b ∈ {0,1}^{H×W} match spatial grid; B masks for B frames; DAG nodes M→Σ→D are dimensionally consistent | PASS |
| **S2** | Well-posedness: binary random masks with temporally varying patterns satisfy RIP-like condition for video recovery; underdetermined system is regularizable | PASS |
| **S3** | Convergent solver exists: GAP-TV, PnP-FFDNet, EfficientSCI all converge for CACTI with known rate bounds | PASS |
| **S4** | Error is bounded: per-frame PSNR computable, e_img < 10^-4, convergence rate q=2.0 confirmed by multi-resolution analysis | PASS |

### Layer 1 reward

```
L1 Principle reward: Reserve grant from DAO vote when S4 gate passes.
No fixed formula — grant size is proportional to expected L4 activity.
Ongoing: 5% of every L4 minting draw + 5% of every L4 usage fee under this Principle.
```

### The Principle is now immutable

Once committed on-chain as `sha256:<principle_hash>`, the CACTI Principle **never changes**. All downstream spec.md files, benchmarks, and solutions reference this hash. Updating the physics means creating Principle v2 (a new hash), not modifying v1.

---

## Layer 2: Principle + S1-S4 → spec.md (Task Design)

### Who does this?

A **task designer** (can be the same domain expert or anyone else). They take the CACTI Principle and design specific, solvable tasks. Accepted specs earn a **Reserve grant** (DAO vote) on submission plus ongoing upstream royalties on all future L4 events.

### What the task designer writes

Each spec.md is a concrete instantiation of the Principle as a flat **six-tuple S = (Ω, E, B, I, O, ε) + principle_ref**. Items that live elsewhere:

| Moved to Principle | Moved to Benchmark (L3) |
|--------------------|------------------------|
| `difficulty` (L_DAG, δ, tier) | `expert_baseline`, `evaluator` |
| `primitives`, `carrier`, `modality` | quality scoring table |
| `quality_metrics` (C field) | per-solver metrics |

**Key insight: one spec, multiple I-benchmarks.** The CACTI measurement-only spec covers all mismatch severity levels — the solver input format never changes (measurement + mask only). Each mismatch severity is a separate I-benchmark tier within the same spec, not a separate spec. The oracle scenario (solver given exact mismatch parameters as input) requires a distinct spec because the input format changes.

**Two natural specs under this Principle:**

| Spec | Solver input | Ω dimensions | Center I-bench | Purpose |
|------|-------------|--------------|----------------|---------|
| #1 Mismatch-only | measurement + mask | H, W, B, noise + 8 mismatch dims | Nominal (all mismatch = 0, ρ=1) | Reconstruction under unknown calibration error |
| #2 Oracle-assisted | measurement + mask + true_phi | H, W, B, noise only (no mismatch dims) | H=256, B=8, noise=0.01 (ρ=1) — tiers scale by H/B/noise | Upper bound — solver knows exact calibration |

```
CACTI Principle (sha256:<principle_hash>)
    │
    ├──→ Spec #1: Mismatch-only (sha256:<spec1_hash>)
    │       ├──→ I-bench T1: Nominal (ρ=1)   ← center_ibenchmark
    │       ├──→ I-bench T2: Low mismatch (ρ=3)
    │       ├──→ I-bench T3: Moderate mismatch (ρ=5)
    │       ├──→ I-bench T4: Blind/severe (ρ=10)
    │       └──→ P-benchmark (ρ=50)
    │
    └──→ Spec #2: Oracle-assisted (sha256:<spec2_hash>)
            ├──→ I-bench T1: Small (H=64, B=4, ρ=1)
            ├──→ I-bench T2: Medium (H=256, B=8, ρ=3)
            ├──→ I-bench T3: Large (H=512, B=32, ρ=5)
            └──→ P-benchmark (ρ=50)
```

> **Ω in spec.md is always a range, not a fixed grid.** The spec declares the full parameter space the solver and P-benchmark must cover. The I-benchmark is pinned to a single `omega_tier` point within that range — that is the "center" the spec creator defines in `ibenchmark_range.center_ibenchmark`.

#### spec.md #1: Mismatch-Only (Canonical CACTI Spec)

```yaml
# cacti/cacti_mismatch_only.yaml
principle_ref: sha256:<principle_hash>

omega:
  H:               [32, 1024]
  W:               [32, 1024]
  B:               [4, 32]          # temporal frames (compression ratio)
  noise_level:     [0.001, 0.1]
  # Mismatch parameters (solver receives measurement + mask only)
  dx:              [0.0, 1.0]       # horizontal mask shift (px)
  dy:              [0.0, 1.0]       # vertical mask shift (px)
  theta:           [0.0, 0.15]      # rotation (deg)
  dt:              [0.0, 0.1]       # clock offset (fraction)
  eta:             [0.90, 1.0]      # duty cycle
  gamma:           [0.95, 1.05]     # gain
  offset:          [0.0, 0.01]      # offset
  sigma_n:         [0.5, 2.0]       # noise std

E:
  forward: "y(i,j) = Σ_b C_b(i,j) · x(i,j,b) + n"
  operator: cacti_forward_mismatch

B:
  nonnegativity: true
  temporal_continuity: true

I:
  strategy: zero_init

O: [per_frame_PSNR, SSIM, temporal_consistency]

epsilon_fn: "26.0 + 1.5 * log2(B / 8)"

input_format:
  measurement:   float32(H, W)
  mask:          bool(H, W, B)
output_format:
  video_cube:    float32(H, W, B)

ibenchmark_range:
  center_ibenchmark:
    rho: 1
    omega_tier:
      H:           256
      W:           256
      B:           8
      noise_level: 0.01
      dx: 0.0  dy: 0.0  theta: 0.0  dt: 0.0  eta: 1.0  gamma: 1.0  offset: 0.0  sigma_n: 1.0
    epsilon: 26.0
  tier_bounds:
    H:             [32, 1024]
    W:             [32, 1024]
    B:             [4, 32]
    noise_level:   [0.001, 0.1]
    dx:            [0.0, 1.0]
    dy:            [0.0, 1.0]
    theta:         [0.0, 0.15]
    dt:            [0.0, 0.1]
    eta:           [0.90, 1.0]
    gamma:         [0.95, 1.05]
    offset:        [0.0, 0.01]
    sigma_n:       [0.5, 2.0]
  proximity_threshold: 0.10

baselines:
  - GAP-TV          # L+N, classical baseline
  - PnP-FFDNet      # L+N, plug-and-play
  - EfficientSCI    # T+N, learned efficient solver
  - STFormer        # T+N, transformer-based
```

#### spec.md #2: Oracle-Assisted (Separate Spec — Different Input Format)

```yaml
# cacti/cacti_oracle_assisted.yaml
principle_ref: sha256:<principle_hash>

omega:
  H:               [32, 1024]
  W:               [32, 1024]
  B:               [4, 32]
  noise_level:     [0.001, 0.1]
  # No mismatch dims — mismatch is in true_phi input, not Ω

E:
  forward: "y = Phi_true * x + n  (Phi_true from true_phi input)"
  operator: cacti_forward_oracle

input_format:
  measurement:   float32(H, W)
  mask:          bool(H, W, B)
  true_phi:      dict   # {dx, dy, theta, dt, eta, gamma, offset, sigma_n}
output_format:
  video_cube:    float32(H, W, B)

epsilon_fn: "27.5 + 1.5 * log2(B / 8)"

ibenchmark_range:
  center_ibenchmark:
    rho: 1
    omega_tier:
      H: 256
      W: 256
      B: 8
      noise_level: 0.01
    epsilon: 27.5
  tier_bounds:
    H:           [32, 1024]
    B:           [4, 32]
    noise_level: [0.001, 0.1]
  proximity_threshold: 0.10

baselines:
  - GAP-TV-oracle
  - EfficientSCI-oracle
```

### What S1-S4 checks at Layer 2

Each spec.md is validated against the CACTI Principle:

| Gate | What it checks | CACTI spec result |
|------|----------------|-------------------|
| **S1** | spec's Ω range [H∈32–1024, B∈4–32] is consistent with Principle's spatial+temporal structure; mask dimensions match temporal frame count | PASS |
| **S2** | spec's parameter bounds (binary masks, B:1 compression) remain within the Principle's well-posedness regime; RIP conditions hold across Ω | PASS |
| **S3** | For all Ω in the declared range, at least one solver converges (GAP-TV at O(1/k)); epsilon_fn hardness rule satisfied | PASS |
| **S4** | epsilon_fn thresholds are feasible per the Principle's error bounds; expert baselines do not universally pass | PASS |

### Layer 2 reward

```
L2 spec.md reward: Reserve grant from DAO vote when S4 gate passes.
Requires d_spec ≥ 0.15 from all existing specs under this Principle.
Ongoing: 10% of every L4 minting draw + 10% of every L4 usage fee under this spec.
```

### The spec.md is now immutable

Once committed on-chain as `sha256:<spec_hash>`, the spec **never changes**. Miners know exactly what thresholds they must meet. No moving targets.

---

## Layer 3: spec.md + Principle + S1-S4 → Benchmark (Data + Baselines)

### Who does this?

A **data engineer** or **benchmark builder** (can be the task designer or someone else). They create the test data, run baseline solvers, and establish quality floors. Accepted benchmarks earn a **Reserve grant** (DAO vote) on submission plus ongoing upstream royalties.

### P-benchmark vs. I-benchmark

Every spec has exactly **one P-benchmark** and one or more **I-benchmarks**:

| Type | Ω coverage | δ weight | Quality threshold | Purpose |
|------|-----------|----------|-------------------|---------|
| **P-benchmark** | Full Ω range (parametric) | 50 (highest) | `epsilon_fn(Ω)` function | Tests generalization across entire parameter space |
| **I-benchmark** | Single Ω tier point | 1/3/5/10 | Fixed ε at that Ω | Tests performance at one specific difficulty level |

### What the benchmark builder creates

Layer 3 outputs a **complete, self-contained directory** — hash-committed and immutable once published. The 20 pre-built dev instances are ready to use directly. All 6 anti-overfitting mechanisms (M1-M6) are embedded as concrete files.

```
benchmark_cacti_mismatch_only_t1_nominal/     ← I-benchmark T1
│                                               omega_tier = {H:256, B:8, all mismatch=0}
│                                               (grid sizes come from omega_tier, not the spec)
├── manifest.yaml              # dataset identity + immutability hashes
│
├── instances/                  # 20 READY-TO-USE dev instances
│   ├── dev_001/
│   │   ├── input.npz          #   { "measurement": (256,256),
│   │   │                      #     "mask": (256,256,8) }
│   │   ├── ground_truth.npz   #   { "video_cube": (256,256,8) }
│   │   └── params.yaml        #   full Ω instance: H=256, B=8, dx=0, dy=0, ...
│   ├── dev_002/ … dev_020/
│
├── baselines/                  # expert solutions (M5: method diversity)
│   ├── gap_tv/
│   │   ├── solution.npz       #   reconstructed video cubes
│   │   ├── metrics.yaml       #   per-instance PSNR/SSIM
│   │   └── method.yaml        #   method_sig: "L+O" (iterative TV)
│   ├── pnp_ffdnet/
│   │   ├── metrics.yaml       #   mean_PSNR: 30.0, worst_PSNR: 28.2
│   │   └── method.yaml        #   method_sig: "L+N" (PnP deep denoiser)
│   └── efficientSCI/
│       ├── metrics.yaml       #   mean_PSNR: 33.0, worst_PSNR: 31.5
│       └── method.yaml        #   method_sig: "T+N" (transformer-based)
│
├── scoring/                    # deterministic evaluation (M3: worst-case)
│   ├── score.py               #   per-frame PSNR, SSIM
│   ├── thresholds.yaml        #   epsilon at this Ω tier point
│   └── worst_case.py          #   Q = f(worst_PSNR across scenes)
│
├── convergence/               # M2: convergence-based scoring
│   ├── check_convergence.py   #   verifies O(h²) rate across resolutions
│   └── resolutions.yaml       #   temporal: [4, 8, 16, 32]
│
├── generator/                  # M1: parameterized random instantiation
│   ├── generate.py            #   deterministic G(θ), seeded by hash
│   ├── params.yaml            #   scene diversity params
│   ├── instantiate.py         #   G(SHA256(h_sub||k)) at submission time
│   └── requirements.txt
│
├── adversarial/               # M4: community adversarial testing
│   ├── submit_adversarial.py
│   └── adversarial_log.yaml
│
├── gates/                      # M6: S1-S4 checks embedded
│   ├── check_s1.py            #   dims: (256,256,8) matches spec grid
│   ├── check_s2.py            #   RIP condition for binary masks
│   ├── check_s3.py            #   residual monotone decrease
│   ├── check_s4.py            #   worst_PSNR ≥ ε(this Ω tier)
│   └── run_all_gates.py
│
└── README.md

WHERE ARE THE 6 MECHANISMS?

M1  Random instantiation    generator/instantiate.py — G(SHA256(h_sub||k))
M2  Convergence scoring     convergence/check_convergence.py
M3  Worst-case eval         scoring/worst_case.py — Q = f(worst scene)
M4  Community adversarial   adversarial/submit_adversarial.py (T_k-rewarded)
M5  Method-sig diversity    baselines/*/method.yaml (L+O vs T+N earn novelty bonus)
M6  S1-S4 gate checks       gates/check_s1..s4.py
```

**Evaluation Tracks:**

| Track | Method | Purpose |
|-------|--------|---------|
| **Track A** | Stratified worst-case — Q = min over Ω strata | Certifies no catastrophic failure region |
| **Track B** | Uniform median — Q = median over sampled Ω | Typical-case performance benchmark |
| **Track C** | Degradation curve — Q(mismatch_severity) | Measures robustness as mismatch increases |

The **P-benchmark** uses all three tracks across the full Ω space. **I-benchmarks** use only Track A and Track B over their fixed dev/ set (20 scenes).

---

#### Track A — Stratified Worst-Case

Divide Ω into 3 strata by primary difficulty dimension (H×W for CACTI):

| Stratum | H×W range | Representative difficulty |
|---|---|---|
| S1 small  | H×W ≤ 128²        | Easy — fits in GPU memory trivially |
| S2 medium | 128² < H×W ≤ 512² | Standard — typical deployment size |
| S3 large  | H×W > 512²        | Hard — memory pressure, long runtime (up to 1024²) |

**Procedure (P-benchmark):**
1. For each stratum, draw N_s = 5 random Ω points within that stratum (randomness from M1 seed)
2. Run solver on all 5 instances → 5 PSNR scores
3. Take the **worst** score from those 5
4. Worst score must pass `epsilon_fn(Ω_centroid_s)` — threshold at stratum centre
5. **All 3 strata must independently pass** — failing S3 fails Track A even if S1–S2 pass

**For I-benchmarks (fixed dev/ set):**
Track A = worst score across all 20 fixed dev scenes ≥ benchmark's fixed ε.

Pass condition: `min_i(PSNR_i) / ε ≥ 1.0`

---

#### Track B — Uniform Median

**Procedure (P-benchmark):**
1. Sample N = 50 Ω points uniformly from the full declared Ω space (no stratification)
2. Run solver on all 50 instances → 50 PSNR scores
3. Take the **median** (25th value after sorting)
4. Compute Ω_median = geometric centroid of the 50 sampled parameter vectors
5. Median score must pass `epsilon_fn(Ω_median)`

**For I-benchmarks:**
Track B = median score across all 20 fixed dev scenes ≥ benchmark's fixed ε.

Pass condition: `median_i(PSNR_i) / ε ≥ 1.0`

Why both tracks: a solver can pass Track B (good median) but fail Track A (catastrophic at large B); or pass Track A (adequate worst-case per stratum) but fail Track B (mediocre everywhere). Both must pass for full certification.

---

#### Track C — Mismatch Degradation Curve (mismatch-only spec only)

Sweeps mismatch severity φ ∈ [0, 1] where φ=0 is calibrated and φ=1 is the maximum declared mismatch bounds. Tests how gracefully quality degrades as calibration error increases.

**CACTI mismatch sweep (5 points):**

| φ | dx | dy | theta | dt | eta | gamma |
|---|---|---|---|---|---|---|
| 0.00 | 0.0 | 0.0 | 0.00° | 0.00 | 1.00 | 1.00 |
| 0.25 | 0.25 | 0.25 | 0.04° | 0.025 | 0.975 | 1.013 |
| 0.50 | 0.50 | 0.50 | 0.08° | 0.05 | 0.95 | 1.025 |
| 0.75 | 0.75 | 0.75 | 0.11° | 0.075 | 0.925 | 1.038 |
| 1.00 | 1.00 | 1.00 | 0.15° | 0.10 | 0.90 | 1.05 |

At each φ point, 10 scenes are evaluated and the median PSNR recorded. The degradation curve Q(φ) is then normalised:

```
Q_norm(φ) = PSNR(φ) / epsilon_fn(Ω at φ)

degradation_score = (1/4) × Σ_{i=1}^{4} [Q_norm(φ_i) + Q_norm(φ_{i+1})] / 2   (trapezoid AUC)
```

A flat curve (degradation_score ≈ 1.0) means the solver is mismatch-robust. A steep drop (degradation_score < 0.5) means it relies heavily on calibration.

**Track C is only active when `difficulty_dims` is declared in the spec.** For the oracle-assisted spec, Track C is omitted (mismatch is an input, not an Ω dimension).

---

#### Combined Q_p Score

```
Without Track C:   Q_p = 0.40 × coverage + 0.40 × margin + 0.20 × stratum_pass_frac
With Track C:      Q_p = 0.35 × coverage + 0.35 × margin + 0.15 × stratum_pass_frac
                        + 0.15 × degradation_score
```

| Term | Meaning |
|---|---|
| `coverage` | Fraction of sampled Ω points where PSNR ≥ ε |
| `margin` | Mean (PSNR/ε − 1) over passing instances |
| `stratum_pass_frac` | Fraction of strata where worst instance passes (Track A) |
| `degradation_score` | AUC of normalised Q(φ) curve (Track C) |

#### manifest.yaml

```yaml
# benchmark_cacti_mismatch_only_t1_nominal/manifest.yaml

benchmark_id:    "cacti_mismatch_only_t1_nominal_v1"
type:            "I-benchmark"
spec_ref:        "sha256:<spec1_hash>"       # mismatch-only spec
principle_ref:   "sha256:<principle_hash>"
# omega_tier: the single fixed Ω point this I-benchmark tests
omega_tier:
  H:               256
  W:               256
  B:               8
  noise_level:     0.01
  dx:              0.0
  dy:              0.0
  theta:           0.0
  dt:              0.0
  eta:             1.0
  gamma:           1.0
  offset:          0.0
  sigma_n:         1.0
rho:             1                           # ρ=1 pool weight for nominal tier
epsilon:         26.0                        # epsilon_fn evaluated at this omega_tier
dataset_hash:    "sha256:<dataset_hash>"
generator_hash:  "sha256:<gen_hash>"
created:         "2026-04-17T00:00:00Z"
num_dev_instances: 20
num_baselines:     4
data_format:      "npz"
mechanisms:       [M1, M2, M3, M4, M5, M6]
```

#### scoring/thresholds.yaml (from epsilon_fn at this Ω tier)

```yaml
# epsilon_fn evaluated at T1 nominal Ω point (H=256, B=8, no mismatch)
PSNR_min:   26.0     # per-frame mean PSNR ≥ 26 dB
SSIM_min:   0.85
residual_max: 0.05   # ||y - Φx̂|| / ||y||

quality_scoring:
  metric: worst_psnr           # M3: worst scene determines Q
  thresholds:
    - {min: 33.0, Q: 1.00}
    - {min: 30.0, Q: 0.90}
    - {min: 27.0, Q: 0.80}
    - {min: 26.0, Q: 0.75}    # floor — always ≥ 0.75
```

**T3 Moderate mismatch I-benchmark** thresholds (same spec, different Ω tier):

```yaml
# epsilon_fn evaluated at T3 Ω point (dx=0.5, dy=0.3, theta=0.1°, dt=0.05, eta=0.95)
PSNR_min:   20.0     # lower threshold — mismatch degrades quality
SSIM_min:   0.50
residual_max: 0.10   # higher tolerance for mismatch scenario
```

### What S1-S4 checks at Layer 3

The benchmark is validated against **both** the spec.md and the Principle:

| Gate | What it checks | CACTI benchmark result |
|------|----------------|------------------------|
| **S1** | `instances/dev_*/input.npz` shape (256,256) and `ground_truth.npz` shape (256,256,8) match spec's Ω dimensions; 8 masks of size (256,256) match temporal frame count per spec | PASS |
| **S2** | Problem defined by this data + Principle has bounded inverse; binary masks at 8:1 compression satisfy RIP conditions per the Principle (`gates/check_s2.py`) | PASS |
| **S3** | GAP-TV residual decreases monotonically across iterations; `convergence/check_convergence.py` confirms O(h²) rate at 4 resolutions (M2) | PASS |
| **S4** | GAP-TV **worst_PSNR = 26.01 dB ≥ ε=26.0 dB** (M3: worst-case over 20 dev scenes); at least one solver clears ε, confirming task is feasible per Principle's error bounds | PASS |

### Layer 3 reward

```
L3 benchmark reward: Reserve grant from DAO vote when S4 gate passes.
Ongoing: 15% of every L4 minting draw + 15% of every L4 usage fee under this benchmark.
```

### The benchmark is now immutable

Once committed as `sha256:<bench_hash>`, the dataset, baselines, and scoring table are fixed. Miners compete against frozen targets.

---

## I-Benchmark Tiers

```
CACTI Principle
    │
    ├──→ Spec #1: Mismatch-only (sha256:<spec1_hash>)
    │       ├──→ I-bench T1: Nominal (ρ=1)   ← center_ibenchmark
    │       ├──→ I-bench T2: Low mismatch (ρ=3)
    │       ├──→ I-bench T3: Moderate mismatch (ρ=5)
    │       ├──→ I-bench T4: Blind/severe (ρ=10)
    │       └──→ P-benchmark (ρ=50)
    │
    └──→ Spec #2: Oracle-assisted (sha256:<spec2_hash>)
            ├──→ I-bench T1: Small (H=64, B=4, ρ=1)
            ├──→ I-bench T2: Medium (H=256, B=8, ρ=3)
            ├──→ I-bench T3: Large (H=512, B=32, ρ=5)
            └──→ P-benchmark (ρ=50)
```

**CACTI I-benchmark tiers — mismatch-only spec:**

| Tier | omega_tier | mismatch severity | ρ | ε |
|---|---|---|---|---|
| T1 (Nominal) | H=256, B=8, all mismatch=0 | None | 1 | 26.0 dB |
| T2 (Low) | dx=0.3, dy=0.2, dt=0.02, eta=0.98 | Small drift | 3 | 23.0 dB |
| T3 (Moderate) | dx=0.5, dy=0.3, theta=0.1°, dt=0.05, eta=0.95, gamma=1.02 | Typical hardware | 5 | 20.0 dB |
| T4 (Blind) | dx=1.0, dy=1.0, theta=0.15°, dt=0.1, eta=0.90, gamma=1.05, sigma_n=2.0 | Large, unknown | 10 | 17.0 dB |

Dataset for T4: simulation_6scenes (kobe, traffic, runner, drop, crash, aerial) with synthetic mismatch at T4 parameters.

**CACTI I-benchmark tiers — oracle-assisted spec** (Ω = system params only; mismatch is in true_phi input):

| Tier | omega_tier (system params only) | ρ | ε |
|------|---------------------------------|----|---|
| T1 | H=64, B=4, noise=0.01 | 1 | 27.5 dB |
| T2 | H=256, B=8, noise=0.01 | 3 | 29.0 dB |
| T3 | H=512, B=32, noise=0.05 | 5 | 27.5 dB |

**I-benchmark distance gate:** A new I-benchmark whose `omega_tier` point is within τ=0.10 of any existing I-benchmark in every Ω dimension is rejected as a near-duplicate. The proximity is measured as a fraction of each dimension's declared `tier_bounds` range.

---

## P-benchmark (Highest Reward Overall, ρ=50)

Tests generalization across the **full** declared Ω space. The solver must work across all combinations of H∈[32,1024], W∈[32,1024], B∈[4,32], noise_level∈[0.001,0.1], and mismatch dims within their declared bounds.

```
P-benchmark uses epsilon_fn(Ω) as threshold — not a fixed number.
Quality is evaluated across all three Tracks (see Track A/B/C details above):
  Track A: 3 strata by H×W; worst of 5 instances per stratum must pass ε
  Track B: median of 50 uniform Ω samples must pass ε at Ω_median
  Track C: mismatch degradation curve; φ swept 0→1 across 5 points
```

**Source dataset:** DAVIS_2017 (90 sequences, ~480×854 native, CC-BY-NC). Stitching rule mirrors CASSI's ICVL approach:

| H×W target | Construction |
|---|---|
| H×W ≤ 480×480 | Single DAVIS sequence — center crop to target H×W |
| H×W > 480 in either dim (up to 1024) | **2×2 hard stitch** of 4 DAVIS sequences (no blending); seam_map provided in true_phi |

Stitch is physically motivated: real CACTI deployments tile sensors to cover wider fields of view. For H×W ≤ 512² the crop always fits within a single 480×854 frame; the stitch threshold is ~480 px per side.

I-benchmarks T1–T4 continue to use `SCI6_simulation` (6 scenes: kobe, traffic, runner, drop, crash, aerial; 256×256×8) — the standard in the SCI literature, evaluated at fixed omega_tier points.

**Full Ω range:** H∈[32,1024], W∈[32,1024], B∈[4,32], all 8 mismatch dims within their declared bounds.

**Track A strata for CACTI:**

| Stratum | H×W range | Dataset construction |
|---|---|---|
| S1 small | H×W ≤ 128² | Single DAVIS crop |
| S2 medium | 128² < H×W ≤ 512² | Single DAVIS crop (fits within 480×480) |
| S3 large | H×W > 512² | 2×2 hard stitch of 4 DAVIS sequences |

ρ=50 makes the P-benchmark pool weight 50× higher than the T1 nominal I-benchmark. A solver that passes the P-benchmark earns substantially more than all I-benchmarks combined.

---

## Layer 4: spec.md + Benchmark + Principle + S1-S4 → Solution (Mining for PWM)

### Who does this?

**Two distinct roles** — a **Solution Provider (SP)** who creates the algorithm and a **Compute Provider (CP)** who executes it. They may be the same person or different people.

**Solution Provider (SP):**
1. Develops the solver algorithm locally and **proves it works** — runs against benchmark dev instances, confirms S1-S4 gates pass and Q ≥ 0.75
2. Uploads the solution binary + model weights to IPFS
3. Declares the **compute manifest** — specifies the hardware requirements CPs must meet to run this solution correctly:
   ```yaml
   compute_manifest:
     min_vram_gb:      8          # minimum GPU VRAM
     recommended_vram_gb: 16
     cpu_only:         false      # whether GPU is required
     min_ram_gb:       16
     expected_runtime_s: 120      # per benchmark instance at center Ω
     expected_runtime_p_bench_s: 2400   # full P-benchmark run
     precision:        float32
     framework:        pytorch    # runtime dependency
     entry_point:      solve.py
     ipfs_cid:         "Qm..."    # hash-locked binary
   ```
4. Sets share ratio `p` (SP's fraction of the solver 55%) — determined by how compute-intensive the solution is
5. Earns `p × 55%` of every L4 event **passively** — no action needed when jobs arrive
6. Retains sole authority to upgrade or replace the solution
7. Owns the Q quality score; appears on the leaderboard

The SP does **not** need GPU hardware at submission time — the compute manifest tells CPs what they need. The protocol matches jobs to CPs whose registered hardware meets the manifest requirements.

**Compute Provider (CP):**
- Registers hardware capabilities (GPU model, VRAM, throughput, region)
- Polls the on-chain job queue; executes SP's exact binary (hash-locked to IPFS CID) on instances that match its hardware against the SP's compute manifest
- Competes with other CPs in a **commit-then-reveal race** for each benchmark job (both I-benchmark and P-benchmark verification runs)
- Earns `(1 − p) × 55%` of each L4 event for jobs they complete
- Applies to **both** benchmark minting draws and user usage fees

**How the protocol calculates PWM distribution** — the SP does not calculate or claim manually. On certificate finalisation the smart contract splits automatically:

```
Per L4 event (minting draw or usage fee) of amount R:
  SP  ←  p × 55% × R          (passive; no action needed)
  CP  ←  (1−p) × 55% × R      (whoever executed the job)
  L3  ←  15% × R
  L2  ←  10% × R
  L1  ←  5% × R
  T_k ←  15% × R              (per-principle treasury)
```

**Share ratio guidance** — the SP sets `p` once at registration based on compute weight:

| Solver type | Typical p | SP | CP | Example compute_manifest |
|-------------|-----------|----|----|--------------------------|
| CPU-only (SP = CP) | 1.0 | 100% | 0% | `cpu_only: true, expected_runtime_s: 5` |
| Lightweight iterative | 0.80 | 80% | 20% | `min_vram_gb: 0, expected_runtime_s: 60` |
| Single GPU | 0.40 | 40% | 60% | `min_vram_gb: 8, expected_runtime_s: 120` |
| GPU cluster | 0.20 | 20% | 80% | `min_vram_gb: 40, expected_runtime_s: 600` |

### Step-by-step mining

#### Step 1: Choose your task

```bash
pwm-node benchmarks | grep cacti
```

Output:
```
# Spec #1: Mismatch-only (measurement + mask input)
cacti   mismatch_only_t1_nominal     ρ=1    mineable   (I-benchmark, ε=26.0 dB)
cacti   mismatch_only_t2_low         ρ=3    mineable   (I-benchmark, ε=23.0 dB)
cacti   mismatch_only_t3_moderate    ρ=5    mineable   (I-benchmark, ε=20.0 dB)
cacti   mismatch_only_t4_blind       ρ=10   mineable   (I-benchmark, ε=17.0 dB)
cacti   mismatch_only_p_benchmark    ρ=50   mineable   (P-benchmark, ε=epsilon_fn(Ω))

# Spec #2: Oracle-assisted (measurement + mask + true_phi input)
# Ω varies H/B/noise only — no mismatch dims in Ω
cacti   oracle_t1_h64_b4             ρ=1    mineable   (I-benchmark, ε=27.5 dB)
cacti   oracle_t2_h256_b8            ρ=3    mineable   (I-benchmark, ε=29.0 dB)
cacti   oracle_t3_h512_b32           ρ=5    mineable   (I-benchmark, ε=27.5 dB)
cacti   oracle_p_benchmark           ρ=50   mineable   (P-benchmark, ε=epsilon_fn(Ω))
```

#### Step 2: Pre-check gates (free, no compute)

```bash
pwm-node verify cacti/cacti_t1_nominal.yaml
```

Checks S1-S2 against the Principle before you spend GPU time.

#### Step 3: Solve

```bash
pwm-node mine cacti/cacti_t1_nominal.yaml
```

Under the hood:
1. Downloads benchmark data (6 videos + 8 masks per frame) from DA layer
2. Runs your solver on all 6 videos
3. Produces 6 reconstructed video cubes (256×256×8 each)
4. Computes per-frame PSNR, SSIM for each video

**You choose the solver.** The spec defines the problem, not the algorithm:

| Solver | Expected PSNR | GPU Time | Quality Q | Notes |
|--------|---------------|----------|-----------|-------|
| GAP-TV | ~26.75 dB | ~2 min/video | 0.75 | Classical baseline |
| PnP-FFDNet | ~30+ dB | ~5 min/video | 0.90 | Plug-and-play |
| EfficientSCI | ~33+ dB | ~1 min/video | 1.00 | Learned efficient solver |
| STFormer | ~35+ dB | ~3 min/video | 1.00 | Transformer-based |

Better solver → higher PSNR → higher Q → more PWM (via larger ranked draw fraction).

#### Step 4: Local verification (S1-S4 on the solution)

Your local Judge Agent checks the solution against **all three upstream artifacts**:

```
Solution verified from TWO directions simultaneously:

Direction 1: BENCHMARK VERIFICATION
  Compare PSNR, SSIM against benchmark baselines
  → Determines quality score Q ∈ [0.75, 1.0]
  → "How good is the solution?"

Direction 2: PRINCIPLE + S1-S4 VERIFICATION
  Check solution against CACTI forward model directly
  S1: output dimensions [256,256,8] match spec grid
  S2: solver used method consistent with well-posedness
  S3: residual ||y - Φ·x̂||₂ decreased monotonically
  S4: PSNR ≥ ε(this Ω tier), SSIM ≥ 0.85, residual < error_bound
  → Determines pass/fail
  → "Is the solution mathematically correct?"

BOTH must pass → S4 Certificate issued → PWM minted
```

| Gate | What it checks on the CACTI solution | Expected |
|------|--------------------------------------|----------|
| **S1** | Output shape [256,256,8] matches spec; masks and compression ratio consistent with Principle | PASS |
| **S2** | Solver method is consistent with Principle's well-posedness (used regularization for underdetermined system) | PASS |
| **S3** | Solver residual ||y - Phi * x_hat||_2 decreases monotonically; convergence rate matches Principle's q=2.0 | PASS |
| **S4** | Worst-case PSNR ≥ ε across all scenes, SSIM ≥ 0.85; residual below error bound | PASS |

#### Step 5: Certificate assembly and automatic reward routing

```json
{
  "cert_hash": "sha256:...",
  "h_s": "sha256:<spec1_hash>",
  "h_b": "sha256:<bench1_hash>",
  "h_p": "sha256:<principle_hash>",
  "h_x": "sha256:... (reconstructed video cubes hash)",
  "r": {
    "residual_norm": 0.031,
    "error_bound": 0.05,
    "ratio": 0.62
  },
  "c": {
    "resolutions": [[128, 0.045], [256, 0.012], [512, 0.003]],
    "fitted_rate": 1.95,
    "theoretical_rate": 2.0,
    "K": 3
  },
  "d": {"consistent": true},
  "Q": 0.92,
  "gate_verdicts": {"S1": "pass", "S2": "pass", "S3": "pass", "S4": "pass"},
  "difficulty": {"tier": "standard", "delta": 3},
  "sp_wallet": "...",
  "share_ratio_p": 0.40,
  "sigma": "ed25519:..."
}
```

The certificate contains **three upstream hashes** — proving it was verified against the immutable Principle, spec, and benchmark:

```
cert references:
  h_p → Principle  sha256:<principle_hash>    (Layer 1, immutable)
  h_s → spec.md    sha256:<spec1_hash>        (Layer 2, immutable)
  h_b → Benchmark  sha256:<bench1_hash>       (Layer 3, immutable)
  h_x → Solution   sha256:<solution_hash>     (Layer 4, this submission)
```

#### Step 6: Challenge period

- **7-day window** for standard-difficulty tasks
- Any verifier can download all artifacts by hash and re-verify independently
- If nobody challenges, the certificate finalizes

#### Step 7: Reward settlement

**Each benchmark has its own independent pool and rank list.** The P-benchmark and every I-benchmark (T1, T2, T3, T4) each maintain a separate pool. Rank 1 on the P-benchmark is the first solution to pass that P-benchmark; Rank 1 on I-benchmark T4 is the first solution to pass T4. A solver can hold Rank 1 on multiple benchmarks simultaneously and draws from each independently.

**Subscript notation:**

| Subscript | Meaning | CACTI example |
|---|---|---|
| `k` | Principle index | k=27 (CACTI Principle) |
| `j` | Spec index within Principle k | j=1 (mismatch-only), j=2 (oracle-assisted) |
| `b` | Benchmark index within Spec j | b=P (P-benchmark), b=T1…T4 (I-benchmarks) |

The pool for one benchmark is `Pool_{k,j,b} = A_{k,j,b} + B_{k,j,b} + T_{k,j,b}`, computed in three stages:

```
A_k and T_k are only allocated to PROMOTED artifacts.
Before promotion: Pool_{k,j,b} = B_{k,j,b} only.
After promotion:  Pool_{k,j,b} = A_{k,j,b} + B_{k,j,b} + T_{k,j,b}.

Stage 1 — Principle allocation (k level):   uses δ_k (Principle difficulty from L_DAG)
  A_k        = (M_pool − M(t)) × w_k / Σ_k*(w_k)          (* promoted Principles only)
  w_k        = δ_k × max(activity_k, 1)
               δ_k = Principle difficulty tier (CACTI: δ=3); fixed at L1 from L_DAG
               activity_k = L4 solutions under Principle k in last 90 days
  T_k        = accumulated 15% of ALL L4 events under promoted Principle k

Stage 2 — Spec allocation (j level, within promoted Principle k):   uses ρ
  A_{k,j}    = A_k × Σ_b* ρ_{j,b} / Σ_{j'*,b'*} ρ_{j',b'}   (* promoted Specs/Benchmarks only)
  T_{k,j}    = T_k × Σ_b* ρ_{j,b} / Σ_{j'*,b'*} ρ_{j',b'}

Stage 3 — Benchmark allocation (b level, within promoted Spec j):   uses ρ
  A_{k,j,b}  = A_{k,j} × ρ_{j,b} / Σ_b* ρ_{j,b}              (* promoted Benchmarks only)
  T_{k,j,b}  = T_{k,j} × ρ_{j,b} / Σ_b* ρ_{j,b}
               ρ_{j,b} = pool weight declared for benchmark b; P-benchmark ρ=50, I-benchmark ρ∈{1,3,5,10}

Bounty term B_{k,j,b}:   available at all stages regardless of promotion status
  B_k^P       = bounty staked at Principle level (flows to all promoted benchmarks under k by ρ)
  B_{k,j}^S   = bounty staked at Spec j level   (flows to all promoted benchmarks under j by ρ)
  B_{k,j,b}^D = bounty staked directly at Benchmark b (goes entirely to that benchmark)

  B_{k,j,b}  = B_{k,j,b}^D
              + B_{k,j}^S × ρ_{j,b} / Σ_b* ρ_{j,b}
              + B_k^P      × ρ_{j,b} / Σ_{j'*,b'*} ρ_{j',b'}
```

> **δ vs ρ in pool allocation:** Stage 1 uses `δ_k` to compare Principles globally (physics difficulty, set at L1). Stages 2–3 use `ρ` to split a Principle's budget among its benchmarks (pool weight, declared at L3). Both use the same numeric scale {1,3,5,10,50} but at different hierarchy levels.

**CACTI example** (mismatch-only spec, j=1; total ρ = 50+10+5+3+1 = 69):

| Benchmark b | ρ | Pool share within spec (ρ / 69) |
|---|---|---|
| P-benchmark | 50 | **72.5%** |
| T4 (blind calib.) | 10 | 14.5% |
| T3 (moderate) | 5 | 7.2% |
| T2 (low) | 3 | 4.3% |
| T1 (nominal) | 1 | 1.4% |

**Ranked draws:** Rank 10 is the last paid rank. Solutions ranked 11+ receive no draw; the remaining ~52% of the epoch pool rolls over to the next epoch.

| Rank | Draw |
|------|------|
| Rank 1 (first solution) | 40% of current pool |
| Rank 2 | 5% of remaining |
| Rank 3 | 2% of remaining |
| Rank 4–10 | 1% of remaining (each) |
| Rank 11+ | No draw |

**Example** (Pool_{k,j,b} = 500 PWM for one benchmark, p=0.40, so AC=40%×55%, CP=60%×55%):

| Rank | Draw (PWM) | AC (p×55%) | CP ((1-p)×55%) | L3 (15%) | L2 (10%) | L1 (5%) | T_k (15%) |
|------|-----------|-----------|---------------|----------|----------|---------|-----------|
| 1 | 200.00 | 44.00 | 66.00 | 30.00 | 20.00 | 10.00 | 30.00 |
| 2 | 15.00 | 3.30 | 4.95 | 2.25 | 1.50 | 0.75 | 2.25 |
| 3 | 5.70 | 1.25 | 1.88 | 0.86 | 0.57 | 0.29 | 0.86 |
| 4 | 2.79 | 0.61 | 0.92 | 0.42 | 0.28 | 0.14 | 0.42 |
| 5–10 | ~2.65 each | ~0.58 | ~0.87 | ~0.40 | ~0.27 | ~0.13 | ~0.40 |
| **Rollover** | **~260** | — | — | — | — | — | — |

**Upstream royalty split (same for minting draws and usage fees):**

| Recipient | Share | Notes |
|-----------|-------|-------|
| SP (Algorithm Creator) | p × 55% | Earns passively; sets p at registration |
| CP (Compute Provider) | (1−p) × 55% | Earns by running jobs; distinct for mining vs. usage |
| L3 Benchmark creator | 15% | Upstream royalty |
| L2 Spec author | 10% | Upstream royalty |
| L1 Principle creator | 5% | Upstream royalty |
| T_{k,j,b} treasury | 15% | Self-funds adversarial bounties + validator fees |

Anti-spam: after ~50 solutions, per-solution reward falls below gas cost.

### Cross-benchmark claims (P-benchmark bonus)

Within 7 days of passing the P-benchmark, the SP may optionally claim:
1. Any I-benchmark of the same spec (auto-verified; pass → one ranked draw)
2. I-benchmarks of other specs under the same Principle

Cross-claims are optional — failure has no penalty.

---

## Complete Hash Chain (Immutability Across All Four Layers)

```
Layer 1 ──→ Principle sha256:<principle_hash>      FIXED
               │
Layer 2 ──→ spec.md sha256:<spec1_hash>            FIXED
               │   contains: principle_ref: sha256:<principle_hash>
               │
Layer 3 ──→ Benchmark sha256:<bench1_hash>         FIXED
               │   contains: spec_ref: sha256:<spec1_hash>
               │             principle_ref: sha256:<principle_hash>
               │
Layer 4 ──→ Certificate sha256:<cert_hash>         SUBMITTED
                   contains: h_s: sha256:<spec1_hash>
                             h_b: sha256:<bench1_hash>
                             h_p: sha256:<principle_hash>
                             h_x: sha256:<solution_hash>

Tampering with ANY artifact changes its hash → breaks the chain.
Every verifier can independently reconstruct this chain.
```

---

## I-Benchmark Tiers — Detailed Mining Guide

Each I-benchmark is a frozen dataset at a single `omega_tier` point. The spec declares the Ω range; the I-benchmark pins one point within it.

### Mismatch-Only Spec: Tier T1 (Nominal — Start Here)

The calibrated mask matches reality. The simplest CACTI task.

| Property | Value |
|----------|-------|
| omega_tier | H=256, B=8, all mismatch dims = 0 |
| Operator | Calibrated masks (Φ = Φ_true) |
| Expert baseline | GAP-TV: PSNR = 26.75 dB, SSIM = 0.854 |
| ε | 26.0 dB (epsilon_fn at this Ω point) |
| ρ | 1 |

```bash
pwm-node mine cacti/cacti_mismatch_only_t1_nominal.yaml
```

### Mismatch-Only Spec: Tiers T2 / T3 (Low / Moderate Mismatch)

Same measurement-only input format — only the `omega_tier` point changes.

| Property | T2 (Low) | T3 (Moderate) |
|----------|----------|---------------|
| omega_tier | dx=0.3, dy=0.2, dt=0.02, eta=0.98 | dx=0.5, dy=0.3, theta=0.1°, dt=0.05, eta=0.95, gamma=1.02 |
| Expert baseline PSNR | ~21 dB | ~18 dB |
| ε | 23.0 dB | 20.0 dB |
| ρ | 3 | 5 |

**Warning (T3):** GAP-TV drops significantly under typical hardware mismatch. A mismatch-aware solver is recommended.

### Mismatch-Only Spec: Tier T4 (Blind Calibration — Highest I-benchmark ρ)

Solver must estimate mismatch parameters from data, then reconstruct. Most practically valuable.

| Property | Value |
|----------|-------|
| omega_tier | dx=1.0, dy=1.0, theta=0.15°, dt=0.1, eta=0.90, gamma=1.05, sigma_n=2.0 |
| Input | Measurement + mask only (no mismatch params — solver must self-calibrate) |
| ε | 17.0 dB |
| ρ | 10 |
| Dataset | simulation_6scenes (kobe, traffic, runner, drop, crash, aerial) with synthetic mismatch at T4 parameters; fixed 6-scene eval set |

**CACTI opportunity:** GAP-TV recovers 100% of the oracle gap in just 60 seconds of grid search calibration. The blind-calibrated result (26.99 dB) actually **exceeds** the ideal result (26.75 dB), demonstrating that calibration can improve upon the nominal operator.

### Oracle-Assisted Spec: I-benchmark Tiers

The center I-benchmark for the oracle spec is at small system params — where oracle information establishes the baseline upper bound.

| Tier | omega_tier | ρ | ε |
|------|-----------|---|---|
| T1 | H=64, W=64, B=4, noise=0.01 | 1 | 27.5 dB |
| T2 | H=256, W=256, B=8, noise=0.01 | 3 | 29.0 dB |
| T3 | H=512, W=512, B=32, noise=0.05 | 5 | 27.5 dB |

---

## Complete Reward Summary (All Four Layers for CACTI)

```
┌─────────┬──────────────────────────────┬──────────────────────────────────────────────┐
│ Layer   │ One-time creation reward     │ Ongoing upstream royalties                   │
├─────────┼──────────────────────────────┼──────────────────────────────────────────────┤
│ L1      │ Reserve grant (DAO vote)     │ 5% of every L4 minting draw                 │
│Principle│ when S4 gate passes          │ 5% of every L4 usage fee                    │
│         │ No fixed formula             │ → If 1,000 solutions at 500 PWM each:       │
│         │                              │   25,000 PWM passively                      │
├─────────┼──────────────────────────────┼──────────────────────────────────────────────┤
│ L2      │ Reserve grant (DAO vote)     │ 10% of every L4 minting draw                │
│ spec.md │ when S4 gate passes          │ 10% of every L4 usage fee                   │
│         │ Requires d_spec ≥ 0.15       │ → If 250 solutions at 500 PWM each:         │
│         │                              │   12,500 PWM per spec                       │
├─────────┼──────────────────────────────┼──────────────────────────────────────────────┤
│ L3      │ Reserve grant (DAO vote)     │ 15% of every L4 minting draw                │
│Benchmark│ when S4 gate passes          │ 15% of every L4 usage fee                   │
│         │ Requires d_ibench ≥ 0.10     │ → If 250 solutions at 500 PWM each:         │
│         │                              │   18,750 PWM per benchmark                  │
├─────────┼──────────────────────────────┼──────────────────────────────────────────────┤
│ L4      │ N/A (no one-time grant)      │ Ranked draw from Pool_{k,j,b}:             │
│Solution │                              │   AC: p × 55%  CP: (1−p) × 55%            │
│         │                              │   Rank 1 draws 40% of pool                 │
│         │                              │   Ranks 2-10 draw diminishing shares        │
│         │                              │   Rank 11+: no draw                         │
└─────────┴──────────────────────────────┴──────────────────────────────────────────────┘

Token supply: 21M PWM total. Minting pool = 82% (17.22M PWM).
Early miners earn more: Rank 1 draws 40% of remaining pool at time of solution.
T_k (15% of every L4 event) accumulates per-Principle — self-funds adversarial bounties.
```

---

## Mining Strategies

| Strategy | Effect |
|----------|--------|
| Start with T1 Nominal | Lowest risk; GAP-TV clears threshold |
| Use EfficientSCI or STFormer on T1 | Higher PSNR → Q ≈ 1.0 → larger pool share |
| Solve T3 moderate with PnP-FFDNet | Demonstrates robustness under typical mismatch |
| Solve T4 blind calibration | Highest I-benchmark ρ=10; CACTI has 100% recovery via grid search |
| Attempt P-benchmark | ρ=50; largest pool weight; cross-claim I-benchmarks after |
| Be first solver in CACTI domain | Novelty multiplier ν_c is highest for first solutions |
| Submit across multiple resolutions | Convergence-based scoring (M2) rewards this |
| Use a novel solver architecture | Method-signature diversity (M5) rewards novelty |

### Recommended progression

| Stage | Task | Approx. reward (Rank 1, draw from Pool) |
|-------|------|--------------------------------------|
| 1. Learn | T1 Nominal with GAP-TV | Rank 1 = 40% of Pool_{k,j,T1} |
| 2. Improve | T1 Nominal with EfficientSCI | Rank 1 = 40% of Pool_{k,j,T1} |
| 3. Challenge | T3 Moderate (requires mismatch-aware solver) | Rank 1 = 40% of Pool_{k,j,T3} |
| 4. Calibrate | T4 Blind calibration (100% recovery in 60s) | Rank 1 = 40% of Pool_{k,j,T4} |
| 5. Frontier | P-benchmark (full Ω range) | Rank 1 = 40% of Pool_{k,j,P} + cross-claims |

---

## What You Cannot Do

- **Memorize benchmark outputs** — Mechanism 1 generates test instances from an unmanipulable randomness source; you cannot predict which scenes you will be tested on.
- **Fake the certificate** — Every full node checks it in O(1); forging is mathematically infeasible.
- **Skip gates** — S3 convergence check catches solvers that produce good numbers without actually converging.
- **Game the quality score** — Worst-case scoring across K instances (Mechanism 3) means one bad scene tanks your score.
- **Reuse someone else's solution** — The certificate commits your SP identity and solution hash; duplicates are detected.
- **Use EfficientSCI naively under mismatch** — EfficientSCI drops 20.58 dB under mismatch; the protocol detects uncalibrated learned solvers.
- **Tamper with upstream hashes** — Changing any artifact (Principle, spec, benchmark) breaks the hash chain; all verifiers detect it.
- **Submit a near-duplicate spec** — d_spec < 0.15 is rejected outright; add an I-benchmark tier instead.

---

## Quick-Start Commands

```bash
# 1. Check available CACTI tasks
pwm-node benchmarks | grep cacti

# 2. Pre-check gates (free, no compute)
pwm-node verify cacti/cacti_mismatch_only_t1_nominal.yaml

# 3. Mine the center I-benchmark (nominal, ρ=1)
pwm-node mine cacti/cacti_mismatch_only_t1_nominal.yaml

# 4. Inspect your certificate
pwm-node inspect sha256:<your_cert_hash>

# 5. Check balance after 7-day challenge period
pwm-node balance

# 6. Mine moderate mismatch tier (ρ=5)
pwm-node mine cacti/cacti_mismatch_only_t3_moderate.yaml

# 7. Mine blind calibration tier (ρ=10, highest I-benchmark)
pwm-node mine cacti/cacti_mismatch_only_t4_blind.yaml

# 8. Mine oracle-assisted center I-benchmark (ρ=1, true_phi provided)
pwm-node mine cacti/cacti_oracle_t1_h64_b4.yaml

# 9. Register as Solution Provider (SP) — after proving solution works locally
#    Include compute manifest so CPs know hardware requirements
pwm-node sp register \
  --entry-point solve.py \
  --share-ratio 0.40 \
  --min-vram-gb 8 \
  --expected-runtime-s 120 \
  --framework pytorch

# 10. Register as Compute Provider (CP)
pwm-node cp register --gpu A100 --vram 80
```

---

## Reference

| Topic | Where to find it |
|-------|------------------|
| CACTI Principle (#27) | L1-027.json in genesis/l1/ |
| Pool allocation formula | pwm_overview1.md §Pool Subscript Notation |
| Ranked draws | pwm_overview1.md §Ranked Draws |
| Track A/B/C evaluation | pwm_overview1.md §Track A/B/C |
| d_spec duplicate gate | pwm_overview1.md §Spec Distance |
| Benchmark validation | pwm_overview1.md §Benchmark Validation |
