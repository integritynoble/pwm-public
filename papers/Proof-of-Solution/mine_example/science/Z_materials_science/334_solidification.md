# Principle #334 — Solidification Modeling

**Domain:** Materials Science | **Carrier:** solid fraction | **Difficulty:** Frontier (δ=5)
**DAG:** ∂.time → ∂.space → N.pointwise → B.dirichlet |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          T→φ→v→λ     solidify    dendrite-2D        PF/CA
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  SOLIDIFICATION MODELING        P = (E,G,W,C)   Principle #334 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ τ ∂φ/∂t = W²∇²φ + φ(1−φ)(φ−1/2+30φ(1−φ)λu)         │
│        │ ∂u/∂t = D∇²u + (1/2)∂φ/∂t  (thermal/solutal field)   │
│        │ u = (T−T_m)/(L/c_p)  (dimensionless undercooling)     │
│        │ Forward: given Δ, anisotropy → dendrite tip v, λ      │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [∂.space] ──→ [N.pointwise] ──→ [B.dirichlet] │
│        │ derivative  derivative  nonlinear  boundary            │
│        │ V={∂.time, ∂.space, N.pointwise, B.dirichlet}  A={∂.time→∂.space, ∂.space→N.pointwise, N.pointwise→B.dirichlet}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (parabolic PDE system)                  │
│        │ Uniqueness: YES (for given undercooling and anisotropy)│
│        │ Stability: tip-speed selection by anisotropy           │
│        │ Mismatch: interface width, grid anisotropy, kinetics   │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |v_tip^sim − v_tip^theory|/v_tip (primary)        │
│        │ q = 2.0 (FDM), convergence with W/d₀ ratio          │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Phase-field and thermal equations coupled consistently | PASS |
| S2 | Sharp-interface limit recovers Gibbs-Thomson condition | PASS |
| S3 | Convergence with decreasing W/d₀ (thin-interface limit) | PASS |
| S4 | Tip velocity measurable against Ivantsov + solvability theory | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# solidification/dendrite_2d_s1_ideal.yaml
principle_ref: sha256:<p334_hash>
omega:
  grid: [2048, 2048]
  domain: [-100, 100] x [-100, 100]  # d₀ units
  time: [0, 5000]
  dt: 0.01
E:
  forward: "coupled phase-field + thermal diffusion"
  anisotropy: 0.04  # 4-fold
B:
  far_field: {u: -0.55}
I:
  scenario: free_dendrite_growth
  undercooling: 0.55
  D_thermal: 1.0
O: [tip_velocity, tip_radius, secondary_arm_spacing]
epsilon:
  v_tip_error_max: 0.05  # relative to solvability theory
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 2048² grid with W/d₀ = 5 achieves thin-interface regime | PASS |
| S2 | Solvability theory gives v_tip and ρ_tip for given Δ | PASS |
| S3 | Phase-field converges in thin-interface limit | PASS |
| S4 | v_tip error < 5% at W/d₀ = 5 | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# solidification/benchmark_dendrite.yaml
spec_ref: sha256:<spec334_hash>
principle_ref: sha256:<p334_hash>
dataset:
  name: dendrite_tip_solvability
  reference: "Karma & Rappel (1998) phase-field benchmark"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Phase-field (explicit)
    params: {grid: [1024,1024], W_d0: 10}
    results: {v_tip_error: 0.12}
  - solver: Phase-field (adaptive mesh)
    params: {min_h: 0.5, W_d0: 5}
    results: {v_tip_error: 0.04}
  - solver: Cellular automaton
    params: {grid: [1024,1024]}
    results: {v_tip_error: 0.15}
quality_scoring:
  - {min_v_error: 0.02, Q: 1.00}
  - {min_v_error: 0.05, Q: 0.90}
  - {min_v_error: 0.10, Q: 0.80}
  - {min_v_error: 0.20, Q: 0.75}
```

**Baseline solver:** Phase-field (AMR) — v_tip error 4%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | v_tip Error | Runtime | Q |
|--------|-----------|---------|---|
| Cellular automaton | 0.15 | 1 h | 0.80 |
| Phase-field (explicit) | 0.12 | 4 h | 0.80 |
| Phase-field (AMR) | 0.04 | 2 h | 0.90 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 5 × 1.0 × Q
Best case (PF-AMR): 500 × 0.90 = 450 PWM
Floor:              500 × 0.75 = 375 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p334_hash>",
  "h_s": "sha256:<spec334_hash>",
  "h_b": "sha256:<bench334_hash>",
  "r": {"residual_norm": 0.04, "error_bound": 0.10, "ratio": 0.40},
  "c": {"fitted_rate": 2.0, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep solidification
pwm-node verify solidification/dendrite_2d_s1_ideal.yaml
pwm-node mine solidification/dendrite_2d_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
