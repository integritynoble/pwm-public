# Principle #306 — Coarse-Grained MD (Martini)

**Domain:** Computational Chemistry | **Carrier:** N/A (CG dynamics) | **Difficulty:** Standard (δ=3)
**DAG:** N.bilinear.pair → ∂.time.symplectic → ∫.ensemble |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.bilinear.pair→∂.time.symplectic→∫.ensemble      cg-md       lipid-membrane    Martini
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  COARSE-GRAINED MD (MARTINI)      P = (E,G,W,C)   Principle #306│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ U_CG = Σ V_bond + Σ V_angle + Σ V_LJ(σ,ε)            │
│        │ 4:1 mapping (4 heavy atoms → 1 CG bead)               │
│        │ Martini parameters from partitioning free energies     │
│        │ Forward: given CG topology → mesoscale trajectory      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.bilinear.pair] ──→ [∂.time.symplectic] ──→ [∫.ensemble] │
│        │ nonlinear  derivative  integrate                       │
│        │ V={N.bilinear.pair, ∂.time.symplectic, ∫.ensemble}  A={N.bilinear.pair→∂.time.symplectic, ∂.time.symplectic→∫.ensemble}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (ODE with CG potential)                │
│        │ Uniqueness: mapping many-to-one; representability issue│
│        │ Stability: dt up to 20 fs; dynamics ~4× faster         │
│        │ Mismatch: lost atomistic detail, entropy compensation  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |APL_CG − APL_exp| / APL_exp (area per lipid)     │
│        │ q = 1.0 (same Verlet algorithm, fewer particles)      │
│        │ T = {area_per_lipid, bilayer_thickness, lateral_D}     │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | CG mapping consistent; bead types cover lipids, proteins, water | PASS |
| S2 | Martini parameterised against experimental partition free energies | PASS |
| S3 | GROMACS with Martini converges for DPPC bilayer in μs timescale | PASS |
| S4 | Area per lipid within 3% of experiment for DPPC at 323 K | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# cg_md/membrane_s1_ideal.yaml
principle_ref: sha256:<p306_hash>
omega:
  lipids: 512  # DPPC
  water_beads: 6000
  box: [12, 12, 10]  # nm
  time: 10.0  # μs
  dt: 20  # fs
E:
  forward: "Martini 3 CG force field"
  cutoff: 1.1  # nm
  electrostatics: reaction_field
B:
  ensemble: NPT
  temperature: 323  # K
  pressure: 1.0  # bar
  semi_isotropic: true
I:
  scenario: DPPC_bilayer_323K
  reference_APL: 0.64  # nm²
  reference_thickness: 3.85  # nm
O: [APL_error, thickness_error, lateral_diffusion]
epsilon:
  APL_error_max: 0.03  # relative
  thickness_error_max: 0.05  # relative
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 512 DPPC lipids in bilayer; dt=20 fs stable with Martini | PASS |
| S2 | Semi-isotropic NPT maintains correct bilayer tension | PASS |
| S3 | 10 μs trajectory yields converged APL and thickness | PASS |
| S4 | APL error < 3% of experimental 0.64 nm² | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# cg_md/benchmark_dppc.yaml
spec_ref: sha256:<spec306_hash>
principle_ref: sha256:<p306_hash>
dataset:
  name: DPPC_bilayer_experiment
  reference: "Nagle & Tristram-Nagle (2000) structural data"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Martini-2.2
    params: {dt: 20fs, time: 1us}
    results: {APL_error: 0.04, thickness_error: 0.06}
  - solver: Martini-3.0
    params: {dt: 20fs, time: 1us}
    results: {APL_error: 0.02, thickness_error: 0.03}
  - solver: CHARMM-CG
    params: {dt: 10fs, time: 1us}
    results: {APL_error: 0.03, thickness_error: 0.04}
quality_scoring:
  - {min_APL_err: 0.01, Q: 1.00}
  - {min_APL_err: 0.02, Q: 0.90}
  - {min_APL_err: 0.04, Q: 0.80}
  - {min_APL_err: 0.08, Q: 0.75}
```

**Baseline solver:** Martini-3.0 — APL error 2%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | APL Error | Thick. Error | Runtime | Q |
|--------|-----------|-------------|---------|---|
| Martini-2.2 | 0.04 | 0.06 | 2 h | 0.80 |
| CHARMM-CG | 0.03 | 0.04 | 4 h | 0.80 |
| Martini-3.0 | 0.02 | 0.03 | 2 h | 0.90 |
| Martini-3.0 (long) | 0.008 | 0.01 | 20 h | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (long Martini3): 300 × 1.00 = 300 PWM
Floor:                     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p306_hash>",
  "h_s": "sha256:<spec306_hash>",
  "h_b": "sha256:<bench306_hash>",
  "r": {"residual_norm": 0.008, "error_bound": 0.03, "ratio": 0.27},
  "c": {"fitted_rate": 1.02, "theoretical_rate": 1.0, "K": 3},
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
pwm-node benchmarks | grep cg_md
pwm-node verify cg_md/membrane_s1_ideal.yaml
pwm-node mine cg_md/membrane_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
