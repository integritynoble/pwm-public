# Principle #294 — Density Functional Theory (DFT)

**Domain:** Computational Chemistry | **Carrier:** N/A (variational) | **Difficulty:** Hard (δ=5)
**DAG:** E.hermitian → N.xc → ∫.volume |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ρ→V→H→D      dft-ks      atomisation-G2    SCF-KS
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  DENSITY FUNCTIONAL THEORY (DFT)  P = (E,G,W,C)   Principle #294│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ E[ρ] = T_s[ρ] + ∫ v_ext ρ dr + E_H[ρ] + E_xc[ρ]     │
│        │ Kohn-Sham: [−½∇² + v_eff(r)]φ_i = ε_i φ_i            │
│        │ ρ(r) = Σ|φ_i(r)|² ; v_eff = v_ext + v_H + v_xc       │
│        │ Forward: given geometry + functional → total energy E  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [E.hermitian] ──→ [N.xc] ──→ [∫.volume]                │
│        │ eigensolve  nonlinear  integrate                       │
│        │ V={E.hermitian, N.xc, ∫.volume}  A={E.hermitian→N.xc, N.xc→∫.volume}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Hohenberg-Kohn theorem)               │
│        │ Uniqueness: YES for ground-state ρ (HK second theorem) │
│        │ Stability: SCF convergence depends on mixing scheme    │
│        │ Mismatch: E_xc approximation (LDA/GGA/hybrid error)   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |E_DFT − E_ref| (kcal/mol, atomisation energy)    │
│        │ q = 3.0 (SCF typically cubic-scaling)                 │
│        │ T = {total_energy, forces, band_gap, atomisation_MAE}  │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | KS equations variational; density integrates to N electrons | PASS |
| S2 | HK theorems guarantee E[ρ] is well-defined functional | PASS |
| S3 | SCF with DIIS/level-shifting converges for most molecules | PASS |
| S4 | Atomisation MAE < 5 kcal/mol (B3LYP/cc-pVTZ on G2 set) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# dft_ks/atomisation_s1_ideal.yaml
principle_ref: sha256:<p294_hash>
omega:
  basis: cc-pVTZ
  functional: B3LYP
  grid: fine  # 99 radial, 590 angular
E:
  forward: "KS-DFT self-consistent field"
  convergence: 1.0e-8  # Hartree
  max_cycles: 200
B:
  symmetry: auto
  initial_guess: SAD
I:
  scenario: G2_atomisation_energies
  molecules: 148
  reference: CCSD(T)/CBS
O: [MAE_kcal, max_error, RMSE]
epsilon:
  MAE_max: 5.0  # kcal/mol
  max_error_max: 20.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | cc-pVTZ basis adequate for B3LYP; 148 molecules well-defined | PASS |
| S2 | B3LYP SCF converges for all G2 molecules with DIIS | PASS |
| S3 | SCF+DIIS converges in <100 cycles for all 148 species | PASS |
| S4 | MAE < 5 kcal/mol well-established for B3LYP/cc-pVTZ | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# dft_ks/benchmark_g2.yaml
spec_ref: sha256:<spec294_hash>
principle_ref: sha256:<p294_hash>
dataset:
  name: G2_atomisation_148
  reference: "Curtiss et al. (1997) G2/97 test set"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: LDA/VWN
    params: {basis: cc-pVTZ}
    results: {MAE: 36.2, RMSE: 42.5}
  - solver: PBE/GGA
    params: {basis: cc-pVTZ}
    results: {MAE: 8.1, RMSE: 10.5}
  - solver: B3LYP/hybrid
    params: {basis: cc-pVTZ}
    results: {MAE: 3.2, RMSE: 4.5}
quality_scoring:
  - {min_MAE: 1.0, Q: 1.00}
  - {min_MAE: 3.0, Q: 0.90}
  - {min_MAE: 5.0, Q: 0.80}
  - {min_MAE: 10.0, Q: 0.75}
```

**Baseline solver:** B3LYP — MAE 3.2 kcal/mol
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | MAE (kcal/mol) | RMSE | Runtime | Q |
|--------|----------------|------|---------|---|
| LDA | 36.2 | 42.5 | 10 s | 0.75 |
| PBE | 8.1 | 10.5 | 12 s | 0.80 |
| B3LYP | 3.2 | 4.5 | 30 s | 0.90 |
| ωB97X-D/cc-pVQZ | 1.8 | 2.5 | 120 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (ωB97X-D): 500 × 1.00 = 500 PWM
Floor:               500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p294_hash>",
  "h_s": "sha256:<spec294_hash>",
  "h_b": "sha256:<bench294_hash>",
  "r": {"residual_norm": 1.8, "error_bound": 5.0, "ratio": 0.36},
  "c": {"fitted_rate": 2.95, "theoretical_rate": 3.0, "K": 4},
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
pwm-node benchmarks | grep dft_ks
pwm-node verify dft_ks/atomisation_s1_ideal.yaml
pwm-node mine dft_ks/atomisation_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
