# PWM Layers — Complete Guide: Create + Use (L1 / L2 / L3 / L4)

**Date:** 2026-05-03
**Audience:** Researchers, students, industry teams, regulators, external developers, founders
**Network:** Ethereum Sepolia testnet (chainId 11155111) for examples; Base mainnet flow identical, just swap `--network testnet` → `--network base`
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

# 2. For miners running deep-learning solvers (MST-L, EfficientSCI, etc.):
pip install -e public/packages/pwm_core   # path inside the pwm-public repo
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
# (adjust the cu128 wheel suffix to match your local CUDA version; CPU-only
#  also works for development, just slower)
```

---

# Layer 1 — Principle

The physics declaration: forward model + parameter space + DAG primitive chain + complexity score.

## L1 — How CONSUMERS use existing Principles

### Browse the catalog (web)

`https://explorer.pwm.platformai.org/principles` — 531 Principles
filterable by domain.

### Browse the catalog (CLI)

```bash
pwm-node --network testnet benchmarks
# Lists all registered L3 benchmarks; each maps back to its parent L1
```

### Inspect one Principle in detail

```bash
pwm-node --network testnet inspect L1-003
# Prints title, domain, gate_class, ω parameters, forward model,
# DAG primitive chain, L_DAG complexity score, references
```

Or read the JSON directly:

```bash
cat pwm-team/pwm_product/genesis/l1/L1-003.json
# Or by domain:
ls pwm-team/content/agent-imaging/principles/      # 100+ medical imaging
ls pwm-team/content/agent-physics/principles/      # 100+ physics
ls pwm-team/content/agent-chemistry/principles/    # 60+ chemistry
ls pwm-team/content/agent-applied/principles/      # 30+ applied
ls pwm-team/content/agent-signal/principles/       # 20+ signal processing
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

```bash
PWM_PRIVATE_KEY=$PWM_PRIVATE_KEY \
PWM_RPC_URL=$SEPOLIA_RPC_URL \
python3 scripts/register_genesis.py \
  --network testnet \
  --manifest my_new_principle/L1-100_my_principle.json \
  --layer L1
# Emits ArtifactRegistered event; saves the keccak256(canonical_json)
# hash to addresses.json for staking later
```

### Stake on an existing Principle (back its credibility)

```bash
pwm-node --network testnet stake quote principle      # show required ~$50 PWM
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

```bash
# Same shape as L1, but include parent_l1 + the six-tuple fields
python3 scripts/register_genesis.py \
  --network testnet \
  --manifest my_new_principle/L2-100_my_spec.json \
  --layer L2 \
  --parent-l1 0x<L1-100-hash>
```

### Stake on an existing Spec (~$5 tier)

```bash
pwm-node --network testnet stake quote spec
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

### Inspect via CLI

```bash
pwm-node --network testnet inspect L3-003
# Prints title, parent L2/L1, n_dev_instances, scoring metric,
# current rank-1 score, dataset CIDs, ω parameters
```

### Download the dataset

The L3 manifest lists dataset CIDs in `dataset_registry`. Pull via IPFS:

```bash
# Option 1: web "Get this benchmark" card on the explorer
# Option 2: programmatic
ipfs get <CID-from-L3-manifest> -o ./cassi_data/

# Option 3: pwm-node helper (if your benchmark inputs are on-chain-resolvable)
pwm-node --network testnet fetch-benchmark L3-003 --output ./cassi_data/
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

## L3 — How PRODUCERS create new Benchmarks

### Author + register

```bash
python3 scripts/register_genesis.py \
  --network testnet \
  --manifest my_new_principle/L3-100_my_benchmark.json \
  --layer L3 \
  --parent-l2 0x<L2-100-hash>
```

The L3 manifest must include:

- `rho` (typically 50)
- `dataset_registry`: dataset CIDs + ground-truth provenance
- `ibenchmarks`: list of tier specifications (T1_nominal, T2_off_axis, etc.)
- `anti_overfitting_mechanisms`: M1-M6 implementations per gate class
- `scoring`: primary + secondary metric + Q formula
- `hardness_rule_check`: proof no expert baseline passes ε everywhere

### Stake on an existing Benchmark (~$1 tier)

```bash
pwm-node --network testnet stake quote benchmark
pwm-node --network testnet stake benchmark 0x<L3-hash>
```

---

# Layer 4 — Solution (Certificate)

The actual "mining" loop: run a solver, compute a quality score Q, submit a tamper-resistant certificate on-chain.

## L4 — How CONSUMERS use existing Certificates

### Verify a published claim

A vendor publishes "We scored 0.95 on PWM L3-523, cert 0xb293...". Verify:

```bash
pwm-node --network testnet verify-cert 0xb293...
# Returns:
#   benchmark: L3-523 (Pneumothorax CXR detection)
#   submitter: 0xab12...cd34
#   Q score: 0.95
#   solver_label: <whatever the submitter declared>
#   submitted block: 10720312
#   challenge status: clean (7-day window passed)
#   finalized: yes, rewards distributed
```

Or via Etherscan:

```
https://sepolia.etherscan.io/tx/0xb293...
```

The on-chain `CertificateSubmitted` event holds all the same data
immutably.

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
pwm-node --network testnet finalize <cert_hash>
# Rank 1 wins 40% of pool, rank 2 wins 5%, rank 3 wins 2%, rank 4-10 win 1% each
```

### One-shot for both CASSI + CACTI

The repo includes a complete walkthrough script:

```bash
bash scripts/testnet_mine_walkthrough.sh
# Pre-flight + hash compute + CASSI stake/mine + CACTI stake/mine + summary
# Knobs: CASSI_ONLY=1, DRY_RUN=1, SKIP_STAKE=1
```

See `PWM_TESTNET_MINE_WALKTHROUGH_USAGE_2026-05-03.md` for the full
usage guide.

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

## End-to-end concrete user journeys

### Journey A — PhD student comparing their CASSI method to SOTA

1. Visit `https://explorer.pwm.platformai.org/benchmarks/L3-003`
2. Click "Get this benchmark" → download inputs
3. Run their method locally → compute PSNR
4. Compare to leaderboard (rank 1 = MST-L 34.1 dB)
5. **Optional:** `pwm-node mine L3-003 --solver my_method.py` to make
   the comparison auditable in their paper

**Time:** ~30 min (excluding their solver dev time)
**Cost:** $0 if local-only; ~$1 Sepolia gas if submitting

### Journey B — AI imaging vendor proving robustness for FDA

1. `pwm-node inspect L1-514` to read the Chest CT severity Principle
2. Download the L3-514 dataset (when registered on mainnet)
3. Run their AI on the holdout split → compute classification accuracy + calibration
4. `pwm-node mine L3-514 --solver our_ai_wrapper.py`
5. Cite the cert hash in their FDA submission as third-party-verifiable evidence

### Journey C — Regulator verifying Aidoc's pneumothorax claim

1. Aidoc publishes: "Cert 0xabcd... shows 95% sensitivity on L3-523"
2. Regulator runs `pwm-node verify-cert 0xabcd...`
3. CLI confirms: cert references L3-523, score is 0.95, submitter is
   Aidoc's published wallet, cert finalized (challenge period clean)
4. Regulator can re-download the L3-523 holdout split and
   independently re-verify if desired

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
7. After 7 days (challenge-period clean), finalize each cert with
   `pwm-node finalize <cert_hash>`
8. Cite cert hashes wherever — papers, FDA submissions, grant
   applications

---

## Quick reference table — all commands

| Want to… | Command |
|---|---|
| Browse all Principles (web) | `https://explorer.pwm.platformai.org/principles` |
| Browse all Benchmarks (CLI) | `pwm-node --network testnet benchmarks` |
| Find a Principle for your problem | `pwm-node match "<description>"` |
| Read one Principle | `pwm-node --network testnet inspect L1-XXX` |
| Read one Spec | `pwm-node --network testnet inspect L2-XXX` |
| Read one Benchmark | `pwm-node --network testnet inspect L3-XXX` |
| Download a benchmark dataset | "Get this benchmark" card on `/benchmarks/L3-XXX` |
| Compare your solver locally (no tx) | `pwm-node mine L3-XXX --solver your.py --dry-run` |
| Submit cert on-chain | `pwm-node mine L3-XXX --solver your.py` |
| Verify someone's published claim | `pwm-node verify-cert 0x...` |
| Stake on a Principle | `pwm-node stake principle 0x<L1-hash>` |
| Stake on a Benchmark | `pwm-node stake benchmark 0x<L3-hash>` |
| Finalize a cert (after 7d) | `pwm-node finalize 0x<cert-hash>` |
| Run full CASSI+CACTI lifecycle | `bash scripts/testnet_mine_walkthrough.sh` |
| Register a new L1/L2/L3 | `python3 scripts/register_genesis.py --network testnet --manifest <path> --layer <L1|L2|L3>` |

## What network for what action

| Network | Use for |
|---|---|
| `--network offline` | Reading local JSON manifests; pure metadata browsing |
| `--network testnet` (Sepolia chainId 11155111) | All examples in this guide; live testnet today; ~$0 in real money |
| `--network baseSepolia` (chainId 84532) | Step 5 dress rehearsal (pending hardware wallets) |
| `--network base` (chainId 8453) | Base mainnet — production once Step 11 lands (~3-4 weeks out per `MAINNET_BLOCKERS_2026-04-30.md`) |

## Common confusions

| ❓ | ✓ |
|---|---|
| "I need to register all 4 layers myself before mining" | No. L1/L2/L3 are typically registered once by Principle authors. As a miner (L4) you just need to find an existing benchmark and submit certs against it. |
| "Mining requires a GPU" | Only for solvers that use deep-learning models (MST, EfficientSCI). The reference solvers `cassi_gap_tv.py` + `cacti_pnp_admm.py` run on numpy CPU only. |
| "I need to be a founder to use PWM" | No. Anyone with a funded testnet wallet can stake + mine. External developers are the *primary* audience; founders are the bootstrap. |
| "Verifying a cert requires my own Sepolia ETH" | No. `verify-cert` is read-only; no tx, no gas. |
| "L4 = my reconstruction output" | Close but not quite. L4 = a **certificate** that includes the Q score + a hash binding the score to a specific (solver, benchmark, ω) tuple. The actual reconstruction can be off-chain (IPFS-pinned). |

---

## Cross-references

### Inside this public repo (pwm-public)

User-facing content that ships with the repo and that every reader of
this guide can open directly:

- `pwm-team/customer_guide/plan.md` — current customer-experience roadmap (Phase 1 / 2 / 3)
- `pwm-team/coordination/PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md` — full flow for authoring a NEW Principle (claim board, manifest schema, PR template)
- `pwm-team/coordination/agent-coord/interfaces/bounties/INDEX.md` — Reserve-bounty roster (8 bounties, ~1.24M PWM allocated)
- `pwm-team/coordination/agent-coord/interfaces/bounties/07-claims.md` — FCFS claim board (open to general L1/L2/L3 contributions, not just Bounty #7 Tier B)
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
- **All examples in this guide work on Sepolia today** — Base Sepolia + Base mainnet are forthcoming; the CLI is network-agnostic via the `--network` flag
