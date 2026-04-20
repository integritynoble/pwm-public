# Sepolia deployment setup

How to obtain the two environment variables `deploy/testnet.js` needs:

- `SEPOLIA_RPC_URL` — a JSON-RPC endpoint for the Sepolia testnet
- `DEPLOYER_PRIVATE_KEY` — a funded Sepolia wallet's private key

Both are free. Total time: 5–15 minutes.

---

## 1. Get a `SEPOLIA_RPC_URL`

Pick **one** of these providers, sign up for the free tier, create a Sepolia
app, and copy the HTTPS endpoint.

| Provider | Endpoint format |
|---|---|
| Alchemy (`alchemy.com`) | `https://eth-sepolia.g.alchemy.com/v2/<API-KEY>` |
| Infura (`infura.io`) | `https://sepolia.infura.io/v3/<API-KEY>` |
| QuickNode (`quicknode.com`) | `https://<subdomain>.ethereum-sepolia.quiknode.pro/<API-KEY>/` |
| Ankr (`ankr.com/rpc`) | `https://rpc.ankr.com/eth_sepolia/<API-KEY>` |

**No-signup public endpoints** (rate-limited; fine for a single deploy):

- `https://rpc.sepolia.org`
- `https://ethereum-sepolia.publicnode.com`
- `https://sepolia.drpc.org`

If you hit `429 Too Many Requests` or `timeout`, switch to a signed-up
provider — the free tier is generous (millions of requests/month).

---

## 2. Generate a throwaway `DEPLOYER_PRIVATE_KEY`

**Never reuse a mainnet wallet.** The deployer key ends up in a local `.env`
file and becomes the initial admin of all 7 contracts. Compromise on testnet
is annoying but recoverable; mainnet would be catastrophic.

### Option A — Node one-liner (no wallet app needed)

```bash
node -e "const w = require('ethers').Wallet.createRandom(); \
  console.log('address:', w.address); \
  console.log('key:    ', w.privateKey);"
```

Prints something like:

```
address: 0x1234AbCd...
key:     0xabcdef0123456789...
```

Save both — the address is what the faucet will fund; the key goes in `.env`.

### Option B — MetaMask

1. Open MetaMask → account menu → **Create Account**
2. Name it `pwm-sepolia-deployer` so you don't confuse it
3. Account menu → **Account details** → **Show private key** → confirm password
4. Copy the private key (64 hex chars, prefix with `0x` when pasting into `.env`)
5. Copy the public address for the faucet step

### Option C — Foundry's `cast` (if installed)

```bash
cast wallet new
```

---

## 3. Fund the wallet with Sepolia ETH

Send the deployer's **address** (not the private key!) to a faucet. Most give
0.05–0.5 Sepolia ETH per drip; you'll want **≈ 0.2 ETH** total to comfortably
deploy all 7 contracts and absorb gas price swings.

| Faucet | Drip | Requirement |
|---|---|---|
| `sepoliafaucet.com` | 0.5 ETH / day | Alchemy account |
| `cloud.google.com/application/web3/faucet/ethereum/sepolia` | 0.05 ETH / day | Google account |
| `faucets.chain.link` | 0.1 ETH | 1 LINK on any mainnet **or** GitHub verify |
| `sepolia-faucet.pk910.de` | variable | PoW mining in-browser, no signup |
| `www.infura.io/faucet/sepolia` | 0.5 ETH / day | Infura account |

Tips:

- If a faucet rejects you for "low mainnet ETH balance", try another — some
  require 0.001 ETH on mainnet as an anti-bot check.
- Multiple drips from different faucets are fine; they stack on the same
  testnet address.
- Confirm the balance in a block explorer:
  `https://sepolia.etherscan.io/address/<your-address>`

Expected deploy cost (7 contracts + wiring transactions) is roughly **0.05 – 0.15
Sepolia ETH** at current gas prices. One good faucet drip is typically enough.

---

## 4. Configure `.env`

From the repo root:

```bash
cd pwm-team/infrastructure/agent-contracts
cp .env.example .env
```

Fill in `.env`:

```env
SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_KEY_HERE
DEPLOYER_PRIVATE_KEY=0xabcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789
ETHERSCAN_API_KEY=     # optional: only if you want post-deploy verification
```

Sanity-check it's readable:

```bash
node -e "require('dotenv').config(); \
  console.log('RPC:', process.env.SEPOLIA_RPC_URL ? 'set' : 'MISSING'); \
  console.log('KEY:', process.env.DEPLOYER_PRIVATE_KEY ? 'set' : 'MISSING');"
```

`.env` is already listed in `.gitignore` — never commit it.

---

## 5. Decide on founder addresses for `PWMGovernance`

The governance contract takes 5 founder addresses in its constructor. These
are the 3-of-5 multisig for the first 6–12 months and **cannot be changed
after deploy**.

Two ways to supply them:

1. **Pass via env** (recommended for real testnet):

   ```bash
   export FOUNDER_ADDRESSES="0xAAA...,0xBBB...,0xCCC...,0xDDD...,0xEEE..."
   ```

   All 5 must be distinct and non-zero. For testnet you can use 5 throwaway
   addresses you control (e.g., 5 MetaMask accounts) — the point is just to
   exercise the multisig code path.

2. **Omit — script falls back to Hardhat's first 5 signers**. Only works
   when you run without `--network sepolia` (local dry-run).

---

## 6. Run the deploy

```bash
cd pwm-team/infrastructure/agent-contracts
npx hardhat run deploy/testnet.js --network sepolia
```

The script:

1. Deploys all 7 contracts in dependency order
2. Wires every cross-contract address via each contract's governance setters
3. Writes real addresses to `addresses.json` under the `testnet` slot
4. Refuses to overwrite an already-populated `testnet` slot unless you set
   `PWM_ALLOW_OVERWRITE=1`

Expect the full run to take 2–5 minutes on Sepolia depending on block times.

---

## 7. Verify on Etherscan (optional but recommended)

If you set `ETHERSCAN_API_KEY` in `.env`, verification can be automated later.
For now, post-deploy you can paste each contract address into
`https://sepolia.etherscan.io/address/<addr>` and use the "Verify and Publish"
flow with:

- Compiler: `v0.8.24+commit.e11b9ed9`
- Optimization: yes, `200` runs, `viaIR` enabled
- Source files: `contracts/*.sol` (flattened via `npx hardhat flatten`)

---

## 8. Publish ABIs to downstream agents

After successful deploy:

```bash
npx hardhat run scripts/publish_abi.js
```

This copies the fresh ABI JSON and `addresses.json` into
`../../coordination/agent-coord/interfaces/` so every downstream agent
(scoring, CLI, mining client, explorer) picks up the real testnet addresses.

Then flip the signal in `../../coordination/agent-coord/progress.md`:

```
CONTRACTS_DEPLOYED = true  # Sepolia addresses <list> — <date>
M1.1 = DONE
```

That's the green light for agent-coord to publish bounties.

---

## Security checklist

- [ ] `.env` is in `.gitignore` (already done — don't remove it)
- [ ] Deployer private key is a **fresh, throwaway** key, never used on mainnet
- [ ] Founder addresses are controlled by separate wallets (don't collapse all 5
      into one EOA — that defeats the multisig)
- [ ] After deploy, rotate the initial admin to the governance multisig by
      calling `setGovernance(governanceAddr)` on each contract once you're
      ready to hand off control

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `insufficient funds for gas * price + value` | Deployer underfunded | Re-drip from faucet; confirm balance on Sepolia Etherscan |
| `invalid api key` / `401` | RPC URL malformed | Copy the URL again from provider dashboard; ensure no trailing spaces |
| `nonce too high` / `nonce too low` | Pending tx in provider's mempool | Wait 1–2 minutes and retry; or reset account in MetaMask |
| `timeout of 40000ms exceeded` | Public RPC overloaded | Switch to a signed-up provider |
| Script refuses to write `addresses.json` | `testnet` slot already populated | Set `PWM_ALLOW_OVERWRITE=1` env var to intentionally overwrite |
| `PWMGovernance: duplicate founder` | Two founder addresses collide | Ensure all 5 `FOUNDER_ADDRESSES` entries are distinct |
