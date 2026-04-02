# Principle #304 — Semiempirical Quantum Chemistry (AM1, GFN-xTB)

**Domain:** Computational Chemistry | **Carrier:** N/A (approx. QM) | **Difficulty:** Standard (δ=3)
**DAG:** E.hermitian → N.xc → L.sparse |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          E.hermitian→N.xc→L.sparse      semiempi    heats-of-form     SCF-SE
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SEMIEMPIRICAL QC (AM1,GFN-xTB)  P = (E,G,W,C)   Principle #304│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ H_SE = H_core + Σ γ_AB(ρ)  (parametrised Hamiltonian) │
│        │ AM1/PM6: NDDO approximation; GFN-xTB: tight-binding   │
│        │ Parameters fit to reproduce exp. heats of formation    │
│        │ Forward: given geometry → E_SE, gradient, properties   │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [E.hermitian] ──→ [N.xc] ──→ [L.sparse]                │
│        │ eigensolve  nonlinear  linear-op                       │
│        │ V={E.hermitian, N.xc, L.sparse}  A={E.hermitian→N.xc, N.xc→L.sparse}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (SCF with parametrised integrals)       │
│        │ Uniqueness: YES for closed-shell ground state           │
│        │ Stability: fast SCF convergence; linear-scaling xTB    │
│        │ Mismatch: parameter transferability, non-covalent int. │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |ΔH_f,SE − ΔH_f,exp| (kcal/mol)                  │
│        │ q = 1.0–2.0 (N¹-N² scaling)                          │
│        │ T = {heat_of_formation, geometry_RMSD, IP_error}       │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | NDDO/TB Hamiltonian well-defined; dimensions consistent | PASS |
| S2 | Parametrisation covers H, C, N, O, S, P, halogens | PASS |
| S3 | SCF converges in <30 cycles for organic molecules up to 500 atoms | PASS |
| S4 | ΔH_f MAE < 8 kcal/mol (PM6), geometry RMSD < 0.05 A (xTB) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# semiempi/hof_s1_ideal.yaml
principle_ref: sha256:<p304_hash>
omega:
  molecules: 1000
  max_atoms: 200
  method: GFN2-xTB
E:
  forward: "GFN2-xTB tight-binding SCF"
  convergence: 1.0e-6  # Hartree
  max_cycles: 50
B:
  dispersion: D4
  solvent: none  # gas phase
I:
  scenario: GMTKN55_subset
  properties: [energy, geometry, non_covalent]
  reference: CCSD(T)/CBS
O: [energy_MAE, geometry_RMSD, NCI_MAE]
epsilon:
  energy_MAE_max: 10.0  # kcal/mol
  geom_RMSD_max: 0.05  # Angstrom
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | GFN2-xTB covers all elements up to Z=86; 1000 molecules | PASS |
| S2 | D4 dispersion correction improves NCI description | PASS |
| S3 | SCF converges in <20 cycles for typical organics | PASS |
| S4 | Energy MAE < 10 kcal/mol; geometry RMSD < 0.05 A | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# semiempi/benchmark_gmtkn.yaml
spec_ref: sha256:<spec304_hash>
principle_ref: sha256:<p304_hash>
dataset:
  name: GMTKN55_subset_1000
  reference: "Goerigk et al. (2017) GMTKN55"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: AM1
    params: {method: AM1}
    results: {energy_MAE: 12.5, geom_RMSD: 0.08}
  - solver: PM6
    params: {method: PM6}
    results: {energy_MAE: 8.2, geom_RMSD: 0.06}
  - solver: GFN2-xTB
    params: {method: GFN2-xTB, D4: true}
    results: {energy_MAE: 6.5, geom_RMSD: 0.03}
quality_scoring:
  - {min_MAE: 3.0, Q: 1.00}
  - {min_MAE: 6.0, Q: 0.90}
  - {min_MAE: 10.0, Q: 0.80}
  - {min_MAE: 15.0, Q: 0.75}
```

**Baseline solver:** GFN2-xTB — MAE 6.5 kcal/mol
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | MAE (kcal/mol) | Geom RMSD (A) | Runtime | Q |
|--------|----------------|----------------|---------|---|
| AM1 | 12.5 | 0.08 | 0.5 s | 0.80 |
| PM6 | 8.2 | 0.06 | 0.5 s | 0.80 |
| GFN2-xTB | 6.5 | 0.03 | 1 s | 0.90 |
| GFN2-xTB + ORCA-DFT/3c | 2.5 | 0.02 | 30 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (xTB+DFT/3c): 300 × 1.00 = 300 PWM
Floor:                   300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p304_hash>",
  "h_s": "sha256:<spec304_hash>",
  "h_b": "sha256:<bench304_hash>",
  "r": {"residual_norm": 2.5, "error_bound": 10.0, "ratio": 0.25},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
  "Q": 1.00,
  "gate_verdicts": {"S1":"pass","S2":"pass","S3":"pass","S4":"pass"}
}
```

---

## Reward Summary

| Layer | Seed Reward | Ongoing Royalties |
|-------|-------------|-------------------|
| L1 Principle | 200 PWM | 5% of L4 mints |
| L2 spec.md | 105 PWM | 10% of L4 mints |
| L3 Benchmark | 60 PWM | 15% of L4 mints |
| L4 Solution | — | 225–300 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep semiempi
pwm-node verify semiempi/hof_s1_ideal.yaml
pwm-node mine semiempi/hof_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
