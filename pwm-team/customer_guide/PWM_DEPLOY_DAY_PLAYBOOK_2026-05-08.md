# Deploy-Day Playbook — Safe Testnet → Base Mainnet Promotion

**Date:** 2026-05-08
**Audience:** Director (D9 mainnet executor) + CPU agent supporting alongside
**Trigger question (Director, 2026-05-08):**
> "If I want to deploy the current PWM from testnet into mainnet,
> what should I do to prevent some errors and bugs?"

**Companion docs:** `MAINNET_BLOCKERS_2026-04-30.md` (action list),
`DIRECTOR_RUNBOOK_D1_TO_D10_2026-05-01.md` (D1-D10 walkthrough),
`PWM_MAINNET_GO_NOGO_2026-05-08.md` (snapshot of current readiness).

---

## TL;DR

**Layered defense in seven layers.** Each layer catches a different
class of bug; skipping any layer is the kind of "I'll just shortcut
this" that loses real money. The protocol's design (immutable
hashes, multisig + 48 h time-lock, 7-day challenge window,
registration_tier ladder, fork preflights) was built precisely so
this playbook can be run mechanically — no judgment calls in the
hot path.

```
Layer 1 — Don't skip the runbook prerequisites          (D1-D9 in DIRECTOR_RUNBOOK)
Layer 2 — Re-run fork preflights on D9 morning          (preflight_step5/8_fork.sh)
Layer 3 — Verify manifest hash integrity end-to-end     (canonical keccak256 matches)
Layer 4 — Stage rollout via registration_tier + caps    (6 manifests at founder_vetted day 1)
Layer 5 — Use the per-benchmark challenge window        (7d default; 3d only after track record)
Layer 6 — daily_stability_check.sh × 7 days post-deploy  (stability clock)
Layer 7 — Pre-fund the bug response budget              (~$500 ETH + ~10K PWM on hand)
```

---

## Layer 1 — Don't skip the runbook prerequisites (D1–D9)

Every step in `DIRECTOR_RUNBOOK_D1_TO_D10_2026-05-01.md` exists
because something can go wrong if you skip it. The most common
"I'll cut corners" mistakes and what they cost:

| Mistake | Cost |
|---|---|
| Single-sig deploy (skip D3 5-HW-wallets) | If your single key is compromised, attacker gets governance — you lose the protocol. Comparable protocols (Wormhole, Ronin) have lost $300M+ to single-sig compromise. |
| Skip Sepolia governance rehearsal (D4) | First-ever multisig propose-approve-execute happens on real money with 48 h timelock locking the wrong parameter values forever. |
| Skip ≥ 20 non-founder L4 submissions (D5) | Real-money launch with zero proof the protocol works for non-insiders. Audit teams flag this. |
| Skip Reserve resizing decision (D2) | `deploy/l2.js` deploys with default allocation that doesn't match the 531-manifest catalog. Pool sizes wrong on day one; can fix via governance but burns weeks. |
| Skip funding (D1) | The 7-contract deploy chain reverts on the first transaction. You re-do everything; if you didn't pre-stage the deployer key carefully, you've already published the address publicly. |
| Skip external audit (D10, post-mainnet) | If a bug is found post-mainnet without an independent audit on file, you're alone in the response. Audit firms also won't touch a post-deploy mess. |

**The runbook IS the playbook for Layer 1.** Read it before D9 morning.

---

## Layer 2 — Re-run the fork preflight scripts the day of deploy

The fork preflights simulate the deploy chain against a forked Base
mainnet without spending real ETH. Last-known-GREEN dates:
- `preflight_step5_fork.sh` — Sepolia governance rehearsal — GREEN 2026-04-29
- `preflight_step8_fork.sh` — Base mainnet contract deploy — GREEN 2026-04-28

**Both must be re-run the morning of D9.** Drift can come from:
- Base mainnet gas price changes
- Hardhat / foundry version bumps
- A merged PR you didn't notice
- A `npm install` adding a vulnerable transitive dep

The preflights catch contract revert reasons, gas estimate misses,
and constructor argument bugs **before** you sign a real transaction.

```bash
# D9 morning, ~6 AM Director-time:
cd /home/spiritai/pwm/Physics_World_Model/pwm

# 1. Refresh dependencies just in case
git fetch && git checkout mainnet-v1.0.0
cd pwm-team/infrastructure/agent-contracts && npm ci

# 2. Run both preflights — both must exit 0
cd ../../..
bash scripts/preflight_step5_fork.sh    # Sepolia, expect GREEN
bash scripts/preflight_step8_fork.sh    # Base mainnet fork, expect GREEN

# If either fails: STOP. File a bug. Investigate. Do NOT proceed.
```

Expected output: each script ends with `=== ALL CHECKS PASSED ===`.
Anything else is a NO-GO signal.

---

## Layer 3 — Verify manifest hash integrity end-to-end

The 531 manifests in `pwm-team/pwm_product/genesis/` and
`pwm-team/content/agent-*/principles/` have computed
`keccak256(canonical_json)` values that the deploy registers
on-chain. If a manifest has drifted since the audit tag, the on-chain
hash will not match what readers (and `pwm-node mine`) expect.

**Two checks:**

```bash
# Check 1 — recompute every founder-vetted manifest's hash
python3 - <<'PY'
import json, glob
from eth_utils import keccak
UI = {'display_slug','display_color','ui_metadata',
      'registration_tier','display_baselines'}
def h(p):
    o = json.load(open(p))
    f = {k:v for k,v in o.items() if k not in UI}
    return '0x' + keccak(json.dumps(f, sort_keys=True,
                                     separators=(',',':')).encode()).hex()
for layer in ('l1', 'l2', 'l3'):
    for path in sorted(glob.glob(f'pwm-team/pwm_product/genesis/{layer}/*.json')):
        print(f'{path:60} {h(path)}')
PY

# Check 2 — diff against the audit-tag baseline
git diff mainnet-v1.0.0..HEAD -- 'pwm-team/pwm_product/genesis/**/*.json'
# Empty diff = body bytes unchanged since audit
# Non-empty diff: review every change. UI_ONLY_FIELDS edits OK
#   (hash invariant); body edits require a v-bump per
#   PWM_BUG_FIX_PLAYBOOK_2026-05-08.md § 3.
```

**Expected on D9 morning** (current state — verified 2026-05-08):

```
L1-003: 0xe3b1328c66835cd729fa50650ef1d1bac4aa407807d6d97d4979e988a99a51ea
L1-004: 0xa2ae37946ef2822a308a4e60245dd2655070190cf8f3913559ae36286b26a56b
L2-003: 0x471e7017692cde623cee2741e751413cfb4752457429f128c0004174fea86896
L2-004: 0x3d15686eff5758f77fac1ae4843e25499a87d0f5fcd2661023eb1b69228aa8f9
L3-003: 0xdc8ad0dc68682eff750188c8d4d84179b3f7deddee1af562bc3b085794048b4a
L3-004: 0x052324ba0585e4cf320914e117bf9b08656d602b9ac753b289a6a75ba926eab4
```

**If a hash differs from the published value:** STOP. Either the
manifest body has drifted (review the diff carefully — was this
intentional? UI_ONLY_FIELDS-only? a real bug fix that should ship as
v2 instead?) or you're on the wrong commit. Either way, do not deploy.

The L1-026b SPC fix this session (`int.temporal → int.spatial`) is
exactly the kind of bug this catches — found because we recomputed
the hash and noticed it didn't match the canonical
`primitives.md:567` signature.

---

## Layer 4 — Stage rollout via `registration_tier` + conservative pools

**Don't register all 531 manifests at `founder_vetted` on day 1.** The
`registration_tier` ladder exists to limit the blast radius of
day-one bugs.

**Day-one registration (D9 Step 9b — `register_genesis.py --network mainnet`):**

| Tier | What gets registered on Base mainnet day one | Count |
|---|---|---|
| `founder_vetted` | The 6 manifests with shipped reference solvers + datasets — CASSI L1+L2+L3-003 + CACTI L1+L2+L3-004 | 6 |
| `community_proposed` | None on day one | 0 |
| `stub` | The other 525 manifests — catalog-visible, not on-chain, no pool, fully editable | 525 |

The 525 stubs stay catalog-only until external Bounty #7 contributors
promote them. Each promotion is its own multisig event;
verifier-agent triple-review re-runs S1-S4. Bugs caught at promotion
time cost only the contributor's PR — not real PWM in a pool.

**Pool caps (D9 Step 10 — multisig + 48 h timelock):**

```python
# Conservative day-one pool caps — ~50-100 PWM per L3 until track record
maxBenchmarkPoolWei = {
    'L3-003': 100 * 10**18,    # 100 PWM cap on CASSI (most active)
    'L3-004':  50 * 10**18,    # 50 PWM cap on CACTI
}
```

These caps prevent runaway emission if a bug is discovered
post-mainnet. Real PWM doesn't lock into a benchmark until 90+ days
of clean mining proves it out.

**After 90 days** (April–July 2026 if D9 happens 2026-05-22): re-evaluate
caps via governance proposal. Successful benchmarks earn a higher cap
proportional to cert volume; unproven benchmarks stay at the floor.

---

## Layer 5 — Use the per-benchmark challenge window as your safety margin

Per `PWM_DEPLOYMENT_FLOW_DESIGN_2026-05-08.md` § 3, keep the 7-day
challenge window at the constitutional default for new mainnet
benchmarks. **Don't shorten it on day one.**

```solidity
// In PWMCertificate.sol
uint64 public constant CHALLENGE_PERIOD_DEFAULT  = 7 days;     // KEEP
uint64 public constant CHALLENGE_PERIOD_EXTENDED = 14 days;    // KEEP for δ ≥ 10
```

Per-benchmark override (`PWMGovernance.setParameter`) only after
**25+ finalized certs** + **12+ months** + **0 upheld challenges**.
For CASSI/CACTI on Sepolia today (~150 certs each), this could
hypothetically apply at +12 months on Base mainnet. Don't shortcut
the timer.

The 14-day window has caught fraud at every comparable protocol;
7 days has too. 3 days has not.

---

## Layer 6 — `daily_stability_check.sh` × 7 days post-deploy

After D9 closes (`mainnet-v1.0.0` deployed, genesis registered, founder
mining transactions live, Immunefi launched), the stability clock
starts. Per the runbook:

```bash
# D9+1 through D9+7, every morning ~9 AM:
cd /home/spiritai/pwm/Physics_World_Model/pwm
bash scripts/daily_stability_check.sh --network mainnet

# Expected outputs (each must be GREEN for 7 consecutive days):
#   ✓ indexer freshness: last block within 5 minutes of head
#   ✓ RPC connectivity: <500 ms latency to Base mainnet
#   ✓ /api/health = "healthy" (not "degraded")
#   ✓ Pool balances consistent: sum(pool_events.delta) == registry.totalMinted
#   ✓ No pending-cert finalize before challenge window
#   ✓ Founder wallet balances >= operational floor
```

**If any single day goes RED:**
1. Pause new submissions via `PWMGovernance.proposeParameter("paused", true)`
2. Investigate the root cause (RPC outage / contract bug / indexer crash)
3. Resolve, re-run check until GREEN
4. Resume; reset 7-day clock

**After 7 consecutive GREEN days** the 30-day stability clock runs
through; at +37 days post-D9 the protocol is officially stable and
can begin accepting new `founder_vetted` registrations beyond the
day-one set of 6.

---

## Layer 7 — Pre-fund the bug response budget

Set aside **before D9**:

| Reserve | Amount | Purpose |
|---|---|---|
| Founder treasury — ETH | ~$500 (≈ 0.15 ETH on Base) | Emergency tx gas: pause, parameter change, multisig coordination, contract calls during incident response |
| Founder treasury — PWM | ~10,000 PWM | Bounty payments to challengers if they catch fraud; emergency liquidity on the leaderboard if a bug requires manual cert invalidation + re-mine |
| External audit retainer | TBD per auditor (separate budget) | If a critical bug is reported, the audit firm needs to be on-call within hours, not days |
| Communication channel | Discord / Telegram / X status account ready | Users learn about an issue from you, not from a Twitter thread written by an attacker |
| Multisig response time | 5 founders reachable within 4 hours, 24/7 for first 30 days | A 3-of-5 governance vote takes 48 h timelock; the 4-hour-to-propose deadline is what matters during an incident |

**Bug response routing (per `PWM_BUG_FIX_PLAYBOOK_2026-05-08.md`):**

| Bug type | First response | Mechanism |
|---|---|---|
| Wrong solver label / framework / PSNR on a cert | None — fixable any time | `POST /api/cert-meta/{hash}` |
| Manifest typo (display_slug, registration_tier, etc.) | Edit and PR | UI_ONLY_FIELDS hash-invariant |
| Manifest body bug (forward model, ε_fn, dataset CIDs) | Cut a v2 | New artifact_id + multisig register |
| Fraudulent L4 cert | Challenge within 7 days | `PWMCertificate.challenge(certHash, proof)` |
| Pool size / reward % wrong | Multisig propose | `PWMGovernance.setParameter` + 48 h timelock |
| Contract bug (front-running, reentrancy, etc.) | Pause + audit | `PWMGovernance.proposeParameter("paused", true)` then external audit firm engagement |
| Indexer / explorer bug | Fix + redeploy | Doesn't touch on-chain; ssh + docker rebuild + restart |

---

## D9 morning — copy-pasteable runbook

Once D1–D5 are all GREEN per `PWM_MAINNET_GO_NOGO_2026-05-08.md`:

```bash
# === D9 morning, ~5 AM Director-time ===

cd /home/spiritai/pwm/Physics_World_Model/pwm
git fetch
git checkout mainnet-v1.0.0       # the audit-clean tag

# Layer 2: re-run fork preflights
bash scripts/preflight_step5_fork.sh
bash scripts/preflight_step8_fork.sh

# Layer 3: verify manifest hashes
python3 -c "
import json
from eth_utils import keccak
UI = {'display_slug','display_color','ui_metadata','registration_tier','display_baselines'}
expected = {
    'L1-003': '0xe3b1328c66835cd729fa50650ef1d1bac4aa407807d6d97d4979e988a99a51ea',
    'L1-004': '0xa2ae37946ef2822a308a4e60245dd2655070190cf8f3913559ae36286b26a56b',
    'L2-003': '0x471e7017692cde623cee2741e751413cfb4752457429f128c0004174fea86896',
    'L2-004': '0x3d15686eff5758f77fac1ae4843e25499a87d0f5fcd2661023eb1b69228aa8f9',
    'L3-003': '0xdc8ad0dc68682eff750188c8d4d84179b3f7deddee1af562bc3b085794048b4a',
    'L3-004': '0x052324ba0585e4cf320914e117bf9b08656d602b9ac753b289a6a75ba926eab4',
}
for aid, want in expected.items():
    layer = aid.split('-')[0].lower()
    o = json.load(open(f'pwm-team/pwm_product/genesis/{layer}/{aid}.json'))
    f = {k:v for k,v in o.items() if k not in UI}
    got = '0x' + keccak(json.dumps(f, sort_keys=True, separators=(',',':')).encode()).hex()
    print(f'{aid}: {\"OK\" if got == want else \"MISMATCH\"}')
    if got != want:
        print(f'   want: {want}')
        print(f'   got : {got}')
"

# Step 7 — fund deployer wallet (D1 — should be done; verify balance)
cast balance $DEPLOYER_ADDRESS --rpc-url $BASE_RPC_URL
# Expect: > 0.012 ETH

# Step 8 — deploy 7 contracts
cd pwm-team/infrastructure/agent-contracts
npx hardhat run deploy/l2.js --network base
# Update addresses.json:mainnet block; commit + push

# Step 9 — wire governance (setGovernance × 5 contracts)
npx hardhat run scripts/wire_governance.js --network base

# Step 9b — register 6 founder_vetted manifests
cd ../../..
python3 scripts/register_genesis.py --network mainnet
# (the 525 stubs stay off-chain by design — registration_tier="stub")

# Step 10 — propose cap configuration (multisig + 48 h timelock)
npx hardhat run scripts/propose_caps.js --network base
# WAIT 48 HOURS

# (T+48h) Step 10 finish — execute cap configuration
npx hardhat run scripts/execute_caps.js --network base

# Step 11 — 7 founder mining transactions (distribute across CASSI + CACTI)
bash scripts/founder_mining_live.sh --network mainnet

# Step 12 — Immunefi listing live + announcement
# (Director executes manually via Immunefi web UI; flip pwm-public to public)
```

**During each step, watch for:**
- Transaction reverts → STOP, investigate
- Gas spikes (>2× preflight estimate) → wait for chain congestion to ease
- Indexer falling behind → expected during deploy; will catch up post-D9
- Multisig signing requests on the wrong wallet → triple-check before signing

---

## Worst-case rollback options

If something goes catastrophically wrong **during D9**:

| Severity | Response | Recovery time |
|---|---|---|
| Single transaction reverted (e.g. constructor arg wrong) | Re-broadcast with corrected args; no on-chain state lost | Minutes |
| Wrong genesis manifest registered (hash drift) | New manifest = new artifact_id; old wrong one stays on-chain forever but inert (no pool, no certs) | Hours |
| Multisig wired to wrong addresses | Propose-approve-execute correction (48 h timelock) | 2 days |
| Multiple contracts deployed to wrong addresses | Re-deploy, abandon the wrong addresses, pay the gas a second time | 1 day + cost duplicated |
| Critical bug in deployed contract | `PWMGovernance.proposeParameter("paused", true)`; engage auditor; cut v2 contracts; migrate via governance | 2-6 weeks |
| Lost multisig hardware wallet | Use the cold-storage backup (D3 paper wallet); rotate all 5 signers via governance | 1-2 weeks |
| Compromised multisig threshold | Pause + governance vote to rotate signers; if attacker can sign 3-of-5, transfer governance to a new multisig (requires audit + community vote) | 4-12 weeks |

**Most of these are recoverable.** The handful that aren't (compromised
3-of-5 multisig with attacker control, contract bug discovered after
significant TVL has accumulated) are the reason the protocol uses
hardware wallets, 48 h timelocks, conservative pool caps, audit tags,
and the 7-day challenge window. The defensive layers compound — an
attacker has to bypass *every* layer to do irreversible damage; a
defender only has to win on *any* layer.

---

## Cross-references

**Companion docs (this same session):**

- `pwm-team/coordination/PWM_MAINNET_GO_NOGO_2026-05-08.md` — today's
  red/yellow/green snapshot of the 12-row deploy-day checklist
- `pwm-team/customer_guide/PWM_BUG_FIX_PLAYBOOK_2026-05-08.md` — what
  to do when a bug surfaces post-deploy (5 categories + 4 strategies)
- `pwm-team/customer_guide/PWM_DEPLOYMENT_FLOW_DESIGN_2026-05-08.md`
  — why 7 days, per-benchmark `challengePeriodSeconds`, why L4
  doesn't have a mandatory testnet → mainnet
- `pwm-team/customer_guide/PWM_CROSS_CHAIN_UX_DESIGN_2026-05-08.md`
  — what's the same / different across Sepolia + Base mainnet

**Action chain (the runbook structure this layered into):**

- `pwm-team/coordination/MAINNET_BLOCKERS_2026-04-30.md` — CPU vs
  Director task split, full action list
- `pwm-team/coordination/DIRECTOR_RUNBOOK_D1_TO_D10_2026-05-01.md`
  — Director-side step-by-step
- `pwm-team/coordination/handoffs/_drafts/STEP_5__governance-rehearsal-sepolia.READY.draft.json`
- `pwm-team/coordination/handoffs/_drafts/STEP_11__founder-mining-live.READY.draft.json`

**Code references:**

- `scripts/preflight_step5_fork.sh` + `scripts/preflight_step8_fork.sh`
  — Layer 2 fork preflights
- `scripts/register_genesis.py` — Layer 3 hash recomputation +
  Layer 4 day-one staged registration
- `scripts/daily_stability_check.sh` — Layer 6 7-day post-deploy
  monitoring
- `pwm-team/infrastructure/agent-contracts/contracts/PWMGovernance.sol`
  — Layer 7 emergency-pause primitive
