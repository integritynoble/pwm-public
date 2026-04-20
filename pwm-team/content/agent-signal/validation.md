# agent-signal: Validation Checklist

Run every check below before merging the signal principles PR. Follows the same L1/L2/L3 structure as all content agents.

---

## V1 — Domain Coverage

| Domain Folder | Expected Principles | Delivered? |
|---|---|---|
| K_scientific_instrumentation | ~12 | [ ] |
| L_spectroscopy | ~12 | [ ] |
| AD_signal_processing | ~14 | [ ] |
| **Total** | **~38** | [ ] |

**IMPORTANT:** Domains M_ultrafast_imaging, N_quantum_imaging, O_multimodal_fusion, P_scanning_probe are assigned to agent-imaging (optical carrier), NOT agent-signal.

**Verify folder names are canonical:**
```bash
ls pwm-team/content/agent-signal/principles/ | sort
# Must include K_scientific_instrumentation (not K_sci_instrumentation)
# Must NOT contain M_, N_, O_, P_ folders (those belong to agent-imaging)
```

---

## V2 — Per-Principle File Structure

```bash
for d in principles/*/; do
  l1=$(ls "$d"L1-*.json 2>/dev/null | wc -l)
  l2=$(ls "$d"L2-*.json 2>/dev/null | wc -l)
  l3=$(ls "$d"L3-*.json 2>/dev/null | wc -l)
  echo "$d: L1=$l1 L2=$l2 L3=$l3"
done
```

---

## V3 — L1 Principle JSON (P = (E, G, W, C))

Same structural checks as agent-imaging V3. Signal-specific additions:

### Forward Model (E):
- [ ] Measurement equation: `y = A·x + n` (compressed sensing), `Y(f) = H(f)·X(f)` (convolution)
- [ ] world_state_x: signal being recovered (time series, spectrum, spatial field)
- [ ] observation_y: ADC samples, spectrometer readings, sensor output
- [ ] physical_parameters_theta: filter coefficients, sampling matrix, noise floor, SNR

### DAG (G) patterns:
- [ ] Filter: sample → transform → reconstruct
- [ ] Deconvolution: measure → PSF → deconvolve
- [ ] Compressed sensing: measure → sparsify → recover

### Well-posedness (W):
- [ ] Compressed sensing: uniqueness depends on RIP/coherence
- [ ] Blind deconvolution: uniqueness=false (scaling ambiguity)
- [ ] Calibrated systems: often well-posed

### Convergence (C):
- [ ] convergence_rate_q: 2.0 default; 1.0 for iterative recovery (ISTA, ADMM)
- [ ] solver_class: "iterative" for most recovery problems

### Physics fingerprint carrier types:
| Domain | Expected Carrier |
|---|---|
| K_scientific_instrumentation | "Acoustic", "Photon", "Electron" |
| L_spectroscopy | "Photon", "RF" |
| AD_signal_processing | "Acoustic", "RF", "Photon" |

### Ω dimensions:
- [ ] Often in frequency space: bandwidth, sampling_rate, SNR
- [ ] NOT spatial dimensions (that's imaging)

### error_metric (CRITICAL — NOT per-channel PSNR):
- [ ] Primary: `"SNR_dB"`, `"NMSE"`, `"spectral_accuracy"`, or `"reconstruction_error"`
- [ ] Units must be signal-appropriate

### difficulty_delta expectations:
- [ ] Typically 1-5 (well-studied mathematical foundations)
- [ ] Blind deconvolution / blind calibration: 5-10 (Hard)
- [ ] Standard compressed sensing: 1-3

---

## V4 — L2 Spec JSON

Same checks as agent-imaging V5, plus:

- [ ] epsilon_fn uses signal-appropriate units (SNR_dB, NMSE — NOT PSNR)
- [ ] Spec 1 (blind deconvolution/separation): Ω = filter/system uncertainty
- [ ] Spec 2 (known-filter inversion): oracle filter; focus on noise robustness
- [ ] Baseline SNRs in range 20-35 dB for Standard difficulty
- [ ] d(Ω_centroid) ∈ [0.3, 0.7]
- [ ] d_spec ≥ 0.15

**epsilon_fn evaluation:**
```python
from pwm_scoring.epsilon import eval_epsilon
# Test with signal-relevant Ω values
result = eval_epsilon(eps_fn, {"SNR": 30, "bandwidth": 1000, "sampling_rate": 4000})
assert isinstance(result, float) and result > 0
```

---

## V5 — L3 Benchmark JSON

Same checks as agent-imaging V6, plus:

### I-benchmark tier descriptions (signal-specific):
| Tier | Signal Meaning | ρ |
|---|---|---|
| T1 nominal | Standard SNR, well-calibrated | 1 |
| T2 low | High SNR (easier) | 3 |
| T3 moderate | Medium SNR + mild calibration mismatch | 5 |
| T4 hard | Low SNR or large calibration mismatch (blind) | 10 |

### Baselines (signal processing solvers):
- [ ] At least 2 from: LASSO, OMP, Wiener filter, MUSIC/ESPRIT, Tikhonov, iterative NMF
- [ ] No baseline passes epsilon everywhere (hardness rule)

### P-benchmark:
- [ ] Real measurement dataset from: PhysioNet (ECG/EEG), MNIST audio, NMR FID, acoustic
- [ ] ρ = 50

---

## V6 — Self-Review (12-Point Checklist)

1. [ ] P = (E, G, W, C) quadruple complete
2. [ ] physics_fingerprint complete (7 fields)
3. [ ] spec_range, ibenchmark_range complete
4. [ ] epsilon_fn evaluates for 10 random Ω
5. [ ] Hardness rule: no baseline passes epsilon everywhere
6. [ ] d_spec ≥ 0.15
7. [ ] d_ibench ≥ 0.10
8. [ ] Tier spacing ≥ 10% in ≥ 1 Ω dimension
9. [ ] All JSON fields present, correctly typed
10. [ ] forward_model L1 matches L2 E
11. [ ] difficulty_delta consistent with L_DAG
12. [ ] P1-P10 physics tests PASS

---

## V7 — Cross-Agent Consistency

- [ ] Domain folders K, L, AD are assigned to signal only
- [ ] M, N, O, P are NOT present (belong to agent-imaging)
- [ ] No overlap with imaging (A-J, M-P), physics (R-W, AA-AB), chemistry (X-Z, AL, AN), or applied (Q, AC, AE-AO)
- [ ] Principle IDs globally unique

---

## V8 — Batch Validation Script

```python
import json, glob, os

errors = []
domains = {}
VALID_DELTAS = {1, 3, 5, 10, 50}
FP_KEYS = {"carrier", "sensing_mechanism", "integration_axis",
           "problem_class", "noise_model", "solution_space", "primitives"}

for f in sorted(glob.glob("principles/*/L1-*.json")):
    domain = os.path.basename(os.path.dirname(f))
    domains.setdefault(domain, 0)
    domains[domain] += 1
    data = json.load(open(f))

    for key in ["forward_model", "dag", "well_posedness", "convergence"]:
        if key not in data:
            errors.append(f"{f}: missing {key}")

    if data.get("layer") != 1:
        errors.append(f"{f}: layer != 1")

    fp = data.get("physics_fingerprint", {})
    missing_fp = FP_KEYS - set(fp.keys())
    if missing_fp:
        errors.append(f"{f}: missing fingerprint fields: {missing_fp}")

    delta = data.get("difficulty_delta")
    if delta not in VALID_DELTAS:
        errors.append(f"{f}: invalid difficulty_delta={delta}")

    # Signal-specific: error_metric should be SNR/NMSE, not PSNR
    metric = data.get("error_metric", {}).get("primary", "")
    if metric == "PSNR":
        errors.append(f"{f}: signal problem should use SNR_dB/NMSE, not PSNR")

    # Signal-specific: domains M/N/O/P should not appear
    if domain.startswith(("M_", "N_", "O_", "P_")):
        errors.append(f"{f}: domain {domain} belongs to agent-imaging, not signal")

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
