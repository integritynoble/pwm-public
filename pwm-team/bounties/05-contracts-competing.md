# Bounty 5 — Smart Contract Suite (Competing Implementation)

- **Amount:** 500,000 PWM
- **Opens:** at Phase 1 sign-off (~Day 30)
- **Reference implementation:** `infrastructure/agent-contracts/contracts/`
  (7 contracts, 53-test suite, deployed on Sepolia)
- **Acceptance harness:** `infrastructure/agent-contracts/test/` (Hardhat)

## What you build

An independent reimplementation of the 7 PWM core contracts. Same ABI, same
economic semantics, different codebase. The purpose is diversification: a
second implementation that passes the same tests insulates the protocol
against bugs in any one codebase. Historical precedent:
Ethereum L1 running Geth + Nethermind + Erigon + Besu + Reth.

This is the largest single bounty in the program. It is also the most
rigorous: the acceptance bar is "passes the complete test suite unchanged
plus three audits by independent firms."

## The seven contracts

| Contract | Responsibility (full spec: `infrastructure/agent-contracts/CLAUDE.md`) |
|---|---|
| `PWMRegistry` | Append-only artifact store, L1/L2/L3/L4 with parent validation |
| `PWMMinting` | Zeno per-event emission; `A_k = (M_POOL − M_emitted) × w_k / Σw_j`; per-benchmark sub-split `A_{k,j,b}` |
| `PWMStaking` | Fixed-PWM stakes (L1=10, L2=2, L3=1; tunable). Graduation 50/50 return+B-pool; challenge/fraud slashing |
| `PWMCertificate` | Submit / challenge (7-day, or 14-day if δ≥10) / finalize. Dispatches distribute + mintFor |
| `PWMReward` | Ranked draw (R1=40%, R2=5%, R3=2%, R4-10=1%, R11+=rollover). Split AC×p×55% / CP×(1-p)×55% / L3=15% / L2=10% / L1=5% / T_k=15% |
| `PWMTreasury` | Per-principle T_k. M4 adversarial bounty capped at 50% of T_k |
| `PWMGovernance` | 3-of-5 multisig, 48h timelock on setParameter, one-way activateDAO |

Read `pwm_overview1.md` §Pool Allocation, §Smart Contracts, and CLAUDE.md
for the exact semantics. Disagreement with pwm_overview1.md is grounds for
rejection — that document is canonical.

## Interface contract

- **ABIs must match** — `interfaces/contracts_abi/*.json`. Function
  signatures, event signatures, and revert strings identical.
- **Storage layout does NOT need to match** — you may rearrange internal
  storage, use structs differently, add auxiliary caches.
- **No additional public functions** that are not equivalent to existing ones.
  Extra admin escape hatches are a rejection.

## What must pass

1. **Full Hardhat test suite**, 53 tests verbatim, running against your
   contracts:
   ```bash
   cd infrastructure/agent-contracts
   CONTRACTS_UNDER_TEST=<your-dir> npx hardhat test
   ```
   All 53 pass. Adding more tests is welcome; removing or skipping any is
   rejection.

2. **Identical event emission.** Every emitted event (name, indexed fields,
   values) must match the reference for the same inputs. Shadow-run diffing
   will surface any divergence.

3. **Two independent audits.** You commission audits from two firms on a
   published allowlist (agent-coord publishes the list 48h before bounty
   opens). Audits must find zero Critical or High issues. Medium / Low /
   Informational findings are allowed if they are fixed in a subsequent PR
   the same firm re-audits.

4. **Gas parity ±10%.** Per-function gas must not exceed reference
   implementation by more than 10%. A gas-report diff is part of the PR.

5. **Deployment script provided.** Your repo ships a working `deploy/` that
   stands up all 7 contracts on a fresh Sepolia network, wires the cross-
   contract addresses, and emits the same final state the reference emits.

6. **90-day shadow run.** Longer than other bounties because money is at
   stake. Your contracts receive every finalized certificate that hits the
   reference; we compare event streams. Any economic divergence (wrong
   payout amounts, wrong splits, wrong M_emitted) voids the award.

## What you may change

- Language: Solidity reference (0.8.24). Vyper, Huff, Yul submissions welcome
  if the ABI is identical and the tests pass.
- Internal algorithms: e.g., weight caching strategies, storage patterns,
  iteration bounds.
- Dependencies: OpenZeppelin, Solmate, or bare implementations all acceptable.
- Gas optimizations: encouraged, subject to the ±10% parity rule on the upper
  bound (lower is fine).

## What you may not change

- External ABI (function signatures, event signatures).
- The emission formula (`A_k`, `A_{k,j,b}`, rank percentages, split
  percentages, challenge window durations, share ratio p bounds).
- Access control logic (who can call what) — see CLAUDE.md §Access Control.
- The `M_POOL = 17_220_000 × 10^18` constant.

## Submission process

1. Open a GitHub Discussion: `[BOUNTY-5] claim intent — <team>` listing
   language, team, expected delivery.
2. Fork the repo. Put your implementation under
   `infrastructure/agent-contracts-alt-<team>/`.
3. Run the reference test suite against your contracts.
4. Commission both audits — audit scope must include all 7 contracts and
   the cross-contract wiring. Publish audit reports as markdown in your
   fork's `audits/` folder.
5. Deploy to Sepolia; add your addresses to `addresses-alt-<team>.json`.
6. Open a PR titled `[BOUNTY-5] <team> submission` with: source, tests
   passing, audit reports, Sepolia addresses.
7. agent-coord runs the reference suite + checks ABI identity + samples gas.
8. 90-day shadow run begins.
9. On clean shadow run, 500,000 PWM released to wallet in PR description.

## Payment

- Paid from Reserve (largest single Reserve allocation).
- Audit costs borne by the submitter; there is no reimbursement budget.
  (Typical audit cost for 7 contracts of this complexity: $40k–$120k USD at
  current market rates. The bounty is sized to cover this plus compensate
  for build time.)
- Wallet listed in PR description.
- Mainnet swap 1:1 at Phase 2.
