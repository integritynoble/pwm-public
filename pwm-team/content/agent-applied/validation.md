# agent-applied: Validation Checklist

Run every check below before merging the applied sciences principles PR. Follows the same L1/L2/L3 structure as all content agents.

---

## V1 — Domain Coverage

| Domain Folder | Expected Principles | Delivered? |
|---|---|---|
| Q_astronomy | ~4 | [ ] |
| AC_astrophysics | ~18 | [ ] |
| AE_computational_biology | ~18 | [ ] |
| AF_environmental_science | ~12 | [ ] |
| AG_control_theory | ~12 | [ ] |
| AH_computational_finance | ~8 | [ ] |
| AI_robotics | ~12 | [ ] |
| AJ_petroleum | ~8 | [ ] |
| AK_geodesy | ~8 | [ ] |
| AM_particle_physics | ~8 | [ ] |
| AO_optimization | ~3 | [ ] |
| **Total** | **~111** | [ ] |

**Verify folder names are canonical:**
```bash
ls pwm-team/content/agent-applied/principles/ | sort
# Must include AE_computational_biology (not AE_computational_bio)
# Must include AF_environmental_science (not AF_environmental_sci)
# Must include AH_computational_finance (not AH_comp_finance)
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

Same structural checks as agent-imaging V3. Applied-science-specific additions:

### Forward Model (E) — domain-dependent:
| Domain | Typical Forward Model |
|---|---|
| AC_astrophysics | y = PSF * x + noise (deconvolution) |
| Q_astronomy | y = orbit_model(x, t) + noise |
| AE_computational_biology | y = H · x + n (structure from measurements) |
| AF_environmental_science | y = transport(x, params) + noise |
| AG_control_theory | y = g(x, u) + v (state estimation) |
| AH_computational_finance | y = F(theta) + epsilon (parameter calibration) |
| AI_robotics | y = sensor_model(state) + noise (SLAM) |
| AJ_petroleum | y = seismic_forward(subsurface) + noise |
| AK_geodesy | y = geometric_model(position) + noise |
| AM_particle_physics | y = detector_response(particles) + noise |
| AO_optimization | y = objective(x) (abstract) |

- [ ] world_state_x: physically meaningful for domain
- [ ] observation_y: realistic measurement type
- [ ] physical_parameters_theta: domain-relevant parameters

### Non-physical forward models:
- [ ] Finance, control theory, optimization: expressed as mathematical operators (no physical carrier)
- [ ] carrier = "N/A" is acceptable for these domains

### Physics fingerprint carrier types:
| Domain | Expected Carrier |
|---|---|
| Q_astronomy | "Photon" |
| AC_astrophysics | "Photon" |
| AE_computational_biology | "Photon", "Electron", "X-ray" |
| AF_environmental_science | "Acoustic", "RF" |
| AG_control_theory | "N/A" |
| AH_computational_finance | "N/A" |
| AI_robotics | "Photon", "Acoustic", "RF" |
| AJ_petroleum | "Acoustic" (seismic) |
| AK_geodesy | "RF" |
| AM_particle_physics | "Particle" |
| AO_optimization | "N/A" |

### error_metric (domain-specific):
| Domain | Expected Metric |
|---|---|
| AC_astrophysics | "PSNR" (imaging) or "magnitude_error" |
| AE_computational_biology | "TM_score", "sequence_identity", "RMSD_angstrom" |
| AF_environmental_science | "RMSE", "relative_L2" |
| AG_control_theory | "tracking_error", "RMSE" |
| AH_computational_finance | "MAE", "relative_error" |
| AI_robotics | "position_error_m", "RMSE" |
| AJ_petroleum | "relative_L2" (same as geophysics) |
| AK_geodesy | "position_error_m" |
| AM_particle_physics | "energy_resolution_GeV" |
| AO_optimization | "objective_gap" |

### difficulty_delta expectations:
| Domain | Expected δ Range |
|---|---|
| Q_astronomy | 3 (Standard) |
| AC_astrophysics | 3-5 (PSF Standard-Challenging), 50 (gravitational lensing Frontier) |
| AE_computational_biology | 5-50 (protein folding Frontier) |
| AF_environmental_science | 5 (Challenging) |
| AG_control_theory | 3-5 (clean math, Standard-Challenging) |
| AH_computational_finance | 5-10 (Challenging-Hard) |
| AI_robotics | 5-10 (SLAM Challenging-Hard) |
| AJ_petroleum | 10 (seismic, same as geophysics) |
| AK_geodesy | 3-10 (GPS Standard, ionosphere Hard) |
| AM_particle_physics | 5-50 (jet Challenging, neutrino mass Frontier) |
| AO_optimization | 1-3 (consult agent-coord) |

---

## V4 — L2 Spec JSON

Same checks as agent-imaging V5, plus:

- [ ] epsilon_fn uses domain-appropriate units (km for geodesy, relative for finance, PSNR for astrophysics)
- [ ] Spec 1 (nominal inversion): well-characterized system
- [ ] Spec 2 (mismatch-robust): model mismatch in Ω
- [ ] d(Ω_centroid) ∈ [0.3, 0.7]
- [ ] d_spec ≥ 0.15

---

## V5 — L3 Benchmark JSON

Same checks as agent-imaging V6, plus:

### I-benchmark tiers (applied-specific):
| Tier | Meaning | ρ |
|---|---|---|
| T1 nominal | Standard conditions, good SNR, low mismatch | 1 |
| T2 low | Easiest regime, clean data, simple model | 3 |
| T3 moderate | Real-world noise, mild mismatch | 5 |
| T4 hard | Low SNR, large mismatch, real artifacts | 10 |

### Baselines (domain-specific):
| Domain | Expected Baseline Solvers |
|---|---|
| AC_astrophysics | CLEAN, Richardson-Lucy |
| AE_computational_biology | Gaussian network model, normal mode analysis |
| AF_environmental_science | Kalman filter, adjoint method |
| AG_control_theory | LQR, H-infinity, pole placement |
| AH_computational_finance | Black-Scholes calibration, MCMC |
| AI_robotics | EKF, UKF, particle filter |
| AJ_petroleum | Kirchhoff migration, RTM |
| AK_geodesy | least-squares, Bayesian |
| AM_particle_physics | template matching, neural net |
| AO_optimization | gradient descent, Newton |

- [ ] At least 2 baselines per benchmark
- [ ] No baseline passes epsilon everywhere (hardness rule)

### P-benchmark (domain-specific real data):
| Domain | Expected Data Sources |
|---|---|
| AC_astrophysics | HST, JWST, Sloan DSS |
| AE_computational_biology | PDB, cryo-EM EMDB |
| AF_environmental_science | ERA5 reanalysis, MODIS |
| AH_computational_finance | Yahoo Finance, FRED |
| AI_robotics | KITTI, TUM RGBD |
| AJ_petroleum | SEG/EAGE models |
| AK_geodesy | IGS GNSS data |

- [ ] ρ = 50 for all P-benchmarks

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

- [ ] Domain folders Q, AC, AE, AF, AG, AH, AI, AJ, AK, AM, AO are assigned to applied only
- [ ] AJ_petroleum (seismic inversion) overlap with agent-physics W_geophysics flagged to agent-coord
- [ ] AO_optimization (3 principles) — agent-coord consulted for appropriate difficulty_delta
- [ ] No overlap with imaging (A-P), physics (R-W, AA-AB), chemistry (X-Z, AL, AN), or signal (K, L, AD)
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

# Domains where carrier = "N/A" is acceptable
NA_CARRIER_DOMAINS = {"AG_control_theory", "AH_computational_finance", "AO_optimization"}

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

    # Applied-specific: verify carrier is reasonable for domain
    carrier = fp.get("carrier", "")
    if carrier == "N/A" and domain not in NA_CARRIER_DOMAINS:
        errors.append(f"{f}: carrier='N/A' unexpected for domain {domain}")

    # Check error_metric is domain-appropriate
    metric = data.get("error_metric", {}).get("primary", "")
    if domain == "AE_computational_biology" and metric == "PSNR":
        errors.append(f"{f}: bio domain should use TM_score/RMSD, not PSNR")

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

## V9 — Overlap Detection

### AJ_petroleum vs W_geophysics:
```python
# Compare AJ principles against W principles for duplicates
import json, glob

aj_models = {}
for f in glob.glob("principles/AJ_petroleum/L1-*.json"):
    data = json.load(open(f))
    aj_models[data["title"]] = data["forward_model"]["equation"]

# Load W_geophysics from agent-physics
w_models = {}
for f in glob.glob("../../agent-physics/principles/W_geophysics/L1-*.json"):
    data = json.load(open(f))
    w_models[data["title"]] = data["forward_model"]["equation"]

# Flag any matching forward models
for title, eq in aj_models.items():
    for w_title, w_eq in w_models.items():
        if eq == w_eq:
            print(f"DUPLICATE: AJ '{title}' matches W '{w_title}'")
```

- [ ] No exact duplicate forward models between AJ_petroleum and W_geophysics
- [ ] Any near-duplicates flagged to agent-coord for resolution
