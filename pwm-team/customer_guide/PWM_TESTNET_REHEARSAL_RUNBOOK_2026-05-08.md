# Testnet Rehearsal Runbook — Bridging Sepolia Smoothness to Mainnet Readiness

**Date:** 2026-05-08
**Audience:** Director (and any miner planning a Base mainnet workflow)
**Trigger question (Director, 2026-05-08):**
> "If testing the customer guide in Sepolia smoothly, can it work in
> mainnet smoothly?"

**Companion docs:**
`PWM_CROSS_CHAIN_UX_DESIGN_2026-05-08.md` (what's the same / different),
`PWM_DEPLOY_DAY_PLAYBOOK_2026-05-08.md` (D9 morning runbook),
`PWM_BUG_FIX_PLAYBOOK_2026-05-08.md` (post-deploy fixes),
`pwm-team/coordination/PWM_CUSTOMER_GUIDE_TESTNET_VERIFICATION_2026-05-08.md`
(42/42 PASS verification of the user-facing flows).

---

## TL;DR

**Smooth on Sepolia is a strong necessary condition for smooth on
mainnet but not a sufficient one.** The customer guide's user-facing
flows passed 42/42 on Sepolia today, which proves the chain-agnostic
parts (CLI, hashes, payload schema, gate code, reward formula). But
six chain-identity gotchas remain — testnet doesn't surface them.

This runbook lists the six gotchas and prescribes a **week-before-D9
rehearsal** that exercises each one against Base Sepolia (or a Base
mainnet fork) so the first time you encounter them isn't on the day
real money is at stake.

---

## What testnet smoothness DOES prove

Verified 42/42 PASS on 2026-05-08 (see
`PWM_CUSTOMER_GUIDE_TESTNET_VERIFICATION_2026-05-08.md`):

- ✅ CLI surface complete and functional
- ✅ Catalog browsing (`principles`, `benchmarks`, `inspect`,
  `match`) — all 4 work end-to-end
- ✅ Manifest hashes (`keccak256(canonical_json)`) match expected
  byte-for-byte
- ✅ Two-tier reference floor + SOTA + delta computation
- ✅ Live cert detail via explorer + Etherscan
- ✅ Walkthrough script exists with documented knobs
- ✅ Reference solvers (4) all present
- ✅ Registration tier ladder (stub vs founder_vetted)
- ✅ Hash invariance under `UI_ONLY_FIELDS` filter
- ✅ Cross-references resolve

Per `PWM_CROSS_CHAIN_UX_DESIGN_2026-05-08.md` § 1, these properties
are **chain-agnostic** — they will behave identically on Base
mainnet. So the testnet success proof carries over.

---

## What testnet smoothness DOES NOT prove

Six chain-identity gotchas that only surface on real-money infra:

### Gotcha 1 — Gas economics

| Sepolia | Base mainnet |
|---|---|
| Free ETH from a faucet (Alchemy / publicnode / quicknode) | Real ETH; ~$0.005 per cert tx today, **spikes to $0.10+ during congestion** |
| `gasPrice` rarely matters (free) | Set `gasPrice` explicitly or pay 5-10× during high-demand windows |
| Out-of-gas tx? Resubmit free | Out-of-gas tx? Lose the gas you paid + nonce churn |
| Workflow that submits 50 certs/hour costs $0 | Same workflow during a Base congestion event can cost $5-50 per cert |

### Gotcha 2 — RPC reliability

| Sepolia | Base mainnet |
|---|---|
| Free public RPCs (publicnode, ankr) — flaky but cost nothing | Need a stable provider (Alchemy / Infura / QuickNode) — costs $30-300/mo |
| Tx dropped due to RPC outage? Resubmit | Tx dropped on Base? You may have already paid gas without state changing |
| Indexer falling 5 minutes behind on Sepolia is normal | On Base, the same lag during high TVL means the leaderboard is showing stale data to other miners — they may submit duplicates |

### Gotcha 3 — MEV / front-running

| Sepolia | Base mainnet |
|---|---|
| No MEV searchers; mempool is sparse | Active MEV bots watching every cert submission for arb opportunities |
| Submit cert with sequential nonce: txs land in order | Submit cert with sequential nonce on Base: a bot can sandwich your tx, observing your `Q_int` before your tx confirms |
| Solver workflow that does not protect `_compute_q_p` output: fine on testnet | Same workflow on mainnet: a competitor sees your Q before you commit, can submit a slightly-better cert in the same block |

### Gotcha 4 — Wallet management

| Sepolia | Base mainnet |
|---|---|
| Hot wallet ($PWM_PRIVATE_KEY env var) is fine — keys hold $0 of real value | **Hardware wallet mandatory** for any cert with non-trivial Q_int |
| Lost private key = lost faucet ETH ($0) | Lost private key = lost real ETH + lost mining rewards forever |
| Forgot to set `--gas` arg? Tx works anyway | Forgot to set `--gas` on Base? Pay 10× more than you needed |
| 1-of-1 single-sig acceptable for founder-only ops | **Multisig (3-of-5 founders + 48h timelock) mandatory for governance ops** |

### Gotcha 5 — Leaderboard population dynamics

| Sepolia | Base mainnet |
|---|---|
| 141 certs already on chain (founder-wallet test data + early miners) | **Starts at 0 certs** on D9 — empty leaderboard |
| `current_sota` is well-defined (MST-L from cert-meta enrichment) | Day-one mainnet: `current_sota` is `null` until the first cert finalizes; explorer falls back to "no certs yet" view |
| `improvement_db` is a stable +9.3 dB number | Day-one mainnet: `improvement_db` is `null`; UI must handle the empty state |
| `synthetic_filtered: 99` (lots of test data hidden) | Day-one mainnet: `synthetic_filtered: 0` (no synthetic, also no real) |

### Gotcha 6 — Real challengers

| Sepolia | Base mainnet |
|---|---|
| 0 upheld challenges in the entire history | **Bug bounty hunters watching from day one** (Immunefi listing exposes this) |
| If someone challenges your cert, it's likely a friendly drill | Real adversaries may game the challenge window for the slashing reward (challenger gets your stake) |
| You probably never invoke `PWMCertificate.challenge` yourself | Best practice: do a challenge drill against your own cert during the rehearsal — get the muscle memory before D9 |

---

## The week-before-D9 rehearsal

Run these 7 procedures against Base Sepolia (chainId 84532) in the
7 days leading up to D9. Each procedure addresses one or more
gotchas above. Use the **same hardware, same RPC provider, same
wallet hygiene** you'll use on D9.

### Rehearsal 1 — Hardware-wallet mining (Gotchas 4, 5)

```bash
# Use D3's actual Ledger / Trezor — NOT a hot wallet
# Set up Base Sepolia via:
export PWM_RPC_URL=https://sepolia.base.org    # or your Alchemy/Infura URL
export PWM_NETWORK=baseSepolia                  # uses addresses.json:baseSepolia

# Sign with the hardware wallet via Frame or a similar HW-aware RPC proxy
# DO NOT export the private key — sign in-place
pwm-node --network baseSepolia mine L3-003 \
  --solver pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py
```

**What to watch for:**
- The HW wallet shows the right `PWMCertificate.submit()` calldata
- The fees field on the HW screen matches your gas estimate
- The cert hash printed by the CLI matches what the HW signs
- The transaction lands within ~1 block; confirm via Base Sepolia explorer

**If anything looks wrong:** STOP. The HW wallet's display is the
last line of defense. Anything you can't read on the HW screen, you
shouldn't sign.

### Rehearsal 2 — Stable-RPC stress test (Gotcha 2)

```bash
# Use the SAME Alchemy / Infura URL you'll use on Base mainnet,
# pointed at Base Sepolia for the rehearsal
export PWM_RPC_URL=https://base-sepolia.g.alchemy.com/v2/<your-key>

# Submit 7 certs in rapid succession (matching D9 Step 11 founder-mining)
for i in 1 2 3 4 5 6 7; do
  pwm-node --network baseSepolia mine L3-003 \
    --solver pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py \
    --seed $i
done
```

**What to watch for:**
- All 7 txs land within reasonable time (~5 minutes total)
- No "RPC error" / "tx dropped" / "nonce too low" failures
- The indexer catches up (visible on the explorer leaderboard)

**If anything looks wrong:** Either the RPC provider is undersized
(upgrade to a paid tier) or the nonce management is wrong (use
`--nonce-strategy sequential` and pre-fund enough ETH for all 7).

### Rehearsal 3 — Gas-spike survival (Gotcha 1)

```bash
# Configure --gas to a fixed maximum
pwm-node --network baseSepolia mine L3-003 \
  --solver pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py \
  --gas 250000   # explicit ceiling

# Then submit during a high-traffic Sepolia window (e.g. coincide
# with a known L2 deployment campaign)
```

**What to watch for:**
- The tx either lands at your set gas or reverts cleanly (no spending
  beyond the ceiling)
- If the network is too congested, your tx queues — does the CLI
  surface this clearly?

**If anything looks wrong:** Implement a `--max-gas-price` and
`--abort-if-above` feature in your D9 workflow. Manual eyeballing is
not safe at scale.

### Rehearsal 4 — Challenge drill (Gotcha 6)

```bash
# Account A: submit a deliberately-suspect cert
pwm-node --network baseSepolia mine L3-003 \
  --solver scripts/test_solvers/synthetic_high_q_solver.py \
  --account A
# Note the cert hash

# Account B: challenge the cert
# (within the 7-day window — but for rehearsal you'll do it
#  immediately to test the response flow)
cast send <PWMCertificate-baseSepolia> \
  "challenge(bytes32,bytes)" 0x<cert-hash> 0x<proof-bytes> \
  --rpc-url $PWM_RPC_URL \
  --account B
```

**What to watch for:**
- Account A's cert is invalidated within minutes
- Account B receives the slashed stake
- The `/cert/<hash>` page on the explorer shows `status: "challenged"`
- A `daily_stability_check.sh` run flags the challenge in its log

**If anything looks wrong:** The challenge proof format is wrong
(see `cert_schema.json`), or the multisig hasn't ruled. Fix the
proof construction; do not deploy until challenge mechanics work.

### Rehearsal 5 — Empty-leaderboard UX (Gotcha 5)

```bash
# Register a NEW L3 on Base Sepolia (a v2 of an existing benchmark
# at a fresh hash; deliberately not minable yet)
python3 scripts/register_genesis.py --network baseSepolia \
  --add-artifact L3-XXX-rehearsal-v1.json

# Visit https://sepolia.explorer.pwm.platformai.org/benchmarks/L3-XXX
# (or your testnet explorer URL)
```

**What to watch for:**
- The page renders cleanly with `current_sota: null`,
  `improvement_db: null`, `synthetic_filtered: 0`, empty `ranks[]`
- Reference floors still show (from the manifest's `baselines[]`)
- "Be the first to submit a solution" CTA visible
- No JavaScript error in the browser console

**If anything looks wrong:** Frontend has an empty-state bug — fix
in `pwm-team/infrastructure/agent-web/frontend/app/benchmarks/[ref]/page.tsx`
before D9.

### Rehearsal 6 — MEV-proof submission (Gotcha 3)

```bash
# Use a private mempool / flashbots / commit-reveal pattern
# (Base mainnet supports private bundles via Coinbase's RPC)
pwm-node --network baseSepolia mine L3-003 \
  --solver pwm-team/pwm_product/reference_solvers/cassi/cassi_mst.py \
  --use-private-mempool      # routes via Coinbase RPC instead of public
```

**What to watch for:**
- The tx never appears in the public mempool (check via
  `mempool.space` or equivalent)
- The cert lands at the same Q_int regardless of public visibility
- No competing cert at the same `(benchmark_hash, ω_instance, block)`

**If anything looks wrong:** You need a private-mempool integration
in the CLI. This is currently a gap (`pwm-node mine` uses the public
mempool by default). Track as a follow-up.

### Rehearsal 7 — Full lifecycle dry run (all gotchas)

```bash
# This is the big one — replicate everything you'll do on D9
# but on Base Sepolia. The full Step 11 founder-mining pattern:

bash scripts/testnet_mine_walkthrough.sh \
  PWM_NETWORK=baseSepolia \
  PWM_RPC_URL=$BASE_SEPOLIA_RPC_URL \
  CASSI_ONLY=0 \
  DRY_RUN=0
```

**What to watch for:**
- Pre-flight checks pass
- Hash compute matches expected values
- CASSI stake + mine succeeds
- CACTI stake + mine succeeds
- Summary exit code = 0
- All 7 founder mining txns land before the timer expires
- Explorer shows all 7 certs on the L3-003 / L3-004 leaderboards

**If anything looks wrong:** STOP. This rehearsal is the dress
rehearsal for D9 itself. Any failure here means D9 won't work
either. Fix; re-run; only proceed when this is clean.

---

## Decision matrix — go-no-go after rehearsal

| Rehearsals 1-7 | Go-no-go for D9? |
|---|---|
| All 7 PASS | ✅ Strong GO signal — proceed with D9 chain |
| 1-2 fail (e.g. private mempool unavailable) | 🟡 Conditional GO — document the workaround in the runbook; proceed if non-critical |
| 3+ fail | ❌ NO-GO — fix the underlying issues, re-run, do not proceed |
| Hardware wallet (Rehearsal 1) fails | ❌ NO-GO — D3 is not actually complete; fix wallet setup |
| Challenge drill (Rehearsal 4) fails | ❌ NO-GO — fraud-detection is broken; fix `cert_schema.json` and proof generation |
| Full lifecycle (Rehearsal 7) fails | ❌ NO-GO — root cause unknown; investigate fully before D9 |

---

## What the customer guide does NOT need to be re-tested for

After the 42/42 PASS verification this morning, the following are
**verified safe** to assume in the rehearsal — don't re-test them:

- CLI command surface (`pwm-node {principles, benchmarks, inspect,
  match, mine, stake, sp, balance, submit-cert, verify}`)
- Manifest hash recipe (`keccak256(canonical_json)` with
  `UI_ONLY_FIELDS` filter)
- Cert payload schema (12 chain-bound + 3 _meta)
- Gate logic (`pwm_scoring/gates.py`)
- Reward share formula (40/5/2/1×7 from `PWMReward.sol`)
- Solver invocation contract (`--input <dir> --output <dir>`)

These are chain-agnostic by design and verified live. The rehearsal
focuses entirely on chain-identity gotchas that the verification
couldn't reach.

---

## Sequencing within the runbook

Per `MAINNET_BLOCKERS_2026-04-30.md` and the `DIRECTOR_RUNBOOK_D1_TO_D10`,
the rehearsal slots in as part of **D5 — ≥ 20 non-founder L4
submissions on Base Sepolia**:

```
Day -7 to -3  : Rehearsals 1, 2, 5 — solo (Director only)
Day -3 to -1  : Rehearsals 3, 4, 6 — with one collaborator (challenger drill)
Day -1        : Rehearsal 7 (full lifecycle dry run)
Day 0         : Final pre-flight + GO/NO-GO call
Day +1 (D9)   : Mainnet deploy chain (Steps 8-12)
```

If Rehearsal 7 reveals a blocker on Day -1, you push D9 by one week
and re-run the full rehearsal. **Don't compress the rehearsal window;
the gotchas it catches are more expensive than the time it takes.**

---

## Cross-references

- `pwm-team/coordination/PWM_CUSTOMER_GUIDE_TESTNET_VERIFICATION_2026-05-08.md`
  — 42/42 PASS report on the customer-guide procedures
- `pwm-team/coordination/PWM_MAINNET_GO_NOGO_2026-05-08.md` — current
  red/yellow/green snapshot of D1–D9 prerequisites
- `pwm-team/customer_guide/PWM_DEPLOY_DAY_PLAYBOOK_2026-05-08.md`
  — 7-layer defense + D9 morning runbook
- `pwm-team/customer_guide/PWM_CROSS_CHAIN_UX_DESIGN_2026-05-08.md`
  — what's identical / different across chains (the 7+11 split)
- `pwm-team/customer_guide/PWM_BUG_FIX_PLAYBOOK_2026-05-08.md`
  — post-deploy fix mechanisms (UI_ONLY_FIELDS, cert-meta,
  versioning, challenges, governance)
- `pwm-team/customer_guide/PWM_DEPLOYMENT_FLOW_DESIGN_2026-05-08.md`
  — per-benchmark `challengePeriodSeconds` override
- `pwm-team/coordination/MAINNET_BLOCKERS_2026-04-30.md` — full
  Director / CPU action list
- `pwm-team/coordination/DIRECTOR_RUNBOOK_D1_TO_D10_2026-05-01.md`
  — Director-side step-by-step
- `scripts/testnet_mine_walkthrough.sh` — referenced in Rehearsal 7
- `scripts/preflight_step5_fork.sh` + `scripts/preflight_step8_fork.sh`
  — fork preflights to re-run morning of D9
