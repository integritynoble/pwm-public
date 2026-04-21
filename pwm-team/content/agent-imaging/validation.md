# agent-imaging: Validation Checklist

Run every check below before merging the imaging principles PR. All content agents follow the same L1/L2/L3 structure. Domain-specific values are in the tables below.

> **Schema note.** Field references use the canonical L1 schema from `CLAUDE.md`, with `E`, `G`, `W`, `C` as top-level namespaces on every L1 JSON. L2 follows `S = (Ω, E, B, I, O, ε)` inside a `six_tuple` block. L3 follows the benchmark schema with I-tiers + P-benchmark.

---

## V1 — Domain Coverage

| Domain Folder | Expected Principles | Delivered? |
|---|---:|:---:|
| A_microscopy              | 24 | [ ] |
| B_compressive_imaging     |  5 | [ ] |
| C_medical_imaging         | 41 | [ ] |
| D_coherent_imaging        |  5 | [ ] |
| E_computational_photo     |  5 | [ ] |
| F_computational_optics    |  4 | [ ] |
| G_electron_microscopy     | 11 | [ ] |
| H_depth_imaging           |  5 | [ ] |
| I_remote_sensing          | 11 | [ ] |
| J_industrial_inspect      | 14 | [ ] |
| M_ultrafast_imaging       |  4 | [ ] |
| N_quantum_imaging         |  3 | [ ] |
| O_multimodal_fusion       |  6 | [ ] |
| P_scanning_probe          |  4 | [ ] |
| **Total**                 | **142** | [ ] |

> **Open reconciliation — folder names.** CLAUDE.md assigns truncated folder names for agent-imaging output (`E_computational_photo`, `J_industrial_inspect`), but the corresponding `source/` symlink uses the full names (`E_computational_photography`, `J_industrial_inspection`). Decide which pattern is canonical; if the full name wins, rename the two output folders and update CLAUDE.md + this checklist.
>
> **Open reconciliation — total count.** The `~115` headline in CLAUDE.md under-counts; the explicit `plan.md` table and the source-file count agree at **142**. Use 142.

**Verify folder names:**
```bash
ls pwm-team/content/agent-imaging/principles/ | sort
# Must list exactly the 14 folder names in the table above.
```

---

## V2 — Per-Principle File Structure

For EVERY principle, verify 3 files exist (filenames carry a `_<slug>` suffix):

```
principles/<domain>/L1-NNN_<slug>.json   # Principle
principles/<domain>/L2-NNN_<slug>.json   # Spec
principles/<domain>/L3-NNN_<slug>.json   # Benchmark
```

**Verify:**
```bash
# Count L1/L2/L3 files per domain (run from pwm-team/content/agent-imaging/)
for d in principles/*/; do
  l1=$(ls "$d"L1-*.json 2>/dev/null | wc -l)
  l2=$(ls "$d"L2-*.json 2>/dev/null | wc -l)
  l3=$(ls "$d"L3-*.json 2>/dev/null | wc -l)
  printf "%-45s L1=%d L2=%d L3=%d\n" "$d" "$l1" "$l2" "$l3"
done
# L1 count must equal L2 count must equal L3 count per domain.
```

---

## V3 — L1 Principle JSON (P = (E, G, W, C) Quadruple)

For each `L1-NNN_<slug>.json`, verify:

### Required top-level fields:
- [ ] `artifact_id` — unique identifier (e.g., `"L1-003"`)
- [ ] `layer` — string `"L1"`
- [ ] `principle_number` — sequential string (e.g., `"003"`)
- [ ] `title` — descriptive name
- [ ] `domain` — matches parent folder (e.g., `"Microscopy"`, `"Compressive Imaging"`)
- [ ] `source_file` — reference to `source/<domain>/NNN_<slug>.md`

### P = (E, G, W, C) — all four top-level namespaces must be present:

**E — Forward Model:**
- [ ] `E.description` — plain-English chain-of-physics (multi-sentence)
- [ ] `E.forward_model` — mathematical expression (e.g., `"y = Φx + ε"`)
- [ ] `E.world_state_x` — what's being recovered
- [ ] `E.observation_y` — what's measured
- [ ] `E.physical_parameters_theta` — list of physical constants / system parameters

**G — DAG:**
- [ ] `G.dag` — string form of the operator chain (e.g., `"K.psf.airy -> int.temporal"`)
- [ ] `G.vertices` — list of primitive nodes
- [ ] `G.arcs` — list of directed edges
- [ ] `G.L_DAG` — numeric: `(|V|-1) + log10(κ/κ₀) + n_c`
- [ ] `G.n_c` — integer, coupling constraint count
- [ ] DAG is acyclic (P10 gate)

**W — Well-posedness:**
- [ ] `W.existence` — bool
- [ ] `W.uniqueness` — bool
- [ ] `W.stability` — `"stable" | "conditional" | "unstable"`
- [ ] `W.condition_number_kappa` — numeric (system compound κ)
- [ ] `W.condition_number_effective` — numeric (κ_eff after regularization)
- [ ] `W.regime` — prose describing the stability regime

**C — Convergence / Error:**
- [ ] `C.solver_class` — e.g., `"iterative_proximal"`, `"direct"`, `"MAP"`
- [ ] `C.convergence_rate_q` — default `2.0`
- [ ] `C.error_bound` — expression (e.g., `"||x_hat - x||_2 <= C1·σ/√m + C2·|mismatch|"`)
- [ ] `C.complexity` — Big-O (e.g., `"O(H·W·log(HW))"`)

### Additional required fields:
- [ ] `difficulty_delta` — integer in `{1, 3, 5, 10, 50}` for `{trivial, standard, challenging, hard, frontier}`
- [ ] `difficulty_tier` — matching string
- [ ] `error_metric` — primary metric string (e.g., `"PSNR_dB"`, `"SSIM"`)
- [ ] `error_metric_secondary` — secondary (e.g., `"SAM_deg"` for hyperspectral)
- [ ] `physics_fingerprint` — all 7 subfields present (see V4)
- [ ] `spec_range` — Ω parameter ranges, allowed operators / problem classes
- [ ] `mismatch_parameters` — list (may be empty for oracle specs)
- [ ] `p1_p10_tests` — list of 10 `"PASS"` / `"FAIL"` entries
- [ ] `s1_s4_gates` — list of 4 gate results

**JSON schema validation:**
```python
import json, glob
REQ_TOP = ["artifact_id","layer","principle_number","title","domain","source_file",
           "E","G","W","C","physics_fingerprint","difficulty_delta","difficulty_tier",
           "mismatch_parameters","error_metric","spec_range",
           "p1_p10_tests","s1_s4_gates"]
REQ_E = ["description","forward_model","world_state_x","observation_y","physical_parameters_theta"]
REQ_G = ["dag","vertices","arcs","L_DAG","n_c"]
REQ_W = ["existence","uniqueness","stability","condition_number_kappa","condition_number_effective","regime"]
REQ_C = ["solver_class","convergence_rate_q","error_bound","complexity"]

for f in sorted(glob.glob("principles/*/L1-*.json")):
    data = json.load(open(f))
    assert data["layer"] == "L1",                  f"{f}: wrong layer ({data.get('layer')!r})"
    for k in REQ_TOP: assert k in data,             f"{f}: missing top-level {k}"
    for k in REQ_E:   assert k in data["E"],        f"{f}: missing E.{k}"
    for k in REQ_G:   assert k in data["G"],        f"{f}: missing G.{k}"
    for k in REQ_W:   assert k in data["W"],        f"{f}: missing W.{k}"
    for k in REQ_C:   assert k in data["C"],        f"{f}: missing C.{k}"
    assert data["difficulty_delta"] in (1,3,5,10,50), f"{f}: bad difficulty_delta"
    print(f"OK  {f}")
```

---

## V4 — Physics Fingerprint (7 Fields)

Every L1 must have all 7 subfields inside `physics_fingerprint`:

| Field | Valid Values (imaging) | Present? |
|---|---|:---:|
| `carrier`            | `"photon"`, `"electron"`, `"x_ray"`, `"radio_wave"`, `"acoustic"`, `"spin"`, `"none"` | [ ] |
| `sensing_mechanism`  | `"tomographic"`, `"interferometric"`, `"coded_aperture"`, `"resonant"`, `"spectral"`, … | [ ] |
| `integration_axis`   | `"spectral"`, `"temporal"`, `"spatial"`, `"angular"`, `"axial"`, … | [ ] |
| `problem_class`      | `"linear_inverse"`, `"nonlinear_inverse"`, `"forward"`, `"estimation"` | [ ] |
| `noise_model`        | `"gaussian"`, `"poisson"`, `"shot_poisson"`, `"poisson_gaussian"`, `"speckle"`, `"multiplicative"`, `"asynchronous_event"` | [ ] |
| `solution_space`     | `"2D_spatial"`, `"3D_temporal"`, `"3D_spectral"`, `"4D_BOLD_signal"`, `"complex_2D"`, `"point_list"`, … | [ ] |
| `primitives`         | list of Level-1/Level-2/Level-3 primitives from the 12-root basis | [ ] |

**Verify:**
```python
FINGERPRINT_KEYS = {"carrier","sensing_mechanism","integration_axis",
                    "problem_class","noise_model","solution_space","primitives"}
for f in glob.glob("principles/*/L1-*.json"):
    data = json.load(open(f))
    fp = data.get("physics_fingerprint", {})
    missing = FINGERPRINT_KEYS - set(fp.keys())
    assert not missing, f"{f}: missing fingerprint fields: {missing}"
```

---

## V5 — L2 Spec JSON (S = (Ω, E, B, I, O, ε))

For each `L2-NNN_<slug>.json`:

- [ ] `layer` = `"L2"`
- [ ] `parent_l1` references the corresponding L1 (e.g., `"L1-003"`)
- [ ] `spec_type` is one of `"mismatch_only"` or `"oracle_assisted"`
- [ ] At least 1 spec (2 preferred):
  - Spec 1: mismatch-only (Ω includes uncertain/calibration parameters)
  - Spec 2: oracle-assisted (calibration parameters moved to `true_phi` input)
- [ ] `six_tuple` contains all six components:
  - `six_tuple.omega` — parameter ranges
  - `six_tuple.E` — `{forward, operator, primitive_chain, inverse}`
  - `six_tuple.B` — boundary / prior conditions
  - `six_tuple.I` — init strategy
  - `six_tuple.O` — list of observables
  - `six_tuple.epsilon_fn` — AST-safe Python expression
- [ ] `protocol_fields` contains `input_format`, `output_format`, `baselines`
- [ ] `ibenchmark_range.center_ibenchmark` with `rho`, `omega_tier`, `epsilon`
- [ ] `ibenchmark_range.tier_bounds` and `proximity_threshold`
- [ ] `d_spec` present; S1–S4 gate justifications present

### epsilon_fn calibration:
```
d(Ω_centroid) = (ε_fn(Ω_centroid) - floor) / (sota - floor)
```
- [ ] d ∈ [0.3, 0.7] — not too easy, not too hard
- [ ] If d < 0.3: epsilon too generous (lower it)
- [ ] If d > 0.7: epsilon too strict (raise it)

### epsilon_fn evaluation test:
```python
import json, glob, random
# from pwm_scoring.epsilon import eval_epsilon   # when available

for f in glob.glob("principles/*/L2-*.json"):
    data = json.load(open(f))
    eps_fn = data["six_tuple"]["epsilon_fn"]
    omega  = data["six_tuple"]["omega"]
    # Test at 10 random Omega samples within declared ranges
    for _ in range(10):
        sample = {k: random.uniform(v[0], v[1])
                  for k, v in omega.items() if isinstance(v, list)}
        # result = eval_epsilon(eps_fn, sample)
        # assert isinstance(result, float), f"{f}: epsilon_fn didn't return float"
        # assert result > 0,                 f"{f}: epsilon_fn returned non-positive"
```

### Distance gate:
- [ ] `d_spec ≥ 0.15` from any other spec under the same principle
  ```
  d_spec(S1, S2) = 0.50 × d_structural + 0.30 × d_omega + 0.20 × d_epsilon
  ```

---

## V6 — L3 Benchmark JSON

For each `L3-NNN_<slug>.json`:

- [ ] `layer` = `"L3"`
- [ ] `parent_l1` and `parent_l2` reference the corresponding L1 / L2
- [ ] `benchmark_type` present (typically `"combined_P_and_I"`)
- [ ] `dataset_registry` with `primary` / `secondary` / `construction_method` / `num_dev_instances_per_tier`

### 4 I-benchmark tiers (T1–T4):

| Tier | Ω Position | ρ | d range |
|------|-----------|---|---------|
| T1 nominal | Ω_centroid | 1  | d < 0.2 |
| T2 low     | easy Ω     | 3  | 0.2 ≤ d < 0.4 |
| T3 moderate| mid Ω      | 5  | 0.4 ≤ d < 0.6 |
| T4 blind   | hard Ω     | 10 | 0.6 ≤ d < 0.8 |

- [ ] All 4 tiers present in `ibenchmarks`
- [ ] `rho` values match table above
- [ ] Each tier has: `omega_tier`, `epsilon`, `d_ibench`, `baselines` (each with `name`, `score`, `Q`)

### P-benchmark:
- [ ] `p_benchmark` present; real dataset referenced (`dataset_p_benchmark.name`)
- [ ] Covers full Ω range
- [ ] `rho = 50` (fixed for all P-benchmarks)
- [ ] If H×W > 480×480: uses 2×2 hard stitch (seam_map in true_phi)

### Baselines (≥ 2 per benchmark):
- [ ] At least 2 baseline solvers included per tier
- [ ] Each baseline has: `score` (PSNR or principle-appropriate metric) and `Q`
- [ ] **HARDNESS RULE**: no single baseline passes `epsilon_fn` everywhere across all Ω — every L3 must carry a `hardness_rule_check` string naming the failure corner.
  ```python
  for f in glob.glob("principles/*/L3-*.json"):
      data = json.load(open(f))
      assert "hardness_rule_check" in data, f"{f}: missing hardness_rule_check"
      assert "SATISFIED" in data["hardness_rule_check"], \
          f"{f}: hardness_rule_check not SATISFIED"
  ```

### I-benchmark tier spacing:
- [ ] Each consecutive tier differs ≥ 10% in at least 1 Ω dimension
  ```python
  # For each pair of adjacent tiers (T1→T2, T2→T3, T3→T4)
  for f in glob.glob("principles/*/L3-*.json"):
      data = json.load(open(f))
      tiers = data["ibenchmarks"]
      for t1, t2 in zip(tiers, tiers[1:]):
          shared = set(t1["omega_tier"]) & set(t2["omega_tier"])
          numeric_shared = [k for k in shared
                            if isinstance(t1["omega_tier"][k], (int, float))
                            and isinstance(t2["omega_tier"][k], (int, float))]
          max_diff = max((abs(t1["omega_tier"][k] - t2["omega_tier"][k])
                          / max(abs(t1["omega_tier"][k]), 1e-10))
                         for k in numeric_shared) if numeric_shared else 0
          assert max_diff >= 0.10, f"{f}: tiers {t1['tier']}→{t2['tier']} too close: {max_diff:.3f}"
  ```

### I-benchmark distance:
- [ ] `d_ibench ≥ 0.10` from existing I-benchmarks in same spec

---

## V7 — Self-Review Checklist (12 Points)

Run for EVERY principle (L1+L2+L3 set):

1. [ ] P = (E, G, W, C) quadruple complete
2. [ ] physics_fingerprint complete (all 7 fields)
3. [ ] spec_range and ibenchmark_range complete
4. [ ] epsilon_fn evaluates without error for 10 random Ω samples
5. [ ] Hardness rule: no baseline passes epsilon everywhere
6. [ ] d_spec ≥ 0.15 from any other spec under same principle
7. [ ] d_ibench ≥ 0.10 from existing I-benchmarks in same spec
8. [ ] I-benchmark tiers: each differs ≥ 10% in ≥ 1 Ω dimension
9. [ ] All JSON fields present and correctly typed
10. [ ] `E.forward_model` in L1 matches `six_tuple.E.forward` in L2
11. [ ] `difficulty_delta` consistent with `G.L_DAG` complexity
12. [ ] P1–P10 physics tests PASS

---

## V8 — Batch Validation Script

```python
#!/usr/bin/env python3
import json, glob, os
from collections import Counter

errors = []
domains = Counter()

for f in sorted(glob.glob("principles/*/L1-*.json")):
    domain = os.path.basename(os.path.dirname(f))
    domains[domain] += 1
    data = json.load(open(f))

    # layer must be "L1"
    if data.get("layer") != "L1":
        errors.append(f"{f}: layer != 'L1' (got {data.get('layer')!r})")

    # P = (E, G, W, C) quadruple — top-level namespaces
    for key in ("E", "G", "W", "C"):
        if key not in data:
            errors.append(f"{f}: missing top-level {key}")

    # Fingerprint
    fp = data.get("physics_fingerprint", {})
    for key in ("carrier","sensing_mechanism","integration_axis",
                "problem_class","noise_model","solution_space","primitives"):
        if key not in fp:
            errors.append(f"{f}: missing fingerprint.{key}")

    # difficulty_delta valid
    delta = data.get("difficulty_delta")
    if delta not in (1, 3, 5, 10, 50):
        errors.append(f"{f}: invalid difficulty_delta={delta}")

print("=== Domain Counts ===")
for d, c in sorted(domains.items()):
    print(f"  {d:30s} {c}")
print(f"  TOTAL: {sum(domains.values())}")

if errors:
    print(f"\n=== {len(errors)} ERRORS ===")
    for e in errors:
        print(f"  {e}")
else:
    print("\nAll L1 files valid!")
```

**Expected (as of 2026-04-20):**
```
=== Domain Counts ===
  A_microscopy              24
  B_compressive_imaging      5
  C_medical_imaging         41
  D_coherent_imaging         5
  E_computational_photo      5
  F_computational_optics     4
  G_electron_microscopy     11
  H_depth_imaging            5
  I_remote_sensing          11
  J_industrial_inspect      14
  M_ultrafast_imaging        4
  N_quantum_imaging          3
  O_multimodal_fusion        6
  P_scanning_probe           4
  TOTAL: 142

All L1 files valid!
```

---

## V9 — Cross-Agent Consistency

- [ ] Domain folders assigned to imaging match CLAUDE.md: A, B, C, D, E, F, G, H, I, J, M, N, O, P
- [ ] Domains M, N, O, P are NOT in agent-signal (moved to imaging because optical carrier)
- [ ] No overlap with agent-physics, agent-chemistry, agent-signal, agent-applied domains
- [ ] Principle IDs are globally unique (no collisions with other content agents)

---

## V10 — Progress Reporting

After each domain batch, `coordination/agent-coord/progress.md` should show a row like:

```
| agent-imaging | B_compressive_imaging | 5 | 5 | DONE | feat/genesis-principles-imaging |
```

- [ ] All 14 domains tracked in progress.md
- [ ] Counts match actual file counts
- [ ] Final status: DONE with PR link
