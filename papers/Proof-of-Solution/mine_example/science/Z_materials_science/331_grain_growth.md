# Principle #331 — Grain Growth (Curvature-Driven)

**Domain:** Materials Science | **Carrier:** grain boundary | **Difficulty:** Standard (δ=3)
**DAG:** ∂.time → N.pointwise → ∂.space.laplacian |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          κ→v→A→⟨R⟩   grain-grow  normal-growth-2D   PF/MC
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  GRAIN GROWTH (CURVATURE-DRIVEN) P = (E,G,W,C)  Principle #331 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ v_n = Mγκ  (boundary velocity = mobility × energy × curvature)│
│        │ dA_i/dt = −2πMγ(n_i − 6)/3  (von Neumann-Mullins)    │
│        │ ⟨R²⟩ − ⟨R₀²⟩ = Kt  (parabolic growth law)            │
│        │ Forward: given microstructure → evolve ⟨R⟩(t)         │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [N.pointwise] ──→ [∂.space.laplacian]     │
│        │ derivative  nonlinear  derivative                      │
│        │ V={∂.time, N.pointwise, ∂.space.laplacian}  A={∂.time→N.pointwise, N.pointwise→∂.space.laplacian}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (parabolic PDE / sharp-interface limit) │
│        │ Uniqueness: YES (topological changes handled by rules) │
│        │ Stability: grain count monotonically decreasing        │
│        │ Mismatch: anisotropic γ, pinning particles, drag      │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |K_sim − K_theory|/K_theory (primary)             │
│        │ q = 2.0 (phase-field), 1.0 (Monte Carlo Potts)      │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Curvature-velocity relation well-defined; grain topology consistent | PASS |
| S2 | Von Neumann-Mullins law exact in 2D for isotropic γ | PASS |
| S3 | Phase-field and MC-Potts converge to sharp-interface limit | PASS |
| S4 | Growth constant K measurable from ⟨R²⟩ vs t slope | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# grain_growth/normal_2d_s1_ideal.yaml
principle_ref: sha256:<p331_hash>
omega:
  grid: [512, 512]
  domain: unit_square
  time: [0, 1000.0]
  n_grains_initial: 5000
E:
  forward: "∂η_i/∂t = −L(δF/δη_i), multi-order-parameter PF"
  mobility: 1.0
  grain_boundary_energy: 1.0
B:
  periodic: true
I:
  scenario: normal_grain_growth_2D
  isotropic: true
O: [mean_grain_radius, grain_size_distribution, growth_exponent]
epsilon:
  growth_exp_error: 0.03  # expect n=0.5
  distribution_KS_stat: 0.05
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 5000 grains on 512² grid; interface resolved | PASS |
| S2 | Normal growth gives ⟨R⟩~t^{1/2} with log-normal distribution | PASS |
| S3 | Multi-order-parameter phase-field converges | PASS |
| S4 | Growth exponent error < 0.03 achievable with 5000 grains | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# grain_growth/benchmark_normal_2d.yaml
spec_ref: sha256:<spec331_hash>
principle_ref: sha256:<p331_hash>
dataset:
  name: normal_grain_growth_theory
  reference: "Mullins (1956): ⟨R²⟩ = ⟨R₀²⟩ + Kt"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: MC-Potts
    params: {grid: [512,512], n_grains: 5000}
    results: {growth_exp: 0.48, KS_stat: 0.06}
  - solver: Phase-field (multi-η)
    params: {grid: [512,512], n_grains: 5000}
    results: {growth_exp: 0.50, KS_stat: 0.04}
  - solver: Front-tracking
    params: {n_grains: 2000}
    results: {growth_exp: 0.50, KS_stat: 0.03}
quality_scoring:
  - {min_exp_error: 0.01, Q: 1.00}
  - {min_exp_error: 0.03, Q: 0.90}
  - {min_exp_error: 0.05, Q: 0.80}
  - {min_exp_error: 0.10, Q: 0.75}
```

**Baseline solver:** Phase-field — growth exponent 0.50
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | Growth Exp | KS Stat | Runtime | Q |
|--------|-----------|---------|---------|---|
| MC-Potts | 0.48 | 0.06 | 10 min | 0.80 |
| Phase-field | 0.50 | 0.04 | 30 min | 0.90 |
| Front-tracking | 0.50 | 0.03 | 15 min | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (front-tracking): 300 × 1.00 = 300 PWM
Floor:                      300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p331_hash>",
  "h_s": "sha256:<spec331_hash>",
  "h_b": "sha256:<bench331_hash>",
  "r": {"residual_norm": 0.00, "error_bound": 0.03, "ratio": 0.0},
  "c": {"fitted_rate": 2.0, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep grain_growth
pwm-node verify grain_growth/normal_2d_s1_ideal.yaml
pwm-node mine grain_growth/normal_2d_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
