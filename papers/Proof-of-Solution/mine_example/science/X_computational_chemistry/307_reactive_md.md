# Principle #307 — Reactive MD (ReaxFF)

**Domain:** Computational Chemistry | **Carrier:** N/A (bond-order potential) | **Difficulty:** Hard (δ=5)
**DAG:** N.reaction → N.bilinear.pair → ∂.time.symplectic |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.reaction→N.bilinear.pair→∂.time.symplectic      reaxff-md   combustion-surf   LAMMPS
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  REACTIVE MD (ReaxFF)             P = (E,G,W,C)   Principle #307│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ E = E_bond(BO) + E_over + E_angle + E_tors + E_vdW    │
│        │     + E_Coul + E_conj + E_penalty                     │
│        │ BO_ij = exp[p_bo(r_ij/r₀)^p] (bond order)             │
│        │ Forward: given ReaxFF params → reactive trajectory     │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.reaction] ──→ [N.bilinear.pair] ──→ [∂.time.symplectic] │
│        │ nonlinear  nonlinear  derivative                       │
│        │ V={N.reaction, N.bilinear.pair, ∂.time.symplectic}  A={N.reaction→N.bilinear.pair, N.bilinear.pair→∂.time.symplectic}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (smooth potential, continuous bond form)│
│        │ Uniqueness: YES (deterministic ODE for given IC)       │
│        │ Stability: dt ≤ 0.25 fs due to bond-breaking events   │
│        │ Mismatch: training set bias, charge equilibration lag  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |E_ReaxFF − E_QM| / N_atoms (meV/atom)            │
│        │ q = 1.5 (charge equilibration adds N² cost)           │
│        │ T = {energy_error, bond_dissociation, product_yields}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Bond-order potential smooth; forces analytic; charge EQ converged | PASS |
| S2 | ReaxFF reproduces QM bond dissociation curves within 5 kcal/mol | PASS |
| S3 | LAMMPS reax/c converges with QEq every step; dt=0.25 fs stable | PASS |
| S4 | Energy error < 50 meV/atom vs DFT for training set | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# reaxff_md/combustion_s1_ideal.yaml
principle_ref: sha256:<p307_hash>
omega:
  atoms: 5000
  box: [40, 40, 40]  # Angstrom
  time: 1.0  # ns
  dt: 0.25  # fs
E:
  forward: "ReaxFF bond-order reactive potential"
  force_field: CHO_2008
  charge_eq: QEq
  QEq_tolerance: 1.0e-6
B:
  ensemble: NVT
  temperature: 2500  # K
  thermostat: Nose-Hoover
I:
  scenario: hydrocarbon_oxidation
  fuel: C8H18  # octane
  oxidiser: O2
  equivalence_ratio: 1.0
O: [product_yield_CO2, product_yield_H2O, ignition_time]
epsilon:
  yield_error_max: 0.10  # relative
  ignition_error_max: 0.20
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | CHO ReaxFF covers C, H, O; 5000 atoms adequate for statistics | PASS |
| S2 | ReaxFF CHO validated for combustion products at 2500 K | PASS |
| S3 | 1 ns NVT with QEq converges; bond-breaking events tracked | PASS |
| S4 | CO2/H2O yields within 10% of DFT-MD reference | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# reaxff_md/benchmark_combustion.yaml
spec_ref: sha256:<spec307_hash>
principle_ref: sha256:<p307_hash>
dataset:
  name: octane_oxidation_ReaxFF
  reference: "Chenoweth et al. (2008) CHO combustion"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: ReaxFF-CHO-2008
    params: {dt: 0.25fs, T: 2500K}
    results: {CO2_yield_err: 0.12, H2O_yield_err: 0.08}
  - solver: ReaxFF-CHO-2016
    params: {dt: 0.25fs, T: 2500K}
    results: {CO2_yield_err: 0.08, H2O_yield_err: 0.06}
  - solver: DFTB-MD
    params: {dt: 0.5fs, T: 2500K}
    results: {CO2_yield_err: 0.05, H2O_yield_err: 0.04}
quality_scoring:
  - {min_yield_err: 0.03, Q: 1.00}
  - {min_yield_err: 0.06, Q: 0.90}
  - {min_yield_err: 0.10, Q: 0.80}
  - {min_yield_err: 0.20, Q: 0.75}
```

**Baseline solver:** ReaxFF-CHO-2016 — CO2 yield error 8%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | CO2 Yield Err | H2O Yield Err | Runtime | Q |
|--------|---------------|---------------|---------|---|
| ReaxFF-2008 | 0.12 | 0.08 | 12 h | 0.80 |
| ReaxFF-2016 | 0.08 | 0.06 | 12 h | 0.90 |
| DFTB-MD | 0.05 | 0.04 | 96 h | 0.90 |
| ReaxFF-refit+ML | 0.025 | 0.02 | 15 h | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (refit+ML): 500 × 1.00 = 500 PWM
Floor:                500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p307_hash>",
  "h_s": "sha256:<spec307_hash>",
  "h_b": "sha256:<bench307_hash>",
  "r": {"residual_norm": 0.025, "error_bound": 0.10, "ratio": 0.25},
  "c": {"fitted_rate": 1.52, "theoretical_rate": 1.5, "K": 4},
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
| L4 Solution | — | 375–500 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep reaxff_md
pwm-node verify reaxff_md/combustion_s1_ideal.yaml
pwm-node mine reaxff_md/combustion_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
