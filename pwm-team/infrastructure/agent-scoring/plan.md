# agent-scoring: Execution Plan

Read `CLAUDE.md` first (your role and all interface specs). This file is your step-by-step work order.

---

## Before You Start

- [ ] Read `CLAUDE.md` — full interface specs for all modules are there.
- [ ] Read `../../papers/Proof-of-Solution/pwm_overview1.md` §Track A/B/C, §S1-S4 Gates, §Difficulty Score and ρ Tier Mapping.
- [ ] Read `../../papers/Proof-of-Solution/mine_example/cassi.md` and `cacti.md` — reference principles.
- [ ] Read `../../coordination/agent-coord/interfaces/cert_schema.json` — your cert_payload must match this exactly.
- [ ] **Wait for M1.1**: you need `cert_schema.json` from agent-contracts before finalizing cert_payload format. You can start all other modules immediately.

---

## Step 1 — epsilon.py (start here — no dependencies)

- [ ] **1.1** `epsilon.py` is already scaffolded. Read the existing file.
- [ ] **1.2** Ensure `eval_epsilon(epsilon_fn_str, omega)` is fully implemented:
  - AST parse `epsilon_fn_str`
  - Walk AST: allow only `Num`, `BinOp`, `UnaryOp`, `Call` (math only), `Name` (omega keys)
  - Forbidden: `Import`, `ImportFrom`, `Exec`, `Eval`, `Attribute`, `Subscript`
  - Bind omega dict as local variables; evaluate with `eval()` in restricted namespace
  - Raise `EpsilonEvalError` on any forbidden node or evaluation error
- [ ] **1.3** Test with examples from cassi.md:
  ```python
  assert abs(eval_epsilon("20 + 5 * log2(N/64)", {"N": 128}) - 25.0) < 1e-9
  assert abs(eval_epsilon("22 + 3 * log2(H*W / 4096)", {"H": 64, "W": 64}) - 22.0) < 1e-9
  ```
- [ ] **1.4** Write `tests/test_epsilon.py` — at least 10 unit tests including injection attempts.

---

## Step 2 — metrics.py

- [ ] **2.1** `psnr(gt, pred)` — implement: `10 * log10(1.0 / mean_squared_error)`, handles float32/uint8 normalization.
- [ ] **2.2** `ssim(gt, pred)` — implement using skimage or manual formula; match standard definition.
- [ ] **2.3** `sam(gt, pred)` — spectral angle mapper for hyperspectral: `mean(arccos(dot(a,b)/(|a||b|)))` per pixel.
- [ ] **2.4** `residual_norm(y, phi, x_hat)` — `||y - phi @ x_hat||_2 / ||y||_2`.
- [ ] **2.5** Write `tests/test_metrics.py` — test each metric against known reference values.

---

## Step 3 — gates.py

- [ ] **3.1** `check_s1(output, manifest) -> (bool, str)`:
  - Verify output array dimensions match manifest expected shape
  - Verify mask consistency (no NaN, correct dtype)
  - Return `(False, reason)` on first failure
- [ ] **3.2** `check_s2(method_sig, principle) -> (bool, str)`:
  - Verify solver method type matches principle's `well_posedness.uniqueness`
  - E.g., if uniqueness=False, iterative/MAP methods are valid; direct inversion is not
- [ ] **3.3** `check_s3(residuals, resolutions) -> (bool, str)`:
  - Given residuals at multiple resolutions, fit log-log slope
  - Pass if slope ≥ 1.8 (≈ O(h²) convergence)
- [ ] **3.4** `check_s4(psnr_worst, epsilon) -> (bool, str)`:
  - Pass if `psnr_worst >= epsilon`
- [ ] **3.5** Write `tests/test_gates.py` — test each gate with passing and failing inputs.

---

## Step 4 — tracks.py

- [ ] **4.1** `track_a(benchmark, solver_fn, omega_range) -> (bool, dict)`:
  - Read strata from benchmark (e.g., CASSI: S1 ≤128², S2 128²–512², S3 >512²)
  - For each stratum: sample 5 Ω points (seed = `int(SHA256(benchmark_hash), 16) % 2**32`)
  - Run solver at each point; record PSNR
  - Worst PSNR per stratum must ≥ `eval_epsilon(benchmark.epsilon_fn, Ω_centroid)`
  - Return `(all_strata_pass, {"stratum": {"worst_psnr": float, "pass": bool}})`
- [ ] **4.2** `track_b(benchmark, solver_fn, omega_range) -> (bool, float)`:
  - Sample 50 Ω points uniformly (same seed mechanism)
  - Compute PSNR at each; take median
  - Pass if median ≥ `eval_epsilon(benchmark.epsilon_fn, Ω_median)`
  - Return `(pass, median_psnr)`
- [ ] **4.3** `track_c(benchmark, solver_fn, mismatch_dims) -> float`:
  - Sweep phi ∈ {0.0, 0.25, 0.50, 0.75, 1.0}
  - At each phi: 10 scenes, record median PSNR
  - Compute `Q_norm(phi) = psnr(phi) / eval_epsilon(benchmark.epsilon_fn, Ω_at_phi)`
  - Return trapezoid AUC of Q_norm vs phi
- [ ] **4.4** Write `tests/test_tracks.py` with a mock solver that returns known PSNR values.

---

## Step 5 — score.py (main entry point)

- [ ] **5.1** Implement `score_solution(benchmark_manifest, instance_dir, solver_output, omega_params) -> SolutionScore`:
  ```
  1. Run check_s1 through check_s4 (gates)
  2. If any gate fails: return SolutionScore with Q=0.0, gate_verdicts showing failure
  3. Run track_a, track_b, track_c
  4. Q = weighted average: track_a 40% + track_b 40% + track_c 20% (0 if no track_c)
  5. Build cert_payload matching cert_schema.json
  6. Return SolutionScore
  ```
- [ ] **5.2** Confirm determinism: run twice with identical inputs → `cert_payload["cert_hash"]` identical both times.
- [ ] **5.3** Write `tests/test_score_integration.py`:
  - Load CASSI T1 nominal benchmark from `../../pwm_product/genesis/l3/L3-003.json`
  - Run `score_solution()` with GAP-TV reference solver
  - Confirm Q within 10% of reference value in L3-003.json baseline

---

## Step 6 — Validate cert_payload Schema

- [ ] **6.1** Wait for `../../coordination/agent-coord/interfaces/cert_schema.json` (after M1.1).
- [ ] **6.2** Run schema validation:
  ```python
  import json, jsonschema
  schema = json.load(open("../../coordination/agent-coord/interfaces/cert_schema.json"))
  payload = score_solution(...).cert_payload
  jsonschema.validate(payload, schema)  # must not raise
  ```
- [ ] **6.3** Fix any field mismatches.

---

## Step 7 — Performance Check

- [ ] **7.1** Benchmark `score_solution()` on a 256×256 CASSI instance:
  ```bash
  python -c "import time; from pwm_scoring import score_solution; t=time.time(); score_solution(...); print(time.time()-t)"
  ```
  Must complete in ≤ 60 seconds on CPU.
- [ ] **7.2** If > 60s: profile and optimize the bottleneck (likely track_a/b sampling loop).

---

## Step 8 — Publish Interface

- [ ] **8.1** Copy scoring API stub to coord interfaces:
  ```bash
  cp pwm_scoring/__init__.py ../../coordination/agent-coord/interfaces/scoring_api.py
  ```

---

## Step 9 — Signal Completion

- [ ] **9.1** Update `../../coordination/agent-coord/progress.md` — mark M1.2 `DONE`.
- [ ] **9.2** Open PR: `feat/scoring-engine-v1`
  - Include: full `pwm_scoring/` package + `tests/`
  - PR description: test count, CASSI integration test result (Q value), timing benchmark
