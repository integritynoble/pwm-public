# PWM Genesis Principle — Style Invariants

**Authoritative for all 502 files in `science/`.** These conventions are
enforced by the acceptance checks of the cassi-style pilot and are mandatory
for the 5 content-agents executing the domain-cluster fan-out per
`new_impl_plan.md`. Deviations must be justified in writing before merge.

Reference implementation: `cassi.md` at the parent directory. When this doc
and `cassi.md` disagree, `cassi.md` wins — update this doc to match.

---

## 1. ASCII-box conventions

- **P = (E, G, W, C) box width:** 78 columns inside the border (cassi line 86).
- **Border characters:** `┌ ─ ┐ │ ├ ┼ ┤ └ ┘` (U+250C class). No ASCII fallback.
- **Column labels** (`E`, `G`, `W`, `C`) are 2 spaces wide, centered, followed
  by a vertical bar.
- **Multi-line content** inside a cell wraps at column 70; continuation lines
  align under the content of the first line (not under the column label).
- **Pipeline diagrams** (Four-Layer Pipeline, Hash Chain) use the same border
  class and ≤ 78-column width per individual box; multiple boxes side-by-side
  are permitted.

## 2. Mathematical notation

- **Greek letters** in running prose and ASCII boxes use Unicode
  (κ, δ, λ, θ, ε, σ, φ, Σ, Ω, ρ, μ).
  In yaml and code blocks use ASCII (`kappa`, `delta`, `lambda`, …).
- **Operators:** `⊛` for convolution, `·` for pointwise multiply,
  `→` for DAG edges, `∫` for integrate/accumulate (consistent with primitive
  notation in `primitives.md`).
- **Condition-number triple:** every principle MUST report
  `κ_sub ≈ …, κ_sys ≈ …, κ_eff ≈ …` (sub-operator, compound system, and
  effective with regularization). Pattern: cassi lines 194-197.
- **Hash placeholders:** `sha256:<{{name}}_hash>` — always angle brackets,
  always the `{{name}}` convention.
- **DAG signature:** `node1 → node2 → ... → nodeN` on a single line, primitive
  names in `root.sub.subsub` form.

## 3. YAML field order

### Seed yaml (Layer 1 input)

```
omega:       # parameter space
E:           # forward model
B:           # boundary/domain constraints
I:           # implementation/imaging details
O:           # output metrics
epsilon:     # feasibility thresholds
```

### Spec yaml (Layer 2)

```
principle_ref:
omega:
E:
I:
O:
epsilon:
tiers:       # T1, T2, T3, T4 for I-benchmark + oracle tiers + P-benchmark
```

### Benchmark yaml (Layer 3)

```
spec_ref:
principle_ref:
dataset:
baselines:
quality_scoring:
```

Nested dict keys within each top-level block follow cassi precedent; do not
invent new top-level keys without a style-notes amendment.

## 4. Reward formula presentation

Always show the closed-form formula AND the numeric substitution, on two lines:

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × 0.98 = 98 PWM
```

Not just one or the other. The closed form documents the mechanism; the
numeric substitution makes the value concrete for the reader.

## 5. Solver comparison table

Four columns minimum, in this order:

```
| Solver | PSNR / primary-metric | SSIM / secondary-metric | Runtime | Q |
```

At least 3 rows, each representing a different solver class:

- one **classical** (closed-form or direct, e.g. Wiener)
- one **iterative** (e.g. Richardson-Lucy, ADMM, gradient descent)
- one **learned** (e.g. a CARE / Noise2Void / U-Net-type network)

More rows welcome; fewer than 3 is a spec violation.

## 6. Certificate snippet

Always a JSON block with exactly these keys (cassi-derived):

- `h_p` — principle hash
- `h_s` — spec hash
- `h_b` — benchmark hash
- `r` — residual block: `{residual_norm, error_bound, ratio}`
- `c` — convergence block: `{fitted_rate, theoretical_rate, K}`
- `Q` — quality score ∈ [0, 1]
- `gate_verdicts` — `{S1, S2, S3, S4}` each ∈ `{pass, fail}`

Any additional keys go AFTER these seven, not interleaved.

## 7. Principle-file filename convention

Unchanged from current: `{{NNN}}_{{short_slug}}.md` — three-digit zero-padded
principle number + underscore + lowercase slug. All 502 files already follow
this; do not rename.

Example: `001_widefield_fluorescence.md`, `025_cassi.md`, `142_cryoem.md`.

## 8. N/A stub pattern

When a section genuinely does not apply to a given principle, use exactly:

```
**N/A for this principle** — reason: {{one-line explanation}}.
```

Do NOT silently skip the heading. Do NOT write placeholder prose. The stub
preserves the section skeleton for automated validators.

## 9. Draft annotation

Uncertain numerics (κ estimates, PSNR bounds, convergence rates) that the
author cannot derive authoritatively from textbook knowledge should be tagged:

```
⟨draft — needs domain expert review⟩
```

Drafts are permitted in narrative sections (Reference citations, step-by-step
worked examples). Drafts are NOT permitted in the Physics Fingerprint, the
P = (E, G, W, C) box, or the yaml seed — these are the principle's identity
and must be authored confidently.
