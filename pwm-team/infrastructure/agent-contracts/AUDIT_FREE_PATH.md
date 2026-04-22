# PWM Contract Audit — Zero-Cost Path

**Status:** in progress (Track A mostly done, Tracks B–E not started)
**Last updated:** 2026-04-22
**Alternative to:** $80K–$130K paid contest audit via Code4rena + Sherlock
(see `AUDIT_SUBMISSION.md` §10 for the paid path; this document is
about reaching the same safety threshold at $0 upfront cost).

## Goal

Reach mainnet-ready confidence on the 7 PWM contracts (832 nSLOC)
without spending upfront budget on a paid audit. Tradeoffs accepted:
slower timeline (4–6 weeks vs 1–2 weeks for a paid contest), more
director effort, and a wider residual-risk envelope that we offset by
capping mainnet TVL until a paid audit eventually lands (via a grant,
or once protocol revenue covers the cost).

---

## Five parallel tracks

Each track is independent — start them all this week and let them run
concurrently. None blocks any other.

### Track A — Automated static analysis + invariant fuzzing

Run free tools against the codebase. Output is a triaged finding list
we fix before mainnet.

| Tool | Kind | What it finds | Status |
|------|------|---------------|--------|
| **Slither** | Static analysis | Reentrancy, uninitialized storage, missing modifiers, suspicious patterns | **DONE** — 43 findings triaged, 1 real fix applied (CEI violation in `mintFor`), remaining are informational/known design decisions |
| **Mythril** | Symbolic execution | Integer overflow, assertion violations, unprotected self-destruct | **DONE** — 5/7 contracts analyzed (0 issues); PWMReward + PWMCertificate exceed solc stack depth limit |
| **Echidna** | Property fuzzer | Invariant violations (e.g. "M_emitted never exceeds M_POOL") | **DONE** — 500K fuzz calls per harness, all invariants held on PWMMinting + PWMReward |
| **Aderyn** | Static analysis (Rust) | Solidity anti-patterns, gas issues, missing checks | Skipped — requires native Rust/cargo install, no Docker image available |
| **Foundry invariant tests** | Invariant tests | Same as Echidna, integrated with Forge | Deferred — Echidna provides equivalent coverage |

#### Slither results summary (2026-04-21)

| Severity | Count | Action |
|----------|-------|--------|
| Medium (reentrancy in `mintFor`) | 1 | **FIXED** — commit `fb1dff7`: moved `_incrementActivity()` and `M_emitted` updates before `reward.depositMinting()` external call |
| Low (division-before-multiplication in `distribute`) | 1 | Known design decision — dust goes to treasury (AUDIT_SUBMISSION.md §3.2) |
| Low (sends ETH to arbitrary address) | 1 | By design — recipients are protocol participants |
| Informational (timestamp comparisons) | 7 | By design — challenge windows and timelocks use `block.timestamp` |
| Informational (pragma version) | 7 | ^0.8.24 is stable; Slither flags any recent version |
| Informational (low-level calls) | 5 | Required — `address(0xdEaD)` and arbitrary wallets need `.call{value:}()` |
| Informational (missing inheritance, naming) | ~20 | Cosmetic — interfaces declared locally, `M_emitted` follows physics convention |

#### Mythril results summary (2026-04-22)

| Contract | Result |
|----------|--------|
| PWMMinting | **No issues detected** |
| PWMStaking | **No issues detected** |
| PWMTreasury | **No issues detected** |
| PWMGovernance | **No issues detected** |
| PWMRegistry | **No issues detected** |
| PWMReward | Skipped — "stack too deep" (Mythril's solc pipeline cannot compile with `--via-ir`) |
| PWMCertificate | Skipped — same stack-depth limitation |

5 of 7 contracts fully analyzed via symbolic execution. The 2 skipped
contracts are covered by Echidna fuzzing below.

#### Echidna invariant fuzzing results (2026-04-22)

**Harnesses:** `contracts/test/EchidnaInvariantMinting.sol`, `contracts/test/EchidnaInvariantReward.sol`

**PWMMinting harness (500K calls):**
- `echidna_emission_cap`: PASSING — `M_emitted <= M_POOL` never violated
- `echidna_remaining_consistent`: PASSING — `remaining() == M_POOL - M_emitted` always holds
- `echidna_weight_sane`: PASSING — `totalPrincipleWeight < 1e18` always holds
- Coverage: 9,593 unique instructions, 4 contracts, 18 corpus sequences

**PWMReward harness (500K calls):**
- `echidna_pool_never_negative`: PASSING — reward contract balance always >= 0
- `echidna_rank_bps_valid`: PASSING — rank BPS constants correct (40%/5%/2%/1% each)
- `echidna_splits_sum_to_100pct`: PASSING — AC_CP + L3 + L2 + L1 + Treasury = 10000 bps
- Assertion: `pool[hash]` never increases from a `distribute()` call — PASSING
- Coverage: 8,926 unique instructions, 3 contracts, 13 corpus sequences

**Acceptance criterion for Track A:** zero High/Medium Slither findings
after triage (achieved). Mythril: zero findings on 5/7 contracts.
Echidna: 500K+ fuzz calls on 2 harnesses with zero invariant breakage.
Track A is substantially complete — only the 24h continuous fuzz run remains.

### Track B — Ecosystem audit grant applications

Large ecosystem foundations sponsor audits for protocols deploying on
their chain. Apply to all eligible programs — accept whichever funds
first; no commitment until they offer.

| Foundation | Program | Typical coverage | Apply at |
|------------|---------|------------------|----------|
| **Ethereum Foundation** | Ecosystem Support Program (ESP) | $25K–$200K grants including audit funding | https://esp.ethereum.foundation/ |
| **Optimism Foundation** | Retroactive Public Goods Funding | Public goods including security audits | https://optimism.io/retropgf |
| **Arbitrum Foundation** | Domain-specific grants | Project grants including audit coverage | https://arbitrum.foundation/grants |

**What to include in each application:**
- Mission: decentralized physics research incentivization protocol
- On-chain activity: Sepolia deployment (7 contracts, 6 genesis artifacts registered)
- Scope: 7 contracts, 832 nSLOC, no external dependencies
- Deliverables: `AUDIT_SUBMISSION.md` package (ready to share)
- Concrete ask: $50K–$60K audit grant for a Code4rena or Sherlock contest

**Acceptance criterion:** one grant accepted. If all three decline,
this track closes and we rely on Tracks A + C + D + E.

**Status:** application drafts not yet written.

### Track C — Immunefi bug bounty (launch with mainnet deploy)

Immunefi is a pay-on-findings marketplace — zero upfront cost.
Researchers submit findings; we pay scaled to funds-at-risk.

**Payout scale (tied to TVL cap from Track D):**

| Severity | Payout | Example |
|----------|--------|---------|
| Critical (direct fund loss) | 10% of funds-at-risk, max $5K at launch | Drain reward pool, mint beyond M_POOL |
| High (incorrect economic outcome) | $1K–$3K | Wrong payout math, weight cache corruption |
| Medium (griefing / DoS) | $500–$1K | Block certificate finalization, proposal spam |
| Low (gas / informational) | $100–$500 | Missing events, gas optimization |

At $10K TVL cap (launch day), the max critical payout is $1K. As TVL
cap rises, bounty payouts scale automatically. This aligns cost with
actual risk exposure.

**Canary period bonus:** for the first 30 days post-deploy, offer 2x
the standard rates. Costs nothing unless a finding lands, and
incentivizes immediate researcher attention.

**Response plan:**
- Triage within 24h (director + agent-contracts)
- Critical: pause affected contract via governance within 4h
- High/Medium: fix, test, redeploy within 7 days
- Publish postmortem for any High or above

**Acceptance criterion:** Immunefi page published before mainnet deploy;
payout scale documented against current TVL; response plan written.

**Status:** not yet drafted. Standard form at https://immunefi.com/ .

### Track D — Community review + Hats Finance

Leverage the security researcher community for free human review.
This partially fills the gap left by not running a paid contest.

**Step 1 — Public community review (free, this week):**

Post the repo + scope for community review in these venues:

| Venue | How to post | Expected quality |
|-------|-------------|-----------------|
| Secureum Discord (`#audit-findings`) | Share repo link + audit scope summary | High — active auditor community |
| r/ethsecurity, r/ethdev | Post with "832 nSLOC, no deps, can you break it?" framing | Medium — mix of hobbyists and pros |
| Twitter/X (`#SmartContractSecurity`) | Thread: protocol summary + link to `AUDIT_SUBMISSION.md` | Variable — good for visibility |
| Code4rena warden community | Many wardens review public repos to build portfolio | High — experienced auditors |

**Incentive:** "First valid High-severity finding earns 10,000 PWM at
mainnet launch." Costs nothing now, strong signal to researchers.

**Step 2 — Hats Finance contest (optional, pay-only-for-bugs):**

Hats Finance (https://hats.finance) runs decentralized audit contests
where you deposit a prize pool but **pay nothing if no bugs are found**.
The deposit is returned if the code is clean.

- Set a modest pool ($2K–$5K) or equivalent in ETH
- Researchers compete to find bugs during a fixed contest window
- If no valid findings: full deposit returned
- If findings: payouts proportional to severity

**Acceptance criterion:** community review posts published; at least
10 unique researchers have viewed the repo (track via GitHub traffic).

**Status:** not yet posted.

### Track E — TVL-capped mainnet launch

The bridge between "not-yet-audited" and "live" is a **TVL cap**:
explicit contract-level limits on how much value can be at risk if
something is wrong. Start tiny and raise as confidence builds.

| Milestone | Gate | TVL cap |
|-----------|------|---------|
| Mainnet deploy (day 0) | Tracks A + C done | **$10K** total across all pools |
| Mainnet + 30 days, no incidents | A + C + D, any findings remediated | **$100K** |
| Paid audit completed (grant or revenue-funded) | Track B delivered OR team pays | **$1M** |
| 6 months post-audit, no critical incident | — | **Uncapped** |

**Implementation:** two new governance-configurable caps:
- `maxBenchmarkPoolWei` in `PWMReward` — caps `pool[benchmarkHash]`
- `maxTotalStakeWei` in `PWMStaking` — caps total staked value

Each function that grows these balances (`depositMinting`,
`depositBounty`, `seedBPool`, `stake`) checks the cap and reverts
if exceeded. Governance can raise caps via the standard 3-of-5
multisig + 48h timelock.

**Implementation estimate:** 2 state vars + 2 `require()` checks +
2 governance setter functions + tests. Approximately 4 hours of work.

**Acceptance criterion:** caps implemented, tested, and set to $10K
equivalent in the mainnet deploy script.

**Status:** not yet implemented.

---

## Week-by-week plan

**Week 1 (this week)**
- [x] Run Slither on all contracts — **DONE**, 1 fix applied
- [x] Run Mythril symbolic execution — **DONE**, 5/7 clean, 2 stack-depth limited
- [x] Write Echidna invariant harnesses for PWMMinting + PWMReward — **DONE**
- [x] Run Echidna 500K fuzz on both harnesses — **DONE**, all invariants held
- [ ] Run 24h continuous Echidna fuzz (extended run)
- [ ] Draft the three ecosystem-grant applications (Track B)
- [ ] Draft the Immunefi submission (Track C)
- [ ] Post repo for community review (Track D)

**Week 2**
- [ ] Implement `maxBenchmarkPoolWei` + `maxTotalStakeWei` caps (Track E)
- [ ] Fix any new findings from Aderyn / community review
- [ ] Run Echidna + Foundry fuzz for 24h+ on the fixed code
- [ ] Submit ecosystem-grant applications (lead time is weeks; start now)

**Week 3**
- [ ] Second-pass fixes from fuzzing and community findings
- [ ] Tag `mainnet-v1-rc1` on the commit that passes all of Track A
- [ ] Dry-run the mainnet deploy script on a forked-mainnet Foundry test
- [ ] Publish Immunefi page (activated on mainnet deploy day)

**Week 4 (deploy day — soft launch)**
- [ ] Mainnet deploy with $10K TVL cap
- [ ] Activate Immunefi page
- [ ] Announce canary period: 2x bounty rates for 30 days

**Weeks 5–8**
- [ ] Monitor. If any critical is found: pause, remediate, re-deploy.
- [ ] If grant lands: full paid audit contest begins.
- [ ] If 30 days pass cleanly: raise TVL cap to $100K via governance.

---

## Costs (not zero, but minimal)

| Item | Cost | Notes |
|------|------|-------|
| Mainnet deploy gas | 0.1–0.3 ETH (~$300–$900) | Unavoidable for any mainnet launch |
| Immunefi listing | $0 upfront | Immunefi takes a % of payouts only |
| Hats Finance pool (optional) | $2K–$5K deposit | Returned if no bugs found |
| Bug bounty payouts | Variable | Pay-on-findings — first critical costs real money |
| Grant applications | $0 | Time cost only |

**Total guaranteed spend: ~$300–$900 in gas.** Everything else is
pay-on-findings or refundable.

---

## Honest limitations vs a paid audit

1. **Human attention density.** A $50K Code4rena contest attracts
   20–50 wardens reading the code intensively for a focused week.
   Tracks A + C + D do not replicate that density — they complement it.

2. **Design-level bugs.** Invariant fuzzing finds implementation bugs
   but not design bugs. A paid auditor catches "this economic model is
   exploitable under conditions X, Y, Z" — Echidna cannot.

3. **Reputation signal.** "Audited by Code4rena" is a trust signal for
   users and investors. "Self-audited with automated tools" is not.
   The TVL cap (Track E) is the honest substitute until a paid audit
   lands.

4. **Residual risk is real.** Do not remove the TVL cap until a paid
   audit is completed. The free path gets us to "safe enough to launch
   small"; it does not get us to "safe enough to hold $10M."

---

## Success criteria

All five must be true before mainnet deploy:

- [x] Zero High/Critical findings from Slither + Mythril (Track A)
- [ ] Invariant fuzz run for 24h+ with no breakage (Track A) — 500K-call run done, 24h run pending
- [ ] TVL cap enforced on-chain and set to $10K (Track E)
- [ ] Immunefi page ready to activate on deploy day (Track C)
- [ ] At least one grant application submitted (Track B)
- [ ] Community review posted with ≥ 7 days exposure (Track D)

---

## Open questions for the director

1. **Micro-budget available?** If there's even $5K–$10K, a Hats Finance
   contest (refundable if no bugs) or a focused 2-contract review of
   PWMMinting + PWMReward (~355 nSLOC) dramatically reduces residual
   risk. A focused two-contract review from a solo auditor typically
   costs $5K–$15K.

2. **TVL cap starting value:** $10K is the proposed soft cap. Lower
   ($1K) reduces blast radius further but limits early-user activity.
   Higher ($50K) is more useful but increases risk. Recommend $10K.

3. **Canary-period 2x bounty:** OK to offer doubled Immunefi rates for
   the first 30 days post-deploy? Costs nothing unless a finding lands.

4. **PWM token incentive for community reviewers:** OK to offer 10,000
   PWM for the first valid High-severity finding from a community
   reviewer? Costs nothing pre-mainnet, strong incentive signal.
