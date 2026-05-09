# PWM — Physics-World-Model Protocol

PWM is a 4-layer protocol for evaluating computational-science methods
on tamper-resistant on-chain benchmarks. This is the **public mirror**
— the canonical reference implementation, customer guide, and contract
sources.

---

## ⚠️ Launch status (2026-05-07)

**This repository is in pre-mainnet testing.** Read before relying on anything here:

| Network | Status today | What works | What does NOT work |
|---|---|---|---|
| **Ethereum Sepolia testnet** (chainId 11155111) | ✓ Live | Full mining flow, real cert submissions, leaderboard, all examples in the customer guide | Sepolia ETH has no monetary value — testnet only |
| **Base mainnet** (chainId 8453) | ✗ Not yet deployed | Nothing — `addresses.json:mainnet` is intentionally null | All production mining; targeted for D9 of the deploy runbook (~3-4 weeks from this README's date) |

**The 531 cataloged Principles** are organized into 3 registration tiers:

- **2 Tier 1 founder-vetted** (CASSI L1-003 + CACTI L1-004) — registered on Sepolia, mineable today
- **0 Tier 2 community-proposed** — the post-launch growth path
- **529 Tier 3 stubs** — declared scientific inventory awaiting external contributors. **Not registered on-chain, not mineable, no reward pool.**

If you're here to mine, only L3-003 and L3-004 produce certs that can earn rewards. If you're here to claim a stub, see the contribution flow at the end of this README.

For details on the tier system + economic protections see `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md` § "Registration tiers".

---

## Quick start (consumers)

```bash
git clone https://github.com/integritynoble/pwm-public.git
cd pwm-public
python3 -m venv .venv && source .venv/bin/activate
pip install -e pwm-team/infrastructure/agent-cli   # → pwm-node CLI

# Browse the catalog
pwm-node --network testnet benchmarks

# Or visit the live explorer:
#   https://explorer.pwm.platformai.org
```

## Full guide

See `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md`
for the complete walkthrough of the L1/L2/L3/L4 layers, with consumer
+ producer flows and 5 concrete user journeys.

## What's in this repo

| Directory | Purpose |
|---|---|
| `pwm-team/pwm_product/` | Genesis manifests (L1/L2/L3) + reference solvers + demo data |
| `pwm-team/infrastructure/agent-contracts/` | 7 Solidity contracts (PWMRegistry, PWMCertificate, etc.) + deploy scripts |
| `pwm-team/infrastructure/agent-cli/` | `pwm-node` CLI |
| `pwm-team/infrastructure/agent-web/` | Web explorer (Next.js + FastAPI + SQLite indexer) |
| `pwm-team/infrastructure/agent-miner/` | Reference miner implementation |
| `pwm-team/infrastructure/agent-scoring/` | Off-chain scoring engine |
| `pwm-team/customer_guide/` | Public-facing documentation |
| `scripts/` | Mining helpers, register_genesis, daily stability check, etc. |
| `papers/Proof-of-Solution/mine_example/science/` | Genesis-manifest catalog (public, by domain) |

## Live explorer

[https://explorer.pwm.platformai.org](https://explorer.pwm.platformai.org) — testnet leaderboard, live cert submissions, benchmark detail pages.

## Contracts on Ethereum Sepolia (chainId 11155111)

| Contract | Address |
|---|---|
| PWMRegistry | [`0x2375217dd8FeC420707D53C75C86e2258FBaab65`](https://sepolia.etherscan.io/address/0x2375217dd8FeC420707D53C75C86e2258FBaab65) |
| PWMCertificate | [`0x8963b60454EC1D9F65eE3cbF7aBC5D1220C3dB08`](https://sepolia.etherscan.io/address/0x8963b60454EC1D9F65eE3cbF7aBC5D1220C3dB08) |

Full set in `pwm-team/infrastructure/agent-contracts/addresses.json`.

## License

PWM NONCOMMERCIAL SHARE-ALIKE LICENSE v1.0 — see [`LICENSE`](LICENSE).

## Contributing

External developers can author new L1 Principles + L2 Specs +
L3 Benchmarks. Reward via Bounty #7 Tier B (~2,000 PWM per anchor on
first external L4 submission).

See `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md`
§ "L1 — How PRODUCERS create new Principles".
