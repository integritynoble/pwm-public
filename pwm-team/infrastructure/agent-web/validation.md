# agent-web: Validation Checklist

Run every check below before merging the web explorer PR.

---

## V1 — Files Exist

### Frontend:
- [ ] `frontend/package.json` — Next.js + TypeScript + Tailwind
- [ ] `frontend/app/page.tsx` — home route `/`
- [ ] `frontend/app/principles/page.tsx` — `/principles`
- [ ] `frontend/app/principles/[id]/page.tsx` — `/principles/<id>`
- [ ] `frontend/app/benchmarks/page.tsx` — `/benchmarks`
- [ ] `frontend/app/benchmarks/[id]/page.tsx` — `/benchmarks/<id>`
- [ ] `frontend/app/leaderboard/[benchmark_id]/page.tsx` — `/leaderboard/<id>`
- [ ] `frontend/app/pools/page.tsx` — `/pools`
- [ ] `frontend/app/cert/[hash]/page.tsx` — `/cert/<hash>`
- [ ] `frontend/app/submit/page.tsx` — `/submit`
- [ ] `frontend/app/bounties/page.tsx` — `/bounties`

### Indexer:
- [ ] `indexer/schema.sql`
- [ ] `indexer/main.py`
- [ ] `indexer/tests/test_indexer.py`

### API:
- [ ] `api/main.py` — FastAPI app
- [ ] `api/tests/test_api.py`

### Deployment:
- [ ] `docker-compose.yml`

**Verify:**
```bash
cd frontend && npm install && npm run build  # must succeed
cd api && pip install -r requirements.txt
```

---

## V2 — All 10 Routes Render

| Route | Content Required | Renders? |
|---|---|---|
| `/` | Total pool remaining, active principles count, recent 10 draws, links to /principles and /benchmarks | [ ] |
| `/principles` | Table: Principle ID \| Domain \| δ \| Pool_k \| Active Benchmarks \| Top PSNR; filter by domain; rows link to detail | [ ] |
| `/principles/<id>` | Forward model (KaTeX/MathJax rendered), L_DAG diagram, specs list, benchmarks, T_k treasury | [ ] |
| `/benchmarks` | Table: Benchmark ID \| Spec \| ρ \| Pool \| Rank 1 PSNR \| ε; filter by domain/ρ tier | [ ] |
| `/benchmarks/<id>` | omega_tier, Track A/B/C pass rates, leaderboard (Ranks 1-10), dataset description | [ ] |
| `/leaderboard/<benchmark_id>` | Rank \| AC wallet \| PSNR \| Q \| Draw amount \| Date (Ranks 1-10) | [ ] |
| `/pools` | Pool_k per principle (bar chart or table), epoch rollover amounts, T_k balances | [ ] |
| `/cert/<hash>` | S1-S4 verdicts (green/red badges), Q score, reward breakdown, challenge status | [ ] |
| `/submit` | Guided L2/L3 submission UI (calls pwm-node under the hood) | [ ] |
| `/bounties` | Open Reserve bounties: title, amount PWM, acceptance criteria link | [ ] |

---

## V3 — Indexer

### Database schema:
```sql
-- Verify these tables exist in schema.sql:
CREATE TABLE artifacts (hash TEXT PRIMARY KEY, parent_hash TEXT, layer INT, creator TEXT, timestamp INT);
CREATE TABLE certificates (cert_hash TEXT PRIMARY KEY, benchmark_hash TEXT, submitter TEXT, Q_int INT, status TEXT, submitted_at INT);
CREATE TABLE draws (cert_hash TEXT, rank INT, amount TEXT, sp_addr TEXT, cp_addr TEXT, settled_at INT);
CREATE TABLE pools (principle_id TEXT, pool_k TEXT, t_k TEXT, updated_at INT);
```

### Events indexed:
- [ ] `PWMRegistry.ArtifactRegistered` → inserts into `artifacts` table
- [ ] `PWMCertificate.CertificateSubmitted` → inserts into `certificates` table
- [ ] `PWMReward.DrawSettled` → inserts into `draws` table

### Behavior:
- [ ] Subscribes to contract events via WebSocket RPC
- [ ] Poll interval: ≤ 12 seconds (one block)
- [ ] On startup: backfills from block 0 to current head
- [ ] Catches up to chain head within 10 minutes of start
- [ ] Updates within ≤ 5 minutes of on-chain event during normal operation

**Test:**
```bash
pytest indexer/tests/test_indexer.py -v
```
- [ ] Mock contract events → correct DB rows created
- [ ] Backfill from genesis produces correct row count
- [ ] Duplicate events handled (idempotent inserts)

---

## V4 — API Endpoints

All responses are JSON with `Cache-Control: max-age=60`.
CORS: `Access-Control-Allow-Origin: *`.

| Endpoint | Returns | Works? |
|---|---|---|
| `GET /api/principles` | List all principles with pool_k, active benchmark count | [ ] |
| `GET /api/principles/:id` | Full detail: L_DAG, forward_model, specs, benchmarks | [ ] |
| `GET /api/benchmarks` | List all with pool size, Rank 1 PSNR, ρ weight | [ ] |
| `GET /api/benchmarks/:id` | Detail + leaderboard (Ranks 1-10) | [ ] |
| `GET /api/pools` | pool_k and t_k per principle | [ ] |
| `GET /api/cert/:hash` | Certificate detail, S1-S4 verdicts, reward breakdown | [ ] |
| `GET /api/leaderboard/:benchmark` | Top 10 solvers sorted by Q then PSNR | [ ] |

**Verify:**
```bash
# Start API server
uvicorn api.main:app --port 8000 &

# Test each endpoint
curl -s http://localhost:8000/api/principles | python -m json.tool
curl -s http://localhost:8000/api/benchmarks | python -m json.tool
curl -s http://localhost:8000/api/pools | python -m json.tool

# Check headers
curl -sI http://localhost:8000/api/principles | grep -i cache-control
# Should show: Cache-Control: max-age=60

curl -sI http://localhost:8000/api/principles | grep -i access-control
# Should show: Access-Control-Allow-Origin: *
```

**Test:**
```bash
pytest api/tests/test_api.py -v
```
- [ ] Each endpoint returns valid JSON
- [ ] Mock DB data produces expected responses
- [ ] Empty DB returns empty lists (not errors)
- [ ] Invalid IDs return 404

---

## V5 — /cert/<hash> Detail Page

This is the most data-dense page. Verify every element:

- [ ] S1-S4 verdicts shown as green (pass) or red (fail) badges
- [ ] Q score displayed prominently
- [ ] Reward breakdown table:

| Recipient | Share | Amount |
|-----------|-------|--------|
| AC (Algorithm Creator) | p × 55% | value |
| CP (Compute Provider) | (1-p) × 55% | value |
| L3 benchmark creator | 15% | value |
| L2 spec author | 10% | value |
| L1 principle creator | 5% | value |
| T_k treasury | 15% | value |

- [ ] Challenge status: pending / finalized / challenged
- [ ] Challenge period remaining (countdown or date)
- [ ] Cert hash displayed
- [ ] Benchmark reference linked

---

## V6 — Math Rendering

- [ ] KaTeX or MathJax loaded on principle detail pages
- [ ] Forward model equations render correctly (LaTeX notation)
- [ ] No raw LaTeX source visible to users
- [ ] Common symbols render: Σ, ∫, ∂, Φ, ε, Ω, ∇², log₂

**Test with CASSI forward model:**
```latex
y = \Phi x + \varepsilon
```
- [ ] Renders as proper math (not plaintext)

---

## V7 — Read-Only Guarantee

- [ ] No wallet connection UI (no MetaMask, no WalletConnect)
- [ ] No login/signup flow
- [ ] No POST/PUT/DELETE endpoints exposed to frontend
- [ ] `/submit` page calls pwm-node CLI (not direct contract writes)
- [ ] All data fetched via GET API endpoints
- [ ] Works in private/incognito browser mode

---

## V8 — Mobile Responsiveness

Test at these breakpoints:
- [ ] 375px width (iPhone SE / small phone)
- [ ] 768px width (tablet)
- [ ] 1024px width (small laptop)
- [ ] 1440px width (desktop)

For each breakpoint:
- [ ] Tables are scrollable or stack vertically
- [ ] Navigation is accessible (hamburger menu or similar)
- [ ] Text is readable without zooming
- [ ] Buttons/links are tappable (min 44px touch target)

---

## V9 — Browser Compatibility

| Browser | Desktop | Mobile | Works? |
|---------|---------|--------|--------|
| Chrome | latest | Android | [ ] |
| Firefox | latest | — | [ ] |
| Safari | latest | iOS | [ ] |

Minimum checks per browser:
- [ ] Home page loads
- [ ] /principles table renders with data
- [ ] /cert/<hash> shows S1-S4 badges
- [ ] Math formulas render on /principles/<id>
- [ ] No console errors

---

## V10 — Deployment

### docker-compose.yml structure:
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

- [ ] `docker-compose up` starts all 3 services
- [ ] Frontend accessible on port 3000
- [ ] API accessible on port 8000
- [ ] Indexer starts syncing events on startup

### Nginx reverse proxy:
- [ ] `/api/*` → api:8000
- [ ] `/*` → frontend:3000
- [ ] Target domain: `pwm.platformai.org`

---

## V11 — Testnet Validation

- [ ] All 500 genesis principles appear at `/principles`
- [ ] Principle count matches expected (~500)
- [ ] Submit a test certificate on testnet → `/cert/<hash>` shows correct data within 10 minutes
- [ ] Leaderboard at `/leaderboard/<benchmark_id>` updates after DrawSettled event
- [ ] `/cert/<hash>` shows S1-S4 verdicts and reward breakdown correctly
- [ ] Pool sizes at `/pools` match on-chain values

---

## V12 — Performance

- [ ] Home page loads in < 3 seconds
- [ ] /principles page loads 500 rows in < 5 seconds
- [ ] API responses cached (Cache-Control: max-age=60)
- [ ] No N+1 query patterns in API (batch database queries)
