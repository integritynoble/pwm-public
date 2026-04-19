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

_⟨draft⟩ TODO Task 6_

### Spec range declaration

_⟨draft⟩ TODO Task 6_

### What S1-S4 checks at Layer 1

_⟨draft⟩ TODO Task 6_

### Layer 1 reward

_⟨draft⟩ TODO Task 6_

### The Principle is now immutable

_⟨draft⟩ TODO Task 6_

---

## Layer 2: Principle + S1-S4 → spec.md (Task Design)

### Who does this?

_⟨draft⟩ TODO Task 7_

### What the task designer writes

_⟨draft⟩ TODO Task 7_

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
