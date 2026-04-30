# v1 Principle removal candidates — pre-mainnet review (2026-04-30)

**Date:** 2026-04-30
**Owner:** Director (per-Principle approval required)
**Audience:** Director + agent-coord
**Status:** Framework + first 15 specific candidates. Director approves/rejects per Principle.

---

## TL;DR

Director's 2026-04-30 permission allows removing weaker v1 baseline Principles from the genesis batch to make room for the v2/v3 expansion (28 new anchors). This doc:

1. Surveys the 502 v1 baseline manifests for removal candidates by category
2. Proposes 15 specific candidates (by L1 ID, with rationale per category)
3. Defines the per-Principle approval workflow

**Headline:** **139 of the 502 v1 manifests** carry the source-data-quality note `"Source MD is widefield-fluorescence template (fan-out artifact). Physics below is grounded in canonical medical-imaging literature for this principle."` — meaning the source MD was generated from a widefield-fluorescence template and retrofitted to other physics. These are the strongest removal candidates: low-cost to remove (no L4 mining activity yet on Sepolia for any of them) and they free up genesis namespace for the v2/v3 expansion plus future Bounty #7 polish.

**No removal happens without per-Principle Director sign-off.** This doc is a candidate list, not an authorization.

---

## Removal-candidate categories

| Category | Count | Strength of removal case | Notes |
|---|---|---|---|
| **A.** Manifests with "widefield-template fan-out artifact" source-quality note | **139** | Strong | Source MD was retrofitted; physics may not match the widefield-template scaffolding it inherited |
| **B.** Niche modalities with no clear clinical / industrial deployment | TBD (~30-50 estimated) | Moderate | Worth keeping a few as long-tail Bounty #7 candidates; remove the lowest-impact ones |
| **C.** Principles superseded by newer authoring (2026-04-30 v2/v3) | TBD (~5-10 estimated) | Weak | Most overlaps are already at d_principle ≥ 0.30 (passing v1 advisory) |
| **D.** Principles with placeholder physics that don't validate S1-S4 cleanly | TBD | Strong | Run the auto-verifier (post-v3-deploy) to identify mechanically; pre-v3, identify by manual review |

**Total likely removal candidates: ~150-200** (most overlap between A and B).

After removal, expected genesis state:

```
Before removal:    531 L1 manifests
After 150 removed: 381 L1 manifests
   = 28 v2/v3 anchors authored 2026-04-30 (kept)
   + 353 v1 baseline retained (502 − ~150 weakest)
```

This still gives PWM a meaningful 380-Principle genesis, with much higher quality density: every retained manifest has either (a) been authored at v2/v3 schema depth in 2026-04-30 OR (b) survived the removal cull as a domain-significant v1 Principle.

---

## Category A — widefield-template fan-out artifacts (139 manifests)

These all carry the source-quality note `"Source MD is widefield-fluorescence template (fan-out artifact). Physics below is grounded in canonical medical-imaging literature for this principle."`

The note is honest — physics WAS grounded in literature post-fan-out — but the manifest's narrative voice and structural choices inherit from widefield-fluorescence. For Principles whose actual physics is far from widefield (e.g., X-ray, MRI, ultrasound), the retrofit may not be coherent.

**Recommended removal triage for Category A (Director approves per row):**

1. **Keep all imaging Principles whose modality is near widefield optical** (livecell microscopy, super-resolution, FLIM, two-photon, structured illumination) — the retrofit is small here.
2. **Remove the manifests that retrofitted to non-optical modalities** (e.g., a widefield template wrapped around X-ray transmission physics). These have the highest narrative-physics mismatch.
3. **Keep Principles that already have a v2/v3 sibling under physics_core_principle** — they're the foundation for new PWDR work and shouldn't be removed.

Sample of Category A manifests across imaging subdomains (139 total; first 10 listed):

```
pwm-team/content/agent-imaging/principles/A_microscopy/L1-002_lowdose_widefield.json
                                                ...    /L1-003_confocal_livecell.json   (also: artifact_id collision per separate doc)
                                                ...    /L1-004_confocal_zstack.json     (also: artifact_id collision per separate doc)
                                                ...    /L1-005_sim.json
                                                ...    /L1-006_lsfm.json
                                                ...    /L1-007_flim.json
                                                ...    /L1-008_fpm.json
                                                ...    /L1-009_twophoton.json
                                                ...    /L1-010_sted.json
                                                ...    /L1-011_palm_storm.json
```

Full list available via:
```bash
grep -lE "Source MD is widefield-fluorescence template" pwm-team/content/agent-imaging/principles/*/L1-*.json
```

---

## Category B — niche modalities with no clear clinical deployment

Examples Director should consider (not yet enumerated; awaits Director priority signal):

- Highly-specialized research-tool imaging methods that haven't seen FDA approval or routine clinical use
- Industrial-inspection methods that overlap with nearby Principles
- Astronomy methods that lack a clear data-availability story
- Petroleum / geology methods that are domain-niche and unlikely to attract miners

CPU agent can produce a ranked Category B list with rationale per Principle if Director wants — ~1 day of analysis. For now, candidate count is estimated at ~30-50.

---

## Category C — superseded by 2026-04-30 v2/v3 authoring

Most v2/v3 anchors authored 2026-04-30 PASS the d_principle ≥ 0.30 distinctness advisory vs their closest existing v1 baseline (per the `distinctness_audit` field in each manifest's `v3_metadata` block). So Category C is small.

Possible candidates:
- L1-041 PAT (acoustic-only photoacoustic) — the new L1-504 qPAT (joint optical+thermoelastic+acoustic) doesn't supersede it (d_principle = 0.42) but it's a weaker Principle than its v3 sibling. **Recommendation: keep.**
- L1-059 SWI — d_principle ≈ 0.50 from L1-503 QSM. **Recommendation: keep** (SWI is clinically distinct from QSM).
- L1-055 MRE (MR phase only, Helmholtz-as-post-step) — could be merged with a future joint MRE multi-physics Principle. **Recommendation: keep** until the joint MRE is authored.

**Net Category C removals: 0-2 likely.**

---

## Category D — placeholder physics that doesn't validate

Pre-v3 (no auto-verifier), this requires manual review. The verifier-agent triple-review process from `MVP_FIRST_STRATEGY.md` Phase A would catch these, but it's only been run on CASSI + CACTI (#003 + #004 demos).

CPU agent can run a static lint pass: check that `E.forward_model` is non-empty, that `physics_fingerprint.primitives` matches `G.vertices`, that `s1_s4_gates` are all PASS, that `condition_number_kappa` is non-zero, etc. ~0.5 day of CPU work for a static lint script that flags suspicious manifests.

---

## First 15 specific removal candidates

Director can approve/reject any subset. Removing all 15 takes the genesis from 531 → 516; the v2/v3 anchor set is unchanged.

| # | L1 ID | File | Category | Rationale |
|---|---|---|---|---|
| 1 | L1-002 | `agent-imaging/A_microscopy/L1-002_lowdose_widefield.json` | A + B | Widefield template; lowdose is a parameter regime, not a distinct Principle. The base L1-001 widefield Principle (if it exists) covers the physics. |
| 2 | L1-005 | `agent-imaging/A_microscopy/L1-005_sim.json` | A | Widefield-template retrofit; SIM (Structured Illumination Microscopy) physics is well-defined but the manifest is a fan-out artifact. Future re-authoring as v2 PWDR is the right path. |
| 3 | L1-007 | `agent-imaging/A_microscopy/L1-007_flim.json` | A | FLIM (Fluorescence Lifetime Imaging Microscopy) — narrow research tool; not FDA-cleared; widefield-template retrofit. |
| 4 | L1-009 | `agent-imaging/A_microscopy/L1-009_twophoton.json` | A | Two-photon microscopy widefield-template retrofit; physics is established but the manifest narrative inherits from widefield. |
| 5 | L1-013 | `agent-imaging/A_microscopy/L1-013_polarization.json` | A | Polarization microscopy widefield-template retrofit; niche imaging tool. |
| 6 | L1-019 | `agent-imaging/A_microscopy/L1-019_*.json` | A + B | (Subject to Director's pick — provided as placeholder for Director's domain knowledge) |
| 7 | L1-094 | `agent-imaging/H_depth_imaging/L1-094_*.json` | A + B | Depth imaging variant overlap — H_depth_imaging has 5 entries; one or two are likely candidates. |
| 8 | L1-119 | `agent-imaging/J_industrial_inspect/L1-119_*.json` | A + B | Industrial-inspection variant overlap. |
| 9 | L1-148 | `agent-signal/AD_signal_processing/L1-148_mass_spectrometry_isotope.json` | A + B | Niche signal-processing variant; not a high-impact Principle. |
| 10 | L1-152 | (subject to Director's audit) | A + B | TBD per Director priority |
| 11 | L1-185 | `agent-physics/R_fluid_dynamics/L1-185_*.json` | A + B | Fluid-dynamics variant where existing L1-170 incompressible NS + L1-181 shallow water cover the operational range. |
| 12 | L1-225 | `agent-physics/T_structural_mechanics/L1-225_*.json` | B | Structural-mechanics variant overlap. |
| 13 | L1-352 | `agent-physics/AA_plasma_physics/L1-352_*.json` | B | Plasma-physics variant overlap. |
| 14 | L1-440 | `agent-applied/AH_comp_finance/L1-440_*.json` | B | Computational-finance Principle — far from PWM's physics-grounded core; unlikely to attract miners; weak fit for genesis. |
| 15 | L1-470 | `agent-applied/AK_geodesy/L1-470_photogrammetry_structure_from_motion.json` | B | Photogrammetry — niche industrial tool; n_c=1 implicit multi-physics but low clinical impact. |

These 15 are illustrative — Director can substitute any of L1-001..L1-502 based on:

- Domain knowledge (which Principles really matter for PWM's launch story)
- Clinical / industrial impact (FDA-cleared, MQSA-mandated, etc.)
- Whether the Principle has any L4 mining activity on Sepolia (none of the v1 baseline does, per `count_external_l4.py` baseline)

---

## Per-Principle approval workflow

1. **Director reviews this doc + the full Category A list** (139 manifests via the `grep` command above).
2. **Director writes a `PWM_V1_REMOVAL_APPROVED.md` decision file** in `pwm-team/pwm_product/genesis/` with the approved L1 IDs (e.g., a YAML list).
3. **CPU agent executes the removal:**
   - Move approved manifests to `pwm-team/pwm_product/genesis/_removed_2026-04-30/` (preserve for archival; don't `rm` outright)
   - Update the `register_genesis.py` discovery to exclude `_removed_*/` paths
   - Re-run `count_registered_principles.py --no-rpc` to confirm the new count (e.g., 531 - 15 = 516 if 15 removals)
   - Commit + push with a single batch commit message
4. **Verify on-chain:** if Step 9b has not yet fired, the removals affect what gets registered. If Step 9b has already fired (post-mainnet-day), removals require an off-chain catalog update only — on-chain artifacts are immutable.

**Recommendation: do removals BEFORE Step 9b.** The pre-mainnet window is the only chance to clean the namespace.

---

## What removal does NOT do

- ❌ Affect v1 contract bytecode — `mainnet-v1.0.0` tag is unchanged; PWMRegistry doesn't care which manifests we hand it
- ❌ Affect the 28 new v2/v3 anchors — they're untouched in any removal scenario
- ❌ Affect the demo CASSI/CACTI L1/L2/L3 — they're in `pwm-team/pwm_product/genesis/{l1,l2,l3}/`, separate from the content tree (and CASSI/CACTI are themselves v2/v3-aware after the 2026-04-29 migration applied to content-tree L1-003/L1-004 — though those collide in artifact_id with the demo files; see `pwm-team/coordination/REGISTER_GENESIS_ARTIFACT_ID_COLLISION_2026-04-30.md`)
- ❌ Trigger any external-link breakage — none of the candidate manifests are referenced by external URLs (the 30-link audit comes back empty)

---

## Decision log

| Date | Decision |
|---|---|
| 2026-04-30 | This candidate framework + first 15 specific candidates authored per Director's 2026-04-30 permission to remove v1 manifests. Awaiting Director's per-Principle approval. |
| _TBD_ | Director publishes `PWM_V1_REMOVAL_APPROVED.md` with approved L1 IDs |
| _TBD_ | CPU executes removals; commits batch removal |
| _TBD_ | `count_registered_principles.py --no-rpc` confirms new genesis count |

---

## Cross-references

- `pwm-team/coordination/MAINNET_BLOCKERS_2026-04-30.md` — C9 task entry in Part 1
- `pwm-team/coordination/MVP_FIRST_STRATEGY.md` § "On Director's 'remove v1 Principles' permission" — original permission grant
- `pwm-team/coordination/REGISTER_GENESIS_ARTIFACT_ID_COLLISION_2026-04-30.md` — separate L1-003/L1-004 collision
- `scripts/count_registered_principles.py` — Step 9b verifier (handles whatever subset gets registered)
- `papers/Proof-of-Solution/mine_example/science/REGISTRY_v3_standalone_multiphysics.md` — list of v2/v3 anchors that must NOT be removed
