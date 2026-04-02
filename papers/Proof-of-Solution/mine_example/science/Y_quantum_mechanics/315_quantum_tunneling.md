# Principle #315 — Quantum Tunneling (WKB)

**Domain:** Quantum Mechanics | **Carrier:** transmission amplitude | **Difficulty:** Textbook (δ=1)
**DAG:** ∂.time → L.hamiltonian → B.absorbing |  **Reward:** 1× base

---

## ASCII Pipeline

```
seed ──→ Principle ──→ spec.md ──→ Benchmark ──→ Solution
 │         (E,G,W,C)     (YAML)      (data+baselines)  (solver)
 │          ∂.time→L.hamiltonian→B.absorbing      WKB-tunnel  rect-barrier      analytic/num
 L1 seeds   L1 out       L2 out       L3 out            L4 out
 200 PWM    immutable    150 PWM      100 PWM           R×δ×Q PWM
```

---

## Layer 1 — Seeds → Principle

```
┌──────────────────────────────────────────────────────────────────┐
│  QUANTUM TUNNELING (WKB)        P = (E,G,W,C)   Principle #315  │
├────────┬─────────────────────────────────────────────────────────┤
│   E    │ T ≈ exp(−2 ∫ₐᵇ κ(x) dx)                               │
│        │ κ(x) = √(2m(V(x)−E))/ℏ  (classically forbidden)      │
│        │ Exact for rectangular: T = [1 + V₀²sinh²(κa)/(4E(V₀−E))]⁻¹│
│        │ Forward: given V(x), E → compute transmission T       │
├────────┼─────────────────────────────────────────────────────────┤
│   G    │ [∂.time] ──→ [L.hamiltonian] ──→ [B.absorbing]         │
│        │ derivative  linear-op  boundary                        │
│        │ V={∂.time, L.hamiltonian, B.absorbing}  A={∂.time→L.hamiltonian, L.hamiltonian→B.absorbing}  L_DAG=2.0 │
├────────┼─────────────────────────────────────────────────────────┤
│   W    │ Existence: YES (transfer matrix always defined)        │
│        │ Uniqueness: YES (T uniquely determined by V, E)        │
│        │ Stability: exponential sensitivity to barrier width    │
│        │ Mismatch: WKB breaks near classical turning points     │
├────────┼─────────────────────────────────────────────────────────┤
│   C    │ e = |T_wkb − T_exact|/|T_exact| (primary)             │
│        │ q = 2.0 (trapezoidal integration of κ)               │
│        │ T = {residual_norm, convergence_rate, K_resolutions}   │
└────────┴─────────────────────────────────────────────────────────┘
```

### S1-S4 Gate Checks (Layer 1)

| Gate | Check | Result |
|------|-------|--------|
| S1 | Barrier region well-defined; turning points identifiable | PASS |
| S2 | Transfer-matrix formalism guarantees unique T for given V, E | PASS |
| S3 | WKB integral converges; exact transfer-matrix available as reference | PASS |
| S4 | T error bounded by connection formula accuracy | PASS |

---

## Layer 2 — Principle → spec.md

```yaml
# tunneling/rect_barrier_s1_ideal.yaml
principle_ref: sha256:<p315_hash>
omega:
  grid: [512]
  domain: [-10, 10]
E:
  forward: "T = [1 + V0^2 sinh^2(κa)/(4E(V0-E))]^{-1}"
  potential: rectangular_barrier
B:
  boundary: {incoming_plane_wave: true}
I:
  scenario: rectangular_barrier
  V0: 5.0
  width: 2.0
  E_range: [0.5, 4.5]
  N_energies: 100
O: [transmission_coefficient, reflection_coefficient]
epsilon:
  T_rel_max: 1.0e-8
```

### S1-S4 Table (Layer 2)

| Gate | Check on spec | Result |
|------|---------------|--------|
| S1 | Energy range below barrier; grid resolves evanescent wave | PASS |
| S2 | Rectangular barrier has closed-form T(E) | PASS |
| S3 | Transfer-matrix method is exact for piecewise-constant V | PASS |
| S4 | T error < 10⁻⁸ achievable with transfer matrix | PASS |

**Layer 2 reward:** 150 × φ(t) × 0.70 = 105 PWM (designer) + upstream 15% → L1

---

## Layer 3 — spec → Benchmark

```yaml
# tunneling/benchmark_rect_barrier.yaml
spec_ref: sha256:<spec315_hash>
principle_ref: sha256:<p315_hash>
dataset:
  name: rectangular_barrier_exact
  reference: "Analytic transfer-matrix solution"
  data_hash: sha256:<dataset_hash>
baselines:
  - solver: WKB (simple)
    params: {N_quad: 100}
    results: {T_rel_error: 5.2e-2}
  - solver: Transfer-matrix
    params: {N_slices: 1}
    results: {T_rel_error: 1.0e-15}
  - solver: Numerov + matching
    params: {N: 1024}
    results: {T_rel_error: 3.1e-8}
quality_scoring:
  - {min_T_error: 1.0e-10, Q: 1.00}
  - {min_T_error: 1.0e-6, Q: 0.90}
  - {min_T_error: 1.0e-3, Q: 0.80}
  - {min_T_error: 1.0e-1, Q: 0.75}
```

**Baseline solver:** Transfer-matrix — T error 1.0×10⁻¹⁵ (exact)
**Layer 3 reward:** 100 × φ(t) × 0.60 = 60 PWM (builder) + upstream

---

## Layer 4 — Benchmark → Solution

### Solver Comparison

| Solver | T Rel Error | Runtime | Q |
|--------|------------|---------|---|
| WKB (simple) | 5.2e-2 | 0.01 s | 0.75 |
| Numerov + matching | 3.1e-8 | 0.1 s | 0.90 |
| Transfer-matrix | 1.0e-15 | 0.001 s | 1.00 |

### Reward Calculation

```
R = R_base × φ(t) × δ × ν_c × Q
  = 100 × 1.0 × 1 × 1.0 × Q
Best case (transfer-matrix): 100 × 1.00 = 100 PWM
Floor:                       100 × 0.75 =  75 PWM
```

### Certificate Snippet

```json
{
  "h_p": "sha256:<p315_hash>",
  "h_s": "sha256:<spec315_hash>",
  "h_b": "sha256:<bench315_hash>",
  "r": {"residual_norm": 1.0e-15, "error_bound": 1.0e-8, "ratio": 1.0e-7},
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
| L4 Solution | — | 75–100 PWM per solve |

---

## Quick-Start

```bash
pwm-node benchmarks | grep tunneling
pwm-node verify tunneling/rect_barrier_s1_ideal.yaml
pwm-node mine tunneling/rect_barrier_s1_ideal.yaml
pwm-node inspect sha256:<cert_hash>
```
