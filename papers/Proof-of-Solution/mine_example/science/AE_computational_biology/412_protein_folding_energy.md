# Principle #412 — Protein Folding Energy

**Domain:** Computational Biology | **Carrier:** conformational energy | **Difficulty:** Advanced (δ=5)
**DAG:** N.bilinear.pair → ∫.volume → O.l2 |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          N.bilinear.pair→∫.volume→O.l2   fold-energy   decoy-scoring     forcefield
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  PROTEIN FOLDING ENERGY         P = (E,G,W,C)   Principle #412  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ U = Σ_bonds K_b(r−r₀)² + Σ_angles K_θ(θ−θ₀)²        │
│        │   + Σ_dihed K_φ[1+cos(nφ−δ)]                          │
│        │   + Σ_{i<j} [A_ij/r¹² − B_ij/r⁶ + q_iq_j/(4πεr)]   │
│        │ U = total potential energy of protein conformation      │
│        │ Forward: given coordinates {r_i} → U, ∇U              │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.bilinear.pair] ──→ [∫.volume] ──→ [O.l2]            │
│        │ nonlinear  integrate  optimize                         │
│        │ V={N.bilinear.pair, ∫.volume, O.l2}  A={N.bilinear.pair→∫.volume, ∫.volume→O.l2}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (energy function bounded below)         │
│        │ Uniqueness: NO (exponentially many local minima)       │
│        │ Stability: native state is thermodynamic minimum       │
│        │ Mismatch: force field parametrization, solvent model   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = RMSD to native structure (after energy minimization)│
│        │ q = N/A (combinatorial optimization)                  │
│        │ T = {RMSD, GDT_TS, TM_score, energy_gap}              │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Coordinate and force field parameter dimensions consistent | PASS |
| S2 | Energy function smooth and bounded below — minimizers exist | PASS |
| S3 | L-BFGS, steepest descent, or MD-based minimization converge | PASS |
| S4 | RMSD and GDT_TS computable against PDB native structures | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# protein_folding/decoy_scoring_s1_ideal.yaml
principle_ref: sha256:<p412_hash>
omega:
  protein_size: 100   # residues
  force_field: AMBER_ff14SB
  solvent: implicit_GB
E:
  forward: "U = bonded + LJ + Coulomb + solvation"
  nonbonded_cutoff: 12.0   # Angstrom
B:
  initial: {structure: extended_chain}
I:
  scenario: decoy_discrimination
  decoy_sets: [Rosetta, I-TASSER, random]
  n_decoys: 1000
O: [native_rank, RMSD_best, energy_gap]
epsilon:
  native_rank: 1   # native should rank #1
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 100-residue protein tractable; AMBER ff14SB well-validated | PASS |
| S2 | Energy function differentiable — gradient-based minimization works | PASS |
| S3 | L-BFGS converges to local minimum from each decoy | PASS |
| S4 | Native rank = 1 achievable with good force field + solvation | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# protein_folding/benchmark_decoy.yaml
spec_ref: sha256:<spec412_hash>
principle_ref: sha256:<p412_hash>
dataset:
  name: CASP_decoy_sets
  reference: "Protein decoy sets from CASP experiments"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: AMBER-GBSA
    params: {ff: ff14SB, GB: OBC2}
    results: {native_rank: 3, RMSD_best: 1.8}
  - solver: Rosetta-score
    params: {scorefunction: ref2015}
    results: {native_rank: 1, RMSD_best: 1.2}
  - solver: GNN-potential
    params: {model: trained_on_PDB}
    results: {native_rank: 1, RMSD_best: 0.8}
quality_scoring:
  - {max_rank: 1, Q: 1.00}
  - {max_rank: 5, Q: 0.90}
  - {max_rank: 10, Q: 0.80}
  - {max_rank: 50, Q: 0.75}
```

**Baseline solver:** Rosetta-score — native rank 1
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Native Rank | RMSD Best | Runtime | Q |
|--------|-----------|----------|---------|---|
| AMBER-GBSA | 3 | 1.8 A | 600 s | 0.90 |
| Rosetta-score | 1 | 1.2 A | 120 s | 1.00 |
| GNN-potential | 1 | 0.8 A | 10 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (GNN): 500 × 1.00 = 500 PWM
Floor:           500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p412_hash>",
  "h_s": "sha256:<spec412_hash>",
  "h_b": "sha256:<bench412_hash>",
  "r": {"native_rank": 1, "RMSD_best": 0.8, "energy_gap": 15.2},
  "c": {"decoys_tested": 1000, "K": 3},
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
pwm-node benchmarks | grep protein_folding
pwm-node verify AE_computational_biology/protein_folding_s1_ideal.yaml
pwm-node mine AE_computational_biology/protein_folding_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
