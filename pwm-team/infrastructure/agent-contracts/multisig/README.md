# PWM mainnet multisig admin keys

**Date:** 2026-04-28
**Owner:** Director
**Audience:** Director + agents managing the mainnet admin path
**Status:** scaffold; signer addresses are placeholders pending hardware-wallet setup

---

## Architecture

PWM does **not** use a Gnosis Safe for protocol admin. Instead, admin
flows through `PWMGovernance.sol` — a built-in 3-of-5 multisig over 5
founder wallets, with a 48-hour time-lock and a one-way `activateDAO()`
switch that promotes governance to a real DAO post-M3.

```
                  PWMGovernance
                      │  (3-of-5 multisig over 5 founder wallets,
                      │   48 h time-lock, activateDAO() flips to DAO)
                      ▼
       ┌──────────────┼───────────────┬──────────────┬──────────────┐
       │              │               │              │              │
       ▼              ▼               ▼              ▼              ▼
  PWMTreasury    PWMReward       PWMStaking    PWMCertificate   PWMMinting
   (governance)  (governance)    (governance)  (governance)    (governance)

  PWMRegistry — no governance (write-once, anyone can register())
```

So the question "do the admin keys belong to a multisig?" has two parts:

1. **Are the 5 founder wallets in PWMGovernance the right multisig?**
   At deploy, PWMGovernance's `founders[5]` array is locked forever
   (or until DAO activation). For mainnet readiness, the 5 addresses
   passed to `PWMGovernance` constructor must be the canonical
   long-term governance keys — typically hardware wallets, not
   the deployer's hot wallet that produced the testnet deploy.

2. **Do all 5 admin contracts (Treasury, Reward, Staking,
   Certificate, Minting) actually have `governance() ==
   PWMGovernance.address`?** This is what the Stream-5 exit signal
   #2 verifies. Run `scripts/verify_governance_owns_admin.js` (this
   directory) to check.

## Files in this directory

| File | Purpose |
|---|---|
| `README.md` | This doc — architecture + procedure |
| `signers.md` | Names and hardware-wallet metadata for the 5 founder signers (filled in by Director) |
| `governance.json` | Canonical PWMGovernance address per network (testnet, baseSepolia, base) |

Companion scripts (in `../scripts/`):

| Script | Purpose |
|---|---|
| `verify_governance_owns_admin.js` | Asserts every admin contract's `governance()` returns PWMGovernance.address. Run before mainnet announcement. |
| `transfer_admin_to_governance.js` | Idempotent helper: calls `setGovernance(PWMGovernance.address)` on each admin contract that doesn't already point there. Useful if a migration is needed. |

## Stream-5 readiness checklist

| Item | How to verify |
|---|---|
| 1. PWMGovernance exists on mainnet | `addresses.json[base].PWMGovernance` is non-null |
| 2. PWMGovernance.founders are the canonical 5 | Read on-chain `founders(0..4)` and compare against `signers.md` hardware-wallet addresses |
| 3. All 5 admin contracts point at PWMGovernance | `npx hardhat run scripts/verify_governance_owns_admin.js --network base` exits 0 |
| 4. None of the 5 admin contracts still point at deployer hot wallet | Same script also fails if any `governance()` ≠ PWMGovernance |
| 5. Each founder wallet is hardware-backed | Manual confirmation per `signers.md` |

## Migration: deployer hot key → founder hardware wallets

If the L2 deploy was done from a single hot wallet (typical for
Sepolia rehearsals), and that same address was passed in as one of
the 5 founders, you have two options:

**Option A (recommended) — re-deploy PWMGovernance with the right founders.**
Re-run `npx hardhat run deploy/l2.js --network base` after editing
the founder list in `deploy/testnet.js` (or whichever script the L2
deploy resolves through). Then run
`scripts/transfer_admin_to_governance.js` to update all 5 admin
contracts to point at the new PWMGovernance.

**Option B — accept the deployer as one of the 5 founders + rotate later.**
Activate a parameter proposal that extends governance via a
controlled migration path. More complex; only do this if Option A
is not viable for your already-live testnet.

For the Base mainnet deploy itself, **Option A is the only safe
path**: pass the 5 hardware-wallet addresses to PWMGovernance at
construction time. This is set-once per the contract's constructor.

## Deployer funding (Step 7)

Mainnet deploy gas fees come from the **deployer wallet** — the same
private key used for the Sepolia testnet deploy
(`addresses.json[testnet].deployer`). It must hold ≥ 0.012 ETH on
**Base L2 mainnet** before runbook step 1 of the mainnet deploy day.

Actual estimated cost is ~$0.04 of Base gas; the 0.012-ETH (~$30 at
$2500/ETH) recommendation includes a 1000× safety buffer for gas
spikes during congestion. Recommended actual transfer: **~$50 worth**
(roughly 0.02 ETH at current price) to absorb both gas spikes and
follow-on admin transactions.

Funding flow:

1. Buy ~$50 of ETH on Coinbase / Kraken / similar exchange.
2. If bought as L1 (Ethereum mainnet) ETH:
   - Bridge to Base via [https://bridge.base.org/](https://bridge.base.org/)
     (Base's official canonical bridge).
   - L1 gas to bridge: ~$1. Bridge time: 10-15 minutes.
3. If bought directly on Base (Coinbase Wallet / similar): skip step 2.
4. Send the resulting Base ETH to the deployer address (read from
   `addresses.json[testnet].deployer`).
5. Verify with:
   ```
   python scripts/check_deployer_balance.py --network base
   ```
   Exit 0 + "OK" line = ready to deploy.

This script also reports USD-equivalent via CoinGecko so the
funding amount is easy to sanity-check.

---

## Hardware-wallet setup recommendation

Per the Stream-4 row in `MAINNET_DEPLOY_PLAN.md`, threshold 3-of-5
means any 2-key loss is non-fatal. Suggested signer composition:

| # | Wallet type | Holder | Storage |
|---|---|---|---|
| 1 | Hardware (Ledger / Trezor #1) | Director | Primary device, daily handling |
| 2 | Hardware (Ledger / Trezor #2) | Director | Off-site backup, different brand than #1 |
| 3 | Hardware | Trusted technical co-founder | Their primary device |
| 4 | Hardware | Second trusted collaborator | Their primary device |
| 5 | Cold-storage backup (paper / air-gapped device) | Locked in safe | Emergency-only key |

After deploy, every signer's address gets recorded in `signers.md`
with checksum, key-derivation path, and emergency contact info
(NOT private keys — those never leave the hardware device).
