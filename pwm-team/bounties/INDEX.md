# PWM Reserve Bounties

**Total:** ~1,238,000 PWM across 8 bounties (7 infrastructure + 1 content), paid
from the 2,100,000 PWM Reserve. External developers/authors compete against a
reference implementation (or, for Bounty #7, a reference content exemplar)
published by the PWM founding team; submissions must pass the reference test
harness or verifier-agent gates to qualify.

Published by: agent-coord
Last updated: **2026-05-01** (refreshed for 2026-04-29/30 v2/v3 expansion + 2026-04-30 coordination-docs polish; Bounty 7 wording updated for the 28 newly-authored v2/v3 anchors that became Tier A founder-authored polish at zero cost to the Bounty 7 pool)

> **Note on Reserve resizing (2026-04-30).** Director is considering a pre-mainnet rebalance of the Reserve from 10% (2.1M PWM) to 13% (2.73M PWM) per `pwm-team/pwm_product/genesis/PWM_RESERVE_RESIZING_FOR_V2_V3.md`. If approved, the bounty totals below stay the same (no per-bounty change), but the un-allocated Reserve pool increases by ~630K PWM. Decision pending Director sign-off as part of mainnet Step 7b.

## Status overview

| # | Bounty | PWM | Opens when | Reference impl | Status |
|---|---|---|---|---|---|
| 1 | [Scoring engine](01-scoring-engine.md)         | 200,000 | agent-scoring merged | `infrastructure/agent-scoring/pwm_scoring/` | **OPEN** — reference impl on main 2026-04-21 (81 tests pass) |
| 2 | [Web UI / Explorer](02-web-explorer.md)         |  80,000 | agent-web merged     | `infrastructure/agent-web/`                 | **OPEN** — reference impl on main 2026-04-21 (17 tests pass) |
| 3 | [pwm-node CLI](03-pwm-node-cli.md)              | 100,000 | agent-cli merged     | `infrastructure/agent-cli/pwm_node/`        | **OPEN** — reference impl on main 2026-04-21 (73 tests: 68 mocked + 5 opt-in e2e). Bounty acceptance procedure: `agent-cli/tests/e2e/README.md` |
| 4 | [Mining client (CP role)](04-mining-client.md)  |  80,000 | agent-miner merged   | `infrastructure/agent-miner/pwm_miner/`     | **OPEN** — reference impl on main 2026-04-21 (87 tests across all 6 modules). Bounty acceptance procedure: `agent-miner/tests/e2e/README.md` |
| 5 | [Contracts, competing impl](05-contracts-competing.md) | 500,000 | Phase 1 sign-off | `infrastructure/agent-contracts/contracts/` | SPEC PUBLISHED — opens Phase 1 sign-off |
| 6 | [IPFS benchmark pinning](06-ipfs-pinning.md)    |  50,000 | Phase 1 sign-off     | (no reference impl — SLA-driven)            | SPEC PUBLISHED — opens Phase 1 sign-off |
| 7 | [Genesis Principle Polish (tiered)](07-genesis-principle-polish.md) | ~168,000 | Phase 2 launch + 7 days | `cassi.md`/`cacti.md` + L1/L2/L3-003/004 JSON as exemplars | SPEC PUBLISHED — per-principle claim model; opens post-mainnet |
| 8 | [LLM-routed / NL matcher](08-llm-matcher.md)     |  60,000 | CASSI/CACTI §10.2.1 gate passes | `agent-cli` + `agent-web` faceted matcher (deterministic, LLM-free) | SPEC PUBLISHED — opens once CASSI/CACTI hit `TWO_ANCHOR_MVP_LOCKED` per `MVP_FIRST_STRATEGY.md` |

Bounties open **rolling**, not all at once. Infrastructure bounties (1-4) open
the day the reference implementation merges to `main`, so external developers
have a concrete harness to build against. Bounties 5 and 6 open at Phase 1
sign-off (~Day 30). **Bounty 7 is structurally different** — it's a per-principle
claim model (not one-PR-one-payout) opening at Phase 2 launch.

**Bounty 7 scope refreshed 2026-05-01.** The original 2026-04-23 framing
(2 done CASSI/CACTI + ~498 un-polished baseline) is updated for the
2026-04-29/30 v2/v3 expansion. New scope:
- **Tier A (founder-authored, no Bounty 7 cost): ~30 anchors** = CASSI + CACTI
  + 8 v3 standalone multi-physics medical imaging Principles (L1-503..L1-510)
  + 2 newly-authored analytical cores (L1-511 PillCam, L1-518 XRD)
  + 19 v2 PWDR Principles (L1-512..L1-517, L1-519..L1-531).
  These 30 are already at v2/v3 schema depth and don't consume Bounty 7 funds.
- **Tier B (anchors): ~15-20** at 2,000 PWM each — pool of next-round anchors
  Director hasn't yet picked from `PWM_V3_MEDICAL_IMAGING_CANDIDATES.md` or
  related candidate docs; 23 candidates remain after the 28 v2/v3 promoted.
- **Tier C (standard): ~200** at 500 PWM each — long-tail v1 baseline
  Principles awaiting external-author re-polishing.
- **Tier D (specialty): ~280** at 100 PWM each — niche / specialty
  Principles after Director's per-Principle removal review per
  `pwm-team/pwm_product/genesis/PWM_V1_REMOVAL_CANDIDATES.md` (currently
  139 of 502 baseline are flagged as Category A widefield-template fan-out
  artifacts; some subset may be removed before mainnet, freeing those slots).

Net Bounty 7 budget unchanged at ~168,000 PWM. Effective per-Principle
payouts within each tier remain stable (the σ-over-unclaimed formula).
The expansion is **net-positive for Bounty 7 economics:** more polished
anchors at launch, same budget for long-tail polish post-launch.

**Bounty 8 is the newest** (added 2026-04-23). It pairs with the PWM-native
reference matcher ("faceted floor") that ships as part of `agent-cli` and
`agent-web`: PWM intentionally does NOT host an LLM-routed matcher itself,
so Bounty 8 is third-party territory from day-one of its opening. Opens only
*after* CASSI + CACTI clear the §10.2.1 promotion gate in
`MVP_FIRST_STRATEGY.md` — publishing earlier would invite over-fitting to a
harness that only covers 2 anchors.

## Common acceptance structure

Every bounty follows the same evaluation path:

1. **Scope check** — submission implements the mandatory interface listed in
   the bounty spec. Anything off-spec is rejected at triage.
2. **Reference test suite** — submission must pass every test the founding
   team's reference implementation passes. Tests are in the reference's
   `tests/` directory and are the authoritative acceptance harness.
3. **Interface parity** — submission must be a drop-in replacement for the
   reference. The CLI calls the scoring engine as a library; if your scoring
   engine rewrite breaks the CLI, it fails.
4. **30-day shadow run** — accepted submissions run alongside the reference
   on testnet for 30 days. Any correctness or availability regressions surface
   here. Serious regressions void the award.
5. **Payment** — after the shadow run, PWM is released from Reserve escrow to
   the submission's designated wallet.

## Claiming a bounty

External developers follow this flow:

```
1. Read the bounty spec + the reference implementation's CLAUDE.md
2. Open a GitHub Discussion in integritynoble/pwm-public titled:
     "[BOUNTY-<N>] claim intent — <your team name>"
   listing intended tech stack + contact + estimated delivery
3. Fork the repo, build against the interface, open a PR titled:
     "[BOUNTY-<N>] <component> submission — <your team name>"
4. agent-coord runs the reference test suite against your PR
5. If tests pass, your PR enters the 30-day shadow run
6. On successful shadow run, agent-coord writes
     coordination/agent-coord/reviews/bounty-<N>.md with the approval
   and the multisig releases PWM to the wallet listed in your PR description
```

Multiple submissions per bounty are accepted. First qualifying submission
wins the full amount; later qualifying submissions receive runner-up rewards
only if the director opens them (not guaranteed).

## Security + IP

- All submissions must be MIT-licensed and publicly readable.
- Do not submit code that includes paid or closed-source dependencies
  unless they are free for research and commercial use without restriction.
- Bounty payment is in PWM (Sepolia testnet initially; mainnet PWM at launch).
- The PWM team does not collect equity, KYC, or personal data from bounty
  participants. Supply only the payout wallet.

## Questions

Open a GitHub Discussion under the `bounties` category in
`integritynoble/pwm-public`. agent-coord triages within 72h.
