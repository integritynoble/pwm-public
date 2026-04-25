# CASSI — Complete Four-Layer Walkthrough

**Principle #25: Coded Aperture Snapshot Spectral Imaging (CASSI)**
Domain: Compressive Imaging | Difficulty: Standard (delta=3) | Carrier: Photon
Verification: triple-verified — canonical reference principle; reviewed 2026-04-21 by physics/numerics/cross-domain verifiers; 3× ACCEPT with schema improvements flagged (see pwm-team/coordination/agent-*-verifier/reviews/025_cassi.md)

---

## The Four-Layer Pipeline for CASSI

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
│  about coded    │    │  for CASSI      │    │  + baselines    │    │  + earn PWM     │
│  aperture +     │    │  imaging tasks  │    │  + thresholds   │    │                 │
│  spectral shear │    │                 │    │                 │    │  (PoSol reward) │
│                 │    │                 │    │                 │    │                 │
│  Reward:        │    │  Reward:        │    │  Reward:        │    │  Reward: ranked │
│  Reserve grant  │    │  Reserve grant  │    │  Reserve grant  │    │  draw from      │
│  (DAO vote)     │    │  (DAO vote)     │    │  (DAO vote)     │    │  per-principle  │
│  + 5% upstream  │    │  + 10% upstream │    │  + 15% upstream │    │  pool           │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## Layer 1: Seeds → Principle (The Physics Foundation)

### What the domain expert writes (seeds)

The seeds are raw domain knowledge — the physics of coded aperture spectral imaging expressed as a six-tuple:

```yaml
# ─── CASSI SEED (Layer 1 input) ───
# Written by: domain expert (spectral imaging researcher)
# Purpose: define the forward model and physics constraints

omega:
  description: "3D hyperspectral datacube"
  spatial: [H, W]                    # spatial dimensions
  spectral: N_lambda                 # number of spectral bands
  range_nm: [lambda_min, lambda_max] # wavelength range

E:
  forward_model: "y(x,y) = sum_lambda C(x, y + a*lambda) * f(x, y + a*lambda) + n"
  components:
    modulation: "C ∈ {0,1}^{H×W}, binary coded aperture"
    dispersion: "Prism shifts band lambda by a*lambda pixels"
    accumulation: "Detector sums all dispersed, modulated bands"
    detection: "Single 2D snapshot y ∈ R^{H×(W+a*N_lambda)}"
  DAG: "L.diag.binary → L.shear.spectral → ∫.spectral"

B:
  nonnegativity: "f(x,y,lambda) >= 0 (radiance)"
  spectral_smoothness: "Adjacent bands are correlated"
  sparsity: "Spectral cube is compressible in some basis"

I:
  carrier: photon
  mask_type: binary_random
  fill_factor: 0.5
  dispersion_slope: "a px/band"
  noise_model: poisson_gaussian

O:
  metrics: [PSNR_per_channel, SSIM, SAM_deg, residual_norm]

epsilon:
  description: "Domain-level feasibility thresholds"
  PSNR_achievable: ">= 20 dB for any well-posed CASSI geometry"
```

### What S1-S4 discovers (the Principle)

Layer 1 runs Valid(B) = S1 ∧ S2 ∧ S3 ∧ S4 ∧ (δ ≥ δ_min) ∧ P1-P10 on the seeds. S1-S4 extracts the **Principle P = (E, G, W, C)**:

```
┌────────────────────────────────────────────────────────────────────────────┐
│  CASSI PRINCIPLE  P = (E, G, W, C)                                       │
│  Principle #25 in the PWM registry                                       │
│  sha256: <principle_hash>  (immutable once committed)                    │
├────────┬───────────────────────────────────────────────────────────────────┤
│   E    │ FORWARD MODEL                                                   │
│        │                                                                  │
│        │ y(x,y) = Σ_λ C(x, y + a·λ) · f(x, y + a·λ) + n               │
│        │                                                                  │
│        │ Physical chain:                                                  │
│        │   Scene f(x,y,λ) ──→ Modulate by mask C ──→ Disperse by prism  │
│        │   ──→ Accumulate across λ ──→ Detect on 2D sensor              │
│        │                                                                  │
│        │ Inverse problem: recover f ∈ R^{H×W×N_λ} from y ∈ R^{H×W'}    │
│        │ Compression ratio: N_λ : 1 (28:1 for 28 bands)                 │
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
│        │   (See primitives.md for the full 143-leaf hierarchy)           │
│        │                                                                  │
│        │ CASSI forward DAG:                                               │
│        │                                                                  │
│        │   [L.broadcast.spectral] → [L.diag.binary] → [L.shear.spectral] → [∫.spectral]
│        │         │                       │                  │                │
│        │    duplicate mask          Hadamard product    prism shear     sum over λ
│        │    C(x,y) → C(x,y,λ)     C(x,y,λ)·f(x,y,λ)  shift a·λ px   onto detector
│        │    same mask ∀λ            element-wise         dispersion     collapse 3D→2D
│        │                                                                  │
│        │ V = {L.broadcast.spectral, L.diag.binary, L.shear.spectral, ∫.spectral}
│        │ A = {L.broadcast.spectral → L.diag.binary,                      │
│        │      L.diag.binary → L.shear.spectral,                          │
│        │      L.shear.spectral → ∫.spectral}                            │
│        │ |V| = 4,  |A| = 3,  n_c = 0 (no coupling)                     │
│        │                                                                  │
│        │ Node semantics (hierarchical decomposition):                     │
│        │   L.broadcast.spectral:                                          │
│        │     root L = linear operator                                    │
│        │     sub  broadcast = replicate along a dimension                │
│        │     subsub spectral = broadcast across wavelength λ             │
│        │     C(x,y) ∈ {0,1}^{H×W} → C(x,y,λ) = C(x,y) ∀λ            │
│        │     every spectral band receives the same mask                  │
│        │                                                                  │
│        │   L.diag.binary:                                                │
│        │     root L = linear operator                                    │
│        │     sub  diag = diagonal (element-wise multiply, O(n))         │
│        │     subsub binary = values ∈ {0,1} (coded aperture mask)       │
│        │     g(x,y,λ) = C(x,y,λ) · f(x,y,λ)  (Hadamard product in 3D)│
│        │                                                                  │
│        │   L.shear.spectral:                                             │
│        │     root L = linear operator                                    │
│        │     sub  shear = dimension-dependent translation               │
│        │     subsub spectral = shift indexed by wavelength λ            │
│        │     g(x,y,λ) → g(x, y+a·λ, λ)  (prism dispersion, O(n))     │
│        │                                                                  │
│        │   ∫.spectral:                                                   │
│        │     root ∫ = integrate / accumulate                             │
│        │     sub  spectral = sum over wavelength dimension              │
│        │     y(x,y) = Σ_λ g(x, y+a·λ, λ)  (collapse 3D→2D)           │
│        │                                                                  │
│        │ Why three L nodes are distinguishable:                           │
│        │   L.broadcast.spectral: expansion, κ = 1, replicates 2D→3D    │
│        │   L.diag.binary:       diagonal sparsity, κ = 1, binary {0,1} │
│        │   L.shear.spectral:    permutation sparsity, κ = 1, λ-indexed │
│        │   Different sub.subsub → different complexity class & structure │
│        │   S1 gate checks dimensional compatibility between nodes       │
│        │                                                                  │
│        │ Cross-domain pattern: L.broadcast appears whenever a 2D        │
│        │   mask/pattern is applied to a higher-dimensional cube         │
│        │   (CASSI: spectral, holography: depth)                          │
│        │                                                                  │
│        │ L_DAG = (|V|-1) + log₁₀(κ/κ₀) + n_c                          │
│        │       = 3 + log₁₀(5000/1000) + 0                              │
│        │       = 3 + 0.70 + 0 = 3.70     (κ₀ = 1000, κ_sys ≈ 5000)    │
│        │                                                                  │
│        │ n_c = number of coupling constraints in the forward physics    │
│        │   DAG — cross-edges or shared-state dependencies between       │
│        │   sub-operators in the physical forward model (not the solver).│
│        │   n_c = 0 here: broadcast→modulate→shear→accumulate is a      │
│        │   pure sequential pipeline; no sub-operator feeds back into    │
│        │   or jointly constrains a prior node.                          │
│        │   (TV or ADMM solvers add coupling in L4, not in L1.)         │
│        │                                                                  │
│        │ Note: κ₀=1000 is the reference; κ_sys≈5000 is the compound    │
│        │ system condition number (28:1 underdetermined inversion);      │
│        │ sub-operator condition numbers (κ≈1) appear in W below.        │
│        │                                                                  │
│        │ Tier: standard (δ = 3)                                          │
├────────┼───────────────────────────────────────────────────────────────────┤
│   W    │ WELL-POSEDNESS CERTIFICATE                                      │
│        │                                                                  │
│        │ Existence: YES — underdetermined but regularizable               │
│        │   (H×W observations for H×W×N_λ unknowns;                      │
│        │    compressive sensing theory guarantees recovery               │
│        │    when mask satisfies RIP-like conditions)                      │
│        │                                                                  │
│        │ Uniqueness: YES — under sparsity assumption                     │
│        │   (spectral cube compressible in wavelet/DCT basis;             │
│        │    binary random mask with 50% fill satisfies RIP)              │
│        │                                                                  │
│        │ Stability: CONDITIONAL — depends on mask quality                │
│        │   Sub-operator κ ≈ 1 (each individual L.* node)                │
│        │   Compound κ_sys ≈ 5000 (full 28:1 inverse problem)            │
│        │   Effective κ_eff ≈ 50 (ideal calibration, with regularization)│
│        │   κ_eff ≈ 200 (with mismatch: dx, dy, θ, a₁, α errors)        │
│        │                                                                  │
│        │ Mismatch model (5 parameters as Ω dimensions):                  │
│        │   Φ_true = D(a₁,α) · T(dx,dy,θ) · Φ_nominal                   │
│        │   dx = horiz shift, dy = vert shift, θ = rotation               │
│        │   a₁ = dispersion slope error, α = dispersion angle error       │
│        │   All 5 are declared Ω dimensions in the spec_range below       │
├────────┼───────────────────────────────────────────────────────────────────┤
│   C    │ ERROR-BOUNDING METHODOLOGY                                      │
│        │                                                                  │
│        │ e = per-channel PSNR (primary), SSIM, SAM (secondary)           │
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
└────────┴───────────────────────────────────────────────────────────────────┘
```

### Physics fingerprint

Each Principle carries an immutable `physics_fingerprint` block committed with the Principle hash. It enables automatic deduplication across the registry (Jaccard distance on fingerprint sets):

```yaml
physics_fingerprint:
  carrier:            photon
  sensing_mechanism:  coded_aperture
  integration_axis:   spectral
  problem_class:      linear_inverse
  noise_model:        shot_poisson
  solution_space:     3D_spectral
  primitives:
    - L.diag.binary
    - L.shear.spectral
    - "∫.spectral"
```

**Deduplication example**: CASSI vs. DD-CASSI (adds depth sensing) → d_principle = 0.42 (Related — contributor may stake a new Principle). CASSI vs. X-ray CT → d_principle = 0.79 (Distinct — proceeds ✓).

### Spec range declaration

The Principle creator declares a `spec_range` block at registration. Only specs within this range earn protocol minting (A_k) and per-principle treasury (T_k). Specs outside the range are accepted but funded from contributor bounty only (B_k).

```yaml
spec_range:
  center_spec:
    problem_class:     spectral_reconstruction
    forward_operator:  coded_aperture_spectral
    input_format:      measurement_only       # no oracle parameters
    omega:
      H:               256
      W:               256
      N_bands:         28
      mask_density:    0.5
      noise_level:     0.01
      disp_a1_error:   0.0    # mismatch params as Ω dimensions
      disp_alpha_error: 0.0
      mask_dx:         0.0
      mask_dy:         0.0
      mask_theta:      0.0
    epsilon_fn_center: "28.0 dB PSNR"

  allowed_forward_operators:
    - coded_aperture_spectral

  allowed_problem_classes:
    - spectral_reconstruction
    - hyperspectral_unmixing

  allowed_omega_dimensions:
    - H
    - W
    - N_bands
    - mask_density
    - noise_level
    - disp_a1_error      # dispersion slope drift (fraction of nominal)
    - disp_alpha_error   # dispersion axis angle error (degrees)
    - mask_dx            # mask x-shift (pixels)
    - mask_dy            # mask y-shift (pixels)
    - mask_theta         # mask rotation (degrees)

  omega_bounds:
    H:               [64, 2048]
    W:               [64, 2048]
    N_bands:         [8,  128]
    mask_density:    [0.3, 0.7]
    noise_level:     [0.001, 0.1]
    disp_a1_error:   [0.0, 0.05]
    disp_alpha_error:[0.0, 0.30]
    mask_dx:         [0.0, 1.0]
    mask_dy:         [0.0, 1.0]
    mask_theta:      [0.0, 0.15]

  epsilon_bounds:
    psnr_db: [20.0, 45.0]
```

### What S1-S4 checks at Layer 1

| Gate | What it checks on the CASSI seeds | Result |
|------|-----------------------------------|--------|
| **S1** | Dimensions: L.diag.binary mask C ∈ {0,1}^{H×W} matches spatial grid; L.shear.spectral dispersion a·N_λ fits detector width; ∫.spectral output is 2D; DAG nodes are dimensionally consistent | PASS |
| **S2** | Well-posedness: binary random mask (50% fill) satisfies RIP-like condition for spectral recovery; underdetermined system is regularizable | PASS |
| **S3** | Convergent solver exists: GAP-TV, ADMM, PnP all converge for CASSI with known rate bounds | PASS |
| **S4** | Error is bounded: per-channel PSNR computable, convergence rate q=2.0 confirmed by multi-resolution analysis | PASS |

### Layer 1 reward

```
L1 Principle creation:
  One-time:  Reserve grant (DAO vote) when S4 gate passes
             Size ∝ expected L4 activity; no fixed formula
  Ongoing:   5% of every L4 minting draw under this Principle
             5% of every L4 usage fee under this Principle

Genesis Principles (#1–500): auto-promoted at launch; no staking required.
Protocol minting (A_k) flows from day 1.
```

### The Principle is now immutable

Once committed on-chain as `sha256:<principle_hash>`, the CASSI Principle **never changes**. All downstream spec.md files, benchmarks, and solutions reference this hash. Updating the physics means creating Principle v2 (a new hash), not modifying v1.

---

## Layer 2: Principle + S1-S4 → spec.md (Task Design)

### Who does this?

A **task designer** (can be the same domain expert or anyone else). They take the CASSI Principle and design specific, solvable tasks. Accepted specs earn a **Reserve grant** (DAO vote) on submission plus ongoing upstream royalties on all future L4 events.

### What the task designer writes

Each spec.md is a concrete instantiation of the Principle as a flat **six-tuple S = (Ω, E, B, I, O, ε) + principle_ref**. Items that live elsewhere:

| Moved to Principle | Moved to Benchmark (L3) |
|--------------------|------------------------|
| `difficulty` (L_DAG, δ, tier) | `expert_baseline`, `evaluator` |
| `primitives`, `carrier`, `modality` | quality scoring table |
| `quality_metrics` (C field) | per-solver metrics |

**Key insight: one spec, multiple I-benchmarks.** The CASSI measurement-only spec covers all mismatch severity levels — the solver input format never changes (measurement + mask only). Each mismatch severity is a separate I-benchmark tier within the same spec, not a separate spec. The oracle scenario (solver given exact mismatch parameters as input) requires a distinct spec because the input format changes.

**Two natural specs under this Principle:**

| Spec | Solver input | Ω dimensions | Center I-bench | Purpose |
|------|-------------|--------------|----------------|---------|
| #1 Mismatch-only | measurement + mask | H, W, N_bands, noise + 5 mismatch dims | Nominal (all mismatch = 0, ρ=1) | Reconstruction under unknown calibration error |
| #2 Oracle-assisted | measurement + mask + true Φ | H, W, N_bands, noise only (no mismatch dims) | H=64, N_bands=8, noise=0.01 (ρ=1) — tiers scale by H/N_bands/noise | Upper bound — solver knows exact calibration |

```
CASSI Principle (sha256:<principle_hash>)
    │
    ├──→ spec.md #1: Mismatch-only       sha256:<spec1_hash>
    │       │   Ω = ranges; center I-bench at nominal (no mismatch)
    │       ├──→ I-bench T1: Nominal (ρ=1)   ← center_ibenchmark
    │       ├──→ I-bench T2: Low (ρ=3)
    │       ├──→ I-bench T3: Moderate (ρ=5)
    │       ├──→ I-bench T4: Blind/severe (ρ=10)
    │       └──→ P-benchmark: Full Ω range (ρ=50)
    │
    └──→ spec.md #2: Oracle-assisted     sha256:<spec2_hash>
            │   Ω = {H, W, N_bands, noise} only — no mismatch dims
            │   center I-bench at small/easy system params (ρ=1)
            ├──→ I-bench T1: Small (H=64, N_bands=8, low noise, ρ=1)   ← center_ibenchmark
            ├──→ I-bench T2: Medium (H=256, N_bands=28, mod. noise, ρ=3)
            ├──→ I-bench T3: Large (H=512, N_bands=64, high noise, ρ=5)
            └──→ P-benchmark: Full Ω range (H/W→2048, N_bands→128, ρ=50)
```

> **Ω in spec.md is always a range, not a fixed grid.** The spec declares the full parameter space the solver and P-benchmark must cover. The I-benchmark is pinned to a single `omega_tier` point within that range — that is the "center" the spec creator defines in `ibenchmark_range.center_ibenchmark`.

#### spec.md #1: Mismatch-Only (Canonical CASSI Spec)

```yaml
# cassi/kaist_mismatch_only.yaml
# Layer 2 output — references the CASSI Principle

principle_ref: sha256:<principle_hash>   # ← links to Layer 1

# Ω = full parameter RANGE (not a fixed grid)
omega:
  H:               [64, 2048]      # spatial height range
  W:               [64, 2048]
  N_bands:         [8, 128]        # spectral bands range
  mask_density:    [0.3, 0.7]
  noise_level:     [0.001, 0.1]
  # Mismatch dims: zero = ideal, non-zero = calibration error
  disp_a1_error:   [0.0, 0.05]    # dispersion slope drift
  disp_alpha_error:[0.0, 0.30]    # dispersion axis angle error (deg)
  mask_dx:         [0.0, 1.0]     # mask x-shift (pixels)
  mask_dy:         [0.0, 1.0]
  mask_theta:      [0.0, 0.15]    # mask rotation (deg)

E:
  forward: "y(x,y) = sum_lambda C(x,y) * x(x,y, lambda + dispersion) + n"
  operator: cassi_forward
  primitive_chain: "L.broadcast.spectral → L.diag.binary → L.shear.spectral → ∫.spectral"
  inverse: "recover x (H×W×N_bands) from single snapshot y"

B:
  nonnegativity: true
  spectral_smoothness: true

I:
  strategy: zero_init

O: [per_channel_PSNR, SSIM, SAM_deg, residual_norm, convergence_curve]

# epsilon_fn maps any Ω point → minimum acceptable PSNR
epsilon_fn: "25.0 + 2.0 * log2(H / 64) + 1.5 * log10(photon_count / 50)"

input_format:
  measurement: float32(H, W)
  mask:         bool(H, W)
  # No mismatch params — solver must infer or be robust to calibration error
output_format:
  spectral_cube: float32(H, W, N_bands)

baselines:
  - GAP-TV        # method_sig: L+O (linear + TV optimization)
  - ADMM-CASSI    # method_sig: L+O
  - PnP-HSICNN    # method_sig: L+N (linear + deep denoiser)

# ibenchmark_range — center I-bench at nominal Ω (all mismatch = 0)
ibenchmark_range:
  center_ibenchmark:
    rho: 1
    omega_tier:
      H:               256
      N_bands:         28
      noise_level:     0.01
      disp_a1_error:   0.0    # ← nominal center: zero mismatch
      disp_alpha_error: 0.0
      mask_dx:         0.0
      mask_dy:         0.0
      mask_theta:      0.0
    epsilon: 28.0              # fixed ε at this exact Ω tier point

  tier_bounds:
    H:               [64,  1024]
    N_bands:         [16,  128]
    noise_level:     [0.005, 0.1]
    disp_a1_error:   [0.0, 0.05]
    disp_alpha_error:[0.0, 0.20]
    mask_dx:         [0.0, 1.0]
    mask_dy:         [0.0, 1.0]
    mask_theta:      [0.0, 0.15]

  proximity_threshold: 0.10   # τ — new I-bench must differ by > 10% in ≥1 dim
```

**epsilon_fn example:**
```
At Ω = {H=128, photon_count=100}:
  ε = 25.0 + 2.0 × log2(128/64) + 1.5 × log10(100/50) = 27.45 dB

At the center I-bench Ω = {H=256, photon_count=50k, disp_a1_error=0.0}:
  ε ≈ 28.0 dB  ← this is what ibenchmark_range.center_ibenchmark.epsilon records
```

The `epsilon_fn` is an AST-sandboxed Python expression. For each I-benchmark, it is evaluated at that benchmark's fixed `omega_tier` to produce the single-value `epsilon` stored in that I-benchmark's `thresholds.yaml`. The P-benchmark uses the full `epsilon_fn` function across all Ω samples.

#### spec.md #2: Oracle-Assisted (Separate Spec — Different Input Format)

```yaml
# cassi/kaist_oracle_assisted.yaml

principle_ref: sha256:<principle_hash>

# Ω contains only intrinsic system parameters — NO mismatch dims, NO mask_density
# Mask pattern is provided directly as input (bool mask); its density is implicit
# Mismatch parameters are INPUTS (true_phi), not Ω dimensions
omega:
  H:               [64, 2048]
  W:               [64, 2048]
  N_bands:         [8, 128]
  noise_level:     [0.001, 0.1]

E:
  forward: "y = Phi_true * x + n  (Phi_true constructed from true_phi input)"
  operator: cassi_forward_oracle

B:
  nonnegativity: true
  spectral_smoothness: true

I:
  strategy: zero_init

O: [per_channel_PSNR, SSIM, SAM_deg, residual_norm]

epsilon_fn: "28.0 + 2.0 * log2(H / 64) + 1.5 * log10(photon_count / 50)"
# Same structure as mismatch spec but higher baseline —
# solver has true calibration, so stricter threshold is appropriate

input_format:
  measurement:   float32(H, W)
  mask:          bool(H, W)
  true_phi:      dict   # ← oracle input: {dx, dy, theta, a1, alpha}
  # This additional input field makes this a DIFFERENT spec from mismatch-only
output_format:
  spectral_cube: float32(H, W, N_bands)

baselines:
  - GAP-TV-oracle   # method_sig: L+O with true operator
  - MST-L-oracle    # method_sig: T+O (transformer + true operator)
  - ADMM-oracle     # method_sig: L+O

# ibenchmark_range — center I-bench at small/easy system params
# No mismatch dims — mismatch is in true_phi input, not in Ω
# I-benchmark difficulty scales with H, N_bands, noise (larger = harder)
ibenchmark_range:
  center_ibenchmark:
    rho: 1
    omega_tier:
      H:             64          # small spatial size → easy
      N_bands:       8           # few spectral bands → easy
      noise_level:   0.01
    epsilon: 30.0              # ε at center Ω (higher than mismatch spec — oracle advantage)

  tier_bounds:
    H:               [64, 2048]
    N_bands:         [8, 128]
    noise_level:     [0.001, 0.1]
    # No mismatch dims — mismatch is in true_phi input, not in Ω

  proximity_threshold: 0.10
```

### Spec distance and duplicate prevention

Before accepting a new spec, the protocol computes:

```
d_spec(S1, S2) = 0.50 · d_structural + 0.30 · d_omega + 0.20 · d_epsilon
```

---

#### Component 1 — d_structural (weight 0.50)

Jaccard distance on a flat set of `(field, value)` pairs from the S2/S3 spec parameters.
Multi-valued fields contribute one pair per entry:

```python
def feature_set(spec) -> set:
    F = set()
    # Single-valued fields
    F.add(("operator_class",         spec.operator_class))
    F.add(("function_space",         spec.function_space))
    F.add(("modulus_of_continuity",  spec.modulus_of_continuity))
    F.add(("convergence_order_tier", spec.convergence_order_tier))
    F.add(("condition_number_tier",  spec.condition_number_tier))
    F.add(("certificate_procedure",  spec.certificate_procedure))
    F.add(("noise_model",            spec.noise_model))
    # Multi-valued fields
    for obs  in spec.observables:            F.add(("observable",  obs))
    for dc   in spec.discretization_classes: F.add(("discr_class", dc))
    for name in spec.omega_dimension_names:  F.add(("omega_dim",   name))
    return F

d_structural = 1 − |F(S1) ∩ F(S2)| / |F(S1) ∪ F(S2)|
```

> **Key:** omega_dimension *names* are included, *values* (ranges) are excluded.
> Two specs with the same dimension names but different ranges are the same
> structural class — different ranges define different I-benchmark tiers.

---

#### Component 2 — d_omega (weight 0.30)

Mean Ω range IoU gap over **shared dimensions only**:

```
For each shared dimension k:
    IoU_k = |range_k(S1) ∩ range_k(S2)| / |range_k(S1) ∪ range_k(S2)|
    continuous: intersection/union of intervals on the real line
    discrete:   intersection/union of declared value sets

d_omega = 1 − (1/|shared_dims|) × Σ_k IoU_k

Special cases:
    No shared dims   →  d_omega = 1.0  (completely different Ω spaces)
    Identical ranges →  d_omega = 0.0  (complete overlap)
```

---

#### Component 3 — d_epsilon (weight 0.20)

Normalised ε threshold gap across all observables:

```
For each observable obs:
    ε̄_i(obs) = median of epsilon_fn_i(Ω) over 50 uniform Ω samples
                (representative threshold for spec i)

    δ_ε(obs) = |ε̄_1(obs) − ε̄_2(obs)| / (sota_obs − floor_obs)

d_epsilon = (1/|O|) × Σ_obs δ_ε(obs)
```

---

#### CASSI Worked Example — Spec #1 (Mismatch-only) vs Spec #2 (Oracle-assisted)

**d_structural:**

| Feature | Spec #1 Mismatch-only | Spec #2 Oracle-assisted | Shared |
|---|---|---|---|
| operator_class | coded_aperture_spectral | coded_aperture_spectral | ✓ |
| function_space | L2_spectral | L2_spectral | ✓ |
| modulus_of_continuity | Lipschitz | Lipschitz | ✓ |
| convergence_order_tier | O(1/k) | O(1/k) | ✓ |
| condition_number_tier | **high** (κ_eff≈200 with mismatch) | **medium** (κ_eff≈50, oracle) | ✗ |
| certificate_procedure | S1-S4_residual | S1-S4_residual | ✓ |
| noise_model | shot_poisson | shot_poisson | ✓ |
| observable | PSNR, SSIM, SAM | PSNR, SSIM, SAM | ✓×3 |
| discr_class | TV, wavelet_L1, deep_unrolling, PnP, transformer | + operator_aware | ✓×5, ✗×1 |
| omega_dim | H, W, N_bands, noise + 5 mismatch dims | H, W, N_bands, noise only | ✓×4, ✗×5 |

```
|F1| = 25,  |F2| = 21
|F1 ∩ F2| = 18  (6 scalars + 3 obs + 5 discr + 4 omega)
|F1 ∪ F2| = 25 + 21 − 18 = 28

d_structural = 1 − 18/28 = 0.36
```

**d_omega:**

Shared dims: H, W, N_bands, noise_level (both specs declare identical ranges)

```
H:           [64, 2048] vs [64, 2048]  →  IoU = 1.0
W:           [64, 2048] vs [64, 2048]  →  IoU = 1.0
N_bands:     [8,  128]  vs [8,  128]   →  IoU = 1.0
noise_level: [0.001, 0.1] vs [0.001, 0.1]  →  IoU = 1.0

d_omega = 1 − (1/4) × (1.0+1.0+1.0+1.0) = 0.0
```

The 5 mismatch dims unique to spec #1 are not shared → not counted in IoU.
Their absence is captured by d_structural (omega_dim names differ).

**d_epsilon:**

```
PSNR: ε̄_1 ≈ 28.0 dB,  ε̄_2 ≈ 30.0 dB
  sota ≈ 34 dB,  floor ≈ 20 dB
  δ_ε(PSNR) = |28.0 − 30.0| / 14.0 = 0.14

SSIM: ε̄_1 ≈ 0.82,  ε̄_2 ≈ 0.86
  sota ≈ 0.96,  floor ≈ 0.60
  δ_ε(SSIM) = |0.82 − 0.86| / 0.36 = 0.11

SAM: ε̄_1 ≈ 12°,  ε̄_2 ≈ 10°
  sota ≈ 4°,  floor ≈ 20°
  δ_ε(SAM) = |12 − 10| / 16 = 0.13

d_epsilon = (0.14 + 0.11 + 0.13) / 3 = 0.13
```

**Combined:**

```
d_spec = 0.50×0.36 + 0.30×0.0 + 0.20×0.13
       = 0.180 + 0.000 + 0.026
       = 0.21  →  "Similar" band (0.15–0.35)
```

The oracle spec is accepted (d_spec > 0.15) but with **reduced ν_c** (B_k only unless within
the Principle's `spec_range`). It qualifies as a distinct spec — not an I-benchmark — because
the input_format changes (solver receives `true_phi`).

---

#### Why mismatch severity variants are I-benchmarks, not separate specs

Input format is identical (measurement + mask only). Only the Ω tier *values* change.
d_spec ≈ 0.10 (omega_dim names are the same, only ranges differ; ranges are excluded
from d_structural) → near-duplicate → **rejected as spec; submit as I-benchmark tier instead**.

---

| d_spec | Label | Action | ν_c multiplier |
|--------|-------|--------|----------------|
| < 0.15 | Near-duplicate | **Rejected** — submit as I-benchmark instead | — |
| 0.15–0.35 | Similar | Accepted, B_k only | Reduced |
| 0.35–0.65 | Related | Accepted, A_k + T_k eligible | Normal |
| > 0.65 | Novel | Accepted, A_k + T_k eligible | Enhanced |

### What S1-S4 checks at Layer 2

Each spec.md is validated against the CASSI Principle:

| Gate | What it checks | CASSI spec result |
|------|----------------|-------------------|
| **S1** | spec's Ω range [H∈64–2048, N_bands∈8–128] is consistent with Principle's spatial+spectral structure; dispersion slope 2.0 px/band is consistent with 28 bands over 450-650 nm | PASS |
| **S2** | spec's parameter bounds (mask_density∈[0.3,0.7], N_bands∈[8,128]) remain within the Principle's well-posedness regime; κ_eff < 200 across Ω | PASS |
| **S3** | For all Ω in the declared range, at least one solver converges (GAP-TV at O(1/k)); epsilon_fn hardness rule satisfied | PASS |
| **S4** | epsilon_fn thresholds are feasible per the Principle's error bounds; expert baselines do not universally pass | PASS |

### Layer 2 reward

```
L2 spec.md creation:
  One-time:  Reserve grant (DAO vote) when S4 gate passes
             Requires d_spec ≥ 0.35 to earn A_k + T_k (in-range)
             No fixed formula — size ∝ expected L4 activity
  Ongoing:   10% of every L4 minting draw under this spec
             10% of every L4 usage fee under this spec
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

**CASSI I-benchmark tiers — mismatch-only spec** (each is a single fixed `omega_tier` point):

| Tier | omega_tier (fixed Ω point) | mismatch severity | ρ | ε (from epsilon_fn at that Ω) |
|------|---------------------------|------------------|----|-------------------------------|
| T1 (Nominal) | H=256, N_bands=28, disp_a1=0.0, dx=0, dy=0 | None — calibrated | 1 | 28.0 dB |
| T2 (Low) | …, disp_a1=0.01, dx=0.2, dy=0.1 | Small drift | 3 | 25.0 dB |
| T3 (Moderate) | …, disp_a1=0.02, dx=0.5, dy=0.3, θ=0.1° | Typical hardware | 5 | 22.0 dB |
| T4 (Blind) | …, disp_a1=0.04, dx=0.8, θ=0.12° | Large, unknown to solver | 10 | 20.0 dB |

**CASSI I-benchmark tiers — oracle-assisted spec** (Ω = system params only; mismatch is in true_phi input, not omega_tier):

| Tier | omega_tier (system params only) | δ | ε |
|------|---------------------------------|----|---|
| T1 | H=256, N_bands=28, noise=0.01 | 1 | 30.0 dB |
| T2 | H=512, N_bands=64, noise=0.01 | 3 | 32.0 dB |
| T3 | H=256, N_bands=28, noise=0.05 | 3 | 28.5 dB |

**I-benchmark distance gate:** A new I-benchmark whose `omega_tier` point is within τ=0.10 of any existing I-benchmark in every Ω dimension is rejected as a near-duplicate. The proximity is measured as a fraction of each dimension's declared `tier_bounds` range.

### ibenchmark_range (declared inside the spec, repeated here for reference)

The `ibenchmark_range` block is part of the spec.md (shown in full in the spec above). It tells the protocol which Ω tier points earn A_k + T_k. Key elements:

| Field | Purpose |
|-------|---------|
| `center_ibenchmark` | The spec creator's canonical I-benchmark — a single fixed `omega_tier` point + `epsilon` (quality threshold at that Ω, from `epsilon_fn(omega_tier)`) + `rho` (benchmark pool weight ρ ∈ {1,3,5,10}). Contributors add higher-ρ I-benchmarks around this center. |
| `tier_bounds` | Which Ω values are in-range for protocol funding (A_k + T_k) |
| `proximity_threshold` | τ=0.10 — new I-bench must differ by > 10% of the declared range in ≥1 Ω dimension |

**CASSI mismatch-only spec center** (T1, nominal):
```yaml
center_ibenchmark:
  rho: 1
  omega_tier: {H: 256, N_bands: 28, noise_level: 0.01,
               disp_a1_error: 0.0, disp_alpha_error: 0.0,
               mask_dx: 0.0, mask_dy: 0.0, mask_theta: 0.0}
  epsilon: 28.0     # ε = epsilon_fn evaluated at this exact Ω tier point
```

**CASSI oracle-assisted spec center** (T1, system params only — no mismatch in Ω):
```yaml
center_ibenchmark:
  rho: 1
  omega_tier: {H: 256, N_bands: 28, noise_level: 0.01}
  epsilon: 30.0     # higher ε than mismatch spec — oracle advantage
```

The two specs have **different Ω dimensions**: the mismatch spec's Ω has 10 dimensions (5 system + 5 mismatch); the oracle spec's Ω has only 5 system dimensions. Mismatch values in the oracle spec are instance-level `true_phi` inputs — they vary per instance but are not Ω coordinates, so they do not appear in `omega_tier` or `tier_bounds`.

### What the benchmark builder creates

Layer 3 outputs a **complete, self-contained directory** — hash-committed and immutable once published. The 20 pre-built dev instances are ready to use directly. All 6 anti-overfitting mechanisms (M1-M6) are embedded as concrete files.

```
benchmark_cassi_mismatch_only_t1_nominal/     ← I-benchmark T1
│                                               omega_tier = {H:256, N_bands:28, all mismatch=0}
│                                               (grid sizes come from omega_tier, not the spec)
├── manifest.yaml              # dataset identity + immutability hashes
│
├── instances/                  # 20 READY-TO-USE dev instances
│   ├── dev_001/
│   │   ├── input.npz          #   { "measurement": (256,256),
│   │   │                      #     "mask": (256,256),
│   │   │                      #     "wavelengths": (28,) }
│   │   ├── ground_truth.npz   #   { "spectral_cube": (256,256,28) }
│   │   └── params.yaml        #   full Ω instance: H=256, N_bands=28, dx=0, dy=0, ...
│   ├── dev_002/ … dev_020/
│
├── baselines/                  # expert solutions (M5: method diversity)
│   ├── gap_tv/
│   │   ├── solution.npz       #   reconstructed spectral cubes
│   │   ├── metrics.yaml       #   per-instance PSNR/SSIM/SAM
│   │   └── method.yaml        #   method_sig: "L+O" (iterative TV)
│   ├── twist/
│   │   ├── metrics.yaml       #   mean_PSNR: 25.1, worst_PSNR: 23.8
│   │   └── method.yaml        #   method_sig: "L+O"
│   └── pnp_hsicnn/
│       ├── metrics.yaml       #   mean_PSNR: 28.2, worst_PSNR: 26.5
│       └── method.yaml        #   method_sig: "L+N" (PnP deep denoiser)
│
├── scoring/                    # deterministic evaluation (M3: worst-case)
│   ├── score.py               #   per-scene PSNR, SSIM, SAM
│   ├── thresholds.yaml        #   epsilon at this Ω tier point
│   └── worst_case.py          #   Q = f(worst_PSNR across 10 scenes)
│
├── convergence/               # M2: convergence-based scoring
│   ├── check_convergence.py   #   verifies O(h²) rate across resolutions
│   └── resolutions.yaml       #   spatial: [64, 128, 256, 512]
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
│   ├── check_s1.py            #   dims: (256,256,28) matches spec grid
│   ├── check_s2.py            #   RIP condition for mask fill
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
M5  Method-sig diversity    baselines/*/method.yaml (L+O vs L+N earn novelty bonus)
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

Divide Ω into 4 strata by primary difficulty dimension (H×W for CASSI):

| Stratum | H×W range | Representative difficulty |
|---|---|---|
| S1 small   | H×W ≤ 256²   | Easy — fits in GPU memory trivially |
| S2 medium  | 256² < H×W ≤ 512²  | Standard — typical deployment size |
| S3 large   | 512² < H×W ≤ 1024² | Hard — memory pressure, long runtime |
| S4 x-large | H×W > 1024²  | Very hard — stitched scenes, boundary effects |

**Procedure (P-benchmark):**
1. For each stratum, draw N_s = 5 random Ω points within that stratum (randomness from M1 seed)
2. Run solver on all 5 instances → 5 PSNR scores
3. Take the **worst** score from those 5
4. Worst score must pass `epsilon_fn(Ω_centroid_s)` — threshold at stratum centre
5. **All 4 strata must independently pass** — failing S4 fails Track A even if S1–S3 pass

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

Why both tracks: a solver can pass Track B (good median) but fail Track A (catastrophic at H=2048); or pass Track A (adequate worst-case per stratum) but fail Track B (mediocre everywhere). Both must pass for full certification.

---

#### Track C — Mismatch Degradation Curve (mismatch-only spec only)

Sweeps mismatch severity φ ∈ [0, 1] where φ=0 is calibrated and φ=1 is the maximum declared mismatch bounds. Tests how gracefully quality degrades as calibration error increases.

**CASSI mismatch sweep (5 points):**

| φ | dx (px) | dy (px) | θ (°) | disp_a1 | alpha (°) |
|---|---|---|---|---|---|
| 0.00 | 0.0 | 0.0 | 0.00 | 0.000 | 0.00 |
| 0.25 | 0.25 | 0.25 | 0.04 | 0.013 | 0.08 |
| 0.50 | 0.50 | 0.50 | 0.08 | 0.025 | 0.15 |
| 0.75 | 0.75 | 0.75 | 0.11 | 0.038 | 0.23 |
| 1.00 | 1.00 | 1.00 | 0.15 | 0.050 | 0.30 |

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
# benchmark_cassi_mismatch_only_t1_nominal/manifest.yaml

benchmark_id:    "cassi_mismatch_only_t1_nominal_v1"
type:            "I-benchmark"
spec_ref:        "sha256:<spec1_hash>"       # mismatch-only spec
principle_ref:   "sha256:<principle_hash>"
# omega_tier: the single fixed Ω point this I-benchmark tests
# (grid dimensions H=256, N_bands=28 come from here — NOT from the spec)
omega_tier:
  H:               256
  N_bands:         28
  noise_level:     0.01
  disp_a1_error:   0.0
  disp_alpha_error: 0.0
  mask_dx:         0.0
  mask_dy:         0.0
  mask_theta:      0.0
rho:             1                           # ρ=1 pool weight for nominal tier
epsilon:         28.0                        # epsilon_fn evaluated at this omega_tier
dataset_hash:    "sha256:<dataset_hash>"
generator_hash:  "sha256:<gen_hash>"
created:         "2026-04-14T00:00:00Z"
num_dev_instances: 20
num_baselines:     3
data_format:      "npz"
mechanisms:       [M1, M2, M3, M4, M5, M6]
```

#### scoring/thresholds.yaml (from epsilon_fn at this Ω tier)

```yaml
# epsilon_fn evaluated at T1 nominal Ω point (H=256, photon_count=50k)
PSNR_min:   24.0     # per-channel mean PSNR ≥ 24 dB
SSIM_min:   0.70
SAM_max:    25.0     # spectral angle ≤ 25°
residual_max: 0.05   # ||y - Φx̂|| / ||y||

quality_scoring:
  metric: worst_psnr           # M3: worst scene determines Q
  thresholds:
    - {min: 30.0, Q: 1.00}
    - {min: 26.0, Q: 0.90}
    - {min: 24.0, Q: 0.80}
    - {min: 22.0, Q: 0.75}    # floor — always ≥ 0.75
```

**T3 Moderate mismatch I-benchmark** thresholds (same spec, different Ω tier):

```yaml
# epsilon_fn evaluated at T3 Ω point (dx=0.5, dy=0.3, theta=0.1°, a1=0.01)
PSNR_min:   20.0     # lower threshold — mismatch degrades quality
SSIM_min:   0.55
residual_max: 0.08   # higher tolerance for mismatch scenario
```

### What S1-S4 checks at Layer 3

The benchmark is validated against **both** the spec.md and the Principle:

| Gate | What it checks | CASSI benchmark result |
|------|----------------|------------------------|
| **S1** | `instances/dev_*/input.npz` shape (256,256) and `ground_truth.npz` shape (256,256,28) match spec's Ω dimensions; 28 wavelengths span [450,650] nm per spec | PASS |
| **S2** | Problem defined by this data + Principle has bounded inverse; mask fill factor 0.5 satisfies RIP conditions per the Principle (`gates/check_s2.py`) | PASS |
| **S3** | GAP-TV residual decreases monotonically across iterations; `convergence/check_convergence.py` confirms O(h²) rate at 4 resolutions (M2) | PASS |
| **S4** | GAP-TV **worst_PSNR = 23.2 dB ≥ ε=22 dB** (M3: worst-case over 20 dev scenes); at least one solver clears ε, confirming task is feasible per Principle's error bounds | PASS |

### Layer 3 reward

```
L3 Benchmark creation:
  One-time:  Reserve grant (DAO vote) when S4 gate passes
             Requires d_ibench ≥ τ=0.10 to earn A_k + T_k (in-range)
             No fixed formula — size ∝ expected L4 activity
  Ongoing:   15% of every L4 minting draw under this benchmark
             15% of every L4 usage fee under this benchmark

Note: T_k (per-principle treasury, 15% of every L4 event) accumulates
automatically and supplements B_k funding for new contributions without
further DAO votes.
```

### The benchmark is now immutable

Once committed as `sha256:<bench_hash>`, the dataset, baselines, and scoring table are fixed. Miners compete against frozen targets.

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
     expected_runtime_s: 180      # per benchmark instance at center Ω
     expected_runtime_p_bench_s: 3600   # full P-benchmark run
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
| Single GPU | 0.40 | 40% | 60% | `min_vram_gb: 8, expected_runtime_s: 180` |
| GPU cluster | 0.20 | 20% | 80% | `min_vram_gb: 40, expected_runtime_s: 600` |

### Step-by-step mining

#### Step 1: Choose your task

```bash
pwm-node benchmarks | grep cassi
```

Output:
```
# Spec #1: Mismatch-only (measurement + mask input)
cassi   mismatch_only_t1_nominal     ρ=1    mineable   (I-benchmark, ε=28.0 dB)
cassi   mismatch_only_t2_low         ρ=3    mineable   (I-benchmark, ε=25.0 dB)
cassi   mismatch_only_t3_moderate    ρ=5    mineable   (I-benchmark, ε=22.0 dB)
cassi   mismatch_only_t4_blind       ρ=10   mineable   (I-benchmark, ε=20.0 dB)
cassi   mismatch_only_p_benchmark    ρ=50   mineable   (P-benchmark, ε=epsilon_fn(Ω))

# Spec #2: Oracle-assisted (measurement + mask + true Φ input)
# Ω varies H/N_bands/noise only — no mismatch dims in Ω
cassi   oracle_t1_h64_nb8            ρ=1    mineable   (I-benchmark, ε=30.0 dB)
cassi   oracle_t2_h256_nb28          ρ=3    mineable   (I-benchmark, ε=32.0 dB)
cassi   oracle_t3_h512_nb64          ρ=5    mineable   (I-benchmark, ε=28.5 dB)
cassi   oracle_p_benchmark           ρ=50   mineable   (P-benchmark, ε=epsilon_fn(Ω))
```

#### Step 2: Pre-check gates (free, no compute)

```bash
pwm-node verify cassi/kaist_t1_nominal.yaml
```

Checks S1-S2 against the Principle before you spend GPU time.

#### Step 3: Solve

```bash
pwm-node mine cassi/kaist_t1_nominal.yaml
```

Under the hood:
1. Downloads benchmark data (10 scenes + mask + dispersion calibration) from DA layer
2. Runs your solver on all 10 scenes
3. Produces 10 reconstructed spectral cubes (256×256×28 each)
4. Computes per-channel PSNR, SSIM, SAM for each scene

**You choose the solver.** The spec defines the problem, not the algorithm:

| Solver | Expected PSNR | GPU Time | Quality Q | Notes |
|--------|---------------|----------|-----------|-------|
| GAP-TV | ~24 dB | ~3 min/scene | 0.80 | Classical baseline |
| TwIST | ~25 dB | ~4 min/scene | 0.82 | TV-based |
| PnP-HSICNN | ~28 dB | ~6 min/scene | 0.90 | Deep denoiser |
| MST-L | ~30+ dB | ~2 min/scene | 0.98 | Transformer |
| CST | ~31+ dB | ~3 min/scene | 1.00 | State of art |

Better solver → higher PSNR → higher Q → more PWM (via larger ranked draw fraction).

#### Step 4: Local verification (S1-S4 on the solution)

Your local Judge Agent checks the solution against **all three upstream artifacts**:

```
Solution verified from TWO directions simultaneously:

Direction 1: BENCHMARK VERIFICATION
  Compare PSNR, SSIM, SAM against benchmark baselines
  → Determines quality score Q ∈ [0.75, 1.0]
  → "How good is the solution?"

Direction 2: PRINCIPLE + S1-S4 VERIFICATION
  Check solution against CASSI forward model directly
  S1: output dimensions [256,256,28] match spec grid
  S2: solver used method consistent with well-posedness
  S3: residual ||y - Φ·x̂||₂ decreased monotonically
  S4: PSNR ≥ ε(this Ω tier), SSIM ≥ 0.70, residual < error_bound
  → Determines pass/fail
  → "Is the solution mathematically correct?"

BOTH must pass → S4 Certificate issued → PWM minted
```

| Gate | What it checks on the CASSI solution | Expected |
|------|--------------------------------------|----------|
| **S1** | Output shape [256,256,28] matches spec; mask and dispersion consistent with Principle | PASS |
| **S2** | Solver method is consistent with Principle's well-posedness (used regularization for underdetermined system) | PASS |
| **S3** | Solver residual ‖y - Φ·x̂‖₂ decreases monotonically; convergence rate matches Principle's q=2.0 | PASS |
| **S4** | Worst-case PSNR ≥ ε across all 10 scenes, SSIM ≥ 0.70, SAM within bounds; residual below error bound | PASS |

#### Step 5: Certificate assembly and automatic reward routing

```json
{
  "cert_hash": "sha256:...",
  "h_s": "sha256:<spec1_hash>",
  "h_b": "sha256:<bench1_hash>",
  "h_p": "sha256:<principle_hash>",
  "h_x": "sha256:... (reconstructed spectral cubes hash)",
  "r": {
    "residual_norm": 0.024,
    "error_bound": 0.05,
    "ratio": 0.48
  },
  "c": {
    "resolutions": [[128, 0.038], [256, 0.009], [512, 0.002]],
    "fitted_rate": 1.92,
    "theoretical_rate": 2.0,
    "K": 3
  },
  "d": {"consistent": true},
  "Q": 0.89,
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

| Subscript | Meaning | CASSI example |
|---|---|---|
| `k` | Principle index | k=3 (CASSI Principle) |
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
               δ_k = Principle difficulty tier (CASSI: δ=3); fixed at L1 from L_DAG
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

**CASSI example** (mismatch-only spec, j=1; total ρ = 50+10+5+3+1 = 69):

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

**Example** (Pool_{k,j,b} = 1,000 PWM for one benchmark, p=0.40, so AC=30%×55%, CP=70%×55%):

| Rank | Draw (PWM) | AC (p×55%) | CP ((1-p)×55%) | L3 (15%) | L2 (10%) | L1 (5%) | T_k (15%) |
|------|-----------|-----------|---------------|----------|----------|---------|-----------|
| 1 | 400.00 | 66.00 | 154.00 | 60.00 | 40.00 | 20.00 | 60.00 |
| 2 | 30.00 | 4.95 | 11.55 | 4.50 | 3.00 | 1.50 | 4.50 |
| 3 | 11.40 | 1.88 | 4.39 | 1.71 | 1.14 | 0.57 | 1.71 |
| 4 | 5.59 | 0.92 | 2.15 | 0.84 | 0.56 | 0.28 | 0.84 |
| 5–10 | ~5.3 each | ~0.88 | ~2.04 | ~0.79 | ~0.53 | ~0.26 | ~0.79 |
| **Rollover** | **520.65** | — | — | — | — | — | — |

**Upstream royalty split (same for minting draws and usage fees):**

| Recipient | Share | Notes |
|-----------|-------|-------|
| SP (Algorithm Creator) | p × 55% | Earns passively; sets p at registration |
| CP (Compute Provider) | (1−p) × 55% | Earns by running jobs; distinct for mining vs. usage |
| L3 Benchmark creator | 15% | Upstream royalty |
| L2 Spec author | 10% | Upstream royalty |
| L1 Principle creator | 5% | Upstream royalty |
| T_k per-principle treasury | 15% | Self-funds adversarial bounties + validator fees |

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

The calibrated mask matches reality. The simplest CASSI task.

| Property | Value |
|----------|-------|
| omega_tier | H=256, N_bands=28, all mismatch dims = 0 |
| Operator | Calibrated mask (Φ = Φ_true) |
| Expert baseline | GAP-TV: PSNR = 24.34 dB, SSIM = 0.723 |
| ε | 28.0 dB (epsilon_fn at this Ω point) |
| ρ | 1 |

```bash
pwm-node mine cassi/kaist_mismatch_only_t1_nominal.yaml
```

### Mismatch-Only Spec: Tiers T2 / T3 (Low / Moderate Mismatch)

Same measurement-only input format — only the `omega_tier` point changes.

| Property | T2 (Low) | T3 (Moderate) |
|----------|----------|---------------|
| omega_tier | disp_a1=0.01, dx=0.2, dy=0.1 | disp_a1=0.02, dx=0.5, dy=0.3, θ=0.1° |
| Expert baseline PSNR | ~23 dB | ~21 dB |
| ε | 25.0 dB | 22.0 dB |
| ρ | 3 | 5 |

**Warning (T3):** GAP-TV barely clears at 20.96 dB. A mismatch-aware solver is recommended.

### Mismatch-Only Spec: Tier T4 (Blind Calibration — Highest I-benchmark ρ)

Solver must estimate mismatch parameters from data, then reconstruct. Most practically valuable.

| Property | Value |
|----------|-------|
| omega_tier | disp_a1=0.04, dx=0.8, θ=0.12° |
| Input | Measurement + mask only (no mismatch params — solver must self-calibrate) |
| ε | 20.0 dB |
| ρ | 10 |
| Dataset | CAVE (32 scenes, 512×512×31 bands); spectrally resampled 31→28 bands (450–650 nm); synthetic mismatch applied at T4 parameters; fixed 10-scene eval set |

### Oracle-Assisted Spec: Tier T1 (Moderate Mismatch + Oracle — center I-bench)

The center I-benchmark for the oracle spec is at moderate mismatch — where oracle information is actually useful.

| Property | Value |
|----------|-------|
| omega_tier | H=256, N_bands=28, disp_a1=0.02, dx=0.5, dy=0.3 |
| Input | Measurement + mask + true Φ parameters |
| ε | 30.5 dB (epsilon_fn at this oracle + moderate-mismatch Ω) |
| δ | 3 |

### Mismatch Recovery by Solver

Not all solvers benefit equally from calibration:

| Solver | ρ (recovery %) | Why |
|--------|----------------|-----|
| PnP-HSICNN | 56.8% | Uses mask in forward model; benefits strongly from calibration |
| MST-L | 46.5% | Transformer partially compensates; moderate benefit |
| HDNet | 0% | Mask-oblivious architecture; calibration has zero effect |

**Strategy:** Use PnP-HSICNN for mismatch tiers. Avoid HDNet for T4 blind calibration.

### P-benchmark (Highest Reward Overall, ρ=50)

Tests generalization across the **full** declared Ω space. The solver must work across all combinations of H∈[64,2048], N_bands∈[8,128], noise_level∈[0.001,0.1], and mismatch dims within their declared bounds.

```
P-benchmark uses epsilon_fn(Ω) as threshold — not a fixed number.
Quality is evaluated across all three Tracks (see Track A/B/C details above):
  Track A: 4 strata by H×W; worst of 5 instances per stratum must pass ε
  Track B: median of 50 uniform Ω samples must pass ε at Ω_median
  Track C: mismatch degradation curve; φ swept 0→1 across 5 points
```

**Source dataset:** ICVL (200 scenes, 1392×1300×519 bands, BGU/Harvard, CC-BY-NC).

**Stitching for H×W > 1024:** Real CASSI deployments tile multiple sensor captures for large scenes (push-broom mosaic, tiled focal planes). The P-benchmark mirrors this: for target H or W > 1024, four ICVL scenes are tiled in a 2×2 arrangement (hard concatenation, no blending) and cropped to the target size. The seam at tile boundaries is a real spatial discontinuity — solvers that handle it score higher. ICVL at 1392×1300 per tile covers 2×2 → 2784×2600, sufficient for any target up to 2048×2048.

| Target H×W | Tile count | Source |
|---|---|---|
| [64, 1024] | 1 ICVL scene crop | No stitching |
| (1024, 2048] | 4 ICVL scenes (2×2 hard stitch) | Seam at tile boundary |

The `true_phi` for a stitched scene includes a `seam_map` (binary mask of tile boundaries) so oracle-assisted solvers can condition on it; mismatch-only solvers must infer or handle it blindly.

ρ=50 makes the P-benchmark pool weight 50× higher than the T1 nominal I-benchmark. A solver that passes the P-benchmark earns substantially more than all I-benchmarks combined.

---

## Complete Reward Summary (All Four Layers for CASSI)

```
┌─────────┬──────────────────────────────┬──────────────────────────────────────────────┐
│ Layer   │ One-time creation reward     │ Ongoing upstream royalties                   │
├─────────┼──────────────────────────────┼──────────────────────────────────────────────┤
│ L1      │ Reserve grant (DAO vote)     │ 5% of every L4 minting draw                 │
│Principle│ when S4 gate passes          │ 5% of every L4 usage fee                    │
│         │ No fixed formula             │ → If 1,000 solutions at 100 PWM each:       │
│         │                              │   5,000 PWM passively                       │
├─────────┼──────────────────────────────┼──────────────────────────────────────────────┤
│ L2      │ Reserve grant (DAO vote)     │ 10% of every L4 minting draw                │
│ spec.md │ when S4 gate passes          │ 10% of every L4 usage fee                   │
│         │ Requires d_spec ≥ 0.35       │ → If 250 solutions at 100 PWM each:         │
│         │                              │   2,500 PWM per spec                        │
├─────────┼──────────────────────────────┼──────────────────────────────────────────────┤
│ L3      │ Reserve grant (DAO vote)     │ 15% of every L4 minting draw                │
│Benchmark│ when S4 gate passes          │ 15% of every L4 usage fee                   │
│         │ Requires d_ibench ≥ 0.10     │ → If 250 solutions at 100 PWM each:         │
│         │                              │   3,750 PWM per benchmark                   │
├─────────┼──────────────────────────────┼──────────────────────────────────────────────┤
│ L4      │ N/A (no one-time grant)      │ Ranked draw from per-principle pool:        │
│Solution │                              │   AC: p × 55% (SP earns passively)          │
│         │                              │   CP: (1−p) × 55% (per job executed)        │
│         │                              │   Example: Rank 1, 1000 PWM pool, p=0.4:   │
│         │                              │   400 PWM draw → AC:66, CP:154              │
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
| Use MST-L or CST on T1 | Higher PSNR → Q ≈ 1.0 → larger pool share |
| Solve T3 moderate with PnP-HSICNN | ρ=56.8% recovery; demonstrates robustness |
| Solve T4 blind calibration | Highest I-benchmark ρ=10; strongest reputation signal |
| Attempt P-benchmark | ρ=50; largest pool weight; cross-claim I-benchmarks after |
| Be first solver in CASSI domain | Novelty multiplier ν_c is highest for first solutions |
| Submit across multiple resolutions | Convergence-based scoring (M2) rewards this |
| Use a novel solver architecture | Method-signature diversity (M5) rewards novelty |

### Recommended progression

| Stage | Task | Approx. reward (Rank 1, small pool) |
|-------|------|--------------------------------------|
| 1. Learn | T1 Nominal with GAP-TV | ~100 PWM |
| 2. Improve | T1 Nominal with MST-L or CST | ~160 PWM |
| 3. Challenge | T3 Moderate with PnP-HSICNN | ~200 PWM |
| 4. Calibrate | T4 Blind calibration | ~250 PWM |
| 5. Frontier | P-benchmark (full Ω range) | ~400 PWM + cross-claims |

---

## What You Cannot Do

- **Memorize benchmark outputs** — M1 generates test instances from an unmanipulable randomness source; you cannot predict which scenes you will be tested on.
- **Fake the certificate** — Every full node checks it in O(1); forging is mathematically infeasible.
- **Skip gates** — S3 convergence check catches solvers that produce good numbers without actually converging.
- **Game the quality score** — Worst-case scoring across K instances (M3) means one bad scene tanks your score.
- **Reuse someone else's solution** — The certificate commits your SP identity and solution hash; duplicates are detected.
- **Use mask-oblivious methods for T4** — HDNet (ρ=0%) cannot benefit from calibration; the protocol detects this.
- **Tamper with upstream hashes** — Changing any artifact (Principle, spec, benchmark) breaks the hash chain; all verifiers detect it.
- **Submit a near-duplicate spec** — d_spec < 0.15 is rejected outright; add an I-benchmark tier instead.

---

## Quick-Start Commands

```bash
# 1. Check available CASSI tasks
pwm-node benchmarks | grep cassi

# 2. Pre-check gates (free, no compute)
pwm-node verify cassi/mismatch_only_t1_nominal.yaml

# 3. Mine the center I-benchmark (nominal, ρ=1)
pwm-node mine cassi/mismatch_only_t1_nominal.yaml

# 4. Inspect your certificate
pwm-node inspect sha256:<your_cert_hash>

# 5. Check balance after 7-day challenge period
pwm-node balance

# 6. Mine moderate mismatch tier (ρ=5)
pwm-node mine cassi/mismatch_only_t3_moderate.yaml

# 7. Mine blind calibration tier (ρ=10, highest I-benchmark)
pwm-node mine cassi/mismatch_only_t4_blind.yaml

# 8. Mine oracle-assisted center I-benchmark (ρ=1, true Φ provided)
pwm-node mine cassi/oracle_t1_h64_nb8.yaml

# 9. Register as Solution Provider (SP) — after proving solution works locally
#    Include compute manifest so CPs know hardware requirements
pwm-node sp register \
  --entry-point solve.py \
  --share-ratio 0.40 \
  --min-vram-gb 8 \
  --expected-runtime-s 180 \
  --framework pytorch

# 10. Register as Compute Provider (CP)
pwm-node cp register --gpu A100 --vram 80
```

---

## Reference

| Topic | Where to find it |
|-------|------------------|
| CASSI Principle (#25) | `principle.md`, Section B (Compressive Imaging) |
| Four-layer pipeline | `pwm_overview1.md` §2 |
| Principle definition P=(E,G,W,C) | `pwm_overview1.md` §3 |
| L_DAG complexity score (κ₀=1000) | `pwm_overview1.md` §3 Primitive Decomposition |
| physics_fingerprint and spec_range | `pwm_overview1.md` §3 |
| Spec six-tuple S=(Ω,E,B,I,O,ε) | `pwm_overview1.md` §4 |
| epsilon_fn (AST-sandboxed) | `pwm_overview1.md` §4 The epsilon_fn |
| Spec distance formula (d_spec) | `pwm_overview1.md` §4 Spec Distance |
| P-benchmark vs. I-benchmark | `pwm_overview1.md` §5 |
| ibenchmark_range declaration | `pwm_overview1.md` §5 |
| Evaluation Tracks A/B/C | `pwm_overview1.md` §5 |
| M1-M6 anti-overfitting mechanisms | `pwm_overview1.md` §5 |
| SP/CP dual-role architecture | `pwm_overview1.md` §6 L4 Dual-Role |
| Ranked draws and T_k=15% | `pwm_overview1.md` §9 Ranked Draws |
| Reserve grants for L1/L2/L3 | `pwm_overview1.md` §9 Early L1/L2/L3 Creation |
| Token economics (82% minting pool) | `pwm_overview1.md` §9 Supply Distribution |
| Upstream royalty split 5/10/15/15% | `pwm_overview1.md` §10 |
| Two-stage security model | `pwm_overview1.md` §11 |
| Hierarchical primitives (143-leaf) | `primitives.md` |
