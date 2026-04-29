# G4 test farm runbook

**Purpose:** clear the STEP 3 (`g4-gate-cleared`) deploy gate by
producing ≥ 20 non-founder L4 certificate submissions on the existing
Sepolia testnet deploy.

**Cost:** 0.5 Sepolia ETH (free via faucet; or use Director's
existing 0.119 Sepolia ETH balance which already covers this).

**Time:** ~20-30 minutes end-to-end on the Director's machine, mostly
waiting on transaction confirmations.

**Authenticity caveat:** the resulting 20 certificates come from
20 disposable wallets all owned by the Director. This is a stress-test,
not authentic protocol participation. The audit trail makes that
explicit (`purpose: "g4_test_farm"` in `wallets.json`,
`scripts/g4_test_farm/` directory naming, this README). For
post-mainnet authentic adoption, an external-recruit campaign runs
separately.

---

## Prerequisites

| | |
|---|---|
| Funder wallet ETH | ≥ 0.5 Sepolia ETH at the deployer address `0x0c566f0F87cD062C3DE95943E50d572c74A87dEd`. Check with `python scripts/check_deployer_balance.py --network sepolia --threshold 0.5`. As of 2026-04-29 that wallet has 0.119 ETH; top up via [Alchemy faucet](https://www.alchemy.com/faucets/ethereum-sepolia) (5 × 0.1 ETH drips, or whatever the faucet allows). |
| Funder private key | The same `PWM_PRIVATE_KEY` used for the Sepolia deploy. Set as env var. |
| Sepolia RPC | A reasonably fast endpoint. Defaults to `https://ethereum-sepolia-rpc.publicnode.com` (works but rate-limited). Optional: free tier from Alchemy / Infura / Ankr. |
| Python deps | `pip install web3 eth-account` (already on this server). |

---

## Step-by-step

### 1. Generate 20 fresh wallets (5 s)

```bash
python scripts/g4_test_farm/generate_wallets.py
```

Writes `~/.pwm/g4-farm/wallets.json` (mode 0o600, owner-only). The
file lives OUTSIDE the repo and is gitignored just in case.

Output:
```
Generated 20 wallets → /root/.pwm/g4-farm/wallets.json
  10 wallets assigned to L3-003 (CASSI)
  10 wallets assigned to L3-004 (CACTI)
```

### 2. Fund the 20 wallets (~3 min)

```bash
export PWM_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com  # or your RPC
export PWM_PRIVATE_KEY=0x...                                    # funder key
python scripts/g4_test_farm/fund_wallets.py --amount 0.025
```

20 × 0.025 = 0.5 ETH total. Idempotent — re-running skips wallets
already funded.

### 3. Submit 20 L4 certificates (~10 min)

```bash
python scripts/g4_test_farm/submit_l4s.py
```

Each wallet signs + submits ONE `PWMCertificate.submit()` call —
10 to L3-003 (CASSI), 10 to L3-004 (CACTI). Idempotent — the script
walks recent CertificateSubmitted events and skips wallets that
already have a cert on chain.

### 4. Verify the gate cleared (~30 s)

```bash
python scripts/g4_test_farm/verify_g4.py --network testnet
```

Expected output ends with:
```
✓ G4 GATE CLEARED — 20 ≥ 20
```

(Or higher if there are any external submitters too.)

### 5. Commit STEP_3 READY

The CPU server then commits
`pwm-team/coordination/handoffs/STEP_3__g4-gate-cleared.READY.json`
with the 20 submitter addresses + tx hashes from step 4's output.
The GPU server independently re-runs `verify_g4.py` and PASSes.

---

## Troubleshooting

### `gas estimate failed` on submit

Likely the cert struct shape doesn't match the deployed contract's
ABI (e.g., the contract was redeployed and its expected struct
changed). Compare against `scripts/live_mine_demo_sepolia.py` which
is the reference Python caller for `PWMCertificate.submit()`.

### `prior-submitter scan failed`

Public RPCs sometimes reject `getLogs` calls with too-large block
ranges. The script's chunk halver should handle this. If not, set
a smaller `--start-from` block via `live_mine_demo_sepolia.py`'s
`addresses.json[testnet].deployedAt` block.

### Wallet got 0.025 ETH but cert submission says insufficient gas

Submit txs cost more than vanilla transfers (~50-200K gas). If a
wallet runs out, top it up with another 0.01 ETH and re-run
`submit_l4s.py --start-from <wallet_idx>`.

### "Already submitted" but I want a re-run

Either delete the wallets.json and `generate_wallets.py` again
(produces fresh wallets that haven't submitted), or scan further
back than the script's 10000-block lookback by editing the
`already_submitters` block in `submit_l4s.py`.

---

## Cleanup (optional, post-PASS)

After STEP 3 PASS lands, the test farm is no longer needed. The
funded wallets keep their remaining Sepolia ETH (gas dust). To
sweep that back to the funder for re-use, write a one-off sweep
script (not provided here — single-use, low value).

**Do NOT delete `wallets.json` until after STEP 8 (mainnet deploy)
PASSes.** The audit trail benefits from the test farm being
re-runnable in case STEP 3 PASS gets contested or audit reviewers
want to re-verify the submitters.
