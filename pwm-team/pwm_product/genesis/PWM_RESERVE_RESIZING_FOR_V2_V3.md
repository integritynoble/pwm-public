# Should the Reserve allocation grow to fund v2 and v3 scaling? Can v1 still be modified?

**Date:** 2026-04-29
**Owner:** Director
**Audience:** PWM contract authors, deploy planners, governance reviewers, founding team
**Status:** decision document — recommendation to rebalance pre-mainnet
**Cross-references:**
- `papers/Proof-of-Solution/pwm_overview1.md` § 10 (Token Economics) — current Reserve at 10%
- `papers/Proof-of-Solution/pwm_overview2.md` Appendix C — v2 contract cost ~$23K
- `papers/Proof-of-Solution/pwm_overview3.md` Appendix C — v3 V2 suite cost ~$60K
- `pwm-team/pwm_product/genesis/PWM_V2_V3_CONTRACT_COMPATIBILITY.md` — full v2/v3 deploy analysis
- `pwm-team/infrastructure/agent-contracts/contracts/PWMMinting.sol` — line 30, `M_POOL = 17_220_000 ether` constant
- `pwm-team/infrastructure/agent-contracts/deploy/mainnet.js` — the deploy script that sets the initial allocation

---

## TL;DR

**The Reserve allocation should grow from 10% → 12-13% before Base mainnet deploy.** The window is open: Sepolia is deployed but Base mainnet is not (Step 7 of the deploy chain blocked on deployer ETH funding). Once mainnet is deployed, the initial allocation is **frozen forever**. Touching it later is impossible — the 21M total supply is fixed and the 17.22M Mining pool is hardcoded as an immutable constant.

The +2-3 percentage points (~420K-630K PWM) materially derisks v2/v3 audit and the first 1-2 years of auto-verifier + per-domain committee operations, which `pwm_overview1.md`'s 10% Reserve was never sized to cover.

---

## Question 1 — what's actually fixed in v1 contracts vs. modifiable at deploy

The four pools in the v1 token-economics table have very different mutability:

| Pool | Where it's enforced | Modifiable now? |
|---|---|---|
| **21M total supply** | `PWMToken` ERC-20 — one-time mint at deploy | **Frozen forever**. Cannot mint more. |
| **Mining pool 82% / 17.22M** | `PWMMinting.sol` line 30: `uint256 public constant M_POOL = 17_220_000 ether` | **Frozen forever**. Hardcoded constant in immutable contract. |
| **Reserve 10% / 2.1M** | NOT enforced by any contract. Set as a deploy-time ERC-20 transfer to the 4-of-7 Reserve multisig in `deploy/mainnet.js`. | **Modifiable until mainnet deploy.** |
| **Liquidity 5% / 1.05M** | Same — deploy-time transfer | **Modifiable until mainnet deploy.** |
| **Founding team 3% / 0.63M** | Likely a vesting contract (4-year linear, 12-month cliff per `pwm_overview1.md` § 10), but the *amount* deposited into the vesting contract is set at deploy time | **Modifiable until mainnet deploy.** |

**Critical constraint:** the `M_POOL = 17_220_000 ether` constant is load-bearing for the v1 emission economics and is hardcoded in the immutable contract. Any rebalancing must come out of the **non-mining 18% (3.78M PWM)** — the Reserve, Liquidity, and Founding Team buckets. The 82% Mining pool cannot be touched without redeploying `PWMMinting`, which would invalidate the current testnet history and the mainnet-v1.0.0 audit.

### Window-of-opportunity check

| State | v1 contracts deployed | Allocation modifiable |
|---|---|---|
| Sepolia (testnet) | Yes — deployed | N/A — testnet uses a separate token instance |
| Base mainnet | **NO — not yet deployed** | **YES — fully open** |

Once Step 7 of `MAINNET_DEPLOY_HANDOFF.md` runs (Director funds deployer wallet → CPU runs `deploy/mainnet.js`), the Reserve allocation locks in for the life of the protocol.

---

## Question 2 — should Reserve grow?

**Yes.** `pwm_overview1.md` sized Reserve at 10% / 2.1M PWM for v1's infrastructure bounty board (smart contracts, scoring engine, CLI, IPFS pinning, UI, mining client). The pre-launch bounty board alone consumes ~1.01M PWM:

| v1 infrastructure bounty | PWM |
|---|---|
| Smart contract suite | 500,000 |
| Scoring engine | 200,000 |
| pwm-node CLI | 100,000 |
| Web submission UI | 80,000 |
| Mining client | 80,000 |
| IPFS benchmark pinning service | 50,000 |
| **Sub-total** | **1,010,000** |

That leaves only ~1.09M PWM for the entire post-launch operating life of the protocol — covering retroactive grants, security audits, university partnerships, emergency response, legal/compliance, AND now the v2/v3 program that didn't exist when v1 was sized.

### v2 and v3 add real new costs

v2 (add-on contracts to the v1 suite) and v3 (parallel V2 contract suite + auto-verifier + per-domain committees + AI authoring infrastructure) add costs that were not in v1's Reserve plan:

| Cost driver | One-time / recurring | USD estimate | PWM @ $0.50/PWM |
|---|---|---|---|
| v2 add-on contract audit (`PWMGateClassRegistry`, `PWML0MetaRegistry`, off-chain settlement) | one-time | ~$23K | ~46,000 |
| v2 implementation (~6.5 weeks engineer @ $4K/wk) | one-time | ~$26K | ~52,000 |
| v3 V2-suite contract audit (`PWMRegistryV2`, `PWMGovernanceV2`, `PWMRewardV2`) | one-time | ~$40K | ~80,000 |
| v3 auto-verifier build + audit | one-time | ~$24K (build) + $20K (audit) | ~88,000 |
| v3 implementation (~14 weeks engineer @ $4K/wk, excluding auto-verifier) | one-time | ~$56K | ~112,000 |
| Auto-verifier ongoing operations (servers, monitoring, model upgrades) | recurring | ~$50K/yr | ~100,000/yr |
| AI authoring agent infrastructure (LLM API, manifest generation) | recurring | ~$30K/yr | ~60,000/yr |
| Per-domain reviewer committee stipends (12 domains × $20K/yr) | recurring | ~$240K/yr | ~480,000/yr |
| Auto-verifier liability insurance pool seed | one-time | ~$100K | ~200,000 |
| Bug bounties (Immunefi pool top-up over time) | recurring | ~$50K/yr | ~100,000/yr |
| **One-time total (v2 + v3 buildout)** | | **~$289K** | **~578,000** |
| **Recurring total (post-v3 maturity)** | | **~$370K/yr** | **~740,000/yr** |
| **Cumulative 5-year v2/v3 burn** | | **~$2.14M** | **~4,300,000** |

These numbers assume PWM at $0.50/USD — at lower prices the PWM burn is higher. At a $0.10 launch price, the 5-year cumulative is ~21M PWM (10× the entire current Reserve), which is obviously infeasible from a 2.1M Reserve alone — operations have to come from royalty inflows by then.

But the **first 2 years (one-time + early recurring)** cost ~580K + ~1.48M = **~2.06M PWM**. That alone consumes essentially all of the 2.1M Reserve before any v1 ongoing operations are funded. Hence the rebalancing case.

### What v1 Reserve was NOT sized for (but v2/v3 needs)

- v2/v3 contract development engineer time (v1 assumed external bounty winners; v2/v3 needs in-house contract authors because the contracts have to interoperate with the immutable v1 suite)
- Auto-verifier as a continuously-run service (v1 has no equivalent — verifier is human-only)
- Per-domain reviewer committee stipends (v1 has one flat reviewer pool; v3 has ~12)
- AI authoring agent infrastructure (v1 has no equivalent)
- v2/v3 audit cycles on top of v1's already-incurred audit
- Insurance pool for auto-verifier liability (v1 has no equivalent)

---

## Two paths to fund v2/v3

### Option A — rebalance pre-mainnet (recommended)

Modify `deploy/mainnet.js`'s initial transfer amounts before Step 7 runs. The `M_POOL` constant is untouched; only the 18% non-mining bucket is rebalanced.

| Pool | v1 spec | Proposed | Delta |
|---|---|---|---|
| Mining 82% | 17.22M | 17.22M | unchanged (hardcoded) |
| **Reserve** | 10% / 2.1M | **13% / 2.73M** | **+0.63M** |
| Liquidity | 5% / 1.05M | 4% / 0.84M | -0.21M |
| Founding team | 3% / 0.63M | 1% / 0.21M (with longer vest) | -0.42M |

**Justification for the trims:**

- **Liquidity 5% → 4%**: Protocol-owned liquidity (POL) generates ongoing trading fees that route back to Reserve per `pwm_overview1.md` § Liquidity. A 1% trim still leaves 840K PWM seeded into Uniswap v3 / Curve, sufficient for day-1 tradability. POL fees backfill toward the 5% target over time.

- **Founding team 3% → 1%**: Director already runs the operation and earns through standard channels (Reserve grants, royalties on staked Principles). The current 3% allocation is a holdover from earlier protocol designs; cutting it to 1% with the same 4-year vest signals "founders mine like everyone else" and avoids the "founders self-allocate" optic. Plus, the team can still propose grants from the expanded Reserve through the standard governance vote — same access, better optics.

- **Reserve 10% → 13%**: +630K PWM. At $0.50/PWM this is +$315K — covers v2 audit (~$23K) + v3 audit (~$60K) + auto-verifier build (~$44K) + insurance pool seed (~$100K) + ~3 years of bug bounties. Roughly the first half of the 5-year v2/v3 burn estimate.

**Cost of executing Option A:** ~30 minutes of Director time + a single review pass on `deploy/mainnet.js`. **Zero contract changes. Zero re-audit cost.** The audit certified the contract logic, not the deploy-script transfer amounts.

### Option B — keep v1 allocation, route v2/v3 fees to Reserve

If the 10% Reserve stays, ongoing inflows can refill it faster than v1 anticipated. Four mechanisms:

1. **v2's withheld 50% from `data_driven_statistical` payouts** routes to Reserve (instead of `PWMTreasury`). This is a settlement-service-level decision that needs no v1 contract change — the off-chain settlement service in v2 Appendix C just changes its destination address.

2. **Slashing penalty redirection.** Currently 50% burn / 50% to challenger. Modify to 25% burn / 50% challenger / **25% Reserve**. **Requires `PWMStaking.sol` change.**

3. **POL trading fees to Reserve** — already specified in v1 § Liquidity. Make sure the mainnet deploy actually wires this; verify in `verify_l2_deploy.py`.

4. **L4 royalty skim to Reserve** — e.g., 1% of every L4 event flows to Reserve infrastructure pool. **Requires `PWMReward.sol` change.**

**Cost of executing Option B:** mechanisms 2 and 4 require modifying audited Solidity. `PWMReward` and `PWMStaking` are currently in audit-clean state (`mainnet-v1.0.0` tag). Touching either means a new audit cycle (estimated ~$15K + 3 weeks elapsed time per contract). Mechanism 1 is essentially free; mechanism 3 just needs verification not new code.

---

## Recommendation: **Option A + mechanism 1 of Option B**

**Option A is the right call** for three reasons:

1. **The window is closing.** Base mainnet deploy is gated only on Director ETH funding (Step 7). Once executed, the allocation locks for the life of the protocol. There is no second chance.

2. **Zero contract risk.** Option A modifies only the deploy script's transfer amounts. The audited Solidity is untouched. No re-audit, no timeline slip, no introduced risk.

3. **Defensible optics.** Trimming founder allocation while expanding the merit-based Reserve pool reads better in any future grant application, regulatory filing, or audit.

**Combine with mechanism 1 of Option B:** at v2 deploy (Phase 2 of the v2/v3 rollout in `PWM_V2_V3_CONTRACT_COMPATIBILITY.md`), wire the v2 50% withholding from `data_driven_statistical` payouts to flow to **Reserve** rather than to per-Principle `PWMTreasury`. This is an off-chain settlement-service routing decision, costs nothing extra, and gives Reserve a continuously-replenishing inflow as the long-tail catalog grows.

**Skip mechanisms 2 and 4 of Option B for now.** They require touching audited contracts. The combination of Option A + mechanism 1 covers the v2/v3 funding gap without that risk. If five years out the Reserve still runs short, mechanisms 2 and 4 can be added in a future contract revision (V3 of the contracts, possibly).

---

## What needs to happen

Concrete checklist before Step 7 of the mainnet deploy chain:

- [ ] Director reviews this doc and confirms the Option A allocation (or proposes alternative).
- [ ] Founding team consents to the 3% → 1% trim (Director consults co-founders if any).
- [ ] Engineer modifies `pwm-team/infrastructure/agent-contracts/deploy/mainnet.js` to set:
  - Reserve multisig transfer = `2_730_000 ether`
  - Liquidity wallet transfer = `840_000 ether`
  - Founding team vesting deposit = `210_000 ether`
  - (Mining pool stays at `17_220_000 ether` — comes from `PWMMinting.M_POOL` constant, not from a transfer)
- [ ] Engineer adds a deploy-time assertion: `require(reserveTransfer + liquidityTransfer + teamTransfer + M_POOL == 21_000_000 ether)` to prevent any future accidental drift.
- [ ] Engineer rebroadcasts `deploy/mainnet.js` against Sepolia first as a dry-run to verify the new amounts land in the right wallets.
- [ ] Director re-signs the audit-clean attestation with the new allocation table (the contract bytecode is unchanged so the audit still applies, but the deployment record should reflect the new initial state).
- [ ] `addresses.json` is updated to show the new allocation in the deployment record.
- [ ] Mainnet deploy proceeds (Step 7) with the new allocation.

After mainnet deploy:

- [ ] At v2 add-on deploy (Phase 2), settlement service is configured so that the 50% multiplier withholding from `data_driven_statistical` payouts routes to the Reserve multisig wallet instead of per-Principle `PWMTreasury`.

---

## Open questions for governance

1. **Exact split.** Is 13% / 4% / 1% the right shape, or should it be 12% / 5% / 1% (preserve full Liquidity), or 12% / 4% / 2% (preserve more of team allocation)? Director + co-founders to confirm before deploy.

2. **Reserve sub-pools.** Should the 13% Reserve be sub-divided at deploy time into named buckets (e.g., "Reserve - v1 infrastructure 8%", "Reserve - v2/v3 future 5%") or kept as a single pool and allocated by governance vote case-by-case? Recommendation: single pool — simpler governance, less constraint on future flexibility.

3. **Founding-team trim politics.** Does the 3% → 1% cut require unanimous founder consent, or can it be set unilaterally by Director (since Director is the only on-record founder so far per the corporate-entity memory)? Likely unilateral but worth confirming.

4. **Mechanism 2/4 (`PWMStaking` / `PWMReward` modifications).** Are these worth doing in a v1.1 audit cycle before mainnet, or is the Option A + mechanism 1 combination sufficient? Recommendation: defer — Option A buys 2-3 years of runway; mechanisms 2/4 can come in a planned V2 contract suite alongside v3.

5. **Liability if v2/v3 doesn't ship.** If Director rebalances Reserve to 13% expecting v2/v3 funding, and v2/v3 is never built, the extra 3% sits unused. Counter-argument: the same 3% would also sit unused if it stayed in Liquidity (where POL just earns trading fees) or in Team (where it would slow-vest to founders). The risk profile is similar; Reserve at minimum gives optionality.

---

## Decision log

| Date | Decision |
|---|---|
| 2026-04-29 | Director asked whether Reserve should grow for v2/v3 and whether v1 can still be modified. This doc captures the analysis and recommends Option A (rebalance to 13% pre-mainnet) + Option B mechanism 1 (route v2 withholdings to Reserve). |
| _TBD_ | Director confirms or modifies the Option A allocation table. |
| _TBD_ | Engineer modifies `deploy/mainnet.js` and dry-runs against Sepolia. |
| _TBD_ | Founding team consents to the 3% → 1% trim. |
| _TBD_ | Mainnet deploy executed with the new allocation (point of no return). |
| _TBD_ | At v2 deploy, settlement service routes 50% withholding to Reserve. |

---

## Summary table

| Question | Answer |
|---|---|
| Can the v1 Reserve allocation be modified now? | **Yes**, until Base mainnet `deploy/mainnet.js` runs. The Reserve is a deploy-time transfer, not a contract-enforced bucket. |
| Will it be modifiable after mainnet deploy? | **No.** The 21M total supply, the 82% Mining pool constant, and the initial token transfers all freeze at that moment. |
| Does v1 Reserve cover v2/v3 costs? | **Probably not.** v1 was sized for 1.01M PWM in pre-launch bounties + ongoing v1 ops. The first 2 years of v2/v3 burn alone is ~2M PWM. |
| Recommended fix? | **Rebalance pre-mainnet to ~13% Reserve** by trimming Liquidity 5%→4% and Founding-team 3%→1%. **Plus** route v2's 50% statistical-payout withholding to Reserve (no contract change). |
| Cost of executing the recommended fix? | ~30 minutes of Director + engineer time. **No contract changes. No re-audit.** |
| Cost of NOT executing it (and finding out in 2 years)? | Reserve runs dry mid-v2 rollout; auto-verifier can't be funded; per-domain committees can't be paid; protocol's analytical-rigor brand erodes because new Principles can't be reviewed. |

The recommended fix is asymmetric: cheap to execute now, impossible to execute later, and the downside of not executing it is operationally severe. **Do it before Step 7.**
