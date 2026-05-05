# Contributing a New PWM Principle (L1 + L2 + L3)

**Audience:** External contributors authoring a new Principle (L1 +
its child L2 spec + L3 benchmark). Bounty #7 Tier B claimants in
particular, but applicable to any open-source contributor.
**Entry point for general flow:** `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md`

---

## What you're contributing

A "Principle" in PWM is a 3-level package:

| Layer | What it is | Authoring effort |
|---|---|---|
| **L1** | Forward model + parameter space + DAG primitive chain | ~1-2 hr if the physics is well-known |
| **L2** | Six-tuple (Ω, E, B, I, O, ε) for one concrete instance of L1 | ~1-3 hr |
| **L3** | P-benchmark with rho=50 instances + anti-overfitting M1-M6 + dataset CIDs | ~3-6 hr (most of the work — dataset curation, baseline measurement) |

So a complete contribution is a 1-2 day effort for a single Principle.
Hand-authored skeletons can reduce this; see Bounty #7 Tier B for an
example of skeleton-then-fill workflow.

---

## Three contribution paths (pick one)

### Path A — Direct on-chain (truly permissionless, no review)

For contributors who want to publish without going through any
centralized review.

```bash
# 1. Author your three manifests locally:
#      L1-XXX_<slug>.json
#      L2-XXX_<slug>.json
#      L3-XXX_<slug>.json
#    See "Manifest schema" below.

# 2. Pin to IPFS (any pinning service):
ipfs add L1-XXX_<slug>.json   # → CID
ipfs add L2-XXX_<slug>.json   # → CID
ipfs add L3-XXX_<slug>.json   # → CID

# 3. Register on-chain via pwm-node:
pwm-node --network testnet register-principle ./L1-XXX_<slug>.json
pwm-node --network testnet register-spec ./L2-XXX_<slug>.json --parent-l1 0x<L1-hash>
pwm-node --network testnet register-benchmark ./L3-XXX_<slug>.json --parent-l2 0x<L2-hash>
```

**Pros:**
- Truly permissionless; no central gatekeeper
- Instant publication
- You control all the timing and content

**Cons:**
- Your manifest gets a "self-submitted" trust badge in the explorer
  (no verifier-agent S1-S4 review)
- Discoverability is lower — the explorer ranks self-submitted entries
  below verified ones in `/match` results
- Cross-domain Jaccard distinctness check (≥0.30 threshold) hasn't
  run, so you risk near-duplicate of an existing Principle being
  ignored by miners

### Path B — GitHub PR (curated, recommended)

For contributors who want quality review and the explorer's
"verifier-reviewed" trust badge.

```
1. Open a GitHub issue in integritynoble/pwm-public titled:
     [L1 claim] L1-XXX <slug> — <author name>

2. agent-coord reserves the next free numeric ID for you on the issue
   (today: L1-532, since 531 are used) and confirms your slug doesn't
   collide with an existing one.

3. Author your three manifests locally using the reserved ID.

4. Open a PR titled:
     feat(genesis): add L1-XXX <slug>
   PR body template at end of this doc.

5. Verifier-agents review:
   - S1 (dimensional consistency)
   - S2 (well-posedness in declared regime)
   - S3 (convergent solver class with rate)
   - S4 (hardness-rule check on epsilon_fn)
   - Cross-domain Jaccard distinctness ≥ 0.30 from closest existing entry

6. agent-coord registers your manifests on-chain at the next genesis-
   extension event (typically batched weekly post-mainnet).

7. Optional: claim Bounty #7 Tier B (~2,000 PWM per anchor) on the
   first external L4 submission against your benchmark.
```

**Pros:**
- Verifier-reviewed → "verified" trust badge in the explorer
- Hash-collision protection (agent-coord reserves your ID before authoring)
- Cross-domain distinctness verified (no duplicate Principles)
- Eligible for Bounty #7 Tier B reward

**Cons:**
- Sequenced by reviewer availability; ~3-7 days from PR to on-chain
- Requires GitHub account and willingness to engage with the public review

### Path C — Third-party aggregator

A future website or service may collect submissions and route them
through Path A or Path B on contributors' behalf. Not yet
operational; reserved for future ecosystem expansion.

---

## Numeric ID assignment

The current sequential allocation:

```
L1-001 .. L1-502   v1 baseline                  (founder-authored, batch import)
L1-503 .. L1-510   v3 standalone medical img    (founder)
L1-511 .. L1-531   v2 PWDR + analytical cores   (founder)
L1-532 .. L1-???   external contributors        (FCFS claim board)
```

**Don't pick your own number.** Open the GitHub claim issue first
(Path B) or use `pwm-node` (Path A) which fetches the next free ID
from chain. Picking your own ID risks:

- **Collision** — two contributors simultaneously claiming "L1-555"
  would both think they own it
- **Sparse numbering** — gaps in the sequence (L1-100, L1-500, L1-9999)
  hide catalog activity and confuse downstream tooling

For L2 and L3 children, **inherit the parent L1's number**:

```
L1-532 → L2-532 + L3-532
```

If a Principle needs multiple Specs (rare), use suffixes: `L2-532a`, `L2-532b`.

---

## Slug naming convention

Every manifest should have a `display_slug` field for human-readable
URLs and grant-doc references:

- **Lowercase, hyphen-separated:** `cassi`, `pillcam-bleeding`, `dual-energy-ct`
- **Common abbreviations preferred** when widely recognized: `qsm`, `mri`, `ecg`, `xrd`
- **Full descriptor** when no abbreviation: `chromatic-confocal`, `bone-fracture-xray`
- **No domain prefix in slug** — domain belongs in the `domain` field
- **Slug uniqueness:** check via `pwm-node match <your-slug>` before claiming

The slug is **off-chain UI metadata only**. It does NOT affect the
on-chain hash of your manifest (`scripts/register_genesis.py` strips
it before keccak256 hashing per the `UI_ONLY_FIELDS` filter).

---

## Manifest schema (minimum required fields)

### L1 example

```json
{
  "artifact_id": "L1-532",
  "layer": "L1",
  "title": "Quantum-Enhanced Radar Imaging",
  "display_slug": "quantum-radar",
  "domain": "applied",
  "spec_range": {
    "allowed_omega_dimensions": ["coherence_time", "snr_db"],
    "omega_bounds": {"coherence_time": [1e-6, 1e-3], "snr_db": [-20, 20]},
    "center_spec": {"forward_operator": "y = entangle(scene) + thermal_noise"}
  },
  "G": {
    "dag": "entangled_source -> beam_splitter -> scene_interaction -> heterodyne_detection",
    "n_c": 0
  },
  "gate_class": "analytical",
  "error_metric": "PSNR_dB",
  "physics_fingerprint": "quantum_radar_v1"
}
```

### L2 example

```json
{
  "artifact_id": "L2-532",
  "layer": "L2",
  "parent_l1": "L1-532",
  "title": "Quantum-Enhanced Radar Imaging — Spec",
  "display_slug": "quantum-radar",
  "spec_type": "mismatch_only",
  "six_tuple": {
    "omega": {"coherence_time": [1e-6, 1e-3], "snr_db": [-20, 20]},
    "E": {"forward": "...", "primitive_chain": "..."},
    "B": {"non_negativity": true},
    "I": {"strategy": "zero_init"},
    "O": ["PSNR_dB", "SSIM"],
    "epsilon_fn": "..."
  },
  "ibenchmark_range": {
    "center_ibenchmark": {"rho": 1, "epsilon": 25.0},
    "tier_bounds": {}
  },
  "d_spec": 0.50,
  "gate_class": "analytical"
}
```

### L3 example

```json
{
  "artifact_id": "L3-532",
  "layer": "L3",
  "parent_l2": "L2-532",
  "parent_l1": "L1-532",
  "title": "Quantum-Enhanced Radar Imaging — P-benchmark",
  "display_slug": "quantum-radar",
  "benchmark_type": "P_benchmark",
  "rho": 50,
  "dataset_registry": {
    "primary": "ChalmersQuantumRadar dataset v1",
    "construction_method": "synthetic + lab-validated",
    "num_dev_instances": 20,
    "holdout_instances": 10,
    "ground_truth_provenance": "ground-truth scenes from MS-COCO crops"
  },
  "ibenchmarks": [
    {
      "tier": "T1_nominal",
      "rho": 1,
      "omega_tier": {"coherence_time": 1e-4, "snr_db": 0},
      "epsilon": 25.0,
      "quality_thresholds": [
        {"Q": 0.55, "tier": "Standard"},
        {"Q": 0.75, "tier": "Strong"},
        {"Q": 0.90, "tier": "Excellent"}
      ],
      "baselines": [
        {"name": "matched-filter", "metric": "PSNR_dB", "score": 18.5, "Q": 0.40}
      ]
    }
  ],
  "scoring": {
    "primary_metric": "PSNR_dB",
    "secondary_metric": "SSIM"
  },
  "anti_overfitting_mechanisms": {
    "M1_random_instantiation": "G(SHA256(h_sub)) seeds the entanglement coherence noise",
    "M2_convergence_check": "PSNR(h/2) - PSNR(h) → 0 as h → 0",
    "M3_cross_instance_worst_case": "stratified worst-case across 4 SNR strata",
    "M4_adversarial_instances": "community-submitted edge cases via GitHub PR",
    "M5_method_signature_diversity": "novelty multiplier on unseen primitive signatures",
    "M6_s1_s4_gates": "per-instance S1-S4 harness in tests/"
  },
  "hardness_rule_check": "no expert baseline passes ε=25.0 dB across all SNR < -10",
  "gate_class": "analytical"
}
```

Full reference for all fields in the existing 531 manifests under
`pwm-team/pwm_product/genesis/l{1,2,3}/` and
`pwm-team/content/agent-*/principles/...`.

---

## PR body template (for Path B)

```markdown
## Summary

Adds L1-XXX <slug>: brief one-line description of the Principle.

- **Domain:** <e.g., compressive_imaging / medical_imaging / signal_processing>
- **Forward model:** <one-line summary of E>
- **Gate class:** <analytical / physical_with_discrete_readout / data_driven_statistical>
- **L_DAG:** <complexity score (V-1 + log10(κ/κ_0) + n_c)>
- **Distinctness:** Jaccard ≥ 0.30 from L1-NNN <closest-slug> (cite the closest)

## Files

- L1-XXX_<slug>.json (Principle)
- L2-XXX_<slug>.json (Spec)
- L3-XXX_<slug>.json (P-benchmark)

## Acceptance evidence

- [ ] S1 (dimensional consistency): <proof or link to derivation>
- [ ] S2 (well-posedness): <regime statement + reference>
- [ ] S3 (convergent solver class): <name + convergence rate>
- [ ] S4 (hardness rule): <proof no expert baseline passes ε everywhere>
- [ ] Cross-domain Jaccard ≥ 0.30 from closest existing entry (cited above)

## Reference solver (optional but recommended)

A weak reference solver at
`pwm-team/pwm_product/reference_solvers/<slug>/<slug>_<method>.py`
demonstrates the protocol works end-to-end. Doesn't need to be SOTA —
the deliberately-weak reference is the floor everyone competes against.

## Testing

- [ ] Manifest JSONs parse cleanly
- [ ] `python3 scripts/register_genesis.py --manifest L1-XXX_<slug>.json --layer L1 --dry-run`
      produces the expected hash
- [ ] If reference solver included: it runs end-to-end on the dataset

🤖 Generated with [Claude Code](https://claude.com/claude-code) (or
not — this template is for any contributor)
```

---

## Anti-patterns to avoid

| ❌ Don't | ✅ Do instead |
|---|---|
| Pick your own L1 number | Open a claim issue or use `pwm-node` to fetch the next free ID |
| Use uppercase or special chars in slug | Lowercase + hyphen-separated only (`pillcam-bleeding`, not `PillCam_Bleeding`) |
| Author L1 only and skip L2/L3 | All three layers required for a complete contribution; partial submissions get rejected |
| Pin manifest CIDs but never register on chain | The chain is the source of truth; off-chain manifests aren't discoverable |
| Submit a Principle that's near-duplicate of existing | Run cross-domain Jaccard check first; if d < 0.30, your work won't be approved |
| Set `display_slug` to a value already used | Slugs must be unique within a layer; check via `pwm-node match` |
| Add `display_slug` and re-register an already-registered manifest | The hash filter handles this — but DON'T re-register; just update the JSON in your PR |

---

## What happens after your PR merges

1. **Manifest registered on-chain** — `agent-coord` runs
   `scripts/register_genesis.py` against your new manifests on the
   next genesis-extension event
2. **Explorer indexes your Principle** — appears at
   `https://explorer.pwm.platformai.org/principles/L1-XXX` and
   `/benchmarks/L3-XXX` (and `/<slug>`)
3. **Bounty #7 Tier B claim opens** — the FCFS claims board at
   `interfaces/bounties/07-claims.md` accepts the next-step claim
4. **External miners can submit L4 certs** against your L3 benchmark —
   each cert hash references your benchmark hash on-chain
5. **First external L4 cert** triggers your Tier B payout
   (~2,000 PWM, currently testnet PWM; mainnet PWM at launch)

---

## Cross-references

- `pwm-team/customer_guide/PWM_PRINCIPLES_SPECS_BENCHMARKS_SOLUTIONS_GUIDE_2026-05-03.md` — full L1/L2/L3/L4 reference (consumer + producer flows)
- `pwm-team/coordination/PWM_HUMAN_READABLE_IDS_AND_CONTRIBUTION_FLOW_2026-05-03.md` — design rationale for slugs + claim-board
- `pwm-team/bounties/07-genesis-principle-polish.md` — Bounty #7 spec
- `pwm-team/bounties/07-claims.md` — FCFS claim board
- `scripts/register_genesis.py` — canonical on-chain registration script
- `scripts/test_register_genesis.py` — hash-invariance tests
- `scripts/add_display_slugs.py` — bulk slug generator
- `https://explorer.pwm.platformai.org/principles` — browse all 531+ existing Principles before contributing

---

## Questions

Open a GitHub Discussion in `integritynoble/pwm-public` under the
`contribute` category. agent-coord triages within ~72h.

If your contribution is for a domain not currently well-represented
(e.g., neuroscience, oceanography, materials at extreme conditions),
flag that in your claim issue — agent-coord may grant priority review.
