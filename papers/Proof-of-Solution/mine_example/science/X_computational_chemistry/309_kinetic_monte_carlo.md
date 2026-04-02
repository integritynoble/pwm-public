# Principle #309 — Kinetic Monte Carlo (KMC)

**Domain:** Computational Chemistry | **Carrier:** N/A (stochastic) | **Difficulty:** Standard (δ=3)
**DAG:** S.random → N.reaction → ∫.ensemble |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          S.random→N.reaction→∫.ensemble      kmc-sim     surface-growth    BKL
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  KINETIC MONTE CARLO (KMC)        P = (E,G,W,C)   Principle #309│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ r_i = ν₀ exp(−E_a,i/k_BT)  (rate for event i)        │
│        │ R_tot = Σ r_i  (total rate)                            │
│        │ Δt = −ln(u)/R_tot  (time advance, u ~ U(0,1))         │
│        │ Forward: given rate catalog → stochastic trajectory    │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [S.random] ──→ [N.reaction] ──→ [∫.ensemble]           │
│        │ sample  nonlinear  integrate                           │
│        │ V={S.random, N.reaction, ∫.ensemble}  A={S.random→N.reaction, N.reaction→∫.ensemble}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (master equation has unique solution)   │
│        │ Uniqueness: statistically; ensemble average converges  │
│        │ Stability: rejection-free BKL algorithm exact          │
│        │ Mismatch: incomplete event catalog, barrier errors     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |⟨O⟩_KMC − ⟨O⟩_ref| / ⟨O⟩_ref (observable error) │
│        │ q = 1.0 (linear in events per step)                   │
│        │ T = {growth_rate, surface_roughness, island_density}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | BKL algorithm rejection-free; time advance statistically exact | PASS |
| S2 | Master equation correspondence proven for Markov processes | PASS |
| S3 | KMC reproduces analytical growth scaling for 2D island nucleation | PASS |
| S4 | Island density within 5% of mean-field theory at low coverage | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# kmc_sim/growth_s1_ideal.yaml
principle_ref: sha256:<p309_hash>
omega:
  lattice: [256, 256]
  domain: square_2D
  coverage: 0.3  # monolayers
  temperature: 500  # K
E:
  forward: "BKL rejection-free KMC"
  events: [deposition, diffusion, desorption]
  E_diffusion: 0.5  # eV
  E_desorption: 1.5  # eV
  deposition_rate: 0.1  # ML/s
B:
  substrate: flat
  PBC: true
I:
  scenario: epitaxial_growth_2D
  reference: mean_field_nucleation_theory
  ensemble: 100  # independent runs
O: [island_density, surface_roughness, growth_rate]
epsilon:
  island_density_error_max: 0.05  # relative
  roughness_error_max: 0.10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 256² lattice large enough; 100 ensemble runs for statistics | PASS |
| S2 | BKL exact for given event catalog; barriers well-defined | PASS |
| S3 | Converges to mean-field scaling law for island density | PASS |
| S4 | Island density error < 5% vs nucleation theory | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# kmc_sim/benchmark_growth.yaml
spec_ref: sha256:<spec309_hash>
principle_ref: sha256:<p309_hash>
dataset:
  name: epitaxial_growth_mean_field
  reference: "Venables (1973) nucleation theory"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: BKL-KMC
    params: {lattice: 128x128, runs: 50}
    results: {island_err: 0.08, roughness_err: 0.12}
  - solver: BKL-KMC (fine)
    params: {lattice: 256x256, runs: 100}
    results: {island_err: 0.04, roughness_err: 0.06}
  - solver: Adaptive-KMC
    params: {lattice: 256x256, saddle_search: true}
    results: {island_err: 0.03, roughness_err: 0.05}
quality_scoring:
  - {min_island_err: 0.01, Q: 1.00}
  - {min_island_err: 0.03, Q: 0.90}
  - {min_island_err: 0.06, Q: 0.80}
  - {min_island_err: 0.12, Q: 0.75}
```

**Baseline solver:** BKL-KMC (256²) — island density error 4%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Island Err | Roughness Err | Runtime | Q |
|--------|------------|---------------|---------|---|
| BKL 128² | 0.08 | 0.12 | 10 s | 0.80 |
| BKL 256² | 0.04 | 0.06 | 60 s | 0.90 |
| Adaptive-KMC | 0.03 | 0.05 | 120 s | 0.90 |
| BKL 512² + 500 runs | 0.008 | 0.02 | 600 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (large): 300 × 1.00 = 300 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p309_hash>",
  "h_s": "sha256:<spec309_hash>",
  "h_b": "sha256:<bench309_hash>",
  "r": {"residual_norm": 0.008, "error_bound": 0.05, "ratio": 0.16},
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
pwm-node benchmarks | grep kmc_sim
pwm-node verify kmc_sim/growth_s1_ideal.yaml
pwm-node mine kmc_sim/growth_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
