# PWM mainnet PWMGovernance founder signers

**Status:** TEMPLATE — fill in actual hardware-wallet addresses
before deploying PWMGovernance to Base mainnet.
**Threshold:** 3 of 5 (per `PWMGovernance.sol` constant
`REQUIRED_APPROVALS = 3`).
**Time-lock:** 48 hours per parameter change.

> **WARNING:** Do **not** put private keys, mnemonics, or seed
> phrases in this file. Only checksummed addresses + metadata.

## The 5 mainnet founder signers

| # | Address (checksummed) | Holder | Wallet type | Derivation path | Notes |
|---|---|---|---|---|---|
| 1 | `0x____________________________________________` | Director (Yang) | Ledger Nano X | `m/44'/60'/0'/0/0` | Primary daily-use device |
| 2 | `0x____________________________________________` | Director (Yang) | Trezor Model T (off-site backup) | `m/44'/60'/0'/0/0` | Different brand than #1 to avoid single-vendor risk |
| 3 | `0x____________________________________________` | Trusted technical collaborator (TBD) | Ledger / Trezor | `m/44'/60'/0'/0/0` | |
| 4 | `0x____________________________________________` | Second trusted collaborator (TBD) | Ledger / Trezor | `m/44'/60'/0'/0/0` | |
| 5 | `0x____________________________________________` | Cold-storage backup | Air-gapped / paper | `m/44'/60'/0'/0/0` | Emergency-only — locked in safe |

## Onboarding checklist (per signer)

For each of the 5 signers, complete before deploy:

- [ ] Hardware wallet acquired and initialized fresh (not re-used)
- [ ] Recovery seed stored in 2 geographically separated locations
- [ ] Address verified on-device (display matches address recorded above)
- [ ] $0.10 of test ETH sent + signed back (proves device works end-to-end)
- [ ] Emergency contact info (in case signer becomes unreachable) recorded out-of-band

## Emergency procedures

| Scenario | Action |
|---|---|
| One device lost / stolen | 3-of-5 still works (2 keys to spare). Flag in incident log; rotate later via DAO activation if/when DAO is live. |
| Two devices lost / stolen | 3-of-5 still works (1 key to spare). Treat as critical; pause non-essential governance ops. |
| Three or more devices lost | Multisig is broken; cannot pass any new proposal. Existing protocol state is unaffected (contract bytecode is immutable; storage is what it is). Plan: defer all governance changes; communicate publicly; build path to redeployment if catastrophic. |
| Director loses 2 personal devices simultaneously | Use signer #5 (cold-storage backup) + 1 collaborator's device + ... actually 2 collaborator devices is enough. No emergency action needed on day-of. |
| Discovered key compromise (signer suspects key exposed) | Immediately propose + execute a parameter change that locks affected operations; transition to DAO if multisig integrity is compromised. |

## Setting these addresses at deploy

The `PWMGovernance` constructor takes
`address[NUM_FOUNDERS] memory _founders`. The mainnet deploy chain:

1. `npx hardhat run deploy/mainnet.js --network base` — entry point
2. → `deploy/testnet.js main()` — does the actual work
3. → reads founders from `deploy/testnet.js` (currently hardcoded; the
   mainnet equivalent should read from `multisig/signers.md` or an
   env var like `PWM_MAINNET_FOUNDERS`)

Before mainnet day:
- Update `deploy/testnet.js` (or its mainnet branch) to use the 5
  addresses from this file.
- Run `npx hardhat run deploy/l2.js --network baseSepolia` from these
  addresses as a rehearsal.
- Then run mainnet deploy with `PWM_MAINNET_CONFIRM=1`.

## Decision log

| Date | Decision |
|---|---|
| 2026-04-28 | Template created. Five founder addresses still placeholders. |
| _TBD_ | Director acquires hardware wallets #1 and #2 |
| _TBD_ | Trusted collaborator #3 onboarded |
| _TBD_ | Trusted collaborator #4 onboarded |
| _TBD_ | Cold-storage signer #5 set up |
| _TBD_ | All 5 addresses updated in this file + deploy script |
| _TBD_ | Base Sepolia rehearsal deploy with the 5 addresses |
| _TBD_ | Base mainnet deploy with the 5 addresses |
