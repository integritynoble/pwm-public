# Principle #480 — Lattice QCD

**Domain:** Particle Physics | **Carrier:** N/A (Monte Carlo) | **Difficulty:** Expert (δ=5)
**DAG:** [S.random.metropolis] --> [L.sparse.dirac] --> [∫.stochastic] | **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.rand.metro-->L.sparse.dirac-->∫.stoch  LQCD  hadron-spectrum  HMC
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  LATTICE QCD                   P = (E,G,W,C)   Principle #480   │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ Z = ∫ DU Dψ Dψ̄ exp(−S_G[U] − S_F[U,ψ,ψ̄])          │
│        │ S_G = β Σ_P (1 − Re tr U_P / 3)  (Wilson gauge action)│
│        │ S_F = ψ̄(D̸[U] + m)ψ   (fermion action)               │
│        │ ⟨O⟩ = (1/Z)∫ O e^{−S}  → Monte Carlo sampling        │
│        │ Forward: given (β,m_q,L,a) → hadron masses, f_π, etc. │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.rand.metro] ──→ [L.sparse.dirac] ──→ [∫.stoch]      │
│        │  Metropolis  Dirac-op  path-integral                   │
│        │ V={S.rand.metro,L.sparse.dirac,∫.stoch}  A={S.rand.metro→L.sparse.dirac,L.sparse.dirac→∫.stoch}  L_DAG=2.0            │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (lattice regularization well-defined)   │
│        │ Uniqueness: YES (ergodic Markov chain → unique ⟨O⟩)   │
│        │ Stability: autocorrelation / critical slowing down     │
│        │ Mismatch: finite volume, lattice spacing, quenching    │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |m_hadron − m_expt|/m_expt  (mass error)          │
│        │ q = 2.0 (O(a²) improved actions)                     │
│        │ T = {hadron_mass_error, chi2_correlator, autocorrel}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Gauge-invariant action; fermion determinant well-defined | PASS |
| S2 | HMC ergodic; detailed balance satisfied | PASS |
| S3 | HMC + multi-level converges; autocorrelation manageable | PASS |
| S4 | Hadron masses within 2% of experiment at physical pion mass | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# lqcd/hadron_spectrum_s1.yaml
principle_ref: sha256:<p480_hash>
omega:
  lattice: [32, 32, 32, 64]
  domain: 4D_Euclidean
  beta: 6.1
  configs: 1000
E:
  forward: "Wilson gauge + clover fermion → HMC → correlators"
  quarks: [u, d, s]
  m_pi_target: 135   # MeV
  a_inv: 2.0         # GeV (lattice spacing⁻¹)
B:
  boundary: periodic_spatial_antiperiodic_temporal
  smearing: Wuppertal_Gaussian
I:
  scenario: light_hadron_spectrum
  lattice_sizes: [16^3x32, 24^3x48, 32^3x64]
O: [pion_mass, proton_mass, fpi, chiral_extrapolation]
epsilon:
  mass_error_max: 0.02    # relative
  fpi_error_max: 0.03
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 32³×64 at a⁻¹=2 GeV → L ≈ 3.2 fm; m_πL > 4 | PASS |
| S2 | HMC with 1000 configs provides adequate statistics | PASS |
| S3 | HMC acceptance > 80%; autocorrelation τ < 20 | PASS |
| S4 | Hadron masses within 2% after continuum extrapolation | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# lqcd/benchmark_hadron.yaml
spec_ref: sha256:<spec480_hash>
principle_ref: sha256:<p480_hash>
dataset:
  name: FLAG_hadron_spectrum
  reference: "FLAG Review (Aoki et al., 2021) lattice averages"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Wilson fermions (quenched)
    params: {configs: 500, lattice: 24^3x48}
    results: {proton_error: 0.08, pion_error: 0.05}
  - solver: Clover fermions (N_f=2+1)
    params: {configs: 1000, lattice: 32^3x64}
    results: {proton_error: 0.025, pion_error: 0.015}
  - solver: Domain-wall (N_f=2+1)
    params: {configs: 1000, lattice: 32^3x64, L_s: 16}
    results: {proton_error: 0.012, pion_error: 0.008}
quality_scoring:
  - {min_err: 0.01, Q: 1.00}
  - {min_err: 0.02, Q: 0.90}
  - {min_err: 0.05, Q: 0.80}
  - {min_err: 0.10, Q: 0.75}
```

**Baseline solver:** Clover (N_f=2+1) — proton mass error 2.5%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Proton Error | Pion Error | Runtime | Q |
|--------|-------------|-----------|---------|---|
| Wilson (quenched) | 0.08 | 0.05 | 10⁴ core-hr | 0.75 |
| Clover (N_f=2+1) | 0.025 | 0.015 | 10⁵ core-hr | 0.90 |
| Domain-wall | 0.012 | 0.008 | 3×10⁵ core-hr | 1.00 |
| Staggered (HISQ) | 0.015 | 0.005 | 2×10⁵ core-hr | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (DWF): 500 × 1.00 = 500 PWM
Floor:           500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p480_hash>",
  "h_s": "sha256:<spec480_hash>",
  "h_b": "sha256:<bench480_hash>",
  "r": {"proton_error": 0.012, "error_bound": 0.02, "ratio": 0.600},
  "c": {"configs": 1000, "lattice": "32^3x64", "K": 3},
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
pwm-node benchmarks | grep lqcd
pwm-node verify lqcd/hadron_spectrum_s1.yaml
pwm-node mine lqcd/hadron_spectrum_s1.yaml
pwm-node inspect sha256:<cert_hash>
```
