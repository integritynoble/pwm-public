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

For each of the 5 signers, complete before deploy. Cross off items
as each signer hits them; the file is the source of truth.

### Signer #1 (Director — Hardware #1)
- [ ] Hardware wallet acquired and initialized fresh (not re-used)
- [ ] Recovery seed stored in 2 geographically separated locations
- [ ] Derived address #0 on path `m/44'/60'/0'/0/0` and verified on the
      device's own screen (NOT just the desktop app)
- [ ] Address recorded in the table above
- [ ] Self-sent ≥ 1 tx on Base Sepolia (any value, even 0 wei) —
      records the tx hash in your local notes for proof-of-custody
- [ ] `python scripts/proof_of_custody.py <signer-1-address>` exits 0

### Signer #2 (Director — Hardware #2, off-site backup)
- [ ] Hardware wallet acquired and initialized fresh
- [ ] Recovery seed stored in 2 separate locations from Signer #1's seed
- [ ] Derived address #0; verified on-device
- [ ] Address recorded in the table above
- [ ] Self-sent ≥ 1 tx on Base Sepolia
- [ ] `python scripts/proof_of_custody.py <signer-2-address>` exits 0

### Signer #3 (Trusted technical collaborator)
- [ ] Identity confirmed (Director knows this person and has high
      confidence in their long-term availability + key custody)
- [ ] Hardware wallet acquired
- [ ] Address derived + verified on-device + recorded in the table above
- [ ] Self-sent ≥ 1 tx on Base Sepolia
- [ ] Emergency contact info recorded out-of-band
- [ ] `python scripts/proof_of_custody.py <signer-3-address>` exits 0

### Signer #4 (Second trusted collaborator)
- [ ] Identity confirmed
- [ ] Hardware wallet acquired
- [ ] Address derived + verified + recorded
- [ ] Self-sent ≥ 1 tx on Base Sepolia
- [ ] Emergency contact info recorded out-of-band
- [ ] `python scripts/proof_of_custody.py <signer-4-address>` exits 0

### Signer #5 (Cold-storage backup)
- [ ] Hardware/paper wallet generated air-gapped
- [ ] Recovery material physically secured (safe-deposit box / fire-rated home safe)
- [ ] Address recorded in the table above
- [ ] Self-sent ≥ 1 tx on Base Sepolia (single touchpoint to confirm
      the key works; then return device to cold storage)
- [ ] `python scripts/proof_of_custody.py <signer-5-address>` exits 0

### Final verification (Director runs after all 5 signers complete)
- [ ] All 5 addresses populated in the table above (no `0x____` placeholders)
- [ ] `python scripts/verify_signers_md.py` exits 0 — confirms 5
      addresses, none equals deployer/testnet-founder, all have
      proof-of-custody on Base Sepolia
- [ ] Director commits + pushes the populated `signers.md`
- [ ] CPU commits `STEP_6__founder-roster-locked.READY.json`

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
