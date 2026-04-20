# agent-physics: Validation Checklist

Run every check below before merging the physics principles PR. Follows the same L1/L2/L3 structure as all content agents.

---

## V1 — Domain Coverage

| Domain Folder | Expected Principles | Delivered? |
|---|---|---|
| R_fluid_dynamics | ~25 | [ ] |
| S_heat_transfer | ~12 | [ ] |
| T_structural_mechanics | ~26 | [ ] |
| U_electromagnetics | ~25 | [ ] |
| V_acoustics | ~15 | [ ] |
| W_geophysics | ~22 | [ ] |
| AA_plasma_physics | ~12 | [ ] |
| AB_nuclear_engineering | ~10 | [ ] |
| **Total** | **~147** | [ ] |

**Verify folder names are canonical:**
```bash
ls pwm-team/content/agent-physics/principles/ | sort
# Must include AB_nuclear_engineering (not AB_nuclear_radiation)
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
# L1=L2=L3 per domain
```

---

## V3 — L1 Principle JSON (P = (E, G, W, C))

Same structural checks as agent-imaging V3. Physics-specific additions:

### Forward Model (E):
- [ ] PDE or governing equation expressed correctly (e.g., `∂u/∂t = ν∇²u + f`)
- [ ] world_state_x: velocity field, temperature field, displacement, stress, etc.
- [ ] observation_y: sensor measurements, probes, boundary measurements
- [ ] physical_parameters_theta: viscosity, density, conductivity, Young's modulus, etc.

### DAG (G) patterns:
- [ ] FWI: forward → adjoint → gradient (for seismic/wave problems)
- [ ] PDE solvers: discretise → solve → invert
- [ ] Modal decomposition: decompose → filter → reconstruct

### Well-posedness (W):
- [ ] Many PDE inverses are ill-posed: existence=true, uniqueness=false, stability="unstable"
- [ ] Verify stability field matches known mathematical properties of the forward model
- [ ] condition_number provided (may be very large for ill-posed problems)

### Convergence (C):
- [ ] convergence_rate_q: 2.0 for FEM/FDM, 1.0 for some spectral methods
- [ ] solver_class matches well-posedness (no direct inversion for non-unique problems)

### Physics fingerprint carrier types:
| Domain | Expected Carrier |
|---|---|
| R_fluid_dynamics | "Acoustic" or "N/A" |
| S_heat_transfer | "Thermal" |
| T_structural_mechanics | "Mechanical" |
| U_electromagnetics | "Electromagnetic" |
| V_acoustics | "Acoustic" |
| W_geophysics | "Acoustic" (seismic) |
| AA_plasma_physics | "Plasma" |
| AB_nuclear_engineering | "Neutron" |

### error_metric:
- [ ] Primary: typically "RMSE" or "relative_L2" (NOT PSNR for PDE problems)
- [ ] Verify units are consistent with world_state_x

### difficulty_delta expectations:
| Domain | Expected δ Range |
|---|---|
| S_heat_transfer | 1-5 (unique solutions common) |
| T_structural_mechanics | 3-5 |
| R_fluid_dynamics | 5-10 (chaotic sensitivity) |
| W_geophysics (seismic FWI) | 10-50 (highly non-unique, frontier) |
| AB_nuclear_engineering | 5-10 |

---

## V4 — L2 Spec JSON

Same checks as agent-imaging V5, plus:

- [ ] epsilon_fn uses units consistent with error_metric (e.g., relative_L2, not PSNR)
- [ ] Spec 1 (mismatch-only): Ω includes uncertain physical parameters (viscosity range, conductivity range, etc.)
- [ ] Spec 2 (oracle-assisted): true parameters provided, focus on numerical solver accuracy
- [ ] d(Ω_centroid) ∈ [0.3, 0.7]
- [ ] d_spec ≥ 0.15 from other specs under same principle

**epsilon_fn evaluation:**
```python
from pwm_scoring.epsilon import eval_epsilon
# Test with physics-relevant Ω values
result = eval_epsilon(eps_fn, {"Re": 1000, "mesh_h": 0.01})
assert isinstance(result, float) and result > 0
```

---

## V5 — L3 Benchmark JSON

Same checks as agent-imaging V6, plus:

### I-benchmark tier descriptions (physics-specific):
| Tier | Physics Meaning | ρ |
|---|---|---|
| T1 nominal | Standard conditions | 1 |
| T2 low | Coarse mesh, low Re/Rayleigh | 3 |
| T3 moderate | Medium resolution, moderate turbulence | 5 |
| T4 hard | Fine mesh, turbulent/high-Ra, real noise | 10 |

### Baselines (physics solvers):
- [ ] At least 2 from: FEM, FDM, spectral, PINN, FNO, Tikhonov, adjoint
- [ ] No baseline passes epsilon everywhere (hardness rule)
- [ ] Baseline expected PSNR/RMSE values are physically reasonable

### P-benchmark:
- [ ] Real simulation data (OpenFOAM, FEniCS, COMSOL) or experimental data
- [ ] ρ = 50

---

## V6 — Self-Review (12-Point Checklist)

Same as agent-imaging V7. Run for every principle:

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

- [ ] Domain folders R, S, T, U, V, W, AA, AB are assigned to physics only
- [ ] No overlap with imaging (A-P), chemistry (X, Y, Z, AL, AN), signal (K, L, AD), or applied (Q, AC, AE-AO)
- [ ] W_geophysics may overlap with agent-applied AJ_petroleum (seismic inversion) — flag duplicates to agent-coord
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

    # Physics-specific: check error_metric is not PSNR
    metric = data.get("error_metric", {}).get("primary", "")
    if metric == "PSNR":
        errors.append(f"{f}: PDE problem should use RMSE/relative_L2, not PSNR")

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
