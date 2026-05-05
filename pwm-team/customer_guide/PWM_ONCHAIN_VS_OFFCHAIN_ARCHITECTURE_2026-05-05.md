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
