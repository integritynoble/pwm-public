# PWM Web Explorer

Read-only public explorer for the Physics World Model protocol. Three services:

| Service | Stack | Purpose |
|---|---|---|
| `indexer/` | Python + `web3.py` + SQLite | Subscribes to Registry/Certificate/Reward/Treasury events; maintains a local DB. |
| `api/`     | Python + FastAPI       | Serves `/api/*` JSON; joins on-chain state with off-chain genesis JSONs. |
| `frontend/`| Next.js 14 (App Router, TypeScript, Tailwind, KaTeX) | SSR UI. |

This is the **80,000 PWM Reserve bounty** reference implementation. Third-party
developers compete to build the production version — the goal here is to make
the interface concrete and demonstrate end-to-end feasibility.

## Quick start

```bash
# 1. Set the RPC and network
export PWM_RPC_URL=https://rpc.sepolia.org
export PWM_NETWORK=testnet

# 2. Bring everything up
docker-compose up --build
```

- Frontend: http://localhost:3000
- API:      http://localhost:8000/api/health

## Run components individually (dev)

```bash
# API only (auto-creates empty DB if the indexer hasn't run yet)
cd infrastructure/agent-web
PYTHONPATH=. uvicorn api.main:app --reload

# Indexer only
PYTHONPATH=. python -m indexer.main

# Frontend only (expects API at http://localhost:8000)
cd frontend && npm install && npm run dev
```

## Tests

```bash
# Backend (indexer + api): 17 tests
cd infrastructure/agent-web
PYTHONPATH=. python -m pytest indexer/tests api/tests

# Frontend build check
cd frontend && npm run build
```

## Pages

| Route                           | Content |
|---------------------------------|---------|
| `/`                             | Pool totals, active-principle count, last 10 draws. |
| `/principles`                   | All genesis L1 principles; domain filter. |
| `/principles/[id]`              | Forward model (KaTeX), L-DAG, specs, treasury balance. |
| `/benchmarks`                   | Off-chain + on-chain L3 benchmarks. |
| `/benchmarks/[ref]`             | Ω tier, baselines, top-10 leaderboard. |
| `/leaderboard/[hash]`           | Full leaderboard by rank for a benchmark. |
| `/pools`                        | Pool_k bars per benchmark; T_k bars per principle. |
| `/cert/[hash]`                  | S1–S4 gates, reward breakdown, challenge status. |
| `/bounties`                     | Open Reserve bounties. |
| `/submit`                       | How to submit using `pwm-node` (no in-browser wallet). |

## Interface dependencies

Pulled at runtime from `../../coordination/agent-coord/interfaces/`:

- `contracts_abi/*.json` — event signatures (used by indexer).
- `addresses.json` — deployed contract addresses per network.
- `bounties/*.md` — rendered at `/bounties`.

Genesis principle/spec/benchmark JSONs live in `../../pwm_product/genesis/`.

## Acceptance criteria (bounty)

- [x] Read-only; no MetaMask required.
- [x] Mobile responsive (Tailwind).
- [x] Works on Chrome/Firefox/Safari desktop + mobile.
- [x] `/cert/<hash>` shows S1–S4 verdicts and reward breakdown.
- [x] Genesis principle list populated from `pwm_product/genesis/l1/`.
- [ ] Leaderboard updates ≤10 minutes after `DrawSettled` (indexer poll = 12s; satisfied when the indexer is running).
