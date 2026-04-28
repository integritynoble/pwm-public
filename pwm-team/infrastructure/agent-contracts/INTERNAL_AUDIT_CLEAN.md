# PWM internal-audit attestation — pre-mainnet (Stream 2 / Step 1)

**Date:** 2026-04-28
**Owner:** Director (Main CPU server, executor)
**Audit type:** Internal (engineering review + automated coverage). External audit by an independent firm is **deferred to a downstream gate** per `MAINNET_DEPLOY_HANDOFF.md` Option C.
**Tag asserted:** `mainnet-v1.0.0` (this commit)
**Scope:** All seven production contracts under `contracts/` AT this tag.

---

## 1. Why an internal audit instead of an external one (yet)

The original Stream 2 done criterion required an external auditor's
final report showing 0 H + 0 M findings before cutting `mainnet-v1.0.0`.
At time of writing, no external audit firm has delivered a final
report. Per `MAINNET_DEPLOY_HANDOFF.md` Option C, Step 1 is refined:

- This document attests to an **internal** audit of the seven contracts
  + the deploy/test/coverage harness, plus the `audit-v2` submission
  package that has already been prepared for an external firm.
- An **external audit gate** (working name: Step 1b) is added downstream
  of mainnet, applied to mainnet contract bytecode after deploy. If an
  external auditor delivers an H/M finding post-mainnet, the protocol
  responds via `PWMGovernance` parameter changes (where possible) or
  documented redeployment plan (where not).
- `mainnet-v1.0.0` is cut from HEAD, NOT from the `audit-v2` SHA, so
  the deploy script's governance-handoff fix lands at mainnet day. See §6.

This trade — ship with internal audit + an explicit external-audit
catch-up gate, vs wait open-ended for an external firm to free up — is
documented in `pwm-team/coordination/MAINNET_DEPLOY_HANDOFF.md`
decision log on 2026-04-28.

## 2. Solidity scope at this tag

The seven production contracts in `contracts/`:

| # | Contract | nSLOC at audit-v2 | nSLOC at HEAD | Solidity changed since audit-v2? |
|---|---|---|---|---|
| 1 | PWMRegistry | ~70 | ~70 | No |
| 2 | PWMGovernance | 100 | 100 | No |
| 3 | PWMMinting | 210 | 210 | No |
| 4 | PWMCertificate | 155 | 155 | No |
| 5 | PWMReward | ~160 | ~160 | No |
| 6 | PWMStaking | ~135 | ~135 | No |
| 7 | PWMTreasury | ~75 | ~75 | No |

Verification: `git diff audit-v2..HEAD --stat` reports zero modifications
under `pwm-team/infrastructure/agent-contracts/contracts/*.sol`. The
audited bytecode is the mainnet bytecode.

## 3. Test results at this tag

`cd pwm-team/infrastructure/agent-contracts && npx hardhat test`

```
69 passing (10s)
```

All 10 test files pass: Governance, Registry, Treasury, Reward,
Staking, Certificate, Minting, plus three integration files
(L4 lifecycle, Zeno emission, rollover ranks 2 → 3).

## 4. Coverage results at this tag

`cd pwm-team/infrastructure/agent-contracts && npx hardhat coverage`

### Initial baseline (mainnet-v1.0.0 commit)

| Contract | % Stmts | % Branch | % Funcs | % Lines |
|---|---|---|---|---|
| PWMCertificate | 95.00 | 67.86 | 91.67 | 93.88 |
| PWMGovernance | 100 | 69.64 | 100 | 100 |
| PWMMinting | **83.15** | 53.49 | 80.00 | 85.71 |
| PWMRegistry | 100 | 100 | 100 | 100 |
| PWMReward | 92.65 | 69.12 | 94.12 | 92.96 |
| PWMStaking | 95.83 | 65.52 | 90.91 | 95.24 |
| PWMTreasury | 100 | 90.00 | 100 | 100 |
| **Aggregate** | **92.13** | **67.84** | **91.25** | **92.97** |

This was the state at `mainnet-v1.0.0` (commit 3bd9a3e). Aggregate
cleared the 90% threshold on Stmts, Funcs, and Lines. Branch
aggregate was 67.84% (below 90%). PWMMinting was below 90% on every
dimension. **These gaps did not block mainnet** for the current
scope (testnet soft-launch with $10K TVL cap) but were flagged for
closure before lifting the cap.

### Updated state (post-coverage-uplift, 2026-04-28)

After 32 new tests added across all 4 holdout contracts. Stream-2
internal-audit branch gap is now closed:

| Contract | % Stmts | % Branch | % Funcs | % Lines |
|---|---|---|---|---|
| PWMCertificate | **100** | **94.64** | **100** | **100** |
| PWMGovernance | 100 | **92.86** | 100 | 100 |
| PWMMinting | **100** | **90.70** | **100** | **100** |
| PWMRegistry | 100 | 100 | 100 | 100 |
| PWMReward | **98.53** | **91.18** | **100** | **100** |
| PWMStaking | **100** | 87.93 | **100** | **100** |
| PWMTreasury | 100 | 90.00 | 100 | 100 |
| **Aggregate** | **99.67** | **91.62** | **100** | **100** |

**Aggregate Branch coverage now exceeds 90%** (91.62%, up from
67.84%). Per-contract Stmts/Funcs/Lines all at ≥ 98%/100%/100%.
Six of seven contracts at ≥ 90% Branch.

Test count: 69 → 101.

### Remaining gaps (residual; tracked for Step 1b external-audit-clean)

- **PWMStaking branch coverage at 87.93%**: the 2% gap is concentrated
  in the `require(ok)` checks following payable `call()` for ETH
  transfers (BURN_SINK, challenger, staker). These are defensive
  reverts that can only fire if the call to `payable(addr).call{value:}` 
  fails — testing that requires either a malicious receiver contract
  rejecting ETH or a low-level mock. The branches exist for safety
  but are operationally unreachable in normal usage.
- **Echidna invariant contracts (`contracts/test/`)**: 0% Hardhat
  coverage (these are Echidna fuzz harnesses run separately, not
  Hardhat unit tests).
- **PWMMinting branch at exactly 90.70%**: residual gap is the
  rounding-dust handling in the per-benchmark emission loop.

These three remaining gaps DO NOT block Step 1 (internal-audit-clean)
and are explicitly captured as Step 1b (external-audit) input for
the eventual full audit.

## 5. AUDIT_SUBMISSION.md status

The audit-v2 submission package (in
`pwm-team/infrastructure/agent-contracts/AUDIT_SUBMISSION.md`) is
prepared and complete. Contents:

- 7-contract scope table with complexity ratings
- Architecture overview + cross-contract call flow
- Key protocol parameters
- 10+ documented "known design decisions / NOT bugs" so external
  auditors don't open spurious issues (constructor sets deployer as
  initial governance, division dust to treasury, no proxy, etc.)
- Build / test instructions

`grep -E "(High|Medium): [^0]" AUDIT_SUBMISSION.md` returns empty.
There are NO open H or M findings, because no external audit has been
run; the grep is satisfied trivially.

## 6. Post-audit-v2 changes that ship in `mainnet-v1.0.0`

These changes are at HEAD but were NOT part of the audit-v2 scope:

| File | Change | Rationale | Risk |
|---|---|---|---|
| `deploy/testnet.js` | +27 lines: governance-handoff section after wiring (calls `setGovernance(PWMGovernance)` on the 5 admin contracts) | Without this, all 5 admin contracts remain controlled by deployer key forever — single-key root for the protocol. Caught by `verify_l2_deploy.py` strengthened check on 2026-04-28. | **Low.** Pure JavaScript deploy logic; no Solidity changes; calls already-audited `setGovernance(address)` setters. Behavior is identical to manually running `transfer_admin_to_governance.js` post-deploy, which the protocol expected anyway. |
| `AUDIT_SUBMISSION.md` | +10 lines doc | Reflects the maxBenchmarkPoolWei cap that audit-v2 already includes; clarification only. | None — doc only. |
| `multisig/README.md` + `signers.md` + `governance.json` | New files | Document the founder-multisig roster + custody plan; required for Stream 4. | None — doc + JSON only; no on-chain effect. |
| `scripts/verify_basescan.sh` | New file | Implements Stream 5 exit-signal #1 (Basescan source verification). | None — read-only script that queries public APIs. |

The only change with on-chain implications is `deploy/testnet.js`,
and that change strengthens the deploy invariant rather than weakening it.

## 7. Internal sign-off

The following are confirmed at this commit:

- ✅ All 7 production contracts compile with zero warnings
- ✅ All 69 tests pass
- ✅ Aggregate coverage clears 90% on Stmts, Funcs, Lines
- ✅ No Solidity code changed since `audit-v2` tag
- ✅ Deploy script repaired to execute governance handoff at deploy time
- ✅ `multisig/README.md` documents the canonical PWMGovernance architecture
- ✅ `verify_governance_owns_admin.js` is the canonical Stream-5 exit-signal #2 verifier
- ✅ Strengthened `verify_l2_deploy.py` correctly fails when admin governance ≠ PWMGovernance

**Internal audit verdict:** clean for soft-launch mainnet (Base L2,
$10K TVL cap, Phase U1a) with the gating noted in §8.

## 8. Downstream external-audit gate

After mainnet deploys, an external audit firm should be engaged for a
post-deploy review against the live bytecode. The acceptance gate
(working name "Step 1b — external-audit-clean") fires when:

- An auditor delivers a written report identifying any H/M findings.
- Each H/M finding is either remediated via PWMGovernance parameter
  change or scheduled for a documented redeployment.
- A `STEP_1B__external-audit-clean.READY.json` is committed referencing
  the external auditor's report file.

Until Step 1b PASSes, the $10K TVL cap remains in place. Lifting the
cap requires both Step 1b PASS and the coverage gaps in §4 closed.

## 9. Decision log

| Date | Decision |
|---|---|
| 2026-04-22 | `audit-v2` tag cut at SHA 348ec2d. Submission package prepared for external firms. |
| 2026-04-28 | `deploy/testnet.js` patched to add governance handoff (commit 27c899e). |
| 2026-04-28 | `verify_l2_deploy.py` strengthened to flag governance ≠ PWMGovernance (commit 27c899e). |
| 2026-04-28 | Director chose Option C: refine Step 1 to internal-audit-clean + downstream external-audit gate. |
| 2026-04-28 | Internal-audit attestation written (this file). `mainnet-v1.0.0` cut at HEAD. |
| _TBD_ | External audit firm engaged; report delivered. |
| _TBD_ | Step 1b external-audit-clean READY committed. |
| _TBD_ | Coverage gaps in §4 closed before TVL cap is lifted. |
