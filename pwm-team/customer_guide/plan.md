# PWM Customer Experience Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the PWM explorer from a working-but-thin testnet UI into a customer-grade interface where researchers, students, regulators, and bounty contributors can use the protocol without internal context.

**Architecture:** Pure off-chain changes — backend SQLite indexer + FastAPI endpoints + Next.js frontend pages. **Zero on-chain modifications. Zero contract redeployment. Zero `mainnet-v1.0.0` audit-clean tag drift.**

**Tech stack:** Python (FastAPI + SQLite indexer), TypeScript / Next.js (frontend), Solidity contracts read-only via ethers/web3.py, Bash + Python scripts.

**Source of truth (already shipped):**
- 7 contracts on Sepolia (chainId 11155111), audit-clean tag `mainnet-v1.0.0`
- 531 L1 Principles in genesis catalog (502 v1 + 8 v3 standalone + 21 v2 PWDR + analytical cores)
- 4 reference implementations (scoring 81 tests, CLI 73 tests, miner 101 tests, web 27 tests)
- Web explorer live at `https://explorer.pwm.platformai.org` (Sepolia mode)
- MST-L + EfficientSCI wrapper solvers ready (`pwm-team/pwm_product/reference_solvers/`)
- Walkthrough script `scripts/testnet_mine_walkthrough.sh` for first cert submissions

---

## Part A — What PWM is (background, copied from customer guide)

PWM is a 4-layer protocol for evaluating computational-science methods:

| Layer | What it is | Action verbs |
|---|---|---|
| **L1 Principle** | Physics declaration: forward model + parameter space + DAG primitive chain + complexity score | Author + register (one-time per Principle); browse / inspect (consumers) |
| **L2 Spec** | Mathematical contract: six-tuple (Ω, E, B, I, O, ε) for one concrete instance of the parent L1 | Author + register (one-time); read math contract (consumers) |
| **L3 Benchmark** | P-benchmark with rho=50 instances + anti-overfitting M1-M6 + dataset_registry pinned to IPFS | Author + register (one-time); download data + evaluate solvers (consumers) |
| **L4 Solution** | A certificate (cert_hash + Q score + benchmark binding) submitted by a CP after running a solver | Mine (repeatedly per submitter per benchmark); verify (consumers); finalize (after 7-day challenge) |

Plus **staking** as orthogonal economic backing: anyone can stake PWM on an L1 (~$50), L2 (~$5), or L3 (~$1) tier to back its credibility.

**Two roles:**
- **Producers** = founders, bounty authors, external developers with a new principle (small fraction of users)
- **Consumers** = researchers, students, industry teams, auditors, regulators (vast majority — the protocol is designed to make their experience frictionless)

**Five concrete user journeys** (the protocol is designed for these specifically):
1. PhD student comparing their CASSI method to SOTA
2. AI imaging vendor proving robustness for FDA submission
3. Regulator verifying a vendor's published claim
4. External developer authoring a new Principle (Bounty #7 Tier B)
5. Founder mining the leaderboard (Director's current path)

Full reference: `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md`.

---

## Part B — Why the explorer doesn't yet serve customers well

Three Director-identified UX gaps from 2026-05-02 / 2026-05-03 review:

### B1. Numeric IDs (`L1-003`) are opaque

Customers see "L1-003" and don't know it means CASSI. The data is
already there (every manifest has a `title` field with the
human-readable name); the display layer just isn't using it
consistently.

### B2. No rank visibility for contributors

Users submit solutions on `/contribute` but get no feedback on what
rank their submission landed at. The very thing PWM incentivizes
(better-than-reference solvers) gets no visible acknowledgement.

### B3. Reference floor and current SOTA are conflated

`/benchmarks/L3-003` shows "Reference PSNR: 26.49 dB" — a static
GAP-TV baseline labeled as "reference." This conflates two distinct
concepts:

- **Reference baseline (floor)** — deliberately-weak solver
  everyone competes against (~26.49 dB GAP-TV); static
- **Current SOTA (ceiling)** — best on-chain cert score for this
  benchmark (e.g., 34.1 dB MST-L); dynamic

The delta between them IS the protocol's value proposition (PWM
enabled +7.6 dB improvement on CASSI). The current page shows
neither story clearly.

### B4. No documented contribution path for external authors

When a user wants to contribute a new Principle, there's no
documented procedure for ID assignment. Risks: collisions
(two contributors both claim L1-555), sparse numbering (L1-100,
L1-500, L1-9999 hides catalog activity).

### B5. Repository is private

`integritynoble/pwm` is currently Director's private repo —
external bounty claimants, researchers citing PWM, auditors, grant
reviewers, and external Bounty #7 authors cannot interact with it
end-to-end.

---

## Part C — Implementation plan

Three phases, sequenced by impact + effort. Each phase is shippable
independently. No phase requires touching contracts or breaking the
audit-clean tag.

---

### Phase 1 — Leaderboard display (rank + SOTA/floor/delta)

**Why first:** Highest customer-facing impact; easiest to verify
end-to-end on Sepolia today; tells the protocol's "permissionless
improvement" story in one glance — exactly what CZI EOSS / NSF POSE
adoption-evidence sections demand.

**Effort:** ~2 days CPU work, single PR.

**Files:**
- Create: `pwm-team/infrastructure/agent-web/api/tests/test_leaderboard.py`
- Modify: `pwm-team/infrastructure/agent-web/api/main.py` (add `/api/leaderboard/{benchmark_id}` endpoint)
- Modify: `pwm-team/infrastructure/agent-web/api/store.py` (rank query + cert_meta join)
- Modify: `pwm-team/infrastructure/agent-web/indexer/db.py` (cert_meta read helper)
- Modify: `pwm-team/infrastructure/agent-web/frontend/app/benchmarks/[ref]/page.tsx` (SOTA / Reference / Delta header + leaderboard table)
- Modify: `pwm-team/infrastructure/agent-web/frontend/app/contribute/page.tsx` (per-submission rank column with badges)

**API contract (new):**

```
GET /api/leaderboard/{benchmark_id}

200 OK:
{
  "benchmark_id": "L3-003",
  "benchmark_title": "Coded Aperture Snapshot Spectral Imaging",
  "reference": { "label": "GAP-TV (numpy)", "score_q": 0.55, "psnr_db": 26.49, "source": "off-chain reference" },
  "current_sota": {
    "cert_hash": "0xb293...", "label": "MST-L", "score_q": 0.82, "psnr_db": 34.1,
    "submitter": "0xab12...cd34", "block_number": 10720312,
    "submitted_at": "2026-05-03T14:23:11Z",
    "status": "pending_challenge", "challenge_ends": "2026-05-10T14:23:11Z"
  },
  "improvement_db": 7.6,
  "ranks": [
    { "rank": 1, "cert_hash": "0xb293...", "label": "MST-L", "score_q": 0.82, "psnr_db": 34.1, "status": "pending_challenge" },
    { "rank": 2, "cert_hash": "0x4ab1...", "label": "PnP-HSICNN", "score_q": 0.71, "psnr_db": 31.8, "status": "finalized" },
    ...
  ]
}
```

**Tasks:**

- [x] **1.1 — Write failing test** `test_leaderboard.py::test_empty_leaderboard_returns_reference_floor`
  - Hit `/api/leaderboard/L3-003` with no on-chain certs → expect `current_sota = null`, `reference.psnr_db = 26.49`
- [x] **1.2 — Run test, confirm 404** (endpoint doesn't exist yet)
- [x] **1.3 — Add endpoint to `api/main.py`** with empty stub returning placeholder JSON
- [x] **1.4 — Confirm test now fails on JSON content** (not 404)
- [x] **1.5 — Implement `store.py::get_leaderboard(benchmark_id)`** — SQL query joining `certs` + `cert_meta` with `RANK() OVER (PARTITION BY benchmarkHash ORDER BY q DESC)`
- [x] **1.6 — Wire endpoint to store function**, return real JSON
- [x] **1.7 — Test passes**
- [x] **1.8 — Add test** `test_leaderboard.py::test_one_cert_appears_as_rank_1`
  - Insert a cert + cert_meta row; expect `current_sota.rank == 1`
- [x] **1.9 — Test passes** (no extra impl needed)
- [x] **1.10 — Add test** `test_leaderboard.py::test_three_certs_ranked_by_q`
  - Insert 3 certs with q = 0.5, 0.7, 0.9; expect ranks [3, 2, 1]
- [x] **1.11 — Test passes**
- [x] **1.12 — Add test** `test_leaderboard.py::test_improvement_delta_computed_from_reference_psnr`
  - Reference = 26.49 dB, SOTA cert PSNR = 34.1 → expect `improvement_db ≈ 7.6`
- [x] **1.13 — Test passes**
- [x] **1.14 — Frontend: update `/benchmarks/[ref]/page.tsx`** — add SOTA / Reference / Delta header section
- [x] **1.15 — Frontend: update `/benchmarks/[ref]/page.tsx`** — replace single-number display with leaderboard table
- [x] **1.16 — Frontend: update `/contribute/page.tsx`** — add per-submission rank column with 🥇🥈🥉🎗 badges
- [x] **1.17 — Smoke test end-to-end on local docker compose**
- [x] **1.18 — Commit + push as `feat/leaderboard-display`**
- [x] **1.19 — Open PR for Director review + merge**
- [ ] **1.20 — Director: SSH to GCP server, redeploy explorer**

**Done when:** Visiting `https://explorer.pwm.platformai.org/benchmarks/L3-003` shows the SOTA / Reference / Delta header; visiting `/contribute?section=solution` shows rank columns. Both render correctly even with zero on-chain certs (empty-leaderboard fallback to reference floor).

---

### Phase 2 — Human-readable IDs and contribution paths

**Why second:** Requires Phase 1's display layer is in place; introduces
new manifest field that needs hash-invariance protection; less urgent
than the SOTA story.

**Effort:** ~6 hours CPU work, single PR.

**Files:**
- Modify (bulk): all 531 manifests under `pwm-team/pwm_product/genesis/l{1,2,3}/` and `pwm-team/content/agent-{imaging,physics,chemistry,applied,signal}/principles/...` — add `display_slug` field
- Modify: `scripts/register_genesis.py` — add `UI_ONLY_FIELDS` filter so `display_slug` is stripped before keccak256
- Modify: `pwm-team/infrastructure/agent-cli/pwm_node/commands/inspect.py` — render `<title> (<id>)`
- Modify: `pwm-team/infrastructure/agent-cli/pwm_node/commands/benchmarks.py` — same
- Modify: `pwm-team/infrastructure/agent-web/frontend/app/principles/page.tsx` — title-first display
- Modify: `pwm-team/infrastructure/agent-web/frontend/app/benchmarks/[ref]/page.tsx` — title-first display
- Create: `pwm-team/coordination/PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md` — claim-board → author → PR flow
- Modify: `pwm-team/coordination/agent-coord/interfaces/bounties/07-claims.md` — extend FCFS claim board to general contributions (not just Bounty #7)
- Modify: `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md` — add "Contributing a new Principle" section

**Slug naming convention:**
- Lowercase, hyphen-separated: `cassi`, `pillcam-bleeding`, `dual-energy-ct`
- Common abbreviations preferred when widely recognized: `qsm`, `mri`, `ecg`, `xrd`
- Full descriptor when no abbreviation: `chromatic-confocal`, `bone-fracture-xray`
- No domain prefix in slug (domain belongs in the `domain` field)

**Critical invariant — hash invariance under display_slug edits:**

```python
# In register_genesis.py:
UI_ONLY_FIELDS = {"display_slug", "display_color", "ui_metadata"}

def _canonical_for_hashing(obj):
    return {k: v for k, v in obj.items() if k not in UI_ONLY_FIELDS}

def _canonical_json(obj):
    filtered = _canonical_for_hashing(obj)
    return json.dumps(filtered, sort_keys=True, separators=(",", ":")).encode("utf-8")
```

Otherwise re-hashing manifests with the new field would produce
different on-chain hashes → break `pwm-node mine`'s benchmark-hash
lookup.

**Tasks:**

- [x] **2.1 — Author** `scripts/add_display_slugs.py` — deterministic generator that reads each manifest, derives a slug from `title` + filename, writes `display_slug` field back
- [x] **2.2 — Run** `scripts/add_display_slugs.py --dry-run` to preview slug list
- [x] **2.3 — Director reviews** the dry-run output for any slugs to fix
- [x] **2.4 — Run** `scripts/add_display_slugs.py` for real on all 531 manifests
- [x] **2.5 — Update** `register_genesis.py` with `UI_ONLY_FIELDS` filter
- [x] **2.6 — Add test** `test_register_genesis.py::test_hash_invariant_under_display_slug_edit` — load a manifest, hash it, add `display_slug`, hash again → hashes equal
- [x] **2.7 — Test passes**
- [x] **2.8 — Update** `pwm-node inspect` to render `<title> (<id>)` first
- [x] **2.9 — Update** `pwm-node benchmarks` to render `<title> (<id>)` first
- [x] **2.10 — Update frontend** `principles/page.tsx` — title-first
- [x] **2.11 — Update frontend** `benchmarks/[ref]/page.tsx` — title-first
- [x] **2.12 — Add slug-based URL routing** `/benchmarks/cassi` redirects to `/benchmarks/L3-003`
- [x] **2.13 — Author** `PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md` — claim-board flow
- [x] **2.14 — Update** `interfaces/bounties/07-claims.md` — open to general contributions
- [x] **2.15 — Update** customer guide — add "Contributing a new Principle" section
- [x] **2.16 — Smoke test end-to-end on local docker compose**
- [x] **2.17 — Commit + push as `feat/human-readable-ids`**
- [x] **2.18 — Open PR for Director review + merge**
- [ ] **2.19 — Director: SSH to GCP server, redeploy explorer**

**Done when:** Every page in the explorer shows `Coded Aperture Snapshot Spectral Imaging (L1-003)` not bare `L1-003`; URLs accept both `/benchmarks/cassi` and `/benchmarks/L3-003`; new contributors have a documented path to claim L1-532 and beyond.

---

### Phase 3 — Public repo (so external customers can actually use PWM)

**Why third:** The biggest blocker for external adoption, but also
the highest-risk change because it exposes commit history. Should
wait until Phases 1+2 land so the public repo immediately presents
a polished customer experience.

**Effort:** ~4 hours CPU work + Director sign-off on what to expose.

**Three options:**

| # | Option | Effort | Risk |
|---|---|---|---|
| 3a | Flip `integritynoble/pwm` to public directly | 1 click | **High** — exposes all commit history; requires audit for past sensitive content |
| 3b | Create new clean public repo (`integritynoble/pwm-public` or `pwm-platformai/pwm`); push only sanitized content | ~4 hr | **Low** — full control over what's exposed; private repo retained for internal ops |
| 3c | Expand existing public `Physics_World_Model` repo to include `pwm-team/` | ~2 hr | **Medium** — repo already exists; need to verify nothing sensitive was ever pushed |

**Recommended:** Option 3b (new clean public repo). Lowest risk, highest control.

**Files:**
- New repo: `integritynoble/pwm-public` (or `pwm-platformai/pwm`)
- Mirror selection: `pwm-team/pwm_product/`, `pwm-team/infrastructure/agent-{contracts,scoring,cli,miner,web}/`, `pwm-team/customer_guide/`, `scripts/`, `papers/Proof-of-Solution/mine_example/science/` (manifests + reference solvers + contracts + CLI + customer guide)
- Excluded from public: `pwm-team/coordination/` (internal team docs), any `.env*` files, internal Slack screenshots, founder-key-related notes

**Tasks:**

- [x] **3.1 — Run pre-flight audit** with `gitleaks` + `trufflehog` on full history of `integritynoble/pwm`
- [ ] **3.2 — Director reviews** the secrets-scan output; flag anything sensitive
- [x] **3.3 — Run pre-flight audit** with grep over commit history for emails / personal data / internal hostnames
- [ ] **3.4 — Director reviews** PII-scan output
- [x] **3.5 — Decide:** option 3a / 3b / 3c (Director makes the call)
- [x] **3.6 — If 3b: Director creates new public repo on GitHub**
- [x] **3.7 — Author** `scripts/sync_to_public_repo.sh` — `git filter-repo` based selective mirror
- [ ] **3.8 — Director runs** `scripts/sync_to_public_repo.sh` (interactive — needs Director's GitHub credentials)
- [x] **3.9 — Update doc references** — find all `integritynoble/pwm` references in coordination docs, customer guide, READMEs, CLI install instructions; replace with public URL where appropriate
- [x] **3.10 — Update `pwm-node` CLI install instructions** in agent-cli/README.md — use public repo URL
- [x] **3.11 — Update web explorer** `view-on-github` links — point to public repo
- [x] **3.12 — Update bounty specs** — public repo URL in claim instructions
- [ ] **3.13 — Director: redeploy explorer with new GitHub URL**
- [ ] **3.14 — Smoke test:** open the public repo URL in incognito browser; clone it as a fresh user; run `pwm-node --network testnet benchmarks` against the cloned copy

**Done when:** A new external user can `git clone <public-repo>`, `pip install -e pwm-team/infrastructure/agent-cli`, and run `pwm-node match "hyperspectral inverse problem"` end-to-end without any private-repo access.

---

## Part D — Sequencing and dependencies

```
Phase 1 (leaderboard display)        ←─── ships independently
   │
   │ informs Phase 2 (display layer is in place)
   ↓
Phase 2 (human-readable IDs)         ←─── ships after Phase 1
   │
   │ informs Phase 3 (public repo presents polished UX)
   ↓
Phase 3 (public repo)                ←─── ships after Phase 2
```

**Total CPU effort:** ~3 days (Phase 1) + ~6 hours (Phase 2) + ~4 hours (Phase 3) = **~5 days CPU work**.

**Director-side time:** ~2 hours total (review PRs, run docker compose redeploys, decide repo option, run mirror script).

**No phase touches:**
- Solidity contracts
- On-chain state
- Sepolia ETH spending
- `mainnet-v1.0.0` audit-clean tag
- Mainnet deploy timeline (which is gated on D3 hardware-wallet shipping anyway, running in parallel)

---

## Part E — Decision points for Director

Before authorizing implementation, please confirm:

| # | Decision | Default | Note |
|---|---|---|---|
| **D1** | Approve Phase 1 (leaderboard display) — ship `feat/leaderboard-display` PR | Yes (recommended) | 2 days; highest customer impact |
| **D2** | Approve Phase 2 (human-readable IDs + slugs + contribution path) | Yes (recommended) | 6 hours; depends on Phase 1 |
| **D3** | Approve Phase 3 (public repo) | Pending audit results | 4 hours; biggest blocker for external adoption |
| **D4** | For Phase 3, which option: 3a (flip current to public) / 3b (new clean repo) / 3c (expand existing public) | 3b (clean repo) | Lowest risk |
| **D5** | Should leaderboard display the static reference floor alongside dynamic SOTA, or replace with SOTA only? | Both visible | The delta IS the protocol value proposition |
| **D6** | Sequence: 1 → 2 → 3, or parallel? | Sequential | Easier to review one at a time |

---

## Part F — What this plan does NOT cover (out of scope)

- **Mainnet deploy (D1-D10)** — separate track, gated on hardware wallets per `MAINNET_BLOCKERS_2026-04-30.md`
- **Contract changes** — `mainnet-v1.0.0` audit-clean tag stays untouched
- **MST-L / EfficientSCI mining** — that's Director's Option C handoff, runs in parallel with this plan
- **Bounty payouts** — those flow automatically from on-chain `PWMReward` after challenge period; not part of UX plan
- **Funding applications** — separate track per `PWM_FUNDING_PI_AND_INSTITUTIONAL_APPLICANT_2026-05-02.md`
- **Coordination docs cleanup** — internal-team rearrangement, separate

---

## Cross-references (sources combined into this plan)

- `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md` — full descriptive guide for all 4 layers (consumer + producer flows)
- `pwm-team/coordination/PWM_LEADERBOARD_DISPLAY_DESIGN_2026-05-03.md` — Phase 1 design specifics
- `pwm-team/coordination/PWM_HUMAN_READABLE_IDS_AND_CONTRIBUTION_FLOW_2026-05-03.md` — Phase 2 design specifics + contribution paths
- `pwm-team/coordination/PWM_TESTNET_TESTING_GUIDE_2026-05-02.md` — testnet usage context
- `pwm-team/coordination/PWM_OPTION_C_HANDOFF_GPU_SUBMISSION_2026-05-02.md` — Director's path to populating leaderboard with first cert
- `pwm-team/coordination/MAINNET_BLOCKERS_2026-04-30.md` — what's deliberately out-of-scope for this plan

---

## Approval

When Director approves this plan, CPU agent will execute Phase 1 (then 2, then 3) following the task list above. Tell me **"go phase 1"** to start with the leaderboard display PR. Or **"go all phases sequential"** to run all three end-to-end with a checkpoint review between each.

Director can also redirect: pause any phase, re-order, drop a phase entirely, or add new requirements before implementation starts.
