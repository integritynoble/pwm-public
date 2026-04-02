# Principle #305 — Implicit Solvation (PCM/COSMO)

**Domain:** Computational Chemistry | **Carrier:** N/A (continuum model) | **Difficulty:** Standard (δ=3)
**DAG:** ∂.space.laplacian → N.pointwise → B.surface |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ρ→C→σ→G      pcm-solv    solvation-FE      IEF-PCM
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  IMPLICIT SOLVATION (PCM/COSMO)   P = (E,G,W,C)   Principle #305│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ G_solv = G_elec + G_cav + G_disp + G_rep              │
│        │ G_elec: ∇·(ε∇φ) = −4πρ (Poisson equation at cavity)  │
│        │ PCM: apparent surface charges σ on cavity boundary     │
│        │ Forward: given ρ(r), ε → ΔG_solv (solvation free energy)│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.space.laplacian] ──→ [N.pointwise] ──→ [B.surface]  │
│        │ derivative  nonlinear  boundary                        │
│        │ V={∂.space.laplacian, N.pointwise, B.surface}  A={∂.space.laplacian→N.pointwise, N.pointwise→B.surface}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (Poisson equation on piecewise domain)  │
│        │ Uniqueness: YES for given cavity shape and ε            │
│        │ Stability: well-conditioned BEM; small added SCF cost  │
│        │ Mismatch: cavity definition, specific H-bond effects   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |ΔG_solv,calc − ΔG_solv,exp| (kcal/mol)           │
│        │ q = 2.0 (BEM + SCF same cost as gas-phase)            │
│        │ T = {solvation_FE, dipole_change, cavity_area}         │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Poisson equation at dielectric boundary well-defined; BEM consistent | PASS |
| S2 | IEF-PCM provides unique surface charges for given cavity | PASS |
| S3 | SCF+PCM converges in same iteration count as gas-phase | PASS |
| S4 | ΔG_solv MAE < 1.5 kcal/mol for neutrals in water (SMD) | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# pcm_solv/solvation_s1_ideal.yaml
principle_ref: sha256:<p305_hash>
omega:
  molecules: 274
  solvent: water
  method: B3LYP/6-31G*
E:
  forward: "IEF-PCM with SMD radii"
  cavity: vdW_radii_SMD
  epsilon: 78.39  # water at 25°C
B:
  tesserae: 60_per_atom
  charge_model: CHELPG
I:
  scenario: Minnesota_solvation_database
  reference: experimental_ΔG_solv
  neutrals: 274
O: [MAE_kcal, RMSE_kcal, max_error]
epsilon:
  MAE_max: 1.5  # kcal/mol
  max_error_max: 5.0
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 274 neutrals; SMD cavity radii well-parametrised | PASS |
| S2 | IEF-PCM + SMD validated for water solvent | PASS |
| S3 | SCF+PCM converges for all 274 molecules | PASS |
| S4 | MAE < 1.5 kcal/mol for neutral solutes in water | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# pcm_solv/benchmark_minnesota.yaml
spec_ref: sha256:<spec305_hash>
principle_ref: sha256:<p305_hash>
dataset:
  name: Minnesota_solvation_274
  reference: "Marenich, Cramer, Truhlar (2009)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: C-PCM/B3LYP
    params: {radii: UFF, basis: 6-31G*}
    results: {MAE: 2.8, RMSE: 3.5}
  - solver: IEF-PCM/SMD/B3LYP
    params: {radii: SMD, basis: 6-31G*}
    results: {MAE: 0.9, RMSE: 1.2}
  - solver: COSMO-RS
    params: {method: BP86/TZVP}
    results: {MAE: 0.6, RMSE: 0.9}
quality_scoring:
  - {min_MAE: 0.3, Q: 1.00}
  - {min_MAE: 0.8, Q: 0.90}
  - {min_MAE: 1.5, Q: 0.80}
  - {min_MAE: 3.0, Q: 0.75}
```

**Baseline solver:** IEF-PCM/SMD — MAE 0.9 kcal/mol
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | MAE (kcal/mol) | RMSE | Runtime | Q |
|--------|----------------|------|---------|---|
| C-PCM/UFF | 2.8 | 3.5 | 5 s | 0.75 |
| IEF-PCM/SMD | 0.9 | 1.2 | 8 s | 0.90 |
| COSMO-RS | 0.6 | 0.9 | 15 s | 0.90 |
| SMD + explicit 1st shell | 0.25 | 0.4 | 120 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (SMD+explicit): 300 × 1.00 = 300 PWM
Floor:                     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p305_hash>",
  "h_s": "sha256:<spec305_hash>",
  "h_b": "sha256:<bench305_hash>",
  "r": {"residual_norm": 0.25, "error_bound": 1.5, "ratio": 0.17},
  "c": {"fitted_rate": 2.05, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep pcm_solv
pwm-node verify pcm_solv/solvation_s1_ideal.yaml
pwm-node mine pcm_solv/solvation_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
