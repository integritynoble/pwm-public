# Agent Role: agent-web
## Web Explorer Developer

You build the web explorer at pwm.platformai.org — the public face of PWM. It makes the protocol legible to researchers, miners, investors, and users without requiring them to run a CLI.

## You own
- `frontend/` — React or Next.js app
- `indexer/` — event log indexer (reads PWMRegistry, PWMReward event streams)
- `api/` — REST endpoints the frontend calls

## You must NOT modify
- `../agent-contracts/` — contracts
- `../agent-scoring/` — scoring engine
- `../agent-cli/` — CLI
- `../agent-miner/` — mining client
- `../agent-*/principles/` — content

## Interfaces you depend on
- `../agent-coord/interfaces/contracts_abi/` — event log schemas
- `../agent-coord/interfaces/addresses.json` — contract addresses

## Unblocked at: M1.1 (contracts ABI for event log structure)

## Pages to implement

| Route | Content |
|---|---|
| `/` | Protocol overview: total pool, active principles, recent draws |
| `/principles` | All 500 principles: domain, δ, Pool_k, active benchmarks, top PSNR |
| `/principles/<id>` | Principle detail: L_DAG, forward model, all specs, benchmarks |
| `/benchmarks` | All benchmarks: pool sizes, Rank 1 holder, ε, ρ weight |
| `/benchmarks/<id>` | Benchmark detail: omega_tier, Track A/B/C pass rates, leaderboard |
| `/leaderboard/<benchmark_id>` | Ranks 1–10: PSNR, Q, SP wallet, draw amount per epoch |
| `/pools` | Live pool sizes: Pool_k per principle, epoch rollover amounts, T_k balances |
| `/cert/<hash>` | Certificate: S1-S4 verdicts, Q score, reward breakdown, challenge status |
| `/submit` | Guided L2/L3 submission UI (calls pwm-node under the hood) |
| `/bounties` | Open Reserve bounties with amounts and acceptance criteria |

## indexer/
- Subscribes to contract events via WebSocket RPC
- Stores indexed data in a lightweight local DB (SQLite or Postgres)
- Events to index:
  - `PWMRegistry.ArtifactRegistered` → principles, specs, benchmarks
  - `PWMCertificate.CertificateSubmitted` → pending solutions
  - `PWMReward.DrawSettled` → rank, amount, SP/CP addresses
- Updates within ≤5 minutes of on-chain event

## api/
REST endpoints (JSON):
```
GET /api/principles              → list all principles with summary stats
GET /api/principles/:id          → full principle detail
GET /api/benchmarks              → list all benchmarks
GET /api/benchmarks/:id          → benchmark detail + leaderboard
GET /api/pools                   → current pool sizes
GET /api/cert/:hash              → certificate detail
GET /api/leaderboard/:benchmark  → ranks 1-10
```

## Requirements
- Read-only: no write access. All transactions go through pwm-node (UI just displays)
- Works without MetaMask (read-only; no wallet required to browse)
- Mobile-responsive
- No login required to view any data

## Definition of done
- All 500 genesis principles display correctly at /principles
- Leaderboard updates within 10 minutes of draw settlement on testnet
- Works on Chrome, Firefox, Safari (desktop + mobile)
- /cert/<hash> shows correct S1-S4 verdicts and reward breakdown
- Deployed at pwm.platformai.org (you handle the deployment config)

## How to signal completion
1. Update `../agent-coord/progress.md` — mark M1.5 DONE
2. Open PR: `feat/web-explorer-v1`
