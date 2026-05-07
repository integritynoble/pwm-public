# SPC Principle Review — Single-Pixel Camera (Hadamard Structured Illumination)

**Date:** 2026-05-07
**Audience:** Director (pre-mining review), future contributor claiming this stub
**Trigger question (Director, 2026-05-07):**
> "Please give the SPC principle in one md file. I need to review it
> before I mine to testnet."

---

## ⚠️ Status — read this first

| Layer | artifact_id | Tier | Mineable today? |
|---|---|---|---|
| L1 Principle | `L1-026b` | **stub** | ✗ Not registered on-chain |
| L2 Spec | `L2-026b` | **stub** | ✗ Not registered on-chain |
| L3 Benchmark | `L3-026b` | **stub** | ✗ Not registered on-chain, no dataset CID, no reference solver |

**Mining `L3-026b` on Sepolia today will not pay out.** A `pwm-node mine` call
either fails to resolve the artifact (CLI walks `pwm_product/genesis/` only; SPC
lives in the content tree) or — if you point at the JSON directly — produces a
benchmarkHash that has no on-chain registration, so `PWMCertificate.submit`
reverts with `"PWMCertificate: benchmark not registered"`.

To mine SPC for real on Sepolia, the principle must first be **promoted from
Tier 3 (stub) to Tier 1 (founder-vetted) or Tier 2 (community-vetted)**. That
requires three missing pieces:

1. **Reference solver** (e.g., `pwm-team/pwm_product/reference_solvers/spc/spc_fista_tv.py`)
2. **At least 1 IPFS-pinned dataset** (e.g., Set11 + BSD68 grayscale crops)
3. **3-of-5 multisig signing `PWMRegistry.register()`** for L1-026b, L2-026b, L3-026b

For the Tier 3→Tier 2 contribution flow, see
`pwm-team/customer_guide/PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md`.

You can still *dry-run* the mining flow to verify the harness works end-to-end
without expecting payout. See "Dry-run testing" near the bottom of this doc.

---

## 1. What is the Single-Pixel Camera (SPC)?

SPC is a compressive imaging modality where:

- A **DMD (digital micromirror device)** projects a sequence of binary `+1/-1`
  Hadamard patterns onto an incoming optical field
- A **single photodetector** integrates the pattern-weighted irradiance once
  per pattern, producing one scalar measurement
- After `m` patterns, you have an `m`-dimensional measurement vector
- If the underlying image is **sparse in some basis** (TV / wavelet) and `m/n ≥ 0.05` (Hadamard sampling satisfies RIP at this rate), you can recover the full `H × W` image

This is the canonical "compressive sensing in the wild" demo — a $5 photodiode
+ a $200 DMD reconstructs images that would otherwise require an entire focal
plane array.

**Why it matters:**
- Imaging in spectral bands where dense detectors are expensive (THz, mid-IR, X-ray)
- Single-photon / photon-counting regimes
- Imaging through scattering media (where DMD-modulated structured illumination buys SNR)

---

## 2. The forward model (E)

```
y_k = ⟨φ_k, x⟩ + n_k     for k = 1, …, m

where:
  x ∈ ℝⁿ          — vectorized image, n = H × W (non-negative)
  φ_k ∈ {-1, +1}ⁿ  — k-th row of a Walsh-Hadamard basis (binary pattern)
  y_k ∈ ℝ           — k-th scalar photodetector reading
  n_k ∼ 𝒩(0, σ²)   — additive Gaussian noise (photon shot + read noise)
  m / n             — sampling ratio (typically 0.05–0.5)
```

In matrix form: `y = Φ x + n`, with `Φ ∈ ℝ^{m × n}`, `m << n`.

**Recovery problem:** given measurement `y` and known pattern matrix `Φ`,
recover `x` from an underdetermined system. Solved via convex optimization
(FISTA-TV, GAP-TV-MLE) or a learned unrolled network (LISTA, ISTA-Net).

### DAG primitive chain

```
S.pattern.hadamard  →  L.inner_product  →  int.temporal  →  D.scalar
   (DMD pattern)      (photon × pattern)    (integrate)    (single readout)
```

L_DAG = 3.0, n_c = 0 (single physics chain, no coupling).

### Physical parameters θ

- `Phi_Hadamard`: Walsh-Hadamard rows, permutation seeded from a deterministic RNG
- `sampling_ratio m/n`: how much you compress (lower = harder)
- `gain α`: photodetector gain drift per measurement
- `illumination σ`: spatial non-uniformity of DMD illumination (Gaussian falloff)
- `DMD timing`: dwell time per pattern, duty cycle

---

## 3. Well-posedness (W)

| Property | Value | Meaning |
|---|---|---|
| Existence | true | A solution always exists for compatible `(y, Φ)` pairs |
| Uniqueness | true | Given Φ satisfies RIP at `m/n ≥ 0.05`, the sparse reconstruction is unique |
| Stability | **conditional** | Stable if RIP holds; unstable when sampling drops below the compression-ratio gate at 5% |
| Condition number κ | 3,000 | Raw ill-conditioning before regularization |
| Effective κ | 30 | After TV-prior regularization |
| Regime | "Hadamard at 25% sampling satisfies RIP for sparse recovery; TV-objective required to handle gain-drift + illumination non-uniformity (residual self-consistency fails for SPC)" | |

**Implication for solvers:** you cannot just least-squares the linear system
— you need a sparsity-promoting regularizer (TV, wavelet, or learned prior).
Otherwise gain drift gets absorbed into noise and reconstruction collapses.

---

## 4. Solvability (C)

```
Solver class:        FISTA-TV, ISTA-Net, LISTA, learned deep unrolling
Convergence rate q:  2.0  (linear in iteration count)
Error bound:         ‖x̂ - x‖₂  ≤  C₁ · σ / √m  +  C₂ · ‖x - x_s‖₁
                                         ↑ noise term            ↑ best s-sparse approx
Complexity:          O(n log n) per iteration (fast Hadamard transform)
```

The error bound is **the canonical compressed-sensing recovery guarantee**:
reconstruction quality scales as `1/√m` in noise and as the best sparse
approximation of `x` (the closer `x` is to truly sparse, the better).

---

## 5. Parameter space Ω (allowed dimensions and bounds)

The L2-026b spec defines what falls "in scope" for SPC mining:

| ω axis | Bounds | What it controls |
|---|---|---|
| `n_pixels` | `[1024, 65536]` | Image size n = H × W (32×32 to 256×256) |
| `sampling_ratio` | `[0.05, 0.50]` | Fraction `m/n` of measurements taken |
| `noise_level` | `[0.001, 0.05]` | Standard deviation σ of Gaussian noise |
| `gain_alpha` | `[0.0, 0.003]` | Per-measurement gain drift (mismatch axis) |
| `illum_sigma` | `[0.0, 15.0]` | DMD illumination Gaussian falloff (mismatch axis) |

**Mismatch axes** = `gain_alpha` and `illum_sigma`. These are the
"real-world ugliness" knobs the L2 spec tests robustness against.

**Allowed forward operators:** `spc_hadamard`, `spc_walsh` (these two are
mathematically equivalent up to permutation; protocol-level equivalence)

---

## 6. Scoring (ε)

**Primary metric:** PSNR (dB)
**Secondary metric:** SSIM
**ε bounds:** `[18.0 dB, 40.0 dB]` (acceptance threshold range across Ω)

**Epsilon function** (from L2-026b):
```
epsilon_fn(ω) = 22.0 + 6.0 · log₂(sampling_ratio / 0.05) + 1.5 · log₁₀(photon_count / 100)
```

So:
- At `sampling_ratio = 0.25` and nominal photons → `epsilon ≈ 22.0 + 6.0 × log₂(5.0) + 1.5 × log₁₀(1) = 22.0 + 13.93 + 0 ≈ 35.9 dB` floor… wait, that's high.

**Actually the L3-026b T1_nominal tier reports `epsilon: 27.0 dB`** at exactly
those conditions, suggesting the manifest's `epsilon_fn` formula is used at
spec-time but T1 hardcodes a floor that's been calibrated against measured
baseline performance. **This is a known stub-stage inconsistency** that would
be cleaned up when promoting to Tier 1/2 — the formula needs to be re-fit
against the FISTA-TV/LISTA performance curve at each tier.

---

## 7. The 4 difficulty tiers (L3-026b benchmark suite)

Each tier is an "I-benchmark" — a single ω instance with a baseline ε.

| Tier | n_pixels | sampling | noise | gain α | illum σ | ε (dB) | d_ibench |
|---|---|---|---|---|---|---|---|
| **T1_nominal** | 4096 (64×64) | 0.25 | 0.01 | 0.0 | 0.0 | 27.0 | 0.14 |
| **T2_gain_drift** | 4096 (64×64) | 0.25 | 0.02 | 0.0015 | 5.0 | 24.5 | 0.30 |
| **T3_blind_calibration** | 16384 (128×128) | 0.15 | 0.03 | 0.0025 | 10.0 | 22.0 | 0.50 |
| **T4_undersampled** | 65536 (256×256) | 0.05 | 0.05 | 0.003 | 15.0 | 19.0 | 0.72 |

The full P-benchmark is **rho=50** instances drawn across these tiers + the
parametric Ω, scored as a distribution.

### Authored baselines per tier

| Tier | FISTA-TV (PSNR / Q) | GAP-TV-MLE (PSNR / Q) | LISTA (PSNR / Q) |
|---|---|---|---|
| T1_nominal | 26.8 dB / 0.64 | 28.4 dB / 0.76 | **32.0 dB / 0.92** |
| T2_gain_drift | 23.2 / 0.46 | 25.0 / 0.56 | **27.2 / 0.72** |
| T3_blind_calibration | 20.4 / 0.38 | 22.1 / 0.50 | **24.0 / 0.62** |
| T4_undersampled | 17.5 / 0.24 | 18.8 / 0.34 | **20.3 / 0.48** |

### Full P-benchmark (rho=50) overall Q

| Solver | overall_Q |
|---|---|
| FISTA-TV | 0.45 |
| GAP-TV-MLE | 0.55 |
| **LISTA** (current SOTA) | **0.70** |

→ Q_int=70 would be the bar for rank-1 if this were registered today.

---

## 8. Hardness check

The `hardness_rule_check` field in L3-026b says:

> **SATISFIED** — LISTA fails at T4_undersampled (20.3 dB > 19.0 ε here but
> fails strata S3/S4 in full P-bench due to RIP degradation at 5% sampling).

Translation: even the strongest authored baseline (LISTA) doesn't beat the
full P-benchmark across all strata, so the benchmark isn't trivially saturated.
Good — that means there's *room for solver innovation*, which is the whole
point of a PWM benchmark.

---

## 9. Datasets (L3-026b dataset_registry)

| Dataset | Source | Construction |
|---|---|---|
| **Set11** | Standard SPC testbed (Lena, Monarch, peppers, etc.) | Grayscale, power-of-2 sizes [32, 64, 128, 256] |
| **BSD68** (secondary) | Berkeley Segmentation Dataset 68-image holdout | Same crop schedule |

**Hadamard pattern construction:** SHA256-seeded RNG selects row indices from
the Walsh-Hadamard matrix (deterministic across runs).

**Dataset CID:** `null` today. Promotion to Tier 2 requires pinning Set11 (or
a re-derivation of it) to IPFS and recording the CID here.

---

## 10. Pre-mining review checklist

If you're considering claiming this stub or just dry-running it for
familiarity, here's what to check:

| Check | Status today | Action to mine for real |
|---|---|---|
| L1-026b forward model is internally consistent | ✓ | None |
| L2-026b spec ε_fn yields bounded values across Ω | ⚠ formula vs T1 hardcoded ε differ | Re-fit ε_fn against measured baseline curve |
| L3-026b has a dataset CID | ✗ | Pin Set11 + BSD68 to IPFS, fill `dataset_registry.cid` |
| Reference solver exists in `pwm-team/pwm_product/reference_solvers/spc/` | ✗ | Author `spc_fista_tv.py` (CPU-runnable) — ~2-4 hours |
| L1-026b registered on-chain | ✗ | Add to `ARTIFACTS_TO_REGISTER` in `scripts/register_genesis.py`, run with `--network testnet`, capture tx hashes |
| Benchmark pool funded | ✗ | Treasury funds via `PWMReward.fundPool()` — keep small (~50 PWM) until track record |
| All hashes invariant under `display_slug=spc` (UI_ONLY) | ✓ | Already correct — `display_slug` is in `UI_ONLY_FIELDS` |

---

## 11. Dry-run testing (works today, no payout)

You can exercise the harness end-to-end without the artifact being registered,
because `pwm-node mine --dry-run` skips the chain submission step:

```bash
cd /home/spiritai/pwm/Physics_World_Model/pwm

# 1. Copy the SPC L3 manifest into the genesis dir so the CLI can find it
mkdir -p pwm-team/pwm_product/genesis/l1 pwm-team/pwm_product/genesis/l2 pwm-team/pwm_product/genesis/l3
cp pwm-team/content/agent-imaging/principles/B_compressive_imaging/L1-026b_spc.json pwm-team/pwm_product/genesis/l1/
cp pwm-team/content/agent-imaging/principles/B_compressive_imaging/L2-026b_spc.json pwm-team/pwm_product/genesis/l2/
cp pwm-team/content/agent-imaging/principles/B_compressive_imaging/L3-026b_spc.json pwm-team/pwm_product/genesis/l3/

# 2. Try to dry-run mine — this will FAIL for a different reason now:
#    "no reference solver" / "no dataset to feed the solver"
pwm-node mine L3-026b \
  --solver pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py \
  --dry-run
```

**Expected result:** the CLI now resolves the artifact (you've copied it to
the genesis dir), but mining will fail because:
- The CASSI GAP-TV solver expects CASSI inputs (mask + dispersion + 3D cube),
  not SPC inputs (Hadamard patterns + 1D measurement vector)
- There's no SPC dataset to feed the solver

To do a *real* dry-run you'd also need to:
1. Author `pwm_product/reference_solvers/spc/spc_fista_tv.py` with CLI signature `--input <dir> --output <dir>`
2. Synthesize a small Set11 sample at T1_nominal Ω (or download from a public mirror)
3. Bundle the sample in `pwm_product/demos/spc/sample_01/`

That's the smallest viable "Tier 2 promotion" package: ~4-6 hours of work and
the principle becomes mineable on Sepolia.

---

## 12. What to do next (3 options)

| Option | Effort | Outcome |
|---|---|---|
| **A. Just review and walk away** | 0 | You understand SPC; no code/chain change |
| **B. Dry-run hand-test** | ~30 min | Run the dry-run blocks above, see what fails, internalize the harness shape |
| **C. Promote SPC to Tier 1** | ~6-12 hours | Author solver + bundle dataset + register on Sepolia → SPC becomes a real benchmark on the leaderboard alongside CASSI/CACTI |

If you want to do (C), the natural sequence is:
1. Author `spc_fista_tv.py` (CPU-runnable, ~3 hours — it's just FISTA + a TV prox operator + fast Hadamard transform)
2. Synthesize 10 Set11 samples at the 4 tier ω configurations (~1 hour)
3. Bundle samples in `demos/spc/sample_01..10/` with SHA-256 fingerprints in `meta.json` (~30 min)
4. Set `registration_tier: founder_vetted` on L1/L2/L3-026b (the field is in `UI_ONLY_FIELDS` so the hash stays the same)
5. Add `("L1-026b", "l1/L1-026b.json", 1), ("L2-026b", "l2/L2-026b.json", 2), ("L3-026b", "l3/L3-026b.json", 3)` to `ARTIFACTS_TO_REGISTER`
6. Run `python3 scripts/register_genesis.py --network testnet --dry-run` first; then drop `--dry-run` to actually broadcast

The reward for promoting a stub: SPC becomes the third mineable Principle on
Sepolia, doubles the reachable bounty surface for external miners, and gives
the customer guide a non-CASSI, non-CACTI third example.

---

## Cross-references

- **Source JSONs (review against these):**
  - `pwm-team/content/agent-imaging/principles/B_compressive_imaging/L1-026b_spc.json`
  - `pwm-team/content/agent-imaging/principles/B_compressive_imaging/L2-026b_spc.json`
  - `pwm-team/content/agent-imaging/principles/B_compressive_imaging/L3-026b_spc.json`
- **Source paper / mine_example reference:**
  - `papers/Proof-of-Solution/mine_example/spc.md` (referenced from L1's `reference_mine_example`)
- **Related stub (general single-pixel, NOT SPC-Hadamard):**
  - `L1-026 / L2-026 / L3-026` — generic random-projection single-pixel imaging (`d_spec ≈ 0.38` from this Hadamard variant)
- **Customer guide cross-references:**
  - `PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md` § "Registration tiers"
  - `PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md` (full Tier 3 → Tier 2 promotion flow)
  - `PWM_HANDS_ON_TEST_WALKTHROUGH_2026-05-07.md` (the mining harness this would slot into)
- **Live explorer:**
  - `https://explorer.pwm.platformai.org/principles/L1-026b` — the public stub detail page (with the amber claim CTA)
