# L2 Spec Restriction via Optical Elements — Design Discussion

**Date:** 2026-05-02
**Status:** Design discussion — Director consideration pending
**Affects:** `pwm_overview1.md` § L2 spec schema, all L2 specs in genesis catalog
**Owner:** agent-coord
**Related:** `pwm_overview1.md` (L2 six-tuple definition), `reports/cassi.md` (descriptive element table that motivated this), `papers/Proof-of-Solution/mine_example/science/B_compressive_imaging/025_cassi.md`

## Question (Director, 2026-05-02)

> "For pwm_overview1.md / spec.md, is it better to add the optical
> elements to restrict the benchmarks?"

## Short answer

**Yes — but only for the `analytical` gate class (CASSI / CACTI / QSM-style),
and as a "≥ this subrole set" minimum-required constraint rather than an
exact-list match.**

The optical-element table already exists in `reports/cassi.md` (source →
mask → disperser → integrator → PSF → sensor → noise, with subroles +
mismatch bounds) — it is currently *descriptive*. Lifting it into L2's
`six_tuple.E` as a normative `required_elements: [{subrole, mismatch_axes}]`
field promotes it from documentation to enforceable spec.

## Four wins from making it normative

1. **Spec compliance becomes mechanical.** An L4 solver claiming CASSI
   must instantiate every required subrole; missing the disperser →
   automatic spec-fail by the verifier-agent. No subjective review needed.

2. **Aligns with what `omega_bounds` already encodes.** The mismatch axes
   (mask_dx, mask_dy, mask_theta, disp_a1, disp_a2, disp_alpha, psf_sigma,
   etc.) are *per-element* knobs, so an explicit element list makes the
   Ω parameterization explicit instead of implicit. Today, a reader has
   to reverse-engineer which axis attaches to which element from naming
   convention only.

3. **L_DAG complexity score stays consistent.** `|V| - 1` in the
   `L_DAG = (|V|-1) + log10(κ/κ_0) + n_c` formula is the number of
   elements in the DAG. Making the element list normative locks the
   score against drift — anyone editing the spec must also re-derive
   L_DAG, which the verifier can check.

4. **Anti-gaming for Bounty #5 / #8.** Without it, a third-party submission
   can claim "CASSI solver" while quietly skipping dispersion modeling
   (e.g., reducing CASSI to plain compressive imaging). Reviewers would
   have to catch this subjectively. With normative elements, the harness
   rejects it at scope-check.

## Tradeoffs and constraints

### DO use `min_required_subroles: [...]`, NOT exact-match

Future submissions may legitimately add nodes the original spec author
didn't include — chromatic aberration, polarization rotation, quantum
efficiency drift, etc. An exact-match list ossifies the spec; a minimum
set keeps the spec future-proof.

```jsonc
// L2-CASSI six_tuple.E proposed shape
{
  "forward_operator": "y = sum_l(shift(warp(Mask) * x, ...))",
  "min_required_subroles": [
    {"subrole": "encoding/mask_transform",       "mismatch_axes": ["mask_dx", "mask_dy", "mask_theta"]},
    {"subrole": "encoding/parametric_dispersion", "mismatch_axes": ["disp_a1", "disp_a2", "disp_alpha"]},
    {"subrole": "encoding/frame_integration",    "mismatch_axes": []},
    {"subrole": "transport/psf_blur",            "mismatch_axes": ["psf_sigma"]},
    {"subrole": "sensor/photon_sensor",          "mismatch_axes": ["qe_drift", "gain"]},
    {"subrole": "noise/poisson_read_sensor",     "mismatch_axes": []}
  ]
}
```

A submission may add a 7th element (e.g., chromatic aberration) — that's
still spec-compliant, because the requirement is *minimum*, not
*exact*. The added element introduces new ω axes; those must be
declared in the submission's manifest.

### DON'T impose on `physical_with_discrete_readout` (PWDR) class

For L1-512..L1-531 (chest CT severity, dermoscopy, ECG arrhythmia, etc.)
the discriminator is **clinical readout**, not the optical chain. The
relevant constraint is "the readout must conform to ETDRS / CO-RADS /
AAMI" — which is a *labeling protocol*, not a physics-element list.
Forcing PWDR L2 specs to enumerate optical elements would:

- Add ~6-10 lines per L2 of irrelevant boilerplate
- Imply restrictions that don't actually apply (a chest CT solver
  doesn't care which X-ray tube spectrum was used as long as the
  CO-RADS readout is the same)
- Conflate the science (reading the image) with the pre-imaging chain
  (acquiring the image)

So: **analytical class gets `min_required_subroles` field; PWDR class
does not.** `data_driven_statistical` class also does not.

### v3 standalone multi-physics: list-of-lists shape

For L1-503..L1-510 (QSM, qPAT, PK-PET, HP-13C MRI, MEG/EEG joint, OCE,
PAUS, cardiac 4D-flow biomech), the DAG can have multiple parallel
physics chains. The schema needs to express "this multi-physics solver
must satisfy *each* sub-chain's element minimum."

```jsonc
// L2-507 MEG/EEG joint six_tuple.E proposed shape
{
  "forward_operator": "joint_meg_eeg(x_brain) -> (y_meg, y_eeg)",
  "physics_chains": [
    {
      "chain_id": "meg",
      "min_required_subroles": [
        {"subrole": "biot_savart_integration",  "mismatch_axes": ["sensor_position_drift"]},
        {"subrole": "squid_sensor",             "mismatch_axes": ["sensor_gain"]},
        {"subrole": "thermal_noise",            "mismatch_axes": []}
      ]
    },
    {
      "chain_id": "eeg",
      "min_required_subroles": [
        {"subrole": "volume_conduction_lead_field", "mismatch_axes": ["scalp_conductivity"]},
        {"subrole": "electrode_sensor",             "mismatch_axes": ["impedance_drift"]},
        {"subrole": "drift_noise",                  "mismatch_axes": []}
      ]
    }
  ],
  "n_c_coupling_constraints": 2,
  "coupling_constraint_description": "shared brain-source orientation; shared time-gating"
}
```

Authorable, but adds a schema field. `n_c` aligns with the existing
`L_DAG` formula's coupling-constraint term.

## Authoring cost

- ~60 analytical L2 specs in v1 baseline + 8 v3 standalones + 2 newly-
  authored analytical cores = ~70 specs need element-list retrofitting.
- Per-spec authoring time: ~20-40 min (the table already exists in the
  reference impl reports for ~25% of these; the rest needs hand-curation
  from the L1's DAG primitive chain field).
- Total: roughly 25-45 hours of focused work — **post-mainnet Bounty #7
  Tier B work**, not pre-mainnet.

The 19 PWDR specs and 0 DDS specs are unaffected.

## Two-Principle exemplar proposal

If Director approves the design direction, agent-coord can land a
**two-Principle exemplar** before broad rollout:

1. **L2-CASSI** (`pwm_product/genesis/l2/L2-CASSI*.json`) — lift the
   existing element table from `reports/cassi.md` into the new schema
   field. ~15 min (just transcription).

2. **L2-503 QSM** (`pwm-team/content/agent-imaging/principles/C_medical_imaging/L2-503_qsm.json`)
   — full hand-author the element list from QSM physics: dipole-kernel
   convolution → field-map unwrapping → background-field removal →
   inverse dipole solve. Currently a skeleton; this would convert the
   skeleton stub for `min_required_subroles` into the first authored
   instance. ~30 min.

The exemplar lets Director see two sides — a transcription job (CASSI:
table already exists) vs. a hand-author job (QSM: element list synthesized
from physics) — before committing to retrofit ~70 specs.

## Decision points for Director

| Decision | Default if no answer | Impact |
|---|---|---|
| **D1.** Adopt `min_required_subroles` field for analytical L2? | Status quo (descriptive only) | Anti-gaming for Bounty #5/#8 |
| **D2.** Apply only to analytical class, not PWDR/DDS? | Apply only to analytical | Avoids irrelevant boilerplate |
| **D3.** Use minimum-set semantics, not exact-list? | Use minimum-set | Future-proofs against new physics |
| **D4.** Land two-Principle exemplar (CASSI + L2-503 QSM) before broad rollout? | Yes | ~45 min of work; gives Director concrete artifacts to evaluate |
| **D5.** Schedule broad retrofit pre- or post-mainnet? | Post-mainnet (Bounty #7 Tier B) | 25-45 hours of work; doesn't block deploy |

## Suggested next step

If Director nods, agent-coord lands the **two-Principle exemplar** as a
single PR, plus a `pwm_overview1.md` § L2 schema patch describing the
new field. This is concrete, reversible, and ~45 min of work. Director
reviews the two artifacts before signing off on the broader retrofit.

If Director defers, no action needed — the design discussion is recorded
here for post-mainnet pickup.

## Cross-references

- `pwm_overview1.md` — L2 six-tuple definition (Ω, E, B, I, O, ε)
- `reports/cassi.md` — pre-existing descriptive element table (motivates lifting to normative)
- `papers/Proof-of-Solution/mine_example/science/B_compressive_imaging/025_cassi.md` — reference Principle that already lists elements
- `pwm-team/coordination/PWM_PART1_C1_STATUS.md` — status of L2/L3 skeletons for the 29 v2/v3 anchors (these would be candidates for retrofitting)
- `pwm-team/pwm_product/genesis/PWM_GATE_CLASSES_AND_SCALING.md` — gate-class taxonomy (analytical / PWDR / DDS) that scopes which L2 specs get the new field
- `pwm-team/coordination/agent-coord/interfaces/bounties/05-contracts-competing.md`, `08-llm-matcher.md` — bounties that benefit most from anti-gaming via normative element lists
