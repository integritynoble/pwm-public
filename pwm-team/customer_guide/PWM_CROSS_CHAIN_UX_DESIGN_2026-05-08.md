# Cross-Chain UX Design — Same User Experience on Sepolia and Base Mainnet

**Date:** 2026-05-08
**Audience:** Director, frontend / CLI maintainers, customers running solvers on both chains
**Trigger question (Director, 2026-05-08):**
> "Is it possible that users who use solution or benchmark get the
> same using experience when using them when L1, L2, L3 and L4 are
> deployed in testnet and mainnet?"

---

## TL;DR

**Yes, by design.** The protocol was built chain-agnostic from day
one: same CLI, same explorer URL pattern, same manifest schemas,
same keccak256 hashing recipe, same cert payload format. A user
browsing CASSI sees the same view on both chains — only the
chain-identity context differs (chain ID, gas currency, leaderboard
population).

Three nice-to-have UX gaps remain (chain badge, compare command,
multi-broadcast); all are non-blocking.

---

## 1. What's identical across Sepolia and Base mainnet

The protocol design forces these to be the same on every chain:

### 1.1 CLI surface

```bash
# Browse — chain-agnostic (offline)
pwm-node principles                                    # 2 founder-vetted on Sepolia today
pwm-node benchmarks                                    # same
pwm-node inspect L3-003                                # same manifest, same output

# Mine — chain-specific via --network
pwm-node mine L3-003 --solver foo.py --network testnet
pwm-node mine L3-003 --solver foo.py --network mainnet
# → identical solver invocation, identical Q computation,
#   identical cert payload structure; only the on-chain destination differs

# Stake / verify / submit — same flow, just different --network
pwm-node stake principle 0x<L1-hash> --network testnet
pwm-node stake principle 0x<L1-hash> --network mainnet
```

The CLI takes `--network` as a single dispatch parameter that
resolves into:
- a different RPC URL (`SEPOLIA_RPC_URL` vs `BASE_RPC_URL`)
- a different `addresses.json` block (`testnet:` vs `mainnet:`)
- a different `chainId` for transaction signing (11155111 vs 8453)

Everything else stays identical.

### 1.2 Explorer URL patterns

```
/benchmarks/L3-003                  — benchmark detail (same data shape)
/benchmarks/cassi                    — slug routing (same)
/cert/0x<hash>                       — cert detail (same payload schema)
/principles/L1-003                   — principle detail (same)
/leaderboard/<benchmark_hash>        — top-10 view (same)
/api/leaderboard/L3-003              — JSON API (same response shape)
/api/cert-meta/<hash>                — POST cert-meta enrichment (same endpoint)
```

The explorer at `https://explorer.pwm.platformai.org` serves both
chains via a `?network=testnet|mainnet` query string (or a sub-domain
split — `testnet.explorer.pwm.platformai.org` vs
`mainnet.explorer.pwm.platformai.org` when both are live). The page
shells, the API contract, and the field names are bytewise identical.

### 1.3 Manifest hashes (chain-agnostic)

`keccak256(canonical_json(manifest))` is computed by stripping
`UI_ONLY_FIELDS` and serialising sorted-keys / no-whitespace —
nothing in this recipe depends on chain context. So:

```
canonical_hash(L1-003.json)  ==  0xe3b1328c66835cd729fa50650ef1d1bac4aa407807d6d97d4979e988a99a51ea

is the same value on every chain.

The on-chain registration is identified by the triple
(chain_id, registry_addr, hash), but the artifact's keccak256 is
chain-agnostic.
```

This means a user verifying "is this manifest the same on both
chains" only needs to check that the triple matches on each chain;
the artifact identity is preserved across registration boundaries.

### 1.4 Cert payload structure (15 fields)

Per `pwm-team/infrastructure/agent-contracts/contracts/PWMCertificate.sol`:

```
12 chain-bound fields (canonical_json keccak256'd → certHash):
  Q_int, benchmarkHash, principleId, delta,
  spWallet, acWallet, cpWallet,
  l1Creator, l2Creator, l3Creator,
  shareRatioP, submittedAt

3 _meta sidecar fields (off-chain, in cert_meta SQL row):
  solver_label, psnr_db, runtime_sec, framework, meta_url
```

Same on both chains. The same payload submitted via `pwm-node mine`
to Sepolia produces the *same `certHash`* as submitted to Base
mainnet — they're the same cert hash, just registered on different
chains. This makes cross-chain "did the same solver produce the same
result" trivial to verify.

### 1.5 S1-S4 gate code

The gates run as Python (`pwm_scoring/gates.py`) before any chain
interaction. The same code runs locally on the miner's machine
regardless of which chain the cert eventually goes to. So any cert
that passes S1-S4 on Sepolia would pass them on Base mainnet — the
gate verdict is independent of chain.

### 1.6 Reward share formula

The 40/5/2/1×7 rank-share table is **constitutional** — hardcoded as
`PWMReward.sol` constants:

```solidity
uint16 public constant RANK1_SHARE = 4_000;  // 40%
uint16 public constant RANK2_SHARE =   500;  // 5%
uint16 public constant RANK3_SHARE =   200;  // 2%
uint16 public constant RANK4_10_SHARE = 100; // 1% each
```

Same on every chain. A rank-1 cert gets 40% of its pool whether the
pool is testnet PWM or Base mainnet PWM.

### 1.7 Solver invocation contract

The framework calls solvers as:
```
python <solver.py> --input <work_dir>/input/ --output <work_dir>/output/
```

Solvers are chain-blind. They don't know whether their cert lands
on Sepolia or Base mainnet — the only thing they touch is the
filesystem. This is a deliberate separation: the solver is the
*algorithm*, the cert is the *payment artifact*.

---

## 2. What necessarily differs (chain identity)

By contrast, these CANNOT be the same — they identify the chain
itself:

| Aspect | Sepolia | Base mainnet |
|---|---|---|
| Chain ID | 11155111 | 8453 |
| Tx explorer | `sepolia.etherscan.io/tx/0x…` | `basescan.org/tx/0x…` |
| Gas currency | Free Sepolia ETH (faucet — `https://sepoliafaucet.com`) | Real ETH on Base (~$0.005 per cert tx today) |
| Reward currency | Sepolia PWM (testnet token, no real value) | PWM (real, tradeable) |
| RPC URL | `SEPOLIA_RPC_URL` (e.g. publicnode) | `BASE_RPC_URL` (e.g. base-mainnet.g.alchemy.com) |
| Registry contract address | `0x2375217dd8FeC420707D53C75C86e2258FBaab65` | (set at D9 deploy) |
| Certificate contract address | `0x8963b60454EC1D9F65eE3cbF7aBC5D1220C3dB08` | (set at D9 deploy) |
| Founder wallets | 5 Sepolia addresses | 5 Base mainnet addresses (different keys, hardware-wallet-protected) |
| Cert population | Whoever submitted to Sepolia (mostly founders + early miners during testnet) | Whoever submits to Base mainnet (production miners) |
| Per-benchmark challenge window | Independently tunable (multisig may keep 7d on Sepolia for verification, shorten on Base) | Independently tunable |
| Pool funding | Sepolia minting from `M_pool` allocation (capped at `maxBenchmarkPoolWei`) | Base mainnet minting (real PWM emission) |

These differences are **inherent to the chains being separate** —
no design tweak removes them. They're the boundary between "test
environment" and "production environment" that PWM inherits from
Ethereum's L1/L2 architecture.

---

## 3. Three identified UX gaps

The structural answer in §§ 1–2 is "yes, the experience is consistent
by design." But there are three concrete UX gaps that, while
non-blocking, would tighten the cross-chain feel:

### Gap 1 — No visible chain badge on explorer pages

**Problem.** A user landing on `/cert/0xabc…` or `/benchmarks/L3-003`
sees the same UI shell on both chains. They don't immediately know
whether the cert they're looking at is a Sepolia testnet cert
(reward = 0 real PWM) or a Base mainnet cert (reward = real PWM).
This is fine when the user comes via a known link, but a user
who pastes a hash into the search bar without thinking about chain
context can mis-read the cert's value.

**Proposed fix.** A coloured pill in the page header:

```
┌────────────────────────────────────────────────────────────┐
│  Cert  0xabc…def     [TESTNET — Sepolia]  ← yellow pill    │
│        rank 1 · Q_int 70 · MST-L (off-chain)               │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Cert  0xabc…def     [MAINNET — Base]     ← blue pill      │
│        rank 1 · Q_int 70 · MST-L (off-chain)               │
└────────────────────────────────────────────────────────────┘
```

**Implementation sketch.**

- File: `pwm-team/infrastructure/agent-web/frontend/components/ChainBadge.tsx`
- Reads `network` from the URL query string (`?network=testnet`
  or `?network=mainnet`) or from the API response (`/api/network`
  endpoint already returns `{network: "testnet"|"mainnet"}`).
- Renders a Tailwind pill with `bg-yellow-500/10` / `text-yellow-400`
  for testnet, `bg-blue-500/10` / `text-blue-400` for mainnet.
- Mounts in the page header on every detail route:
  `/cert/[hash]/page.tsx`, `/benchmarks/[ref]/page.tsx`,
  `/principles/[id]/page.tsx`, `/leaderboard/[hash]/page.tsx`.
- Add a unit test asserting the pill renders the right text given
  a mocked network.

**Effort.** ~2 hours (component + 4 page integrations + 1 unit test).

**Risk.** None — pure additive UI. Doesn't touch contracts, API, or
indexer.

### Gap 2 — No `pwm-node compare` command

**Problem.** A user wanting to confirm "the same cert was submitted
to both Sepolia and Base mainnet" has to:

```bash
pwm-node --network testnet inspect <sepolia-cert-hash>
pwm-node --network mainnet inspect <mainnet-cert-hash>
# → manually diff the outputs
```

This is fine for technical users but tedious. A common case is a
miner who deployed to both chains and wants to verify the certs are
structurally identical (everything except `submittedAt`, `tx_hash`,
`block_number` should match — those are chain-context).

**Proposed fix.** A `pwm-node compare` command:

```bash
pwm-node compare 0x<cert-hash-1> --vs 0x<cert-hash-2>
# Output:
#   Q_int            : 70 == 70                           ✓ MATCH
#   benchmarkHash    : 0xdc8a… == 0xdc8a…                ✓ MATCH
#   submitter        : 0x0c56… == 0x0c56…                ✓ MATCH
#   shareRatioP      : 5000 == 5000                      ✓ MATCH
#   chain_a          : sepolia
#   chain_b          : base-mainnet
#   submittedAt diff : 47 days, 3 hours                  ⚠ chain context
#   block_number diff: differs (chain-specific)          ⚠ chain context
#   Verdict          : SAME LOGICAL CERT (chain context differs as expected)
```

**Implementation sketch.**

- File: `pwm-team/infrastructure/agent-cli/pwm_node/commands/compare.py`
- New subcommand registered in `__main__.py`:
  ```python
  cmp_p = sub.add_parser("compare", help="Diff two certs across chains")
  cmp_p.add_argument("cert_a", help="0x… cert hash on chain A")
  cmp_p.add_argument("--vs", required=True, help="0x… cert hash on chain B")
  cmp_p.add_argument("--chain-a", default="testnet")
  cmp_p.add_argument("--chain-b", default="mainnet")
  ```
- Resolves each hash via the API (`/api/cert/<hash>?network=…`)
  on each chain, decodes the canonical 12-field payload, prints
  field-by-field diffs.
- Special-cases `submittedAt`, `block_number`, `tx_hash` as
  "chain context — different is expected" rather than "match
  fail".
- New tests in `agent-cli/tests/test_compare.py` covering match,
  mismatch in `Q_int` (real divergence), mismatch in `submittedAt`
  (chain context — should pass).

**Effort.** ~1 day (subcommand + API resolution + diff renderer +
tests).

**Risk.** Low. Purely client-side; no contract or indexer changes.

### Gap 3 — No "submit to both chains" wizard

**Problem.** A miner who wants belt-and-suspenders coverage
(submit to Sepolia for the audit trail + submit to Base mainnet
for the real reward) has to run `pwm-node mine` twice, with two
different `--network` flags, on two different RPCs. The solver
gets re-executed on each chain (or the miner has to pre-stage the
solver output and `--use-cached`).

**Proposed fix.** A `pwm-node mine ... --networks testnet,mainnet`
plural form:

```bash
pwm-node mine L3-003 \
  --solver pwm-team/pwm_product/reference_solvers/cassi/cassi_mst.py \
  --networks testnet,mainnet                              # plural

# Output:
#   [mine] running solver: cassi_mst.py
#   [mine]   runtime=12.3s  PSNR=35.295 dB  Q=0.353
#   [mine]   cert_hash:      0x7c7740…e13                ← same hash for both chains
#   [mine] broadcasting to testnet:
#   [mine]   tx submitted:   0x8883a90d…
#   [mine]   gas:            0.00012 ETH (Sepolia, free)
#   [mine] broadcasting to mainnet:
#   [mine]   tx submitted:   0xfedc…
#   [mine]   gas:            0.00045 ETH (Base, ~$1.20)
#   [mine] both certs registered; finalize each independently after challenge windows
```

The solver runs once; the cert payload is computed once; the same
`certHash` is submitted to both chains as separate transactions.

**Implementation sketch.**

- Modify `pwm-team/infrastructure/agent-cli/pwm_node/commands/mine.py`:
  - Accept `--networks` plural (comma-separated) as an alternative
    to `--network`.
  - After `_run_solver` + `_compute_q`, loop the broadcast step
    once per chain.
  - Each broadcast uses the chain's RPC + addresses + signing key
    (currently uses the same `PWM_PRIVATE_KEY` env var; works as
    long as the key holds funded wallets on both chains).
- Add tests in `agent-cli/tests/test_mine_multi_chain.py`:
  - Mock both RPC endpoints
  - Assert solver runs once, payload is computed once, two
    transactions are broadcast.
- Edge cases:
  - If one broadcast fails (e.g. mainnet RPC down), fall back to
    submitting only to the other chain; print warning.
  - If the wallet has insufficient gas on one chain, skip that
    chain with a clear error.
  - Default `--networks` to a single chain (`testnet`) so existing
    workflows don't break.

**Effort.** ~2-3 days (CLI changes + RPC retry + multi-chain tests +
docs update).

**Risk.** Medium. Touches the mine command which is the most-used
miner code path. Needs careful testing — a bug here could lose a
miner real money on Base mainnet.

---

## 4. The full updated picture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PWM CROSS-CHAIN UX (post-2026-05-08 design)                              │
└─────────────────────────────────────────────────────────────────────────────┘

  STRUCTURAL (already chain-agnostic — zero work)
  ───────────────────────────────────────────────
    CLI surface          : same commands, --network dispatch
    Explorer URLs        : same paths, network in query / sub-domain
    Manifest hashes      : keccak256 chain-agnostic
    Cert payload         : same 15-field schema
    Gate code            : pwm_scoring/*.py — chain-blind
    Reward formula       : constitutional — hardcoded
    Solver contract      : --input/--output dirs, chain-blind

  CHAIN IDENTITY (cannot be hidden)
  ─────────────────────────────────
    Chain ID, gas currency, RPC URL, registry/cert/governance addrs,
    founder wallets, real PWM vs testnet PWM, leaderboard population

  UX GAPS (proposed adds)
  ───────────────────────
    Gap 1: chain badge on explorer detail pages          ~2 hours
    Gap 2: pwm-node compare cert_a --vs cert_b           ~1 day
    Gap 3: pwm-node mine --networks testnet,mainnet      ~2-3 days
```

---

## 5. Open decisions for Director

| Decision | Default recommendation | When to act |
|---|---|---|
| **D1.** Implement Gap 1 (chain badge) | **Yes — quick win.** Pure UI; no risk; clearly improves the "am I on testnet or mainnet" intuition. | Before D9 mainnet launch (so first mainnet visitors see the badge from day one) |
| **D2.** Implement Gap 2 (`pwm-node compare`) | **Yes — useful for power users.** Low risk; helps miners running both chains. | Post-D9; not blocking mainnet launch |
| **D3.** Implement Gap 3 (multi-broadcast `--networks` plural) | **Defer until contributor demand surfaces.** Touches the most-trafficked CLI path; risk of breaking single-chain workflows. Most miners won't use it. | If 5+ miners ask for it OR if Director wants it as an audit-trail feature |
| **D4.** Add chain identity to cert-meta sidecar (so cross-chain compare is one query) | **No — redundant.** The cert hash already uniquely identifies the cert; chain context is in the indexer's `(chain_id, hash)` pair already. | If indexer schema needs revision anyway |
| **D5.** Document cross-chain consistency in the main customer guide | **Yes — pure-doc edit, ships today.** | Now |

D1 is the highest-value-per-hour item. D3 is the riskiest; defer
unless real demand. D5 ships today as part of the same commit
that creates this document.

---

## Cross-references

**Source documents:**

- `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md`
  § "What network for what action"
- `pwm-team/customer_guide/PWM_DEPLOYMENT_FLOW_DESIGN_2026-05-08.md`
  § 4 (L1/L2/L3 testnet → mainnet flow already works) +
  § 5 (why L4 doesn't have a mandatory testnet → mainnet step)
- `pwm-team/customer_guide/PWM_BUG_FIX_PLAYBOOK_2026-05-08.md`
  § 5 (per-benchmark `challengePeriodSeconds` override applies
  independently per chain)

**Code references:**

- `pwm-team/infrastructure/agent-cli/pwm_node/__main__.py`
  — `--network` arg parsing
- `pwm-team/infrastructure/agent-cli/pwm_node/chain.py`
  — RPC + addresses dispatch
- `pwm-team/infrastructure/agent-contracts/addresses.json`
  — chain-specific contract addresses
- `pwm-team/infrastructure/agent-web/api/main.py`
  — `/api/network` endpoint that returns the active chain
- `pwm-team/infrastructure/agent-web/frontend/app/components/`
  — where the proposed `ChainBadge.tsx` would land

**Live state today:**

- Sepolia testnet: `addresses.json:testnet` populated (PWMRegistry
  `0x2375…`, PWMCertificate `0x8963…`)
- Base mainnet: `addresses.json:mainnet` block exists with
  `chainId: 8453` but contract addresses are `null` until D9 deploy
- Explorer: `https://explorer.pwm.platformai.org` serves Sepolia
  today; mainnet deployment shares the same frontend with a
  `?network=mainnet` query string at D9
