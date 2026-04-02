# Principle #337 — Thin Film Growth (PVD/CVD/KMC)

**Domain:** Materials Science | **Carrier:** surface configuration | **Difficulty:** Frontier (δ=5)
**DAG:** ∂.time → N.reaction → ∂.space |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.reaction→∂.space     thin-film   homoepitaxy-KMC    KMC/rate-eq
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  THIN FILM GROWTH (PVD/CVD/KMC) P = (E,G,W,C)   Principle #337│
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ r_i = ν₀ exp(−E_i/kT)  (Arrhenius rate for event i)  │
│        │ Events: deposition, diffusion, aggregation, desorption │
│        │ KMC: Σ_events r_i → select event → advance time      │
│        │ Forward: given flux, T, barriers → evolve morphology  │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [N.reaction] ──→ [∂.space]                │
│        │ derivative  nonlinear  derivative                      │
│        │ V={∂.time, N.reaction, ∂.space}  A={∂.time→N.reaction, N.reaction→∂.space}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (master equation for lattice states)    │
│        │ Uniqueness: statistical (ensemble averages converge)   │
│        │ Stability: island density scales as n~(F/D)^{χ}       │
│        │ Mismatch: barrier accuracy, lattice model, strain      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |n_island^sim − n_island^theory|/n_theory (primary)│
│        │ q = O(1/√N_runs) (statistical)                       │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Event rates satisfy detailed balance; lattice well-defined | PASS |
| S2 | KMC master equation well-posed; rejection-free algorithm exact | PASS |
| S3 | Island density converges with simulation size and runs | PASS |
| S4 | Scaling exponent χ measurable against nucleation theory | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# thin_film/homoepitaxy_s1_ideal.yaml
principle_ref: sha256:<p337_hash>
omega:
  lattice: [512, 512]
  coverage: 0.3  # monolayers
E:
  forward: "KMC: deposition + surface diffusion on square lattice"
  E_diffusion: 0.5  # eV
  E_binding: 0.3  # eV per neighbor
B:
  substrate: perfect_crystal
  boundary: periodic
I:
  scenario: homoepitaxy_submonolayer
  flux: 0.01  # ML/s
  T: 500  # K
  n_runs: 100
O: [island_density, island_size_distribution, scaling_exponent]
epsilon:
  chi_error_max: 0.05
  n_island_rel_error: 0.10
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 512² lattice at 0.3 ML gives ~1000 islands for statistics | PASS |
| S2 | Nucleation theory predicts χ = i*/(i*+2) for critical nucleus i* | PASS |
| S3 | KMC converges with lattice size and ensemble averaging | PASS |
| S4 | Scaling exponent error < 0.05 with 100 runs | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# thin_film/benchmark_homoepitaxy.yaml
spec_ref: sha256:<spec337_hash>
principle_ref: sha256:<p337_hash>
dataset:
  name: homoepitaxy_scaling
  reference: "Amar & Family (1995) KMC scaling results"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: KMC (BKL)
    params: {lattice: [256,256], runs: 50}
    results: {chi_error: 0.08, n_island_error: 0.15}
  - solver: KMC (BKL)
    params: {lattice: [512,512], runs: 100}
    results: {chi_error: 0.03, n_island_error: 0.08}
  - solver: Rate-equation
    params: {i_star: 1}
    results: {chi_error: 0.02, n_island_error: 0.05}
quality_scoring:
  - {min_chi_error: 0.01, Q: 1.00}
  - {min_chi_error: 0.05, Q: 0.90}
  - {min_chi_error: 0.10, Q: 0.80}
  - {min_chi_error: 0.20, Q: 0.75}
```

**Baseline solver:** KMC (512², 100 runs) — χ error 0.03
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | χ Error | n_island Error | Runtime | Q |
|--------|---------|---------------|---------|---|
| KMC (256², 50) | 0.08 | 0.15 | 1 h | 0.80 |
| KMC (512², 100) | 0.03 | 0.08 | 8 h | 0.90 |
| Rate-equation | 0.02 | 0.05 | 0.1 s | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case: 500 × 0.90 = 450 PWM
Floor:     500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p337_hash>",
  "h_s": "sha256:<spec337_hash>",
  "h_b": "sha256:<bench337_hash>",
  "r": {"residual_norm": 0.03, "error_bound": 0.05, "ratio": 0.60},
  "c": {"fitted_rate": 0.5, "theoretical_rate": 0.5, "K": 4},
  "Q": 0.90,
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
| L4 Solution | — | 375–450 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep thin_film
pwm-node verify thin_film/homoepitaxy_s1_ideal.yaml
pwm-node mine thin_film/homoepitaxy_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
