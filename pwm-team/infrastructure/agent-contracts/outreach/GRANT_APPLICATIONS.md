# PWM Audit-Grant Application Drafts

**Prepared by:** agent-coord (Server 2)
**Date:** 2026-04-21
**Purpose:** three parallel applications — whichever funds first wins.
Director fills in contact info and submits via each foundation's portal.

---

## Application 1 — Ethereum Foundation Ecosystem Support Program (ESP)

**Portal:** https://esp.ethereum.foundation/applicants
**Form type:** Small Grants (<$30K) OR Project Grants ($30K–$200K+)
**Recommended tier:** Project Grant, $60K ask (audit-only)

### Project Name
Physics World Model (PWM)

### One-sentence description
A decentralized protocol for incentivized physics research that converts verifiable scientific contribution (a Principle, a Benchmark, a Solution) into on-chain rewards via a 4-layer artifact hierarchy and ranked-draw payout.

### Website / repo
- Web explorer (reference impl): https://pwm-explorer-dsag.onrender.com and https://pwm-explorer.fly.dev/
- Code: https://github.com/integritynoble/pwm-public
- Protocol paper: `papers/Proof-of-Solution/pwm_overview1.md` in the repo

### What are you building and why?
PWM is a full-stack protocol — 7 Solidity contracts, a CLI miner reference implementation, a web explorer, and a genesis catalogue of 500 scientific principles covering imaging, spectroscopy, fluid dynamics, microscopy, and related fields. The goal is to make the process of contributing a verified scientific solution (publishing a benchmark, solving it, getting paid) a fully on-chain primitive that any researcher with a wallet can participate in.

Today, research contribution is rewarded by citations, grants, and employment — all slow, centralized, and gated. PWM turns the process into a three-layer **principle / spec / benchmark / solution** pipeline where every layer is a content-addressed artifact on-chain, every layer carries slashable stakes, and every verified L4 solution triggers a ranked-draw payout from a dedicated per-benchmark pool.

### What problem is this solving for the ecosystem?
- **For researchers**: a permissionless, immediate, composable reward channel. No peer-review lag; slashing enforces quality.
- **For Ethereum**: PWM is pure L1-usable today and targets an L2 mainnet for gas economics. It adds a *scientific computation* use case to Ethereum's application portfolio — distinct from DeFi / NFTs / identity.
- **For open science**: every artifact hash is content-addressed; benchmarks are reproducible; solutions are open-verifiable. We treat a scientific principle as a first-class on-chain object.

### Current status and on-chain evidence
All 7 contracts are deployed and operational on Sepolia testnet:
- `PWMRegistry`, `PWMGovernance`, `PWMMinting`, `PWMCertificate`, `PWMReward`, `PWMStaking`, `PWMTreasury`
- Addresses: `pwm-team/coordination/agent-coord/interfaces/addresses.json`
- 6 genesis artifacts registered on-chain (CASSI + CACTI, L1/L2/L3 each): Sepolia blocks 10703851–10703857
- **100 L4 certificates submitted end-to-end** across 4 wallets: blocks 10704316–10704408 (see `scripts/phase_d_100_job_run.py` / `phase_d_100_sequential_topup.py` results)
- 3-CP concurrent-submission race: all 3 CPs landed in the same block (10704267), zero contract-side reverts
- Slashing mechanics verified: `setStakeAmount → stake → slashForFraud → restore` cycle executed successfully (blocks 10704715–10704722)
- Web explorer live at https://pwm-explorer.fly.dev/ and https://pwm-explorer-dsag.onrender.com

### Team
- **Chengshuai Yang** — founder, author of the protocol spec (pwm_overview1.md) and primary developer
- Team architecture uses 11 specialized agent roles + 3 verifier agents as documented in `papers/Proof-of-Solution/new_impl_plan.md`. The team is currently small; PWM is targeting broader community build-out via Reserve bounties (1.3M PWM allocated) as the protocol matures.

### What are you asking ESP for?
- **$60,000 USD** to cover a paid competitive audit (Code4rena or Sherlock contest) for the 7-contract suite (832 nSLOC)
- Timeline: 4–6 weeks (contest + judge pool + remediation review)
- This would directly unblock our Ethereum mainnet deploy. Without audit funding, we launch on an L2 mainnet with TVL caps as a risk-mitigation measure; with audit funding, we can launch at full scale.

### What does success look like?
- Audit completed, findings remediated, contracts deployed on Ethereum mainnet (or equivalent audited L2)
- Genesis 500 bounty opens (Bounty #7, ~168K PWM, already pre-staged — see `pwm-team/bounties/07-genesis-principle-polish.md`)
- First external L4 solution submitted by a researcher outside the founding team

### Timeline
- Audit: weeks 1–4 (contest + judging)
- Remediation: week 5
- Mainnet deploy: week 6
- First external contributor onboarded: week 7–8

### Prior funding
None. Self-funded to date. All deploy + Sepolia testing gas paid by the founder's wallet.

### Attachments
- `pwm-team/infrastructure/agent-contracts/AUDIT_SUBMISSION.md` (audit scope package)
- `pwm-team/infrastructure/agent-contracts/AUDIT_FREE_PATH.md` (current zero-cost plan we'd replace with your funding)
- `papers/Proof-of-Solution/pwm_overview1.md` (protocol spec)
- `pwm-team/coordination/CHECKLIST_EXECUTION_REPORT.md` (operational evidence)

---

## Application 2 — Optimism Foundation (Retro-Funding / Mission Grants)

**Portal:** https://app.optimism.io/retropgf (Retro-Funding rounds)  OR https://optimism.foundation/grants (Mission Grants, upfront)
**Form type:** Mission Grant (upfront) — Developer Tooling or Protocol Innovation category
**Recommended ask:** 50,000 OP (~$50K at current rates — verify)

### Project Name
Physics World Model (PWM)

### Which OP category does this fit?
**Protocol Innovation** (primary) + **Developer Tooling** (secondary). PWM is a novel protocol category — on-chain incentivized science — that does not overlap with any existing DeFi / NFT / infrastructure project on Optimism today.

### Short description
PWM is a 7-contract protocol for turning verifiable scientific contribution into on-chain rewards. A researcher registers a Principle (L1), writes a Spec for it (L2), publishes a reproducible Benchmark (L3), and any Solver (L4) who beats the benchmark gets paid from a per-benchmark reward pool. The protocol is immutable (no proxies, no upgradability), self-custodial, and currently live on Sepolia testnet.

### Why Optimism (not Ethereum mainnet)?
- **Gas economics**: PWM generates many small on-chain actions (cert submissions per solved benchmark, per-principle activity updates every mint). L2 makes this viable for researchers; L1 gas would gate out academic users.
- **Superchain alignment**: PWM's per-benchmark pools and six-way payout splits are a natural fit for OP-stack composability. A future PWM could be deployed across Base, Optimism, and other OP-stack chains with shared L1 state anchoring.
- **Our deploy script already supports Optimism**: see `pwm-team/infrastructure/agent-contracts/hardhat.config.js` lines 35-39. We can deploy to OP mainnet within hours of your engagement.

### On-chain activity and evidence
- 100 certificates submitted end-to-end on Sepolia across 4 wallets
- 3-CP concurrent race (same-block landing, zero reverts)
- Slashing mechanics verified
- Web explorer live: https://pwm-explorer.fly.dev/

### Specific ask
**50,000 OP** (or USD-equivalent) allocated as:
- 40,000 OP → competitive audit contest (Code4rena or Sherlock)
- 10,000 OP → Optimism-specific integration work (OP Stack adapter in web explorer, Superchain-compatible event indexing)

### Deliverables within 90 days
1. Audit complete, all High/Critical findings remediated
2. PWM contracts deployed to Optimism mainnet
3. Optimism-native web explorer live (indexing OP events)
4. First scientific benchmark (CASSI compressed sensing) accepting real solutions on Optimism mainnet
5. Bounty #7 (Genesis Principle Polish, ~168K PWM reserve allocation) opens for external contributors

### Team / credentials
- Chengshuai Yang — founder, sole primary developer
- Protocol spec: `papers/Proof-of-Solution/pwm_overview1.md`
- Code: https://github.com/integritynoble/pwm-public

### KPIs to measure success
- # of L4 certificates submitted on OP mainnet within 90 days: target 500+
- # of distinct L1 Principles registered: target 10+ post-launch
- $ value of stake locked in PWMStaking on OP: target $50K+ within 90 days
- Unique researcher wallets submitting L4s: target 25+

---

## Application 3 — Arbitrum Foundation Grants Program

**Portal:** https://arbitrum.foundation/grants
**Form type:** Domain-specific grant (Protocol Research / Infrastructure)
**Recommended ask:** $50,000 USDC

### Project Name
Physics World Model (PWM)

### Category
**Protocol Research + Developer Infrastructure**. PWM is a new primitive — incentivized on-chain science — and it benefits from Arbitrum's Stylus (future Rust support for scoring logic) and its low-latency finality for research-grade solution evaluation.

### One-paragraph description
Physics World Model (PWM) is a 7-contract Solidity protocol that makes scientific contribution a first-class on-chain primitive. A researcher publishes a Benchmark with content-addressed stake; any Compute Provider who submits a verified Solution receives a ranked-draw payout from a dedicated per-benchmark pool. The protocol is immutable, self-custodial, has no external dependencies, and has been verified end-to-end on Sepolia testnet with 100+ certificates successfully submitted and settled.

### Why Arbitrum?
- **Low and predictable gas** for the per-event minting pattern in PWMMinting
- **Stylus** compatibility on the horizon: our future scoring engine (now Python off-chain in `pwm-team/infrastructure/agent-scoring/`) could migrate to Stylus for on-chain verification of certain benchmark classes
- **Existing research community**: Arbitrum's grant history shows openness to non-DeFi primitives (research infra, identity, public goods), which aligns with PWM's mission

### Evidence of progress
- 7 immutable Solidity contracts shipped, 53/53 Hardhat tests passing
- Live on Sepolia testnet with full end-to-end activity:
  - 6 genesis artifact registrations (CASSI + CACTI)
  - 100 L4 certificates successfully submitted across 4 wallets
  - 3-CP concurrent race verified
  - Slashing mechanics exercised end-to-end
- Two public web-explorer deploys live today
- Reference CLI, miner, scoring engine, and genesis 500 catalogue all on `main`

### Funding ask breakdown
- $40,000 USDC → competitive audit contest
- $10,000 USDC → Arbitrum-specific integration (Stylus explorer module for future scoring)

### Deliverables within 90 days
1. Audited contracts deployed on Arbitrum mainnet (One or Nova, your call)
2. First 5 L4 certificates submitted on Arbitrum mainnet by non-founder wallets
3. Published write-up / blog post on using Arbitrum for scientific-contribution markets
4. Open Bounty #7 (Genesis Principle Polish) — brings external physics researchers on-chain to Arbitrum

### Anti-goals / what we will NOT do with this grant
- Not for marketing / paid ads
- Not for salaries
- Not for token liquidity or DEX listings
- 100% into audit + L2 integration

### Contact
[director to fill in]

---

## Application checklist before submitting

- [ ] Replace all [director to fill in] placeholders with real contact info
- [ ] Verify the current OP / USDC conversion and adjust the 50,000 OP number if OP price has shifted significantly
- [ ] Confirm `https://pwm-explorer.fly.dev/` and `https://pwm-explorer-dsag.onrender.com` are both reachable the day you submit (free-tier cold starts can make them slow)
- [ ] Make the GitHub repo either (a) public, or (b) have a ready process for granting read access to foundation staff within 24h of request
- [ ] If submitting all three in one week, space them by 2–3 days so the first response informs the next application
- [ ] Track submission dates in `pwm-team/coordination/agent-coord/progress.md` under a new `GRANT_APPLICATIONS_OPEN` signal
