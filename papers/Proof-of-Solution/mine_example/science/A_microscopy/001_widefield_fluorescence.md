# Widefield Fluorescence Microscopy — Complete Four-Layer Walkthrough

**Principle #1: Widefield Fluorescence Microscopy**
Domain: Microscopy | Difficulty: Textbook (delta=1) | Carrier: Photon

---

## The Four-Layer Pipeline for Widefield Fluorescence

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
│  WIDEFIELD FLUORESCENCE PRINCIPLE  P = (E, G, W, C)                      │
│  Principle #1 in the PWM registry                                        │
│  sha256: <widefield_principle_hash>  (immutable once committed)          │
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

Once committed on-chain as `sha256:<widefield_principle_hash>`, the Widefield Fluorescence Principle **never changes**. All downstream spec.md files, benchmarks, and solutions reference this hash. Updating the physics — for example, extending to anisotropic PSFs or 3D z-stack forward models — means creating Principle v2 (a new hash), not modifying v1. The registry treats immutability as a first-class invariant.

---

## Layer 2: Principle + S1-S4 → spec.md (Task Design)

### Who does this?

A **task designer** (can be the same domain expert or anyone else). They take the Widefield Fluorescence Principle and design specific, solvable tasks — concrete spec.md files that pin down grid size, pixel pitch, numerical aperture, emission wavelength, noise model, and tier-structured mismatch ranges. Accepted specs earn a **Reserve grant** (DAO vote) on submission plus ongoing upstream royalties on all future L4 events that reference the spec.

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
Widefield Fluorescence Principle (sha256:<principle_hash>)
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
# widefield/fluocells_mismatch_only.yaml
# Layer 2 output — references the Widefield Fluorescence Principle

principle_ref: sha256:<widefield_principle_hash>   # ← links to Layer 1

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
# widefield/fluocells_oracle_assisted.yaml

principle_ref: sha256:<widefield_principle_hash>

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

_⟨draft⟩ TODO Task 8_

### What S1-S4 checks at Layer 2

_⟨draft⟩ TODO Task 8_

### Layer 2 reward

_⟨draft⟩ TODO Task 8_

### The spec.md is now immutable

_⟨draft⟩ TODO Task 8_

---

## Layer 3: spec.md + Principle + S1-S4 → Benchmark (Data + Baselines)

### Who does this?

_⟨draft⟩ TODO Task 9_

### P-benchmark vs. I-benchmark

_⟨draft⟩ TODO Task 9_

### ibenchmark_range (declared inside the spec, repeated here for reference)

_⟨draft⟩ TODO Task 9_

### What the benchmark builder creates

_⟨draft⟩ TODO Task 10_

### What S1-S4 checks at Layer 3

_⟨draft⟩ TODO Task 10_

### Layer 3 reward

_⟨draft⟩ TODO Task 10_

### The benchmark is now immutable

_⟨draft⟩ TODO Task 10_

---

## Layer 4: spec.md + Benchmark + Principle + S1-S4 → Solution (Mining for PWM)

### Who does this?

_⟨draft⟩ TODO Task 11_

### Step-by-step mining

_⟨draft⟩ TODO Task 11_

### Cross-benchmark claims (P-benchmark bonus)

_⟨draft⟩ TODO Task 12_

---

## Complete Hash Chain (Immutability Across All Four Layers)

_⟨draft⟩ TODO Task 14_

---

## I-Benchmark Tiers — Detailed Mining Guide

### Mismatch-Only Spec: Tier T1 (Nominal — Start Here)

_⟨draft⟩ TODO Task 13_

### Mismatch-Only Spec: Tiers T2 / T3 (Low / Moderate Mismatch)

_⟨draft⟩ TODO Task 13_

### Mismatch-Only Spec: Tier T4 (Blind Calibration — Highest I-benchmark ρ)

_⟨draft⟩ TODO Task 13_

### Oracle-Assisted Spec: Tier T1 (Moderate Mismatch + Oracle — center I-bench)

_⟨draft⟩ TODO Task 13_

### Mismatch Recovery by Solver

_⟨draft⟩ TODO Task 13_

### P-benchmark (Highest Reward Overall, ρ=50)

_⟨draft⟩ TODO Task 13_

---

## Complete Reward Summary (All Four Layers for Widefield Fluorescence)

_⟨draft⟩ TODO Task 14_

---

## Mining Strategies

### Recommended progression

_⟨draft⟩ TODO Task 14_

---

## What You Cannot Do

_⟨draft⟩ TODO Task 14_

---

## Quick-Start Commands

_⟨draft⟩ TODO Task 14_

---

## Reference

_⟨draft⟩ TODO Task 14_
