# SPC — Complete Four-Layer Walkthrough (Single-Pixel Camera, Hadamard Illumination)

**Date:** 2026-05-08
**Audience:** Director, principle authors claiming SPC at L1-026b, contributors implementing SPC reference solvers, regulators verifying SPC certs
**Source manifests:** `pwm-team/content/agent-imaging/principles/B_compressive_imaging/L{1,2,3}-026b_spc.json`
**Canonical references (followed verbatim):**
- `papers/Proof-of-Solution/pwm_overview1.md` § 3 (Principle), § 4 (spec.md), § 5 (Benchmark), § 6 (Solution)
- `papers/Proof-of-Solution/mine_example/pwm_overview.md` Figures 0–9 (lifecycle, six-tuple, immutability, primitive decomposition)
- `papers/Proof-of-Solution/mine_example/primitives.md` (canonical 12-primitive basis + line 567 SPC signature)

This file is the SPC-specific instantiation of `mine_example/cassi.md`'s
template — same structure, SPC physics, every primitive in the canonical
basis.

---

## The Four-Layer Pipeline for SPC

```
   Layer 1: Seeds → Principle      (the physics quadruple P = (E, G, W, C))
       ↓                             owns: forward model, well-posedness, error bound
       ↓                             produces: L1-026b artifact, hashed on-chain
       ↓
   Layer 2: Principle + S1-S4       (the formal contract — six-tuple)
       → spec.md                    owns: Ω, E, B, I, O, ε
       ↓                             produces: L2-026b artifact, hashed on-chain
       ↓
   Layer 3: spec.md + Principle     (the verification infrastructure)
       + S1-S4 → Benchmark         owns: dataset, baselines, tier ε floors
       ↓                             produces: L3-026b artifact + dataset CIDs
       ↓
   Layer 4: spec.md + Benchmark     (mining loop)
       + Principle + S1-S4         owns: solver runs, cert payload, Q, reward
       → Solution                   produces: L4 cert hashes, on-chain
```

**Where SPC sits today:** all three of L1-026b / L2-026b / L3-026b are
**Tier-3 stubs** in the catalog (`registration_tier: "stub"`, no
on-chain registration, no IPFS dataset CID, no reference solver
shipped). The walkthrough below is what the artifacts assert formally —
the gap to mineable is in § 9 ("Promotion path").

---

# Layer 1 — Principle (`L1-026b`)

A Principle is the mathematical foundation for an entire family of
inverse problems. Per `pwm_overview1.md` § 3, every Principle is the
quadruple `P = (E, G, W, C)`.

## 1.0 The formal definition (verbatim from `pwm_overview.md` Figure 0b)

```
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │  DEFINITION: PRINCIPLE  P = (E, G, W, C)                                   │
    │                                                                             │
    │  The output of Layer 1.  Extracted from seeds after Valid(B) passes.       │
    └─────────────────────────────────────────────────────────────────────────────┘

    ┌────────┬────────────────────────────────────────────────────────────────────┐
    │ Symbol │ What it is — instantiated for SPC                                  │
    ├────────┼────────────────────────────────────────────────────────────────────┤
    │   E    │ FORWARD MODEL                                                      │
    │        │ The mathematical operator: unknowns → observables.                 │
    │        │ Taken from the seed's E field.                                     │
    │        │                                                                     │
    │        │ SPC: y = Φ x + n                                                  │
    │        │      Φ ∈ ℝ^{m×n}  Walsh-Hadamard rows in {-1,+1}                  │
    │        │      x ∈ ℝⁿ       (vectorised image, n = H·W)                     │
    │        │      y ∈ ℝᵐ       (m bucket-detector readings)                    │
    │        │      n ∼ 𝒩(0, σ²) (additive Gaussian)                              │
    ├────────┼────────────────────────────────────────────────────────────────────┤
    │   G    │ DAG DECOMPOSITION  G = (V, A)                                      │
    │        │ Directed acyclic graph where:                                      │
    │        │   V = nodes (primitives from the 12-element general basis)        │
    │        │   A = arcs (data dependencies between primitives)                  │
    │        │ Made explicit by S1 (dimensional consistency across nodes).        │
    │        │                                                                     │
    │        │ The 12 general computational primitives:                           │
    │        │   ∂  ∫  L  N  E  F  Π  S  K  B  G  O                              │
    │        │                                                                     │
    │        │ Derived quantities (and W.κ):                                      │
    │        │   |V|  = number of distinct primitive nodes                        │
    │        │   n_c  = number of coupling interfaces (feedback loops)            │
    │        │   L_DAG = (|V| − 1) + log₁₀(κ / κ₀) + n_c                          │
    │        │           where κ from W, κ₀ = 10                                  │
    │        │   δ = tier(L_DAG):                                                 │
    │        │        L_DAG < 2.0 → δ=1 (textbook)                                │
    │        │        [2.0, 5.0) → δ=3 (standard)                                 │
    │        │        [5.0, 7.0) → δ=5 (advanced)                                 │
    │        │        [7.0, 10)  → δ=10 (frontier)                                │
    │        │        ≥ 10.0     → δ=50 (grand challenge)                         │
    │        │                                                                     │
    │        │ SPC instantiation:                                                 │
    │        │   strict signature  : [L.diag.binary] → [∫.spatial]                │
    │        │                       (primitives.md line 567)                     │
    │        │   elaborated         : [G.structured.random] → [L.diag.binary]    │
    │        │                       → [∫.spatial]                                │
    │        │   |V| = 3, n_c = 0, κ_eff = 30, κ₀ = 10                            │
    │        │   L_DAG = 2 + log₁₀(30/10) + 0 = 2 + 0.48 = 2.48 → δ = 3 (standard)│
    ├────────┼────────────────────────────────────────────────────────────────────┤
    │   W    │ WELL-POSEDNESS CERTIFICATE                                         │
    │        │                                                                     │
    │        │ W = (existence, uniqueness, stability, κ, mismatch)                │
    │        │                                                                     │
    │        │ All from S2 (mathematical well-posedness).                          │
    │        │ Physical grounding (instrument, units, physics_ref) is              │
    │        │ handled by P1-P10, NOT by W. W is purely mathematical.              │
    │        │                                                                     │
    │        │ SPC instantiation:                                                 │
    │        │   existence  : true (linear inverse, Φ has full row rank)          │
    │        │   uniqueness : true (under sparsity prior; RIP holds at m/n ≥ 5%) │
    │        │   stability  : conditional (Lipschitz w.r.t. y under TV regularizer)│
    │        │   κ_raw           : 3000   (unregularised pseudo-inverse)          │
    │        │   κ_effective     :   30   (after TV-prior regularisation)         │
    │        │   κ_mismatched    :  120   (when gain α > 0 and illum σ > 0       │
    │        │                              corrupt the assumed Φ)                │
    │        │   mismatch sources: gain drift α, illumination falloff σ           │
    ├────────┼────────────────────────────────────────────────────────────────────┤
    │   C    │ ERROR-BOUNDING METHODOLOGY  C = (e, q, T)                          │
    │        │   e  = error metric (PSNR, RMSE, relative error, ...)              │
    │        │   q  = theoretical convergence rate for the problem class          │
    │        │   T  = certificate template (what S4 cert must report)             │
    │        │ Produced by S3 and S4.                                              │
    │        │                                                                     │
    │        │ SPC instantiation:                                                 │
    │        │   e  = PSNR_dB (primary), SSIM (secondary)                          │
    │        │   q  = 2.0    (linear in iteration count under sparsity prior)     │
    │        │   T  = { residual_norm = ‖y − Φx̂‖₂,                              │
    │        │          rate_log_residual / log_iter,                              │
    │        │          recovery_bound = C₁·σ/√m + C₂·‖x − x_s‖₁ }                │
    │        │   complexity per iteration: O(n log n)                              │
    │        │                              (fast Walsh-Hadamard transform)        │
    └────────┴────────────────────────────────────────────────────────────────────┘
```

The four sub-sections below (1.1–1.8) walk each component in detail.

## 1.1 What is SPC?

SPC is a compressive imaging modality where:

- A **DMD (digital micromirror device)** projects a sequence of binary
  `+1/-1` Hadamard patterns onto the incoming optical field
- A **single photodetector** (the "bucket detector") integrates the
  pattern-weighted irradiance once per pattern, producing one scalar
  measurement
- After `m` patterns, you have an `m`-dimensional measurement vector
- If the underlying image is sparse in some basis (TV / wavelet / DCT)
  and `m/n ≥ 0.05` (Hadamard sampling at ~5% Nyquist satisfies RIP),
  you can recover the full `H × W` image

This is the canonical "compressive sensing in the wild" demo — a $5
photodiode + a $200 DMD reconstructs images that would otherwise
require an entire focal-plane array.

**Why it matters:**
- Imaging in spectral bands where dense detectors are expensive (THz,
  mid-IR, X-ray)
- Single-photon / photon-counting regimes
- Imaging through scattering media (where DMD-modulated structured
  illumination buys SNR)

## 1.2 Forward model E

The deterministic operator `E: X → Y` maps the world state (an image)
to the observable measurement (a vector of bucket-detector readings):

```
y_k = ⟨φ_k, x⟩ + n_k     for k = 1, …, m

where:
  x ∈ ℝⁿ           — vectorized image, n = H × W (non-negative)
  φ_k ∈ {-1, +1}ⁿ  — k-th row of a Walsh-Hadamard basis (binary pattern)
  y_k ∈ ℝ          — k-th scalar photodetector reading
  n_k ∼ 𝒩(0, σ²)   — additive Gaussian noise (photon shot + read noise)
  m / n            — sampling ratio (typically 0.05–0.5)
```

Matrix form: `y = Φx + n`, with `Φ ∈ ℝ^{m × n}`, `m << n`.

**Recovery problem:** given measurement `y` and known pattern matrix
`Φ`, recover `x` from an underdetermined system. Solved via convex
optimization (FISTA-TV, GAP-TV-MLE) or learned unrolled networks
(LISTA, ISTA-Net).

## 1.3 DAG decomposition G = (V, A) — primitives in the canonical basis

Per `pwm_overview1.md` § 3 ("Primitive Decomposition"), the forward
operator decomposes into a DAG of primitives drawn from the
12-primitive Level-1 catalog (`∂ ∫ L N E F Π S K B G O`).

The canonical SPC signature, per `primitives.md` line 567:

```
#26 SPC = [L.diag.binary] → [∫.spatial]                      (strict 2-primitive form)
```

Expanded with the upstream pattern generator (every primitive still
in the canonical basis):

```
G.structured.random  →  L.diag.binary  →  ∫.spatial
  (Hadamard pattern       (apply binary mask    (sum across
   generator on DMD)       to optical field)     bucket detector)
```

| Primitive | Where defined in `primitives.md` | What it does in SPC |
|---|---|---|
| `G.structured.random` | line 505 — "random pattern (SPC, coded illumination)" | DMD generates the k-th Walsh-Hadamard binary `+1/-1` pattern |
| `L.diag.binary` | line 118 — "binary mask {0,1} — coded aperture, SPC" | Multiply the optical field element-wise by the pattern (the `<φ_k, x>` inner-product reduces to this multiply followed by the sum below) |
| `∫.spatial` | line 88 — "sum over spatial region (SPC bucket detector)" | Single photodetector sums photons across the spatially-modulated field — produces one scalar reading per pattern |

**There is no separate "single-pixel readout" primitive** — the
scalar reading is the output of `∫.spatial`. There is also **no `D`
root primitive** in the basis; the 12 roots are
`∂ ∫ L N E F Π S K B G O`.

**L_DAG complexity score** (per `pwm_overview1.md` § 3 formula):

```
L_DAG = (|V| − 1) + log₁₀(κ / κ₀) + n_c
      = (3 − 1) + log₁₀(30 / 10) + 0
      = 2 + 0.48 + 0
      ≈ 2.5
```

Where `|V| = 3` (vertices in the DAG), `κ = 30` (effective condition
number after TV regularisation; raw `κ = 3000` before regularisation),
`κ₀ = 10` (reference), `n_c = 0` (single-physics — no coupling
constraints in the forward operator).

That puts SPC in tier `δ = 3` (standard tier; L_DAG ∈ [2, 5)) per the
difficulty-tier table at `pwm_overview1.md` § 3.

## 1.4 Well-posedness W (Hadamard certificate)

| Property | Value | Source |
|---|---|---|
| Existence | `true` | Linear inverse problem with `Φ` full row rank |
| Uniqueness | `true` (under sparsity prior) | RIP-like condition holds for Walsh-Hadamard at ~5% sampling |
| Stability | `conditional` | Solution is Lipschitz w.r.t. `y` only when sparsity is enforced |
| Condition number κ (raw) | `3000` | `σ_max(Φ⁻ᵀ) / σ_min(Φ⁻ᵀ)` for unregularised pseudo-inverse |
| Condition number κ (effective, after TV) | `30` | After TV-prior regularisation (the operating regime) |
| Condition number κ (mismatched, with calibration error) | `120` | When `gain α > 0` and `illum σ > 0` corrupt the assumed Φ |

**Regime statement (verbatim from L1-026b):**

> "Hadamard measurement at 25% sampling satisfies RIP for sparse
> recovery; Gate-1 minimum compression ratio ~5%. Residual-based
> calibration fails for SPC (undetermined self-consistency); TV-based
> objective required for gain-drift and illumination-non-uniformity
> correction. Mismatched conditioning estimate (κ ≈ 120) extrapolated
> from CASSI's effective×4 ratio (50→200); refine with empirical
> sweeps over `gain_α` and `illum_σ` when available."

## 1.5 Convergence and error-bounding methodology C

Per `pwm_overview1.md` § 3, C is the certificate that a solver class
achieves a stated error bound on E-type problems.

| Field | Value |
|---|---|
| Solver class | FISTA-TV, ISTA-Net, LISTA, learned deep unrolling |
| Convergence rate `q` | `2.0` (linear in iteration count under sparsity prior) |
| Error bound | `‖x̂ − x‖₂ ≤ C₁ · σ / √m + C₂ · ‖x − x_s‖₁` |
| Per-iteration complexity | `O(n log n)` (fast Walsh-Hadamard transform) |

The error bound is the canonical compressed-sensing recovery
guarantee: reconstruction quality scales as `1/√m` in noise and as
the best `s`-sparse approximation of `x` (the second `‖·‖₁` term).

## 1.6 Physics fingerprint (Level-1 catalog tags)

Required by L1 manifests so the registry can index by carrier /
sensing mechanism / problem class:

| Field | Value |
|---|---|
| `carrier` | `photon` |
| `sensing_mechanism` | `structured_illumination` |
| `integration_axis` | `spatial` |
| `problem_class` | `linear_inverse` |
| `noise_model` | `gaussian` |
| `solution_space` | `2D_spatial` |
| `primitives` | `G.structured.random`, `L.diag.binary`, `∫.spatial` |
| `difficulty_delta` | `3` (standard tier) |
| `error_metric` | `PSNR_dB` (secondary: `SSIM`) |

## 1.7 Physical parameters θ

The forward model takes `θ` knobs that are **fixed at instrument-build
time** (vs. `Ω` parameters that vary at evaluation time and live in L2):

- `Phi_Hadamard`: Walsh-Hadamard rows, permutation seeded from a
  deterministic SHA256 RNG so the pattern matrix is reproducible
- `sampling_ratio m/n`: how much you compress (lower = harder)
- `gain α`: photodetector gain drift per measurement
- `illumination σ`: spatial non-uniformity of DMD illumination
  (Gaussian falloff)
- `DMD timing`: dwell time per pattern, duty cycle

`gain α` and `illum σ` will reappear in L2 as **mismatch axes** of `Ω`
— deliberately injected to test solver robustness.

## 1.8 P1-P10 physics validity tests + S1-S4 mathematical gates

Per `pwm_overview1.md` § 3 (the ten physics validity tests + the four
mathematical gates), L1-026b currently records all PASS. These are
self-asserted in the stub manifest; verifier-agent triple-review
runs at Tier-3 → Tier-2 promotion.

| Test | Status | Note |
|---|---|---|
| P1-P10 (physics validity) | all `PASS` | Stub-asserted; verifier-agent recomputes at promotion |
| S1 (dimensional consistency) | `PASS` | `Φ ∈ ℝ^{m×n}`, `y ∈ ℝ^m`, `x ∈ ℝ^n` — dimensions match |
| S2 (well-posedness) | `PASS` | Existence ✓ uniqueness ✓ stability=conditional |
| S3 (convergence rate) | `PASS` | `q = 2.0` derived from compressed-sensing literature |
| S4 (error bound) | `PASS` | Canonical recovery bound (§ 1.5) |

---

# Layer 2 — spec.md (`L2-026b`)

The spec is the **mathematical contract** — a six-tuple `(Ω, E, B, I,
O, ε)` per `pwm_overview1.md` § 4 — that turns the L1 physics into a
concrete instance schema solvers must conform to.

## 2.0 The formal spec.md format (verbatim from `pwm_overview.md` Figure 0d)

```
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │  THE spec.md FORMAT: ONE FLAT SIX-TUPLE                                    │
    └─────────────────────────────────────────────────────────────────────────────┘

    Every mineable task is a single file with seven fields:

        spec.md  =  S = (Ω, E, B, I, O, ε)  +  principle_ref

          principle_ref: hash          # hash of the Principle P = (E,G,W,C)
          omega:    Domain             # Ω: parameter range (system + mismatch)
          E:        OperatorGraph      # E: forward model / DAG primitive chain
          B:        BoundaryConstraints# B: constraints on the solution
          I:        InputData          # I: input data + committed dataset
          O:        Observables        # O: what the certificate must report
          epsilon:  Tolerance          # ε: pass/fail thresholds (epsilon_fn)

        That's it. No layers, no indirection, no separate files.

    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ WHAT USED TO BE ELSEWHERE          NOW LIVES IN                            │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ domain_id, carrier, modality    →  Principle (already in G)                │
    │ primitives                      →  Principle (already in G)                │
    │ quality_metrics                 →  Principle (already in C)                │
    │ expert_baseline, evaluator      →  Benchmark (L3)                          │
    │ system_elements (hardware)      →  Principle (physical context)            │
    │ dataset pointer                 →  I (input data in six-tuple)             │
    │ difficulty (L_DAG, δ)           →  Principle (already computed)            │
    │ instance_params                 →  Ω (domain parameters)                   │
    └─────────────────────────────────────────────────────────────────────────────┘
```

The full L2-026b spec.md (`spec_range` block) follows the canonical
CASSI shape — `center_spec` + `allowed_*` lists + `omega_bounds` +
`epsilon_bounds`:

```yaml
# spc/spc_mismatch_only.yaml — SPC L2-026b spec.md
principle_ref: sha256:<L1-026b_hash>     # hash of L1-026b after Tier-1 promotion

spec_range:
  # The canonical center spec — defined by the Principle creator.
  # New specs are evaluated for distance FROM this center.
  center_spec:
    problem_class:    spc_reconstruction
    forward_operator: spc_hadamard
    input_format:     measurement_plus_pattern_set    # measurements + pattern row IDs
    omega:
      n_pixels:       4096      # 64 × 64 image
      sampling_ratio: 0.25      # 25% Nyquist
      noise_level:    0.01      # σ of additive Gaussian
      gain_alpha:     0.0       # nominal — no mismatch
      illum_sigma:    0.0       # nominal — no mismatch
    epsilon_fn_center: "27.0 dB PSNR"

  # Which forward-operator families are in scope for this Principle
  allowed_forward_operators:
    - spc_hadamard               # Walsh-Hadamard {-1,+1} basis (this spec)
    - spc_walsh                  # equivalent up to row permutation

  # Which problem classes this Principle covers
  allowed_problem_classes:
    - spc_reconstruction
    - sparse_recovery

  # Which Ω dimension names are valid for specs under this Principle
  # (system parameters + mismatch parameters)
  allowed_omega_dimensions:
    - n_pixels                   # n = H × W (image size)
    - sampling_ratio             # m / n
    - noise_level                # detector σ
    # Mismatch parameters — physical calibration drift
    - gain_alpha                 # per-measurement gain drift
    - illum_sigma                # DMD illumination Gaussian falloff (px)

  # Valid value ranges for each Ω dimension
  omega_bounds:
    n_pixels:       [1024, 65536]    # 32×32 → 256×256
    sampling_ratio: [0.05, 0.50]     # 5% Nyquist → 50% Nyquist
    noise_level:    [0.001, 0.05]
    # Physically realistic mismatch bounds
    gain_alpha:     [0.0, 0.003]     # ≤0.3% gain drift per measurement
    illum_sigma:    [0.0, 15.0]      # ≤15 px Gaussian falloff width

  # Valid quality threshold range (prevents trivially easy or impossible specs)
  epsilon_bounds:
    psnr_db: [18.0, 40.0]

# epsilon_fn maps any Ω point → minimum acceptable PSNR
epsilon_fn:
  PSNR: "22.0 + 6.0 * log2(sampling_ratio / 0.05) + 1.5 * log10(photon_count / 100)"
  SSIM: "0.55"
  residual_norm: "0.05"

# d_spec from the canonical center
d_spec: 0.38                # vs L2-026 random-projection variant
d_spec_notes: "Differs in structured_basis (Hadamard vs random Gaussian/Bernoulli)
               and operator_class id; same omega axis count, different labels."

s1_s4_gates: ["PASS", "PASS", "PASS", "PASS"]
```

**Key difference: seed vs spec.md** (per `pwm_overview.md` Figure 0d):

| Seed | spec.md |
|---|---|
| 3 fields | 7 fields (six-tuple + `principle_ref`) |
| equations + goal | precise grid, data commitment, thresholds |
| informal | formal YAML with hash-committed data |
| anyone can write | requires Principle + S1-S4 to validate |
| Layer 1 input | Layer 2 output → Layers 3/4 input |
| FREE to submit | earns reward when accepted |

The nine sub-sections below (2.1–2.9) walk each part of the spec in
detail.

## 2.1 Ω — parameter space

`Ω` declares the full RANGE of parameters over which the spec is
defined. Specific evaluations sample `ω ∈ Ω`.

| ω axis | Bounds | What it controls | In L1's θ? |
|---|---|---|---|
| `n_pixels` | `[1024, 65536]` | Image size `n = H × W` (32×32 → 256×256) | yes (system param) |
| `sampling_ratio` | `[0.05, 0.50]` | Fraction `m/n` of measurements taken | yes |
| `noise_level` | `[0.001, 0.05]` | Standard deviation `σ` of Gaussian noise | yes |
| **`gain_alpha`** | `[0.0, 0.003]` | Per-measurement gain drift | **mismatch axis** |
| **`illum_sigma`** | `[0.0, 15.0]` | DMD illumination Gaussian falloff | **mismatch axis** |

**Mismatch axes** = `gain_alpha` and `illum_sigma`. Per
`pwm_overview1.md` § 4 ("Mismatch Parameters as Ω Dimensions"), these
are the "real-world ugliness" knobs the spec tests robustness against
— solvers must work even when `Φ` they assumed differs from the `Φ`
that actually shaped the measurement.

## 2.2 E — forward operator (with mismatch)

```
y_k = ⟨φ_k_Hadamard, x⟩ + n_k
where φ_k may be corrupted by gain drift α and illumination falloff σ.
```

**Primitive chain** (canonical basis):

```
G.structured.random → L.diag.binary → ∫.spatial
```

**Inverse:** recover `x ∈ ℝⁿ` from `m` Hadamard-projection scalars
`y`. Operator id (for routing): `spc_forward_mismatch`.

## 2.3 B — boundary constraints

| Constraint | Required |
|---|---|
| Non-negativity (`x ≥ 0`) | yes |
| Sparsity in wavelet or TV basis | yes |

## 2.4 I — initialization strategy

`zero_init` — solvers start from `x_0 = 0`. The spec is initialisation-
agnostic in the sense that any sparsity-promoting prior + iterative
shrinkage converges from zero under RIP.

## 2.5 O — observable outputs

The spec demands solvers report **three** metrics per reconstruction:

1. **PSNR** (primary, ranking metric) — `10 · log₁₀(MAX² / MSE)`
2. **SSIM** (structural similarity)
3. **`residual_norm`** = `‖y − Φ · x̂‖₂` — sanity check that the
   solver's `x̂` is consistent with the measurements

## 2.6 ε — acceptance threshold function

Per `pwm_overview1.md` § 4 ("The epsilon_fn"), `ε` maps any `ω ∈ Ω`
to the minimum acceptable PSNR.

```
ε_fn(ω) = 22.0 + 6.0 · log₂(sampling_ratio / 0.05)
              + 1.5 · log₁₀(photon_count / 100)        [dB]
```

Worked examples:

| `sampling_ratio` | `photon_count` | `ε_fn` |
|---|---|---|
| 0.05 (minimum) | 100 | 22.0 dB |
| 0.25 (nominal) | 100 | 35.93 dB |
| 0.50 (maximum) | 100 | 41.93 dB |

**Stub-stage inconsistency to resolve at promotion:** L3-026b's T1
hardcodes `ε = 27.0 dB` at `sampling_ratio = 0.25`, but `ε_fn(0.25, 100)
= 35.93 dB`. The discrepancy reflects that the formula was fit
analytically while the T1 baseline was authored against measured
GAP-TV runs. Tier-2 promotion must re-fit `ε_fn` against the four
authored baselines so analytical and empirical agree.

## 2.7 Spec-level metadata

| Field | Value |
|---|---|
| `spec_type` | `mismatch_only` |
| `d_spec` | `0.38` (vs L2-026 random-projection variant — see § 2.8) |
| `display_slug` | `spc` |
| S1-S4 gates | all `PASS` |

## 2.8 Spec distance and the L2-026 sibling

There's a related stub L2-026 (without 'b') that covers **general
single-pixel imaging with random Gaussian/Bernoulli measurement
basis** — a sibling spec that shares the L1 family but differs in:

- Measurement basis: random Gaussian/Bernoulli vs Hadamard `+1/-1`
- `omega_dim` names: same axis count but different axis labels
- `operator_class` id: different routing keys

Per `pwm_overview1.md` § 4 ("Spec Distance and Duplicate Prevention"),
distinct specs need `d_spec ≥ 0.15`. L2-026b has `d_spec = 0.38`
against L2-026 — well above the floor — confirming the Hadamard
variant is genuinely distinct and not a duplicate.

## 2.9 Protocol fields (input/output schema)

The contract solvers must implement:

```yaml
input_format:
  measurements: float32(m)              # the m bucket-detector readings
  pattern_ids: int32(m)                 # row indices of the Walsh-Hadamard matrix
output_format:
  image: float32(H, W)                  # reconstructed grayscale image
```

Patterns are not transmitted directly — only their row indices, since
the matrix is reproducible from a SHA256 seed declared in L3.

---

# Layer 3 — Benchmark (`L3-026b`)

L3 is where the spec meets data. SPC's L3 is a `combined_P_and_I`
artifact that carries **both an I-benchmark suite (4 tiers) and a
P-benchmark (rho=50)** in a single JSON.

Per `pwm_overview1.md` § 5 + `mine_example/pwm_overview.md` Figure 0d
("Two benchmark types"), every spec must have **both** a P-benchmark
and an I-benchmark; the S4 gate at L2 enforces this.

| Aspect | **P-benchmark** | **I-benchmark** |
|---|---|---|
| Full name | Parametric Benchmark | Instance Benchmark |
| Ω draw | Random `ω ∼ Ω` *at evaluation time* | Fixed `ω_i` snapped to a standard tier |
| ε threshold | `ε_fn(ω)` evaluated per draw | Pre-computed scalar from `ε_fn` at each `ω_i` |
| `rho` | **always 50** (full-range generalisation) | **1 / 3 / 5 / 10** per difficulty tier |
| Tests | Broad generalisation across `Ω` | Performance at one operating point |

## 3.0 The canonical L3 directory format (verbatim from `pwm_overview.md` Figure 5a)

A registered SPC benchmark publishes a complete, self-contained,
hash-committed dataset. All six anti-overfitting mechanisms (M1-M6)
are embedded as concrete files inside the dataset.

```
benchmark_spc_mismatch_only/                   # the SPC L3-026b benchmark dataset
│
├── manifest.yaml                              # dataset identity + immutability hashes
│       spec_ref:       sha256:<L2-026b_hash>
│       principle_ref:  sha256:<L1-026b_hash>
│       dataset_hash:   sha256:<entire-dir>
│       generator_hash: sha256:<generate.py>
│       hadamard_seed:  sha256:<seed-string>   # row-permutation seed
│
├── instances/                                 # 20 READY-TO-USE dev instances per tier
│   ├── T1_nominal/
│   │   ├── dev_001/
│   │   │   ├── input.npz        # (measurements y in ℝᵐ, pattern_ids in ℤᵐ)
│   │   │   ├── ground_truth.npz # true image x in ℝ^{64×64}
│   │   │   └── params.yaml      # ω = (n_pixels=4096, sampling=0.25, noise=0.01, …)
│   │   ├── dev_002/ … dev_020/
│   ├── T2_gain_drift/  dev_001..020
│   ├── T3_blind_calibration/  dev_001..020
│   └── T4_undersampled/  dev_001..020         # 80 dev instances total across 4 tiers
│
├── baselines/                                 # M5: method-signature diversity (3 distinct classes)
│   ├── fista_tv/
│   │   ├── solution.npz          # baseline output across all 80 dev instances
│   │   ├── metrics.yaml          # PSNR/SSIM/residual_norm per instance
│   │   └── method.yaml           # method_sig: "L+O" (linear inverse + optimisation)
│   ├── gap_tv_mle/               # method_sig: "L+O"
│   └── lista/                    # method_sig: "L+N" (linear inverse + neural)
│
├── scoring/                                   # M3: deterministic worst-case scoring
│   ├── score.py                  # Q_p = 0.40·coverage + 0.40·margin + 0.20·stratum_pass_frac
│   ├── thresholds.yaml           # ε values from spec.md (T1=27, T2=24.5, T3=22, T4=19)
│   ├── worst_case.py             # Track A: min(PSNR/ε) per stratum
│   ├── median_case.py            # Track B: median PSNR over 50 instances
│   ├── worst_case_parametric.py  # P-benchmark: stratified M3 across H×W strata
│   └── median_case_parametric.py # P-benchmark: 50 uniform Ω samples, median Q
│
├── convergence/                               # M2: convergence-based scoring
│   ├── check_convergence.py      # verifies O(1/√m) recovery rate vs measurement count
│   └── resolutions.yaml          # m ∈ {0.05·n, 0.10·n, 0.25·n, 0.50·n}
│
├── generator/                                 # M1: parameterised random instantiation
│   ├── generate.py               # G(SHA256(h_sub‖k)) draws ω ∼ Ω, builds Φ, samples y
│   ├── params.yaml               # mirrors L2-026b omega_bounds
│   ├── instantiate.py            # wraps generate.py + writes input.npz/ground_truth.npz
│   └── requirements.txt          # numpy, scipy, hadamard helpers
│
├── adversarial/                               # M4: community adversarial testing
│   ├── submit_adversarial.py     # accepts ω that breaks the published SOTA
│   └── adversarial_log.yaml      # record of accepted adversarial instances
│
├── gates/                                     # M6: S1-S4 gate checks
│   ├── check_s1.py               # dimensional consistency (Φ shape, x/y shapes)
│   ├── check_s2.py               # well-posedness (RIP at the declared sampling)
│   ├── check_s3.py               # convergence rate (q ≥ 2 within 100 iters)
│   ├── check_s4.py               # error bound (recovery within C₁σ/√m + C₂‖x − x_s‖₁)
│   └── run_all_gates.py          # orchestrates S1-S4 in sequence
│
└── README.md                                  # human-readable usage guide
```

**Where the six anti-overfitting mechanisms live in SPC's L3:**

| Mech | Purpose | Embedded as |
|---|---|---|
| M1 | Random instantiation (prevents overfitting to dev) | `generator/instantiate.py` — `G(SHA256(h_sub‖k))` builds fresh `(Φ, y, x)` triples for any submission |
| M2 | Convergence-based scoring (detects fake solvers) | `convergence/check_convergence.py` — verifies `‖x̂_m − x‖₂ ∝ 1/√m` |
| M3 | Cross-instance worst-case (no cherry-picking) | `scoring/worst_case.py` — `Q = min(PSNR/ε)` across the rho instances per tier |
| M4 | Community adversarial testing (PoInf-rewarded) | `adversarial/submit_adversarial.py` + `adversarial_log.yaml` — finder-bounty for ω that breaks SOTA |
| M5 | Method-signature diversity (cross-method agreement) | `baselines/*/method.yaml` — three distinct method_sigs (L+O, L+O, L+N); novel signatures earn novelty bonus |
| M6 | S1-S4 gate checks (mathematical verification) | `gates/check_s1..s4.py` — same checks as L1/L2 but evaluated on the dataset |

**Immutability — once published, NOTHING changes:**

- All 80 dev instances (20 × 4 tiers) are fixed forever
- The Hadamard pattern matrix is fixed (same SHA256 seed = same Φ)
- Generator code is fixed (same hash = same outputs)
- Baselines are fixed (FISTA-TV / GAP-TV-MLE / LISTA scores are immutable references)
- Scoring function is fixed (no mid-stream Q formula changes)
- Thresholds are fixed (T1=27, T2=24.5, T3=22, T4=19 dB)
- S1-S4 gate code is fixed (same checks for every solver)

```
Hash chain:
   Principle (sha256:L1-026b)  ← spec.md (sha256:L2-026b)  ← Benchmark (sha256:L3-026b)
```

New version of any layer? → New hash, new artifact ID; old version
stays valid and citable. Immutability is the foundation of the
"verify any cert against an immutable benchmark forever" guarantee.

The four sub-sections below (3.1–3.4) walk SPC's specific dataset
registry, I-benchmark tier table, P-benchmark formula, and M1-M6
implementations.

## 3.1 Dataset registry

| Dataset | Source | Construction |
|---|---|---|
| **Set11** (primary) | Standard SPC testbed (Lena, Monarch, peppers, …) | Grayscale, power-of-2 sizes [32, 64, 128, 256] |
| **BSD68** (secondary) | Berkeley Segmentation 68-image holdout | Same crop schedule |

**Hadamard pattern construction:** SHA256-seeded RNG selects row
indices from the Walsh-Hadamard matrix (deterministic across runs);
row indices stored in the per-instance `meta.json`.

**Dataset CID:** `null` today. Promotion to Tier-2 requires pinning
Set11 + BSD68 + their grayscale crops to IPFS and recording the CIDs
here. Until then there is no canonical dataset on which to compute Q.

**`num_dev_instances_per_tier`:** 20.

## 3.2 I-benchmark — the 4 difficulty tiers

Each I-benchmark fixes a specific `ω_i` and evaluates the solver on
`rho` instances at that point. ε floors decline as `ω` moves into the
mismatched / undersampled regime:

| Tier | `rho` | `n_pixels` | `sampling_ratio` | `noise_level` | `gain_α` | `illum_σ` | ε (dB) | `d_ibench` |
|---|---|---|---|---|---|---|---|---|
| **T1_nominal** | 1 | 4,096 (64²) | 0.25 | 0.01 | 0.0 | 0.0 | **27.0** | 0.14 |
| **T2_gain_drift** | 3 | 4,096 (64²) | 0.25 | 0.02 | 0.0015 | 5.0 | **24.5** | 0.30 |
| **T3_blind_calibration** | 5 | 16,384 (128²) | 0.15 | 0.03 | 0.0025 | 10.0 | **22.0** | 0.50 |
| **T4_undersampled** | 10 | 65,536 (256²) | 0.05 | 0.05 | 0.003 | 15.0 | **19.0** | 0.72 |

The `rho` progression `1 → 3 → 5 → 10` follows the canonical I-bench
difficulty scale (`pwm_overview1.md` § 5 "Mismatch Tiers"). Each tier
draws that many instances at the fixed `ω_i` and reports an aggregate
PSNR + Q.

`d_ibench` is the per-tier distance to T1, ensuring tiers are
genuinely distinct difficulty regimes (`pwm_overview1.md` § 5.7
"I-Benchmark Distance").

### Authored baseline performance per tier (PSNR / Q)

| Tier | FISTA-TV | GAP-TV-MLE | LISTA |
|---|---|---|---|
| T1_nominal | 26.8 / 0.64 | 28.4 / 0.76 | **32.0 / 0.92** |
| T2_gain_drift | 23.2 / 0.46 | 25.0 / 0.56 | **27.2 / 0.72** |
| T3_blind_calibration | 20.4 / 0.38 | 22.1 / 0.50 | **24.0 / 0.62** |
| T4_undersampled | 17.5 / 0.24 | 18.8 / 0.34 | **20.3 / 0.48** |

These are **authored reference values** — the benchmark author runs
each baseline solver across the tier's `rho` instances and records
the resulting PSNR + Q in the manifest. They are NOT auto-computed
from a single PSNR value.

## 3.3 P-benchmark — the rho=50 aggregate

The P-benchmark is the **headline ranking score** — 50 instances
drawn parametrically across `Ω`, scored as a distribution (not a
single PSNR). Per `pwm_overview1.md` § 5 "P-Benchmark Evaluation
Protocol".

| Field | Value |
|---|---|
| `rho` | 50 |
| Dataset | Set11 + BSD68 union |
| `num_dev_instances` | 200 |
| `num_holdout_instances` | 100 |
| Construction | parametric sampling over `(n_pixels, sampling_ratio, gain_α, illum_σ)` |

### Authored P-benchmark baselines (overall Q from `_compute_q_p`)

| Solver | overall_Q |
|---|---|
| FISTA-TV | 0.45 |
| GAP-TV-MLE | 0.55 |
| **LISTA** (current SOTA) | **0.70** |

**Q_int = 70** would be the rank-1 bar against today's reference
field. Q is computed via the production engine
(`pwm-team/infrastructure/agent-scoring/pwm_scoring/score.py:_compute_q_p`):

```
Q_p = 0.40 · coverage + 0.40 · margin + 0.20 · stratum_pass_frac
```

Where `coverage` = fraction of instances clearing `ε_fn(ω)`, `margin`
= mean `(PSNR/ε − 1)` on passing instances (saturated at 1.0), and
`stratum_pass_frac` = fraction of Track-A strata passing.

### Hardness check

L3-026b's `hardness_rule_check` field declares **SATISFIED** — even
LISTA (the strongest authored baseline) doesn't beat the full
P-benchmark across all strata, because RIP degrades at 5% sampling
in T4. That guarantees the benchmark isn't trivially saturated; there
remains room for solver innovation, exactly the property a PWM
benchmark needs (`pwm_overview1.md` § 5 "Benchmark Validation").

## 3.4 The six anti-overfitting mechanisms (M1-M6)

Per `pwm_overview1.md` § 5 ("The Six Anti-Overfitting Mechanisms"),
every L3 must implement six guards. SPC's:

| Mechanism | SPC implementation |
|---|---|
| **M1** Held-out test set | BSD68 reserved as test-only; Set11 = dev |
| **M2** Random Ω draws | P-benchmark draws fresh `ω` at evaluation time |
| **M3** Stratified worst-case | Track-A reports min-PSNR per H×W stratum (S1-S4) |
| **M4** Adversarial reward | Bounty for finding ω that breaks the published SOTA |
| **M5** Dataset rotation | New `dataset_registry` entry every 12 months → new L3 |
| **M6** Hash-bound submission | Cert binds `(solver_id, benchmark_hash, ω_instance)` |

---

# Layer 4 — Solution (`L4` certs)

L4 is the mining loop: a Solution Provider runs a solver against the
benchmark, computes `Q`, and submits a tamper-resistant certificate
on-chain.

## 4.1 The cert payload (15 fields)

```jsonc
{
  // 12 chain-bound fields (canonical_json keccak256'd → certHash):
  "Q_int":             70,                           // round(Q × 100) ∈ [0, 100]
  "benchmarkHash":     "0x2d88…3ba2",                // keccak256(canonical L3-026b)
  "principleId":       26,                           // numeric ID of L1-026b
  "delta":             3,                            // difficulty_delta from L1
  "spWallet":          "0x…",                        // Solution Provider (the miner)
  "acWallet":          "0x…",                        // Algorithm Contributor (solver author)
  "cpWallet":          "0x…",                        // Compute Provider (GPU runner)
  "l1Creator":         "0x…",                        // who registered L1-026b
  "l2Creator":         "0x…",                        // who registered L2-026b
  "l3Creator":         "0x…",                        // who registered L3-026b
  "shareRatioP":       5000,                         // SP share × 10000 (default 0.50)
  "submittedAt":       1777800000,                   // unix timestamp from EVM block

  // 3 inspection-only fields (stripped before keccak by the canonical filter):
  "_meta": {
    "solver_label":   "LISTA-SPC",
    "psnr_db":        32.0,
    "framework":      "PyTorch 2.1 + CUDA 12.1",
    "Q_float":        0.70,
    "gate_verdicts":  {"S1": "pass", "S2": "pass", "S3": "pass", "S4": "pass"}
  }
}

certHash = keccak256(canonical_json(payload))     // strips _meta + UI-only
```

The 12 chain-bound fields are immutable on PWMCertificate; `_meta` is
optional off-chain enrichment posted via `POST /api/cert-meta/{hash}`
(it surfaces the human label on the leaderboard but doesn't change
ranking or rewards).

## 4.2 The 5-command mining flow

```bash
# 1. (One-time) Stake on the L1 Principle to back the problem
pwm-node --network testnet stake principle 0x<L1-026b-hash>

# 2. (One-time) Stake on the L3 Benchmark
pwm-node --network testnet stake benchmark 0x<L3-026b-hash>

# 3. Mine — run your solver, score across rho=50, submit cert
pwm-node --network testnet mine L3-026b \
  --solver pwm-team/pwm_product/reference_solvers/spc/spc_lista.py
# Output:
#   [mine] runtime=12.3s  PSNR=32.0 dB  Q=0.70
#   [mine] cert_hash:      0xb293…
#   [mine] tx submitted:   0xabcd…

# 4. Wait 7 days for the challenge period

# 5. Finalize — triggers reward distribution (no CLI wrapper yet,
#    direct Foundry call):
cast send <PWMCertificate-addr> "finalize(bytes32)" 0x<cert-hash> \
  --rpc-url $SEPOLIA_RPC_URL --private-key $PWM_PRIVATE_KEY
```

## 4.3 Reference solvers (Tier-2 promotion deliverables)

Three baseline classes need to ship in `pwm_product/reference_solvers/spc/`:

| Solver | Class | T1 PSNR | T1 Q | P-bench Q | Implementation notes |
|---|---|---|---|---|---|
| **FISTA-TV** | classical (proximal gradient) | 26.8 dB | 0.64 | 0.45 | Iterative shrinkage + TV prox; CPU-runnable; ~30 s/scene |
| **GAP-TV-MLE** | classical (generalised alternating projection) | 28.4 dB | 0.76 | 0.55 | Better TV-prior + MLE noise model; CPU-runnable; ~60 s/scene |
| **LISTA** | learned (unrolled neural network) | 32.0 dB | 0.92 | **0.70** | Deep-learning SOTA; GPU-needed; ~2 s/scene; pretrained weights on Set11 |

CASSI's 4 solvers in `pwm_product/reference_solvers/cassi/` are the
template — minimal CLI signature `python solver.py --input <dir>
--output <dir>`, deterministic given a seed in `meta.json`.

## 4.4 Reward distribution (rank-1 hypothetical)

If a rank-1 cert lands at `Q_int = 70` against a pool of 1,000 PWM:

| Role | Share | Amount |
|---|---|---|
| Algorithm Contributor (AC) | `40% × 0.55 × p` (`p = shareRatioP / 10000`) | 110 PWM at `p = 0.50` |
| Compute Provider (CP) | `40% × 0.55 × (1−p)` | 110 PWM at `p = 0.50` |
| L3-026b creator | `40% × 0.15` | 60 PWM |
| L2-026b creator | `40% × 0.10` | 40 PWM |
| L1-026b creator | `40% × 0.05` | 20 PWM |
| Treasury T_k | `40% × 0.15` | 60 PWM |
| **Subtotal rank-1** | **40%** | **400 PWM** |
| Rank 2 | 5% | 50 PWM |
| Rank 3 | 2% | 20 PWM |
| Ranks 4–10 | 1% each | 70 PWM total |
| Rolls over to next epoch | ~52% | 520 PWM |

`maxBenchmarkPoolWei` caps the absolute risk per benchmark — at
mainnet launch the Treasury seeds new L3s with ~50–100 PWM until a
track record builds.

## 4.5 The dual-role architecture (SP vs CP)

Per `pwm_overview1.md` § 6 ("L4 Dual-Role Architecture"):

- **Solution Provider (SP)** owns the algorithm — picks `solver.py`,
  declares `shareRatioP` (the AC/CP split), publishes pretrained
  weights / commits to a model
- **Compute Provider (CP)** owns the GPU minutes — pulls the solver,
  runs against the benchmark, signs the cert with their wallet

For SPC, all three reference solvers are SP/CP-collapsable: the same
person can run all roles. As external miners join, the split lets a
LISTA-trainer (SP) earn from many GPU operators (CPs) running their
weights.

---

# Hash chain — immutability across all four layers

Per `pwm_overview1.md` § 2 ("Immutability and the On-Chain Registry")
+ `mine_example/pwm_overview.md` Figure 0a, every layer's artifact
hash is computed by stripping a known-UI-only field set, then
keccak256'ing the canonical JSON:

```
canonical_for_hashing(obj):
    strip {display_slug, display_color, ui_metadata,
           registration_tier, display_baselines}    # UI_ONLY_FIELDS
    return obj sorted-key, no-whitespace JSON

artifact_hash = keccak256(canonical_for_hashing(obj))
```

Current SPC hashes (Tier-3 stub, not yet on-chain):

| Layer | Computed hash (will register at) |
|---|---|
| L1-026b | `0x81069639f3f76182baaa5e62acaa11da1598f3eada05972dc22d8084722f814d` |
| L2-026b | (compute via `python -c …` against `L2-026b_spc.json`) |
| L3-026b | `0x2d88771166293b57611b35cfd7578ab45ebc57ad635d409ed1878ffb28bf3ba2` |

L4 cert hashes are likewise `keccak256(canonical_payload)` where the
canonical filter strips `_meta`. Per `pwm_overview1.md` § 6, the
canonical filter must be IDENTICAL across `register_genesis.py`,
`pwm-node mine`, and the contract — so any cert-meta enrichment never
changes the cert's identity or its rank.

---

# Mining strategies

| Strategy | Pros | Cons |
|---|---|---|
| **Tier-by-tier** — clear T1 first, then T2, … | Predictable Q gains; easy to debug | T4 (5% sampling) may need fundamentally different solver |
| **All-in on LISTA** — train on Set11 → expect P-bench Q ≈ 0.70 | Beats classical floor by 25 pp | GPU + training data required; 4-6 weeks of work |
| **Adversarial on M4** — find `ω ∈ Ω` where SOTA fails | Treasury bounty payout; uplift T_k | Requires deep RIP/calibration insight |
| **Dataset extension (M5)** — pin a new dataset (e.g. medical PET) | New L3 ID with own pool | Must clear S4 gate against base spec |

---

# What you cannot do

Per `pwm_overview1.md` § 5 + § 6 limits:

- **Modify L1/L2/L3 after registration** — manifest hashes are immutable;
  any change spawns a new artifact ID + a new pool
- **Submit `Q_int > 100`** — out-of-range certs are filtered from the
  public leaderboard (see `_is_synthetic_cert`)
- **Skip the 7-day challenge window** — `PWMCertificate.finalize` reverts
  before the window elapses
- **Stake-and-unstake to game royalties** — staked PWM is locked for
  the artifact's lifetime; redemption requires de-listing

---

# Promotion path — Tier 3 stub → Tier 1 founder-vetted

What's gating mineable status today (per `customer_guide/PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md`):

- [ ] Author `pwm_product/reference_solvers/spc/spc_fista_tv.py`
      (CPU, ~3 hours)
- [ ] Synthesize 10 Set11 samples at the 4 tier `ω` configurations
      (~1 hour)
- [ ] Bundle samples in `pwm_product/demos/spc/sample_01..10/` with
      SHA-256 fingerprints in `meta.json` (~30 min)
- [ ] Pin Set11 + BSD68 to IPFS, record CIDs in
      `L3-026b.dataset_registry.cid` (~30 min)
- [ ] Re-fit `ε_fn(0.25, 100)` against the measured GAP-TV baseline so
      analytical and empirical agree (~1 hour)
- [ ] Verifier-agent triple-review (PR labelled `bounty-07-claim`)
- [ ] 3-of-5 multisig signs `PWMRegistry.register()` for L1/L2/L3-026b
- [ ] Pool seeded via `PWMReward.fundPool()` (~50 PWM until track record)
- [ ] Set `registration_tier: "founder_vetted"` on all three manifests
      (the field is in `UI_ONLY_FIELDS` → hash invariant)

After all of the above, SPC becomes the **third mineable Principle**
on Sepolia, alongside CASSI (L1-003) and CACTI (L1-004).

---

# Quick-start commands

```bash
# Clone + install
git clone --recursive https://github.com/integritynoble/pwm-public.git
cd pwm-public
pip install -e pwm-team/infrastructure/agent-cli

# Browse SPC manifests
ls pwm-team/content/agent-imaging/principles/B_compressive_imaging/L*-026b*

# Read the SPC L1 in formatted form (works today even on stubs via jq)
jq . pwm-team/content/agent-imaging/principles/B_compressive_imaging/L1-026b_spc.json

# Run SPC's would-be P-benchmark (post-promotion)
pwm-node --network testnet mine L3-026b \
  --solver pwm-team/pwm_product/reference_solvers/spc/spc_lista.py \
  --dry-run                                      # works without spending Sepolia ETH

# After 7-day challenge clean (post-promotion):
cast send <PWMCertificate-addr> "finalize(bytes32)" 0x<cert-hash>
```

---

# Cross-references

**Source manifests:**

- `pwm-team/content/agent-imaging/principles/B_compressive_imaging/L1-026b_spc.json`
- `pwm-team/content/agent-imaging/principles/B_compressive_imaging/L2-026b_spc.json`
- `pwm-team/content/agent-imaging/principles/B_compressive_imaging/L3-026b_spc.json`

**Canonical PWM specifications followed verbatim:**

- `papers/Proof-of-Solution/pwm_overview1.md` § 3-6 (system reference for L1/L2/L3/L4)
- `papers/Proof-of-Solution/mine_example/pwm_overview.md` Figures 0–9 (lifecycle, six-tuple, immutability, primitive decomposition)
- `papers/Proof-of-Solution/mine_example/primitives.md` (line 88, 118, 505, 567)

**Adjacent customer-guide docs:**

- `PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md` — main user-facing reference (§ "Registration tiers")
- `PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md` — full Tier-3 → Tier-2 promotion flow + verifier-agent triple-review checklist
- `PWM_SPC_PRINCIPLE_REVIEW_2026-05-07.md` — pre-mining review of SPC's stub state (this doc's predecessor; consumer-side perspective)
- `PWM_Q_SCORE_EXPLAINED_2026-05-06.md` — how Q_p is computed by `_compute_q_p`
- `PWM_VERIFY_MST_L_CASSI_CLAIM_2026-05-06.md` — 5-layer verification flow that would apply to an SPC cert post-mining
- `PWM_ONCHAIN_VS_OFFCHAIN_ARCHITECTURE_2026-05-05.md` — what binds Q_int to the cert hash on-chain

**Related stub** (general single-pixel, NOT Hadamard-specific):

- L1-026 / L2-026 / L3-026 — general random-projection single-pixel
  (`d_spec ≈ 0.38` from this Hadamard variant)

**Live explorer:**

- `https://explorer.pwm.platformai.org/principles/L1-026b` — SPC's
  public stub detail page (with the amber "claim this stub" CTA)
