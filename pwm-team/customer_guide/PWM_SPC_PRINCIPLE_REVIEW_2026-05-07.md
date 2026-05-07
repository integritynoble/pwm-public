# SPC Layer-by-Layer Review — Single-Pixel Camera (Hadamard Structured Illumination)

**Date:** 2026-05-07
**Audience:** Director (pre-mining review), future contributor claiming this stub
**Trigger questions (Director, 2026-05-07):**
> "Please give the SPC principle in one md file. I need to review it
> before I mine to testnet."
> "Please also add SPC's principle, spec, benchmarks (P-benchmark and
> I-benchmark) and solutions in one md file."

---

## ⚠ Status — read this first

| Layer | artifact_id | Tier | Mineable today? |
|---|---|---|---|
| L1 Principle | `L1-026b` | **stub** | ✗ Not registered on-chain |
| L2 Spec | `L2-026b` | **stub** | ✗ Not registered on-chain |
| L3 Benchmark | `L3-026b` | **stub** | ✗ Not registered on-chain, no dataset CID |
| L4 Solution | (none submitted yet) | n/a | ✗ Cannot submit until L3 is registered |

**Mining `L3-026b` on Sepolia today will not pay out.** A `pwm-node mine`
call either fails to resolve the artifact (CLI walks `pwm_product/genesis/`
only; SPC lives in the content tree) or — if forced to recognize it —
produces a benchmarkHash that has no on-chain registration, so
`PWMCertificate.submit` reverts with
`"PWMCertificate: benchmark not registered"`.

Verified live (2026-05-07) by computing L3-026b's would-be canonical hash
(`0x2d88771166293b57611b35cfd7578ab45ebc57ad635d409ed1878ffb28bf3ba2`) and
calling `PWMRegistry.exists(...)` → returned `False`. **Tier 3 inertness is
structural, not just a CLI-visibility artifact.**

To make SPC mineable: see § "Next-step options" near the bottom.

---

# Layer 1 — Principle (`L1-026b`)

## 1.1 What is SPC?

SPC is a compressive imaging modality where:

- A **DMD (digital micromirror device)** projects a sequence of binary `+1/-1`
  Hadamard patterns onto the incoming optical field
- A **single photodetector** integrates the pattern-weighted irradiance once
  per pattern, producing one scalar measurement
- After `m` patterns, you have an `m`-dimensional measurement vector
- If the underlying image is sparse in some basis (TV / wavelet) and `m/n ≥ 0.05`
  (Hadamard sampling satisfies RIP at this rate), you can recover the full `H × W`
  image

This is the canonical "compressive sensing in the wild" demo — a $5 photodiode
+ a $200 DMD reconstructs images that would otherwise require an entire focal
plane array.

**Why it matters:**
- Imaging in spectral bands where dense detectors are expensive (THz, mid-IR, X-ray)
- Single-photon / photon-counting regimes
- Imaging through scattering media (where DMD-modulated structured illumination buys SNR)

## 1.2 Forward model E

```
y_k = ⟨φ_k, x⟩ + n_k     for k = 1, …, m

where:
  x ∈ ℝⁿ           — vectorized image, n = H × W (non-negative)
  φ_k ∈ {-1, +1}ⁿ  — k-th row of a Walsh-Hadamard basis (binary pattern)
  y_k ∈ ℝ          — k-th scalar photodetector reading
  n_k ∼ 𝒩(0, σ²)   — additive Gaussian noise (photon shot + read noise)
  m / n            — sampling ratio (typically 0.05–0.5)
```

Matrix form: `y = Φ x + n`, with `Φ ∈ ℝ^{m × n}`, `m << n`.

**Recovery problem:** given measurement `y` and known pattern matrix `Φ`,
recover `x` from an underdetermined system. Solved via convex optimization
(FISTA-TV, GAP-TV-MLE) or learned unrolled networks (LISTA, ISTA-Net).

## 1.3 DAG primitive chain (G)

```
S.pattern.hadamard  →  L.inner_product  →  int.temporal  →  D.scalar
   (DMD pattern)        (photon × pattern)   (integrate)     (single readout)
```

**L_DAG = 3.0** (4 primitives, 3 edges) · **n_c = 0** (single physics, no coupling)

## 1.4 Physical parameters θ

- `Phi_Hadamard`: Walsh-Hadamard rows, permutation seeded from a deterministic RNG
- `sampling_ratio m/n`: how much you compress (lower = harder)
- `gain α`: photodetector gain drift per measurement
- `illumination σ`: spatial non-uniformity of DMD illumination (Gaussian falloff)
- `DMD timing`: dwell time per pattern, duty cycle

## 1.5 Well-posedness W

| Property | Value |
|---|---|
| Existence | true |
| Uniqueness | true |
| Stability | **conditional** |
| Condition number κ (raw) | 3,000 |
| Condition number κ (effective, after TV regularization) | 30 |

**Regime:** Hadamard at 25% sampling satisfies RIP for sparse recovery; TV
prior required to handle gain-drift + illumination non-uniformity. Without
regularization, gain drift gets absorbed into noise and reconstruction
collapses.

## 1.6 Solvability C

```
Solver class:        FISTA-TV, ISTA-Net, LISTA, learned deep unrolling
Convergence rate q:  2.0 (linear in iteration count)
Error bound:         ‖x̂ - x‖₂ ≤ C₁·σ/√m + C₂·‖x - x_s‖₁
                                 ↑ noise term       ↑ best s-sparse approx
Complexity:          O(n log n) per iteration (fast Hadamard transform)
```

The error bound is the canonical compressed-sensing recovery guarantee:
reconstruction quality scales as `1/√m` in noise and as the best sparse
approximation of `x`.

## 1.7 Physics fingerprint

| Field | Value |
|---|---|
| carrier | photon |
| sensing_mechanism | structured_illumination |
| integration_axis | spatial |
| problem_class | linear_inverse |
| noise_model | gaussian |
| solution_space | 2D_spatial |
| primitives | `S.pattern.hadamard`, `L.inner_product`, `int.temporal`, `D.scalar` |
| difficulty_delta | 3 (standard tier) |
| error_metric | PSNR_dB (secondary: SSIM) |

---

# Layer 2 — Spec (`L2-026b`)

The L2 is the **mathematical contract** — a six-tuple `(Ω, E, B, I, O, ε)`
that turns the L1 physics into a concrete instance schema solvers must conform to.

## 2.1 Ω — parameter space

| ω axis | Bounds | What it controls |
|---|---|---|
| `n_pixels` | `[1024, 65536]` | Image size n = H × W (32×32 → 256×256) |
| `sampling_ratio` | `[0.05, 0.50]` | Fraction `m/n` of measurements taken |
| `noise_level` | `[0.001, 0.05]` | Standard deviation σ of Gaussian noise |
| `gain_alpha` | `[0.0, 0.003]` | Per-measurement gain drift (mismatch axis) |
| `illum_sigma` | `[0.0, 15.0]` | DMD illumination Gaussian falloff (mismatch axis) |

**Mismatch axes** = `gain_alpha` and `illum_sigma`. These are the
"real-world ugliness" knobs the spec tests robustness against.

**Allowed forward operators:** `spc_hadamard`, `spc_walsh` (mathematically
equivalent up to permutation).

## 2.2 E — forward operator (with mismatch)

```
y_k = ⟨φ_k_Hadamard, x⟩ + n_k

where φ_k may be corrupted by gain drift α and illumination falloff σ.
```

**Primitive chain:** `S.pattern.hadamard → L.inner_product → int.temporal → D.scalar`
**Inverse:** recover `x ∈ ℝⁿ` from `m` Hadamard-projection scalars `y`.

## 2.3 B — boundary constraints

| Constraint | Required |
|---|---|
| Non-negativity (`x ≥ 0`) | yes |
| Sparsity in wavelet or TV basis | yes |

## 2.4 I — initialization strategy

`zero_init` — solvers start from `x_0 = 0`.

## 2.5 O — observable outputs

The spec demands solvers report **three** metrics per reconstruction:

1. **PSNR** (primary, ranking metric)
2. **SSIM**
3. **residual_norm** = `‖y − Φ·x̂‖₂`

## 2.6 ε — acceptance threshold function

```
ε_fn(ω) = 22.0 + 6.0 · log₂(sampling_ratio / 0.05) + 1.5 · log₁₀(photon_count / 100)   [dB]
```

So at `sampling_ratio = 0.25` and 100 photons, `ε ≈ 22.0 + 13.93 + 0 ≈ 35.9 dB`.
Note: T1_nominal in L3-026b hardcodes `ε = 27.0 dB` at the same conditions —
this is a known stub-stage inconsistency that needs resolution at Tier 1/2
promotion (re-fit ε_fn against measured baseline curves).

## 2.7 Spec-level metadata

| Field | Value |
|---|---|
| spec_type | `mismatch_only` |
| d_spec | 0.38 (vs L2-026 random-projection variant) |
| `display_slug` | `spc` |
| S1-S4 gates | all PASS |

---

# Layer 3 — Benchmark (`L3-026b`)

L3 is where the spec meets data. SPC's L3 carries **both an I-benchmark suite
(4 difficulty tiers) and a P-benchmark (rho=50 aggregate)** in a single
`combined_P_and_I` artifact.

## 3.0 Canonical P-benchmark vs I-benchmark (per `pwm_overview.md` Figure 0d)

Every spec produces **both** a P-benchmark and an I-benchmark. They share
the same Ω / E / B / I / O / ε definitions but draw evaluation instances
differently:

| Aspect | **P-benchmark** | **I-benchmark** |
|---|---|---|
| Full name | Parametric Benchmark | Instance Benchmark |
| Ω draw | Random Ω drawn from the full declared range *at evaluation time* | Fixed `Ω_i` snapped to a standard size tier (stored in benchmark) |
| ε threshold | `epsilon_fn(Ω)` AST-sandboxed expression evaluated per draw | Pre-computed scalars from `epsilon_fn` at each `Ω_i` |
| rho | **always 50** (full-range generalization required) | **1 / 3 / 5 / 10** depending on the spec's declared difficulty tier |
| Tests | Broad generalization across Ω | Performance at a specific operating point |
| Count per spec | 1 | 1 |

**S4 gate at L2** rejects spec submissions that don't include one worked
example of each. SPC's L3-026b includes both: the rho=50 P-benchmark
(below in § 3.3) and a **4-tier I-benchmark suite** (§ 3.2) with rho ∈
{1, 3, 5, 10} per tier.

## 3.1 Dataset registry

| Dataset | Source | Construction |
|---|---|---|
| **Set11** (primary) | Standard SPC testbed (Lena, Monarch, peppers, …) | Grayscale, power-of-2 sizes [32, 64, 128, 256] |
| **BSD68** (secondary) | Berkeley Segmentation 68-image holdout | Same crop schedule |

**Hadamard pattern construction:** SHA256-seeded RNG selects row indices from
the Walsh-Hadamard matrix (deterministic across runs).

**Dataset CID:** `null` today. Promotion to Tier 2 requires pinning to IPFS
and recording the CID here.

**num_dev_instances_per_tier:** 20

## 3.2 I-benchmarks — the 4 difficulty tiers

Each I-benchmark is a single-instance evaluation (`rho` small, fixed ω) with
its own ε floor. Solvers can clear individual tiers without saturating the
full P-benchmark.

| Tier | rho | n_pixels | sampling | noise | gain α | illum σ | ε (dB) | d_ibench |
|---|---|---|---|---|---|---|---|---|
| **T1_nominal** | 1 | 4,096 (64×64) | 0.25 | 0.01 | 0.0 | 0.0 | **27.0** | 0.14 |
| **T2_gain_drift** | 3 | 4,096 (64×64) | 0.25 | 0.02 | 0.0015 | 5.0 | **24.5** | 0.30 |
| **T3_blind_calibration** | 5 | 16,384 (128×128) | 0.15 | 0.03 | 0.0025 | 10.0 | **22.0** | 0.50 |
| **T4_undersampled** | 10 | 65,536 (256×256) | 0.05 | 0.05 | 0.003 | 15.0 | **19.0** | 0.72 |

The rho values follow the canonical 1/3/5/10 progression — each tier draws
that many instances at the fixed `Ω_i` and reports an aggregate score.

### Authored baseline performance per tier (PSNR / Q)

| Tier | FISTA-TV | GAP-TV-MLE | LISTA |
|---|---|---|---|
| T1_nominal | 26.8 / 0.64 | 28.4 / 0.76 | **32.0 / 0.92** |
| T2_gain_drift | 23.2 / 0.46 | 25.0 / 0.56 | **27.2 / 0.72** |
| T3_blind_calibration | 20.4 / 0.38 | 22.1 / 0.50 | **24.0 / 0.62** |
| T4_undersampled | 17.5 / 0.24 | 18.8 / 0.34 | **20.3 / 0.48** |

## 3.3 P-benchmark — the rho=50 aggregate

The P-benchmark is the **headline ranking score** — 50 instances drawn
parametrically across Ω, scored as a distribution (not a single PSNR).

| Field | Value |
|---|---|
| rho | 50 |
| dataset | Set11 + BSD68 union |
| num_dev_instances | 200 |
| construction | parametric sampling over `(n_pixels, sampling_ratio, gain_α, illum_σ)` |

### Authored P-benchmark baselines (overall Q)

| Solver | overall_Q |
|---|---|
| FISTA-TV | 0.45 |
| GAP-TV-MLE | 0.55 |
| **LISTA** (current SOTA) | **0.70** |

**→ Q_int = 70 would be the bar for rank-1 if this were registered today.**

### Hardness check

L3-026b's `hardness_rule_check` field says:

> **SATISFIED** — LISTA fails at T4_undersampled (20.3 dB > 19.0 ε here but
> fails strata S3/S4 in full P-bench due to RIP degradation at 5% sampling).

Translation: even the strongest authored baseline doesn't beat the full
P-benchmark across all strata, so the benchmark isn't trivially saturated.
That means there's *room for solver innovation* — exactly the property a
PWM benchmark needs.

---

# Layer 4 — Solutions (`L4` certs)

## 4.1 Today: zero certs on-chain

No `L4` certs exist for L3-026b because the L3 isn't registered. Once
promoted to Tier 1, miners would submit certs through the standard
`pwm-node mine` flow. Each cert is a **15-field cert payload** that hashes
to a `bytes32 certHash` recorded on-chain.

## 4.2 What an SPC cert payload would look like

```jsonc
{
  "Q_int": 70,                    // → 0.70 × 100 from the P-benchmark overall_Q
  "benchmarkHash": "0x2d88771166293b57611b35cfd7578ab45ebc57ad635d409ed1878ffb28bf3ba2",
                                  // ↑ keccak256(canonical_json(L3-026b)) — verified
                                  //    if the manifest hadn't changed since registration
  "principleId": 26,              // numeric ID of L1-026b
  "delta": 3,                     // difficulty_delta from L1
  "spWallet": "0x...",            // Solution Provider (the miner)
  "acWallet": "0x...",            // Algorithm Contributor (solver author)
  "cpWallet": "0x...",            // Compute Provider (GPU runner)
  "l1Creator": "0x...",           // who registered L1-026b
  "l2Creator": "0x...",           // who registered L2-026b
  "l3Creator": "0x...",           // who registered L3-026b
  "shareRatioP": 5000,            // SP share × 10000 (default 0.50 = 50%)
  "submittedAt": 1777800000,      // unix timestamp from EVM block
  "rank": 0,                      // not yet finalized
  "_meta": {                      // optional inspection-only sidecar (stripped before hashing)
    "solver_label": "LISTA-SPC",
    "psnr_db": 32.0,
    "framework": "PyTorch 2.1 + CUDA 12.1",
    "Q_float": 0.70,
    "gate_verdicts": {"S1": "pass", "S2": "pass", "S3": "pass", "S4": "pass"}
  }
}

certHash = keccak256(canonical_json(payload))   // strips _meta + UI-only fields first
```

The 12 chain-bound fields above are what the chain remembers. The cert hash
on-chain is `keccak256(canonical_json_payload)` — same recipe as
`scripts/register_genesis.py` and `pwm-team/infrastructure/agent-cli/pwm_node/commands/mine.py`.

## 4.3 The 3 reference baselines (would-be Tier 1 solutions)

| Solver | Class | T1 PSNR | T1 Q | P-bench Q | What it is |
|---|---|---|---|---|---|
| **FISTA-TV** | classical (proximal gradient) | 26.8 dB | 0.64 | 0.45 | Iterative shrinkage + TV prox; CPU-runnable; ~30 s/scene |
| **GAP-TV-MLE** | classical (generalized alternating projection) | 28.4 dB | 0.76 | 0.55 | Better TV-prior + MLE noise model; CPU-runnable; ~60 s/scene |
| **LISTA** | learned (unrolled neural network) | 32.0 dB | 0.92 | **0.70** | Deep-learning SOTA; GPU-needed; ~2 s/scene; pretrained weights on Set11 |

To submit a cert today, the simplest path:

1. Author `pwm-team/pwm_product/reference_solvers/spc/spc_fista_tv.py` (CPU)
2. Reproduce the T1_nominal benchmark locally → expect Q ≈ 0.64
3. Run `pwm-node mine L3-026b --solver pwm-team/pwm_product/reference_solvers/spc/spc_fista_tv.py --dry-run` to inspect the would-be cert
4. (Once L3-026b is registered) drop `--dry-run` to broadcast

## 4.4 Reward distribution if rank-1 (hypothetical)

If a rank-1 cert lands at `Q_int = 70` against a pool of, say, 1,000 PWM:

| Role | Share | Amount |
|---|---|---|
| Algorithm Contributor (AC) | `40% × 0.55 × p` (p = shareRatioP/10000) | 110 PWM at p=0.50 |
| Compute Provider (CP) | `40% × 0.55 × (1-p)` | 110 PWM at p=0.50 |
| L3-026b creator | `40% × 0.15` | 60 PWM |
| L2-026b creator | `40% × 0.10` | 40 PWM |
| L1-026b creator | `40% × 0.05` | 20 PWM |
| Treasury T_k | `40% × 0.15` | 60 PWM |
| **Subtotal rank-1** | **40%** | **400 PWM** |
| Rank 2 | 5% | 50 PWM |
| Rank 3 | 2% | 20 PWM |
| Ranks 4-10 | 1% each | 70 PWM total |
| Rolls over to next epoch | ~52% | 520 PWM |

Per-pool cap (`maxBenchmarkPoolWei`) keeps the absolute risk bounded — at
mainnet launch the recommendation is ~50-100 PWM per new L3 until track
record builds.

---

## 5. Pre-mining review checklist

If you're considering claiming this stub or just dry-running it for
familiarity, here's what to check:

| Check | Status today | Action to mine for real |
|---|---|---|
| L1-026b forward model is internally consistent | ✓ | None |
| L2-026b spec ε_fn yields bounded values across Ω | ⚠ formula vs T1 hardcoded ε differ | Re-fit ε_fn against measured baseline curve |
| L3-026b has a dataset CID | ✗ | Pin Set11 + BSD68 to IPFS, fill `dataset_registry.cid` |
| Reference solver in `pwm_product/reference_solvers/spc/` | ✗ | Author `spc_fista_tv.py` (CPU-runnable) — ~2-4 hours |
| L1/L2/L3-026b registered on-chain | ✗ | Add to `ARTIFACTS_TO_REGISTER` in `scripts/register_genesis.py`, run `--network testnet` |
| Benchmark pool funded | ✗ | Treasury funds via `PWMReward.fundPool()` — keep small (~50 PWM) until track record |
| `display_slug=spc` doesn't change hash | ✓ | `display_slug` is in `UI_ONLY_FIELDS` |

---

## 6. Dry-run testing (works today, no payout)

You can exercise the harness end-to-end without the artifact being
registered, because `pwm-node mine --dry-run` skips the chain submission.

```bash
cd /home/spiritai/pwm/Physics_World_Model/pwm

# 1. Copy SPC manifests into the genesis dir so the CLI can find them
mkdir -p pwm-team/pwm_product/genesis/l1 pwm-team/pwm_product/genesis/l2 pwm-team/pwm_product/genesis/l3
cp pwm-team/content/agent-imaging/principles/B_compressive_imaging/L1-026b_spc.json pwm-team/pwm_product/genesis/l1/
cp pwm-team/content/agent-imaging/principles/B_compressive_imaging/L2-026b_spc.json pwm-team/pwm_product/genesis/l2/
cp pwm-team/content/agent-imaging/principles/B_compressive_imaging/L3-026b_spc.json pwm-team/pwm_product/genesis/l3/

# 2. Try to dry-run mine — fails at "no SPC reference solver"
pwm-node mine L3-026b \
  --solver $(pwd)/pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py \
  --dry-run
```

**Expected result:** the CLI now resolves the artifact (you've copied it to
the genesis dir), but mining still fails because:
- The CASSI GAP-TV solver expects CASSI inputs (mask + dispersion + 3D cube),
  not SPC inputs (Hadamard patterns + 1D measurement vector)
- There's no SPC dataset to feed the solver

To do a *real* dry-run you'd also need to:
1. Author `pwm_product/reference_solvers/spc/spc_fista_tv.py` with CLI signature `--input <dir> --output <dir>`
2. Synthesize a small Set11 sample at T1_nominal Ω
3. Bundle the sample in `pwm_product/demos/spc/sample_01/`

That's the smallest viable "Tier 2 promotion" package: ~4-6 hours of work
and the principle becomes mineable on Sepolia.

---

## 7. Next-step options

| Option | Effort | Outcome |
|---|---|---|
| **A. Just review and walk away** | 0 | You understand SPC; no code/chain change |
| **B. Dry-run hand-test** | ~30 min | Run the dry-run blocks above, see what fails, internalize the harness shape |
| **C. Promote SPC to Tier 1** | ~6-12 hours | Author solver + bundle dataset + register on Sepolia → SPC becomes a real benchmark on the leaderboard alongside CASSI/CACTI |

If you want to do (C), the natural sequence is:

1. Author `spc_fista_tv.py` — CPU-runnable, ~3 hours (FISTA + a TV prox operator + fast Hadamard transform)
2. Synthesize 10 Set11 samples at the 4 tier ω configurations (~1 hour)
3. Bundle samples in `demos/spc/sample_01..10/` with SHA-256 fingerprints in `meta.json` (~30 min)
4. Set `registration_tier: founder_vetted` on L1/L2/L3-026b (the field is in `UI_ONLY_FIELDS` so the hash stays the same)
5. Add the artifact tuple to `ARTIFACTS_TO_REGISTER` in `scripts/register_genesis.py`:

```python
ARTIFACTS_TO_REGISTER = [
    # ... existing CASSI + CACTI entries ...
    ("L1-026b", "l1/L1-026b.json", 1),
    ("L2-026b", "l2/L2-026b.json", 2),
    ("L3-026b", "l3/L3-026b.json", 3),
]
```

6. Run `python3 scripts/register_genesis.py --network testnet --dry-run` first; then drop `--dry-run` to actually broadcast.

The reward for promoting a stub: SPC becomes the third mineable Principle on
Sepolia, doubles the reachable bounty surface for external miners, and gives
the customer guide a non-CASSI, non-CACTI third example.

---

## Cross-references

**Source manifests (review against these):**

- `pwm-team/content/agent-imaging/principles/B_compressive_imaging/L1-026b_spc.json`
- `pwm-team/content/agent-imaging/principles/B_compressive_imaging/L2-026b_spc.json`
- `pwm-team/content/agent-imaging/principles/B_compressive_imaging/L3-026b_spc.json`

**Source paper / mine_example reference:**

- `papers/Proof-of-Solution/mine_example/spc.md` (referenced from L1's `reference_mine_example`)
- `papers/Proof-of-Solution/mine_example/pwm_overview.md` — canonical 4-layer pipeline definition; § Figure 0d defines spec.md six-tuple format and the P-benchmark vs I-benchmark distinction this doc inherits

**Related stub** (general single-pixel, NOT Hadamard-specific):

- `L1-026 / L2-026 / L3-026` — generic random-projection single-pixel imaging (`d_spec ≈ 0.38` from this Hadamard variant)

**Customer guide cross-references:**

- `PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md` § "Registration tiers"
- `PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md` (full Tier 3 → Tier 2 promotion flow)
- `PWM_HANDS_ON_TEST_WALKTHROUGH_2026-05-07.md` (the mining harness this would slot into)
- `PWM_Q_SCORE_EXPLAINED_2026-05-06.md` (how the would-be Q_int is computed)
- `PWM_VERIFY_MST_L_CASSI_CLAIM_2026-05-06.md` (5-layer verification flow that would apply once a cert is submitted)
- `PWM_ONCHAIN_VS_OFFCHAIN_ARCHITECTURE_2026-05-05.md` (what binds Q_int to the cert hash on-chain)

**Live explorer:**

- `https://explorer.pwm.platformai.org/principles/L1-026b` — the public stub detail page (with the amber claim CTA)
