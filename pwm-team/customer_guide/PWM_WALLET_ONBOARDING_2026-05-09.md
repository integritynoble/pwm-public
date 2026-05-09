# Wallet Onboarding — From Zero ETH to First Cert in ~15 Minutes

**Date:** 2026-05-09
**Audience:** First-time PWM miners, D5 recruit-campaign respondents
**Closes:** P1 row 3 of `PWM_PRELAUNCH_POLISH_PRIORITY_2026-05-08.md`

This is the absolute-minimum walkthrough for a non-founder reaching
their first L4 certificate on Sepolia testnet. Every step is
copy-pasteable; total wall time ≈ 15 minutes (most of it waiting for
the faucet to drip).

If you already have a funded Sepolia wallet, jump to **Step 4**.

---

## Step 1 — Generate a wallet (~30 s)

You need a 64-hex-character Ethereum private key. Three paths:

**Path A — Python (recommended for CI / scripts)**

```bash
python3 -c "
from eth_account import Account
import secrets
acct = Account.from_key('0x' + secrets.token_hex(32))
print(f'Address:     {acct.address}')
print(f'Private key: {acct.key.hex()}')
"
```

**Path B — Foundry**

```bash
cast wallet new
```

**Path C — MetaMask** (if you prefer a GUI):
1. Install MetaMask: https://metamask.io
2. Create a new wallet → write down the seed phrase
3. Switch network to **Sepolia testnet** (built-in)
4. Account icon → **Account Details** → **Show private key** → copy

You now have two strings: an **address** (`0x742d35…`, public — share
for funding) and a **private key** (`0xac0974…`, secret — never share,
never commit, never paste anywhere public).

> **⚠ Rules** (build the habit on testnet so it's automatic on mainnet):
> - Never commit the key to git
> - Never reuse a dev-machine env-var key on Base mainnet
> - The Sepolia key is throwaway-grade — generate a fresh one anytime
> - For Base mainnet: **hardware wallet only**, not an env var

---

## Step 2 — Fund from a faucet (~1-5 min)

Three Sepolia faucets that work as of 2026-05-09:

| Faucet | URL | Cap per request |
|---|---|---|
| Alchemy | https://www.alchemy.com/faucets/ethereum-sepolia | 0.5 Sepolia ETH (free, daily) |
| QuickNode | https://faucet.quicknode.com/ethereum/sepolia | 0.05 Sepolia ETH |
| publicnode | https://sepoliafaucet.com | 0.5 Sepolia ETH |

Paste your **address** (NOT private key — the public `0x742d35…` part)
into one of them. Solve the captcha. Wait 30-60 seconds.

A typical mining session uses ~0.001 Sepolia ETH; **0.05 ETH lasts a
long time** — most miners only ever need to use the faucet once.

**Verify the faucet drip arrived:**

```bash
curl -sX POST https://ethereum-sepolia-rpc.publicnode.com \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_getBalance","params":["0xYOUR_ADDR","latest"]}'

# Expected: a non-zero hex value, e.g. {"jsonrpc":"2.0","id":1,"result":"0x6f05b59d3b20000"}
# 0x6f05b59d3b20000 = 0.5 ETH; convert via cast --to-unit:
cast --to-unit 0x6f05b59d3b20000 ether    # → 0.500000000000000000
```

If the result is `"0x0"`, the faucet hasn't dripped yet — wait
another minute and re-curl.

---

## Step 3 — Set environment variables (~30 s)

```bash
export PWM_PRIVATE_KEY=0x<paste-the-64-hex-private-key-here>
export SEPOLIA_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
export PWM_RPC_URL=$SEPOLIA_RPC_URL
```

Do **not** add these to `.bashrc` / `.zshrc` — keep them session-local
so the key isn't sitting in plaintext in your home directory after
you stop mining.

---

## Step 4 — Install the CLI (~2 min)

```bash
git clone --recursive https://github.com/integritynoble/pwm-public.git
cd pwm-public

# Pull the LFS-pinned weights (only needed for deep-learning solvers
# like MST-L; CPU-only solvers don't need this step):
git lfs install
git -C public lfs pull

# Create a Python venv + install the CLI:
python3 -m venv .venv && source .venv/bin/activate
pip install -e pwm-team/infrastructure/agent-cli
```

Verify install:

```bash
pwm-node --version
# → pwm-node 0.1.0
```

---

## Step 5 — Browse the catalog (no chain interaction needed)

```bash
# What's mineable today?
pwm-node principles
# → 2 founder-vetted: CASSI L1-003, CACTI L1-004

# Inspect one:
pwm-node inspect L3-003
# → benchmark detail

# Find a benchmark for your problem:
pwm-node match "I have a hyperspectral inverse problem"
# → L3-003 #1 with explanation
```

These commands don't touch the chain, don't need PWM_PRIVATE_KEY,
and work even before you fund the wallet.

---

## Step 6 — Confirm the wallet sees Sepolia (~10 s)

```bash
pwm-node --network testnet balance
# → Address: 0x742d35…
# → Balance: 0.500000000000000000 ETH (Sepolia)
```

If this returns `0.000…`, the faucet hasn't completed yet. Re-run.

---

## Step 7 — Mine your first cert (~5 min, real on-chain tx)

The walkthrough script ships with the repo and runs CASSI + CACTI
end-to-end:

```bash
# Quickest: dry-run first to see the cert payload without spending gas
DRY_RUN=1 bash scripts/testnet_mine_walkthrough.sh

# Real run (CASSI only, ~2 min, costs ~0.001 Sepolia ETH):
CASSI_ONLY=1 bash scripts/testnet_mine_walkthrough.sh

# Real run (CASSI + CACTI, ~4 min):
bash scripts/testnet_mine_walkthrough.sh
```

The script:
1. Pre-flight checks (CLI installed, RPC reachable, wallet funded)
2. Computes the cert hash for your solver run
3. Stakes on the L1 Principle (~0.0005 ETH gas)
4. Stakes on the L3 Benchmark (~0.0005 ETH gas)
5. Mines: runs the reference solver → submits the cert (~0.0005 ETH gas)
6. Prints summary with the on-chain cert hash + Etherscan tx URL

Open the printed Etherscan URL in a browser to confirm the cert
landed.

---

## Step 8 — Verify on the explorer (~30 s)

```
https://explorer.pwm.platformai.org/cert/<your-cert-hash>
```

You should see:
- Your wallet as `submitter`
- `Q_int` (the integer quality score, e.g. 35)
- `solver_label` (set by `cert-meta` if you posted it; default empty)
- Status: `pending_challenge` for the next 7 days

After 7 days clean (no successful challenge), the cert can be
finalized and your share of the rank-1 / rank-2 / etc. reward pool
is released.

---

## Common first-time errors

| Error | What it means | Fix |
|---|---|---|
| `ConnectionError: Cannot connect to RPC https://rpc.sepolia.org` | The `PWM_RPC_URL` env var is unset or pointed at a stale RPC | `export PWM_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com` |
| `ValueError: insufficient funds for gas * price + value` | Sepolia balance is 0 or too low | Re-faucet; verify with `pwm-node balance` |
| `ContractLogicError: Pausable: paused` | The contract's emergency pause is on (rare; check explorer for an active incident) | Wait for the multisig to unpause; check `https://explorer.pwm.platformai.org/api/health` |
| `nonce too low` | Two txs signed with the same nonce | Wait for the prior tx to confirm; pwm-node should auto-recover on retry |
| `pwm-node: command not found` | Venv isn't activated | `source .venv/bin/activate` |
| `ImportError: cannot import 'pwm_core'` | LFS weights not pulled (only matters for deep-learning solvers) | `git lfs install && git -C public lfs pull` |

---

## What's next

After your first cert:

1. **Try a different solver.** The reference solvers in
   `pwm-team/pwm_product/reference_solvers/` are designed to be
   forkable starting points. Beat them on Q_int and rank up.

2. **Read the bug-fix playbook.** `PWM_BUG_FIX_PLAYBOOK_2026-05-08.md`
   covers what's editable post-deploy (UI fields, cert-meta) vs what
   requires a v-bump (forward model, ε_fn, dataset CIDs).

3. **For Base mainnet:** wait for D9 launch, then **don't reuse this
   key**. Set up a hardware wallet first; per
   `PWM_TESTNET_REHEARSAL_RUNBOOK_2026-05-08.md` § R1, run a
   dress-rehearsal cert from the HW wallet on Base Sepolia before
   touching real money on Base mainnet.

---

## Cross-references

- `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md` — full L1/L2/L3/L4 reference (you'll graduate to this after your first cert)
- `pwm-team/customer_guide/PWM_TESTNET_REHEARSAL_RUNBOOK_2026-05-08.md` — week-before-D9 hardware-wallet rehearsal
- `pwm-team/customer_guide/PWM_BUG_FIX_PLAYBOOK_2026-05-08.md` — what to do when something goes wrong post-mining
- `scripts/testnet_mine_walkthrough.sh` — the script Step 7 invokes
- `pwm-team/infrastructure/agent-cli/README.md` — full `pwm-node` CLI reference
