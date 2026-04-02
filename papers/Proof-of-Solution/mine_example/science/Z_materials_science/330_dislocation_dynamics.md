# Principle #330 — Dislocation Dynamics (DD)

**Domain:** Materials Science | **Carrier:** dislocation line | **Difficulty:** Frontier (δ=5)
**DAG:** N.bilinear.pair → ∂.time → ∫.ensemble |  **Reward:** 5× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          σ→F→v→x      DD-sim      Frank-Read-src     ParaDiS
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  DISLOCATION DYNAMICS           P = (E,G,W,C)   Principle #330 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ F_PK = (σ·b) × ξ  (Peach-Koehler force per unit length)│
│        │ v = F_PK / B  (overdamped mobility law)                │
│        │ σ_total = σ_applied + Σ σ_self(dislocation segments)   │
│        │ Forward: given σ_app, initial config → evolve segments │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [N.bilinear.pair] ──→ [∂.time] ──→ [∫.ensemble]        │
│        │ nonlinear  derivative  integrate                       │
│        │ V={N.bilinear.pair, ∂.time, ∫.ensemble}  A={N.bilinear.pair→∂.time, ∂.time→∫.ensemble}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (ODE system for node positions)         │
│        │ Uniqueness: YES (Lipschitz force field)                │
│        │ Stability: time-step limited by segment collision      │
│        │ Mismatch: mobility law, core regularization, topology  │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |τ_crit^sim − τ_crit^theory|/τ_crit (primary)    │
│        │ q = 1.0 (explicit Euler), 2.0 (implicit trapezoid)  │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Peach-Koehler force consistent; Burgers vector conserved | PASS |
| S2 | ODE system well-posed for non-intersecting segments | PASS |
| S3 | Explicit/implicit time-stepping converges with dt | PASS |
| S4 | Critical stress for Frank-Read source computable against theory | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# dd/frank_read_s1_ideal.yaml
principle_ref: sha256:<p330_hash>
omega:
  domain: [10, 10, 10]  # microns
  segments: 100
  time: [0, 1.0e-6]  # seconds
  dt: 1.0e-10
E:
  forward: "dx/dt = F_PK/B, F_PK = (σ·b)×ξ"
  mobility: 1.0e4  # Pa⁻¹s⁻¹
B:
  boundary: {type: free_surface}
  burgers: [1, 1, 0]  # FCC
I:
  scenario: Frank_Read_source
  L_source: 1.0  # micron
  shear_modulus: 48.0  # GPa
  applied_stress: 20.0  # MPa
O: [critical_stress, loop_expansion_rate, dislocation_density]
epsilon:
  tau_crit_error_max: 0.05  # relative
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 100 segments resolve source bow-out; dt stable | PASS |
| S2 | Frank-Read τ_c = μb/(2L) well-known analytically | PASS |
| S3 | Explicit time-stepping converges for overdamped dynamics | PASS |
| S4 | τ_crit error < 5% achievable with sufficient segments | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# dd/benchmark_frank_read.yaml
spec_ref: sha256:<spec330_hash>
principle_ref: sha256:<p330_hash>
dataset:
  name: frank_read_critical_stress
  reference: "Analytic: τ_c ≈ μb/(2L)"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: ParaDiS
    params: {segments: 50, dt: 1e-10}
    results: {tau_crit_error: 0.08}
  - solver: ParaDiS
    params: {segments: 200, dt: 5e-11}
    results: {tau_crit_error: 0.03}
  - solver: Custom-DD (implicit)
    params: {segments: 100, dt: 1e-9}
    results: {tau_crit_error: 0.05}
quality_scoring:
  - {min_tau_error: 0.01, Q: 1.00}
  - {min_tau_error: 0.05, Q: 0.90}
  - {min_tau_error: 0.10, Q: 0.80}
  - {min_tau_error: 0.20, Q: 0.75}
```

**Baseline solver:** ParaDiS (200 seg) — τ_crit error 3%
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | τ_crit Error | Segments | Runtime | Q |
|--------|-------------|----------|---------|---|
| ParaDiS (50 seg) | 0.08 | 50 | 5 min | 0.80 |
| Custom-DD (impl.) | 0.05 | 100 | 10 min | 0.90 |
| ParaDiS (200 seg) | 0.03 | 200 | 30 min | 0.90 |

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
  "h_p": "sha256:<p330_hash>",
  "h_s": "sha256:<spec330_hash>",
  "h_b": "sha256:<bench330_hash>",
  "r": {"residual_norm": 0.03, "error_bound": 0.05, "ratio": 0.60},
  "c": {"fitted_rate": 1.5, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep dd
pwm-node verify dd/frank_read_s1_ideal.yaml
pwm-node mine dd/frank_read_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
