# Principle #310 — Monte Carlo Sampling (Metropolis)

**Domain:** Computational Chemistry | **Carrier:** N/A (stochastic) | **Difficulty:** Standard (δ=3)
**DAG:** S.random.metropolis → N.bilinear.pair → ∫.ensemble |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.random.metropolis→N.bilinear.pair→∫.ensemble      mc-metro    LJ-fluid          NVT-MC
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  MONTE CARLO SAMPLING (METROPOLIS) P=(E,G,W,C)    Principle #310│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ P(x→x') = min(1, exp(−ΔU/k_BT))  (Metropolis criterion)│
│        │ ⟨O⟩ = (1/N)Σ O(x_i)  (ensemble average)               │
│        │ Detailed balance: P(x)α(x→x') = P(x')α(x'→x)         │
│        │ Forward: given U(x) → sample canonical ensemble        │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.random.metropolis] ──→ [N.bilinear.pair] ──→ [∫.ensemble] │
│        │ sample  nonlinear  integrate                           │
│        │ V={S.random.metropolis, N.bilinear.pair, ∫.ensemble}  A={S.random.metropolis→N.bilinear.pair, N.bilinear.pair→∫.ensemble}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (ergodic Markov chain → Boltzmann dist) │
│        │ Uniqueness: YES (unique stationary distribution)       │
│        │ Stability: acceptance ratio 30–50% optimal             │
│        │ Mismatch: autocorrelation, quasi-ergodicity at low T   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |⟨U⟩_MC − ⟨U⟩_ref| / |⟨U⟩_ref| (energy error)   │
│        │ q = 1.0 (cost per step independent of system size)    │
│        │ T = {energy, pressure, RDF, acceptance_ratio}          │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Detailed balance satisfied; Boltzmann distribution is target | PASS |
| S2 | Ergodic for LJ fluid with single-particle displacement moves | PASS |
| S3 | 10⁶ MC steps converge energy and pressure for 256 LJ particles | PASS |
| S4 | Energy within 0.1% of long MD reference for LJ at T*=1.0 | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# mc_metro/lj_fluid_s1_ideal.yaml
principle_ref: sha256:<p310_hash>
omega:
  particles: 256
  box: cubic_PBC
  density: 0.8  # reduced units
  temperature: 1.0  # reduced units
E:
  forward: "Metropolis NVT with single-particle displacements"
  cutoff: 2.5  # sigma
  tail_correction: true
  max_displacement: auto_tuned  # target 40% acceptance
B:
  initial: FCC_lattice
  equilibration: 1.0e5  # MC cycles
  production: 1.0e6  # MC cycles
I:
  scenario: LJ_fluid_NVT
  reference: NIST_LJ_data
  rho_star: 0.8
  T_star: 1.0
O: [energy_per_particle, pressure, RDF]
epsilon:
  energy_error_max: 1.0e-3  # reduced units
  pressure_error_max: 5.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 256 particles with tail correction; cutoff=2.5σ standard | PASS |
| S2 | Auto-tuned displacement gives ~40% acceptance | PASS |
| S3 | 10⁶ cycles converge energy to 4 significant figures | PASS |
| S4 | Energy error < 0.1% of NIST reference at ρ*=0.8, T*=1.0 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# mc_metro/benchmark_lj.yaml
spec_ref: sha256:<spec310_hash>
principle_ref: sha256:<p310_hash>
dataset:
  name: NIST_LJ_fluid
  reference: "Johnson, Zollweg, Gubbins (1993)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Metropolis-NVT
    params: {cycles: 1e5, particles: 256}
    results: {energy_err: 5.0e-3, pressure_err: 0.08}
  - solver: Metropolis-NVT (long)
    params: {cycles: 1e6, particles: 256}
    results: {energy_err: 8.0e-4, pressure_err: 0.02}
  - solver: GCMC
    params: {cycles: 1e6, mu: -3.5}
    results: {energy_err: 1.2e-3, density_err: 5.0e-3}
quality_scoring:
  - {min_energy_err: 1.0e-4, Q: 1.00}
  - {min_energy_err: 1.0e-3, Q: 0.90}
  - {min_energy_err: 5.0e-3, Q: 0.80}
  - {min_energy_err: 1.0e-2, Q: 0.75}
```

**Baseline solver:** Metropolis-NVT (long) — energy error 8.0×10⁻⁴
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Energy Err | Pressure Err | Runtime | Q |
|--------|------------|-------------|---------|---|
| NVT 10⁵ cycles | 5.0e-3 | 0.08 | 2 s | 0.80 |
| NVT 10⁶ cycles | 8.0e-4 | 0.02 | 20 s | 0.90 |
| NVT 10⁷ cycles | 2.5e-4 | 0.006 | 200 s | 0.90 |
| NVT 10⁸ + 1024 part. | 5.0e-5 | 0.001 | 3600 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (large system): 300 × 1.00 = 300 PWM
Floor:                     300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p310_hash>",
  "h_s": "sha256:<spec310_hash>",
  "h_b": "sha256:<bench310_hash>",
  "r": {"residual_norm": 5.0e-5, "error_bound": 1.0e-3, "ratio": 0.05},
  "c": {"fitted_rate": 0.50, "theoretical_rate": 0.5, "K": 3},
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
pwm-node benchmarks | grep mc_metro
pwm-node verify mc_metro/lj_fluid_s1_ideal.yaml
pwm-node mine mc_metro/lj_fluid_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
