# agent-scoring: Validation Checklist

Run every check below before merging the scoring engine PR. All formulas and constants reference `pwm_overview1.md` (canonical spec).

---

## V1 — Files Exist

- [ ] `pwm_scoring/__init__.py` — exports `score_solution`, `SolutionScore`
- [ ] `pwm_scoring/score.py` — main entry point
- [ ] `pwm_scoring/tracks.py` — Track A/B/C implementations
- [ ] `pwm_scoring/gates.py` — S1-S4 gate checks
- [ ] `pwm_scoring/epsilon.py` — AST-sandboxed epsilon evaluator
- [ ] `pwm_scoring/metrics.py` — PSNR, SSIM, SAM, residual_norm
- [ ] `tests/test_epsilon.py` — ≥ 10 unit tests including injection attempts
- [ ] `tests/test_metrics.py` — tests against known reference values
- [ ] `tests/test_gates.py` — passing and failing inputs per gate
- [ ] `tests/test_tracks.py` — mock solver tests
- [ ] `tests/test_score_integration.py` — CASSI T1 nominal end-to-end

**Verify:**
```bash
pip install -e .
python -c "from pwm_scoring import score_solution, SolutionScore; print('OK')"
pytest tests/ -v
```

---

## V2 — epsilon.py

### Allowed AST nodes (whitelist):
- [ ] `Num` (numeric literals)
- [ ] `BinOp` (arithmetic: +, -, *, /, **, //)
- [ ] `UnaryOp` (unary: -, +)
- [ ] `Call` — only these math functions: `log2`, `log10`, `sqrt`, `exp`, `abs`, `min`, `max`
- [ ] `Name` — only omega dict keys

### Forbidden AST nodes (must reject):
- [ ] `Import`, `ImportFrom`
- [ ] `Exec`, `Eval`
- [ ] `Attribute` (no `os.system`, `__import__`, etc.)
- [ ] `Subscript` (no `dict[key]` tricks)

### eval_epsilon() behavior:
- [ ] Returns `float`
- [ ] Raises `EpsilonEvalError` on any forbidden node
- [ ] Raises `EpsilonEvalError` on evaluation error (division by zero, etc.)
- [ ] Omega dict keys become local variables during evaluation

**Canonical test cases (from cassi.md):**
```python
assert abs(eval_epsilon("20 + 5 * log2(N/64)", {"N": 128}) - 25.0) < 1e-9
assert abs(eval_epsilon("22 + 3 * log2(H*W / 4096)", {"H": 64, "W": 64}) - 22.0) < 1e-9
```

**Injection tests (must all raise EpsilonEvalError):**
```python
eval_epsilon("__import__('os').system('rm -rf /')", {})           # Import
eval_epsilon("eval('1+1')", {})                                    # Eval
eval_epsilon("open('/etc/passwd').read()", {})                     # Attribute
eval_epsilon("(lambda: 1)()", {})                                  # Lambda
eval_epsilon("[x for x in range(10)]", {})                         # ListComp
eval_epsilon("{'a': 1}['a']", {})                                  # Subscript
```

---

## V3 — metrics.py

- [ ] `psnr(gt, pred, data_range) -> float`
  - Formula: `10 * log10(data_range**2 / MSE)`
  - Handles float32 (range 0-1) and uint8 (range 0-255) normalization
  - Returns `inf` when MSE = 0 (perfect reconstruction)

- [ ] `ssim(gt, pred) -> float`
  - Matches standard SSIM definition (Wang et al. 2004)
  - Returns value in [-1, 1], typically [0, 1]

- [ ] `sam(gt, pred) -> float`
  - Spectral angle mapper for hyperspectral data
  - Formula: `mean(arccos(dot(a,b) / (|a| * |b|)))` per pixel
  - Returns angle in radians (or degrees — document which)

- [ ] `residual_norm(y, phi_fn, x_hat) -> float`
  - Formula: `||y - phi_fn(x_hat)||_2 / ||y||_2`
  - Must handle phi as callable (not just matrix)

**Verify with known values:**
```python
import numpy as np
gt = np.ones((8,8), dtype=np.float32)
pred = gt.copy()
assert psnr(gt, pred) == float('inf')  # perfect match

pred_noisy = gt + 0.1 * np.random.randn(8,8).astype(np.float32)
p = psnr(gt, pred_noisy)
assert 10 < p < 50  # sanity range
```

---

## V4 — gates.py (S1-S4)

### S1 — Dimensional Consistency
- [ ] `check_s1(output, manifest) -> (bool, str)`
- [ ] Verifies output array dimensions match manifest expected shape
- [ ] Checks for NaN values in output
- [ ] Checks correct dtype

### S2 — Well-posedness (Hadamard)
- [ ] `check_s2(method_sig, principle) -> (bool, str)`
- [ ] If `principle.W.uniqueness == False`: iterative/MAP methods valid; direct inversion is NOT valid
- [ ] If `principle.W.uniqueness == True`: direct inversion is valid
- [ ] Checks solver method type matches well-posedness conditions

### S3 — Convergent Solver
- [ ] `check_s3(residuals, resolutions) -> (bool, str)`
- [ ] Fits log-log slope of residuals vs resolutions
- [ ] Pass if slope ≥ 1.8 (approximately O(h²) convergence)
- [ ] Fail if slope < 1.8 with message showing actual slope

### S4 — Bounded Error
- [ ] `check_s4(psnr_worst, epsilon) -> (bool, str)`
- [ ] Pass if `psnr_worst >= epsilon`
- [ ] Fail with message: actual PSNR, required epsilon, difference

**Test each gate with both passing and failing inputs:**
```bash
pytest tests/test_gates.py -v
```

---

## V5 — tracks.py

### Track A — Stratified Worst-Case
- [ ] Divides Ω into K=4 roughly equal-volume strata
- [ ] Draws N_s=5 random Ω points per stratum
- [ ] Seed = `int(SHA256(benchmark_hash), 16) % 2**32` (deterministic)
- [ ] Worst score per stratum must ≥ `eval_epsilon(epsilon_fn, Ω_centroid)`
- [ ] All 4 strata must independently pass
- [ ] Returns `(bool, {"stratum_0": {"worst_psnr": float, "pass": bool}, ...})`

### Track B — Uniform Median
- [ ] Samples N=50 Ω points uniformly (no stratification)
- [ ] Seed same mechanism as Track A
- [ ] Median = 25th value (sorted ascending, index 24)
- [ ] Ω_median = geometric centroid of all 50 parameter vectors
- [ ] Pass if median ≥ `eval_epsilon(epsilon_fn, Ω_median)`
- [ ] Returns `(bool, median_psnr)`

### Track C — Degradation AUC
- [ ] Only runs when `difficulty_dims` declared in spec
- [ ] Sweeps K_phi=5 points: phi ∈ {0.0, 0.25, 0.50, 0.75, 1.0}
- [ ] At each phi: 10 scenes, record median PSNR
- [ ] Q_norm(phi) = psnr(phi) / eval_epsilon(epsilon_fn, Ω_at_phi)
- [ ] Returns trapezoid AUC of Q_norm vs phi
- [ ] Returns `float` (the AUC)

**Determinism test:**
```python
# Run Track A twice with same benchmark_hash
result1 = track_a(benchmark, solver_fn, omega_range)
result2 = track_a(benchmark, solver_fn, omega_range)
assert result1 == result2  # must be identical
```

---

## V6 — Q_p Formula (MUST match canonical spec exactly)

### Without Track C (oracle specs, no difficulty_dims):
```
Q_p = 0.40 × coverage + 0.40 × margin + 0.20 × stratum_pass_frac
```

### With Track C (mismatch specs, difficulty_dims declared):
```
Q_p = 0.35 × coverage + 0.35 × margin + 0.15 × stratum_pass_frac + 0.15 × degradation_score
```

### Component definitions:
- [ ] `coverage` = fraction of ALL sampled Ω points where `r_i >= 1.0`
- [ ] `margin` = `mean(r_i - 1.0)` over ONLY passing instances (r_i ≥ 1.0)
- [ ] `stratum_pass_frac` = fraction of K=4 strata where ALL instances in that stratum pass
- [ ] `degradation_score` = area under normalized degradation curve (Track C AUC)

### Certification tiers:
- [ ] Strong: all tracks pass AND Q_p ≥ 0.75
- [ ] Standard: all tracks pass AND Q_p ≥ 0.55
- [ ] Below threshold: not certified → Q set to 0, no minting reward

**Verify weights sum to 1.0:**
```python
assert 0.40 + 0.40 + 0.20 == 1.0  # without Track C
assert 0.35 + 0.35 + 0.15 + 0.15 == 1.0  # with Track C
```

**WRONG values to reject (from prior bugs):**
- ~~Q_p = 0.35×T_A + 0.45×T_B + 0.20×T_C~~ (WRONG — uses track scores not components)
- ~~Q_p = 0.40×T_A + 0.60×T_B~~ (WRONG — only two tracks)

---

## V7 — score.py (Main Entry Point)

### score_solution() flow:
1. [ ] Run S1 through S4 gates in order
2. [ ] If any gate fails: return `SolutionScore(Q=0.0, gate_verdicts={"S1":"fail",...})`
3. [ ] Run Track A, Track B, Track C (if applicable)
4. [ ] Compute Q_p using formula from V6
5. [ ] Determine certification tier (Strong / Standard / below)
6. [ ] Build cert_payload matching cert_schema.json
7. [ ] Return complete SolutionScore

### SolutionScore dataclass fields:
- [ ] `psnr_per_instance: list[float]`
- [ ] `ssim_per_instance: list[float]`
- [ ] `Q: float` — in [0, 1]
- [ ] `track_a_pass: bool`
- [ ] `track_b_pass: bool`
- [ ] `track_c_auc: float | None` (None if no difficulty_dims)
- [ ] `gate_verdicts: dict` — `{"S1": "pass"|"fail", "S2": ..., "S3": ..., "S4": ...}`
- [ ] `cert_payload: dict` — ready for PWMCertificate.submit()

---

## V8 — Staged Verification Pipeline

| Stage | Instances | Pass Condition | Reward |
|-------|-----------|---------------|--------|
| Stage 0 | 20 primary I-benchmark | Q ≥ ε on ≥ 18/20 | 50% |
| Stage 1 | ~37 P-lite (stratified) | Q ≥ ε on ≥ 34/37 | 85% |
| Stage 2 | ~170 full P-benchmark | Q ≥ ε on ≥ 161/170 | 100% |

- [ ] Verify pass thresholds: 18/20 = 90%, 34/37 ≈ 91.9%, 161/170 ≈ 94.7%
- [ ] Reward multipliers applied correctly per stage

---

## V9 — Determinism

```python
# Run score_solution twice with identical inputs
score1 = score_solution(manifest, instance_dir, output, omega)
score2 = score_solution(manifest, instance_dir, output, omega)

assert score1.Q == score2.Q
assert score1.cert_payload == score2.cert_payload

# cert_hash must be identical
import hashlib, json
h1 = hashlib.sha256(json.dumps(score1.cert_payload, sort_keys=True).encode()).hexdigest()
h2 = hashlib.sha256(json.dumps(score2.cert_payload, sort_keys=True).encode()).hexdigest()
assert h1 == h2
```

- [ ] No random state leaks (all randomness uses deterministic seed from benchmark_hash)
- [ ] Float operations produce identical results across runs
- [ ] JSON serialization is deterministic (sorted keys)

---

## V10 — cert_payload Schema Validation

```python
import json, jsonschema

schema = json.load(open("../../coordination/agent-coord/interfaces/cert_schema.json"))
payload = score_solution(...).cert_payload
jsonschema.validate(payload, schema)  # must not raise
```

- [ ] All required fields present in cert_payload
- [ ] Field types match schema (bytes32 as hex string, uint8 as int, etc.)
- [ ] cert_hash is valid SHA-256 hex string

---

## V11 — Performance

```bash
python -c "
import time
from pwm_scoring import score_solution
# Load CASSI T1 nominal 256x256 instance
t = time.time()
score_solution(manifest, instance_dir, output, omega)
elapsed = time.time() - t
print(f'Elapsed: {elapsed:.1f}s')
assert elapsed <= 60, f'Too slow: {elapsed:.1f}s > 60s'
"
```

- [ ] score_solution() completes in ≤ 60 seconds on CPU for 256×256 instance
- [ ] If bottleneck: profile to identify (likely Track A/B sampling loop)

---

## V12 — Integration Test (CASSI T1 Nominal)

```bash
pytest tests/test_score_integration.py -v
```

- [ ] Loads CASSI T1 nominal benchmark from `../../pwm_product/genesis/l3/L3-003.json`
- [ ] Runs `score_solution()` with GAP-TV reference solver
- [ ] Q value within 10% of reference value in L3-003.json baseline
- [ ] All 4 S-gates pass
- [ ] Track A passes (all 4 strata)
- [ ] Track B passes (median above epsilon)
- [ ] cert_payload validates against schema

---

## V13 — Interface Published

After all tests pass:
- [ ] `pwm_scoring/__init__.py` copied to `../../coordination/agent-coord/interfaces/scoring_api.py`
- [ ] progress.md updated: scoring engine = DONE
