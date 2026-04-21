# PWM Smart Contract Audit Submission Package

**Project:** Physics World Model (PWM)
**Prepared by:** Chengshuai Yang
**Date:** 2026-04-21
**Compiler:** Solidity ^0.8.24
**Framework:** Hardhat
**Network:** Sepolia testnet (chainId 11155111); targeting Ethereum mainnet post-audit
**External dependencies:** None (no OpenZeppelin, no oracles, no proxies)

---

## 1. Submission Form (Code4rena / Sherlock)

### Project Name

Physics World Model (PWM)

### Project Description

Physics World Model (PWM) is a decentralized protocol for incentivized physics research. The protocol establishes a four-layer artifact hierarchy (L1 Principles, L2 Specs, L3 Benchmarks, L4 Solutions) where researchers submit physics solutions against registered benchmarks, undergo a challenge window, and receive payouts from a ranked-draw reward pool funded by Zeno-curve token emission and direct bounties. The system is governed by a 3-of-5 founder multisig with a 48-hour timelock, designed to transition irreversibly to DAO governance. Seven immutable smart contracts (no proxy pattern) handle artifact registration, tiered staking with slashing, per-event minting from a fixed 17.22M token emission pool, certificate lifecycle management with 7/14-day challenge windows, per-benchmark reward pools with six-way payout splits, and per-principle treasury isolation with adversarial bounty caps.

### Repository

- **GitHub:** https://github.com/integritynoble/pwm
- **Contract path:** `pwm-team/infrastructure/agent-contracts/contracts/`
- **Test path:** `pwm-team/infrastructure/agent-contracts/test/`

### How to Build and Test

```bash
cd pwm-team/infrastructure/agent-contracts
npm install
npx hardhat test        # ~54 tests, ~3 seconds
```

### Total nSLOC

**~782 nSLOC** across 7 contracts (1,162 total lines including comments and blanks)

### Scope Table

| # | Contract | File | Total Lines | nSLOC | Complexity | Description |
|---|----------|------|-------------|-------|------------|-------------|
| 1 | PWMRegistry | `PWMRegistry.sol` | 68 | 52 | Low | Immutable append-only L1-L4 artifact hash store with parent-chain validation |
| 2 | PWMGovernance | `PWMGovernance.sol` | 133 | 100 | Medium | 3-of-5 multisig, 48h timelock proposals, irreversible DAO activation switch |
| 3 | PWMMinting | `PWMMinting.sol` | 295 | 210 | High | Zeno-curve per-event emission from 17.22M fixed pool; weighted principle/benchmark allocation with cached totals |
| 4 | PWMCertificate | `PWMCertificate.sol` | 227 | 155 | Medium | L4 certificate submission, 7/14-day challenge window, finalization dispatching to Reward and Minting |
| 5 | PWMReward | `PWMReward.sol` | 202 | 145 | High | Per-benchmark reward pool, ranked-draw settlement (Rank 1-10), six-way payout split with treasury remainder |
| 6 | PWMStaking | `PWMStaking.sol` | 161 | 115 | Medium | Three-tier staking (10/2/1 PWM), graduation 50/50, challenge slash, fraud 100% burn |
| 7 | PWMTreasury | `PWMTreasury.sol` | 76 | 55 | Low | Per-principle treasury T_k, 15% inflow from draws, adversarial bounty payouts capped at 50% |
| | **Totals** | | **1,162** | **~832** | | |

### Complexity Ratings Explained

- **Low:** Straightforward storage + access control; minimal arithmetic
- **Medium:** State machine transitions, multi-party access control, time-dependent logic
- **High:** Multi-step arithmetic with integer division, cached weight bookkeeping, cross-contract fund flows

---

## 2. Architecture Overview

```
PWMGovernance (3-of-5 multisig, 48h timelock)
    |
    +-- PWMRegistry (immutable artifact store, L1->L2->L3->L4 chain)
    |
    +-- PWMStaking (stake per layer: 10/2/1 PWM)
    |       |
    |       +-->  PWMReward.seedBPool() (50% of graduated stake seeds reward pool)
    |
    +-- PWMCertificate (submit -> 7d/14d challenge window -> finalize)
    |       |
    |       +-->  PWMReward.distribute() (ranked-draw settlement)
    |       +-->  PWMMinting.mintFor() (per-event Zeno emission)
    |
    +-- PWMReward (pool per benchmark, 6-way payout split)
    |       |
    |       +-->  PWMTreasury.receive15pct() (15% to principle treasury T_k)
    |
    +-- PWMTreasury (per-principle T_k, adversarial bounty payouts)
```

### Cross-Contract Call Flow (L4 Settlement)

1. User calls `PWMCertificate.submit()` with certificate data
2. After challenge window (7 or 14 days), anyone calls `PWMCertificate.finalize()`
3. `finalize()` calls `PWMMinting.mintFor()` to compute and deposit Zeno emission into benchmark pool
4. `finalize()` calls `PWMReward.distribute()` to settle the ranked draw
5. `distribute()` splits the drawn amount six ways (AC, CP, L1, L2, L3 creators, treasury)
6. `distribute()` calls `PWMTreasury.receive15pct()` to deposit the treasury share

### Key Protocol Parameters

| Parameter | Value | Location |
|-----------|-------|----------|
| M_POOL (total emission cap) | 17,220,000 * 10^18 | PWMMinting |
| Challenge window (standard) | 7 days | PWMCertificate |
| Challenge window (extended, delta >= 10) | 14 days | PWMCertificate |
| Multisig threshold | 3-of-5 | PWMGovernance |
| Timelock | 48 hours | PWMGovernance |
| Rank 1 draw | 40% of pool | PWMReward |
| Rank 2 draw | 5% of pool | PWMReward |
| Rank 3 draw | 2% of pool | PWMReward |
| Ranks 4-10 draw | 1% each of pool | PWMReward |
| Ranks 11+ | 0% (rollover) | PWMReward |
| AC+CP combined share of draw | 55% | PWMReward |
| L3 creator share | 15% | PWMReward |
| L2 creator share | 10% | PWMReward |
| L1 creator share | 5% | PWMReward |
| Treasury share | 15% (remainder absorbs dust) | PWMReward |
| shareRatioP range | 1000-9000 (10%-90% in bps) | PWMCertificate, PWMReward |
| Staking: L1 Principle (mainnet design) | 10 PWM | PWMStaking |
| Staking: L2 Spec (mainnet design) | 2 PWM | PWMStaking |
| Staking: L3 Benchmark (mainnet design) | 1 PWM | PWMStaking |

**Note on stake unit / current testnet values.** `PWMStaking.stake()` accepts the
chain's native asset (`msg.value`). No PWM ERC20 token is deployed; the PWM
denomination above describes the *mainnet* design intent once the PWM token
ships. The current **Sepolia testnet** live values, set via
`setStakeAmount()` by governance, are:

| Layer | Testnet value (native ETH) |
|-------|----------------------------|
| L1 Principle | 0 ETH |
| L2 Spec | 10 ETH |
| L3 Benchmark | 2 ETH |

Auditors should review the slashing/graduation math against both sets of
values — particularly any rounding behavior where `amount / 2` meets odd
wei totals.
| Adversarial bounty cap | 50% of T_k | PWMTreasury |
| BURN_SINK | 0x000000000000000000000000000000000000dEaD | PWMStaking |

---

## 3. Known Issues / Design Decisions (NOT Bugs)

The following behaviors are intentional design decisions and should NOT be reported as findings:

### 3.1 Constructor Sets Deployer as Initial Governance

All governance-gated contracts accept `initialGovernance` in their constructor, which is set to the deployer address. Governance is subsequently transferred to the `PWMGovernance` multisig contract via `setGovernance()`. This is a standard deployment pattern for contracts without proxy/upgrade capability.

### 3.2 Division Rounding Dust Goes to Treasury

In `PWMReward.distribute()`, the six-way split computes AC, CP, L3, L2, and L1 amounts individually using integer division. The treasury amount is calculated as `drawAmt - acAmt - cpAmt - l3Amt - l2Amt - l1Amt`, absorbing all rounding dust. This ensures the six buckets always sum to exactly `drawAmt` with zero wei stuck in the contract. This is by design.

### 3.3 No Proxy / Upgrade Pattern (Immutable Deployment)

The contracts are deployed without proxy patterns (no UUPS, no Transparent Proxy, no Beacon). This is a deliberate choice: the protocol prioritizes immutability and auditability over upgradability. Migration to new contract versions would be handled via governance-gated address pointer updates (e.g., `setReward()`, `setCertificate()`).

### 3.4 shareRatioP Is Submitter-Controlled Within Bounds

The `shareRatioP` parameter (the AC/CP split ratio `p`) is set by the certificate submitter and accepted within the range 1000-9000 (10%-90%). This is intentional: the action credit holder and compute provider negotiate `p` off-chain, and the submitter commits it on-chain. The protocol enforces bounds but does not dictate the ratio.

### 3.5 BURN_SINK Is 0xdEaD (Not Actual Burn)

`PWMStaking` uses `0x000000000000000000000000000000000000dEaD` as the burn address rather than `address(0)`. This is because `address(0)` cannot receive native ETH via `call{value:}()` on all EVM implementations. The 0xdEaD address is a widely-used convention for permanent token removal. Tokens sent there are effectively irrecoverable.

### 3.6 Activity Uses Cumulative Count (Not Rolling Window)

`PWMMinting` uses cumulative activity counters for weight calculation rather than the 90-day rolling window specified in the design document. This is a deliberate simplification for M1.1; the rolling window is flagged as a follow-up item. Auditors should evaluate the cumulative model as-deployed.

**Expected remediation:** We anticipate auditors will recommend implementing the 90-day rolling window before mainnet (either via circular-buffer accounting or chunked epoch decay). We agree this should land pre-mainnet; the pre-disclosure is informational so auditors understand it is a known gap, not an oversight.

### 3.7 No External Dependencies

The contracts import no external libraries (no OpenZeppelin, no Chainlink). All access control, math, and payment logic is implemented inline. This reduces supply-chain risk but means standard patterns (ReentrancyGuard, SafeTransfer) are not used.

### 3.8 PWMMinting Requires Native ETH Prefunding

`PWMMinting.mintFor()` transfers native ETH from its own balance. The contract must be prefunded (via `receive() external payable`) before minting events. If underfunded, `mintFor()` reverts with "PWMMinting: underfunded." This is by design: the protocol operator ensures funding as part of deployment.

### 3.9 Any Founder Can Cancel Any Proposal

In `PWMGovernance`, any single founder can cancel any pending proposal via `cancelProposal()`. This is a design tradeoff: it prevents a griefing scenario where a majority pushes through a controversial change, at the cost of allowing a single founder to delay (but not permanently block) governance actions, since the proposal can simply be re-proposed.

### 3.10 Minting Contract Is Optional in PWMCertificate

`PWMCertificate.finalize()` skips the `minting.mintFor()` call if the minting address is unset (`address(0)`). This allows the certificate lifecycle to function in test environments or during pre-promotion phases without a live minting contract.

---

## 4. Critical Audit Focus Areas

### 4.1 Token Emission Math (PWMMinting) -- HIGHEST PRIORITY

- **M_POOL = 17,220,000 * 10^18** is a hard cap that must never be exceeded
- Zeno emission formula: `A_kjb = ((M_POOL - M_emitted) * w_k / sum_w) * w_b / sum_bw`
- Two sequential divisions create compounding precision loss -- verify dust never accumulates to material amounts
- Cached weight totals (`totalPrincipleWeight`, `sumBenchmarkWeight`) must remain perfectly synchronized with underlying state through all code paths (promotion, demotion, delta changes, benchmark add/remove, activity increments)
- Edge case: behavior when `remaining()` approaches zero (final emissions)
- Edge case: single promoted principle with single benchmark (degenerate weights)

### 4.2 Reward Distribution (PWMReward) -- HIGH PRIORITY

- Six-way payout: AC (`p * 55%`), CP (`(1-p) * 55%`), L3 (15%), L2 (10%), L1 (5%), Treasury (remainder)
- Double nested BPS math: `(drawAmt * shareRatioP * SPLIT_AC_CP) / (BPS_DENOM * BPS_DENOM)` -- overflow risk with large pool balances?
- `settled[certHash]` prevents double-settle -- verify no bypass via resubmission
- ETH transfers to 6 addresses in single tx -- CEI pattern adherence? Reentrancy via malicious recipient?
- Pool accounting: `pool[benchmarkHash]` must never go negative or leave stuck funds

### 4.3 Challenge Window Timing (PWMCertificate)

- `block.timestamp` comparison for 7/14-day windows -- manipulation risk is low on mainnet but should be documented
- Status transitions: `None -> Pending -> Challenged -> {Pending, Rejected}` and `Pending -> Finalized`
- Verify: challenged certificate cannot be finalized (requires status == Pending)
- Verify: rejected certificate cannot be re-challenged or re-finalized
- Challenge proof is emitted but not validated on-chain (governance resolves off-chain) -- is this clearly documented?

### 4.4 Access Control (All Contracts)

- `onlyGovernance` modifier on all state-changing admin functions
- `onlyCertificate` in PWMReward and PWMMinting
- `onlyReward` in PWMTreasury
- `msg.sender == staking` check in PWMReward.seedBPool
- Verify: no unprotected external function can drain or corrupt state
- Verify: governance transfer (`setGovernance`) cannot be called by non-governance

### 4.5 Staking Slash Logic (PWMStaking)

- Graduate: `half = amount / 2; other = amount - half` -- handles odd amounts correctly (other >= half)
- Challenge: same 50/50 with burn + challenger payout
- Fraud: 100% to BURN_SINK
- One-shot enforcement: `stakes[hash].status == Status.None` required for `stake()` -- verify no double-stake
- Can a staker front-run a slash by somehow unstaking? (No unstake function exists -- good)

### 4.6 Governance (PWMGovernance)

- 3-of-5 with 48h timelock
- `activateDAO()` is irreversible (`daoActivated = true`)
- Any founder can cancel any proposal -- griefing vector but bounded by re-proposal
- `proposedAt` is set to 0 only initially; executed/cancelled proposals keep their timestamp -- verify no confusion
- Proposal ID counter (`nextProposalId++`) is monotonic -- no collision possible

### 4.7 Reentrancy Considerations

- No ReentrancyGuard used anywhere
- `PWMReward.distribute()` sends ETH to 5 external addresses + treasury before the function ends
- `pool[benchmarkHash]` is decremented before sends (CEI pattern on pool balance)
- `settled[certHash] = true` is set before sends (CEI pattern on double-settle guard)
- However: a malicious recipient could reenter -- verify no exploitable path
- `PWMStaking.graduate()` sends ETH to staker then calls `reward.seedBPool()` -- ordering matters

---

## 5. Severity Guide

### Critical (Fund Loss / Protocol Breaking)

- Direct loss of user funds or protocol reserves
- Emission overflow beyond M_POOL cap (minting more than 17.22M tokens)
- Access control bypass allowing unauthorized fund withdrawal
- Double-spend or double-settlement of certificates
- Ability to drain reward pools or treasury beyond intended limits

### High (Incorrect Economic Outcomes)

- Incorrect payout math resulting in wrong amounts to recipients
- State corruption in cached weight totals causing incorrect future emissions
- Reentrancy enabling extraction of excess funds
- Challenge/finalization logic allowing invalid certificates to settle
- Staking slash logic paying wrong parties or wrong amounts

### Medium (Protocol Disruption / Griefing)

- Denial-of-service vectors blocking certificate finalization
- Griefing via governance proposals (cancel spam, proposal flooding)
- Timestamp manipulation affecting challenge windows (within block.timestamp tolerance)
- Stuck funds due to failed ETH transfers to non-payable addresses
- Activity counter manipulation affecting weight distribution

### Low (Gas / Style / Informational)

- Gas optimization opportunities
- Missing event emissions
- Code style improvements
- Redundant checks or unnecessary storage reads
- Documentation inconsistencies

---

## 6. Test Coverage Summary

| Test File | Cases | Coverage Area |
|-----------|-------|---------------|
| PWMRegistry.test.js | 7 | Registration, layer validation, parent chain, duplicate prevention |
| PWMGovernance.test.js | 8 | Multisig threshold, timelock enforcement, DAO activation, cancellation |
| PWMMinting.test.js | 9 | Emission math, weight calculation, activity tracking, access control |
| PWMCertificate.test.js | 6 | Submit, challenge, finalize, window timing, status transitions |
| PWMReward.test.js | 7 | Ranked draw, six-way split, pool accounting, double-spend prevention |
| PWMStaking.test.js | 8 | Stake, graduate, challenge slash, fraud burn, one-shot enforcement |
| PWMTreasury.test.js | 8 | Receive funding, bounty cap enforcement, isolation between principles |
| integration_l4_lifecycle.test.js | 1 | Full 7-contract end-to-end: register -> stake -> certify -> mint -> reward -> treasury |
| **Total** | **~54** | |

### Running Tests

```bash
cd pwm-team/infrastructure/agent-contracts
npm install
npx hardhat test
```

---

## 7. Files in Scope

```
infrastructure/agent-contracts/
+-- contracts/
|   +-- PWMRegistry.sol          (68 lines,  ~52 nSLOC)
|   +-- PWMGovernance.sol        (133 lines, ~100 nSLOC)
|   +-- PWMMinting.sol           (295 lines, ~210 nSLOC)
|   +-- PWMCertificate.sol       (227 lines, ~155 nSLOC)
|   +-- PWMReward.sol            (202 lines, ~145 nSLOC)
|   +-- PWMStaking.sol           (161 lines, ~115 nSLOC)
|   +-- PWMTreasury.sol          (76 lines,  ~55 nSLOC)
+-- test/
|   +-- PWMRegistry.test.js
|   +-- PWMGovernance.test.js
|   +-- PWMMinting.test.js
|   +-- PWMCertificate.test.js
|   +-- PWMReward.test.js
|   +-- PWMStaking.test.js
|   +-- PWMTreasury.test.js
|   +-- integration_l4_lifecycle.test.js
+-- hardhat.config.js
```

### Out of Scope

- Off-chain components (CLI, miner, web explorer, indexer)
- IPFS integration
- Frontend / API code
- Genesis JSON content
- **On-chain `commit()` / `reveal()`** -- planned extension, not yet implemented on any contract in this audit. Note: `agent-miner/pwm_miner/commit_reveal.py` implements an *off-chain* commit/reveal state machine that a future on-chain version would mirror. The off-chain module is out of scope for this audit.
- DAO voting implementation (deferred post-M3; `activateDAO()` is a flag only)

---

## 8. Specification References

- **pwm_overview1.md** -- Protocol specification (canonical source of truth for all math, parameters, and economic design)
- **new_impl_plan.md** -- Implementation plan and acceptance criteria
- **validation.md** -- Per-contract validation checklist (12 sections)

---

## 9. Deployed Addresses (Sepolia Testnet)

| Contract | Address |
|----------|---------|
| PWMRegistry | See `interfaces/addresses.json` |
| PWMGovernance | See `interfaces/addresses.json` |
| PWMMinting | See `interfaces/addresses.json` |
| PWMCertificate | See `interfaces/addresses.json` |
| PWMReward | See `interfaces/addresses.json` |
| PWMStaking | See `interfaces/addresses.json` |
| PWMTreasury | See `interfaces/addresses.json` |

**Deployer:** `0x0c566f0F87cD062C3DE95943E50d572c74A87dEd`
**Founder wallets:** 5 addresses configured at PWMGovernance deployment.

---

## 10. Draft Outreach Emails

### 10a. Code4rena Submission Email

```
To: contests@code4rena.com
Subject: Audit Contest Request -- Physics World Model (PWM) Smart Contracts

Dear Code4rena Team,

We are writing to request a competitive audit contest for the Physics World Model
(PWM) smart contract suite.

PROJECT OVERVIEW

PWM is a decentralized protocol for incentivized physics research. The protocol
manages a four-layer artifact hierarchy with per-event token emission (Zeno curve),
ranked-draw reward settlement, tiered staking with slashing, and 3-of-5 multisig
governance with a 48-hour timelock. The contracts are written in Solidity ^0.8.24
with no external dependencies (no OpenZeppelin, no proxies, no oracles).

SCOPE

- 7 Solidity contracts, ~832 nSLOC (1,162 total lines)
- Compiler: solc ^0.8.24
- Framework: Hardhat
- Test suite: ~54 tests passing
- No external library dependencies
- Currently deployed on Sepolia testnet; targeting Ethereum mainnet post-audit

REPOSITORY

- GitHub: https://github.com/integritynoble/pwm  (currently private; we will
  grant read access to Code4rena staff upon engagement, or provide a
  public snapshot at the `audit-v1` tag)
- Path: pwm-team/infrastructure/agent-contracts/contracts/
- Scope commit: tagged `audit-v1` — frozen snapshot for the duration of
  the contest
- Submission package (this document): pwm-team/infrastructure/agent-contracts/AUDIT_SUBMISSION.md

BUDGET

- Prize pool / contest fee: [TODO: $XX,000 USD — to be set by director before sending]
- We are flexible on the split between prize pool, judge pool, and
  remediation review fees

KEY RISK AREAS

1. Token emission math (nested integer division, cached weight consistency)
2. Reward distribution (six-way payout split, ranked-draw pool accounting)
3. Challenge window timing and status transition integrity
4. Cross-contract fund flows (Minting -> Reward -> Treasury)
5. Staking slash logic and one-shot enforcement

TIMELINE

We are ready to begin the contest at your earliest available slot. We have a
complete audit submission package including known issues, severity guide, and
architecture documentation.

We look forward to discussing scope, timeline, and pricing.

Best regards,
Chengshuai Yang
Physics World Model (PWM)
https://github.com/integritynoble/pwm
```

### 10b. Sherlock Submission Email

```
To: audit@sherlock.xyz
Subject: Audit Contest Request -- Physics World Model (PWM) Smart Contracts

Dear Sherlock Team,

We would like to submit the Physics World Model (PWM) smart contract suite for a
Sherlock audit contest.

PROJECT OVERVIEW

PWM is a decentralized protocol for incentivized physics research, implementing
per-event Zeno-curve token emission from a fixed 17.22M pool, ranked-draw reward
settlement with six-way payout splits, three-tier staking with graduation and
slashing mechanics, and 3-of-5 multisig governance with a 48-hour timelock. All
contracts are written in Solidity ^0.8.24 with zero external dependencies.

SCOPE

- 7 contracts, ~832 nSLOC across 1,162 total lines
- No proxies, no upgradability, no external imports
- ~54 Hardhat tests passing, including a full 7-contract integration test
- Deployed on Sepolia testnet; mainnet deployment planned post-audit

CONTRACTS

| Contract        | nSLOC | Complexity | Purpose                                    |
|-----------------|-------|------------|--------------------------------------------|
| PWMRegistry     | ~52   | Low        | Immutable artifact hash store               |
| PWMGovernance   | ~100  | Medium     | 3-of-5 multisig + 48h timelock             |
| PWMMinting      | ~210  | High       | Zeno-curve per-event emission (17.22M cap) |
| PWMCertificate  | ~155  | Medium     | Certificate lifecycle + challenge window   |
| PWMReward       | ~145  | High       | Ranked-draw pool + six-way split           |
| PWMStaking      | ~115  | Medium     | Three-tier staking + slashing              |
| PWMTreasury     | ~55   | Low        | Per-principle treasury + bounty payouts    |

REPOSITORY

- GitHub: https://github.com/integritynoble/pwm  (currently private; we will
  grant read access to Sherlock staff upon engagement, or provide a
  public snapshot at the `audit-v1` tag)
- Path: pwm-team/infrastructure/agent-contracts/contracts/
- Scope commit: tagged `audit-v1` — frozen snapshot for the duration of
  the contest
- Submission package (this document): pwm-team/infrastructure/agent-contracts/AUDIT_SUBMISSION.md

BUDGET

- Prize pool / contest fee: [TODO: $XX,000 USD — to be set by director before sending]
- We are flexible on the split between contest pool, lead auditor fee,
  and remediation review

We have prepared a comprehensive audit submission package with known design
decisions, severity definitions, and architecture documentation. We can provide
this immediately upon engagement.

We are flexible on timing and would appreciate guidance on your current contest
schedule and pricing for this scope.

Best regards,
Chengshuai Yang
Physics World Model (PWM)
https://github.com/integritynoble/pwm
```

---

## Appendix A: Contract-by-Contract Summary

### A.1 PWMRegistry.sol

**Purpose:** Immutable, append-only artifact hash store for all protocol artifacts across four layers (L1 Principle, L2 Spec, L3 Benchmark, L4 Solution).

**Key functions:**
- `register(hash, parentHash, layer, creator)` -- stores artifact with parent-chain validation
- `getArtifact(hash)` -- returns metadata
- `exists(hash)` -- boolean existence check

**Invariants:**
- No artifact can be registered twice (duplicate prevention via timestamp check)
- L1 artifacts must have zero parent; L2-L4 must reference a registered parent
- No delete or update functions exist

### A.2 PWMGovernance.sol

**Purpose:** Phase 1-2 governance via 3-of-5 founder multisig with 48-hour timelock on parameter changes. Includes irreversible DAO activation switch.

**Key functions:**
- `proposeParameter(key, value)` -- creates timelocked proposal (auto-approves for proposer)
- `approveProposal(id)` -- one vote per founder per proposal
- `executeProposal(id)` -- requires 3 approvals + 48h elapsed
- `cancelProposal(id)` -- any founder can cancel any pending proposal
- `activateDAO(id)` -- irreversible; disables multisig path forever

**Invariants:**
- Exactly 5 unique, non-zero founder addresses set at construction
- Proposals require >= 3 approvals AND >= 48h timelock before execution
- DAO activation is one-way (once `daoActivated = true`, all multisig functions revert)

### A.3 PWMMinting.sol

**Purpose:** Per-event Zeno token emission from a fixed 17.22M pool, allocated across promoted principles and their benchmarks by weight.

**Key functions:**
- `mintFor(principleId, benchmarkHash)` -- called by PWMCertificate.finalize(); computes and deposits emission
- `setDelta(principleId, delta)` -- governance sets principle weight factor
- `setPromotion(principleId, status)` -- governance promotes/demotes principles
- `registerBenchmark(principleId, benchmarkHash, rho)` -- governance registers benchmarks
- `removeBenchmark(principleId, benchmarkHash)` -- governance removes benchmarks (swap-and-pop)

**Invariants:**
- `M_emitted` must never exceed `M_POOL` (17,220,000 * 10^18)
- `totalPrincipleWeight` must equal the sum of weights of all promoted principles
- `sumBenchmarkWeight[k]` must equal the sum of weights of all registered benchmarks under principle k
- Activity increments happen after emission calculation (first event uses genesis weight)

### A.4 PWMCertificate.sol

**Purpose:** Manages the L4 certificate lifecycle: submission, challenge window, and finalization dispatching to Reward and Minting contracts.

**Key functions:**
- `submit(args)` -- registers a certificate with all payout wiring locked at submission time
- `challenge(certHash, proof)` -- files a challenge within the active window
- `resolveChallenge(certHash, upheld)` -- governance resolves (upheld = rejected; not upheld = reinstated)
- `finalize(certHash)` -- dispatches to Minting and Reward after window closes

**Invariants:**
- A certificate can only be finalized if status == Pending AND window has elapsed
- A challenged certificate cannot be finalized until governance resolves it
- A finalized or rejected certificate cannot be re-finalized
- shareRatioP is locked at submission (1000-9000 range)

### A.5 PWMReward.sol

**Purpose:** Holds per-benchmark reward pools and settles ranked-draw payouts with six-way splits.

**Key functions:**
- `distribute(certHash, draw)` -- settles a certificate's ranked draw (called by PWMCertificate only)
- `seedBPool(benchmarkHash)` -- receives 50% of graduated stakes (called by PWMStaking only)
- `depositMinting(benchmarkHash)` -- receives minting emission (called by PWMMinting only)
- `depositBounty(benchmarkHash)` -- public bounty deposits
- `rankBps(rank)` -- returns draw percentage for rank 1-10 (0 for 11+)

**Invariants:**
- Each certHash can only be settled once (`settled` mapping)
- The six payout amounts must sum to exactly `drawAmt` (treasury absorbs dust)
- Pool balance must be sufficient for the draw
- Rank 11+ draws zero (full rollover)

### A.6 PWMStaking.sol

**Purpose:** Three-tier fixed-amount staking for artifact promotion, with graduation, challenge slash, and fraud slash outcomes.

**Key functions:**
- `stake(layer, artifactHash)` -- stakes exact per-layer amount (10/2/1 PWM)
- `graduate(artifactHash, benchmarkHash)` -- 50% returned to staker, 50% seeds reward pool
- `slashForChallenge(artifactHash, challenger)` -- 50% burned, 50% to challenger
- `slashForFraud(artifactHash)` -- 100% burned

**Invariants:**
- Each artifact can only be staked once (Status.None required)
- Stake amount must exactly match the per-layer requirement
- No unstake function exists (funds are locked until resolution)
- BURN_SINK (0xdEaD) receives burned amounts

### A.7 PWMTreasury.sol

**Purpose:** Per-principle treasury (T_k) accumulating 15% of each draw, with adversarial bounty payouts capped at 50%.

**Key functions:**
- `receive15pct(principleId, amount)` -- credited by PWMReward during settlement
- `payAdversarialBounty(principleId, winner, amount)` -- governance-gated, capped at 50% of T_k

**Invariants:**
- `msg.value` must equal `amount` in `receive15pct` (value mismatch check)
- Bounty payout must not exceed 50% of current T_k balance (`amount * 2 <= balance`)
- Principles are fully isolated (no cross-principle fund access)

---

## Appendix B: Recommended Audit Platforms

| Platform | Model | Est. Timeline | Notes |
|----------|-------|---------------|-------|
| Code4rena | Competitive contest | 1-2 weeks | Cost-effective for ~800 nSLOC, multiple independent auditors |
| Sherlock | Contest + lead auditor | 1-2 weeks | Lead auditor guarantee, structured severity classification |
| Cantina | Managed contest | 2-3 weeks | Spearbit auditors, higher cost |
| OpenZeppelin | Traditional engagement | 4-8 weeks | Gold standard, significantly more expensive |
| Trail of Bits | Traditional engagement | 4-6 weeks | Deep expertise, significantly more expensive |

For a ~832 nSLOC codebase with focused complexity in two contracts (PWMMinting and PWMReward), a **competitive audit contest** (Code4rena or Sherlock) is recommended as the most cost-effective approach. Multiple independent wardens typically surface more findings than a single-auditor engagement at this scale.
