# agent-web: Execution Plan

Read `CLAUDE.md` first (your role and all page specs). This file is your step-by-step work order.

> This is a **bounty reference implementation** (80,000 PWM). You are building a reference to validate the interface — third-party developers will compete to build the production version.

---

## Before You Start

- [ ] Read `CLAUDE.md` — all 9 page specs and API endpoint list are there.
- [ ] **Wait for M1.1** (contracts ABI) — you need event schemas before building the indexer.
- [ ] Check available before proceeding:
  - `../../coordination/agent-coord/interfaces/contracts_abi/` — event log schemas
  - `../../coordination/agent-coord/interfaces/addresses.json` — contract addresses
- [ ] You can start `frontend/` static scaffolding and design immediately.

---

## Step 1 — Choose Stack and Scaffold

- [ ] **1.1** Choose framework: Next.js (recommended — server-side rendering helps SEO + data freshness).
  ```bash
  cd infrastructure/agent-web/frontend
  npx create-next-app@latest . --typescript --tailwind --app
  ```
- [ ] **1.2** Choose indexer DB: SQLite for simplicity (upgrade to Postgres if needed).
- [ ] **1.3** Create `api/` as a FastAPI app (Python, consistent with rest of stack):
  ```bash
  cd infrastructure/agent-web/api
  pip install fastapi uvicorn sqlalchemy
  ```

---

## Step 2 — Indexer (after M1.1)

Build `indexer/` first — the frontend is useless without data.

- [ ] **2.1** Create `indexer/schema.sql`:
  ```sql
  CREATE TABLE artifacts (hash TEXT PRIMARY KEY, parent_hash TEXT, layer INT, creator TEXT, timestamp INT);
  CREATE TABLE certificates (cert_hash TEXT PRIMARY KEY, benchmark_hash TEXT, submitter TEXT, Q_int INT, status TEXT, submitted_at INT);
  CREATE TABLE draws (cert_hash TEXT, rank INT, amount TEXT, sp_addr TEXT, cp_addr TEXT, settled_at INT);
  CREATE TABLE pools (principle_id TEXT, pool_k TEXT, t_k TEXT, updated_at INT);
  ```
- [ ] **2.2** Implement `indexer/main.py`:
  ```python
  # Subscribe to events via WebSocket RPC
  # Events to index:
  #   PWMRegistry.ArtifactRegistered → artifacts table
  #   PWMCertificate.CertificateSubmitted → certificates table
  #   PWMReward.DrawSettled → draws table
  # Poll interval: 12s (one block)
  # On startup: backfill from block 0 to current
  ```
- [ ] **2.3** Confirm indexer catches up to chain head within 10 minutes of start.
- [ ] **2.4** Write `indexer/tests/test_indexer.py` — mock contract events; confirm DB rows created.

---

## Step 3 — API (after indexer schema is set)

- [ ] **3.1** Implement all endpoints in `api/main.py`:
  ```
  GET /api/principles              → list all, with pool_k, active benchmark count
  GET /api/principles/:id          → full detail including L_DAG, forward_model
  GET /api/benchmarks              → list all with pool size, rank 1 PSNR, ρ weight
  GET /api/benchmarks/:id          → detail + leaderboard (ranks 1–10)
  GET /api/pools                   → pool_k and t_k per principle
  GET /api/cert/:hash              → certificate detail, S1-S4 verdicts, reward breakdown
  GET /api/leaderboard/:benchmark  → top 10 solvers sorted by Q then PSNR
  ```
- [ ] **3.2** All responses are JSON. Add `Cache-Control: max-age=60` headers (data updates ~1/minute).
- [ ] **3.3** CORS: allow `*` (read-only, no secrets exposed).
- [ ] **3.4** Write `api/tests/test_api.py` — mock DB; test each endpoint with known data.

---

## Step 4 — Frontend Pages

Implement pages in order of importance:

- [ ] **4.1** `/` — Home:
  - Total minting pool remaining
  - Active principles count
  - Recent draws (last 10 DrawSettled events)
  - Link to /principles and /benchmarks

- [ ] **4.2** `/principles` — Principle list:
  - Table: Principle ID | Domain | δ | Pool_k | Active Benchmarks | Top PSNR
  - Filter by domain
  - Link each row to `/principles/<id>`

- [ ] **4.3** `/principles/<id>` — Principle detail:
  - Forward model (rendered with KaTeX or MathJax)
  - L_DAG diagram
  - List of specs (link to benchmarks)
  - T_k treasury balance

- [ ] **4.4** `/benchmarks` — Benchmark list:
  - Table: Benchmark ID | Spec | ρ | Pool | Rank 1 PSNR | ε
  - Filter by domain / ρ tier

- [ ] **4.5** `/benchmarks/<id>` — Benchmark detail:
  - omega_tier, Track A/B/C pass rates
  - Leaderboard (ranks 1–10)
  - Dataset description and stitching notes

- [ ] **4.6** `/leaderboard/<benchmark_id>` — Full leaderboard:
  - Columns: Rank | AC wallet | PSNR | Q | Draw amount | Date

- [ ] **4.7** `/pools` — Pool overview:
  - Pool_k per principle (bar chart or table)
  - Epoch rollover amounts
  - T_k balances

- [ ] **4.8** `/cert/<hash>` — Certificate detail:
  - S1-S4 verdicts (green/red badges)
  - Q score
  - Reward breakdown (AC%, CP%, L3%, L2%, L1%, T_k%)
  - Challenge status (pending / finalized / challenged)

- [ ] **4.9** `/bounties` — Open bounties:
  - List from Reserve pool (static data for now, admin-editable)
  - Each bounty: title, amount PWM, acceptance criteria link

---

## Step 5 — Requirements

- [ ] **5.1** No login required for any page (read-only).
- [ ] **5.2** Works without MetaMask.
- [ ] **5.3** Mobile-responsive (test at 375px width).
- [ ] **5.4** Math formulas render correctly (KaTeX or MathJax).
- [ ] **5.5** Test on Chrome, Firefox, Safari (desktop + mobile).

---

## Step 6 — Deployment

- [ ] **6.1** Create `docker-compose.yml`:
  ```yaml
  services:
    indexer:
      build: ./indexer
      environment:
        - RPC_URL=${PWM_RPC_URL}
    api:
      build: ./api
      depends_on: [indexer]
      ports: ["8000:8000"]
    frontend:
      build: ./frontend
      environment:
        - API_URL=http://api:8000
      ports: ["3000:3000"]
  ```
- [ ] **6.2** Deploy to server at `pwm.platformai.org`.
- [ ] **6.3** Add nginx reverse proxy: `/api/*` → api:8000, `/*` → frontend:3000.

---

## Step 7 — Validation on Testnet

- [ ] **7.1** Confirm all 500 genesis principles appear at `/principles`.
- [ ] **7.2** Submit a test certificate on testnet; confirm `/cert/<hash>` shows correct data within 10 minutes.
- [ ] **7.3** Confirm leaderboard updates after DrawSettled event.
- [ ] **7.4** Confirm `/cert/<hash>` shows S1-S4 verdicts and reward breakdown correctly.

---

## Step 8 — Signal Completion

- [ ] **8.1** Update `../../coordination/agent-coord/progress.md` — mark web explorer tasks `DONE`.
- [ ] **8.2** Open PR: `feat/web-explorer-v1`
  - Include: `frontend/`, `indexer/`, `api/`, `docker-compose.yml`
  - PR description: screenshot of /principles with 500 principles loaded; /cert/<hash> screenshot
