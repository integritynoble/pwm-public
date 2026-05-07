# PWM Layers — Complete Guide: Create + Use (L1 / L2 / L3 / L4)

**Date:** 2026-05-03 (refreshed 2026-05-06 — registration tiers + CLI flag fix)
**Audience:** Researchers, students, industry teams, regulators, external developers, founders
**Network:** Ethereum Sepolia testnet (chainId 11155111) for examples. Base mainnet at launch reuses the same `--network mainnet` flag; the chain selection is determined by which `addresses.json` entry the CLI resolves (`testnet` → Sepolia today; `mainnet` → Base mainnet at launch).
**Canonical public repo:** `https://github.com/integritynoble/pwm-public`
**Web explorer:** `https://explorer.pwm.platformai.org`
**Related (in this repo):** [`PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md`](#cross-references-inside-this-public-repo)

---

## About this guide and the repo

This document is the canonical user-facing reference for PWM. It ships
in the public repo at `https://github.com/integritynoble/pwm-public`,
and every path shown below (e.g., `pwm-team/customer_guide/...`,
`pwm-team/pwm_product/...`, `pwm-team/infrastructure/...`,
`pwm-team/content/...`, `scripts/...`, `public/...`) is relative to
the root of that repo. So:

```bash
git clone https://github.com/integritynoble/pwm-public.git
cd pwm-public
ls pwm-team/customer_guide/     # → this guide lives here
```

If you're reading this on GitHub, every code-blocked path is
clickable in the file tree. If you're reading it after a local clone,
the same paths work in your shell.

> **Repo visibility status (current):** `pwm-public` is currently a
> **private repo** during the pre-mainnet preparation window.
> Anonymous browsers see a GitHub 404; access today is granted
> per-engagement to auditors, partner labs, and grant reviewers on
> request. The repo flips to fully public on **D9 Step 12 (mainnet
> launch day, ~3-4 weeks)** per `customer_guide/plan.md` Phase 3.
> If you're reading this from inside the founding team or as an
> invited collaborator, the URL above works directly for you.

> **Note for internal reviewers:** some cross-referenced design docs
> (`PWM_TESTNET_TESTING_GUIDE_2026-05-02.md`, `PWM_OPTION_C_HANDOFF_GPU_SUBMISSION_2026-05-02.md`,
> etc.) live in the founding-team's private coordination tree and
> aren't mirrored to the public repo. Where this guide references them,
> the public-repo reader can safely treat them as "additional internal
> design notes — not required for any user-facing workflow." Everything
> a customer needs is in this guide + the contribution guide.

---

## Big picture — the 4 layers + 2 roles

PWM organizes computational-science problems into 4 layers. Each layer
supports two roles:

```
                    ┌─────────────── PRODUCER ────────────┐  ┌──── CONSUMER ────┐
   L1 Principle     │  Author + register the physics     │  │  Browse, read,    │
                    │  + parameter space                  │  │  understand       │
                    ├─────────────────────────────────────┤  ├───────────────────┤
   L2 Spec          │  Author + register the six-tuple   │  │  Read the math    │
                    │  (Ω, E, B, I, O, ε)                 │  │  contract         │
                    ├─────────────────────────────────────┤  ├───────────────────┤
   L3 Benchmark     │  Author + register the P-benchmark │  │  Download data,   │
                    │  (rho=50, anti-overfit, dataset)    │  │  evaluate solvers │
                    ├─────────────────────────────────────┤  ├───────────────────┤
   L4 Solution      │  Mine: run solver, submit cert     │  │  Verify cert,     │
                    │                                      │  │  audit claims     │
                    └─────────────────────────────────────┘  └───────────────────┘
   Backing (any)    │  Stake PWM on L1/L2/L3              │  (consumers don't stake) │
```

**Producer = founder, bounty author, external developer with a new principle.**
**Consumer = researcher, student, industry team, auditor, regulator.**

Most PWM users are consumers. The protocol is designed to make
consumption frictionless and producer entry well-defined.

---

## Pre-flight (shared by all layers, ~10 min one-time setup)

### For consumers (zero-cost, no wallet needed)

```bash
git clone https://github.com/integritynoble/pwm-public.git
cd pwm-public
python3 -m venv .venv && source .venv/bin/activate
pip install -e pwm-team/infrastructure/agent-cli   # installs the `pwm-node` CLI
```

That's it. Browse with `pwm-node --network testnet benchmarks` or
visit `https://explorer.pwm.platformai.org`.

### For producers (need a funded wallet for any on-chain action)

Add to the consumer setup above:

```bash
# 1. Funded testnet wallet (free Sepolia ETH from a faucet):
#      https://sepoliafaucet.com
#      https://www.alchemy.com/faucets/ethereum-sepolia
#      https://faucet.quicknode.com/ethereum/sepolia
export PWM_PRIVATE_KEY=0x<your-Sepolia-key>
export SEPOLIA_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
export PWM_RPC_URL=$SEPOLIA_RPC_URL

# 2. For miners running deep-learning solvers (MST-L, EfficientSCI, etc.),
#    pwm_core is a separate package vendored as a submodule. To pull it
#    into the working tree, clone with --recursive (or run the submodule
#    init step against an existing clone). Install Git LFS first so the
#    pretrained .pth weight files come down with the submodule:
#
#      # one-time on this machine:
#      git lfs install
#      # then either:
#      git clone --recursive https://github.com/integritynoble/pwm-public.git
#      # or against an existing clone:
#      git submodule update --init --recursive
#      git -C public lfs pull
#
#    Verify weights landed (and auto-fix common issues):
#      bash scripts/download_weights.sh
#
#    Then install pwm_core + a CUDA-matched torch wheel:
pip install -e public/packages/pwm_core
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
# (adjust the cu128 wheel suffix to match your local CUDA version; CPU-only
#  also works for development, just slower)
```

---

# Layer 1 — Principle

The physics declaration: forward model + parameter space + DAG primitive chain + complexity score.

## L1 — How CONSUMERS use existing Principles

### Browse the catalog (web)

`https://explorer.pwm.platformai.org/principles` — shows artifacts
registered on the live network (today: 2 founder-vetted Principles
on Sepolia — CASSI and CACTI).

### Browse the catalog (CLI)

```bash
# L1 Principles registered on the active network (default genesis dir):
pwm-node principles
#   Today: 2 entries (CASSI, CACTI) — these are the founder-vetted set
#   that ships with the protocol launch and is registered on Sepolia.

# L3 Benchmarks registered on the active network:
pwm-node benchmarks
```

Both commands are offline-by-default — no `--network` flag needed for
catalog reads.
Add `--domain <substring>` to filter (e.g. `pwm-node principles --domain imaging`).

### Two views of the catalog: registered vs cataloged

PWM's catalog has two sizes depending on what you're asking:

| View | Count today | What it shows | How to access |
|---|---|---|---|
| **Registered on-chain** | 2 (CASSI, CACTI) | Principles the multisig has registered to `PWMRegistry`. **Mineable** — submitting a cert against these has a real reward pool.  | `pwm-node principles`, `https://explorer.pwm.platformai.org/principles` |
| **Cataloged in repo** | 531 | Scientifically-declared L1 inventory across imaging, physics, applied, chemistry, signal — most are **stubs awaiting an external contributor** to author a reference solver and pin a dataset. **Not mineable** until promoted (see "Registration tiers" below). | `find pwm-team/content/agent-*/principles -name "L1-*.json"` |

That's why this guide's CLI examples print 2 entries even though the
repo has 531 manifest files — the CLI defaults to showing what's
actually registered and minable, not the wider claim-board inventory.

### Inspect one Principle in detail

```bash
pwm-node inspect L1-003
# Prints title, domain, gate_class, ω parameters, forward model,
# DAG primitive chain, L_DAG complexity score, references
```

Or read the JSON directly:

```bash
cat pwm-team/pwm_product/genesis/l1/L1-003.json
# Or by domain (manifests are nested under topic subdirs):
find pwm-team/content/agent-imaging/principles   -name "L1-*.json" | wc -l   # 165 medical imaging
find pwm-team/content/agent-physics/principles   -name "L1-*.json" | wc -l   # 148 physics
find pwm-team/content/agent-applied/principles   -name "L1-*.json" | wc -l   # 112 applied
find pwm-team/content/agent-chemistry/principles -name "L1-*.json" | wc -l   #  67 chemistry
find pwm-team/content/agent-signal/principles    -name "L1-*.json" | wc -l   #  39 signal processing
# Total: 531 cataloged L1 Principles across all domains (mostly Tier 3
# stubs awaiting contributor authoring — see "Registration tiers" below).
```

### Find a Principle for your problem

```bash
pwm-node match "I have a hyperspectral inverse problem with coded aperture and dispersion"
# Returns: L3-003 (CASSI), top match with explanation
```

Or web: `https://explorer.pwm.platformai.org/match`

## L1 — How PRODUCERS create new Principles

### Author a new L1 manifest

```bash
mkdir -p my_new_principle
cat > my_new_principle/L1-100_my_principle.json <<'JSON'
{
  "artifact_id": "L1-100",
  "layer": "L1",
  "title": "My Custom Inverse Problem",
  "domain": "computational_imaging",
  "spec_range": {
    "allowed_omega_dimensions": ["resolution", "noise_sigma"],
    "omega_bounds": {"resolution": [64, 512], "noise_sigma": [0.01, 0.1]},
    "center_spec": {"forward_operator": "y = A x + n"}
  },
  "G": {"dag": "source -> linear_op -> sensor -> noise", "n_c": 0},
  "gate_class": "analytical",
  "error_metric": "PSNR_dB",
  "physics_fingerprint": "linear_inverse_v1"
}
JSON
```

### Register it on-chain

`scripts/register_genesis.py` only registers the founding-team's
hardcoded `ARTIFACTS_TO_REGISTER` list (CASSI + CACTI L1/L2/L3); it
doesn't accept `--manifest` / `--layer` flags. To get a NEW Principle
on-chain, the recommended path is the **PR-based claim flow** in
`pwm-team/customer_guide/PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md`:

```
1. Open a GitHub issue in integritynoble/pwm-public titled:
     [L1 claim] L1-XXX <slug> — <author name>
2. agent-coord reserves the next free numeric ID
3. Author the L1/L2/L3 manifests, open a PR
4. After verifier-agent review, agent-coord registers them on-chain
   at the next genesis-extension event
```

Power-users who want to register their own artifact directly can
edit `scripts/register_genesis.py` to add their manifest tuple to the
`ARTIFACTS_TO_REGISTER` list, then run:

```bash
# What founders run for the seeded CASSI + CACTI genesis batch:
PWM_PRIVATE_KEY=$PWM_PRIVATE_KEY \
PWM_RPC_URL=$SEPOLIA_RPC_URL \
python3 scripts/register_genesis.py --network testnet --dry-run
# Drop --dry-run to actually broadcast.
```

For the contribution flow + manifest schema, see
`pwm-team/customer_guide/PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md` — the
canonical public contribution guide (moved out of `coordination/`
into `customer_guide/` 2026-05-05 so it ships in the public mirror).

### Stake on an existing Principle (back its credibility)

```bash
pwm-node --network testnet stake quote                # all 3 layers; or use --layer 0 for principle only
pwm-node --network testnet stake principle 0x<L1-hash>
```

---

# Layer 2 — Spec

The mathematical contract: six-tuple (Ω, E, B, I, O, ε) for a concrete instance of the parent Principle.

## L2 — How CONSUMERS use existing Specs

### Read the math contract

```bash
pwm-node --network testnet inspect L2-003
# Output:
#   six_tuple:
#     Ω = parameter space (allowed dispersions, mask types, photon levels)
#     E = forward operator + DAG primitive chain
#     B = boundary constraints (non-negativity, physical realizability)
#     I = initialization strategy
#     O = observable list (PSNR, SSIM)
#     ε = epsilon_fn (acceptance threshold function)
#   gate_class: analytical
#   s1_s4_gates: [PASS, PASS, PASS, PASS]
```

This is what solver authors implement against — the input/output schema
+ acceptance threshold.

### Read the JSON

```bash
cat pwm-team/pwm_product/genesis/l2/L2-003.json
```

## L2 — How PRODUCERS create new Specs

### Author + register

L2 manifests follow the same shape as L1, with `parent_l1` + six-tuple
fields. They register on-chain via the same flow as L1 — through the
PR-based claim path documented in `PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md`.
L2 and L3 children typically inherit the parent L1's reserved numeric
ID (so `L1-XXX` claim → `L2-XXX` + `L3-XXX` ship in the same PR).

### Stake on an existing Spec (~$5 tier)

```bash
pwm-node --network testnet stake quote                # all 3 layers; or use --layer 1 for spec only
pwm-node --network testnet stake spec 0x<L2-hash>
```

L2 staking is rare in practice; the protocol's economic incentives
concentrate at L1 backing and L3 mining.

---

# Layer 3 — Benchmark

The P-benchmark: rho=50 instances, anti-overfitting mechanisms M1-M6, dataset_registry pinned to IPFS.

## L3 — How CONSUMERS use existing Benchmarks

### Browse on the web

`https://explorer.pwm.platformai.org/benchmarks/L3-003` —
benchmark detail page with ω parameters, baseline solver scores,
sample data PNGs, "Get this benchmark" download card, leaderboard.

### Two reference floors per benchmark

The benchmark page surfaces **two** reference floors so contributors
see both onboarding gates at once:

| Floor | Today on L3-003 | What it means |
|---|---|---|
| 📊 **Classical floor** | GAP-TV 26.0 dB | Deliberate weak baseline. Anyone better than this wins rewards — easy onboarding gate. |
| 🧠 **Deep-learning floor** | MST-L 35.3 dB | Published deep-learning landmark. Beating this is the harder gate that signals real solver progress. |

The `improvement_db` shown on the page is anchored to the **classical
floor**, so the protocol's "PWM-enabled +X dB" story stays anchored to
the easy-to-beat baseline (it would otherwise be 0 dB whenever the SOTA
matches the deep-learning landmark).

The data sources are split deliberately to preserve hash invariance:

| Field | Where in manifest | Hashed (on-chain)? | Use case |
|---|---|---|---|
| Classical floor | `ibenchmarks[0].baselines[0]` | ✓ Yes | Frozen at registration; e.g. GAP-TV on L3-003 |
| Deep-learning floor | top-level `display_baselines[]` (in `UI_ONLY_FIELDS`) | ✗ No | Updateable post-registration; e.g. MST-L landmark added 2026-05-05 |

This means a founder can land a new SOTA (e.g. EfficientSCI surpassing
MST-L) by appending to `display_baselines` and re-deploying the
explorer — no manifest re-registration needed, on-chain hash stays
valid. The legacy `baselines[*].category: "deep_learning"` path is
still supported as a fallback for not-yet-registered manifests, but it
DOES change the keccak256 — only use it on Tier-3 stubs.

### Inspect via CLI

```bash
pwm-node --network testnet inspect L3-003
# Prints title, parent L2/L1, n_dev_instances, scoring metric,
# current rank-1 score, dataset CIDs, ω parameters
```

### Download the dataset

```bash
# Option 1 (recommended): web "Get this benchmark" card on the explorer
# https://explorer.pwm.platformai.org/benchmarks/L3-003 — serves per-sample
# downloads from /api/demos/cassi/sample_NN/{snapshot,ground_truth,solution}
# .{npz,png} + meta.json. Multiple samples available (sample_01, sample_02,
# …); each is a complete evaluator input + reference output you can feed
# straight into pwm-node mine --dry-run --solver your.py.

# Option 2 (post-launch): once the IPFS pinning bounty (Bounty #6) ships,
# CIDs will land in the L3 manifest's `dataset_registry` and you'll be able
# to fetch the full T1_nominal/T2_low/… splits directly:
#   ipfs get <CID-from-L3-manifest> -o ./cassi_data/
# Today, dataset_registry in the manifest holds textual dataset names +
# construction notes only (KAIST-30, CAVE, ICVL, the build recipe, dev/
# holdout instance counts) — `ipfs_cid` and `ground_truth_cid` are
# explicitly null. The explorer card is the working path until pinning.

# Option 3: source-author releases (full datasets, license-permitting)
#   KAIST-30 hyperspectral:  http://vclab.kaist.ac.kr/iccv2017p1/index.html
#   CAVE multispectral:      https://www.cs.columbia.edu/CAVE/databases/multispectral/
#   ICVL hyperspectral:      http://icvl.cs.bgu.ac.il/hyperspectral/

# Option 4: read dataset metadata as currently committed
jq '.dataset_registry' pwm-team/pwm_product/genesis/l3/L3-003.json
# Returns: {primary, secondary, tertiary, construction_method,
#           num_dev_instances_per_tier, holdout_instances_per_tier}
```

### Evaluate your own solver locally (no on-chain submission, no wallet needed)

```bash
pwm-node --network testnet mine L3-003 \
  --solver my_solver.py \
  --dry-run
# Prints the cert_payload it WOULD submit (Q score, runtime), no tx
```

This is how a researcher compares their method to SOTA without
spending Sepolia ETH or revealing their submission identity.

**Solver contract:** the framework calls
`python <solver.py> --input <work_dir>/input/ --output <work_dir>/output/`
inside a per-mine working directory. Place the L3 dataset (downloaded
via "Get this benchmark" or `ipfs get`) under `<work_dir>/input/`
before invoking, or have the solver fetch it itself from a CID listed
in the manifest's `dataset_registry`. The `--dry-run` flag stops at
score-and-payload time; it does NOT auto-stage data.

## L3 — How PRODUCERS create new Benchmarks

### Author + register

L3 manifests register on-chain through the same PR-based claim flow as
L1 + L2 (see `PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md`). The L3 ships in the
same PR as its parent L1 + L2; agent-coord registers all three together
at the next genesis-extension event.

The L3 manifest must include:

- `rho` (typically 50)
- `dataset_registry`: dataset CIDs + ground-truth provenance
- `ibenchmarks`: list of tier specifications (T1_nominal, T2_off_axis, etc.)
- `anti_overfitting_mechanisms`: M1-M6 implementations per gate class
- `scoring`: primary + secondary metric + Q formula
- `hardness_rule_check`: proof no expert baseline passes ε everywhere

### Stake on an existing Benchmark (~$1 tier)

```bash
pwm-node --network testnet stake quote                # all 3 layers; or use --layer 2 for benchmark only
pwm-node --network testnet stake benchmark 0x<L3-hash>
```

---

# Layer 4 — Solution (Certificate)

The actual "mining" loop: run a solver, compute a quality score Q, submit a tamper-resistant certificate on-chain.

## L4 — How CONSUMERS use existing Certificates

### Verify a published claim

A vendor publishes "We scored 0.95 on PWM L3-523, cert 0xb293...".

**Easiest path — explorer page:**

```
https://explorer.pwm.platformai.org/cert/0xb293...
```

Renders the cert detail: benchmark hash, submitter address, Q score,
solver label (if submitter posted meta), challenge status, and a
direct link to the on-chain tx.

**Programmatic — Etherscan (canonical):**

```
https://sepolia.etherscan.io/tx/0xb293...
```

The on-chain `CertificateSubmitted` event holds the cert hash,
benchmarkHash, submitter address, and Q_int — immutable, no UI in
between. For deeper verification, read the `PWMCertificate` contract
state directly via `cast call` or web3.py.

> **Note:** a CLI wrapper (`pwm-node verify-cert <hash>`) is
> on the roadmap. Until then the two URLs above are the canonical
> verification path.

> **Concrete worked example with real on-chain data:** see
> [`PWM_VERIFY_MST_L_CASSI_CLAIM_2026-05-06.md`](PWM_VERIFY_MST_L_CASSI_CLAIM_2026-05-06.md)
> — five layers of verification depth (from "look at the explorer page" →
> "rebuild the cert payload bytes from scratch and re-keccak") for the
> live MST-L 35.295 dB CASSI cert
> (`0x7c7740faad378c8514128903a26165d5e5d303b56e2b5b4649917265c5a3ee13`,
> tx `0x8883a90d…`, block 10778856 on Sepolia). That doc walks the
> same flow as this section but with a real cert hash you can paste
> into Etherscan today.

### Download a published Solution as a reference

If the cert payload includes an off-chain `solution_uri` (typically
IPFS), pull it and re-run:

```bash
ipfs get <solution-uri-from-cert-payload> -o ./reference_solution/
# Examine the solver code; verify it produces the claimed Q
```

This is the **"reproducibility on-demand"** layer.

## L4 — How PRODUCERS mine new Solutions

### The full flow (5 commands)

```bash
# 1. (One-time per benchmark) Stake on the L1 Principle to back the problem
pwm-node --network testnet stake principle 0x<L1-hash>

# 2. (One-time per benchmark) Stake on the L3 Benchmark
pwm-node --network testnet stake benchmark 0x<L3-hash>

# 3. Mine — run your solver, submit cert
pwm-node --network testnet mine L3-003 \
  --solver pwm-team/pwm_product/reference_solvers/cassi/cassi_mst.py
# Output:
#   [mine] runtime=12.3s  PSNR=34.1 dB  Q=0.82
#   [mine] cert_hash: 0xb293...
#   [mine] tx submitted: 0xabcd...

# 4. Wait 7 days for the challenge period

# 5. Finalize — triggers reward distribution
#    No CLI wrapper yet; call the contract directly:
cast send <PWMCertificate-addr> "finalize(bytes32)" <cert_hash> \
  --rpc-url $SEPOLIA_RPC_URL --private-key $PWM_PRIVATE_KEY
# Rank 1 wins 40% of pool, rank 2 wins 5%, rank 3 wins 2%, rank 4-10 win 1% each
```

### One-shot for both CASSI + CACTI

The repo includes a complete walkthrough script:

```bash
bash scripts/testnet_mine_walkthrough.sh
# Pre-flight + hash compute + CASSI stake/mine + CACTI stake/mine + summary
# Knobs: CASSI_ONLY=1, DRY_RUN=1, SKIP_STAKE=1
```

Read the script header (`head -60 scripts/testnet_mine_walkthrough.sh`)
for the full env-var matrix and what each phase does — it doubles as
the walkthrough's reference manual.

### What happens on-chain during `mine`

1. Solver runs locally → produces `solution.npz` + `meta.json`
2. CLI computes `cert_hash = keccak256(canonical_payload)` where
   payload includes (Q score, solver_id, benchmarkHash, ω instance)
3. CLI calls `PWMCertificate.submit(cert_hash, benchmarkHash, Q_int, payload)`
4. 7-day challenge period starts; anyone can call
   `PWMCertificate.challenge(cert_hash, proof)` if they suspect fraud
5. After 7 days clean, anyone calls `finalize(cert_hash)` →
   `PWMReward.distribute()` runs the ranked-draw payout

### Reward distribution (rough numbers)

| Rank | Pool share | Notes |
|---|---|---|
| 1 | **40%** | The "big prize" — incentivizes SOTA |
| 2 | 5% | |
| 3 | 2% | |
| 4-10 | 1% each | "thanks for participating" |
| 11+ | 0% | ~52% of pool rolls over to next epoch |

Within rank 1's 40%, the AC (algorithm contributor — solver author)
gets `p × 55%` and CP (compute provider) gets `(1-p) × 55%`, where
`p ∈ [0.10, 0.90]` is set by SP at registration. L3/L2/L1 contributors
get 15%/10%/5% respectively. The principle's treasury T_k gets 15%.

---

## Registration tiers — what's mineable, what's claimable, what's neither

Every L1/L2/L3 manifest carries a `registration_tier` field that tells
you exactly where the artifact sits in its lifecycle. Three values:

| Tier | Field value | What it means | Mineable? | Pool funded? |
|---|---|---|---|---|
| **Tier 1** | `"founder_vetted"` | Founders personally ran the reference solver, confirmed scoring, funded the pool. Today: L1-003 + L1-004 (CASSI + CACTI) + their L2/L3 children. | ✓ Yes | ✓ Yes |
| **Tier 2** | `"community_proposed"` | External contributor PR'd the missing pieces (reference solver, IPFS dataset, S1-S4 review). Multisig signed `PWMRegistry.register()` after merge. None today (post-launch path). | ✓ Yes | ✓ Yes (capped) |
| **Tier 3** | `"stub"` | JSON manifest exists in repo as a "claim board" entry. Forward model declared, but no reference solver, no dataset, not registered on-chain. **The 529 of 531 cataloged manifests sit at this tier today.** | ✗ No (cert submits succeed but resolve to a zero pool) | ✗ No |

### Inspect the tier of any artifact

```bash
jq -r '.registration_tier' pwm-team/content/agent-imaging/principles/C_medical_imaging/L1-503_qsm.json
# Output: stub

jq -r '.registration_tier' pwm-team/pwm_product/genesis/l1/L1-003.json
# Output: founder_vetted
```

### Why the 529 stubs don't drain mainnet

`PWMReward.distribute()` only pays out for cert hashes whose
`benchmarkHash` resolves to a **registered** L3 in `PWMRegistry`.
Stubs aren't registered, so a cert submitted against L3-523 (for
example) lands in a zero-pool — the cert is recorded for
reproducibility purposes, but no PWM moves. Registration is
multisig-gated; only Tier 1 + promoted Tier 2 artifacts ever reach
the chain.

### How a Tier 3 stub becomes mineable

```
Tier 3 (stub in repo)              Tier 2 (community-vetted)         Tier 1 (founder-vetted)
──────────────────────             ───────────────────────────       ─────────────────────────
"L1-503 QSM exists as a    ──→     External contributor:        ──→  (rare; founders take
description; nobody has           1. Opens PR with reference         direct ownership only
written a solver yet"                solver                          for personally-proven
                                  2. Pins ≥1 dataset to IPFS         expertise — e.g. Cai
                                  3. Updates L3-XXX manifest         et al. for MST-L on
                                  4. Verifier-agent triple-           CASSI)
                                     reviews
                                  5. 3-of-5 multisig signs
                                     PWMRegistry.register()
                                  6. Per-principle pool funded
                                     (capped via maxBenchmarkPoolWei)
                                  ↓
                                  Now mineable on mainnet
```

For the per-PR contribution policy and gate criteria, see
`pwm-team/customer_guide/PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md`.

### Hash invariance — adding `registration_tier` doesn't break existing on-chain hashes

`registration_tier` is in the `UI_ONLY_FIELDS` filter (alongside
`display_slug`, `display_color`, `ui_metadata`). The canonical-JSON
hashing strips it before computing keccak256, so:

- L1-003's on-chain hash `0xe3b1328c…99a51ea` stays valid after the
  field is added (verified 2026-05-06).
- Tier promotion (stub → community_proposed → founder_vetted)
  changes the catalog metadata without re-registering the artifact
  or invalidating prior certs.

---

## End-to-end concrete user journeys

### Journey A — PhD student comparing their CASSI method to SOTA

1. Visit `https://explorer.pwm.platformai.org/benchmarks/L3-003`
2. Note the two reference floors at the top: classical floor (GAP-TV
   ~26 dB) and deep-learning floor (MST-L 35.30 dB). Their method
   must beat at least the classical floor to register meaningful
   improvement; beating the deep-learning floor is the harder gate.
3. Click "Get this benchmark" → download inputs
4. Run their method locally → compute PSNR
5. Compare to leaderboard (rank 1 today: MST-L at 35.30 dB; the
   `improvement_db` shown on the page is `current_sota − classical_floor`,
   i.e. the +9.3 dB gap PWM has surfaced so far)
6. **Optional:** `pwm-node mine L3-003 --solver my_method.py` to make
   the comparison auditable in their paper

**Time:** ~30 min (excluding their solver dev time)
**Cost:** $0 if local-only; ~$1 Sepolia gas if submitting

### Journey B — AI imaging vendor proving robustness for FDA

1. Read the Chest CT severity Principle. L1-514 is a Tier-3 stub today
   (catalog entry, not yet on-chain), so `pwm-node inspect` can't load
   it; read the manifest directly:
   ```bash
   jq . pwm-team/content/agent-imaging/principles/C_medical_imaging/L1-514_chest_ct_severity_pwdr.json
   ```
   When L1-514 graduates to Tier-1 / Tier-2 (founder_vetted /
   community_proposed), `pwm-node inspect L1-514` will surface it.
2. Download the L3-514 dataset (when registered on mainnet)
3. Run their AI on the holdout split → compute classification accuracy + calibration
4. `pwm-node mine L3-514 --solver our_ai_wrapper.py`
5. Cite the cert hash in their FDA submission as third-party-verifiable evidence

### Journey C — Regulator verifying Aidoc's pneumothorax claim

1. Aidoc publishes: "Cert 0xabcd... shows 95% sensitivity on L3-523"
2. Regulator opens `https://explorer.pwm.platformai.org/cert/0xabcd...`
   (or pulls the same data from the on-chain `CertificateSubmitted`
   event via `https://sepolia.etherscan.io/tx/0xabcd...`)
3. The page confirms: cert references L3-523, score is 0.95, submitter
   is Aidoc's published wallet, cert finalized (challenge period clean)
4. Regulator can re-download the L3-523 holdout split and
   independently re-verify if desired

> **Worked example (real cert, real chain data):** the L3-523/Aidoc
> example above is hypothetical (L3-523 isn't registered on-chain
> yet — it's a Tier-3 stub). For a regulator-style verification
> against a *real* on-chain cert today, follow
> [`PWM_VERIFY_MST_L_CASSI_CLAIM_2026-05-06.md`](PWM_VERIFY_MST_L_CASSI_CLAIM_2026-05-06.md).
> It walks the same Journey C steps against the live MST-L CASSI
> cert (`0x7c7740…e13`, Q_int 35, PSNR 35.295 dB) at five increasing
> depth levels — explorer page → Etherscan event → contract
> state read → re-derive cert hash from the payload bytes → rerun
> the solver and confirm the same Q.

### Journey D — External developer writing a new Principle (Bounty #7 Tier B)

1. Pick an unauthored anchor from `PWM_V3_MEDICAL_IMAGING_CANDIDATES.md`
2. Author L1/L2/L3 manifests following the schema
3. Submit PR to `integritynoble/pwm-public`
4. Pass the verifier-agent triple-review (S1-S4 gates)
5. Manifests get registered on-chain at next genesis-extension event
6. Receive Bounty #7 Tier B reward (~2,000 PWM per anchor) on first
   external L4 submission

### Journey E — Founder or external miner populating the leaderboard

1. Set up a Linux box with NVIDIA + CUDA + Python 3.10+ (CPU works
   too, just slower)
2. Clone the repo: `git clone https://github.com/integritynoble/pwm-public.git && cd pwm-public`
3. Install: `pip install -e pwm-team/infrastructure/agent-cli`
4. Set env: `export PWM_PRIVATE_KEY=0x<funded-Sepolia-key>` and
   `export SEPOLIA_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com`
5. Run `bash scripts/testnet_mine_walkthrough.sh`
6. Both CASSI and CACTI cert hashes appear on the leaderboard within
   ~1-2 minutes of the on-chain confirmation
7. After 7 days (challenge-period clean), the cert auto-becomes
   citable — finalization is an on-chain call against
   `PWMCertificate.finalize(cert_hash)`. Until a CLI wrapper ships,
   anyone can call it directly via `cast send` (Foundry) or web3.py.
8. Cite cert hashes wherever — papers, FDA submissions, grant
   applications

---

## Quick reference table — all commands

| Want to… | Command |
|---|---|
| Browse all Principles (web) | `https://explorer.pwm.platformai.org/principles` |
| Browse all Principles (CLI) | `pwm-node principles` |
| Browse all Benchmarks (CLI) | `pwm-node benchmarks` |
| Find a Principle for your problem | `pwm-node match "<description>"` |
| Read one Principle | `pwm-node inspect L1-XXX` |
| Read one Spec | `pwm-node inspect L2-XXX` |
| Read one Benchmark | `pwm-node inspect L3-XXX` |
| Download a benchmark dataset | "Get this benchmark" card on `/benchmarks/L3-XXX` |
| Compare your solver locally (no tx) | `pwm-node mine L3-XXX --solver your.py --dry-run` |
| Submit cert on-chain | `pwm-node mine L3-XXX --solver your.py` |
| Verify someone's published claim | `https://explorer.pwm.platformai.org/cert/0x...` (or Etherscan tx URL) |
| Stake on a Principle | `pwm-node stake principle 0x<L1-hash>` |
| Stake on a Benchmark | `pwm-node stake benchmark 0x<L3-hash>` |
| Finalize a cert (after 7d) | on-chain only: `cast send <PWMCertificate> "finalize(bytes32)" 0x<cert-hash>` (CLI wrapper TBD) |
| Run full CASSI+CACTI lifecycle | `bash scripts/testnet_mine_walkthrough.sh` |
| Register a new L1/L2/L3 | open a `[L1 claim]` issue per `PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md`; agent-coord registers via `scripts/register_genesis.py --network testnet` (script's `ARTIFACTS_TO_REGISTER` list is hardcoded; no `--manifest` / `--layer` flags) |

## What network for what action

The CLI accepts three values for `--network`: `offline`, `testnet`,
`mainnet`. The actual chain selected depends on which entry is
populated in `pwm-team/infrastructure/agent-contracts/addresses.json`.

| Network flag | Resolves to (today) | Use for |
|---|---|---|
| `--network offline` (default) | No chain | Reading local JSON manifests; pure metadata browsing; `pwm-node principles` and `inspect` work without RPC |
| `--network testnet` | Ethereum Sepolia (chainId 11155111) | All examples in this guide; live testnet today; ~$0 in real money |
| `--network mainnet` | Base mainnet (chainId 8453) at launch — `addresses.json:mainnet` is currently null and gets populated on D9 | Production mining once Step 11 (founder mining live) lands; same flag as testnet, just a different `addresses.json` entry |

The Base Sepolia dress-rehearsal step (chainId 84532) is run by
swapping the `testnet` entry in `addresses.json` to point at the
Base Sepolia contracts during Step 5, then swapping back. It's not
a separate CLI flag.

## Common confusions

| ❓ | ✓ |
|---|---|
| "I need to register all 4 layers myself before mining" | No. L1/L2/L3 are typically registered once by Principle authors. As a miner (L4) you just need to find an existing benchmark and submit certs against it. |
| "Mining requires a GPU" | Only for solvers that use deep-learning models (MST, EfficientSCI). The reference solvers `cassi_gap_tv.py` + `cacti_pnp_admm.py` run on numpy CPU only. |
| "I need to be a founder to use PWM" | No. Anyone with a funded testnet wallet can stake + mine. External developers are the *primary* audience; founders are the bootstrap. |
| "Verifying a cert requires my own Sepolia ETH" | No. The explorer URL and Etherscan are pure reads — no tx, no gas, no wallet needed. |
| "L4 = my reconstruction output" | Close but not quite. L4 = a **certificate** that includes the Q score + a hash binding the score to a specific (solver, benchmark, ω) tuple. The actual reconstruction can be off-chain (IPFS-pinned). |

---

## Cross-references

### Inside this public repo (pwm-public)

User-facing content that ships with the repo and that every reader of
this guide can open directly:

- `pwm-team/customer_guide/plan.md` — current customer-experience roadmap (Phase 1 / 2 / 3)
- `pwm-team/customer_guide/PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md` — full flow for authoring a NEW Principle (claim board, manifest schema, PR template)
- `pwm-team/customer_guide/PWM_Q_SCORE_EXPLAINED_2026-05-06.md` — what `Q_int` on the leaderboard actually means + how PSNR floor/ceiling normalization works (CASSI 26.49 dB → Q_int 85 worked example)
- `pwm-team/customer_guide/PWM_ONCHAIN_VS_OFFCHAIN_ARCHITECTURE_2026-05-05.md` — what data lives on-chain (registry hashes, cert payloads) vs off-chain (manifests, datasets, cert-meta), and how they're bound together by keccak256
- `pwm-team/customer_guide/PWM_VERIFY_MST_L_CASSI_CLAIM_2026-05-06.md` — concrete walkthrough of independently verifying the MST-L 35.295 dB cert (`0x7c7740…e13`); mirrors Journey C with real on-chain data
- `pwm-team/bounties/INDEX.md` — Reserve-bounty roster (8 bounties, ~1.24M PWM allocated)
- `pwm-team/bounties/07-claims.md` — FCFS claim board (open to general L1/L2/L3 contributions, not just Bounty #7 Tier B)
- `pwm-team/infrastructure/agent-cli/README.md` — full `pwm-node` CLI docs
- `pwm-team/pwm_product/reference_solvers/` — reference solvers (CASSI GAP-TV, CASSI MST-L, CACTI PnP-ADMM, CACTI EfficientSCI)
- `pwm-team/pwm_product/genesis/l1/`, `l2/`, `l3/` — canonical genesis manifests
- `pwm-team/content/agent-{imaging,physics,chemistry,applied,signal}/principles/` — domain-organized full catalog (~1599 manifests, 531 first-class Principles)
- `scripts/testnet_mine_walkthrough.sh` — one-command full lifecycle for both CASSI and CACTI on Sepolia
- `scripts/register_genesis.py` — canonical on-chain registration tool (used both by founders and external contributors)

### External resources

- `https://explorer.pwm.platformai.org/` — public web frontend (browse, match, view leaderboards)
- `https://sepolia.etherscan.io/address/0x2375217dd8FeC420707D53C75C86e2258FBaab65` — PWMRegistry contract on Sepolia (canonical artifact registry)
- `https://sepolia.etherscan.io/address/0x8963b60454EC1D9F65eE3cbF7aBC5D1220C3dB08` — PWMCertificate contract on Sepolia (where mining txns land)

### Internal-only design notes (NOT mirrored to the public repo)

These docs live in the founding-team's private coordination tree.
Listed here for cross-session continuity only; public-repo readers
don't need any of them — everything customer-facing is in the guide
above plus `PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md`.

- `PWM_TESTNET_TESTING_GUIDE_2026-05-02.md` — testnet basics + 4 testing paths
- `PWM_TESTNET_MINE_WALKTHROUGH_USAGE_2026-05-03.md` — walkthrough-script usage notes
- `PWM_OPTION_C_HANDOFF_GPU_SUBMISSION_2026-05-02.md` — GPU machine setup procedure
- `PWM_TESTNET_TESTING_DEPTH_2026-05-02.md` — strategic posture on testnet testing depth
- `PWM_LEADERBOARD_DISPLAY_DESIGN_2026-05-03.md` — design rationale for the SOTA / Reference / Delta header
- `PWM_HUMAN_READABLE_IDS_AND_CONTRIBUTION_FLOW_2026-05-03.md` — design rationale for slugs + claim board
- `MAINNET_BLOCKERS_2026-04-30.md` — what's blocking Base mainnet deploy

---

## Memory anchors (for next-conversation continuity)

- **This guide is the canonical reference** for "how do I create or use PWM artifacts" — when Director (or anyone) asks similar questions in future sessions, point here first
- **Producer vs consumer split:** most PWM users are consumers; the protocol design front-loads consumer ease-of-use
- **L1/L2/L3 = registered (one-time):** L4 = mined (repeated); staking is orthogonal and optional
- **The walkthrough script** (`scripts/testnet_mine_walkthrough.sh`) automates Journey E — Director's path to populating the testnet leaderboard
- **All examples in this guide work on Sepolia today** — Base Sepolia + Base mainnet are forthcoming. The CLI's `--network mainnet` flag will resolve to Base mainnet contracts (via `addresses.json:mainnet`) once D9 populates that entry; no new flag values are added.
- **Registration tiers (added 2026-05-06):** every L1/L2/L3 manifest carries a `registration_tier` field — `founder_vetted` (today: 2 Principles + their L2/L3 children, registered on Sepolia), `community_proposed` (none yet — post-launch path), or `stub` (529 cataloged inventory entries awaiting a contributor). Only Tier 1 + promoted Tier 2 are mineable; Tier 3 stubs can't drain the mainnet pool. `registration_tier` is in `UI_ONLY_FIELDS` so adding/promoting it is hash-invariant.
