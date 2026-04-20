# agent-imaging: Validation Checklist

Run every check below before merging the imaging principles PR. All content agents follow the same L1/L2/L3 structure. Domain-specific values are in the tables below.

---

## V1 — Domain Coverage

| Domain Folder | Expected Principles | Delivered? |
|---|---|---|
| A_microscopy | ~24 | [ ] |
| B_compressive_imaging | ~5 | [ ] |
| C_medical_imaging | ~41 | [ ] |
| D_coherent_imaging | ~5 | [ ] |
| E_computational_photography | ~5 | [ ] |
| F_computational_optics | ~4 | [ ] |
| G_electron_microscopy | ~11 | [ ] |
| H_depth_imaging | ~5 | [ ] |
| I_remote_sensing | ~11 | [ ] |
| J_industrial_inspection | ~14 | [ ] |
| M_ultrafast_imaging | ~4 | [ ] |
| N_quantum_imaging | ~3 | [ ] |
| O_multimodal_fusion | ~6 | [ ] |
| P_scanning_probe | ~4 | [ ] |
| **Total** | **~115** | [ ] |

**Verify folder names are canonical (no truncation):**
```bash
# These must match exactly
ls pwm-team/content/agent-imaging/principles/ | sort
# Must include E_computational_photography (not E_computational_photo)
# Must include J_industrial_inspection (not J_industrial_inspect)
```

---

## V2 — Per-Principle File Structure

For EVERY principle, verify 3 files exist:

```
principles/<domain>/L1-NNN.json   # Principle
principles/<domain>/L2-NNN.json   # Spec
principles/<domain>/L3-NNN.json   # Benchmark
```

**Verify:**
```bash
# Count L1/L2/L3 files per domain
for d in principles/*/; do
  l1=$(ls "$d"L1-*.json 2>/dev/null | wc -l)
  l2=$(ls "$d"L2-*.json 2>/dev/null | wc -l)
  l3=$(ls "$d"L3-*.json 2>/dev/null | wc -l)
  echo "$d: L1=$l1 L2=$l2 L3=$l3"
done
# L1 count should match L2 and L3 counts per domain
```

---

## V3 — L1 Principle JSON (P = (E, G, W, C) Quadruple)

For each L1-NNN.json, verify:

### Required top-level fields:
- [ ] `artifact_id` — unique identifier
- [ ] `layer` — must be 1
- [ ] `principle_number` — sequential
- [ ] `title` — descriptive name
- [ ] `domain` — matches parent folder name
- [ ] `source_file` — reference to mine_example source

### P = (E, G, W, C) — all four must be present:

**E — Forward Model:**
- [ ] `forward_model.equation` — mathematical expression (y = Φx + ε)
- [ ] `forward_model.description` — plain English
- [ ] `world_state_x` — what's being recovered
- [ ] `observation_y` — what's measured
- [ ] `physical_parameters_theta` — physical constants

**G — DAG:**
- [ ] `dag.nodes` — list of operator nodes
- [ ] `dag.edges` — connections between nodes
- [ ] No cycles in DAG (P10 test)

**W — Well-posedness:**
- [ ] `well_posedness.existence` — bool
- [ ] `well_posedness.uniqueness` — bool
- [ ] `well_posedness.stability` — "stable" | "conditionally_stable" | "unstable"
- [ ] `well_posedness.condition_number` — numeric estimate

**C — Convergence:**
- [ ] `convergence.solver_class` — e.g., "iterative", "direct", "MAP"
- [ ] `convergence.convergence_rate_q` — default 2.0
- [ ] `convergence.error_bound` — expression
- [ ] `convergence.complexity` — Big-O notation

### Additional required fields:
- [ ] `difficulty_delta` — integer: 1 (trivial), 3 (standard), 5 (challenging), 10 (hard), 50 (frontier)
- [ ] `error_metric.primary` — e.g., "PSNR", "SSIM"
- [ ] `error_metric.secondary` — e.g., "SAM" for hyperspectral
- [ ] `physics_fingerprint` — all 7 subfields present (see V4)
- [ ] `spec_range` — Ω parameter ranges
- [ ] `ibenchmark_range` — center_ibenchmark, tier_bounds
- [ ] `mismatch_parameters` — list (may be empty for oracle specs)
- [ ] `p1_p10_tests` — results of physics validity tests
- [ ] `s1_s4_gates` — gate check results

**JSON schema validation:**
```python
import json, glob
for f in glob.glob("principles/*/L1-*.json"):
    data = json.load(open(f))
    assert data["layer"] == 1, f"{f}: wrong layer"
    assert "forward_model" in data, f"{f}: missing forward_model (E)"
    assert "dag" in data, f"{f}: missing dag (G)"
    assert "well_posedness" in data, f"{f}: missing well_posedness (W)"
    assert "convergence" in data, f"{f}: missing convergence (C)"
    assert "difficulty_delta" in data, f"{f}: missing difficulty_delta"
    assert "physics_fingerprint" in data, f"{f}: missing physics_fingerprint"
    print(f"OK  {f}")
```

---

## V4 — Physics Fingerprint (7 Fields)

Every L1 must have all 7:

| Field | Valid Values (imaging) | Present? |
|---|---|---|
| `carrier` | "photon", "electron", "X-ray", "spin", etc. | [ ] |
| `sensing_mechanism` | "tomographic", "interferometric", "coded_aperture", "resonant", "spectral" | [ ] |
| `integration_axis` | "spectral", "temporal", "spatial", "angular", "volumetric" | [ ] |
| `problem_class` | "linear_inverse", "nonlinear_inverse", "forward", "estimation" | [ ] |
| `noise_model` | "gaussian", "poisson", "shot_poisson", "multiplicative" | [ ] |
| `solution_space` | "2D_spatial", "3D_temporal", "4D_spectral_depth", etc. | [ ] |
| `primitives` | list of Level 1 and/or Level 2 primitives | [ ] |

**Verify:**
```python
FINGERPRINT_KEYS = {"carrier", "sensing_mechanism", "integration_axis",
                     "problem_class", "noise_model", "solution_space", "primitives"}
for f in glob.glob("principles/*/L1-*.json"):
    data = json.load(open(f))
    fp = data.get("physics_fingerprint", {})
    missing = FINGERPRINT_KEYS - set(fp.keys())
    assert not missing, f"{f}: missing fingerprint fields: {missing}"
```

---

## V5 — L2 Spec JSON (S = (Ω, E, B, I, O, ε))

For each L2-NNN.json:

- [ ] `layer` = 2
- [ ] References parent L1 by `principle_id`
- [ ] At least 1 spec (2 preferred):
  - Spec 1: mismatch-only (Ω = uncertain parameters)
  - Spec 2: oracle-assisted (known parameters)
- [ ] `epsilon_fn` — string expression, evaluable by epsilon.py
- [ ] `omega_range` — parameter ranges for Ω
- [ ] S1-S4 gate justifications present

### epsilon_fn calibration:
```
d(Ω_centroid) = (ε_fn(Ω_centroid) - floor) / (sota - floor)
```
- [ ] d ∈ [0.3, 0.7] — not too easy, not too hard
- [ ] If d < 0.3: epsilon too generous (lower it)
- [ ] If d > 0.7: epsilon too strict (raise it)

### epsilon_fn evaluation test:
```python
from pwm_scoring.epsilon import eval_epsilon
for f in glob.glob("principles/*/L2-*.json"):
    data = json.load(open(f))
    eps_fn = data["epsilon_fn"]
    omega = data["omega_range"]
    # Test at 10 random Omega samples
    for _ in range(10):
        sample = {k: random.uniform(v[0], v[1]) for k, v in omega.items()}
        result = eval_epsilon(eps_fn, sample)
        assert isinstance(result, float), f"{f}: epsilon_fn didn't return float"
        assert result > 0, f"{f}: epsilon_fn returned non-positive"
```

### Distance gate:
- [ ] `d_spec ≥ 0.15` from any other spec under the same principle
  ```
  d_spec(S1, S2) = 0.50 × d_structural + 0.30 × d_omega + 0.20 × d_epsilon
  ```

---

## V6 — L3 Benchmark JSON

For each L3-NNN.json:

- [ ] `layer` = 3
- [ ] References parent L2 by `spec_id`

### 4 I-benchmark tiers (T1-T4):

| Tier | Ω Position | ρ | d range |
|------|-----------|---|---------|
| T1 nominal | Ω_centroid | 1 | d < 0.2 |
| T2 low | easy Ω | 3 | 0.2 ≤ d < 0.4 |
| T3 moderate | mid Ω | 5 | 0.4 ≤ d < 0.6 |
| T4 blind | hard Ω | 10 | 0.6 ≤ d < 0.8 |

- [ ] All 4 tiers present
- [ ] ρ values match table above
- [ ] Each tier has: `omega_tier`, `dataset_description`, `quality_thresholds`

### P-benchmark:
- [ ] Real dataset (not synthetic only)
- [ ] Covers full Ω range
- [ ] ρ = 50 (fixed for all P-benchmarks)
- [ ] If H×W > 480×480: uses 2×2 hard stitch (seam_map in true_phi)

### Baselines (≥ 2 per benchmark):
- [ ] At least 2 baseline solvers included
- [ ] Each baseline has: expected PSNR, expected Q
- [ ] **HARDNESS RULE**: no single baseline passes epsilon_fn everywhere across all Ω
  ```python
  # For each baseline, verify it fails epsilon at some Omega point
  for baseline in data["baselines"]:
      all_pass = all(
          baseline["psnr_at_omega"][i] >= eval_epsilon(eps_fn, omega_i)
          for i, omega_i in enumerate(omega_samples)
      )
      assert not all_pass, f"Baseline {baseline['name']} passes everywhere — violates hardness rule"
  ```

### I-benchmark tier spacing:
- [ ] Each consecutive tier differs ≥ 10% in at least 1 Ω dimension
  ```python
  # For each pair of adjacent tiers
  for t1, t2 in [(T1, T2), (T2, T3), (T3, T4)]:
      max_diff = max(abs(t1.omega[k] - t2.omega[k]) / max(abs(t1.omega[k]), 1e-10)
                     for k in t1.omega)
      assert max_diff >= 0.10, f"Tiers too close: max relative diff = {max_diff}"
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
10. [ ] forward_model in L1 matches E in L2
11. [ ] difficulty_delta consistent with L_DAG complexity
12. [ ] P1-P10 physics tests PASS

---

## V8 — Batch Validation Script

```python
import json, glob, os

errors = []
domains = {}

for f in sorted(glob.glob("principles/*/L1-*.json")):
    domain = os.path.basename(os.path.dirname(f))
    domains.setdefault(domain, 0)
    domains[domain] += 1

    data = json.load(open(f))

    # Check P quadruple
    for key in ["forward_model", "dag", "well_posedness", "convergence"]:
        if key not in data:
            errors.append(f"{f}: missing {key}")

    # Check layer
    if data.get("layer") != 1:
        errors.append(f"{f}: layer != 1")

    # Check fingerprint
    fp = data.get("physics_fingerprint", {})
    for key in ["carrier", "sensing_mechanism", "integration_axis",
                 "problem_class", "noise_model", "solution_space", "primitives"]:
        if key not in fp:
            errors.append(f"{f}: missing fingerprint.{key}")

    # Check difficulty_delta valid
    delta = data.get("difficulty_delta")
    if delta not in [1, 3, 5, 10, 50]:
        errors.append(f"{f}: invalid difficulty_delta={delta}")

print("=== Domain Counts ===")
for d, c in sorted(domains.items()):
    print(f"  {d}: {c}")
print(f"  TOTAL: {sum(domains.values())}")

if errors:
    print(f"\n=== {len(errors)} ERRORS ===")
    for e in errors:
        print(f"  {e}")
else:
    print("\nAll L1 files valid!")
```

---

## V9 — Cross-Agent Consistency

- [ ] Domain folders assigned to imaging match CLAUDE.md: A, B, C, D, E, F, G, H, I, J, M, N, O, P
- [ ] Domains M, N, O, P are NOT in agent-signal (moved to imaging because optical carrier)
- [ ] No overlap with agent-physics, agent-chemistry, agent-signal, agent-applied domains
- [ ] Principle IDs are globally unique (no collisions with other content agents)

---

## V10 — Progress Reporting

After each domain batch, progress.md should show:
```
| agent-imaging | B_compressive_imaging | 5 | 5 | DONE | feat/genesis-principles-imaging |
```

- [ ] All 14 domains tracked in progress.md
- [ ] Counts match actual file counts
- [ ] Final status: DONE with PR link
