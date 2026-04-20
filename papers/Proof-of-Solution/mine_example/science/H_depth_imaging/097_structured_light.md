# Structured Light — Complete Four-Layer Walkthrough

**Principle #97: Structured Light**
Domain: Microscopy | Difficulty: Standard (delta=2) | Carrier: Photon

---

## The Four-Layer Pipeline for Structured Light

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
│  about Airy     │    │  for widefield  │    │  + baselines    │    │  + earn PWM     │
│  PSF +          │    │  fluorescence   │    │  + thresholds   │    │                 │
│  fluorophore    │    │  tasks          │    │                 │    │  (PoSol reward) │
│  density        │    │                 │    │                 │    │                 │
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

The seeds are raw domain knowledge — the physics of widefield fluorescence
microscopy expressed as a six-tuple:

```yaml
# ─── WIDEFIELD FLUORESCENCE SEED (Layer 1 input) ───
# Written by: domain expert (fluorescence microscopy researcher)
# Purpose: define the forward model and physics constraints

omega:
  description: "2D fluorophore density image on a sampled grid"
  spatial: [H, W]                    # spatial dimensions in pixels
  pixel_nm: pixel_size               # pixel spacing in object plane (nm)
  emission_nm: lambda_em             # fluorescence emission wavelength (nm)
  NA: numerical_aperture             # objective lens NA (dimensionless)

E:
  forward_model: "y(r) = [PSF(r) ⊛ f(r)] + n(r)"
  components:
    point_spread: "PSF = Airy(NA, λ_em), circularly symmetric, band-limited"
    accumulation: "Camera integrates photon counts over exposure τ"
    noise:        "n = n_Poisson(signal) + n_Gaussian(read)"
  DAG: "K.psf.airy → ∫.temporal"

B:
  nonnegativity:      "f(r) >= 0 (fluorophore density is nonnegative)"
  band_limit:         "F[f] supported within OTF cutoff k_c = 2·NA/λ_em"
  bounded_background: "Uniform dark offset b >= 0, sigma_bg << peak"

I:
  carrier: photon
  NA_range:             [0.4, 1.49]
  pixel_nm_range:       [30, 200]
  emission_nm_range:    [400, 800]
  noise_model:          poisson_gaussian
  peak_photons_range:   [50, 10000]

O:
  metrics: [PSNR, SSIM, resolution_nm]

epsilon:
  description: "Domain-level feasibility thresholds"
  PSNR_achievable:  ">= 30 dB for Nyquist-sampled images with SNR >= 20"
  resolution_limit: "Abbe diffraction limit: d_min = λ_em / (2·NA)"
```

### What S1-S4 discovers (the Principle)

Layer 1 runs Valid(B) = S1 ∧ S2 ∧ S3 ∧ S4 ∧ (δ ≥ δ_min) ∧ P1-P10 on the
seeds. S1-S4 extracts the **Principle P = (E, G, W, C)**:

```
┌────────────────────────────────────────────────────────────────────────────┐
│  STRUCTURED LIGHT PRINCIPLE  P = (E, G, W, C)                      │
│  Principle #97 in the PWM registry                                        │
│  sha256: <structured_light_principle_hash>  (immutable once committed)          │
├────────┬───────────────────────────────────────────────────────────────────┤
│   E    │ FORWARD MODEL                                                    │
│        │                                                                  │
│        │ y(r) = [PSF_Airy(r) ⊛ f(r)] + n(r)                               │
│        │                                                                  │
│        │ Physical chain:                                                  │
│        │   Fluorophore density f(r) ──→ PSF convolution (Airy) ──→        │
│        │   Detector accumulation ──→ Sensor readout y(r)                  │
│        │                                                                  │
│        │ Inverse problem: recover f ∈ R^{H×W} (non-negative) from         │
│        │ blurred noisy y ∈ R^{H×W}                                        │
│        │ Compression ratio: 1:1 (deconvolution, no dim reduction)         │
├────────┼───────────────────────────────────────────────────────────────────┤
│   G    │ DAG DECOMPOSITION  G = (V, A)                                    │
│        │ Directed acyclic graph where:                                    │
│        │   V = nodes (hierarchical primitives from the 12-root basis)    │
│        │   A = arcs (data dependencies between primitives)                │
│        │ Made explicit by S1 (dimensional consistency across nodes).      │
│        │                                                                  │
│        │ Hierarchical primitive notation: root.sub.subsub                 │
│        │   Level 1 (root): WHAT computation — cross-domain comparable    │
│        │   Level 2 (sub):  WHAT structure — determines complexity class  │
│        │   Level 3 (subsub): WHAT variant — affects conditioning/flow    │
│        │   (See primitives.md for the full 143-leaf hierarchy)            │
│        │                                                                  │
│        │ Widefield forward DAG:                                           │
│        │                                                                  │
│        │   [K.psf.airy] ──→ [∫.temporal]                                  │
│        │         │                  │                                     │
│        │    PSF blur (Airy)   Accumulate (camera + noise)                 │
│        │    NA-dependent      Poisson + Gaussian read                     │
│        │    band-limited      (sensor integration)                        │
│        │                                                                  │
│        │ V = {K.psf.airy, ∫.temporal}                                    │
│        │ A = {K.psf.airy → ∫.temporal}                                   │
│        │ |V| = 2,  |A| = 1,  n_c = 0 (no coupling)                      │
│        │                                                                  │
│        │ Node semantics (hierarchical decomposition):                     │
│        │   K.psf.airy:                                                    │
│        │     root K = kernel convolution                                 │
│        │     sub  psf = point-spread function                            │
│        │     subsub airy = Airy disk (circular band-limited kernel)      │
│        │     PSF(r) = [2·J₁(k_c·|r|) / (k_c·|r|)]²                       │
│        │     k_c = 2·NA/λ_em   (cutoff spatial frequency)                │
│        │                                                                  │
│        │   ∫.temporal:                                                    │
│        │     root ∫ = integrate / accumulate                             │
│        │     sub  temporal = over exposure time τ                        │
│        │     y = ∫₀^τ (signal + noise) dt   (camera integration)         │
│        │                                                                  │
│        │ Why the two G nodes are distinguishable:                         │
│        │   K.psf.airy: kernel structure, κ ≈ 15 (Nyquist-sampled at      │
│        │               NA=1.4), band-limited, shift-invariant             │
│        │   ∫.temporal: trivial linear accumulator, κ ≈ 1,                 │
│        │               Poisson+Gaussian noise is introduced here          │
│        │   Different root → different complexity class & structure        │
│        │                                                                  │
│        │ Cross-domain pattern: K.psf appears in any imaging system        │
│        │   with a finite point-response (widefield, confocal, SIM,        │
│        │   STED — different PSF geometries, same primitive category).     │
│        │                                                                  │
│        │ L_DAG = (|V|-1) + max(0, log₁₀(κ_sys/κ₀)) + n_c                 │
│        │       = 1 + max(0, log₁₀(15/1000)) + 0                          │
│        │       = 1 + 0 + 0 = 1.0     (κ₀ = 1000 reference;                │
│        │                               κ_sys < κ₀ ⇒ log term floors at 0) │
│        │                                                                  │
│        │ n_c = number of coupling constraints in the forward physics      │
│        │   DAG — cross-edges or shared-state dependencies between         │
│        │   sub-operators.                                                 │
│        │   n_c = 0 here: K.psf → ∫ is a pure sequential pipeline;         │
│        │   no sub-operator feeds back into or jointly constrains          │
│        │   a prior node. (Regularized solvers like TV or ADMM add         │
│        │   coupling in L4, not in L1.)                                    │
│        │                                                                  │
│        │ Tier: textbook (δ = 1)                                           │
├────────┼───────────────────────────────────────────────────────────────────┤
│   W    │ WELL-POSEDNESS CERTIFICATE                                       │
│        │                                                                  │
│        │ Existence: YES — bounded pseudo-inverse exists                   │
│        │   (band-limited PSF has non-zero OTF over its support;           │
│        │    Wiener filter achieves finite error for SNR > 0)              │
│        │                                                                  │
│        │ Uniqueness: YES within OTF support                               │
│        │   (spatial frequencies above k_c are zeroed by the PSF;          │
│        │    recovery is unique on frequencies |k| ≤ k_c; high-freq        │
│        │    detail above cutoff is irrecoverable without priors)          │
│        │                                                                  │
│        │ Stability: CONDITIONAL — depends on sampling and SNR             │
│        │   Sub-operator κ_∫ ≈ 1 (∫.temporal adds noise but no             │
│        │                         conditioning cost)                       │
│        │   Sub-operator κ_K ≈ 15 (K.psf.airy, Nyquist-sampled NA=1.4)    │
│        │   Compound κ_sys ≈ 15 (well-sampled) / ≈ 80 (under-sampled)     │
│        │   Effective κ_eff ≈ 5  (Wiener regularization at typical SNR)   │
│        │                                                                  │
│        │ Mismatch model (2 parameters as Ω dimensions):                   │
│        │   y_observed = K_{Δz} · f + σ_bg + n                             │
│        │   where Δz    = axial defocus (introduces OTF phase error)       │
│        │         σ_bg  = uniform background offset (fraction of peak)     │
│        │   Nominal: Δz = 0, σ_bg = 0                                      │
│        │   Mismatch bounds: Δz ∈ [0, 1500] nm, σ_bg ∈ [0, 0.10]           │
│        │                                                                  │
│        │ Note: widefield has FEWER mismatch dimensions than cassi         │
│        │ (cassi uses a 5-param shear+binary model). Fewer nuisance        │
│        │ parameters ⇒ easier blind calibration at T4.                     │
├────────┼───────────────────────────────────────────────────────────────────┤
│   C    │ CONVERGENCE / METRICS                                            │
│        │                                                                  │
│        │ Primary metric: e = PSNR (dB) — normalized MSE on intensity     │
│        │ Secondary:      SSIM — structural similarity ∈ [0,1]            │
│        │ Derived:        resolution_nm — FWHM of recovered PSF estimate  │
│        │                                                                  │
│        │ Convergence rate: q = 2.0 (Richardson-Lucy on Poisson            │
│        │                           likelihood exhibits O(1/k²)            │
│        │                           convergence near the MLE)              │
│        │                                                                  │
│        │ Witness set T = {residual_norm, fitted_rate, K_resolutions}      │
│        │   residual_norm = ||y − K·f̂|| / ||y||                           │
│        │   fitted_rate   = empirical q extracted from iterate errors      │
│        │   K_resolutions = successive resolution estimates at grid        │
│        │                   refinements (stability witness)                │
└────────┴───────────────────────────────────────────────────────────────────┘
```

### Physics fingerprint

Each Principle carries an immutable `physics_fingerprint` block committed with the Principle hash. It enables automatic deduplication across the registry (Jaccard distance on fingerprint sets):

```yaml
physics_fingerprint:
  carrier:            photon
  sensing_mechanism:  fluorescence_widefield
  integration_axis:   temporal
  problem_class:      linear_inverse_deconvolution
  noise_model:        poisson_gaussian
  solution_space:     2D_intensity
  primitives:
    - K.psf.airy
    - "∫.temporal"
```

**Deduplication example**: Widefield vs. Confocal (point-scanning PSF, different subsub leaf) → d_principle ≈ 0.28 (Related — contributor may stake a new Principle). Widefield vs. CASSI → d_principle ≈ 0.72 (Distinct — proceeds ✓).

### Spec range declaration

The Principle creator declares a `spec_range` block at registration. Only specs within this range earn protocol minting (A_k) and per-principle treasury (T_k). Specs outside the range are accepted but funded from contributor bounty only (B_k).

```yaml
spec_range:
  center_spec:
    problem_class:     fluorescence_deconvolution
    forward_operator:  airy_psf_convolution
    input_format:      measurement_only   # no oracle parameters
    omega:
      H:            512
      W:            512
      pixel_nm:     65
      emission_nm:  525
      NA:           1.4
      peak_photons: 1000
      dz_nm:        0.0      # defocus mismatch (nm)
      sigma_bg:     0.0      # background offset (fraction of peak)
    epsilon_fn_center: "30.0 dB PSNR"

  allowed_forward_operators:
    - airy_psf_convolution
    - gaussian_psf_approx    # when NA << 1 and apodization is significant

  allowed_problem_classes:
    - fluorescence_deconvolution
    - blind_deconvolution
    - background_estimation

  allowed_omega_dimensions:
    - H
    - W
    - pixel_nm
    - emission_nm
    - NA
    - peak_photons
    - dz_nm              # defocus (mismatch)
    - sigma_bg           # background offset (mismatch)

  omega_bounds:
    H:            [128, 4096]
    W:            [128, 4096]
    pixel_nm:     [30,  200]
    emission_nm:  [400, 800]
    NA:           [0.4, 1.49]
    peak_photons: [50,  10000]
    dz_nm:        [0.0, 1500.0]
    sigma_bg:     [0.0, 0.10]

  epsilon_bounds:
    psnr_db: [20.0, 45.0]
```

### What S1-S4 checks at Layer 1

| Gate | What it checks on the widefield seeds | Result |
|------|----------------------------------------|--------|
| **S1** | Dimensions: PSF grid matches spatial grid; OTF cutoff k_c = 2·NA/λ_em within Nyquist band at declared pixel size; DAG nodes K.psf.airy and ∫.temporal are dimensionally consistent | PASS |
| **S2** | Well-posedness: OTF is non-zero over its support ⇒ bounded pseudo-inverse via Wiener filter; Tikhonov regularization tames high-frequency noise amplification outside the support | PASS |
| **S3** | Convergent solver exists: Richardson-Lucy monotonically improves Poisson likelihood; ADMM with TV prior converges with rate bounds known in the literature | PASS |
| **S4** | Error is bounded: PSNR computable on recovered intensity; q=2.0 convergence rate confirmed by multi-resolution witness K_resolutions at three grid refinements | PASS |

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

Closed-form seed reward + numeric substitution per STYLE_NOTES §4:

```
R_L1_seed = R_base × φ(t) × δ
          = 200 × 1.0 × 1 = 200 PWM (one-time, at genesis)
```

### The Principle is now immutable

Once committed on-chain as `sha256:<structured_light_principle_hash>`, the Structured Light Principle **never changes**. All downstream spec.md files, benchmarks, and solutions reference this hash. Updating the physics — for example, extending to anisotropic PSFs or 3D z-stack forward models — means creating Principle v2 (a new hash), not modifying v1. The registry treats immutability as a first-class invariant.

---

## Layer 2: Principle + S1-S4 → spec.md (Task Design)

### Who does this?

A **task designer** (can be the same domain expert or anyone else). They take the Structured Light Principle and design specific, solvable tasks — concrete spec.md files that pin down grid size, pixel pitch, numerical aperture, emission wavelength, noise model, and tier-structured mismatch ranges. Accepted specs earn a **Reserve grant** (DAO vote) on submission plus ongoing upstream royalties on all future L4 events that reference the spec.

### What the task designer writes

Each spec.md is a concrete instantiation of the Principle as a flat **six-tuple S = (Ω, E, B, I, O, ε) + principle_ref**. Items that live elsewhere:

| Moved to Principle | Moved to Benchmark (L3) |
|--------------------|------------------------|
| `difficulty` (L_DAG, δ, tier) | `expert_baseline`, `evaluator` |
| `primitives`, `carrier`, `modality` | quality scoring table |
| `quality_metrics` (C field) | per-solver metrics |

**Key insight: one spec, multiple I-benchmarks.** The widefield measurement-only spec covers all mismatch severity levels — the solver input format never changes (raw blurred image only). Each mismatch severity (nominal / low / moderate / blind) is a separate I-benchmark tier within the same spec, not a separate spec. The oracle scenario (solver given true NA, emission, defocus, background as input) requires a distinct spec because the input format changes.

**Two natural specs under this Principle:**

| Spec | Solver input | Ω dimensions | Center I-bench | Purpose |
|------|-------------|--------------|----------------|---------|
| #1 Mismatch-only | measurement only | H, W, pixel_nm, emission_nm, NA, peak_photons + 2 mismatch dims | Nominal (Δz=0, σ_bg=0, ρ=1) | Deconvolution under unknown calibration error |
| #2 Oracle-assisted | measurement + true_phi | H, W, pixel_nm, peak_photons (no mismatch, no NA/emission) | H=128, pixel_nm=100, peak=500 (ρ=1) — tiers scale by H/peak_photons | Upper bound — solver knows exact PSF |

```
Structured Light Principle (sha256:<principle_hash>)
    │
    ├──→ spec.md #1: Mismatch-only       sha256:<spec1_hash>
    │       │   Ω = ranges; center I-bench at nominal (no mismatch)
    │       ├──→ I-bench T1: Nominal (ρ=1)           ← center_ibenchmark
    │       ├──→ I-bench T2: Low mismatch (ρ=2)
    │       ├──→ I-bench T3: Moderate mismatch (ρ=4)
    │       ├──→ I-bench T4: Blind/severe (ρ=10)
    │       └──→ P-benchmark: Full Ω range (ρ=50)
    │
    └──→ spec.md #2: Oracle-assisted     sha256:<spec2_hash>
            │   Ω = {H, W, pixel_nm, peak_photons} — no mismatch, no NA/λ
            │   center I-bench at small/easy system params (ρ=1)
            ├──→ I-bench T1: Small (H=128, pixel=100 nm, peak=500, ρ=1)  ← center_ibenchmark
            ├──→ I-bench T2: Medium (H=512, pixel=65 nm, peak=1000, ρ=3)
            ├──→ I-bench T3: Large (H=2048, pixel=32 nm, peak=5000, ρ=5)
            └──→ P-benchmark: Full Ω range (ρ=50)
```

> **Ω in spec.md is always a range, not a fixed grid.** The spec declares the full parameter space the solver and P-benchmark must cover. The I-benchmark is pinned to a single `omega_tier` point within that range — that is the "center" the spec creator defines in `ibenchmark_range.center_ibenchmark`.

#### spec.md #1: Mismatch-Only (Canonical Widefield Spec)

```yaml
# structured_light/fluocells_mismatch_only.yaml
# Layer 2 output — references the Structured Light Principle

principle_ref: sha256:<structured_light_principle_hash>   # ← links to Layer 1

# Ω = full parameter RANGE (not a fixed grid)
omega:
  H:             [128, 4096]      # spatial height range (pixels)
  W:             [128, 4096]      # spatial width  range (pixels)
  pixel_nm:      [30, 200]        # pixel size in object plane (nm)
  emission_nm:   [400, 800]       # fluorescence emission wavelength (nm)
  NA:            [0.4, 1.49]      # objective numerical aperture
  peak_photons:  [50, 10000]      # peak signal strength
  # Mismatch dims: zero = ideal, non-zero = calibration error
  dz_nm:         [0.0, 1500.0]    # axial defocus (nm)
  sigma_bg:      [0.0, 0.10]      # uniform background offset (fraction of peak)

E:
  forward:  "y(r) = [PSF_Airy(r; NA, λ_em, Δz) ⊛ f(r)] + σ_bg + n(r)"
  operator: widefield_fluorescence_forward
  primitive_chain: "K.psf.airy → ∫.temporal"
  inverse: "recover f (H×W, non-negative) from single blurred noisy snapshot y (H×W)"

B:
  nonnegativity: true
  band_limit:    true    # f approximately band-limited by OTF cutoff k_c

I:
  strategy: zero_init

O: [PSNR, SSIM, resolution_nm, residual_norm, convergence_curve]

# epsilon_fn maps any Ω point → minimum acceptable PSNR
epsilon_fn: "22.0 + 2.0 * log2(H / 128) + 1.5 * log10(peak_photons / 50)"

input_format:
  measurement: float32(H, W)
  psf_hint:    optional_float32(K, K)   # if PSF calibration known; else solver fits
  # No mismatch params — solver must infer dz, sigma_bg, or be robust
output_format:
  intensity:   float32(H, W)

baselines:
  - Richardson-Lucy   # method_sig: I+M (iterative Poisson MLE)
  - Wiener            # method_sig: L+R (linear + Tikhonov regularization)
  - CARE-UNet         # method_sig: L+N (learned denoiser, domain-adapted)

# ibenchmark_range — center I-bench at nominal Ω (all mismatch = 0)
ibenchmark_range:
  center_ibenchmark:
    rho: 1
    omega_tier:
      H:             512
      W:             512
      pixel_nm:      65
      emission_nm:   525
      NA:            1.4
      peak_photons:  1000
      dz_nm:         0.0        # ← nominal center: zero mismatch
      sigma_bg:      0.0
    epsilon: 30.0                # fixed ε at this exact Ω tier point

  tier_bounds:
    H:             [128, 2048]
    W:             [128, 2048]
    pixel_nm:      [30, 200]
    emission_nm:   [400, 800]
    NA:            [0.4, 1.49]
    peak_photons:  [50, 10000]
    dz_nm:         [0.0, 1500.0]
    sigma_bg:      [0.0, 0.10]

  proximity_threshold: 0.10   # τ — new I-bench must differ by > 10% in ≥1 dim
```

**epsilon_fn example:**

```
At Ω = {H=256, peak_photons=200}:
  ε = 22.0 + 2.0 × log2(256/128) + 1.5 × log10(200/50)
    = 22.0 + 2.0 + 0.90 = 24.90 dB

At the center I-bench Ω = {H=512, peak_photons=1000, dz_nm=0}:
  ε ≈ 30.0 dB  ← this is what ibenchmark_range.center_ibenchmark.epsilon records
```

The `epsilon_fn` is an AST-sandboxed Python expression. For each I-benchmark, it is evaluated at that benchmark's fixed `omega_tier` to produce the single-value `epsilon` stored in that I-benchmark's `thresholds.yaml`. The P-benchmark uses the full `epsilon_fn` function across all Ω samples.

#### spec.md #2: Oracle-Assisted (Separate Spec — Different Input Format)

```yaml
# structured_light/fluocells_oracle_assisted.yaml

principle_ref: sha256:<structured_light_principle_hash>

# Ω contains only intrinsic system parameters — NO mismatch dims
# Calibration parameters (NA, emission, dz, sigma_bg) are INPUTS (true_phi),
# not Ω dimensions
omega:
  H:             [128, 4096]
  W:             [128, 4096]
  pixel_nm:      [30, 200]
  peak_photons:  [50, 10000]

E:
  forward: "y = PSF(r; true_phi) ⊛ f + true_phi.sigma_bg + n"
  operator: widefield_fluorescence_forward_oracle

B:
  nonnegativity: true
  band_limit:    true

I:
  strategy: zero_init

O: [PSNR, SSIM, resolution_nm, residual_norm]

epsilon_fn: "25.0 + 2.0 * log2(H / 128) + 1.5 * log10(peak_photons / 50)"
# Same structure as mismatch spec but higher baseline —
# solver has true calibration, so stricter threshold is appropriate

input_format:
  measurement:  float32(H, W)
  true_phi:     dict    # ← oracle input: {NA, emission_nm, dz_nm, sigma_bg}
  # This additional input field makes this a DIFFERENT spec from mismatch-only
output_format:
  intensity:    float32(H, W)

baselines:
  - Richardson-Lucy-oracle   # method_sig: I+M with true PSF
  - Wiener-oracle            # method_sig: L+R with true OTF
  - CARE-UNet-oracle         # method_sig: L+N conditioned on true_phi

# ibenchmark_range — center I-bench at small/easy system params
# No mismatch dims — mismatch is in true_phi input, not in Ω
# I-benchmark difficulty scales with H, pixel_nm, peak_photons (larger H / smaller pixel / fewer photons = harder)
ibenchmark_range:
  center_ibenchmark:
    rho: 1
    omega_tier:
      H:             128       # small spatial size → easy
      W:             128
      pixel_nm:      100       # coarse sampling → easy
      peak_photons:  500
    epsilon: 33.0               # ε at center Ω (higher than mismatch spec — oracle advantage)

  tier_bounds:
    H:             [128, 2048]
    W:             [128, 2048]
    pixel_nm:      [30, 200]
    peak_photons:  [50, 10000]
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

#### Widefield Worked Example — Spec #1 (Mismatch-only) vs Spec #2 (Oracle-assisted)

**d_structural:**

| Feature | Spec #1 Mismatch-only | Spec #2 Oracle-assisted | Shared |
|---|---|---|---|
| operator_class | airy_psf_convolution | airy_psf_convolution | ✓ |
| function_space | L2_spatial | L2_spatial | ✓ |
| modulus_of_continuity | Lipschitz | Lipschitz | ✓ |
| convergence_order_tier | O(1/k²) | O(1/k²) | ✓ |
| condition_number_tier | **medium** (κ_eff≈50 with mismatch) | **low** (κ_eff≈5, oracle) | ✗ |
| certificate_procedure | S1-S4_residual | S1-S4_residual | ✓ |
| noise_model | poisson_gaussian | poisson_gaussian | ✓ |
| observable | PSNR, SSIM, resolution_nm | PSNR, SSIM, resolution_nm | ✓×3 |
| discr_class | Richardson-Lucy, Wiener, CARE-UNet, blind-RL, transformer | + operator_aware | ✓×5, ✗×1 |
| omega_dim | H, W, pixel_nm, emission_nm, NA, peak_photons + 2 mismatch dims | H, W, pixel_nm, peak_photons only | ✓×4, ✗×4 |

```
|F1| = 7 scalars + 3 obs + 5 discr + 8 omega = 23
|F2| = 7 scalars + 3 obs + 6 discr + 4 omega = 20
|F1 ∩ F2| = 6 + 3 + 5 + 4 = 18
|F1 ∪ F2| = 23 + 20 − 18 = 25

d_structural = 1 − 18/25 = 0.28
```

**d_omega:**

Shared dims: H, W, pixel_nm, peak_photons (both specs declare identical ranges)

```
H:            [128, 4096]  vs [128, 4096]  →  IoU = 1.0
W:            [128, 4096]  vs [128, 4096]  →  IoU = 1.0
pixel_nm:     [30,  200]   vs [30,  200]   →  IoU = 1.0
peak_photons: [50,  10000] vs [50,  10000] →  IoU = 1.0

d_omega = 1 − (1/4) × (1.0+1.0+1.0+1.0) = 0.0
```

The 4 dims unique to spec #1 (emission_nm, NA, dz_nm, sigma_bg) are not shared →
not counted in IoU. Their absence is captured by d_structural (omega_dim names differ).

**d_epsilon:**

```
PSNR: ε̄_1 ≈ 28.0 dB,  ε̄_2 ≈ 32.0 dB
  sota ≈ 38 dB,  floor ≈ 20 dB
  δ_ε(PSNR) = |28.0 − 32.0| / 18.0 = 0.22

SSIM: ε̄_1 ≈ 0.85,  ε̄_2 ≈ 0.90
  sota ≈ 0.98,  floor ≈ 0.60
  δ_ε(SSIM) = |0.85 − 0.90| / 0.38 = 0.13

resolution_nm: ε̄_1 ≈ 230 nm,  ε̄_2 ≈ 200 nm    (smaller is better)
  sota ≈ 150 nm,  floor ≈ 400 nm
  δ_ε(res) = |230 − 200| / 250 = 0.12

d_epsilon = (0.22 + 0.13 + 0.12) / 3 ≈ 0.157
```

**Combined:**

```
d_spec = 0.50×0.28 + 0.30×0.0 + 0.20×0.157
       = 0.140 + 0.000 + 0.031
       = 0.17  →  "Similar" band (0.15–0.35)
```

The oracle spec is accepted (d_spec > 0.15) but with **reduced ν_c** (B_k only unless within
the Principle's `spec_range`). It qualifies as a distinct spec — not an I-benchmark — because
the input_format changes (solver receives `true_phi`).

---

#### Why mismatch severity variants are I-benchmarks, not separate specs

Input format is identical (raw measurement only). Only the Ω tier *values* change
(dz_nm, sigma_bg). d_spec ≈ 0.10 (omega_dim names are the same, only ranges differ;
ranges are excluded from d_structural) → near-duplicate → **rejected as spec; submit
as I-benchmark tier instead**.

---

| d_spec | Label | Action | ν_c multiplier |
|--------|-------|--------|----------------|
| < 0.15 | Near-duplicate | **Rejected** — submit as I-benchmark instead | — |
| 0.15–0.35 | Similar | Accepted, B_k only | Reduced |
| 0.35–0.65 | Related | Accepted, A_k + T_k eligible | Normal |
| > 0.65 | Novel | Accepted, A_k + T_k eligible | Enhanced |

### What S1-S4 checks at Layer 2

Each spec.md is validated against the Structured Light Principle:

| Gate | What it checks | Widefield spec result |
|------|----------------|-----------------------|
| **S1** | spec's Ω range [H∈128–4096, NA∈0.4–1.49, pixel∈30–200 nm] is consistent with the Principle's spatial + optical structure; pixel size satisfies Nyquist at OTF cutoff k_c = 2·NA/λ_em for the tightest configuration | PASS |
| **S2** | spec's parameter bounds remain within the Principle's well-posedness regime; κ_eff < 200 across Ω for Wiener-regularized inverse; mismatch bounds [Δz ≤ 1500 nm, σ_bg ≤ 0.1] preserve existence | PASS |
| **S3** | For all Ω in the declared range, at least one solver converges (Richardson-Lucy at O(1/k²)); epsilon_fn hardness rule is satisfied monotonically in H and peak_photons | PASS |
| **S4** | epsilon_fn thresholds are feasible per the Principle's error bounds; expert baselines (Wiener, Richardson-Lucy) do not universally pass across the full Ω range — headroom exists for improved solvers | PASS |

### Layer 2 reward

```
L2 spec.md creation:
  One-time:  Reserve grant (DAO vote) when S4 gate passes
             Requires d_spec ≥ 0.35 to earn A_k + T_k (in-range)
             No fixed formula — size ∝ expected L4 activity
  Ongoing:   10% of every L4 minting draw under this spec
             10% of every L4 usage fee under this spec
```

Closed-form seed reward + numeric substitution per STYLE_NOTES §4:

```
R_L2_seed = 150 × φ(t) × 0.70
          = 150 × 1.0 × 0.70 = 105 PWM (designer, one-time at acceptance)
        + 15% upstream royalty → Principle author (L1)
```

### The spec.md is now immutable

Once committed on-chain as `sha256:<widefield_spec_hash>`, the spec **never changes**. Miners know exactly what thresholds they must meet. No moving targets. Bug fixes to the spec yaml (typos, unit corrections) require a new spec ID; the old one is deprecated but its hash stays in the chain so certificates referencing it remain verifiable.

---

## Layer 3: spec.md + Principle + S1-S4 → Benchmark (Data + Baselines)

### Who does this?

A **data engineer** or **benchmark builder** (can be the task designer, a microscopy core facility, or someone else). They create the test data — real or simulated widefield images with ground-truth fluorophore distributions — run baseline solvers, and establish quality floors. Accepted benchmarks earn a **Reserve grant** (DAO vote) on submission plus ongoing upstream royalties on every L4 certificate that references them.

### P-benchmark vs. I-benchmark

Every spec has exactly **one P-benchmark** and one or more **I-benchmarks**:

| Type | Ω coverage | ρ weight | Quality threshold | Purpose |
|------|-----------|----------|-------------------|---------|
| **P-benchmark** | Full Ω range (parametric) | 50 (highest) | `epsilon_fn(Ω)` function | Tests generalization across entire parameter space |
| **I-benchmark** | Single Ω tier point | 1/2/4/10 | Fixed ε at that Ω | Tests performance at one specific difficulty level |

**Widefield I-benchmark tiers — mismatch-only spec** (each is a single fixed `omega_tier` point):

| Tier | omega_tier (fixed Ω point) | mismatch severity | ρ | ε (from epsilon_fn at that Ω) |
|------|---------------------------|------------------|----|-------------------------------|
| T1 (Nominal) | H=512, NA=1.4, pixel=65, emit=525, peak=1000, dz=0, σ_bg=0 | None — calibrated | 1 | 30.0 dB |
| T2 (Low) | …, dz=200 nm, σ_bg=0.02 | Small drift | 2 | 28.0 dB |
| T3 (Moderate) | …, dz=600 nm, σ_bg=0.05 | Typical hardware | 4 | 25.5 dB |
| T4 (Blind) | …, dz=1200 nm, σ_bg=0.08 | Large, unknown to solver | 10 | 22.0 dB |

**Widefield I-benchmark tiers — oracle-assisted spec** (Ω = system params only; mismatch is in true_phi input, not omega_tier):

| Tier | omega_tier (system params only) | ρ | ε |
|------|---------------------------------|----|---|
| T1 | H=128, pixel=100 nm, peak=500 | 1 | 33.0 dB |
| T2 | H=512, pixel=65 nm, peak=1000 | 3 | 35.0 dB |
| T3 | H=2048, pixel=32 nm, peak=5000 | 5 | 37.0 dB |

**I-benchmark distance gate:** A new I-benchmark whose `omega_tier` point is within τ=0.10 of any existing I-benchmark in every Ω dimension is rejected as a near-duplicate. The proximity is measured as a fraction of each dimension's declared `tier_bounds` range.

### ibenchmark_range (declared inside the spec, repeated here for reference)

The `ibenchmark_range` block is part of the spec.md (shown in full in the spec above). It tells the protocol which Ω tier points earn A_k + T_k. Key elements:

| Field | Purpose |
|-------|---------|
| `center_ibenchmark` | The spec creator's canonical I-benchmark — a single fixed `omega_tier` point + `epsilon` (quality threshold at that Ω, from `epsilon_fn(omega_tier)`) + `rho` (benchmark pool weight ρ ∈ {1,2,4,10}). Contributors add higher-ρ I-benchmarks around this center. |
| `tier_bounds` | Which Ω values are in-range for protocol funding (A_k + T_k) |
| `proximity_threshold` | τ=0.10 — new I-bench must differ by > 10% of the declared range in ≥1 Ω dimension |

**Widefield mismatch-only spec center** (T1, nominal):

```yaml
center_ibenchmark:
  rho: 1
  omega_tier: {H: 512, W: 512, pixel_nm: 65, emission_nm: 525,
               NA: 1.4, peak_photons: 1000,
               dz_nm: 0.0, sigma_bg: 0.0}
  epsilon: 30.0     # ε = epsilon_fn evaluated at this exact Ω tier point
```

**Widefield oracle-assisted spec center** (T1, system params only — no mismatch in Ω):

```yaml
center_ibenchmark:
  rho: 1
  omega_tier: {H: 128, W: 128, pixel_nm: 100, peak_photons: 500}
  epsilon: 33.0     # higher ε than mismatch spec — oracle advantage
```

The two specs have **different Ω dimensions**: the mismatch spec's Ω has 8 dimensions (6 system + 2 mismatch); the oracle spec's Ω has only 4 system dimensions. Mismatch values (NA, emission_nm, dz_nm, sigma_bg) in the oracle spec are instance-level `true_phi` inputs — they vary per instance but are not Ω coordinates, so they do not appear in `omega_tier` or `tier_bounds`.

### What the benchmark builder creates

Layer 3 outputs a **complete, self-contained directory** — hash-committed and immutable once published. The 20 pre-built dev instances are ready to use directly. All 6 anti-overfitting mechanisms (M1-M6) are embedded as concrete files.

```
benchmark_structured_light_mismatch_only_t1_nominal/   ← I-benchmark T1
│                                                 omega_tier = {H:512, NA:1.4, pixel:65,
│                                                               emit:525, peak:1000,
│                                                               dz:0, sigma_bg:0}
│                                                 (grid sizes come from omega_tier, not the spec)
├── manifest.yaml              # dataset identity + immutability hashes
│
├── instances/                  # 20 READY-TO-USE dev instances
│   ├── dev_001/
│   │   ├── input.npz          #   { "measurement": (512,512),
│   │   │                      #     "psf_hint":    (65,65),    # optional
│   │   │                      #     "emission_nm": 525 }
│   │   ├── ground_truth.npz   #   { "intensity": (512,512) }
│   │   └── params.yaml        #   full Ω instance: H=512, NA=1.4, pixel=65, dz=0, ...
│   ├── dev_002/ … dev_020/
│
├── baselines/                  # expert solutions (M5: method diversity)
│   ├── richardson_lucy/
│   │   ├── solution.npz       #   reconstructed intensity maps
│   │   ├── metrics.yaml       #   per-instance PSNR/SSIM/resolution_nm
│   │   └── method.yaml        #   method_sig: "I+M" (iterative Poisson MLE)
│   ├── wiener/
│   │   ├── metrics.yaml       #   mean_PSNR: 30.5, worst_PSNR: 29.2
│   │   └── method.yaml        #   method_sig: "L+R" (linear + Tikhonov)
│   └── care_unet/
│       ├── metrics.yaml       #   mean_PSNR: 35.8, worst_PSNR: 34.1
│       └── method.yaml        #   method_sig: "L+N" (learned denoiser)
│
├── scoring/                    # deterministic evaluation (M3: worst-case)
│   ├── score.py               #   per-scene PSNR, SSIM, resolution_nm
│   ├── thresholds.yaml        #   epsilon at this Ω tier point
│   └── worst_case.py          #   Q = f(worst_PSNR across 20 scenes)
│
├── convergence/               # M2: convergence-based scoring
│   ├── check_convergence.py   #   verifies O(1/k²) rate across resolutions
│   └── resolutions.yaml       #   spatial: [128, 256, 512, 1024]
│
├── generator/                  # M1: parameterized random instantiation
│   ├── generate.py            #   deterministic G(θ), seeded by hash
│   ├── params.yaml            #   scene diversity params (cell density, fluorophore dist.)
│   ├── instantiate.py         #   G(SHA256(h_sub||k)) at submission time
│   └── requirements.txt
│
├── adversarial/               # M4: community adversarial testing
│   ├── submit_adversarial.py
│   └── adversarial_log.yaml
│
├── gates/                      # M6: S1-S4 checks embedded
│   ├── check_s1.py            #   dims: (512,512) matches spec grid
│   ├── check_s2.py            #   OTF non-zero over support per Principle
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
M5  Method-sig diversity    baselines/*/method.yaml (I+M vs L+R vs L+N earn novelty bonus)
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

Divide Ω into 4 strata by primary difficulty dimension (H×W for widefield):

| Stratum | H×W range | Representative difficulty |
|---|---|---|
| S1 small   | H×W ≤ 256²   | Easy — fits in GPU memory trivially |
| S2 medium  | 256² < H×W ≤ 512²  | Standard — typical deployment size |
| S3 large   | 512² < H×W ≤ 1024² | Hard — memory pressure, long runtime |
| S4 x-large | H×W > 1024²  | Very hard — stitched fields of view, boundary effects |

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

**Widefield mismatch sweep (5 points):**

| φ | dz_nm | sigma_bg |
|---|---|---|
| 0.00 | 0    | 0.000 |
| 0.25 | 375  | 0.025 |
| 0.50 | 750  | 0.050 |
| 0.75 | 1125 | 0.075 |
| 1.00 | 1500 | 0.100 |

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
# benchmark_structured_light_mismatch_only_t1_nominal/manifest.yaml

benchmark_id:    "structured_light_mismatch_only_t1_nominal_v1"
type:            "I-benchmark"
spec_ref:        "sha256:<structured_light_spec1_hash>"       # mismatch-only spec
principle_ref:   "sha256:<structured_light_principle_hash>"
# omega_tier: the single fixed Ω point this I-benchmark tests
# (grid dimensions H=512, NA=1.4 come from here — NOT from the spec)
omega_tier:
  H:             512
  W:             512
  pixel_nm:      65
  emission_nm:   525
  NA:            1.4
  peak_photons:  1000
  dz_nm:         0.0
  sigma_bg:      0.0
rho:             1                           # ρ=1 pool weight for nominal tier
epsilon:         30.0                        # epsilon_fn evaluated at this omega_tier
dataset_hash:    "sha256:<structured_light_dataset_hash>"
generator_hash:  "sha256:<structured_light_gen_hash>"
created:         "2026-04-19T00:00:00Z"
num_dev_instances: 20
num_baselines:     3
data_format:      "npz"
mechanisms:       [M1, M2, M3, M4, M5, M6]
```

#### scoring/thresholds.yaml (from epsilon_fn at this Ω tier)

```yaml
# epsilon_fn evaluated at T1 nominal Ω point (H=512, peak_photons=1000, no mismatch)
PSNR_min:     30.0     # primary metric PSNR ≥ 30 dB
SSIM_min:     0.85
resolution_nm_max: 230 # FWHM of recovered PSF ≤ 230 nm (Abbe-limited)
residual_max: 0.05     # ||y - PSF ⊛ f̂|| / ||y||

quality_scoring:
  metric: worst_psnr           # M3: worst scene determines Q
  thresholds:
    - {min: 36.0, Q: 1.00}
    - {min: 33.0, Q: 0.90}
    - {min: 30.0, Q: 0.80}
    - {min: 28.0, Q: 0.75}    # floor — always ≥ 0.75
```

**T3 Moderate mismatch I-benchmark** thresholds (same spec, different Ω tier):

```yaml
# epsilon_fn evaluated at T3 Ω point (dz_nm=600, sigma_bg=0.05)
PSNR_min:     25.5     # lower threshold — mismatch degrades quality
SSIM_min:     0.72
residual_max: 0.08     # higher tolerance for mismatch scenario
```

### What S1-S4 checks at Layer 3

The benchmark is validated against **both** the spec.md and the Principle:

| Gate | What it checks | Widefield benchmark result |
|------|----------------|-----------------------------|
| **S1** | `instances/dev_*/input.npz` shape (512,512) and `ground_truth.npz` shape (512,512) match spec's Ω dimensions; emission_nm=525 within spec range [400,800]; pixel=65 nm satisfies Nyquist at NA=1.4 | PASS |
| **S2** | Problem defined by this data + Principle has bounded inverse; OTF cutoff k_c = 2·NA/λ = 2·1.4/525e-9 ≈ 5.3×10⁶ m⁻¹ is within the Principle's well-posed regime (`gates/check_s2.py`) | PASS |
| **S3** | Richardson-Lucy residual decreases monotonically across iterations; `convergence/check_convergence.py` confirms O(1/k²) rate at 4 resolutions (M2) | PASS |
| **S4** | Richardson-Lucy **worst_PSNR = 30.8 dB ≥ ε=30 dB** (M3: worst-case over 20 dev scenes); at least one solver clears ε, confirming task is feasible per Principle's error bounds | PASS |

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

Closed-form seed reward + numeric substitution per STYLE_NOTES §4:

```
R_L3_seed = 100 × φ(t) × 0.60
          = 100 × 1.0 × 0.60 = 60 PWM (builder, one-time at acceptance)
        + 15% upstream royalty split 5% / 10% → Principle (L1) / spec (L2) authors
```

### The benchmark is now immutable

Once committed as `sha256:<widefield_bench_hash>`, the dataset, baselines, and scoring table are fixed. Miners compete against frozen targets. Additional datasets under the same spec (new cell lines, different fluorophores, new noise regimes) earn **new benchmark IDs** — they do not modify this one.

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
     min_vram_gb:      4          # minimum GPU VRAM (widefield is modest)
     recommended_vram_gb: 8
     cpu_only:         false      # GPU preferred; CPU fallback possible
     min_ram_gb:       8
     expected_runtime_s: 30       # per 512×512 instance on single GPU
     expected_runtime_p_bench_s: 1200   # full P-benchmark run
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
| CPU-only (SP = CP) | 1.0 | 100% | 0% | `cpu_only: true, expected_runtime_s: 2` |
| Lightweight iterative | 0.80 | 80% | 20% | `min_vram_gb: 0, expected_runtime_s: 5` |
| Single GPU | 0.50 | 50% | 50% | `min_vram_gb: 4, expected_runtime_s: 30` |
| GPU cluster | 0.25 | 25% | 75% | `min_vram_gb: 24, expected_runtime_s: 300` |

### Step-by-step mining

#### Step 1: Choose your task

```bash
pwm-node benchmarks | grep structured_light
```

Output:
```
# Spec #1: Mismatch-only (measurement only input)
widefield   mismatch_only_t1_nominal     ρ=1    mineable   (I-benchmark, ε=30.0 dB)
widefield   mismatch_only_t2_low         ρ=2    mineable   (I-benchmark, ε=28.0 dB)
widefield   mismatch_only_t3_moderate    ρ=4    mineable   (I-benchmark, ε=25.5 dB)
widefield   mismatch_only_t4_blind       ρ=10   mineable   (I-benchmark, ε=22.0 dB)
widefield   mismatch_only_p_benchmark    ρ=50   mineable   (P-benchmark, ε=epsilon_fn(Ω))

# Spec #2: Oracle-assisted (measurement + true_phi input)
# Ω varies H/pixel_nm/peak_photons only — no mismatch dims in Ω
widefield   oracle_t1_h128_pix100        ρ=1    mineable   (I-benchmark, ε=33.0 dB)
widefield   oracle_t2_h512_pix65         ρ=3    mineable   (I-benchmark, ε=35.0 dB)
widefield   oracle_t3_h2048_pix32        ρ=5    mineable   (I-benchmark, ε=37.0 dB)
widefield   oracle_p_benchmark           ρ=50   mineable   (P-benchmark, ε=epsilon_fn(Ω))
```

#### Step 2: Pre-check gates (free, no compute)

```bash
pwm-node verify structured_light/fluocells_t1_nominal.yaml
```

Checks S1-S2 against the Principle before you spend GPU time.

#### Step 3: Solve

```bash
pwm-node mine structured_light/fluocells_t1_nominal.yaml
```

Under the hood:
1. Downloads benchmark data (20 scenes + PSF hint + Ω params) from DA layer
2. Runs your solver on all 20 scenes
3. Produces 20 reconstructed intensity maps (512×512 each)
4. Computes PSNR, SSIM, resolution_nm for each scene

**You choose the solver.** The spec defines the problem, not the algorithm:

| Solver | Expected PSNR | GPU Time | Quality Q | Notes |
|--------|---------------|----------|-----------|-------|
| Wiener            | ~30 dB | <1 s/scene   | 0.80 | Classical, closed-form Tikhonov |
| Richardson-Lucy   | ~31 dB | 2–5 s/scene  | 0.82 | Iterative Poisson MLE |
| Blind-RL          | ~29 dB | 20–60 s/scene| 0.78 | Joint PSF + intensity estimation |
| CARE-UNet         | ~36 dB | 0.5 s/scene  | 0.98 | Learned, pretrained on FluoCells |
| Noise2Void        | ~34 dB | 1 s/scene    | 0.92 | Self-supervised learned |

Better solver → higher PSNR → higher Q → more PWM (via larger ranked draw fraction).

#### Step 4: Local verification (S1-S4 on the solution)

Your local Judge Agent checks the solution against **all three upstream artifacts**:

```
Solution verified from TWO directions simultaneously:

Direction 1: BENCHMARK VERIFICATION
  Compare PSNR, SSIM, resolution_nm against benchmark baselines
  → Determines quality score Q ∈ [0.75, 1.0]
  → "How good is the solution?"

Direction 2: PRINCIPLE + S1-S4 VERIFICATION
  Check solution against Widefield forward model directly
  S1: output dimensions [512,512] match spec grid
  S2: solver used method consistent with well-posedness
  S3: residual ||y − PSF ⊛ f̂||₂ decreased monotonically
  S4: PSNR ≥ ε(this Ω tier), SSIM ≥ 0.85, residual < error_bound
  → Determines pass/fail
  → "Is the solution mathematically correct?"

BOTH must pass → S4 Certificate issued → PWM minted
```

| Gate | What it checks on the widefield solution | Expected |
|------|-------------------------------------------|----------|
| **S1** | Output shape [512,512] matches spec; non-negative intensity; emission_nm metadata preserved | PASS |
| **S2** | Solver method is consistent with Principle's well-posedness (used Wiener/Tikhonov or equivalent regularization for underdetermined high-frequency recovery) | PASS |
| **S3** | Solver residual ‖y − PSF ⊛ f̂‖₂ decreases monotonically; convergence rate matches Principle's q=2.0 to within 10% | PASS |
| **S4** | Worst-case PSNR ≥ ε across all 20 scenes, SSIM ≥ 0.85, residual below error bound | PASS |

#### Step 5: Certificate assembly and automatic reward routing

```json
{
  "cert_hash": "sha256:...",
  "h_s": "sha256:<structured_light_spec1_hash>",
  "h_b": "sha256:<structured_light_bench1_hash>",
  "h_p": "sha256:<structured_light_principle_hash>",
  "h_x": "sha256:... (reconstructed intensity maps hash)",
  "r": {
    "residual_norm": 0.018,
    "error_bound": 0.05,
    "ratio": 0.36
  },
  "c": {
    "resolutions": [[128, 0.041], [256, 0.011], [512, 0.003]],
    "fitted_rate": 1.95,
    "theoretical_rate": 2.0,
    "K": 3
  },
  "d": {"consistent": true},
  "Q": 0.92,
  "gate_verdicts": {"S1": "pass", "S2": "pass", "S3": "pass", "S4": "pass"},
  "difficulty": {"tier": "textbook", "delta": 1},
  "sp_wallet": "...",
  "share_ratio_p": 0.50,
  "sigma": "ed25519:..."
}
```

The certificate contains **three upstream hashes** — proving it was verified against the immutable Principle, spec, and benchmark:

```
cert references:
  h_p → Principle  sha256:<structured_light_principle_hash>   (Layer 1, immutable)
  h_s → spec.md    sha256:<structured_light_spec1_hash>       (Layer 2, immutable)
  h_b → Benchmark  sha256:<structured_light_bench1_hash>      (Layer 3, immutable)
  h_x → Solution   sha256:<structured_light_solution_hash>    (Layer 4, this submission)
```

#### Step 6: Challenge period

- **3-day window** for textbook-difficulty tasks (δ=1); 7-day for δ≥3
- Any verifier can download all artifacts by hash and re-verify independently
- If nobody challenges, the certificate finalizes

#### Step 7: Reward settlement

**Each benchmark has its own independent pool and rank list.** The P-benchmark and every I-benchmark (T1, T2, T3, T4) each maintain a separate pool. Rank 1 on the P-benchmark is the first solution to pass that P-benchmark; Rank 1 on I-benchmark T4 is the first solution to pass T4. A solver can hold Rank 1 on multiple benchmarks simultaneously and draws from each independently.

**Subscript notation:**

| Subscript | Meaning | Widefield example |
|---|---|---|
| `k` | Principle index | k=1 (Widefield Principle) |
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
               δ_k = Principle difficulty tier (Widefield: δ=1); fixed at L1 from L_DAG
               activity_k = L4 solutions under Principle k in last 90 days
  T_k        = accumulated 15% of ALL L4 events under promoted Principle k

Stage 2 — Spec allocation (j level, within promoted Principle k):   uses ρ
  A_{k,j}    = A_k × Σ_b* ρ_{j,b} / Σ_{j'*,b'*} ρ_{j',b'}   (* promoted Specs/Benchmarks only)
  T_{k,j}    = T_k × Σ_b* ρ_{j,b} / Σ_{j'*,b'*} ρ_{j',b'}

Stage 3 — Benchmark allocation (b level, within promoted Spec j):   uses ρ
  A_{k,j,b}  = A_{k,j} × ρ_{j,b} / Σ_b* ρ_{j,b}              (* promoted Benchmarks only)
  T_{k,j,b}  = T_{k,j} × ρ_{j,b} / Σ_b* ρ_{j,b}
               ρ_{j,b} = pool weight declared for benchmark b; P-benchmark ρ=50, I-benchmark ρ∈{1,2,4,10}

Bounty term B_{k,j,b}:   available at all stages regardless of promotion status
  B_k^P       = bounty staked at Principle level (flows to all promoted benchmarks under k by ρ)
  B_{k,j}^S   = bounty staked at Spec j level   (flows to all promoted benchmarks under j by ρ)
  B_{k,j,b}^D = bounty staked directly at Benchmark b (goes entirely to that benchmark)

  B_{k,j,b}  = B_{k,j,b}^D
              + B_{k,j}^S × ρ_{j,b} / Σ_b* ρ_{j,b}
              + B_k^P      × ρ_{j,b} / Σ_{j'*,b'*} ρ_{j',b'}
```

> **δ vs ρ in pool allocation:** Stage 1 uses `δ_k` to compare Principles globally (physics difficulty, set at L1). Stages 2–3 use `ρ` to split a Principle's budget among its benchmarks (pool weight, declared at L3). Both use the same numeric scale {1,2,4,10,50} but at different hierarchy levels.

**Widefield example** (mismatch-only spec, j=1; total ρ = 50+10+4+2+1 = 67):

| Benchmark b | ρ | Pool share within spec (ρ / 67) |
|---|---|---|
| P-benchmark      | 50 | **74.6%** |
| T4 (blind calib.)| 10 | 14.9% |
| T3 (moderate)    | 4  | 6.0% |
| T2 (low)         | 2  | 3.0% |
| T1 (nominal)     | 1  | 1.5% |

**Ranked draws:** Rank 10 is the last paid rank. Solutions ranked 11+ receive no draw; the remaining ~52% of the epoch pool rolls over to the next epoch.

| Rank | Draw |
|------|------|
| Rank 1 (first solution) | 40% of current pool |
| Rank 2 | 5% of remaining |
| Rank 3 | 2% of remaining |
| Rank 4–10 | 1% of remaining (each) |
| Rank 11+ | No draw |

**Example** (Pool_{k,j,b} = 100 PWM for one widefield benchmark, p=0.50, so SP=27.5%, CP=27.5%):

| Rank | Draw (PWM) | SP (p×55%) | CP ((1−p)×55%) | L3 (15%) | L2 (10%) | L1 (5%) | T_k (15%) |
|------|-----------|-----------|---------------|----------|----------|---------|-----------|
| 1 | 40.00 | 11.00 | 11.00 | 6.00 | 4.00 | 2.00 | 6.00 |
| 2 | 3.00  | 0.83  | 0.83  | 0.45 | 0.30 | 0.15 | 0.45 |
| 3 | 1.14  | 0.31  | 0.31  | 0.17 | 0.11 | 0.06 | 0.17 |
| 4 | 0.56  | 0.15  | 0.15  | 0.08 | 0.06 | 0.03 | 0.08 |
| 5–10 | ~0.53 each | ~0.15 | ~0.15 | ~0.08 | ~0.05 | ~0.03 | ~0.08 |
| **Rollover** | **~52.0** | — | — | — | — | — | — |

**Upstream royalty split (same for minting draws and usage fees):**

| Recipient | Share | Notes |
|-----------|-------|-------|
| SP (Algorithm Creator) | p × 55% | Earns passively; sets p at registration |
| CP (Compute Provider)  | (1−p) × 55% | Earns by running jobs; distinct for mining vs. usage |
| L3 Benchmark creator   | 15% | Upstream royalty |
| L2 Spec author         | 10% | Upstream royalty |
| L1 Principle creator   | 5%  | Upstream royalty |
| T_k per-principle treasury | 15% | Self-funds adversarial bounties + validator fees |

Anti-spam: after ~50 solutions at a given ρ=1 tier, per-solution reward falls below gas cost.

### Cross-benchmark claims (P-benchmark bonus)

Within **3 days** of passing the widefield P-benchmark (textbook tier has a short challenge window), the SP may optionally claim:

1. Any I-benchmark of the same spec (auto-verified by re-running the solver on that tier's 20 dev scenes; pass → one ranked draw in that I-benchmark's independent pool)
2. I-benchmarks of other specs under the same Principle — e.g. a solver that passes the mismatch-only P-benchmark may claim the oracle-assisted T1 (the oracle has more information, so passing should be strictly easier)

Cross-claims are optional — failure has no penalty. The protocol enforces that a cross-claim run uses the *same* hash-locked binary as the original P-benchmark submission; no tuning or substitution is allowed. This is how the P-benchmark's ρ=50 reward cascades into cheap I-benchmark ranks for generalist solvers.

**Worked example.** A CARE-UNet submission passes `structured_light/mismatch_only_p_benchmark` (ρ=50) with Q=0.94. Within 72 hours the SP submits cross-claims for T1_nominal (ρ=1), T2_low (ρ=2), T3_moderate (ρ=4), T4_blind (ρ=10). All four auto-verifications pass (CARE-UNet is mismatch-robust by training). Result: five ranked draws from five independent pools in one epoch — the P-benchmark draw plus four I-benchmark draws at no additional compute cost beyond the four verification runs.

---

## Complete Hash Chain (Immutability Across All Four Layers)

```
Layer 1 ──→ Principle sha256:<structured_light_principle_hash>     FIXED
               │
Layer 2 ──→ spec.md sha256:<structured_light_spec1_hash>           FIXED
               │   contains: principle_ref: sha256:<structured_light_principle_hash>
               │
Layer 3 ──→ Benchmark sha256:<structured_light_bench1_hash>        FIXED
               │   contains: spec_ref: sha256:<structured_light_spec1_hash>
               │             principle_ref: sha256:<structured_light_principle_hash>
               │
Layer 4 ──→ Certificate sha256:<structured_light_cert_hash>        SUBMITTED
                   contains: h_s: sha256:<structured_light_spec1_hash>
                             h_b: sha256:<structured_light_bench1_hash>
                             h_p: sha256:<structured_light_principle_hash>
                             h_x: sha256:<structured_light_solution_hash>

Tampering with ANY artifact changes its hash → breaks the chain.
Every verifier can independently reconstruct this chain.
```

---

## I-Benchmark Tiers — Detailed Mining Guide

### Mismatch-Only Spec: Tier T1 (Nominal — Start Here)

The PSF is correctly calibrated, no defocus, no background drift. The simplest widefield deconvolution task.

| Property | Value |
|----------|-------|
| omega_tier | H=512, NA=1.4, pixel=65 nm, emit=525 nm, peak=1000, dz=0, σ_bg=0 |
| Operator | Calibrated PSF (Φ = Φ_true) |
| Expert baseline | Richardson-Lucy: PSNR = 31.2 dB, SSIM = 0.872 |
| ε | 30.0 dB (epsilon_fn at this Ω point) |
| ρ | 1 |

```bash
pwm-node mine structured_light/fluocells_mismatch_only_t1_nominal.yaml
```

### Mismatch-Only Spec: Tiers T2 / T3 (Low / Moderate Mismatch)

Same measurement-only input format — only the `omega_tier` point changes (defocus and background drift).

| Property | T2 (Low) | T3 (Moderate) |
|----------|----------|---------------|
| omega_tier | dz=200 nm, σ_bg=0.02 | dz=600 nm, σ_bg=0.05 |
| Expert baseline PSNR | Richardson-Lucy: ~29 dB | Richardson-Lucy: ~26 dB |
| ε | 28.0 dB | 25.5 dB |
| ρ | 2 | 4 |

**Warning (T3):** Richardson-Lucy without a PSF hint barely clears at 26.1 dB. A PSF-calibration-aware solver (Blind-RL, learned denoiser with defocus-augmentation) is recommended. CARE-UNet trained on defocus-augmented data clears comfortably at ~33 dB.

### Mismatch-Only Spec: Tier T4 (Blind Calibration — Highest I-benchmark ρ)

Solver must estimate PSF parameters (effective defocus, background level) from data, then deconvolve. Most practically valuable — matches real-world uncalibrated microscopy.

| Property | Value |
|----------|-------|
| omega_tier | dz=1200 nm, σ_bg=0.08 |
| Input | Measurement only (no defocus or background hints — solver must self-calibrate) |
| ε | 22.0 dB |
| ρ | 10 |
| Dataset | FluoCells (40 scenes, 1024×1024 intensity + ground-truth fluorophore maps); cropped and resampled to 512×512; synthetic defocus + background applied at T4 parameters; fixed 20-scene eval set |

### Oracle-Assisted Spec: Tier T1 (Moderate Mismatch + Oracle — center I-bench)

The center I-benchmark for the oracle spec is at small system size + moderate mismatch — where oracle information (true NA, emission, defocus, background) genuinely helps.

| Property | Value |
|----------|-------|
| omega_tier | H=128, W=128, pixel_nm=100, peak_photons=500 |
| true_phi (inputs, not Ω) | NA=1.4, emission_nm=525, dz_nm=400, sigma_bg=0.03 |
| Input | Measurement + true_phi dict |
| ε | 33.0 dB (epsilon_fn at this oracle Ω tier) |
| ρ | 1 |

Why oracle-assisted T1 is easier than mismatch-only T1: the solver receives the exact PSF parameters, eliminating the need for blind calibration and allowing tighter Wiener regularization. The threshold is correspondingly higher (33 vs 30 dB).

### Mismatch Recovery by Solver

Not all solvers benefit equally from calibration information:

| Solver | ρ (recovery %) | Why |
|--------|----------------|-----|
| Blind-RL                | 65% | Explicitly estimates defocus and background; uses them in the forward model each iteration |
| Richardson-Lucy + hint  | 40% | Uses supplied PSF hint; partially compensates defocus but cannot adapt mid-iteration |
| CARE-UNet (defocus-aug) | 28% | Trained on defocus-augmented data; robustness baked in but no explicit estimation |
| Wiener                  | 0%  | Fixed Tikhonov filter; PSF-oblivious for mismatched cases |

**Strategy:** Use Blind-RL for mismatch-heavy tiers (T3 / T4). CARE-UNet trained with defocus augmentation is a safer baseline for T2 / T3 if you lack the expertise to tune Blind-RL. Avoid Wiener for anything beyond T1 nominal.

### P-benchmark (Highest Reward Overall, ρ=50)

Tests generalization across the **full** declared Ω space. The solver must work across all combinations of H∈[128,4096], pixel_nm∈[30,200], NA∈[0.4,1.49], emission_nm∈[400,800], peak_photons∈[50,10000], and mismatch dims within their declared bounds.

```
P-benchmark uses epsilon_fn(Ω) as threshold — not a fixed number.
Quality is evaluated across all three Tracks (see Track A/B/C details above):
  Track A: 4 strata by H×W; worst of 5 instances per stratum must pass ε
  Track B: median of 50 uniform Ω samples must pass ε at Ω_median
  Track C: mismatch degradation curve; φ swept 0→1 across 5 points (dz/σ_bg)
```

**Source dataset:** FluoCells-XL (500 scenes, 2048×2048 intensity + ground-truth fluorophore maps, CC-BY-NC). A subset of the Broad Bioimage Benchmark Collection's synthetic fluorescence library augmented with real confocal-derived ground truths for pairwise comparison.

**Stitching for H×W > 1024:** Real widefield deployments tile multiple fields of view for large-area imaging (whole-well scans, tissue slides). The P-benchmark mirrors this: for target H or W > 1024, four FluoCells-XL scenes are tiled in a 2×2 arrangement (hard concatenation, no blending) and cropped to the target size. The seam at tile boundaries is a real spatial discontinuity — solvers that handle it score higher. FluoCells-XL at 2048×2048 per tile covers 2×2 → 4096×4096, sufficient for any target up to 4096.

| Target H×W | Tile count | Source |
|---|---|---|
| [128, 1024] | 1 FluoCells-XL crop | No stitching |
| (1024, 4096] | 4 FluoCells-XL scenes (2×2 hard stitch) | Seam at tile boundary |

The `true_phi` for a stitched scene includes a `seam_map` (binary mask of tile boundaries) so oracle-assisted solvers can condition on it; mismatch-only solvers must infer or handle it blindly.

ρ=50 makes the P-benchmark pool weight 50× higher than the T1 nominal I-benchmark. A solver that passes the P-benchmark earns substantially more than all I-benchmarks combined.

---

## Complete Reward Summary (All Four Layers for Structured Light)

```
┌─────────┬──────────────────────────────┬──────────────────────────────────────────────┐
│ Layer   │ One-time creation reward     │ Ongoing upstream royalties                   │
├─────────┼──────────────────────────────┼──────────────────────────────────────────────┤
│ L1      │ Reserve grant (DAO vote)     │ 5% of every L4 minting draw                  │
│Principle│ when S4 gate passes          │ 5% of every L4 usage fee                     │
│         │ (≈ 200 PWM for genesis)      │ → If 1,000 solutions at 50 PWM each:         │
│         │                              │   2,500 PWM passively                        │
├─────────┼──────────────────────────────┼──────────────────────────────────────────────┤
│ L2      │ Reserve grant (DAO vote)     │ 10% of every L4 minting draw                 │
│ spec.md │ when S4 gate passes          │ 10% of every L4 usage fee                    │
│         │ Requires d_spec ≥ 0.35       │ → If 250 solutions at 50 PWM each:           │
│         │ (≈ 105 PWM typical)          │   1,250 PWM per spec                         │
├─────────┼──────────────────────────────┼──────────────────────────────────────────────┤
│ L3      │ Reserve grant (DAO vote)     │ 15% of every L4 minting draw                 │
│Benchmark│ when S4 gate passes          │ 15% of every L4 usage fee                    │
│         │ Requires d_ibench ≥ 0.10     │ → If 250 solutions at 50 PWM each:           │
│         │ (≈ 60 PWM typical)           │   1,875 PWM per benchmark                    │
├─────────┼──────────────────────────────┼──────────────────────────────────────────────┤
│ L4      │ N/A (no one-time grant)      │ Ranked draw from per-principle pool:         │
│Solution │                              │   SP: p × 55% (passively)                    │
│         │                              │   CP: (1−p) × 55% (per job executed)         │
│         │                              │   Example: Rank 1, 100 PWM pool, p=0.5:      │
│         │                              │   40 PWM draw → SP:11, CP:11                 │
└─────────┴──────────────────────────────┴──────────────────────────────────────────────┘

Token supply: 21M PWM total. Minting pool = 82% (17.22M PWM).
Early miners earn more: Rank 1 draws 40% of remaining pool at time of solution.
T_k (15% of every L4 event) accumulates per-Principle — self-funds adversarial bounties.
Widefield (δ=1) draws are smaller than CASSI (δ=3) per-solution, but Widefield
volume is expected to be higher (simpler problem, broader researcher base).
```

---

## Mining Strategies

| Strategy | Effect |
|----------|--------|
| Start with T1 Nominal | Lowest risk; Richardson-Lucy clears threshold at 31 dB |
| Use CARE-UNet on T1 | PSNR ≈ 36 dB → Q ≈ 0.98 → larger pool share |
| Solve T3 moderate with Blind-RL | ρ=65% recovery; demonstrates defocus robustness |
| Solve T4 blind calibration | Highest I-benchmark ρ=10; strongest reputation signal |
| Attempt P-benchmark | ρ=50; largest pool weight; cross-claim I-benchmarks after |
| Be first solver in widefield domain | Novelty multiplier ν_c is highest for first solutions |
| Submit across multiple resolutions | Convergence-based scoring (M2) rewards this |
| Use a novel solver architecture | Method-signature diversity (M5) rewards novelty (e.g. a diffusion-prior deconvolver instead of yet-another U-Net) |

### Recommended progression

| Stage | Task | Approx. reward (Rank 1, small pool) |
|-------|------|--------------------------------------|
| 1. Learn     | T1 Nominal with Richardson-Lucy | ~40 PWM |
| 2. Improve   | T1 Nominal with CARE-UNet       | ~80 PWM |
| 3. Challenge | T3 Moderate with Blind-RL       | ~120 PWM |
| 4. Calibrate | T4 Blind calibration            | ~160 PWM |
| 5. Frontier  | P-benchmark (full Ω range) + cross-claims | ~250 PWM + 4 cross-claim draws |

Rewards scale with how many other solvers have attempted the same benchmark — first-mover bonuses are largest. Widefield is Principle #1 in the registry, so early miners in this domain also benefit from the "first-Principle" activity multiplier until more Principles accumulate L4 activity.

---

## What You Cannot Do

- **Memorize benchmark outputs** — M1 generates test instances from an unmanipulable randomness source; you cannot predict which scenes you will be tested on.
- **Fake the certificate** — Every full node checks it in O(1); forging is mathematically infeasible.
- **Skip gates** — S3 convergence check catches solvers that produce good numbers without actually converging.
- **Game the quality score** — Worst-case scoring across 20 dev scenes (M3) means one bad scene tanks your score.
- **Reuse someone else's solution** — The certificate commits your SP identity and solution hash; duplicates are detected.
- **Use PSF-oblivious methods for T4** — Wiener (0% mismatch recovery) cannot benefit from implicit PSF calibration; the protocol detects this via the cross-tier degradation curve.
- **Tamper with upstream hashes** — Changing any artifact (Principle, spec, benchmark) breaks the hash chain; all verifiers detect it.
- **Submit a near-duplicate spec** — d_spec < 0.15 is rejected outright; add an I-benchmark tier instead.

---

## Quick-Start Commands

```bash
# 1. Check available widefield tasks
pwm-node benchmarks | grep structured_light

# 2. Pre-check gates (free, no compute)
pwm-node verify structured_light/mismatch_only_t1_nominal.yaml

# 3. Mine the center I-benchmark (nominal, ρ=1)
pwm-node mine structured_light/mismatch_only_t1_nominal.yaml

# 4. Inspect your certificate
pwm-node inspect sha256:<your_cert_hash>

# 5. Check balance after 3-day challenge period (textbook tier)
pwm-node balance

# 6. Mine moderate mismatch tier (ρ=4)
pwm-node mine structured_light/mismatch_only_t3_moderate.yaml

# 7. Mine blind calibration tier (ρ=10, highest I-benchmark)
pwm-node mine structured_light/mismatch_only_t4_blind.yaml

# 8. Mine oracle-assisted center I-benchmark (ρ=1, true_phi provided)
pwm-node mine structured_light/oracle_t1_h128_pix100.yaml

# 9. Register as Solution Provider (SP) — after proving solution works locally
#    Include compute manifest so CPs know hardware requirements
pwm-node sp register \
  --entry-point solve.py \
  --share-ratio 0.50 \
  --min-vram-gb 4 \
  --expected-runtime-s 30 \
  --framework pytorch

# 10. Register as Compute Provider (CP)
pwm-node cp register --gpu RTX4070 --vram 12
```

---

## Reference

| Topic | Where to find it |
|-------|------------------|
| Structured Light Principle (#1) | `principle.md`, Section A (Microscopy) |
| Four-layer pipeline | `pwm_overview.md` §2 |
| Principle definition P=(E,G,W,C) | `pwm_overview.md` §3 |
| L_DAG complexity score (κ₀=1000) | `pwm_overview.md` §3 Primitive Decomposition |
| physics_fingerprint and spec_range | `pwm_overview.md` §3 |
| Spec six-tuple S=(Ω,E,B,I,O,ε) | `pwm_overview.md` §4 |
| epsilon_fn (AST-sandboxed) | `pwm_overview.md` §4 The epsilon_fn |
| Spec distance formula (d_spec) | `pwm_overview.md` §4 Spec Distance / `spec_distance_design.md` |
| P-benchmark vs. I-benchmark | `pwm_overview.md` §5 |
| ibenchmark_range declaration | `pwm_overview.md` §5 |
| Evaluation Tracks A/B/C | `pwm_overview.md` §5 / `pbenchmark_scoring.md` |
| M1-M6 anti-overfitting mechanisms | `pwm_overview.md` §5 |
| SP/CP dual-role architecture | `pwm_overview.md` §6 / `l4_dual_role.md` |
| Ranked draws and T_k=15% | `pwm_overview.md` §9 Ranked Draws |
| Reserve grants for L1/L2/L3 | `pwm_overview.md` §9 Early L1/L2/L3 Creation |
| Token economics (82% minting pool) | `pwm_overview.md` §9 Supply Distribution / `token_supply.md` |
| Upstream royalty split 5/10/15/15% | `pwm_overview.md` §10 |
| Two-stage security model | `pwm_overview.md` §11 |
| Hierarchical primitives (143-leaf) | `primitives.md` |
| Condition number conventions (κ_sub, κ_sys, κ_eff) | `condition_number.md` |
| Airy PSF theory | G. Airy, *Trans. Camb. Phil. Soc.*, 1835 ⟨draft — canonical optics textbook reference⟩ |
| Richardson-Lucy deconvolution | W. H. Richardson, *J. Opt. Soc. Am.*, 1972; L. B. Lucy, *Astron. J.*, 1974 |
| Poisson-likelihood convergence O(1/k²) | Shepp & Vardi, *IEEE Trans. Med. Imag.*, 1982 |
| FluoCells dataset | Broad Bioimage Benchmark Collection ⟨draft — pending exact DOI / collection ID⟩ |
| CARE-UNet content-aware restoration | M. Weigert et al., *Nature Methods*, 2018 |
