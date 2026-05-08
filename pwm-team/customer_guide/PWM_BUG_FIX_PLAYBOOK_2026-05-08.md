# Bug-Fix Playbook — How to Fix Mistakes After Deployment

**Date:** 2026-05-08
**Audience:** L1/L2/L3 Principle authors, L4 miners, founders running the multisig — anyone who deployed an artifact and now wants to fix something
**Trigger question (Director, 2026-05-08):**
> "After I deploy some principles, spec, benchmark and solutions, is it
> possible to modify them to make them better? I am afraid that there
> will be some bugs in them at first."

---

## TL;DR

The **on-chain hash never changes** — that's a hard constraint by
design (the whole "verify any cert forever" guarantee depends on it).
But there are real escape hatches for bug fixes; they just don't
mutate the original artifact's hash. Five categories of fix, summary
table:

| Bug type | Fixable? | How |
|---|---|---|
| Typo in `display_slug`, wrong `registration_tier`, missing deep-learning floor | ✅ Yes, hash-invariant | Edit the field directly. `UI_ONLY_FIELDS` are stripped before keccak256 — see § 1. |
| Wrong solver label / PSNR / framework on a cert you submitted | ✅ Yes, off-chain only | `POST /api/cert-meta/{cert_hash}` — see § 2. |
| Bug in the **forward model**, **DAG primitives**, **ε_fn**, **dataset CIDs**, or any `baselines[*]` entry | ❌ No, the hash *will* change | Cut a new version `L1-026b-v2` — see § 3. |
| Fraudulent or wrong L4 cert someone submitted | ✅ Yes, during the 7-day window | `PWMCertificate.challenge(cert_hash, proof)` — see § 4. |
| Pool size, reward %, mint emission, finalization window | ✅ Yes, multisig-gated | `PWMGovernance.setParameter` with 48 h time-lock — see § 5. |

---

## 1. Hash-invariant edits (always safe, no re-registration)

The canonical hash filter (`scripts/register_genesis.py`,
`pwm-node mine`, the contracts) all strip a known set of UI-only
fields before computing keccak256:

```python
UI_ONLY_FIELDS = frozenset({
    "display_slug",        # human-readable URL slug, e.g. "cassi"
    "display_color",       # accent colour for UI cards
    "ui_metadata",          # arbitrary UI sidecar (badges, tooltips, etc.)
    "registration_tier",   # "stub" | "community_proposed" | "founder_vetted"
    "display_baselines",   # leaderboard sidecar (e.g. deep-learning floor)
})
```

Any field in this set can be **added, edited, or removed** at any time
on a registered manifest without invalidating any past cert. The
manifest's keccak256 stays valid because these fields never made it
into the canonical bytes.

**What this lets you do post-deployment:**

- Rename the slug (`/benchmarks/casssi` → `/benchmarks/cassi`)
- Change the colour the explorer renders the card in
- Add tooltip / badge metadata for the explorer
- Promote a Tier-3 stub to `community_proposed` once a verifier-agent
  triple-review passes — without re-registering on-chain
- Add a deep-learning floor (`display_baselines: [{name: "MST-L", …}]`)
  AFTER an authored deep-learning baseline lands, without touching the
  classical `baselines[]` that contributed to the original hash

**What this does NOT cover:** anything in the canonical body — `E`,
`G`, `W`, `C`, `spec_range`, `omega_bounds`, `epsilon_fn`,
`dataset_registry`, `baselines[]`, `ibenchmarks[]`. Those changes
require § 3 (versioning).

**Verification:** the customer guide doc
`PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md` § "Hash
invariance" walks the L1-003 hash before and after `registration_tier`
was added — same `0xe3b1328c…99a51ea` byte-for-byte.

---

## 2. L4 cert-meta enrichment (off-chain, always editable)

When you submit an L4 cert, the on-chain `CertificateSubmitted` event
carries 12 immutable fields:

```
certHash, benchmarkHash, principleId, delta, spWallet, acWallet,
cpWallet, l1Creator, l2Creator, l3Creator, shareRatioP, submittedAt,
Q_int, status, rank
```

These are frozen forever. But the **off-chain `cert_meta` sidecar** —
the human labels you see on the leaderboard — lives in the explorer's
SQLite indexer, not on-chain. Anyone with the cert hash can re-post
it via the explorer API:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
        "solver_label":  "MST-L (revised: was tagged GAP-TV)",
        "psnr_db":       35.295,
        "runtime_sec":   12.3,
        "framework":     "PyTorch 2.1 + CUDA 12.1",
        "meta_url":      "ipfs://Qm…/full_meta.json"
      }' \
  https://explorer.pwm.platformai.org/api/cert-meta/0x7c7740…e13
```

Authentication model: the cert hash itself is proof of submission.
Anyone with it can post; lying about `solver_label` or `psnr_db`
**doesn't change the on-chain Q_int / rank / reward** (those are
determined by `PWMCertificate.submit()` and `PWMReward.distribute()`).
The cert-meta is presentation; the cert itself is law.

**What this lets you do post-deployment:**

- Fix a wrong solver label after submission (the live MST-L cert
  `0x7c7740…e13` was originally posted unlabeled; we fixed it with
  exactly this endpoint on 2026-05-05)
- Update `framework` when you re-train the model
- Add a `meta_url` pointing at a new IPFS pin with the full reproducibility
  bundle (weights, config, training data hash, etc.)
- Roll back a bad meta posting by re-posting with corrected values

**Limit:** rate-limited at the reverse-proxy layer (~10 req/min/IP).

---

## 3. Versioning — the canonical fix for body bugs

When the bug is in the **canonical body** (forward model wrong,
ε_fn formula wrong, dataset CID dead, baselines mis-measured),
the hash WILL change. The protocol's answer is to author a new
version, not mutate the old one:

```
L1-026b   (Walsh-Hadamard SPC; bug found in epsilon_fn at T1)
   │
   │ stays valid forever — past certs against L1-026b
   │ remain verifiable
   ↓
L1-026b-v2  (new artifact_id, new keccak256, new on-chain registration,
             corrected epsilon_fn)
```

The naming convention is `<original-id>-v<N>`:
- `L1-026b` (deployed 2026-05-08 — Tier 1)
- `L1-026b-v2` (re-registered 2026-08-01 — corrected ε_fn)
- `L1-026b-v3` (registered 2027-02-15 — added third I-benchmark tier)

Both versions stay on-chain. The old version's pool continues to
accept submissions; new mining naturally migrates to v2 as the
explorer surfaces it as the recommended target. Reserve grants pay
both as long as both have meaningful activity (multisig discretion).

**What changes the hash and triggers a v-bump:**

| Field | Hash impact |
|---|---|
| `E`, `G`, `W`, `C` blocks | YES |
| `spec_range.center_spec` values | YES |
| `spec_range.allowed_*` lists | YES |
| `omega_bounds`, `epsilon_bounds` | YES |
| `epsilon_fn` formula | YES |
| `dataset_registry` (any field except `cid` placeholders) | YES |
| `baselines[]` (canonical I-bench / P-bench reference scores) | YES |
| `physics_fingerprint` block | YES |
| `p1_p10_tests`, `s1_s4_gates` arrays | YES |
| Any of the `UI_ONLY_FIELDS` (§ 1) | NO — edit in place |

**Procedure for cutting a v2:**

```bash
# 1. Copy and edit the source manifest
cp pwm-team/pwm_product/genesis/l1/L1-026b.json \
   pwm-team/pwm_product/genesis/l1/L1-026b-v2.json
$EDITOR pwm-team/pwm_product/genesis/l1/L1-026b-v2.json
#    set "artifact_id": "L1-026b-v2"
#    fix the bug (e.g. epsilon_fn coefficient)
#    increment "version": 2 in v3_metadata if you want explicit numbering

# 2. Verifier-agent triple-review on PR
git checkout -b fix/l1-026b-v2-epsilon-correction
git add . && git commit -m "fix(spc): epsilon_fn baseline correction (L1-026b → L1-026b-v2)"
gh pr create --title "L1-026b → L1-026b-v2 (epsilon_fn fix)" \
             --body "Old L1-026b stays valid; new certs should target v2…"

# 3. Multisig signs PWMRegistry.register() for the new hash
python3 scripts/register_genesis.py --network mainnet --manifest L1-026b-v2.json
#    (after PR merges and 3-of-5 multisig approves)

# 4. Update explorer "current version" pointer in the artifact's display_slug
#    (this IS hash-invariant — see § 1)
```

**What you cannot do as v-bump:**

- Delete the old version (it's on-chain forever)
- Force past miners to migrate (they keep their certs and rewards)
- Change the original hash (that's the whole point)
- Skip the verifier-agent triple-review (S1-S4 gates re-run on v2)
- Skip the multisig (`PWMRegistry.register` is multisig-gated)

---

## 4. Challenge a fraudulent / wrong L4 cert (during the 7-day window)

Every L4 cert has a 7-day challenge period after `submit()`. During
that window, anyone can call:

```solidity
PWMCertificate.challenge(bytes32 certHash, bytes calldata proof)
```

`proof` is a structured payload (defined in
`pwm-team/coordination/agent-coord/interfaces/cert_schema.json`)
showing why the cert's claimed Q is wrong:

- A different solver run on the same `(benchmark_hash, ω_instance)`
  tuple producing a higher PSNR than the cert claimed → solver was
  cherry-picking inputs
- A run on the documented dev/holdout split producing an inconsistent
  result → solver memorised the dev set, fails on holdout
- The cert's ω parameters falling outside the manifest's
  `omega_bounds` → submission targeted an out-of-spec point

If the multisig accepts the challenge:

- The cert is **invalidated** (`status = "challenged"`); no rank, no
  reward
- The challenger receives the cert's staked PWM (3× the per-cert
  staking floor)
- The submitter loses their stake

After 7 days clean (no challenge upheld), the cert is **finalized** —
`PWMCertificate.finalize(certHash)` mints rewards. After finalization,
the cert is immutable.

**What this protects against:**

- Solver gaming the dev split (publish high Q on cherry-picked instances)
- Submitter posting a `Q_int` that doesn't reproduce
- Out-of-spec submissions slipping past S1 dimensional checks

**What this does NOT cover:**

- A genuine algorithmic improvement that beats the published baseline
  by a small margin (that's just better solving — no fraud)
- A meta-data error (wrong solver label) — fix via § 2 cert-meta
- A finalized cert (>7 days old) — fully immutable; no recourse

---

## 5. Governance-controlled parameters (multisig-gated)

A small set of system parameters are **not in any artifact manifest**
— they live in `PWMGovernance` as on-chain constants. They CAN be
changed, but only via:

1. A founder proposes a new value via `PWMGovernance.proposeParameter(key, value)`
2. The proposal enters a 48-hour time-lock window
3. 3-of-5 founders sign approval before the time-lock expires
4. After the time-lock, anyone can call `executeParameter(key)` to apply

| Parameter key | What it controls | Default | Can post-D9 change? |
|---|---|---|---|
| `usdFloors.principle` | $50 minimum stake on L1 | 50 | yes (vote) |
| `usdFloors.spec` | $5 minimum stake on L2 | 5 | yes |
| `usdFloors.benchmark` | $1 minimum stake on L3 | 1 | yes |
| `challengePeriodSeconds` | Cert challenge window | 604800 (7 d) | yes |
| `challengePeriodExtended` | Extended-window for high-delta certs | 1209600 (14 d) | yes |
| `slashingRates.fraud` | % of stake burned on fraud | 100 | yes |
| `slashingRates.upheld` | % of stake to challenger on upheld | 50 | yes |
| `deltaTiers.*` | δ thresholds for tier classification | per `pwm_overview1.md` § 3 | yes (rare) |
| `maxBenchmarkPoolWei` | Pool cap per L3 (anti-runaway) | varies | yes |

**Things that CANNOT change even via multisig:**

- The `M_pool` minting cap (17.22M PWM = 82% of 21M total)
- The 7-rank-payout shape (40/5/2/1/1/1/1/1/1/1) — hardcoded in
  `PWMReward.sol` constants
- The `principle:5%, spec:10%, L3:15%, treasury:15%` royalty split
- The `keccak256(canonical_json)` hashing recipe

These are constitutional. Changing them would require a contract
re-deploy under a new audit tag — i.e. a hard fork.

---

## Practical strategy: how to avoid most bugs in the first place

The four habits that fix bugs cheaply BEFORE they reach production:

### Habit 1 — Use the registration tiers as a staging gate

Every new manifest starts as `registration_tier: "stub"` — present in
the catalog but **not on-chain at all**, no pool, no reward, fully
editable. This is the cheapest place to fix bugs (just edit the
JSON). Promote to `community_proposed` only after verifier-agent
triple-review; promote to `founder_vetted` only after live mining
proves it out.

SPC (`L1-026b`) sits at `stub` today specifically so the team has
unlimited ability to fix the bugs we've already found in this session
(the wrong source_file path, the missing source_data_quality_note,
the `int.temporal → int.spatial` primitive bug). All three of those
were free fixes because SPC isn't on-chain yet.

### Habit 2 — Mine on Sepolia first

Sepolia testnet costs ~$0 in real money. CASSI / CACTI / SPC have
been (or will be) tested on Sepolia for weeks before Base mainnet
flips. Bugs found on Sepolia are free fixes via § 3 (cut a v2
manifest); the same bug found on mainnet costs real PWM that miners
have already locked into the bad version's pool.

The 5-founder testnet on Sepolia (`addresses.json:testnet`) is set
up specifically for this — every manifest bound for mainnet should
get at least one full mining cycle on Sepolia first.

### Habit 3 — Adopt a versioning convention up front

Even if you never use it, naming everything as `L<n>-<id>-v<N>`
makes the path to `v2` obvious when the time comes. Documents in
`pwm_product/genesis/` follow this convention; new contributions
under Bounty #7 should adopt it from the start.

When you DO need a v2, document the reason in
`pwm-team/coordination/agent-coord/interfaces/CHANGELOG_<artifact_id>.md`
so future readers can trace the lineage.

### Habit 4 — Treat the `_meta` cert sidecar as your scratchpad

Anything off-chain — `solver_label`, `psnr_db`, `framework`,
`runtime_sec`, IPFS pin URLs — can be corrected via § 2 cert-meta.
Reserve the on-chain payload for what genuinely cannot move (the
12 chain-bound fields). When in doubt, put it in `_meta`.

This is exactly how we handled the original MST-L cert
(`0x7c7740…e13`): the on-chain `Q_int=35` is permanent, but the
solver label was wrong at submission time and we fixed it via
`POST /api/cert-meta` two days later. No on-chain churn.

---

## The "what you can never do" line

To be explicit about the immutability invariants the protocol depends
on:

| Action | Possible? |
|---|---|
| Modify an on-chain L1/L2/L3 manifest's keccak256 | ❌ NEVER |
| Delete a registered artifact | ❌ NEVER |
| Force past miners to migrate to a v2 | ❌ NEVER |
| Re-rank a finalized L4 cert | ❌ NEVER |
| Change the cert hash recipe | ❌ NEVER (constitutional) |
| Change the rank payout shape (40/5/2/1×7) | ❌ NEVER (constitutional) |

These guarantees are exactly why PWM is useful — every cert ever
submitted remains verifiable forever against an immutable benchmark.
Take them as non-negotiable; design your bug-fix flow around them.

---

## Cross-references

**Source documents (formal definitions of the invariants above):**

- `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md`
  — main user guide, § "Registration tiers" + § "Hash invariance" +
  § "What you cannot do"
- `pwm-team/customer_guide/PWM_ONCHAIN_VS_OFFCHAIN_ARCHITECTURE_2026-05-05.md`
  — what's on-chain vs off-chain (the basis of all the fixability
  questions)
- `pwm-team/customer_guide/PWM_Q_SCORE_EXPLAINED_2026-05-06.md`
  — Q_int is uint8 + immutable on-chain; everything else is editable
- `papers/Proof-of-Solution/pwm_overview1.md` § 2 ("Immutability and
  the On-Chain Registry") — the constitutional principle
- `papers/Proof-of-Solution/mine_example/pwm_overview.md` Figure 0a
  ("Immutability — Principle and spec.md Are Fixed Once Established")
  — the canonical immutability picture

**Code references (where the invariants are enforced):**

- `scripts/register_genesis.py` — `UI_ONLY_FIELDS` set definition;
  the canonical hash filter
- `pwm-team/infrastructure/agent-contracts/contracts/PWMRegistry.sol`
  — `register(bytes32 hash, …)`: hash is `bytes32`, no setter
- `pwm-team/infrastructure/agent-contracts/contracts/PWMCertificate.sol`
  — `submit()` + `challenge()` + `finalize()` lifecycle
- `pwm-team/infrastructure/agent-contracts/contracts/PWMGovernance.sol`
  — multisig + 48 h time-lock for parameter changes
- `pwm-team/infrastructure/agent-web/api/main.py:upsert_cert_meta`
  — the cert-meta POST endpoint

**Concrete bug-fix examples from this team:**

- L1-026b SPC: `int.temporal → int.spatial` primitive correction
  (Tier-3 stub, free fix — § 1 + § 3 path) — commit `f0e3ff1`
- L1-026b SPC: corrected `source_file` path + restored `source_data_quality_note`
  (Tier-3 stub, free fix — § 1 path) — commits `8b61a31` and `d45d812`
- MST-L cert `0x7c7740…e13`: solver label correction via cert-meta
  (live cert, off-chain fix — § 2 path) — `POST /api/cert-meta` 2026-05-05
- L3-003 CASSI: added MST-L deep-learning floor via `display_baselines`
  sidecar (live registered artifact, hash-invariant fix — § 1 path)
  — commit `f886b17`
