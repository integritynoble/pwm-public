# Immunefi Bug Bounty Submission — PWM Smart Contracts

**Prepared by:** agent-coord (Server 2)
**Date:** 2026-04-21
**Submission portal:** https://immunefi.com/new-bug-bounty/

This document is a ready-to-paste fill for the Immunefi bug-bounty listing
form. Director reviews, fills the bracketed contact/TVL fields, and submits
via the Immunefi portal.

---

## Basics

| Field | Value |
|-------|-------|
| Project name | Physics World Model (PWM) |
| Project type | Protocol (Smart Contracts) |
| Ecosystem | Ethereum (Sepolia testnet today; L2 mainnet in weeks) |
| Category | Scientific contribution / Public goods / Protocol infrastructure |
| Website | https://pwm-explorer.fly.dev/ |
| Alt site | https://pwm-explorer-dsag.onrender.com |
| Repo | https://github.com/integritynoble/pwm (private; read access on request) |
| Launch status | **Testnet live, mainnet in Q3 2026** |
| Active from | Mainnet deploy day (TBD) |
| Max payout (USD) | Starts at $10,000; scales with TVL (see Scale table) |

---

## Project description

Physics World Model (PWM) is a 7-contract Solidity protocol that turns
verifiable scientific contribution into on-chain rewards. A researcher
registers a four-layer artifact hierarchy — **Principle (L1) → Spec
(L2) → Benchmark (L3) → Solution (L4)** — and earns from per-benchmark
reward pools when verified solutions are submitted. Certificates go
through a 7- or 14-day challenge window, settle via a six-way ranked-draw
distribution, and unclaimed ranks roll over into the next epoch's pool.

The contracts are immutable (no proxies, no admin-controlled upgrades),
use only native ETH for staking (no external ERC20), and depend on **zero
external libraries** (no OpenZeppelin, no Chainlink, no oracles). The
surface area is **~867 nSLOC across 7 contracts** (audit-v2, includes
pre-mainnet TVL caps); full scope is in
`pwm-team/infrastructure/agent-contracts/AUDIT_SUBMISSION.md` in the
repo.

## Assets in scope

All 7 contracts at the pinned commit `348ec2d6dc4dda1f6618f83b60f6d6d6f6a1eed9` (tag `audit-v2`):

| Contract | Address (mainnet, TBD at deploy) | nSLOC | Complexity |
|----------|-----------------------------------|-------|------------|
| `PWMRegistry` | TBD | 52 | Low |
| `PWMGovernance` | TBD | 100 | Medium |
| `PWMMinting` | TBD | 210 | **High** |
| `PWMCertificate` | TBD | 155 | Medium |
| `PWMReward` | TBD | ~160 | **High** |
| `PWMStaking` | TBD | ~135 | Medium |
| `PWMTreasury` | TBD | 55 | Low |

**Out of scope:**
- Off-chain code (CLI, miner, web explorer, indexer)
- IPFS / pinning services
- Frontend HTML/CSS/JS
- Known design decisions documented in `AUDIT_SUBMISSION.md` §3

## Impacts in scope

### Critical
- Direct theft of any user funds (stakes, reward-pool balances, treasury)
- Emission beyond `M_POOL` (17,220,000 × 10^18) cap in `PWMMinting`
- Permanent freezing of user funds (stakes that can never be recovered)
- Double-settlement of a certificate paying out > 100% of the benchmark pool
- Access-control bypass allowing a non-governance address to call `onlyGovernance` functions (`setStakeAmount`, `slashForFraud`, `graduate`, `resolveChallenge`, DAO activation)

### High
- Incorrect reward distribution math (wrong recipient gets paid, or
  the six-way split does not sum to `drawAmt` up to the dust-tolerance
  already documented)
- Reentrancy allowing extraction of funds beyond the intended amount
- Challenge / finalization logic allowing an invalid certificate to settle
- Incorrect slash payouts (wrong address credited, wrong percentage burned)
- Weight-bookkeeping corruption in `PWMMinting` causing incorrect future emissions

### Medium
- Denial-of-service blocking certificate finalization permanently
- Stuck funds due to failed ETH transfers to non-payable addresses
- Timestamp-manipulation-based attacks on challenge windows (beyond normal `block.timestamp` tolerance)

### Low / Informational
- Gas optimization opportunities (we accept these as findings but pay Low tier)
- Missing event emissions
- Documentation inaccuracies

## Impacts NOT in scope (pre-disclosed design decisions — see `AUDIT_SUBMISSION.md §3`)

- Constructor sets deployer as initial governance (known; governance is then transferred)
- Division-rounding dust goes to treasury (by design; documented in §3.2)
- No proxy / upgrade pattern (intentional; §3.3)
- `shareRatioP` is submitter-controlled within [1000, 9000] bounds (intentional; §3.4)
- BURN_SINK is `0x…dEaD`, not `address(0)` (known; §3.5)
- Activity uses cumulative count, not 90-day rolling window (known; remediation pre-agreed; §3.6)
- No external dependencies means no ReentrancyGuard (known; §3.7)
- Any founder can cancel any proposal (known design tradeoff; §3.9)

Reports on these will be closed as "out of scope" without payment.

## Rewards

### Payout scale (in USD, paid in ETH or stablecoin)

| Severity | Amount | Cap |
|----------|--------|-----|
| Critical | 10% of funds-at-risk | **Start: $10,000 min / $25,000 max**; scales with TVL |
| High | $5,000 fixed | — |
| Medium | $1,000 fixed | — |
| Low | $500 fixed | — |

**TVL-scaled Critical cap** (updates as TVL grows):

| TVL | Critical cap |
|-----|--------------|
| $0 – $100K | $25,000 |
| $100K – $1M | $100,000 |
| $1M – $10M | $500,000 |
| $10M+ | $1,000,000 |

### Canary-period bonus (first 30 days post mainnet deploy)

**2x payouts** for all Critical and High severity findings during the
first 30 days after mainnet deploy. A finding submitted at Day 5 with
Critical severity and $20K funds-at-risk would pay $4,000 (10% × $20K ×
2). This caps our outward exposure: early enough that TVL is still
small, high enough per-finding to reward researchers who drop everything
to look at PWM in its first month.

## Rules

1. **Proof required.** Reports must include a proof-of-concept demonstrating
   the vulnerability on a Sepolia fork (or current mainnet fork when
   live). We test every submission against the actual contract state.
2. **Responsible disclosure.** Do not disclose publicly until we confirm
   remediation.
3. **Duplicate handling.** First valid submission of a given root cause
   gets full payout; near-duplicates get 25% at our discretion.
4. **Out-of-scope rejections are final.** See §"Impacts NOT in scope" above.
5. **Sybil / spam filtering.** Low-effort submissions (linter-tier reports
   pasted from Slither output with no triage) will be closed without
   payment.
6. **Triage SLA.** Initial response within **48 hours**; finding classification within **7 days**; remediation within **14–30 days** depending on severity.

## Response plan

| Severity | Who triages | Within | Action |
|----------|-------------|--------|--------|
| Critical | [director + primary dev] | 24 hours | Immediately deploy `pause()` on affected contract if available; otherwise isolate via governance proposal; confirm fix; ship patched redeploy |
| High | [director + primary dev] | 48 hours | Evaluate exploitability; patch in next deploy window |
| Medium | [director + primary dev] | 7 days | Patch in normal release cadence |
| Low | [primary dev] | 14 days | Patch in normal release cadence |

## Contact information

| Purpose | Contact |
|---------|---------|
| Security issues | [director email — TBD fill in] |
| Operational issues | [director email — TBD fill in] |
| General inquiries | [director email — TBD fill in] |
| GitHub | https://github.com/integritynoble/pwm |

## Additional assets for researchers

- **Protocol spec:** `papers/Proof-of-Solution/pwm_overview1.md` (canonical)
- **Audit submission package:** `pwm-team/infrastructure/agent-contracts/AUDIT_SUBMISSION.md`
- **Test suite:** `pwm-team/infrastructure/agent-contracts/test/` (53 tests, 1 integration test covering full 7-contract lifecycle)
- **Sepolia testnet deployment** live now — researchers can exercise the full flow without mainnet funds. Contract addresses in `pwm-team/coordination/agent-coord/interfaces/addresses.json`.
- **Slither report:** run `slither contracts/` yourself; our own triage is tracked in the repo

---

## Director-submission checklist

- [ ] Replace all `[director email — TBD fill in]` placeholders
- [ ] Replace contract addresses TBD entries with mainnet addresses (after L2 mainnet deploy)
- [ ] Confirm Immunefi fee structure at sign-up (% of payouts) and document here
- [ ] Decide if the canary-bonus 2x is offered publicly or just in private researcher briefs
- [ ] Track submission date in `pwm-team/coordination/agent-coord/progress.md` under `IMMUNEFI_LIVE` signal

---

## Suggested launch sequence

1. Submit Immunefi form the **same day** you deploy to L2 mainnet (not before — Immunefi requires live contracts)
2. Tweet / announce on deploy day with the Immunefi link
3. Post to r/ethsecurity and Secureum Discord the next day
4. Run the canary period for 30 days; monitor daily
5. At Day 30, if no Criticals found: raise TVL cap, lower canary bonus back to 1x, and transition to standard operations
