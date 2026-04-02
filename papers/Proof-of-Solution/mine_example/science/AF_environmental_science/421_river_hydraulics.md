# Principle #421 — River Hydraulics (Saint-Venant)

**Domain:** Environmental Science | **Carrier:** water depth/discharge | **Difficulty:** Standard (δ=3)
**DAG:** ∂.time → N.flux → ∂.space → B.open |  **Reward:** 3× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→N.flux→∂.space→B.open      Saint-Venant  dam-break         Godunov
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  RIVER HYDRAULICS (SAINT-VENANT) P = (E,G,W,C)  Principle #421 │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ ∂A/∂t + ∂Q/∂x = q_lat               (continuity)     │
│        │ ∂Q/∂t + ∂(Q²/A + gI₁)/∂x = gA(S₀ − S_f) (momentum) │
│        │ A = wetted area, Q = discharge, S₀ = bed slope        │
│        │ S_f = friction slope (Manning: S_f = n²Q²/(A²R^{4/3}))│
│        │ Forward: given IC/BC, channel geometry → h(x,t), Q(x,t)│
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [N.flux] ──→ [∂.space] ──→ [B.open]       │
│        │ derivative  nonlinear  derivative  boundary            │
│        │ V={∂.time, N.flux, ∂.space, B.open}  A={∂.time→N.flux, N.flux→∂.space, ∂.space→B.open}  L_DAG=3.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (hyperbolic system; Riemann problem)    │
│        │ Uniqueness: YES (entropy condition selects weak sol.)  │
│        │ Stability: CFL on gravity wave speed c = √(gA/T)      │
│        │ Mismatch: Manning's n, cross-section geometry          │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = relative L2 error ‖h−h_ref‖/‖h_ref‖              │
│        │ q = 1.0 (Godunov), 2.0 (MUSCL-Hancock)              │
│        │ T = {h_error, Q_error, wavefront_speed_error}          │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Area, discharge, slope dimensions consistent | PASS |
| S2 | Hyperbolic system — Riemann solver well-defined | PASS |
| S3 | Godunov-type FVM converges; MUSCL achieves 2nd order | PASS |
| S4 | h(x,t) error computable against Ritter dam-break analytic | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# river_hydraulics/dam_break_s1_ideal.yaml
principle_ref: sha256:<p421_hash>
omega:
  grid: [500]
  domain: channel_1D
  length: 2000   # m
  time: [0, 60.0]   # s
  dt: 0.05
E:
  forward: "Saint-Venant: ∂A/∂t + ∂Q/∂x = 0; momentum with friction"
  gravity: 9.81
  n_manning: 0.0   # frictionless for Ritter solution
B:
  upstream: {transmissive: true}
  downstream: {transmissive: true}
  initial: {h_left: 10.0, h_right: 0.001, dam_position: 1000}
I:
  scenario: dam_break_dry_bed
  mesh_sizes: [100, 250, 500]
O: [h_L2_error, wavefront_error]
epsilon:
  h_error_max: 1.0e-2
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | 500 cells over 2 km; dt=0.05 s satisfies CFL for c~10 m/s | PASS |
| S2 | Frictionless dam-break — Ritter analytic solution exists | PASS |
| S3 | Godunov FVM converges at O(h); MUSCL at O(h²) for smooth regions | PASS |
| S4 | h error < 1% achievable at 500 cells | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# river_hydraulics/benchmark_dam_break.yaml
spec_ref: sha256:<spec421_hash>
principle_ref: sha256:<p421_hash>
dataset:
  name: Ritter_dam_break_analytic
  reference: "Ritter (1892) dam-break solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: Godunov-HLL
    params: {N: 250, CFL: 0.9}
    results: {h_error: 2.5e-2, wave_err: 0.5}
  - solver: MUSCL-Hancock
    params: {N: 250, CFL: 0.9}
    results: {h_error: 8.0e-3, wave_err: 0.15}
  - solver: DG-P1
    params: {N: 250, CFL: 0.3}
    results: {h_error: 3.5e-3, wave_err: 0.05}
quality_scoring:
  - {min_h_err: 1.0e-3, Q: 1.00}
  - {min_h_err: 1.0e-2, Q: 0.90}
  - {min_h_err: 5.0e-2, Q: 0.80}
  - {min_h_err: 1.0e-1, Q: 0.75}
```

**Baseline solver:** MUSCL-Hancock — h error 8.0×10⁻³
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | h L2 Error | Wavefront Error (m) | Runtime | Q |
|--------|-----------|---------------------|---------|---|
| Godunov-HLL | 2.5e-2 | 0.5 | 0.5 s | 0.80 |
| MUSCL-Hancock | 8.0e-3 | 0.15 | 1 s | 0.90 |
| DG-P1 | 3.5e-3 | 0.05 | 2 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 3 × 1.0 × Q
Best case (DG-P1): 300 × 1.00 = 300 PWM
Floor:             300 × 0.75 = 225 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p421_hash>",
  "h_s": "sha256:<spec421_hash>",
  "h_b": "sha256:<bench421_hash>",
  "r": {"h_error": 3.5e-3, "wave_err": 0.05, "ratio": 0.35},
  "c": {"fitted_rate": 1.95, "theoretical_rate": 2.0, "K": 3},
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
pwm-node benchmarks | grep river_hydraulics
pwm-node verify AF_environmental_science/river_hydraulics_s1_ideal.yaml
pwm-node mine AF_environmental_science/river_hydraulics_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
