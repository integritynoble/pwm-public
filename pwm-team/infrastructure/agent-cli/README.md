# `pwm-node` — PWM protocol CLI

Discover benchmarks, verify solver claims, stake on artifacts, and mine
L4 certificates against on-chain PWM benchmarks. Network-agnostic
(`--network testnet` for Sepolia today, `--network base` for Base
mainnet post-launch).

---

## Install

```bash
git clone https://github.com/integritynoble/pwm-public.git
cd pwm-public
python3 -m venv .venv && source .venv/bin/activate
pip install -e pwm-team/infrastructure/agent-cli
```

After install, `pwm-node` is on your `PATH`.

For deep-learning solvers (MST-L, EfficientSCI):

```bash
pip install -e public/packages/pwm_core
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
```

(adjust the CUDA suffix to match your driver — `cu121`, `cu118`, etc.)

---

## Quick start (consumers, no wallet needed)

```bash
# Browse all benchmarks
pwm-node --network testnet benchmarks

# Find a benchmark for your problem
pwm-node match "compressive sensing inverse problem"

# Read one benchmark in detail
pwm-node --network testnet inspect L3-003

# Verify a published claim
pwm-node --network testnet verify-cert 0xb293...
```

These are all read-only — no Sepolia ETH needed.

---

## Mining flow (producers, need a funded wallet)

```bash
# Configure once
export PWM_PRIVATE_KEY=0x<your-Sepolia-key>
export PWM_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com

# (One-time per benchmark) stake on the parent L1 + L3
pwm-node --network testnet stake principle 0x<L1-hash>
pwm-node --network testnet stake benchmark  0x<L3-hash>

# Mine — runs your solver, computes Q, submits cert
pwm-node --network testnet mine L3-003 \
    --solver pwm-team/pwm_product/reference_solvers/cassi/cassi_mst.py

# After 7-day challenge period, finalize → triggers reward distribution
pwm-node --network testnet finalize 0x<cert-hash>
```

Free Sepolia ETH from any of:

- https://sepoliafaucet.com
- https://www.alchemy.com/faucets/ethereum-sepolia
- https://faucet.quicknode.com/ethereum/sepolia

---

## Commands

| Command | Purpose |
|---|---|
| `pwm-node benchmarks` | List all registered L3 benchmarks |
| `pwm-node match <query>` | Find a benchmark for a natural-language problem description |
| `pwm-node inspect L1-XXX` | Read principle metadata, forward model, DAG |
| `pwm-node inspect L2-XXX` | Read spec six-tuple (Ω, E, B, I, O, ε) |
| `pwm-node inspect L3-XXX` | Read benchmark + leaderboard preview |
| `pwm-node mine <bench> --solver <path>` | Run solver + submit L4 cert |
| `pwm-node mine <bench> --solver <path> --dry-run` | Compute Q + cert hash without submitting (no tx) |
| `pwm-node verify-cert <hash>` | Read on-chain cert state (no tx) |
| `pwm-node stake quote <tier>` | Show required stake amount in PWM |
| `pwm-node stake principle <0x-hash>` | Stake on an L1 (~$50 tier) |
| `pwm-node stake spec <0x-hash>` | Stake on an L2 (~$5 tier) |
| `pwm-node stake benchmark <0x-hash>` | Stake on an L3 (~$1 tier) |
| `pwm-node finalize <cert-hash>` | After 7-day challenge window, trigger reward distribution |
| `pwm-node balance` | Show your wallet's ETH + PWM balances |

`pwm-node --help` shows the full options for each subcommand.

---

## Networks

| `--network` | Chain | When to use |
|---|---|---|
| `offline` | none | Local manifest browsing; no chain access |
| `testnet` | Ethereum Sepolia (chainId 11155111) | All examples in this README; live testnet today |
| `baseSepolia` | Base Sepolia (chainId 84532) | Step 5 governance rehearsal |
| `base` | Base mainnet (chainId 8453) | Production once mainnet launches |

The CLI reads contract addresses from `pwm-team/infrastructure/agent-contracts/addresses.json`.

---

## Env vars

| Variable | Purpose | Required when |
|---|---|---|
| `PWM_PRIVATE_KEY` | Wallet key for signing on-chain txs | Mining, staking, finalizing |
| `PWM_RPC_URL` | RPC endpoint | All on-chain commands |
| `PWM_NETWORK` | Override `--network` flag | Optional |
| `PWM_DB` | Local cache of indexer data | Optional |

---

## Configuration

The CLI ships with sensible defaults. To see what would be used:

```bash
pwm-node --network testnet inspect L3-003 --explain
```

The `--explain` flag prints the resolved config (RPC URL, contract
addresses, solver path candidates) before executing, so you can
see exactly what the command will do.

---

## Mining lifecycle in detail

The full `mine` flow:

1. Solver runs locally → produces `solution.npz` + `meta.json`
2. CLI computes `cert_hash = keccak256(canonical_payload)` where the
   payload includes (Q score, solver_id, benchmarkHash, ω instance)
3. CLI calls `PWMCertificate.submit(cert_hash, benchmarkHash, Q_int, payload)`
4. 7-day challenge period starts — anyone can call
   `PWMCertificate.challenge(cert_hash, proof)` to dispute
5. After 7 days clean: anyone calls `finalize(cert_hash)` → reward
   distribution

After mining, optionally enrich the on-chain cert with a human-readable
solver label so the leaderboard displays "MST-L 34.1 dB" instead of
just the cert hash:

```bash
bash scripts/submit_cert_meta.sh /tmp/pwm-out/cassi-mst/meta.json
```

This calls `POST /api/cert-meta/{cert_hash}` on the explorer's
off-chain enrichment endpoint. No tx, no gas — purely cosmetic.

---

## Reward structure (informational)

Per `PWMReward.distribute()`:

| Rank | Pool share |
|---|---|
| 1 | 40% |
| 2 | 5% |
| 3 | 2% |
| 4-10 | 1% each |
| 11+ | 0% (rolls over to next epoch) |

Within rank 1's 40%, the algorithm contributor (AC) gets `p × 55%` and
the compute provider (CP) gets `(1-p) × 55%` where `p ∈ [0.10, 0.90]`
is set by the SP at registration. L3/L2/L1 contributors get
15%/10%/5%; the principle's treasury gets 15%.

---

## Cross-references

- **Customer guide:** `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md`
- **Live explorer:** [https://explorer.pwm.platformai.org](https://explorer.pwm.platformai.org)
- **Reference solvers:** `pwm-team/pwm_product/reference_solvers/`
- **Mining walkthrough:** `scripts/testnet_mine_walkthrough.sh`
- **Genesis manifests:** `pwm-team/pwm_product/genesis/{l1,l2,l3}/`

---

## License

PWM NONCOMMERCIAL SHARE-ALIKE LICENSE v1.0 — see [`LICENSE`](../../../LICENSE) at the repo root.
