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

### Why a single-character change to the JSON breaks the binding

A natural follow-up: *if I change one tiny detail in the JSON,
why does the hash change so completely that the chain entry no
longer matches?* The answer is the **avalanche effect** — the
foundational property of cryptographic hash functions like the
keccak256 used by Ethereum.

#### Concrete demonstration with the real `L3-003.json`

```
ORIGINAL L3-003.json:
  hash = 0xdc8ad0dc68682eff750188c8d4d84179b3f7deddee1af562bc3b085794048b4a

After changing ONE letter case ("CASSI" → "Cassi"):
  hash = 0xfe2b71053066a0c032b2a28403bbf033ace452fdd9126346ee67b6d80ea83981
  → ~128 of the 256 output bits flipped (50%)

After changing ONE number (epsilon 28.0 → 28.001):
  hash = 0xeb16774aa9195c5826e041bc2dd80b512f0a5bbadbaccbdebb66cdb3fce32686
  → totally unrelated to original

After adding ONE trailing space:
  hash = 0x35ebf748263d1a526e13fea94b24d2c28318dc8b48e47400dd787e06a0a50c1f
  → totally unrelated

NOT a change: re-pretty-printing the JSON with extra indentation
  hash = 0xdc8ad0dc68682eff750188c8d4d84179b3f7deddee1af562bc3b085794048b4a
  → identical (canonical_json normalizes whitespace + key order)
```

#### Why this happens

A cryptographic hash function takes any-length input and outputs a
fixed-length number — for keccak256, exactly 256 bits (= 64 hex
chars). It is engineered with three deliberate properties:

**Property 1 — Avalanche.** When ONE bit of input changes, about
**half of the output bits flip in unpredictable positions**. This
is a deliberate design feature: the function performs 24 rounds of
bit-level mixing operations (S-box substitutions, rotations, XORs
across multiple state lanes) so any single-bit change cascades
through every round.

**Property 2 — Determinism.** Run keccak256 on the same input on
any machine, in any language, at any time → same hash. The
function has no randomness; the "randomness" is structural in how
the bits get mixed.

**Property 3 — Preimage resistance.** Given a hash, you cannot
find an input that produces it (other than by brute-force guessing).
For a 256-bit output, that's 2^256 ≈ 10^77 possibilities — more
than the estimated number of atoms in the observable universe.

#### Why these properties matter for the protocol

| Property | What it gives the protocol |
|---|---|
| Avalanche | A 1-character JSON change → totally different hash → impossible to "almost match" the chain entry |
| Determinism | Anyone can re-hash a JSON locally and verify it matches the chain |
| Preimage resistance | Nobody can craft a malicious JSON that happens to hash to the same value as the original (~10^77 search space) |
| 256-bit output | Collisions are statistically impossible — no two different inputs ever produce the same hash in practice |

#### The one normalization step: `canonical_json`

You might worry that pretty-printing or re-ordering keys would
spuriously change the hash, since the bytes ARE different. The
protocol handles this with **canonical JSON**:

```python
json.dumps(obj, sort_keys=True, separators=(",", ":"))
```

This produces a single, deterministic byte sequence regardless of
how the file is formatted on disk:

- **Sorted keys** — `{"b": 2, "a": 1}` → `{"a":1,"b":2}` (alphabetical)
- **Compact separators** — no spaces after `,` or `:`
- **No trailing whitespace, no indentation**

So the hash is sensitive to:

- ✅ Any value change (1 character in any string, 1 digit in any
  number, adding or removing a key)
- ❌ NOT sensitive to formatting / whitespace / key order

This is the right balance: **meaningful changes are caught;
cosmetic changes are tolerated.** That's why `git diff` showing a
re-formatted manifest doesn't break mining, but `git diff` showing
a value change does.

#### The intuition

Think of `keccak256` as a **digital fingerprint** for content:

- A person's fingerprint doesn't change if they put on different clothes (formatting)
- But someone with even a slightly different finger has a totally different fingerprint pattern
- Two people NEVER have identical fingerprints by accident
- Given a fingerprint, you can't reconstruct the person

The chain stores the JSON's "fingerprint" (`0xdc8ad0dc…` for L3-003).
Anyone who claims to have "the same JSON" must produce a file with
the same fingerprint — and even a 1-character change makes that
mathematically impossible.

**That's why the agreement enforcement works:** there's no edit
small enough to escape detection. Either the hashes match exactly
(✅ in sync) or they're totally unrelated (❌ drifted). There's no
in-between, no fuzzy match, no "close enough." Cryptographic
hashing is binary: identical or completely different.

### How the hash actually "measures" the JSON's content

The previous subsection establishes *that* a tiny change breaks the
binding. A natural follow-up: *how does the hash actually look at
the content of the JSON?* The answer is that it doesn't understand
JSON syntax at all — it treats the file as a flat sequence of bytes
and mixes every byte into the output through 24 rounds of bit-level
operations. Here's the chain step-by-step.

#### Step 1 — JSON file → canonical string

The file on disk is text. After
`json.dumps(obj, sort_keys=True, separators=(",", ":"))`, you get a
single string with sorted keys and no whitespace:

```
{"artifact_id":"L1-003","title":"CASSI"}
```

40 characters. Every character — `{`, `"`, `:`, `,`, digits,
letters — is part of the input.

#### Step 2 — Each character → one byte (UTF-8)

Each character has a numeric code (its ASCII / UTF-8 value):

| Character | Decimal | Hex | Binary |
|---|---|---|---|
| `{` | 123 | `0x7b` | `01111011` |
| `"` | 34  | `0x22` | `00100010` |
| `a` | 97  | `0x61` | `01100001` |
| `0` | 48  | `0x30` | `00110000` |
| `1` | 49  | `0x31` | `00110001` |

So `{"artifact_id":"L1-003","title":"CASSI"}` becomes (40 bytes,
shown as hex):

```
7b 22 61 72 74 69 66 61 63 74 5f 69 64 22 3a 22 4c 31 2d 30 30 33 22 2c 22 74 69 74 6c 65 22 3a 22 43 41 53 53 49 22 7d
↑                                                                                                                       ↑
{                                                                                                                       }
```

40 bytes = 320 bits. **Every single one of those 320 bits is input
to the hash function.** No JSON-syntax awareness, no field-by-field
walk — just raw bytes.

#### Step 3 — Keccak256 mixes ALL the bytes through 24 rounds

The hash function (`keccak256`, the SHA-3 variant Ethereum uses)
runs the byte sequence through this process:

1. **Pad** the input to a multiple of 1088 bits (so any-length input fits)
2. **Absorb** the padded input into a 1600-bit internal state, XORing
   1088 bits of input at a time
3. **Permute** the state by running the **Keccak-f[1600] permutation**
   — 24 rounds of:
   - **θ (theta)** — XOR each bit with the parity of two neighboring columns
   - **ρ (rho)** — bitwise rotate each lane by a fixed amount
   - **π (pi)** — permute the position of each lane in the 5×5×64 state matrix
   - **χ (chi)** — non-linear S-box: each bit is XORed with a function of two neighbors
   - **ι (iota)** — XOR a round-specific constant
4. **Squeeze** out 256 bits from the permuted state → that's your hash

Every one of those 24 rounds touches every bit. So changing 1
input bit propagates: round 1 affects ~5 output bits → round 2
spreads those to ~25 → round 3 to ~125 → after a few rounds, every
output bit depends on every input bit. By round 24, the dependency
is "complete" and effectively unpredictable.

#### Step 4 — Concrete demo: flipping ONE input bit

Watch what happens when one ASCII character changes from `'0'`
(`0x30 = 00110000`) to `'1'` (`0x31 = 00110001`) — that's exactly
**one bit flipped** in the 320-bit input:

```
Original input bytes:  ...30 30 33...   ("003")
Modified input bytes:  ...30 31 33...   ← single-bit change
                            ↑
                            one bit flipped (LSB of one byte)
```

The 256-bit output hashes:

```
Original:  69c426a5e830c55cf0d781392b89c82da990e6af1e4dd199e30e4a61e1cc42b8
Modified:  8cafda27c0f39d49c2f21b5f59257911a0c49e4d33530beebd6223caf5343556

                                          ↳ 129 of 256 bits flipped (~50%)
```

**One-bit input change → roughly half the output bits flip in
unpredictable positions.** That's the avalanche effect at the byte
level.

#### Why every byte gets "measured" equally

Because of the absorption + permutation structure:

- Every input byte gets XORed into the 1600-bit state during the absorb phase
- Every round of the permutation MIXES bits across the whole state — no bit stays "isolated" after even 1-2 rounds
- After 24 rounds, the contribution of every input byte has been spread across every output bit

So the answer to *how the hash measures the JSON's details*: **it
doesn't measure anything semantic.** It just XORs every byte into
a giant state and stirs vigorously enough that every input byte
affects every output bit. The "stirring" is so thorough that even
a 1-bit change is statistically indistinguishable from a completely
different input.

#### What this means for the protocol

When you change ONE detail in `L3-003.json`:

- That detail = 1+ characters = 8+ bits in the byte sequence
- Those bits flip in the input to keccak256
- After 24 rounds of mixing, the output hash has ~half its 256 bits flipped
- The new hash is **statistically indistinguishable from a totally unrelated input**
- It bears no visible relation to `0xdc8ad0dc…`

There is **no edit small enough** to keep the hash close to the
original. Cryptographic hashing is binary: bit-identical input →
bit-identical output; anything else → unrelated output.

This property is called the **strict avalanche criterion**:

> Each output bit should change with probability 0.5 when any
> single input bit is changed.

Keccak256 satisfies this. SHA-256 satisfies this. Any hash function
that DIDN'T satisfy this would be considered cryptographically
broken (you could partially recover input information from
similarities in output).

#### Common misconceptions

| What you might think | What actually happens |
|---|---|
| "The hash sees the JSON structure / fields / values" | No — it sees only a flat byte sequence. JSON syntax is invisible to the hash function. |
| "Small changes → small hash diffs" | No — single-bit input change → ~128 output bits flip. |
| "The hash function is 'reading' the content" | Closer to: every byte is XORed into a state and permuted 24 times. |
| "I could engineer a small edit that keeps the hash close" | No — every edit produces a statistically-random-looking new hash. |
| "The hash function understands meaning of fields like `epsilon` vs `title`" | No — it can't tell the difference between changing a meaningful field and a meaningless one. Both produce uncorrelated output. (This is a feature: the protocol doesn't have to enumerate which fields matter.) |

The chain doesn't trust you to be honest about content. It trusts
the math: any change you make is **mathematically guaranteed** to
produce a hash that doesn't match the on-chain entry. **The hash
is the protocol's way of measuring without trusting.**

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

## What if the owner tries to silently rewrite a registered manifest?

The previous sections cover the general case. A natural follow-up
zooms in on the worst-case threat model: **what if the GitHub-repo
owner — i.e., Director — tries to substantively change a registered
artifact, e.g., weaken `L3-003`'s forward model so existing solvers
trivially pass?** The protocol's defense is layered, and crucially it
doesn't depend on Director being well-behaved.

### What the owner CAN technically do

| Action | Possible? | Effect |
|---|---|---|
| Edit `L3-003.json` to weaken the forward model in the repo | ✅ Yes — owner has write access | None on-chain |
| Force-push to overwrite git history | ✅ Yes | None on-chain |
| Get the modification deployed to mining users | ❌ No (see below) | — |
| Get the modification accepted by the chain | ❌ No (see below) | — |
| Hide the modification from auditors / users | ❌ No (see below) | — |

**The key distinction:** editing the file is permitted; making the
edit consequential at the protocol level is not.

### What stops the modification from being applied

#### 1. The on-chain hash for L3-003 is permanent

```
PWMRegistry on-chain:
  L3-003 → 0xdc8ad0dc68682eff750188c8d4d84179b3f7deddee1af562bc3b085794048b4a
           (registered 2026-04-19, immutable)
```

The contract has no `updateArtifact()` function. There is no admin-
override path. **Even via the 3-of-5 governance multisig with 48h
timelock, the only governance capability is to change protocol
parameters (caps, periods, etc.) — not to retroactively rewrite an
`ArtifactRegistered` event.**

#### 2. Editing the JSON only orphans the chain entry

If the owner modifies `L3-003.json`'s `E.forward_model`, the new file
hashes to `0xNEW...`. Now:

```
On-chain:                                Off-chain repo:
L3-003 = 0xdc8ad0dc...                   L3-003.json hashes to 0xNEW...
   ↑                                          ↑
   │                                          │
   └──────────── these no longer match ──────┘
```

The on-chain entry doesn't change. It still says "L3-003 is the
artifact whose hash is `0xdc8ad0dc...`". But there's no JSON in the
repo that hashes to that value anymore — the on-chain entry now
points at "missing" off-chain content.

#### 3. Mining fails immediately and visibly

Every user running `pwm-node mine L3-003`:

```python
benchmark_hash = keccak256(canonical_json(local_L3_003_file))
# benchmark_hash = 0xNEW... (because the file is the modified version)

contract.submit(cert_hash, benchmark_hash, Q_int, payload)
# Solidity: require(registry[benchmark_hash].layer != 0, "benchmark not registered")
# REVERTS — benchmark_hash 0xNEW... has no on-chain entry
```

Every miner sees `"benchmark not registered"` the next time they
mine L3-003. The CLI surfaces the offending hash in the error
message. **The owner can't push the modification through silently —
they can only push a state where mining is broken for everyone.**

#### 4. CI catches it before merge

`pwm-team/infrastructure/agent-cli/tests/test_hash_convention.py`
contains an explicit assertion that `L3-003.json` hashes to
`0xdc8ad0dc...`. If the owner edits the file:

- Local pre-commit runs the test → fails
- CI on the PR runs the test → red X
- They'd have to **deliberately bypass CI** to merge it
- Merging still doesn't change anything on-chain — it just commits a
  broken state to `main` for the next reviewer to revert

#### 5. The git commit is forensically visible

Even if the owner force-pushes to hide the change:

- The pwm-public mirror has its own commit history (created by
  `sync_to_public_repo.sh`); they'd have to force-push there too
- Anyone who cloned before the force-push has the original content
  on their disk forever
- The chain hash `0xdc8ad0dc...` provides cryptographic proof of what
  the manifest used to be — anyone can show "the original L3-003
  hashed to X; here's the JSON that hashes to X; here's the new JSON
  that doesn't"
- Reviewers, auditors, regulators, and grant reviewers all comparing
  cited cert hashes to the chain see the same disconnect

#### 6. The "register a new artifact" path also leaves a paper trail

What the owner COULD do is register a new artifact at the new hash:

```python
# Hypothetical: register a v2 of L3-003 with weakened forward model
PWMRegistry.register(0xNEW..., parent_hash=L2-003-hash, layer=3, creator=owner)
```

But this:

- Doesn't replace the original — it adds a NEW entry; the original
  `0xdc8ad0dc...` stays on chain forever
- Is a public on-chain transaction visible on Etherscan
- Takes the deployer wallet (owner's key, with funded Sepolia ETH)
- Would need to be plumbed into `register_genesis.py`'s
  `ARTIFACTS_TO_REGISTER` list (a code change in a public commit)
- Researchers / auditors comparing "L3-003 cited 2026-04-22" vs
  "owner's new L3-003-v2 cited 2026-05-05" see TWO entries, not a
  silent swap
- All existing certs (the 10 D5-stress-test ones, plus any future
  MST-L cert) STILL bind to the original `0xdc8ad0dc...` — they
  don't migrate

In other words, a v2 isn't an override — it's a NEW thing alongside
the original, fully visible.

### Threat-mitigation matrix — what each mechanism prevents

| Mechanism | Prevents what? |
|---|---|
| **Append-only Solidity (no UPDATE)** | Retroactive in-place modification of the on-chain entry. Even with multisig keys, this is impossible. |
| **Per-operation re-hash in CLI** | Silent acceptance of a modified manifest. Every miner immediately sees `revert("benchmark not registered")`. |
| **CI hash test** | Merging the modification to `main` without explicit override + visible failure |
| **Cryptographic audit trail (chain hash)** | Hiding that a modification happened. Anyone can compare the chain entry to the modified JSON in 2 lines of code. |
| **Git history (especially pwm-public mirror)** | Quietly rewriting history without leaving traces |
| **Existing certs bind to old hash** | Migrating past submissions to a new "version" — old certs are forever bound to old hash |

### What it would actually take to weaken L3-003 in practice

For a substantive modification of L3-003's forward model to actually
take effect at the protocol level, the owner would need ALL of these
simultaneously:

1. Push the modified JSON, **and**
2. Bypass / override the CI hash test, **and**
3. Re-register a new artifact at the new hash on-chain (requires the
   deployer wallet with Sepolia ETH; later requires 3-of-5 multisig
   signatures for any contract-state change), **and**
4. Convince every researcher, regulator, miner, and audit firm that
   the new artifact is the "real" L3-003 — despite the original
   `0xdc8ad0dc...` still being on-chain with full registration
   history, **and**
5. Deal with the fact that all existing certs on the leaderboard,
   all published papers citing L3-003, and all reproducibility chains
   (e.g., FDA submissions citing a cert hash) are still bound to the
   original.

**Step 4 is where it falls apart.** The chain provides cryptographic
proof that the original hash was registered first by the deployer
wallet. Any third party can compare a "new" L3-003 to the chain's
record and see the discrepancy. **The protocol doesn't depend on the
owner being well-behaved — it depends on bad behavior being publicly
visible and easily disproven, which it is.**

### Practical owner-options summary

| Approach | Outcome |
|---|---|
| Edit JSON, push to main | CI fails. If forced, mining breaks for everyone immediately. Visible. |
| Edit JSON, force-push to mirror | Mirror users notice via `git log`; chain hash still doesn't match. Visible. |
| Register a new artifact L3-003-v2 with weakened forward model | Public on-chain event; old artifact still in registry; researchers can choose; visible. |
| Try to claim "L3-003 = the new content" | Direct contradiction with on-chain `0xdc8ad0dc...`; trivially disproven by anyone with `keccak256`. |

**There's no path for the owner to silently weaken the forward model
and have it accepted.** Their options are: break the protocol loudly,
add a v2 artifact transparently, or leave the original untouched.

### What the protocol genuinely trusts the owner with

The only thing the protocol genuinely trusts the owner with is:
**deciding what to register in the first place.** That's the
founding-team's privileged moment — picking which Principles, which
Specs, which Benchmarks become canonical at genesis (or at later
batch-extensions). Once registered, the owner loses the ability to
silently change them, just like everyone else.

This is the same trust model as Bitcoin/Ethereum themselves: the
chain depends on the genesis state being authored honestly, but
once that genesis is locked in, no party — including the original
authors — can rewrite it.

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
