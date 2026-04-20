# agent-chemistry: Validation Checklist

Run every check below before merging the chemistry principles PR. Follows the same L1/L2/L3 structure as all content agents.

---

## V1 — Domain Coverage

| Domain Folder | Expected Principles | Delivered? |
|---|---|---|
| X_computational_chemistry | ~18 | [ ] |
| Y_quantum_mechanics | ~15 | [ ] |
| Z_materials_science | ~15 | [ ] |
| AL_polymer_physics | ~6 | [ ] |
| AN_semiconductor | ~10 | [ ] |
| **Total** | **~64** | [ ] |

**Verify folder names are canonical:**
```bash
ls pwm-team/content/agent-chemistry/principles/ | sort
# Must include X_computational_chemistry (not X_comp_chemistry)
# Must include AL_polymer_physics (not AL_polymer_science)
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

Same structural checks as agent-imaging V3. Chemistry-specific additions:

### Forward Model (E):
- [ ] Schrödinger equation, DFT functional, force field, or molecular dynamics equation
- [ ] world_state_x: molecular geometry, electron density, atomic positions, wavefunction
- [ ] observation_y: NMR spectrum, XRD pattern, absorption spectrum, binding energy
- [ ] physical_parameters_theta: XC functional, force field params, basis set, cutoff energy

### DAG (G) patterns:
- [ ] DFT: potential → Hamiltonian → eigensolve → density
- [ ] Molecular dynamics: force → integrate → observable
- [ ] Scattering: incident → scatter → detect

### Well-posedness (W):
- [ ] Quantum mechanics: often non-unique (phase ambiguity), unstable (decoherence)
- [ ] Crystal structure from XRD: phase problem → uniqueness=false
- [ ] DFT self-consistency: conditional stability

### Convergence (C):
- [ ] convergence_rate_q: 2.0 for FEM/basis set; varies for iterative SCF
- [ ] solver_class: "iterative" for SCF, "direct" for small systems

### Physics fingerprint carrier types:
| Domain | Expected Carrier |
|---|---|
| X_computational_chemistry | "Electron" or "Photon" |
| Y_quantum_mechanics | "Electron" |
| Z_materials_science | "Photon" or "Phonon" |
| AL_polymer_physics | "Photon" or "Ion" |
| AN_semiconductor | "Electron" or "Phonon" |

### error_metric (CRITICAL — NOT PSNR):
- [ ] Primary: `"energy_error_eV"`, `"structure_RMSD_angstrom"`, `"spectral_distance"`, or `"MAE_eV"`
- [ ] NEVER "PSNR" for chemistry problems
- [ ] Units must be physically meaningful for the observable

### difficulty_delta expectations:
| Domain | Expected δ Range |
|---|---|
| Z_materials_science (crystal from XRD) | 5-10 (phase ambiguity) |
| X_computational_chemistry (structure from spectra) | 5+ (non-unique) |
| Y_quantum_mechanics (wavefunction reconstruction) | 5-50 (decoherence, non-convex) |
| AL_polymer_physics (chain from rheology) | 3-5 |
| AN_semiconductor (doping inversion) | 5 |

---

## V4 — L2 Spec JSON

Same checks as agent-imaging V5, plus:

- [ ] epsilon_fn uses chemistry-appropriate units (eV, Å, spectral overlap — NOT dB or PSNR)
- [ ] Spec 1 (structure-to-property inversion): reconstruct molecular structure from spectrum
- [ ] Spec 2 (parameter inversion): identify force field / XC parameters from observables
- [ ] d(Ω_centroid) ∈ [0.3, 0.7]
- [ ] d_spec ≥ 0.15

**epsilon_fn evaluation:**
```python
from pwm_scoring.epsilon import eval_epsilon
# Test with chemistry-relevant Ω values
result = eval_epsilon(eps_fn, {"N_atoms": 50, "basis_size": 100})
assert isinstance(result, float) and result > 0
```

---

## V5 — L3 Benchmark JSON

Same checks as agent-imaging V6, plus:

### I-benchmark tier descriptions (chemistry-specific):
| Tier | Chemistry Meaning | ρ |
|---|---|---|
| T1 nominal | Small molecule / simple crystal | 1 |
| T2 low | Slightly larger system | 3 |
| T3 moderate | Medium (50-atom cluster) | 5 |
| T4 hard | Large/complex (protein fragment, disordered alloy) | 10 |

### Baselines (chemistry solvers):
- [ ] At least 2 from: HF, DFT-B3LYP, PM6, XTBGFN2, classical FF, DFTB, ML-FF (SchNet, DimeNet)
- [ ] No baseline passes epsilon everywhere (hardness rule)
- [ ] Baseline error values physically reasonable (e.g., DFT error ~0.1 eV for organics)

### P-benchmark:
- [ ] Real experimental or high-quality computed data from: QM9, Materials Project, NIST, CSD, PDB
- [ ] ρ = 50

---

## V6 — Self-Review (12-Point Checklist)

Same as agent-imaging V7 plus:
- [ ] error_metric uses domain-appropriate units (eV, Å, not PSNR)

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

- [ ] Domain folders X, Y, Z, AL, AN are assigned to chemistry only
- [ ] No overlap with imaging (A-P), physics (R-W, AA-AB), signal (K, L, AD), or applied (Q, AC, AE-AO)
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

    # Chemistry-specific: error_metric should NOT be PSNR
    metric = data.get("error_metric", {}).get("primary", "")
    if metric == "PSNR":
        errors.append(f"{f}: chemistry problem should use eV/Å/spectral metric, not PSNR")

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
