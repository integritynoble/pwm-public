# PWM Genesis Principle — Four-Layer Walkthrough Template

**Authoritative for all 501 non-pilot principles.** This template is the
section skeleton extracted from `cassi.md`. Every principle file in `science/`
MUST contain every H2 and every H3 listed below, in the order given. A
section that genuinely does not apply to a given principle is replaced by
the **N/A stub** (see `STYLE_NOTES.md §8`), not silently skipped.

Canonical filled example: `A_microscopy/001_widefield_fluorescence.md`
(the pilot). Read it first; it resolves ambiguities that this template alone
cannot.

---

## 1. Top-matter

Every file begins with this exact frame:

```markdown
# {{PrincipleName}} — Complete Four-Layer Walkthrough

**Principle #{{N}}: {{Full Name}}**
Domain: {{Domain}} | Difficulty: {{Tier}} (delta={{δ}}) | Carrier: {{Carrier}}

---
```

Placeholder meanings:
- `{{PrincipleName}}` — short title (e.g. "Widefield Fluorescence Microscopy", "CASSI").
- `{{N}}` — integer principle ID, same as the filename prefix.
- `{{Full Name}}` — the long-form name if different from the short title; else repeat the short title.
- `{{Domain}}` — the domain cluster (e.g. Microscopy, Compressive Imaging).
- `{{Tier}}` — one of: `Textbook`, `Standard`, `Advanced`, `Research`, `Frontier`.
- `{{δ}}` — integer 1-5 matching the tier.
- `{{Carrier}}` — Photon, Electron, Phonon, Field, Particle, etc.

## 2. Mandatory section tree

Every H2 and H3 below is mandatory. Ordering is fixed.

```
## The Four-Layer Pipeline for {{PrincipleShortName}}
    (ASCII diagram L1→L2→L3→L4, cassi lines 10-31 pattern)

## Layer 1: Seeds → Principle (The Physics Foundation)
### What the domain expert writes (seeds)
    (yaml block with omega, E, B, I, O, epsilon — STYLE_NOTES §3)
### What S1-S4 discovers (the Principle)
    (ASCII box for P = (E, G, W, C), STYLE_NOTES §1 widths)
### Physics fingerprint
### Spec range declaration
### What S1-S4 checks at Layer 1
### Layer 1 reward
### The Principle is now immutable

## Layer 2: Principle + S1-S4 → spec.md (Task Design)
### Who does this?
### What the task designer writes
    (full spec.md yaml — all tiers T1..T4, plus oracle-assisted tier, plus P-benchmark)
### Spec distance and duplicate prevention
### What S1-S4 checks at Layer 2
### Layer 2 reward
### The spec.md is now immutable

## Layer 3: spec.md + Principle + S1-S4 → Benchmark (Data + Baselines)
### Who does this?
### P-benchmark vs. I-benchmark
### ibenchmark_range (declared inside the spec, repeated here for reference)
### What the benchmark builder creates
    (dataset manifest yaml, baseline solver table, quality_scoring ladder)
### What S1-S4 checks at Layer 3
### Layer 3 reward
### The benchmark is now immutable

## Layer 4: spec.md + Benchmark + Principle + S1-S4 → Solution (Mining for PWM)
### Who does this?
### Step-by-step mining
    (ONE solver end-to-end, numeric walk-through ending in certificate JSON)
### Cross-benchmark claims (P-benchmark bonus)

## Complete Hash Chain (Immutability Across All Four Layers)
    (ASCII diagram h_p → h_s → h_b → h_cert)

## I-Benchmark Tiers — Detailed Mining Guide
### Mismatch-Only Spec: Tier T1 (Nominal — Start Here)
### Mismatch-Only Spec: Tiers T2 / T3 (Low / Moderate Mismatch)
### Mismatch-Only Spec: Tier T4 (Blind Calibration — Highest I-benchmark ρ)
### Oracle-Assisted Spec: Tier T1 (Moderate Mismatch + Oracle — center I-bench)
### Mismatch Recovery by Solver
### P-benchmark (Highest Reward Overall, ρ=50)

## Complete Reward Summary (All Four Layers for {{PrincipleShortName}})

## Mining Strategies
### Recommended progression

## What You Cannot Do

## Quick-Start Commands

## Reference
```

## 3. Fill-in rules (per section)

### Layer 1

- **What the domain expert writes (seeds).** YAML per STYLE_NOTES §3 order.
  Concrete ranges, not descriptions. Fields must be physical quantities
  with units.
- **What S1-S4 discovers (the Principle).** The P = (E,G,W,C) ASCII box.
  Four cells, in order: forward model in closed form → DAG decomposition
  with node semantics block → well-posedness certificate with
  existence/uniqueness/stability triple → metrics/convergence/witness set.
- **Physics fingerprint.** Four lines, no prose: forward model, DAG signature,
  carrier, difficulty tier. Pattern: cassi lines 222-240.
- **Spec range declaration.** Table parameter → range → units → notes,
  covering every Ω dimension the principle owns. Split into Ω-as-spec and
  Ω-as-mismatch dimensions.
- **What S1-S4 checks at Layer 1.** Markdown table `| Gate | Check | Result |`.
  All four gates, PASS or FAIL with one-line justification.
- **Layer 1 reward.** Formula + numeric per STYLE_NOTES §4.
  `R_L1 = 200 × φ(t) × δ` is the canonical base; principles diverge only if
  δ ≠ 1.
- **The Principle is now immutable.** One paragraph on hash-freezing.

### Layer 2

- **Who does this?** 1-2 paragraphs identifying the task designer role.
- **What the task designer writes.** Full yaml spec with ALL of:
  `principle_ref`, `omega`, `E`, `I`, `O`, `epsilon`, `tiers`. Every tier
  block (T1_nominal, T2, T3, T4_blind, T1_oracle, P_benchmark) must have
  `description`, `mismatch` (if applicable), `expected_metric`, `reward_rho`.
  No empty tier blocks.
- **Spec distance and duplicate prevention.** Define a distance function
  over Ω; state the duplicate threshold; include 2 worked examples
  (one reject, one accept). Pattern: cassi lines 533-695.
- **What S1-S4 checks at Layer 2.** Markdown table, 4 rows.
- **Layer 2 reward.** `R_L2 = 150 × φ(t) × 0.70 + 15% upstream → L1 author`.
- **Immutability.** One paragraph.

### Layer 3

- **Who does this?** 1-2 paragraphs identifying the benchmark builder role.
- **P-benchmark vs. I-benchmark.** Side-by-side definition + when a miner
  picks one over the other.
- **ibenchmark_range.** Compact repeat of the Ω ranges from the spec, for
  Layer-3 reader convenience.
- **What the benchmark builder creates.** Three artifacts: dataset manifest
  yaml with `data_hash`, baseline solver table per STYLE_NOTES §5
  (≥3 solvers: classical, iterative, learned), quality_scoring ladder
  (≥4 PSNR→Q thresholds).
- **What S1-S4 checks at Layer 3.** Markdown table, 4 rows.
- **Layer 3 reward.** `R_L3 = 100 × φ(t) × 0.60 + 15% upstream split 5/10`.
- **Immutability.** One paragraph.

### Layer 4

- **Who does this?** Role table: SP / CP / Validator / Reviewer.
- **Step-by-step mining.** ONE solver, numeric walk-through, 6-10 numbered
  steps ending in a certificate JSON snippet per STYLE_NOTES §6.
- **Cross-benchmark claims.** Short paragraph on the P-benchmark ρ=50
  multiplier + one worked example of cross-tier generalization.

### Back-half sections

- **Complete Hash Chain.** ASCII diagram showing `h_p → h_s → h_b → h_cert`
  with each dependency labeled. Pattern: cassi lines 1339-1361.
- **I-Benchmark Tiers.** Six subsections, each a paragraph + one numeric
  example. Include a solver-vs-tier recovery table (Mismatch Recovery by
  Solver subsection).
- **Complete Reward Summary.** Markdown table, one row per layer, with both
  seed reward and ongoing royalty share per STYLE_NOTES §4.
- **Mining Strategies → Recommended progression.** Numbered list, principle-
  specific. "Start at T1 with solver X, progress to T4 with solver Y."
- **What You Cannot Do.** Registry-level constraints, 8-10 bullets.
  Boilerplate; copy from cassi lines 1518-1529 without principle-specific
  changes.
- **Quick-Start Commands.** 4-5 `pwm-node` CLI lines, following cassi lines
  1531-1572 pattern.
- **Reference.** Citations to: primitive notation (`primitives.md`), condition
  number conventions (`condition_number.md`), P-benchmark scoring
  (`pbenchmark_scoring.md`), the principle's domain references (papers, DOIs).

## 4. N/A stub pattern

See `STYLE_NOTES.md §8`. Exact wording:

```
**N/A for this principle** — reason: {{one-line explanation}}.
```

The H2/H3 heading stays; only the content is replaced by the stub.

## 5. Example of a filled template

See `A_microscopy/001_widefield_fluorescence.md` for the canonical
filled example. When this template and the pilot disagree, the pilot wins —
update this template to match.
