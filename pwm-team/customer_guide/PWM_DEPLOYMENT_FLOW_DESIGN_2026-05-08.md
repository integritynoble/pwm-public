# Deployment Flow Design — Testnet → Mainnet for L1/L2/L3/L4

**Date:** 2026-05-08
**Audience:** Director, founders evaluating governance-parameter tunings, contributors deploying new artifacts
**Trigger question (Director, 2026-05-08):**
> "Challenge a fraudulent / wrong L4 cert (during the 7-day window).
> Is 7-days long? How about L4 can be available directly after L4 is
> deployed in testnet and only after 7 days or some verification, can
> be deployed in mainnet? All L1, L2, L3 and L4 should use the same
> method. First in testnet and available to everyone and after
> verification, be deployed in mainnet?"

---

## TL;DR

| Layer | Testnet → mainnet flow today | Recommended change |
|---|---|---|
| **L1 / L2 / L3** | Already works that way: `registration_tier: stub` (catalog, off-chain) → `community_proposed` (Sepolia, multisig-registered) → `founder_vetted` (Base mainnet, multisig-registered). CASSI / CACTI sat on Sepolia for ~weeks before mainnet. | **No structural change.** Document the convention more prominently. |
| **L4** | Each cert lives on the chain it's submitted to. Sepolia certs and mainnet certs have separate hashes; same cert can be re-submitted to both. The 7-day challenge window is the same on both chains. | **Expose per-benchmark `challengePeriodSeconds` override.** Don't force a mandatory testnet → mainnet flow for L4 (would break reward economics — see § 5). |

The 7-day default is appropriate for new L3 benchmarks; for proven L3s
(CASSI / CACTI after 12+ months on-chain) it's overkill. Multisig can
shorten the window per-benchmark via `PWMGovernance.setParameter`,
which the contract already supports. This document spells out when
and why.

---

## 1. The 7-day challenge window — why it's the default

Per `pwm-team/infrastructure/agent-contracts/contracts/PWMCertificate.sol:CHALLENGE_PERIOD_DEFAULT`:

```solidity
uint64 public constant CHALLENGE_PERIOD_DEFAULT  = 7 days;     // 604800 sec
uint64 public constant CHALLENGE_PERIOD_EXTENDED = 14 days;    // for δ ≥ 10
```

Rationale (from `pwm_overview1.md` § 6 and the audit memo):

| Reason | Why 7 days specifically |
|---|---|
| **Verifier needs wall-clock time** | Challenge proofs require re-running the solver on the same `ω` instance, downloading dataset CIDs from IPFS (can be slow), running S1-S4 gate checks, and writing a structured proof payload. A few hours is too tight; a few days is comfortable. |
| **Global timezone coverage** | A weekend (~2 days) + a work week (~5 days) gives challengers in any timezone fair access. Shorter windows favour Asia-business-hour challengers; longer windows are wasteful. |
| **Web3 audit-response norm** | Compound, Aave, MakerDAO all use 7-day governance time-locks for similar "audit then act" patterns. PWM follows the convention so contributors don't need a separate mental model. |
| **Bitcoin analogy ≠ applicable** | Bitcoin's 6-confirmation rule (~1 hour) works because validation is *bit-checking* (signatures + UTXO state). PWM validation is *re-execution* — running someone's solver on someone else's data. That's hours of compute per challenge, not seconds. |

**14 days for δ ≥ 10**: high-delta certs (frontier / grand-challenge
benchmarks) demand more verification time because the solvers are
larger, datasets are larger, and the stakes are higher. The protocol
hard-codes the doubled window for `delta ≥ 10` in
`PWMCertificate.challengeWindow(certHash)`.

---

## 2. Why 7 days is right for new benchmarks but overkill for proven ones

The challenge window is a **fraud-detection budget**. The right size
depends on:

- **How well-tested is the L3?** A brand-new L3 with no mining history
  needs the full 7 days for the community to discover edge cases. An
  L3 that has accepted 100+ certs without a successful challenge is
  effectively battle-tested — fraud is much rarer.
- **Dataset retrieval time.** If the L3's dataset is pinned to multiple
  IPFS gateways with redundant peers, retrieval is fast (minutes). If
  it's pinned only to one gateway, retrieval can take hours.
- **Solver complexity.** A LISTA-class deep-learning solver takes
  minutes to run; a frontier `δ=10` solver may take days.
- **Pool size.** A 50-PWM pool isn't worth defrauding; a 500K-PWM
  treasury pool is. Higher stakes deserve more verification time.

Concretely, after CASSI / CACTI have been live on Base mainnet for
12+ months with N successful finalizations and zero upheld
challenges, 7 days is excessive. 3 days would be plenty.

---

## 3. The per-benchmark `challengePeriodSeconds` override

The contract already supports per-benchmark windows via:

```solidity
// In PWMCertificate.sol
function challengeWindow(bytes32 benchmarkHash) public view returns (uint64) {
    uint64 override_ = benchmarkChallengeWindow[benchmarkHash];
    if (override_ > 0) return override_;
    if (delta[benchmarkHash] >= 10) return CHALLENGE_PERIOD_EXTENDED;
    return CHALLENGE_PERIOD_DEFAULT;
}
```

The override is set via `PWMGovernance.setParameter`:

```solidity
PWMGovernance.proposeParameter(
    bytes32 paramKey,        // keccak("benchmark.challengeWindow", benchmarkHash)
    uint256 newValue         // e.g. 259200 = 3 days
);
// 48h time-lock; 3-of-5 founder approval;
// then anyone calls executeParameter() to apply
```

Recommended values per benchmark maturity:

| Benchmark state | Recommended challengePeriodSeconds | Rationale |
|---|---|---|
| **Newly registered** (no finalized certs yet) | **604,800 sec (7 days)** — the default | Full window for community to discover gating bugs |
| **Active** (1-25 finalized certs, 0 challenges upheld) | **604,800 sec (7 days)** | Default still fits; track-record too short to shorten |
| **Proven** (25+ finalized certs, 0 challenges upheld over 12+ months) | **259,200 sec (3 days)** | Track record demonstrates fraud is rare; tighter window cuts miner reward latency 4× |
| **Frontier (δ ≥ 10)** | **1,209,600 sec (14 days)** — hardcoded | Larger solvers, larger datasets, higher stakes |
| **Compromised** (a fraud-upheld challenge in last 30 days) | **1,209,600 sec (14 days)** — promote up | Tighten verification until 30 days clean elapse |

**Implementation status:** the contract supports this. The recommended
state-machine-driven adjustment (auto-promote / demote based on cert
counts and challenge outcomes) is **not implemented** — would require
an additional governance action per benchmark state change. For now
the multisig manually tunes proven benchmarks.

---

## 4. The L1/L2/L3 testnet → mainnet flow (already works this way)

L1, L2, L3 already follow exactly the staging the Director described.
The model is the **`registration_tier` ladder**:

```
                    Tier 3 (stub)              Tier 2 (community)         Tier 1 (founder_vetted)
                    ──────────────             ────────────────────       ─────────────────────────
                                                                          
Status              JSON in repo,              Registered on Sepolia,     Registered on Base mainnet,
                    not on-chain               testnet pool funded         mainnet pool funded
                    
Mineable?           ✗ No                       ✓ Yes (testnet PWM)        ✓ Yes (mainnet PWM)
                    
Edit cost           Free (just edit JSON)      Hash-locked on Sepolia;    Hash-locked on Base; v-bump
                                               v-bump for body changes    for body changes (high cost)
                                               (low cost — fake PWM)      (real PWM)
                    
Promotion gate      Verifier-agent triple      Multisig sign on Base
                    review on PR; multisig     mainnet after Sepolia
                    sign on Sepolia            track record proves it
                    
Examples            ~531 cataloged stubs       (none today — post-launch  CASSI L1-003, L2-003, L3-003
                    (e.g. SPC L1-026b)         path)                       CACTI L1-004, L2-004, L3-004
                                                                          (Sepolia for weeks → mainnet)
```

**Each ascent is a multisig event.** The contract enforces:

- `PWMRegistry.register()` is multisig-gated (3-of-5 founders signing
  via `PWMGovernance`).
- Each ascent (Tier 3 → 2 → 1) re-runs the S1-S4 gate suite plus
  verifier-agent triple-review.
- Sepolia and Base mainnet have **different** `PWMRegistry` deployments
  (per `addresses.json`), so an L1 registered on Sepolia is a
  *different on-chain artifact* from the same L1 registered on Base
  mainnet. The keccak256 of the manifest is the same on both chains
  (the canonical hash is chain-agnostic), but the `(chain_id,
  registry_address, hash)` triple uniquely identifies an
  *registration*, not just an artifact.

In this model, "available on testnet first, mainnet after verification"
is **already what L1/L2/L3 do today**. CASSI was registered on Sepolia
2026-04-19 and remained Sepolia-only for the testnet phase; Base
mainnet registration is gated by the D9 deploy chain.

The customer guide section "Registration tiers" (in
`PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md`)
documents this. **No structural change is recommended for L1/L2/L3.**

---

## 5. Why L4 cannot follow the same testnet → mainnet flow

L4 certs are structurally different from L1/L2/L3:

| Property | L1/L2/L3 | L4 |
|---|---|---|
| Frequency | One-time event per artifact (CASSI L1 was registered ONCE) | High-frequency event (a popular L3 sees thousands of L4 certs over its lifetime) |
| Authoring | A small group authors a manifest carefully | Any miner submits a cert any time |
| Promotion gate | Multisig + verifier-agent triple-review | Free for anyone with a wallet (the protocol's whole point) |
| Reward timing | One-time grant + ongoing royalty | Per-cert, after challenge window clean |
| Cross-chain unification | Same canonical hash; identity preserved | Each cert has its own hash; testnet and mainnet certs are independent events |

**A mandatory L4 testnet → mainnet promotion would break four things:**

1. **Reward economics.** Mainnet pool sits idle for the duration of
   the testnet → mainnet delay (7+ days). Per-epoch minting rolls
   over, but miners get paid 7+ days late. For a high-frequency
   benchmark with daily certs, this means 7+ days of mainnet liquidity
   evaporated per cert. Multiply across 50 certs/year → permanent ~14%
   capital lockup.

2. **Doubled miner cost.** Submit cert to testnet (gas + stake),
   wait, re-submit to mainnet (gas + stake again). For a `Q_int=70`
   rank-1 cert paying ~110 PWM, the additional gas would erode 5-15%
   of net reward depending on chain congestion.

3. **Different fraud surface.** A miner who submits a fraudulent cert
   on testnet (no real money at stake) and waits for the 7-day window
   to elapse (no challenger bothered) could then auto-promote to
   mainnet — converting a free-tier safe-bet into a real-money win.
   The current model forces fraud risk to live on the chain where the
   real stake is.

4. **Independence is a feature, not a bug.** Some legitimate miners
   submit ONLY to testnet (researchers iterating without spending
   real PWM); some submit ONLY to mainnet (production-grade solvers
   with mature test records elsewhere). Forcing the testnet → mainnet
   path would coerce both groups into a model that suits neither.

**The current L4 model already supports the spirit of the proposal:**
- Anyone can submit the *same* solver on the *same* `(benchmark_hash,
  ω_instance)` to BOTH chains. The certs are independent — different
  hashes, different challenge windows, different rewards.
- Sepolia certs are effectively a "dry-run" — they probe whether a
  solver beats the published baselines without spending real PWM.
- Once a Sepolia cert finalizes (7 days clean), the miner has *evidence*
  that the cert would survive on mainnet too; they can choose to submit
  to mainnet immediately or skip.
- The challenge window on mainnet is independently shortened/lengthened
  per benchmark via § 3 above.

**No structural change recommended for L4.** The per-benchmark
`challengePeriodSeconds` override is the right knob — exposed and
documented, but not by default short.

---

## 6. The full updated picture

Combining the recommendations:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PWM DEPLOYMENT MODEL (post-2026-05-08 governance update)                  │
└─────────────────────────────────────────────────────────────────────────────┘

L1 / L2 / L3 Principle / Spec / Benchmark
─────────────────────────────────────────────
  registration_tier:         Tier 3 (stub)  →  Tier 2 (community_proposed)  →  Tier 1 (founder_vetted)
  chain:                     none           →  Sepolia                       →  Base mainnet
  promotion gate:            JSON edit free →  Multisig + S1-S4 + 3 verifier-agent ACCEPT  →  Multisig + Sepolia track record
  pool funded:               no             →  Sepolia testnet PWM           →  Base mainnet PWM (capped per maxBenchmarkPoolWei)
  edit cost (post-promote):  free           →  v-bump (testnet PWM, low)     →  v-bump (real PWM, high)
  
  (No change recommended — already works as designed.)


L4 Solution (cert)
─────────────────────────────────────────────
  Anyone with a funded wallet on Sepolia or Base mainnet submits a cert against any registered L3.
  
  The challenge window applies on whichever chain the cert lives:
  
  ┌──────────────────────────────┬────────────────────┬────────────────────┐
  │ Benchmark state              │ Sepolia window     │ Base mainnet window │
  ├──────────────────────────────┼────────────────────┼────────────────────┤
  │ Newly registered             │  7 days (default)  │  7 days (default)  │
  │ Active (≤ 25 finalized)      │  7 days            │  7 days            │
  │ Proven (≥ 25 finalized,      │  3 days (override) │  3 days (override) │
  │   12+ months, 0 upheld)      │                    │                    │
  │ Frontier (δ ≥ 10)            │ 14 days (hardcode) │ 14 days (hardcode) │
  │ Compromised (recent fraud)   │ 14 days (override) │ 14 days (override) │
  └──────────────────────────────┴────────────────────┴────────────────────┘
  
  Multisig sets the override per benchmark via PWMGovernance.setParameter.
  No mandatory testnet → mainnet promotion (would break the four properties in § 5).
```

---

## 7. Open decisions for Director

Before any of this turns into governance actions:

| Decision | Default recommendation | When to revisit |
|---|---|---|
| **D1.** Adopt the per-benchmark `challengePeriodSeconds` override convention as documented? | **Yes — document only for now**, no governance action until a benchmark hits the "proven" criterion (post-mainnet, ≥ 12 months, ≥ 25 finalized certs) | Annually, or after the first benchmark crosses the 25-cert milestone |
| **D2.** Codify the auto-promote / demote state machine (cert counts → window adjustment) as a governance proposal? | **No — leave as manual tuning** until at least 5 distinct benchmarks have lived through the lifecycle | After 5+ benchmarks have data |
| **D3.** Add a "force testnet → mainnet" flag for L4 certs anyway, as an opt-in? | **No** — the four-property breakage in § 5 outweighs the benefit. Miners who want this can already do it manually (submit to Sepolia first, wait, then submit to Base mainnet). | If contributor friction surfaces a real demand |
| **D4.** Document the L1/L2/L3 testnet → mainnet flow more prominently in the main customer guide? | **Yes** — extend `PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md` § "Registration tiers" with a "Sepolia testnet phase / Base mainnet phase" sub-section. | Now |
| **D5.** Document the per-benchmark challenge window in `PWM_BUG_FIX_PLAYBOOK_2026-05-08.md` § 5? | **Yes** — extend § 5 with the matrix from § 3. | Now |

D4 + D5 are pure-doc edits and can ship today. D1 needs a governance
proposal but the contract already supports it. D2 + D3 stay as
considered-but-not-acted decisions for the lifecycle log.

---

## Cross-references

**Source documents:**

- `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md`
  § "Registration tiers" (the Tier 3 → 2 → 1 ladder) + § "What network for what action"
- `pwm-team/customer_guide/PWM_BUG_FIX_PLAYBOOK_2026-05-08.md`
  § 5 (governance-controlled parameters; will be extended with the per-benchmark window matrix)
- `papers/Proof-of-Solution/pwm_overview1.md` § 6
  (L4 lifecycle — submit / challenge / finalize)

**Code references:**

- `pwm-team/infrastructure/agent-contracts/contracts/PWMCertificate.sol`
  — `CHALLENGE_PERIOD_DEFAULT`, `CHALLENGE_PERIOD_EXTENDED`,
  `challengeWindow(benchmarkHash)`, `benchmarkChallengeWindow` mapping
- `pwm-team/infrastructure/agent-contracts/contracts/PWMGovernance.sol`
  — `proposeParameter`, `executeParameter`, 48-hour time-lock
- `pwm-team/infrastructure/agent-contracts/addresses.json`
  — Sepolia testnet vs Base mainnet registry addresses

**Concrete examples:**

- CASSI Sepolia → mainnet path: registered on Sepolia 2026-04-19,
  remained Sepolia-only through the audit + bounty-prep window;
  Base mainnet registration gated by D9 of the deploy chain
  (`pwm-team/coordination/DIRECTOR_RUNBOOK_D1_TO_D10_2026-05-01.md`)
- L1-026b SPC Tier 3: cataloged but not on-chain; demonstrates
  the "edit cost is free at Tier 3" property (we corrected the
  `int.temporal → int.spatial` bug at zero on-chain cost)
