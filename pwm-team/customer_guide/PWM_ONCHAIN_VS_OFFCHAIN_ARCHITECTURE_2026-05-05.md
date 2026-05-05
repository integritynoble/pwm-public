# PWM Architecture — What's On-Chain vs Off-Chain (and Where Off-Chain Data Lives)

**Date:** 2026-05-05
**Audience:** Researchers, students, regulators, auditors, anyone trying to
understand what gets stored where in the PWM protocol.
**Companion to:** `PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md`
(the canonical create-and-use guide)

---

## Quick answer (TL;DR)

| Layer | What's on-chain | What's off-chain |
|---|---|---|
| L1 / L2 / L3 | `keccak256(canonical_json)` hash + parent hash + creator + timestamp + layer | The **full JSON manifest** with title, six-tuple, dataset CIDs, etc. |
| L4 Solution / Cert | `cert_hash` + benchmark binding + Q score + submitter + status + cert payload bytes (compact) | The **actual reconstruction output** (e.g., the 256×256×28 hyperspectral cube `.npz` file the solver produced) |
| Stakes / Mints / Rewards | Pure on-chain (no off-chain mirror) | — |
| `cert_meta` (solver label, PSNR-as-dB, runtime, framework) | NOT on-chain | Off-chain SQLite indexer DB on the explorer server |

**Director's intuition is correct: solutions are off-chain.** The
chain stores the *proof* (32-byte hash + small-event metadata); the
actual reconstructed image / video / classification output stays on
the miner's disk (and optionally on IPFS).

---

## Why the split

Putting big data on-chain is genuinely expensive ($0.50-$50 per KB
depending on chain + congestion). Hashes are 32 bytes and don't
care how big the source content is.

So the protocol stores:

- The **fingerprint** on-chain → cheap, tamper-resistant, anyone can
  verify
- The **content** off-chain → cheap to host, anyone can re-hash to
  verify it matches the chain

This is the same architecture as Bitcoin / Ethereum themselves: a
small `transaction.input.hash` on-chain pointing at a much larger
data blob off-chain.

---

## What's on-chain (Sepolia testnet today; Base mainnet at launch)

The PWM contract suite (`mainnet-v1.0.0` audit-clean) records:

### `PWMRegistry` — every L1 / L2 / L3 artifact

Stores via `ArtifactRegistered` event:
- `hash` (bytes32) — `keccak256(canonical_json(manifest))`
- `parentHash` (bytes32) — for L2/L3
- `layer` (uint8) — 1, 2, or 3
- `creator` (address)
- `timestamp` (uint256)

That's **80 bytes total** per artifact, regardless of how big the
manifest is.

### `PWMCertificate` — every L4 Solution submission

Stores via `CertificateSubmitted` event:
- `certHash` (bytes32) — `keccak256(canonical_payload)`
- `benchmarkHash` (bytes32)
- `submitter` (address)
- `Q_int` (uint8) — quality score, scaled
- `status` (uint8) — Pending / Challenged / Finalized / Invalid / Resolved
- The cert payload (~200-500 bytes packed) is also passed in the
  submit-call calldata

After challenge period: `DrawSettled` event records `rank`,
`drawAmount`, `rolloverRemaining`. Then `RoyaltiesPaid` records the
AC / CP / treasury split.

### `PWMStaking` — backing actions

Per-event records (Staked / Graduated / ChallengeUpheld / FraudSlashed):
- `artifactHash`
- `staker`
- `amount` (in wei of PWM)
- `layer` (1/2/3 for principle/spec/benchmark)
- `eventKind`

### `PWMMinting` — A-pool emissions

Per-epoch mint events:
- `principleId`
- `benchmarkHash`
- `A_k` (principle-level emission)
- `A_kjb` (per-benchmark slice)
- `remainingAfter`

### `PWMTreasury` — per-principle T_k balances

Per-principle treasury balances + payouts (e.g., M4 adversarial bounty).

### `PWMGovernance` — multisig + parameter changes

3-of-5 multisig with 48h timelock; records `setParameter` proposals,
approvals, and executions.

**Total chain footprint per artifact / cert:** ~80-500 bytes.
**Total chain footprint of the entire 531-Principle catalog:** ~250 KB
(at full registration) — fits in a single Ethereum block.

---

## What's off-chain (and where it lives)

### 1. L1 / L2 / L3 manifest JSONs — GitHub

```
pwm-team/pwm_product/genesis/l1/L1-003.json     ← canonical genesis batch
pwm-team/pwm_product/genesis/l2/L2-003.json
pwm-team/pwm_product/genesis/l3/L3-003.json

pwm-team/content/agent-imaging/principles/.../*.json     ← ~1599 manifests
pwm-team/content/agent-physics/principles/.../*.json        across 5 domain
pwm-team/content/agent-chemistry/principles/.../*.json      catalogs
pwm-team/content/agent-applied/principles/.../*.json
pwm-team/content/agent-signal/principles/.../*.json
```

Ship in the public repo (`integritynoble/pwm-public`), MIT-licensed.
Anyone clones the repo and reads them directly. The chain stores
only the hash; if a cloned manifest doesn't `keccak256` to what's
on-chain, it's been tampered with — easy to detect.

### 2. L3 benchmark **input data** — bundled samples + IPFS for full datasets

Each L3 benchmark needs measurements / synthetic snapshots that
solvers run against. Two storage tiers:

**Bundled demos** — small samples, ~1-10 MB, committed in the repo:
```
pwm-team/pwm_product/demos/cassi/sample_01/snapshot.npz
pwm-team/pwm_product/demos/cassi/sample_01/ground_truth.npz
pwm-team/pwm_product/demos/cassi/sample_01/mask.npy
pwm-team/pwm_product/demos/cassi/sample_01/meta.json
…
```

For reproducibility — anyone clones the repo and runs the reference
solver against these immediately.

**Full dataset registry** — large, IPFS-pinned via the L3 manifest's
`dataset_registry` field:
```json
"dataset_registry": {
    "primary": "KAIST hyperspectral 30 (2017)",
    "secondary": "CAVE multispectral dataset",
    "construction_method": "crop center 2x crop + 28-band downselect from 31-band source"
}
```

Bounty #6 (50,000 PWM, IPFS pinning) funds the always-available
pinning of these CIDs. Without that, full datasets would be host-
dependent.

### 3. L4 SOLUTIONS — the actual reconstruction outputs

This is what Director's question pointed at. **Reconstructed
images, videos, or classification labels are OFF-CHAIN** because
they're typically tens of MB to GB.

Where each piece lives:

| Item | Location | Size |
|---|---|---|
| `solution.npz` (the actual reconstructed cube / video / labels) | **Local disk** during the mining run; **optionally IPFS-pinned** if the miner sets `solution_uri` in the cert payload | 1-100 MB typical |
| Cert payload — `(Q score, solver_id, benchmarkHash, ω instance, optional solution_uri)` packed as bytes | Submitted **on-chain** as the calldata of `PWMCertificate.submit()` | ~200-500 bytes |
| `cert_hash` = `keccak256(cert_payload)` | Stored **on-chain** as the cert's primary key | 32 bytes |
| `meta.json` produced by the solver wrapper (`solver_label`, `psnr_db`, `runtime_sec`, `framework`) | Local disk; can be POSTed to the explorer's `cert_meta` table | <1 KB |

When a miner submits a Solution:

```
LOCAL DISK:                                       ON-CHAIN:
─────────────                                     ─────────
solution.npz   (10 MB)                            
meta.json      (200 B)                            
                       ↓                          
              pwm-node mine computes:             
                payload = {                       
                  Q: 820,                         
                  solver_id: "0x...",             
                  benchmarkHash: "0x...",         
                  ω: {...},                       
                  optional solution_uri: ...      
                }                                 
                cert_hash = keccak256(payload)    
                       ↓                          
                  PWMCertificate.submit(  ──────→  CertificateSubmitted event
                       cert_hash,                  (cert_hash, benchmarkHash,
                       benchmarkHash,               submitter, Q_int, status,
                       Q_int,                       payload bytes, timestamp)
                       payload_bytes               
                  )                               
                                                  
                  optional:                       
                  submit_cert_meta.sh POSTs to    
                  explorer API                    
                       ↓                          
                                                  SQLite cert_meta row
                                                  (solver_label="MST-L",
                                                   psnr_db=34.1,
                                                   runtime_sec=12.3)
```

**The reconstruction itself stays on the miner's disk** unless they
choose to pin it to IPFS for reproducibility (e.g., for a paper
citation, a regulator audit, or to prove provenance to a vendor).
Even then, IPFS pinning is the miner's responsibility, not the
chain's.

### 4. Solver code — reference solvers + custom

```
pwm-team/pwm_product/reference_solvers/cassi/cassi_gap_tv.py     ← reference floor (numpy, ~24 dB)
pwm-team/pwm_product/reference_solvers/cassi/cassi_mst.py        ← MST-L wrapper (~34 dB on KAIST)
pwm-team/pwm_product/reference_solvers/cacti/cacti_pnp_admm.py
pwm-team/pwm_product/reference_solvers/cacti/cacti_efficientsci.py
public/packages/pwm_core/weights/mst/mst_l.pth                    ← pretrained weights (~50 MB)
```

All committed in the public repo (MIT-licensed). Custom solvers from
external miners stay on the miner's disk OR can be pinned to IPFS
if they want others to reproduce.

### 5. Smart-contract source + ABIs

```
pwm-team/infrastructure/agent-contracts/contracts/*.sol           ← Solidity source
pwm-team/coordination/agent-coord/interfaces/contracts_abi/*.json ← compiled ABIs
pwm-team/infrastructure/agent-contracts/addresses.json            ← deployed-contract addresses
```

The compiled bytecode is deployed on-chain; the source + ABIs are
off-chain in the repo so:
- auditors can read the source
- the CLI knows which functions to call
- new client implementations (e.g., a JavaScript wallet, an R package)
  can build against the standard ABIs

### 6. The web explorer's local database

```
GCP server: /var/lib/docker/volumes/pwm_index_data/_data/pwm_index.db
```

A SQLite database that:
- Mirrors on-chain events for fast UX queries (no per-page-load chain
  reads — the indexer streams events into SQLite continuously)
- Holds the off-chain `cert_meta` annotations (solver labels, PSNR-as-dB)
  POSTed via `submit_cert_meta.sh`
- Holds joined views for the frontend (e.g., the leaderboard query)

**If this DB is wiped, the explorer rebuilds from scratch by re-reading
the chain.** No permanent data loss — only the off-chain `cert_meta`
annotations would need to be re-POSTed (those are the only data the
chain doesn't carry).

### 7. Everything else customer-facing

```
pwm-team/customer_guide/                          ← user-facing docs
pwm-team/coordination/PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md   (now in customer_guide/)
pwm-team/bounties/                                ← bounty specs
pwm-team/pwm_product/explainers/                  ← per-Principle one-pagers
pwm-team/pwm_product/benchmark_cards/             ← per-L3 YAML cards
papers/Proof-of-Solution/                         ← whitepaper + reference impls
```

All in the public repo. The chain doesn't reference any of this
directly — these are the human-readable docs that orient
researchers, regulators, and bounty claimants.

### 8. Things that NEVER go in the public repo

```
pwm-team/coordination/                            ← internal team docs (audits,
                                                    funding strategy, runbooks,
                                                    progress signals)
.env files, deploy keys                           ← gitignored
Director's local notes / experiments              ← in private integritynoble/pwm only
```

Per the public-mirror selection in `scripts/sync_to_public_repo.sh`,
only specific subtrees mirror to `pwm-public`. Coordination docs and
operational secrets stay in the founding-team-only private repo.

---

## Mental model summary

```
                 ON-CHAIN                              OFF-CHAIN
                 ─────────                             ──────────
                                                       
                                 hash               GitHub (pwm-public):
                 L1/L2/L3   ←──────────  →  pwm-team/pwm_product/genesis/l{1,2,3}/
                 hashes                          pwm-team/content/agent-*/principles/
                 (32B each)                      
                                                IPFS:
                                                L3 dataset_registry CIDs
                                                
                                 hash              Local miner disk:
                 L4 cert    ←──────────  →     solution.npz, meta.json
                 + Q_int                       (optionally IPFS-pinned via solution_uri)
                 + payload                     
                 (~300B)                       
                                                GCP SQLite (explorer DB):
                                                cert_meta (solver_label, psnr_db, …)
                                                
                 Stakes,                       
                 Mints,        ← pure on-chain;  no off-chain mirror needed
                 Rewards,      
                 Governance    
                                                GitHub (pwm-public):
                 Compiled       ─────────  →  pwm-team/infrastructure/agent-contracts/
                 bytecode                      contracts/*.sol (source) + 
                 (deployed)                    addresses.json + ABIs
```

---

## Permissions and immutability — "if the JSONs are in a public repo, can anyone change them?"

A common follow-up question: the manifests live in a public Git repo
that humans can edit. Doesn't that make them mutable? The answer is
**yes for the file system, no for the protocol**. Here's why.

### Two layers of permission

**GitHub layer (file-system access):**

- **Anyone can fork** `pwm-public` and modify their fork — public,
  free, can't be prevented (it's MIT-licensed open source).
- **Only people with write access** to `integritynoble/pwm-public`
  (today: just Director, possibly 1-2 collaborators in the future)
  can push directly.
- **Pull requests from outside contributors** require the maintainer's
  approval to merge.
- **The repo owner** can push directly, force-push, or rewrite
  history within their own copy.

**Chain layer (the cryptographic enforcement):**

- The chain stores `keccak256(canonical_json)` of each manifest at
  registration time.
- The chain has its own copy of the hash, independent of any
  off-chain repo.
- Editing the JSON in the repo does not change what's on-chain.
- A modified manifest's new hash will not match any registered
  artifact.

### What happens when someone edits a registered manifest

```
ON-CHAIN (PWMRegistry, immutable):
  L1-003 hash = 0xe3b1328c66835cd729fa50650ef1d1bac4aa407807d6d97d4979e988a99a51ea
  registered 2026-04-19, creator 0x0c566f...7dEd

REPO (mutable):
  L1-003.json file content   ─keccak256(canonical_json)─►  computed hash

  unchanged file:  computed = 0xe3b1328c66… → MATCHES on-chain  ✓
  edited file:     computed = 0xNEW_DIFFERENT_HASH → DOES NOT MATCH  ✗
```

The protocol's runtime checks:

1. `pwm-node mine L3-003` reads the local JSON, computes
   `keccak256(canonical_json)`, calls
   `PWMCertificate.submit(cert_hash, benchmarkHash, …)` where
   `benchmarkHash` is the freshly-computed local hash.
2. The contract checks: *is `benchmarkHash` a registered artifact?*
3. **If the JSON was edited, the answer is NO** — the submission
   reverts with `"benchmark not registered"`.
4. **Result:** an edit silently breaks all mining and verification
   for that artifact, and every CLI user sees the failure
   immediately.

### The one safe edit: `display_slug` and other UI-only fields

`scripts/register_genesis.py` defines a `UI_ONLY_FIELDS` filter that
strips presentation-only fields (`display_slug`, `display_color`,
`ui_metadata`) before hashing. These fields can be added or changed
in the JSON without affecting the on-chain hash:

```python
UI_ONLY_FIELDS = frozenset({"display_slug", "display_color", "ui_metadata"})
```

Editing the slug (`"cassi"` → `"cassi-v2"`) re-renders the URL but
leaves the chain binding intact. The invariant is enforced by
`scripts/test_register_genesis.py::test_hash_invariant_under_display_slug_addition`,
so any future regression that breaks the filter fails CI before it
can reach `main`.

### Permissions matrix — what the maintainer CAN and CANNOT do

| Action | Who can do it | Effect |
|---|---|---|
| Edit `display_slug` / `display_color` / `ui_metadata` on a registered manifest | Anyone with write access | Safe — UI rendering changes; chain hash unchanged because of the filter |
| Edit a manifest's substantive content (physics, scoring, dataset CIDs, baselines) | Anyone with write access | **Breaks the chain binding immediately**. Mining + verification revert. Should never happen after registration; if it does, `git revert` restores. |
| Register a new manifest (L1-532, etc.) on-chain | The deployer wallet (today, via `scripts/register_genesis.py`) | Adds a new artifact; old artifacts are unaffected |
| Delete a registered artifact from the chain | **Nobody** — the contract has no `delete` function | Once registered, `ArtifactRegistered` events are permanent |
| Change a registered artifact's hash on-chain | **Nobody** — the contract has no edit function for past events | Hashes are append-only; corrections require registering a new artifact at a new hash |
| Bypass the on-chain hash check at submission time | **Nobody** | The check is enforced inside Solidity by the `PWMCertificate.submit()` precondition |

### Practical attack scenarios and what protects against them

| Scenario | What actually happens |
|---|---|
| **Adversary forks `pwm-public`, edits L3-003 to make CASSI trivially easy, deploys their own contracts** | Their fork is a *separate protocol*, not PWM. Their cert hashes don't match `integritynoble/pwm-public`'s `PWMRegistry` registrations. Researchers citing "PWM L3-003" cite the original on-chain hash, not the fork. The fork has zero adoption signal because nothing builds on it. |
| **Adversary submits a PR that subtly weakens an L3 epsilon threshold** | Code review catches it — substantive manifest changes are visible diffs. Even if merged, the chain hash doesn't auto-update; a separate `register_genesis.py` re-run would be needed (which the deployer wallet controls) to apply the change on-chain. The two-step gap creates a public paper trail and gives reviewers time to catch the change. |
| **Maintainer accidentally edits `L3-003.json` (typo fix on a paragraph in a `description` field)** | Mining breaks immediately for that benchmark — CI / smoke tests catch within minutes. `git revert` fixes it; no on-chain damage. |
| **Maintainer deliberately rewrites the substantive content of a registered manifest** | Mining breaks for everyone. To "publish" the change, the maintainer would need to register a new artifact at a new hash (e.g., `L3-003v2`) — a public on-chain event with a clear paper trail. The original `L3-003` and any certs bound to it remain intact. |
| **Multisig signer key compromise** | An attacker who captures 3 of 5 signing keys could change governance parameters (caps, periods) but **still cannot retroactively alter `ArtifactRegistered` events** — the contract has no such function. They could register *new* malicious artifacts, but those would appear as new entries in the catalog, not as silent overwrites of existing ones. |

### What this means for the protocol's trust model

**The owner cannot retroactively change a registered Principle, Spec,
or Benchmark. Neither can anyone else.** The repo files are editable
in the file-system sense, but every meaningful protocol operation
re-derives the chain hash and bails out on mismatch. The chain is
the cryptographic source of truth; the repo is a content-addressable
cache that anyone can verify by re-hashing.

If the maintainer genuinely needs to "fix" a registered manifest
after the fact (e.g., the L3 dataset's IPFS CID rotates because the
pinning service changed), the protocol's design says: **register a
new artifact at a new hash, deprecate the old one in human-readable
docs.** Existing certs stay bound to the old hash forever; the new
hash gets picked up by future submissions.

For meaningful tampering an attacker would need to either:

1. Take over the 3-of-5 multisig **and** register a malicious
   replacement (visible on-chain event with clear paper trail), or
2. Convince every researcher / regulator / cited paper to migrate
   to a fork that they trust over the original protocol.

Both are very hard. That's the core of what makes the protocol
trustworthy despite living in a public, mutable Git repo.

---

## How L1/L2/L3 on-chain and off-chain are kept in agreement

A natural follow-up: if the `.json` files in the repo can be edited
and the on-chain hash is independent of them, **how does the system
ensure the two stay consistent over time?** The answer is six
interlocking mechanisms; together they make drift either impossible
to do silently, or impossible to apply at the protocol level.

### The relationship in one sentence

The chain stores `keccak256(canonical_json(manifest))` as the
artifact's primary key. The repo stores the manifest content. **The
hash IS the link** — and the protocol re-derives it on every
operation, so the two sides are forced to stay in sync or every
operation against that artifact breaks loudly.

### Visual model — what binds the two together

```
                         The hash IS the binding
                         ───────────────────────

      OFF-CHAIN                                                ON-CHAIN
   (mutable file)                                          (immutable hash)
   ──────────────                                          ────────────────

   pwm-team/
   pwm_product/                       keccak256(             PWMRegistry
   genesis/l1/    ──canonical_json──►   canonical_json) ───►  ───────────
   L1-003.json                                                {
                                                                "0xe3b1328c…": {
   {                                                              parent: 0x0…,
     "artifact_id": "L1-003",                                     layer: 1,
     "title": "CASSI",                                            creator: 0x0c56…7dEd,
     ...                                                          timestamp: 2026-04-19,
   }                                                            },
                                                                ...
                                                              }

     ↑                                                          ↑
   anyone can edit                                            nobody can edit
   (forks, PRs)                                               (Solidity has no UPDATE)
```

The hash is **computed**, not stored, on the off-chain side. The
chain doesn't depend on a specific JSON file existing — it depends
on a JSON file existing **that hashes to the same value**. Any
clone (Director's, an external auditor's, a malicious fork) is
verifiable against the chain by the same re-hash test.

### The four possible "agreement states"

| State | Repo JSON | Chain entry | Behavior |
|---|---|---|---|
| **A. In sync** | exists, hash = X | exists at hash X | Everything works — mine, verify, stake, browse all succeed |
| **B. Drifted (edit broke it)** | exists, hash = Y ≠ X | exists at X | Mining/staking against this artifact silently reverts with `"benchmark not registered"` because the CLI computes Y and looks for Y on chain, finds nothing |
| **C. Repo has it but chain doesn't** | exists | not registered | The artifact is a *draft*. CLI works for offline browsing; mining fails because no on-chain entry exists. Common for newly authored manifests awaiting batch registration |
| **D. Chain has it but repo doesn't** | missing | exists at X | CLI can't find the manifest locally to inspect; only Etherscan / direct chain query works. Means the user has the wrong repo branch / version |

State A is the goal. State B is a regression that gets caught
immediately. States C and D are normal during authoring or during
clone-out-of-sync. The protocol is designed to make all four states
**detectable**.

### Six mechanisms that enforce / detect agreement

#### 1. Per-operation re-hash (automatic, runtime)

Every CLI operation re-derives the hash before any chain call:

```python
# pwm-node/commands/mine.py — the actual code path
benchmark_hash = _keccak256_hex(_canonical_json(artifact))    # local re-hash
submit_certificate(cert_hash, benchmark_hash, ...)            # contract call
# Solidity: require(registry.getArtifact(benchmark_hash).layer != 0)  ← reverts if mismatch
```

Every miner, verifier, and staker performs a fresh consistency check
on every action. If anyone's repo copy drifts, their next operation
fails — visible to them and to anyone watching the chain for failed
submission attempts.

#### 2. Test suite with explicit chain-hash assertions (CI, per-PR)

`pwm-team/infrastructure/agent-cli/tests/test_hash_convention.py`
walks all 6 CASSI/CACTI genesis artifacts (L1/L2/L3 × 2), re-hashes
each, and asserts equality with the known on-chain hash:

```python
@pytest.mark.parametrize("artifact_id,expected_hash", [
    ("L1-003", "0xe3b1328c66835cd729fa50650ef1d1bac4aa407807d6d97d4979e988a99a51ea"),
    ("L2-003", "0x471e7017692cde623cee2741e751413cfb4752457429f128c0004174fea86896"),
    ("L3-003", "0xdc8ad0dc68682eff750188c8d4d84179b3f7deddee1af562bc3b085794048b4a"),
    ...
])
def test_genesis_artifact_hash_matches_onchain(artifact_id, expected_hash):
    obj = load_manifest(artifact_id)
    computed = keccak256_canonical_json(obj)
    assert computed == expected_hash, f"{artifact_id} drifted!"
```

If a PR edits any registered manifest substantively (not just a
`display_slug` change), this test fails on CI before merge. The
maintainer literally cannot push a change that orphans a registered
artifact without first seeing 6 red Xs.

#### 3. UI_ONLY_FIELDS filter for safe edits (deliberate carve-out)

`scripts/register_genesis.py` defines:

```python
UI_ONLY_FIELDS = frozenset({"display_slug", "display_color", "ui_metadata"})
```

These fields are stripped before hashing, so adding a slug to a
registered manifest doesn't invalidate the chain hash. Regression-
tested by `scripts/test_register_genesis.py::test_hash_invariant_under_display_slug_addition`.

#### 4. Append-only chain semantics (Solidity-level guarantee)

The PWMRegistry contract has `register()` but no `update()` or
`delete()`. Once an `ArtifactRegistered` event is emitted, it's
permanent:

- Even if a maintainer wanted to retroactively change a registered
  artifact, the chain wouldn't let them
- A "correction" requires registering a NEW artifact at a new hash,
  leaving the old one as-is
- Auditors looking at the chain see the full registration history;
  no silent overwrites are possible

#### 5. Multisig-gated registration (governance-level guarantee)

`scripts/register_genesis.py` calls `PWMRegistry.register()` from
the deployer wallet. The deployer is the only address authorized to
add to the canonical genesis batch. After mainnet, this transitions
to multisig governance (3-of-5).

- An adversary with write access to the GitHub repo cannot register
  a new artifact on chain
- They can only modify off-chain JSONs, which then fail per-operation
  hash check
- "Register a malicious new principle" requires keys, not just
  GitHub access

#### 6. Loud failure modes (no silent drift)

Drift never fails silently. Every disagreement between the off-chain
content and the on-chain hash triggers an immediate, visible
operation failure:

| Detection point | What the user sees | Recovery |
|---|---|---|
| Pre-commit (local) | Hash test runs; commit blocked | Revert the change OR confirm it's a UI-only field |
| CI on PR | Red X on `test_hash_convention.py` | Block merge until fixed; investigate why the manifest changed |
| Runtime (CLI mining) | `pwm-node mine ...` reverts with `"benchmark not registered"` | `git diff` against canonical pwm-public; revert the local edit; or pull the right branch |
| Runtime (explorer) | Benchmark page shows correct title from JSON but `/api/leaderboard/<id>` returns no certs because chain has no record matching the new hash | Check explorer's git checkout; sync to canonical pwm-public |

In every case the failure is loud and traceable to the specific
manifest that drifted.

### How to detect drift right now (concrete commands)

```bash
# 1. Run the genesis hash-convention test (~2 sec, takes 6 SHAs vs known on-chain values)
python3 -m pytest pwm-team/infrastructure/agent-cli/tests/test_hash_convention.py -v

# 2. Run the UI_ONLY_FIELDS regression test (~1 sec)
python3 -m pytest scripts/test_register_genesis.py -v

# 3. Spot-check one manifest manually
python3 -c "
import json, sys
sys.path.insert(0, 'scripts')
from register_genesis import _canonical_json
from eth_utils import keccak
obj = json.load(open('pwm-team/pwm_product/genesis/l1/L1-003.json'))
h = '0x' + keccak(_canonical_json(obj)).hex()
print('local hash :', h)
print('expected   : 0xe3b1328c66835cd729fa50650ef1d1bac4aa407807d6d97d4979e988a99a51ea')
print('match      :', h == '0xe3b1328c66835cd729fa50650ef1d1bac4aa407807d6d97d4979e988a99a51ea')
"

# 4. Live verify against on-chain (browse Sepolia events)
# Visit: https://sepolia.etherscan.io/address/0x2375217dd8FeC420707D53C75C86e2258FBaab65#events
# Confirm the L1/L2/L3 hashes appear in the ArtifactRegistered events list.
```

As of this writing all 6 genesis artifacts hash bit-identically to
their on-chain registrations.

### Bottom line — agreement is structural, not trust-based

**The agreement is not enforced by trust ("Director promises not to
edit").** It's enforced by:

1. **Cryptographic content addressing** — the hash IS the lookup key
2. **Append-only on-chain semantics** — the registered state can't
   be retroactively modified
3. **Per-operation re-hashing** — every CLI/contract call verifies
   fresh
4. **CI tests with explicit chain-hash assertions** — drift fails
   before merge
5. **Multisig-gated registration** — only the founding team can
   add canonical entries
6. **Loud failure modes** — drift surfaces at the first
   mining/staking attempt

The repo's `.json` files are editable, but every edit immediately
diverges the hash, which immediately breaks the protocol-level
binding, which immediately surfaces as a test failure or a revert.
There is no code path where a maintainer (or anyone else) edits a
registered manifest substantively and the chain quietly accepts it.

---

## Why this matters for different audiences

### Researchers citing PWM in papers

**Cite the cert hash in your methods section.** It's permanent,
verifiable, and links to all other public artifacts (benchmark hash
→ L3 manifest on GitHub → dataset on IPFS). Reviewers can re-derive
your Q score from the on-chain cert + the off-chain manifest.

If you also pin your `solution.npz` to IPFS and embed the CID in the
cert payload's `solution_uri`, anyone can re-execute scoring on your
exact reconstruction. That's the gold-standard reproducibility level.

### Regulators / auditors verifying clinical-AI claims

The chain is your **trust anchor**. A vendor's `cert_hash` is
immutable proof that they submitted a specific Q score against a
specific benchmark on a specific date. You can:
1. Pull the cert from the chain
2. Pull the L3 manifest from GitHub
3. Verify the manifest hash matches what's on-chain
4. Inspect the L3 acceptance protocol (e.g., CO-RADS, ETDRS)
5. Optionally pull the vendor's `solution_uri` and re-run scoring

**No trust in the vendor's reported numbers required** — every step
is independently verifiable.

### Industry teams running their own evaluation

You can do the entire flow without ever submitting on-chain:
- Clone the public repo
- Read the L3 manifest
- Pull the dataset (bundled demos or IPFS)
- Run your solver
- Compute your Q score locally

**Submitting on-chain is opt-in** — only do it if you want a
tamper-resistant public record (for grant evidence, FDA submission,
press release). Otherwise everything works offline.

### External developers writing new Principles

Your manifests live in the GitHub repo (off-chain) until agent-coord
batch-registers them on-chain at the next genesis-extension event.
The chain side is a one-line `PWMRegistry.register(hash, ...)` call
per artifact. Everything else — the schema, the documentation, the
review process — is off-chain.

---

## Frequently confused points

| Confused belief | Reality |
|---|---|
| "PWM stores my reconstruction on the blockchain" | No. Only the cert hash. Reconstruction stays on your disk. |
| "I need to pay gas for every benchmark image" | No. The big data is off-chain. Gas covers only the 32-byte cert hash + small payload. |
| "If the explorer's SQLite DB dies, I lose my cert" | No. The cert is on-chain. The SQLite DB only mirrors on-chain events for fast queries; it can be rebuilt from scratch by re-reading the chain. The only off-chain-only data is `cert_meta` (solver labels, PSNR), which you'd need to re-POST. |
| "I have to upload my dataset to the chain" | No. Datasets live on IPFS (or git). The L3 manifest references CIDs. The chain only sees the manifest's hash. |
| "PWM controls my private key / data" | No. PWM is permissionless. You control your own wallet, your own data, your own solver code. The protocol just standardizes the on-chain proof + scoring formula. |

---

## Cross-references

- `PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md` — full create-and-use flows for all 4 layers
- `PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md` — how to author new Principles + the on-chain registration flow
- `pwm-team/infrastructure/agent-contracts/contracts/` — Solidity source for all 7 contracts
- `pwm-team/infrastructure/agent-contracts/addresses.json` — current deployed addresses (Sepolia today; Base mainnet at launch)
- `https://sepolia.etherscan.io/address/0x2375217dd8FeC420707D53C75C86e2258FBaab65` — PWMRegistry on Sepolia (browse hashes directly)
- `https://sepolia.etherscan.io/address/0x8963b60454EC1D9F65eE3cbF7aBC5D1220C3dB08` — PWMCertificate on Sepolia (browse cert events)
- `https://explorer.pwm.platformai.org` — web explorer that joins on-chain events with off-chain `cert_meta` for human-readable display
