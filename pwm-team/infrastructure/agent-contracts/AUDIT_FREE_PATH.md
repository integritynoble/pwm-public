# PWM Contract Audit — Zero-Cost Path

**Status:** proposal (director to approve)
**Last updated:** 2026-04-21
**Alternative to:** $80K–$130K paid contest audit via Code4rena + Sherlock
(see `AUDIT_SUBMISSION.md` §10 for the paid path; this document is
about reaching the same safety threshold at $0 upfront cost).

## Goal

Reach mainnet-ready confidence on the 7 PWM contracts (832 nSLOC)
without spending upfront budget on a paid audit. Tradeoffs accepted:
slower timeline (3–6 weeks vs 1–2 weeks for a paid contest), more
director effort, and a wider residual-risk envelope that we offset by
capping mainnet TVL until a paid audit eventually lands (via a grant,
or once revenue covers the cost).

## Four parallel tracks

Each track is independent — start them all this week and let them run
concurrently. None blocks any other.

### Track A — Automated static + symbolic analysis (this week)

Run four free tools. Each takes ≤ 1 day, output is a triaged finding
list we fix before anything else.

| Tool | Kind | Finds | Command |
|------|------|-------|---------|
| **Slither** | Static analysis | Reentrancy, uninitialized storage, missing modifier, suspicious patterns | `pip install slither-analyzer && slither pwm-team/infrastructure/agent-contracts/contracts/` |
| **Mythril** | Symbolic execution | Integer overflow paths, assertion violations, reachable reverts | `pip install mythril && myth analyze contracts/*.sol` |
| **Echidna** | Property fuzzer | Invariant violations (e.g. "M_emitted never exceeds M_POOL") | `echidna-test test/InvariantHarness.sol` (harness to be written) |
| **Foundry fuzz** | Invariant tests | Same as Echidna, in-repo | `forge test --fuzz-runs 100000` |

**Acceptance criterion for Track A:** zero Slither findings at
`Informational` or above after triage, zero Mythril `High`/`Medium`
findings after triage, Echidna + Foundry run for ≥ 24h continuous with
no invariant breakage.

**Status / next step:** none run yet. Start with Slither — it's a
one-liner and surfaces the most bang-per-second.

### Track B — Ecosystem audit grant application (start this week, multi-week lead time)

The large ecosystem foundations sponsor audits for protocols that
bring users to their chain. Apply to all three — you can pick whichever
funds first; no commitment from us until they offer.

| Foundation | Program | Typical coverage | Apply at |
|------------|---------|------------------|----------|
| **Ethereum Foundation** | Ecosystem Support Program (ESP) | $25K–$200K grants, including audit funding | https://esp.ethereum.foundation/ |
| **Optimism Foundation** | Retro-Funding rounds (ongoing) | Open-source public goods including audit grants | https://optimism.io/retropgf |
| **Arbitrum Foundation** | Domain-specific grants | Project-specific, includes audits | https://arbitrum.foundation/grants |

**What to include in each application:** our mission (decentralized
physics research incentivization), on-chain activity to date (links to
the Sepolia tx history — registrations, 100-cert ecosystem run, slash
proxy), the `AUDIT_SUBMISSION.md` package, and a concrete ask
(e.g. $60K audit grant or equivalent sponsored contest slot).

**Acceptance criterion for Track B:** one grant accepted, OR all three
declined (then we know this track is closed and we rely on A + C + D).

**Status / next step:** application drafts not yet written. Can draft
all three in one ~1-hour session.

### Track C — Immunefi bug bounty (launch with the mainnet deploy)

Immunefi is a pay-on-findings marketplace — zero upfront cost.
Researchers submit findings; we pay scaled to funds-at-risk.

**Standard scale**:
- Critical (funds-at-risk): 10% of TVL, capped at $XYZ
- High: $10K–$50K
- Medium: $1K–$10K
- Low: $500–$2K

Since we control TVL at launch (see Track D), the bug-bounty max payout
is tiny early and grows as TVL grows.

**Acceptance criterion for Track C:** Immunefi page published before
mainnet deploy; payout scale written against current TVL; response
plan (who triages in < 24h) documented.

**Status / next step:** draft an Immunefi submission. Standard form at
https://immunefi.com/new-bug-bounty/ .

### Track D — TVL-capped mainnet launch (gates the whole thing)

The bridge between "not-yet-audited" and "live" is a **TVL cap**:
explicit contract-level limits on how much value can be stuck if
something's wrong. Start tiny and raise as confidence builds.

| Milestone | Gate | TVL cap |
|-----------|------|---------|
| Mainnet deploy day 0 | Tracks A + C done | $10K total across all pools |
| Mainnet + 30 days, no incidents | A + C + any new findings remediated | $100K |
| Paid audit completed (grant or revenue-funded) | Track B delivered OR team pays | $1M |
| 6 months post-audit, no critical incident | — | uncapped |

**Implementation:** a `pool` cap per benchmark and a `stakeAmount`
ceiling — both governance-settable. Concretely: before mainnet deploy,
add `maxBenchmarkPoolWei` to `PWMReward` (governance-configurable) and
`maxTotalStakeWei` to `PWMStaking`. Each function that grows these
balances checks the cap.

**Acceptance criterion for Track D:** caps implemented + tested +
documented as part of the mainnet-deploy script. Caps set to $10K at
deploy.

**Status / next step:** two new state vars + two require() checks +
governance setter functions. Maybe 4 hours' work plus tests.

## Week-by-week

**Week 1 (this week)**
- Run Slither, Mythril on current contracts (≤ 1 day)
- Triage findings, open issues, fix highest-severity first
- Write Echidna / Foundry invariant harnesses for the two High-complexity
  contracts (PWMMinting, PWMReward). Ship one invariant per critical
  property:
  - `M_emitted ≤ M_POOL` always
  - Sum of six payout buckets equals drawAmt exactly
  - `settled[certHash]` is set before any external call
- Draft the three ecosystem-grant applications
- Draft the Immunefi submission

**Week 2**
- Implement `maxBenchmarkPoolWei` + `maxTotalStakeWei` caps in
  PWMReward and PWMStaking respectively; tests
- Fix all Week-1 tool findings
- Run Echidna + Foundry fuzz for 24h+ on the fixed code
- Submit ecosystem-grant applications (the lead time is weeks, start now)

**Week 3**
- Second-pass fixes from Echidna/Foundry findings
- Tag `mainnet-v1-rc1` on the commit that passes all of Track A
- Dry-run the mainnet deploy script on a forked-mainnet Foundry test
- Publish Immunefi page (activation-contingent on mainnet deploy)

**Week 4 (deploy day, soft launch)**
- Mainnet deploy with $10K TVL cap
- Activate Immunefi page
- Announce a "canary period" on Twitter / Discord — the first 30 days
  are explicitly a wider-bounty period (2x Immunefi rates for criticals
  found in this window)

**Weeks 5–8**
- Monitor. If any critical is found, pause, remediate, re-deploy.
- If grant lands: full audit contest begins.
- If 30 days pass cleanly: raise TVL cap to $100K.

## Not free — stuff we still need to pay for

- Mainnet deploy gas. Expect 0.1–0.3 ETH in gas to deploy 7 contracts.
  Unavoidable for any mainnet launch, paid audit or not.
- Immunefi listing fee: zero upfront; Immunefi takes a % of payouts
  only. (Sanity-check at sign-up; current terms may have changed.)
- Any critical bounty payouts. These are by definition pay-on-findings
  — the first big finding will cost real money. But it's cheaper
  than a stolen TVL.

## Honest limitations vs a paid audit

- A $50K Code4rena contest produces ~20–50 wardens reading the code in
  a focused week. Tracks A + C do not replace that density of human
  attention — they complement it.
- Invariant fuzzing finds implementation bugs but not *design* bugs. A
  paid auditor will catch "this economic model is exploitable" issues
  that Echidna cannot.
- Residual risk is what the TVL cap is for. Don't remove the cap until
  the paid audit lands.

## Success criteria for this plan

- Zero `High`/`Critical` findings at mainnet deploy (from Tracks A + C)
- TVL cap enforced on-chain (Track D)
- Immunefi live on deploy day (Track C)
- At least one grant application in flight (Track B)
- A written remediation playbook for when critical findings land

## Open questions for the director

1. **Budget confirmation**: are we genuinely zero-budget, or is there a
   small (~$5K–$10K) floor we could spend on, e.g., a one-firm
   fixed-fee review of PWMMinting + PWMReward only (the two
   high-complexity contracts, ~355 nSLOC combined)? A focused
   two-contract audit is often $15K–$25K and would materially reduce
   residual risk.
2. **TVL cap starting value**: $10K feels right as a soft cap. Does the
   director want it lower ($1K) or higher ($50K)? Tradeoff is
   early-user friction vs. blast radius.
3. **Canary-period doubled bounty**: OK to offer 2x rates for the first
   30 days post-deploy? Costs nothing until a finding lands.
